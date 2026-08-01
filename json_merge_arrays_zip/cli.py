"""Zip JSON arrays together index by index into tuples.

Given JSON documents that are (or contain) arrays, produces one array of
tuples where tuple i holds the i-th element of every input array:

    [1, 2, 3]  +  ["a", "b", "c"]  ->  [[1, "a"], [2, "b"], [3, "c"]]

Sources: multiple files, --json inline values, or a JSONL stream/stdin
where each line contributes one array. Arrays of different lengths are
truncated (zip semantics), padded with --fill, or rejected with
--strict-len.

Exit codes:
    0  success
    1  CLI or I/O error (missing file, invalid JSON, no arrays given)
    2  check failed (--strict-len on unequal lengths, --require N not met)
"""

import argparse
import json
import sys


def zip_arrays(arrays, fill=None, pad=False):
    """Zip arrays into a list of tuples; pad with fill if requested."""
    if pad:
        length = max(len(a) for a in arrays)
        return [[a[i] if i < len(a) else fill for a in arrays]
                for i in range(length)]
    length = min(len(a) for a in arrays)
    return [[a[i] for a in arrays] for i in range(length)]


def load_source(spec):
    """Load one JSON array from a file path, '-' (stdin), or inline JSON."""
    if spec == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(spec, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            try:
                return json.loads(spec)
            except json.JSONDecodeError:
                raise ValueError("cannot read %r as file or JSON" % spec)
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty input in %r" % spec)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON in %r: %s" % (spec, exc))


def extract_array(doc, path):
    """Extract the array at a dotted path (empty = the document itself)."""
    if not path:
        return doc
    cur = doc
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            raise ValueError("path %r not found" % path)
    return cur


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="json-merge-arrays-zip",
        description="Zip JSON arrays together index by index into tuples.",
    )
    parser.add_argument("sources", nargs="*",
                        help="files, '-' for stdin, or inline JSON arrays")
    parser.add_argument("--jsonl", action="store_true",
                        help="read stdin as JSONL: each line is one array")
    parser.add_argument("--path", default="",
                        help="dotted path to the array inside each document")
    parser.add_argument("--pad", action="store_true",
                        help="pad shorter arrays with --fill instead of "
                             "truncating to the shortest")
    parser.add_argument("--fill", default=None,
                        help="fill value used with --pad (parsed as JSON if "
                             "possible)")
    parser.add_argument("--strict-len", action="store_true",
                        help="exit 2 if input arrays do not all have the "
                             "same length")
    parser.add_argument("--require", type=int, metavar="N",
                        help="exit 2 if fewer than N tuples are produced")
    parser.add_argument("--compact", action="store_true",
                        help="emit compact JSON")
    parser.add_argument("--stats-json", action="store_true",
                        help="emit a JSON stats report instead of tuples")
    args = parser.parse_args(argv)

    try:
        fill = json.loads(args.fill) if args.fill is not None else None
    except (json.JSONDecodeError, TypeError):
        fill = args.fill

    docs = []
    if args.jsonl or (not args.sources):
        lines = sys.stdin.read().splitlines()
        docs = [ln for ln in lines if ln.strip()]
        if not docs:
            print("error: empty JSONL input", file=sys.stderr)
            return 1
        try:
            docs = [json.loads(ln) for ln in docs]
        except json.JSONDecodeError as exc:
            print("error: invalid JSONL: %s" % exc, file=sys.stderr)
            return 1
    else:
        for spec in args.sources:
            try:
                docs.append(load_source(spec))
            except ValueError as exc:
                print("error: %s" % exc, file=sys.stderr)
                return 1

    arrays = []
    for doc in docs:
        try:
            arr = extract_array(doc, args.path)
        except ValueError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 1
        if not isinstance(arr, list):
            print("error: source is not an array", file=sys.stderr)
            return 1
        arrays.append(arr)

    lengths = sorted({len(a) for a in arrays})
    if len(lengths) > 1 and args.strict_len:
        print("error: unequal lengths: %s" % lengths, file=sys.stderr)
        return 2

    result = zip_arrays(arrays, fill=fill, pad=args.pad)

    if args.stats_json:
        print(json.dumps({
            "arrays": len(arrays),
            "input_lengths": lengths,
            "tuples": len(result),
            "truncated": bool(len(lengths) > 1 and not args.pad),
            "padded": bool(args.pad and len(lengths) > 1),
        }, indent=2, sort_keys=True))
    else:
        if args.compact:
            print(json.dumps(result, separators=(",", ":"),
                             ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.require is not None and len(result) < args.require:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
