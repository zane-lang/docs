#!/usr/bin/env python3
"""Check the Zane code examples in Markdown against the real `zane` CLI.

Fence convention (canonical description: CONTRIBUTING.md):

  ```zane            whole program: must build and run, exit 0
  ```output         exact stdout of the zane fence just before it
  ```zane fragment   shown on the page, not run; counted as skipped
  ```zane error      must fail `zane check`; `// error: <text>` on the first
                     line must appear in the diagnostics
  ```c file=PATH     any fence with `file=PATH` in its info string: a file
                     written at PATH, relative to the package directory, for
                     the next `zane` or `zane error` example of the page
  anything else      ignored

Stdlib only.
"""

import argparse
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

STD_URL = "https://github.com/zane-lang/std"
ZANE_URL = "https://github.com/zane-lang/zane/releases/download/{v}/zane-{os}-{arch}"
COMPILER_URL = (
    "https://github.com/zane-lang/compiler/releases/download/{v}/"
    "zane-compiler-{v}-{os}-{arch}.tar.gz"
)
TIMEOUT = 300
# The exit code run() returns for a command it had to stop. No real process
# exits with this code: a negative code is a signal number, and signal numbers
# end at 64.
TIMED_OUT = -1000


# --------------------------------------------------------------------------
# Fence parser (CommonMark fenced code blocks)
# --------------------------------------------------------------------------

@dataclass
class Fence:
    line: int          # 1-based line of the opening fence
    info: str          # whole info string
    body: str          # content, without the trailing newline

    @property
    def words(self):
        return self.info.split()

    @property
    def lang(self):
        return self.words[0] if self.words else ""


_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")


def parse_fences(text):
    """Return every top-level fenced code block of `text`, in order."""
    lines = text.splitlines()
    fences = []
    i = 0
    while i < len(lines):
        m = _OPEN.match(lines[i])
        if not m or (m.group(2)[0] == "`" and "`" in m.group(3)):
            i += 1
            continue
        indent, marker, info = len(m.group(1)), m.group(2), m.group(3).strip()
        closer = re.compile(r"^ {0,3}%s{%d,}[ \t]*$" % (re.escape(marker[0]), len(marker)))
        body = []
        j = i + 1
        while j < len(lines) and not closer.match(lines[j]):
            body.append(re.sub(r"^ {0,%d}" % indent, "", lines[j]))
            j += 1
        fences.append(Fence(i + 1, info, "\n".join(body)))
        i = j + 1  # an unclosed fence runs to the end of the file
    return fences


# --------------------------------------------------------------------------
# Examples
# --------------------------------------------------------------------------

PROGRAM, FRAGMENT, ERROR = "program", "fragment", "error"


@dataclass
class Example:
    path: str
    line: int
    kind: str
    code: str
    expected: str = None   # program: exact stdout, or None when unchecked
    error_text: str = None  # error: required diagnostic text
    files: dict = field(default_factory=dict)  # companion files: path -> text


class FenceError(Exception):
    """A fence the checker cannot use, reported as `path:line: message`."""


def companion_path(fence):
    """The `file=PATH` of a fence, or None when the fence names no file."""
    for w in fence.words[1:] if fence.words else []:
        if w.startswith("file="):
            return w[len("file="):]
    return None


def _check_companion(path):
    """Why a companion file's path is refused, or None when it is usable."""
    p = PurePosixPath(path)
    if not path or p.is_absolute() or "\\" in path:
        return "file=%s must be a relative path with / separators" % path
    if any(part == ".." for part in p.parts):
        return "file=%s must stay inside the package directory" % path
    if str(p) == ".":
        return "file=%s names the package directory, not a file" % path
    if str(p) == "main.zn":
        return "file=main.zn would replace the example itself"
    return None


def classify(fence):
    """The example kind of a fence, or None when the fence is not a zane example."""
    if fence.lang != "zane" or companion_path(fence) is not None:
        return None
    attrs = fence.words[1:]
    if "fragment" in attrs:
        return FRAGMENT
    if "error" in attrs:
        return ERROR
    return PROGRAM


