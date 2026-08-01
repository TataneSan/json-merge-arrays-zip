# json-merge-arrays-zip

[![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

Merge two JSON / JSONL array streams **by index** into tuples `[a, b]`.

Each line (or document) of FILE_A is zipped, index by index, with the matching
line of FILE_B. Non-array values are skipped. When arrays have different
lengths a fill value is used, unless `--strict-len` rejects them (exit 2).

Typical uses: combining a stream of keys with a stream of values, joining
features and labels, merging two parallel data exports.

## Features

- Accepts plain JSON (`[1,2,3]`) or JSON Lines (one value per line)
- Zips arrays pairwise: `[a0,b0], [a1,b1], ...`
- `--fill VALUE` for jagged inputs (VALUE parsed as JSON, default `null`)
- `--strict-len` CI gate: exit 2 when paired arrays differ in length
- `--compact` single-line output, `--json` machine-readable summary
- Reads FILE_A from stdin with `-`
- Pure Python standard library, no dependencies

## Installation

From source:

```sh
pip install .
```

Or directly from GitHub:

```sh
pip install git+https://github.com/TataneSan/json-merge-arrays-zip.git
```

## Usage

```text
usage: json-merge-arrays-zip [-h] [--fill FILL] [--strict-len] [--compact]
                             [--json] [-q] [--version]
                             FILE_A FILE_B
```

### Merge two JSONL files

```sh
$ cat keys.jsonl
["a", "b", "c"]

$ cat values.jsonl
[1, 2, 3]

$ json-merge-arrays-zip keys.jsonl values.jsonl --compact
[["a",1],["b",2],["c",3]]
```

### Pipe the first stream from stdin

```sh
$ echo '["x","y"]' | json-merge-arrays-zip - values.jsonl --compact
[["x",1],["y",2]]
```

### Jagged arrays with fill

```sh
$ echo '[1, 2]' > a.json
$ echo '["a", "b", "c"]' > b.json
$ json-merge-arrays-zip a.json b.json --compact
[[1,"a"],[2,"b"],[null,"c"]]

$ json-merge-arrays-zip a.json b.json --fill '"?"' --compact
[[1,"a"],[2,"b"],["?","c"]]
```

### Strict length check (CI)

```sh
$ json-merge-arrays-zip a.json b.json --strict-len
json-merge-arrays-zip: line 1: arrays of different lengths (2 vs 3) rejected by --strict-len
# exit code 2
```

### Summary report

```sh
json-merge-arrays-zip keys.jsonl values.jsonl --compact --json
```

writes the zipped tuples on stdout and a JSON report (`pairs_merged`,
`tuples_emitted`, fill value, ...) on stderr.

## Exit codes

| Code | Meaning                                                    |
|------|------------------------------------------------------------|
| 0    | success                                                    |
| 1    | I/O or CLI error (missing file, malformed JSON)            |
| 2    | `--strict-len` rejected a pair of arrays of unequal length |

## Development

Run the test suite:

```sh
python -m unittest discover -s tests -v
```

## License

MIT - see [LICENSE](LICENSE).
