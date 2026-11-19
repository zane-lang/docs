import io
import os
import shutil
import tarfile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_examples as ce  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
# CI sets ZANE to the installed pinned zane and ZANE_REQUIRED=1, so that the
# integration tests fail instead of skipping when it is missing.
ZANE = os.environ.get("ZANE") or shutil.which("zane")
if os.environ.get("ZANE_REQUIRED") and not (ZANE and Path(ZANE).exists()):
    raise SystemExit("ZANE_REQUIRED is set, but no zane was found (ZANE=%r)" % ZANE)


class FenceParser(unittest.TestCase):
    def test_backticks_and_tildes(self):
        fs = ce.parse_fences("```a\nx\n```\n\n~~~b c\ny\n~~~\n")
        self.assertEqual([(f.lang, f.body, f.line) for f in fs],
                         [("a", "x", 1), ("b", "y", 5)])
        self.assertEqual(fs[1].words, ["b", "c"])

    def test_nested_longer_fence(self):
        fs = ce.parse_fences("````markdown\n```zane\nin\n```\n````\n")
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].lang, "markdown")

    def test_closer_needs_same_char_and_length(self):
        fs = ce.parse_fences("````x\na\n```\n~~~~\nb\n````\n")
        self.assertEqual(fs[0].body, "a\n```\n~~~~\nb")

    def test_unclosed_runs_to_end(self):
        fs = ce.parse_fences("```zane\na\nb\n")
        self.assertEqual(fs[0].body, "a\nb")

    def test_backtick_info_cannot_contain_backtick(self):
        self.assertEqual(ce.parse_fences("```a`b\nx\n"), [])

    def test_four_space_indent_is_not_a_fence(self):
        self.assertEqual(ce.parse_fences("    ```zane\n    x\n    ```\n"), [])


class Classify(unittest.TestCase):
    def kinds(self, text):
        return [e.kind for e in ce.extract("t.md", text)]

    def test_kinds(self):
        text = ("```zane\na\n```\n```zane fragment\nb\n```\n"
                "```zane error\nc\n```\n```sh\nd\n```\n```coda\ne\n```\n")
        self.assertEqual(self.kinds(text), [ce.PROGRAM, ce.FRAGMENT, ce.ERROR])

    def test_nested_is_not_an_example(self):
        self.assertEqual(self.kinds("````markdown\n```zane\na\n```\n````\n"), [])

    def test_output_pairing(self):
        ex = ce.extract("t.md", "```zane\na\n```\n\n\n```output\nhi\n```\n")
        self.assertEqual(ex[0].expected, "hi")

    def test_output_not_adjacent(self):
        ex = ce.extract("t.md", "```zane\na\n```\ntext\n```output\nhi\n```\n")
        self.assertIsNone(ex[0].expected)

    def test_output_after_fragment_ignored(self):
        ex = ce.extract("t.md", "```zane fragment\na\n```\n```output\nhi\n```\n")
        self.assertIsNone(ex[0].expected)

    def test_error_text(self):
        ex = ce.extract("t.md", "```zane error\n// error: bad thing\nx\n```\n")
        self.assertEqual(ex[0].error_text, "bad thing")

    def test_line_numbers(self):
        ex = ce.extract("t.md", "x\n\n```zane\na\n```\n")
        self.assertEqual(ex[0].line, 3)


class Misc(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(ce.summary(3, 1, 2), "3 passed, 1 failed, 2 skipped")

    def test_rename_package(self):
        self.assertEqual(ce.rename_package("package demo;\nx", "tmpl"), "package tmpl;\nx")

    def test_read_coda(self):
        p = Path(tempfile.mkdtemp()) / "t.coda"
        p.write_text("zane v0.18\ncompiler v0.40\n")
        self.assertEqual(ce.read_coda(p), {"zane": "v0.18", "compiler": "v0.40"})

    def test_toolchain_pins(self):
        pins = ce.read_coda(Path(__file__).resolve().parent.parent / "toolchain.coda")
        self.assertEqual(set(pins), {"zane", "compiler", "std"})

    def test_collect_folder(self):
        names = {Path(e.path).name for e in ce.collect([FIX])}
        self.assertIn("pass.md", names)
        self.assertNotIn("nested.md", names)


class Robustness(unittest.TestCase):
    """Behaviour that must not depend on the platform or on zane being installed."""

    def test_utf8_files_under_an_ascii_locale(self):
        with tempfile.TemporaryDirectory() as d:
            coda = Path(d) / "toolchain.coda"
            coda.write_text("zane v0.18\n# caf\u00e9\n", encoding="utf-8")
            code = ("import sys; sys.path.insert(0, %r); import check_examples as c; "
                    "print(c.read_coda(%r)['zane'])" % (str(Path(__file__).parent), str(coda)))
            env = dict(__import__("os").environ, LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONUTF8="0")
            r = subprocess.run([sys.executable, "-X", "utf8=0", "-c", code],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "v0.18")

    def test_missing_command_is_reported_not_raised(self):
        rc, out, err = ce.run(["/nonexistent/zane", "check"], ".")
        self.assertEqual(rc, 127)
        self.assertIn("command not found: /nonexistent/zane", err)

    def test_missing_zane_fails_cleanly(self):
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "check_examples.py"),
                            "--zane", "/nonexistent/zane", str(FIX / "pass.md")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("command not found: /nonexistent/zane", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class OutputAndPins(unittest.TestCase):
    def test_one_trailing_newline_is_ignored_and_no_more(self):
        self.assertTrue(ce.same_output("hi\n", "hi"))
        self.assertTrue(ce.same_output("hi", "hi\n"))
        self.assertFalse(ce.same_output("hi\n\n", "hi"))
        self.assertFalse(ce.same_output("hi\n\n\n", "hi\n"))

    def test_template_is_moved_to_the_pinned_compiler(self):
        # A stand-in zane that logs its arguments and makes the files init makes.
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "log"
            fake = Path(d) / "zane"
            fake.write_text(
                "#!/bin/sh\n"
                "echo \"$*\" >> %s\n"
                "if [ \"$1\" = init ]; then mkdir -p \"$2/bin/$2\"; fi\n" % log,
                encoding="utf-8")
            fake.chmod(0o755)
            ce.make_template(str(fake), d, compiler="v0.40")
            calls = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls[0], "init tmpl --yes")
            self.assertEqual(calls[1], "toolchain update v0.40")