def extract(path, text):
    """Examples of one Markdown file."""
    fences = parse_fences(text)
    lines = text.splitlines()
    examples = []
    pending = {}  # companion files waiting for the next program or error example
    first_pending = None
    for idx, f in enumerate(fences):
        name = companion_path(f)
        if name is not None:
            problem = _check_companion(name)
            if not problem and str(PurePosixPath(name)) in pending:
                problem = "file=%s is given twice for one example" % name
            if problem:
                raise FenceError("%s:%d: %s" % (path, f.line, problem))
            pending[str(PurePosixPath(name))] = f.body
            first_pending = first_pending or f.line
            continue
        kind = classify(f)
        if kind is None:
            continue
        ex = Example(str(path), f.line, kind, f.body)
        if kind != FRAGMENT:
            ex.files, pending, first_pending = pending, {}, None
        if kind == ERROR:
            first = f.body.split("\n", 1)[0].strip()
            m = re.match(r"//\s*error:\s*(.*\S)", first)
            ex.error_text = m.group(1) if m else None
        if kind == PROGRAM and idx + 1 < len(fences):
            nxt = fences[idx + 1]
            if nxt.lang == "output" and _only_blank(lines, f, nxt):
                ex.expected = nxt.body
        examples.append(ex)
    if pending:
        raise FenceError("%s:%d: a file= fence has no `zane` or `zane error` "
                         "example after it" % (path, first_pending))
    return examples


def _fence_end(lines, f):
    """Index (0-based) of the line after f's closing fence."""
    marker = _OPEN.match(lines[f.line - 1]).group(2)
    closer = re.compile(r"^ {0,3}%s{%d,}[ \t]*$" % (re.escape(marker[0]), len(marker)))
    j = f.line
    while j < len(lines) and not closer.match(lines[j]):
        j += 1
    return j + 1


def _only_blank(lines, a, b):
    return all(not ln.strip() for ln in lines[_fence_end(lines, a):b.line - 1])


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(p.rglob("*.md"))
        else:
            files.append(p)
    out = []
    for f in files:
        out += extract(f, f.read_text(encoding="utf-8"))
    return out


# --------------------------------------------------------------------------
# Toolchain
# --------------------------------------------------------------------------

def read_coda(path):
    """Minimal coda reader: top-level `key value` lines only."""
    data = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        parts = raw.split(None, 1)
        if len(parts) == 2 and not raw.startswith((" ", "\t", "#")):
            data[parts[0]] = parts[1].strip()
    return data


def _plat():
    os_ = {"linux": "linux", "darwin": "macos"}.get(sys.platform)
    arch = {"x86_64": "x86_64", "amd64": "x86_64", "arm64": "arm64",
            "aarch64": "arm64"}.get(platform.machine().lower())
    if not os_ or not arch:
        sys.exit("check_examples: unsupported platform for --install")
    return os_, arch


def _download(url, dest):
    """Download to a temporary file next to `dest`, and move it to `dest` only once the download is complete."""
    dest = Path(dest)
    fd, part = tempfile.mkstemp(prefix=dest.name + ".", suffix=".part", dir=dest.parent)
    try:
        with urllib.request.urlopen(url) as r, os.fdopen(fd, "wb") as out:
            shutil.copyfileobj(r, out)
        os.replace(part, dest)
    except BaseException:
        Path(part).unlink(missing_ok=True)
        raise


def zane_home():
    """Where `zane` keeps installed toolchains: $ZANE_HOME, else ~/.zane."""
    return Path(os.environ.get("ZANE_HOME") or Path.home() / ".zane")


def _check_member(m):
    """Refuse an archive member that would land, or link, outside the folder it is unpacked in."""
    def escapes(path):
        p = PurePosixPath(path)
        if p.is_absolute() or Path(path).is_absolute():
            return True
        depth = 0
        for part in p.parts:
            depth += -1 if part == ".." else 0 if part == "." else 1
            if depth < 0:
                return True
        return False

    if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
        raise ValueError("compiler archive member %s is not a file, folder or link" % m.name)
    if escapes(m.name):
        raise ValueError("compiler archive member %s lies outside the archive" % m.name)
    if m.issym() and escapes(str(PurePosixPath(m.name).parent / m.linkname)):
        raise ValueError("compiler archive link %s points outside the archive" % m.name)
    if m.islnk():
        # A hard link names its target by archive path, top directory included.
        parts = PurePosixPath(m.linkname).parts[1:]
        if not parts or escapes(m.linkname) or escapes(str(PurePosixPath(*parts))):
            raise ValueError("compiler archive link %s points outside the archive" % m.name)
        m.linkname = str(PurePosixPath(*parts))


