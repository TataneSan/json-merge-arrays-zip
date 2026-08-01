import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from json_merge_arrays_zip.cli import main


def run(argv, stdin_text=""):
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_text)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


def tmp_json(content):
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    fh.write(content)
    fh.close()
    return fh.name


class TestZip(unittest.TestCase):
    def test_inline_json(self):
        code, out, _ = run(["[1,2,3]", '["a","b","c"]', "--compact"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [[1, "a"], [2, "b"], [3, "c"]])

    def test_files(self):
        p1 = tmp_json("[1,2]")
        p2 = tmp_json('["a","b"]')
        try:
            code, out, _ = run([p1, p2, "--compact"])
        finally:
            os.unlink(p1)
            os.unlink(p2)
        self.assertEqual(json.loads(out), [[1, "a"], [2, "b"]])

    def test_jsonl_stdin(self):
        code, out, _ = run(["--jsonl", "--compact"], "[1,2,3]\n[4,5,6]\n")
        self.assertEqual(json.loads(out), [[1, 4], [2, 5], [3, 6]])

    def test_truncate_default(self):
        code, out, _ = run(["[1,2,3]", "[9]", "--compact"])
        self.assertEqual(json.loads(out), [[1, 9]])

    def test_pad(self):
        code, out, _ = run(["[1,2,3]", "[9]", "--pad", "--compact"])
        self.assertEqual(json.loads(out), [[1, 9], [2, None], [3, None]])

    def test_pad_fill_string(self):
        code, out, _ = run(["[1,2]", "[9]", "--pad", "--fill", '"X"',
                            "--compact"])
        self.assertEqual(json.loads(out), [[1, 9], [2, "X"]])

    def test_strict_len(self):
        code, _, err = run(["[1,2]", "[9]", "--strict-len"])
        self.assertEqual(code, 2)
        self.assertIn("unequal lengths", err)

    def test_path(self):
        code, out, _ = run(['{"rows":[1,2]}', '--path', 'rows', "--compact"])
        self.assertEqual(json.loads(out), [[1], [2]])

    def test_path_missing(self):
        code, _, err = run(['{"rows":[1]}', '--path', 'nope'])
        self.assertEqual(code, 1)

    def test_require(self):
        code, _, _ = run(["[1,2,3]", "[4,5,6]", "--require", "3"])
        self.assertEqual(code, 0)
        code, _, _ = run(["[1]", "[4]", "--require", "5"])
        self.assertEqual(code, 2)

    def test_stats(self):
        code, out, _ = run(["[1,2,3]", "[4,5]", "--stats-json"])
        rep = json.loads(out)
        self.assertEqual(rep["tuples"], 2)
        self.assertTrue(rep["truncated"])

    def test_not_array(self):
        code, _, err = run(['{"a": 1}'])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
