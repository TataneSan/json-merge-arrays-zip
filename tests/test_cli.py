import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(args, stdin_text=""):
    return subprocess.run(
        [sys.executable, "-m", "json_merge_arrays_zip"] + args,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=HERE,
    )


def two_files(a_text, b_text):
    td = tempfile.TemporaryDirectory()
    fa = os.path.join(td.name, "a.json")
    fb = os.path.join(td.name, "b.json")
    with open(fa, "w") as fh:
        fh.write(a_text)
    with open(fb, "w") as fh:
        fh.write(b_text)
    return td, fa, fb


class TestZip(unittest.TestCase):
    def test_basic(self):
        td, fa, fb = two_files('[1, 2, 3]', '["a", "b", "c"]')
        with td:
            r = run_cli([fa, fb, "--compact", "-q"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), '[[1,"a"],[2,"b"],[3,"c"]]')

    def test_stdin(self):
        td, fa, fb = two_files("", "[1,2]")
        with td:
            r = run_cli(["-", fb, "--compact", "-q"], '["a","b"]')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), '[["a",1],["b",2]]')

    def test_fill_default_null(self):
        td, fa, fb = two_files("[1,2]", '["a","b","c"]')
        with td:
            r = run_cli([fa, fb, "--compact", "-q"])
        self.assertEqual(r.stdout.strip(), '[[1,"a"],[2,"b"],[null,"c"]]')

    def test_fill_custom(self):
        td, fa, fb = two_files("[1]", '["a","b"]')
        with td:
            r = run_cli([fa, fb, "--fill", '"?"', "--compact", "-q"])
        self.assertEqual(r.stdout.strip(), '[[1,"a"],["?","b"]]')

    def test_strict_len(self):
        td, fa, fb = two_files("[1,2]", '["a","b","c"]')
        with td:
            r = run_cli([fa, fb, "--strict-len", "-q"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("lengths", r.stderr)

    def test_skip_non_arrays(self):
        td, fa, fb = two_files('{"x": 1}\n[1, 2]', '{"y": 2}\n["a", "b"]')
        with td:
            r = run_cli([fa, fb, "--compact", "-q"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), '[[1,"a"],[2,"b"]]')

    def test_json_report(self):
        td, fa, fb = two_files("[1,2]", '["a","b"]')
        with td:
            r = run_cli([fa, fb, "--compact", "--json"])
        self.assertEqual(r.returncode, 0)
        report = json.loads(r.stderr)
        self.assertEqual(report["pairs_merged"], 1)
        self.assertEqual(report["tuples_emitted"], 2)

    def test_bad_json(self):
        td, fa, fb = two_files("not json}", "[1]")
        with td:
            r = run_cli([fa, fb, "-q"])
        self.assertEqual(r.returncode, 1)

    def test_missing_file(self):
        r = run_cli(["/nonexistent/a.json", "/nonexistent/b.json", "-q"])
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