def extract_compiler(archive, tc):
    """Unpack a compiler release into `tc`; `tc` is created only if every member extracts."""
    tc.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=tc.name + ".", suffix=".part", dir=tc.parent))
    try:
        with tarfile.open(archive) as t:
            for m in t.getmembers():
                parts = Path(m.name).parts[1:]  # strip the top directory
                if not parts:
                    continue
                m.name = str(Path(*parts))
                _check_member(m)
                if sys.version_info >= (3, 12):
                    t.extract(m, staging, filter="data")
                else:
                    t.extract(m, staging)
        os.replace(staging, tc)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def install(pins, cache):
    """Fetch the pinned zane (into `cache`) and compiler (into zane_home()/toolchains)."""
    os_, arch = _plat()
    cache = Path(cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    zane = cache / "bin" / ("zane-%s" % pins["zane"])
    if not zane.exists():
        zane.parent.mkdir(exist_ok=True)
        print("downloading zane %s" % pins["zane"], file=sys.stderr)
        part = zane.with_name(zane.name + ".download")
        _download(ZANE_URL.format(v=pins["zane"], os=os_, arch=arch), part)
        part.chmod(part.stat().st_mode | stat.S_IEXEC)
        os.replace(part, zane)
    tc = zane_home() / "toolchains" / pins["compiler"]
    if not tc.exists():
        print("downloading compiler %s" % pins["compiler"], file=sys.stderr)
        tmp = cache / "compiler.tar.gz"
        _download(COMPILER_URL.format(v=pins["compiler"], os=os_, arch=arch), tmp)
        try:
            extract_compiler(tmp, tc)
        finally:
            tmp.unlink(missing_ok=True)
    return str(zane), {}


# --------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------

def run(cmd, cwd, env=None, timeout=None):
    timeout = timeout or TIMEOUT
    e = dict(os.environ)
    e.update(env or {})
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError:
        return 127, "", "command not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return TIMED_OUT, "timed out after %ds" % timeout, ""
    return p.returncode, p.stdout, p.stderr


def executable(cmd):
    """Make a command given as a path absolute, because commands run in other
    directories; leave a bare command name unchanged, so that PATH lookup finds it."""
    if os.sep in cmd or (os.altsep and os.altsep in cmd):
        return str(Path(cmd).resolve())
    return cmd


def make_template(zane, root, std=None, std_tag=None, env=None, compiler=None):
    """Create the template project once; returns its directory.

    `zane init` pins the newest installed compiler, so when `compiler` is given
    and `zane init` pinned another one, `zane toolchain update` moves the
    template to `compiler`. The update asks the GitHub API for the release, so
    it runs only when the pin differs.
    """
    rc, out, err = run([zane, "init", "tmpl", "--yes"], root, env)
    if rc:
        sys.exit("zane init failed:\n" + (out + err))
    proj = Path(root) / "tmpl"
    manifest = proj / "zane.coda"
    pinned = read_coda(manifest).get("zane-version") if manifest.exists() else None
    if compiler and compiler != pinned:
        rc, out, err = run([zane, "toolchain", "update", compiler], proj, env)
        if rc:
            sys.exit("zane toolchain update %s failed:\n%s" % (compiler, out + err))
    cmd = [zane, "add", STD_URL] + ([std_tag] if std_tag else []) + ["--from-source"]
    rc, out, err = run(cmd, proj, env)
    if rc:
        sys.exit("zane add std failed:\n" + (out + err))
    if std:
        rc, out, err = run([zane, "dev", "std", str(Path(std).resolve())], proj, env)
        if rc:
            sys.exit("zane dev std failed:\n" + (out + err))
    run([zane, "fetch"], proj, env)  # warm caches; failure is not fatal
    return proj


def main_file(proj):
    found = sorted(Path(proj).glob("bin/*/main.zn"))
    if not found:
        sys.exit("template project has no bin/<name>/main.zn")
    return found[0]


def rename_package(code, name):
    return re.sub(r"^(\s*package\s+)[A-Za-z_][A-Za-z0-9_]*", r"\g<1>" + name, code,
                  count=1, flags=re.M)


def trim(s, n=25):
    lines = s.strip().splitlines()
    if len(lines) > n:
        lines = lines[:n] + ["... (%d more lines)" % (len(lines) - n)]
    return "\n".join("    " + ln for ln in lines)


def same_output(actual, expected):
    """The program's exact stdout, ignoring one trailing newline (CONTRIBUTING.md)."""
    def drop_one(s):
        return s[:-1] if s.endswith("\n") else s
    return drop_one(actual) == drop_one(expected)


def check_example(ex, zane, template, env, keep, workdir):
    """Return None on success or a failure message."""
    proj = Path(tempfile.mkdtemp(prefix="ex-", dir=workdir))
    shutil.copytree(template, proj, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out"), symlinks=True)
    mf = main_file(proj)
    mf.write_text(rename_package(ex.code, mf.parent.name) + "\n", encoding="utf-8")
    for name, text in ex.files.items():
        dest = mf.parent / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text + "\n", encoding="utf-8")
    try:
        if ex.kind == ERROR:
            rc, out, err = run([zane, "check"], proj, env)
            diag = out + err
            if rc == TIMED_OUT:
                return "`zane check` timed out:\n" + trim(diag)
            if rc == 0:
                return "expected `zane check` to fail, but it succeeded"
            if ex.error_text and ex.error_text not in diag:
                return ("diagnostics do not contain %r:\n%s" % (ex.error_text, trim(diag)))
            return None
        rc, out, err = run([zane, "run"], proj, env)
        if rc == TIMED_OUT:
            return "`zane run` timed out:\n" + trim(out + err)
        if rc != 0:
            return "`zane run` exited %d:\n%s" % (rc, trim(out + err))
        if ex.expected is not None and not same_output(out, ex.expected):
            return ("output differs\n  expected:\n%s\n  actual:\n%s"
                    % (trim(ex.expected), trim(out)))
        return None
    finally:
        if not keep:
            shutil.rmtree(proj, ignore_errors=True)
        else:
            print("kept %s (%s:%d)" % (proj, ex.path, ex.line), file=sys.stderr)


def check_all(examples, zane, template, env, jobs, keep, workdir):
    """Returns (failures, passed, skipped); failures is [(ex, message)]."""
    todo = [e for e in examples if e.kind != FRAGMENT]
    skipped = len(examples) - len(todo)
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        results = list(pool.map(
            lambda e: check_example(e, zane, template, env, keep, workdir), todo))
    failures = [(e, r) for e, r in zip(todo, results) if r]
    return failures, len(todo) - len(failures), skipped


def summary(passed, failed, skipped):
    return "%d passed, %d failed, %d skipped" % (passed, failed, skipped)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", help="Markdown files or folders")
    ap.add_argument("--zane", default=shutil.which("zane") or "zane")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--std", help="local std checkout instead of the released one")
    ap.add_argument("--install", action="store_true",
                    help="download the toolchain pinned in toolchain.coda")
    ap.add_argument("--keep", action="store_true", help="keep temp projects")
    args = ap.parse_args(argv)

    try:
        examples = collect(args.paths)
    except FenceError as e:
        print(e)
        return 1
    work = tempfile.mkdtemp(prefix="zane-check-")
    env, zane, std_tag, compiler = {}, executable(args.zane), None, None
    try:
        toolchain = Path(__file__).resolve().parent.parent / "toolchain.coda"
        pins = read_coda(toolchain) if toolchain.exists() else {}
        compiler = pins.get("compiler")
        if args.install:
            zane, env = install(pins, "~/.cache/zane-check-examples")
        if not args.std:
            std_tag = pins.get("std")
        if not any(e.kind != FRAGMENT for e in examples):
            print(summary(0, 0, len(examples)))
            return 0
        template = make_template(zane, work, args.std, std_tag, env, compiler)
        failures, passed, skipped = check_all(
            examples, zane, template, env, args.jobs, args.keep, work)
        for ex, msg in failures:
            print("%s:%d: %s" % (ex.path, ex.line, msg))
        print(summary(passed, len(failures), skipped))
        return 1 if failures else 0
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
        else:
            print("work dir kept: %s" % work, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