def fake_zane(d, body):
    """A stand-in zane: a shell script that runs `body` with the arguments in $@."""
    fake = Path(d) / "zane"
    fake.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    fake.chmod(0o755)
    return str(fake)


class Install(unittest.TestCase):
    def test_toolchains_go_under_zane_home(self):
        with mock.patch.dict(os.environ, {"ZANE_HOME": "/opt/zh"}):
            self.assertEqual(ce.zane_home(), Path("/opt/zh"))
        with mock.patch.dict(os.environ, {"ZANE_HOME": ""}):
            self.assertEqual(ce.zane_home(), Path.home() / ".zane")

    def test_failed_download_leaves_nothing_behind(self):
        class Broken(io.BytesIO):
            def read(self, *a):
                if self.tell():
                    raise ConnectionResetError("cut off")
                return super().read(4)
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "zane-v0.18"
            with mock.patch.object(ce.urllib.request, "urlopen", lambda url: Broken(b"partial data")):
                with self.assertRaises(ConnectionResetError):
                    ce._download("https://example.invalid/zane", dest)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_failed_extraction_leaves_no_toolchain(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "c.tar.gz"
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as t:
                data = os.urandom(100000)  # incompressible, so the cut lands mid-member
                info = tarfile.TarInfo("top/bin/zanec")
                info.size = len(data)
                t.addfile(info, io.BytesIO(data))
            archive.write_bytes(buf.getvalue()[:200])  # truncated
            tc = Path(d) / "toolchains" / "v0.40"
            with self.assertRaises(Exception):
                ce.extract_compiler(archive, tc)
            self.assertFalse(tc.exists())
            self.assertEqual(list(tc.parent.iterdir()), [])

    def test_complete_archive_extracts_without_its_top_directory(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "c.tar.gz"
            with tarfile.open(archive, "w:gz") as t:
                info = tarfile.TarInfo("top/bin/zanec")
                info.size = 2
                t.addfile(info, io.BytesIO(b"ok"))
            tc = Path(d) / "toolchains" / "v0.40"
            ce.extract_compiler(archive, tc)
            self.assertEqual((tc / "bin" / "zanec").read_bytes(), b"ok")


class Commands(unittest.TestCase):
    def test_relative_zane_path_is_made_absolute(self):
        self.assertEqual(ce.executable("./bin/zane"), str(Path("bin/zane").resolve()))
        self.assertEqual(ce.executable("zane"), "zane")

    def test_timed_out_check_fails_an_error_example(self):
        with tempfile.TemporaryDirectory() as d:
            zane = fake_zane(d, "sleep 5\n")
            template = Path(d) / "tmpl"
            (template / "bin" / "tmpl").mkdir(parents=True)
            (template / "bin" / "tmpl" / "main.zn").write_text("", encoding="utf-8")
            ex = [e for e in ce.collect([str(FIX / "error_compiles.md")]) if e.kind == ce.ERROR][0]
            ex.error_text = None  # with no expected text, any non-zero exit used to pass
            with mock.patch.object(ce, "TIMEOUT", 1):
                msg = ce.check_example(ex, zane, template, {}, False, d)
            self.assertIsNotNone(msg)
            self.assertIn("timed out", msg)


@unittest.skipUnless(ZANE, "zane is not installed")
class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp(prefix="ce-test-")
        cls.template = ce.make_template(ZANE, cls.work, std=None, std_tag=None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def run_fixture(self, name):
        ex = ce.collect([FIX / name])
        return ce.check_all(ex, ZANE, self.template, {}, 1, False, self.work)

    def test_passing(self):
        failures, passed, skipped = self.run_fixture("pass.md")
        self.assertEqual((failures, passed, skipped), ([], 1, 0))

    def test_wrong_output(self):
        failures, passed, _ = self.run_fixture("wrong_output.md")
        self.assertEqual(passed, 0)
        self.assertIn("output differs", failures[0][1])

    def test_compile_error(self):
        failures, _, _ = self.run_fixture("compile_error.md")
        self.assertEqual(len(failures), 1)

    def test_error_fence_that_compiles(self):
        failures, _, _ = self.run_fixture("error_compiles.md")
        self.assertIn("expected `zane check` to fail", failures[0][1])

    def test_fragment_skipped(self):
        failures, passed, skipped = self.run_fixture("fragment.md")
        self.assertEqual((failures, passed, skipped), ([], 0, 1))

    def test_cli_exit_code(self):
        r = subprocess.run([sys.executable, str(Path(ce.__file__)), "--zane", ZANE,
                            str(FIX / "wrong_output.md")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"wrong_output\.md:3: ")
        self.assertIn("0 passed, 1 failed, 0 skipped", r.stdout)


if __name__ == "__main__":
    unittest.main()
