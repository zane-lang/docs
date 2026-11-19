import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_examples as ce  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
ZANE = shutil.which("zane")


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
