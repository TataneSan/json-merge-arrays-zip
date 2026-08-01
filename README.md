# json-merge-arrays-zip

Zip JSON arrays together index by index into tuples.

```console
$ json-merge-arrays-zip '[1,2,3]' '["a","b","c"]' --compact
[[1,"a"],[2,"b"],[3,"c"]]
```

Sources can be files, inline JSON strings, `-` for stdin, or a JSONL
stream where every line contributes one array (`--jsonl`).

## Features

- Classic zip semantics: stop at the shortest array (default)
- `--pad --fill VALUE` to pad shorter arrays instead of truncating
- `--strict-len` to fail when input lengths differ (data-quality gate)
- `--path a.b.c` to reach an array nested inside each document
- `--require N` minimum tuple count for CI, JSON stats report
- Compact or pretty output
- Pure Python standard library, Python >= 3.9

## Install

```sh
pip install .
# or straight from the repo
pip install git+https://github.com/TataneSan/json-merge-arrays-zip.git
```

You can also run it without installing:

```sh
python3 -m json_merge_arrays_zip '[1,2]' '["a","b"]'
```

## Usage

```console
$ json-merge-arrays-zip names.json scores.json
$ json-merge-arrays-zip --jsonl < arrays.jsonl
$ json-merge-arrays-zip --path data.values a.json b.json
```

### Examples

Two files:

```console
$ cat a.json
[1, 2, 3]
$ cat b.json
["x", "y", "z"]
$ json-merge-arrays-zip a.json b.json --compact
[[1,"x"],[2,"y"],[3,"z"]]
```

JSONL stream:

```console
$ printf '[1,2,3]\n[4,5,6]\n' | json-merge-arrays-zip --jsonl --compact
[[1,4],[2,5],[3,6]]
```

Unequal lengths — truncated by default:

```console
$ json-merge-arrays-zip '[1,2,3]' '[9]' --compact
[[1,9]]
```

Padded instead:

```console
$ json-merge-arrays-zip '[1,2,3]' '[9]' --pad --compact
[[1,9],[2,null],[3,null]]
```

Fail on unequal lengths (CI gate):

```console
$ json-merge-arrays-zip '[1,2]' '[9]' --strict-len; echo $?
error: unequal lengths: [1, 2]
2
```

Arrays nested inside documents:

```console
$ json-merge-arrays-zip --path payload.values resp_a.json resp_b.json
```

Stats as JSON:

```console
$ json-merge-arrays-zip '[1,2,3]' '[4,5]' --stats-json
{
  "arrays": 2,
  "input_lengths": [2, 3],
  "padded": false,
  "truncated": true,
  "tuples": 2
}
```

## Options

| Option | Description |
|---|---|
| `--jsonl` | Read stdin as JSONL: each line is one array |
| `--path P` | Dotted path to the array inside each document |
| `--pad` | Pad shorter arrays instead of truncating |
| `--fill V` | Fill value for `--pad` (parsed as JSON when possible) |
| `--strict-len` | Exit 2 when input lengths differ |
| `--require N` | Exit 2 if fewer than N tuples are produced |
| `--compact` | Emit compact JSON |
| `--stats-json` | Emit a JSON stats report instead of tuples |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | CLI or I/O error (bad JSON, missing path, non-array source) |
| 2 | `--strict-len` on unequal lengths, or `--require N` not met |

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
