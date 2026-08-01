#!/usr/bin/env python3
"""json-merge-arrays-zip - Merge JSONL arrays by index into [a, b] tuples.

Reads two JSONL streams (or JSON files containing arrays) line by line and,
for each pair of arrays at the same position, zips their elements together
into tuples [a_item, b_item]. Useful to combine two parallel data sources
(for example keys + values, features + labels).

Exit codes:
    0 - success
    1 - I/O or CLI error (missing file, malformed JSON)
    2 - --strict-len assertion failed (pair arrays have different lengths)
"""

import argparse
import json
import sys

PROG = "json-merge-arrays-zip"
VERSION = "1.0.0"


def read_doc(source):
    """Return a list of JSON values from a file path or stdin ('-')."""
    if source == "-":
        text = sys.stdin.read()
    else:
        with open(source, "r", encoding="utf-8") as fh:
            text = fh.read()
    text = text.strip()
    if not text:
        return []
    # JSONL: one JSON value per line
    if text.startswith("[") or text.startswith("{") or text.startswith('"'):
        try:
            value = json.loads(text)
            return [value]
        except json.JSONDecodeError:
            pass  # fall through to JSONL parsing
    docs = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            docs.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError("%s: invalid JSON at line %d: %s" % (source, lineno, exc))
    return docs


def zip_arrays(a, b, fill, strict, source_label):
    if strict and len(a) != len(b):
        raise ValueError(
            "%s: arrays of different lengths (%d vs %d) rejected by --strict-len"
            % (source_label, len(a), len(b))
        )
    n = max(len(a), len(b))
    out = []
    for i in range(n):
        av = a[i] if i < len(a) else fill
        bv = b[i] if i < len(b) else fill
        out.append([av, bv])
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        prog=PROG,
        description="Merge two JSONL/JSON array streams by index into [a, b] tuples.",
    )
    p.add_argument("a_file", metavar="FILE_A",
                   help="first JSON/JSONL input (use '-' for stdin)")
    p.add_argument("b_file", metavar="FILE_B",
                   help="second JSON/JSONL input")
    p.add_argument(
        "--fill", default="null",
        help="value used when one array is shorter than the other "
        "(parsed as JSON, default: null; e.g. 0, \"\", \"N/A\")",
    )
    p.add_argument(
        "--strict-len", action="store_true",
        help="fail (exit 2) if a pair of arrays has different lengths",
    )
    p.add_argument(
        "--compact", action="store_true",
        help="emit compact JSON lines instead of indented blocks",
    )
    p.add_argument(
        "--json", action="store_true",
        help="print a machine-readable summary report on stderr as JSON",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress human-readable reports on stderr",
    )
    p.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    args = p.parse_args(argv)

    try:
        fill = json.loads(args.fill)
    except json.JSONDecodeError:
        fill = args.fill  # treat as plain string

    try:
        docs_a = read_doc(args.a_file)
    except (OSError, ValueError) as exc:
        print("%s: %s" % (PROG, exc), file=sys.stderr)
        return 1
    try:
        docs_b = read_doc(args.b_file)
    except (OSError, ValueError) as exc:
        print("%s: %s" % (PROG, exc), file=sys.stderr)
        return 1

    pairs = 0
    emitted = 0
    for idx, (da, db) in enumerate(zip(docs_a, docs_b), 1):
        label = "line %d" % idx
        if not isinstance(da, list) or not isinstance(db, list):
            if not args.quiet:
                print("%s: %s skipped (not an array on both sides)"
                      % (PROG, label), file=sys.stderr)
            continue
        try:
            zipped = zip_arrays(da, db, fill, args.strict_len, label)
        except ValueError as exc:
            print("%s: %s" % (PROG, exc), file=sys.stderr)
            return 2
        pairs += 1
        emitted += len(zipped)
        if args.compact:
            print(json.dumps(zipped, separators=(",", ":"), ensure_ascii=False))
        else:
            print(json.dumps(zipped, ensure_ascii=False, indent=2))

    if len(docs_a) != len(docs_b) and not args.quiet:
        print("%s: input lengths differ (%d vs %d JSON values); extra values ignored"
              % (PROG, len(docs_a), len(docs_b)), file=sys.stderr)

    if args.json:
        report = {
            "file_a": args.a_file,
            "file_b": args.b_file,
            "values_a": len(docs_a),
            "values_b": len(docs_b),
            "pairs_merged": pairs,
            "tuples_emitted": emitted,
            "strict_len": bool(args.strict_len),
            "fill": fill,
        }
        print(json.dumps(report, indent=2), file=sys.stderr)
    elif not args.quiet:
        print("%s: merged %d pair(s), emitted %d tuple(s)"
              % (PROG, pairs, emitted), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
