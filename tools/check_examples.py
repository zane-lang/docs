#!/usr/bin/env python3
"""Check the Zane code examples in Markdown against the real `zane` CLI.

Fence convention (canonical description: CONTRIBUTING.md):

  ```zane            whole program: must build and run, exit 0
  ```output         exact stdout of the zane fence just before it
  ```zane fragment   shown only, skipped
  ```zane error      must fail `zane check`; `// error: <text>` on the first
                     line must appear in the diagnostics
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
from pathlib import Path

STD_URL = "https://github.com/zane-lang/std"
ZANE_URL = "https://github.com/zane-lang/zane/releases/download/{v}/zane-{os}-{arch}"
COMPILER_URL = (
    "https://github.com/zane-lang/compiler/releases/download/{v}/"
    "zane-compiler-{v}-{os}-{arch}.tar.gz"
)
TIMEOUT = 300


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


def classify(fence):
    """Kind of a fence, or None when it is not a zane example."""
    if fence.lang != "zane":
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
    for idx, f in enumerate(fences):
        kind = classify(f)
        if kind is None:
            continue
        ex = Example(str(path), f.line, kind, f.body)
        if kind == ERROR:
            first = f.body.split("\n", 1)[0].strip()
            m = re.match(r"//\s*error:\s*(.*\S)", first)
            ex.error_text = m.group(1) if m else None
        if kind == PROGRAM and idx + 1 < len(fences):
            nxt = fences[idx + 1]
            if nxt.lang == "output" and _only_blank(lines, f, nxt):
                ex.expected = nxt.body
        examples.append(ex)
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
    with urllib.request.urlopen(url) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out)


def install(pins, cache):
    """Fetch the pinned zane (into `cache`) and compiler (into ~/.zane/toolchains)."""
    os_, arch = _plat()
    cache = Path(cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    zane = cache / "bin" / ("zane-%s" % pins["zane"])
    if not zane.exists():
        zane.parent.mkdir(exist_ok=True)
        print("downloading zane %s" % pins["zane"], file=sys.stderr)
        _download(ZANE_URL.format(v=pins["zane"], os=os_, arch=arch), zane)
        zane.chmod(zane.stat().st_mode | stat.S_IEXEC)
    tc = Path.home() / ".zane" / "toolchains" / pins["compiler"]
    if not tc.exists():
        print("downloading compiler %s" % pins["compiler"], file=sys.stderr)
        tmp = cache / "compiler.tar.gz"
        _download(COMPILER_URL.format(v=pins["compiler"], os=os_, arch=arch), tmp)
        tc.mkdir(parents=True)
        with tarfile.open(tmp) as t:
            for m in t.getmembers():
                parts = Path(m.name).parts[1:]  # strip the top directory
                if not parts:
                    continue
                m.name = str(Path(*parts))
                t.extract(m, tc, filter="data") if sys.version_info >= (3, 12) else t.extract(m, tc)
        tmp.unlink()
    return str(zane), {}


# --------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------

def run(cmd, cwd, env=None, timeout=TIMEOUT):
    e = dict(os.environ)
    e.update(env or {})
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError:
        return 127, "", "command not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "timed out after %ds" % timeout, ""
    return p.returncode, p.stdout, p.stderr


def make_template(zane, root, std=None, std_tag=None, env=None, compiler=None):
    """Create the template project once; returns its directory.

    `zane init` pins the newest installed compiler, so a pinned `compiler`
    moves the template to it with `zane toolchain update`.
    """
    rc, out, err = run([zane, "init", "tmpl", "--yes"], root, env)
    if rc:
        sys.exit("zane init failed:\n" + (out + err))
    proj = Path(root) / "tmpl"
    if compiler:
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
    """Exact stdout, but for one trailing newline (CONTRIBUTING.md)."""
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
    try:
        if ex.kind == ERROR:
            rc, out, err = run([zane, "check"], proj, env)
            diag = out + err
            if rc == 0:
                return "expected `zane check` to fail, but it succeeded"
            if ex.error_text and ex.error_text not in diag:
                return ("diagnostics do not contain %r:\n%s" % (ex.error_text, trim(diag)))
            return None
        rc, out, err = run([zane, "run"], proj, env)
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

    examples = collect(args.paths)
    work = tempfile.mkdtemp(prefix="zane-check-")
    env, zane, std_tag, compiler = {}, args.zane, None, None
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
