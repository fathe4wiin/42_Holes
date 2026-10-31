# francinette-tests.json

Parse contract for `francinette-tests.json` (`schema` is `francinette-tests/1`).

Load the whole file with a JSON parser. Do not scan it as text. After parsing, every string is already decoded: `\u000b` is one vertical-tab character, not the six characters `\u000b`.

```python
import json
data = json.load(open("francinette-tests.json"))
cases = data["tests"]
```

`data["counts"]` is the summary. `data["errors"]` is empty when the extract succeeded. `data["tests"]` is the only list of cases. There are no other arrays of cases.

## Top-level object

| Key | Use it for |
| --- | --- |
| `schema` | Must be `francinette-tests/1`. Stop if it is something else. |
| `tests` | The cases. Array order is source order. |
| `counts.total` | Length of `tests`. |
| `counts.by_project` | `libft`, `ft_printf`, `get_next_line`. |
| `counts.by_suite` | Keys look like `libft/fsoares`. |
| `counts.by_kind` | How many cases of each `kind`. |
| `fields` | Keys present on every case. |
| `optional` | Keys present only on some cases. Absent means "not set". They are never JSON `null`. |
| `kinds` | Short description of each `kind`. |
| `notes` | Catalog-wide warnings. Not per-case notes. |

Projects in this file: `libft`, `ft_printf`, `get_next_line`. There is no pipex.

## One case

Every object in `tests` has these keys:

| Key | JSON type | Meaning |
| --- | --- | --- |
| `id` | string | Unique. Format: `{project}/{suite}/{function}/{NNNN}`. The number is 4 digits and is only unique inside that function. Use `id` as the identity. |
| `project` | string | `libft`, `ft_printf`, or `get_next_line`. |
| `suite` | string | Which tester the case came from. See the suite table below. |
| `function` | string | `ft_atoi`, `ft_printf`, `get_next_line`, and the other `ft_*` names. |
| `part` | string | `part1`, `part2`, `bonus`, `additional`, `extra`, or `mandatory`. |
| `index` | string | The case number inside that suite. Always a string, even when it looks like `1`. Not unique. `ft_printf` restarts `index` in every `group`. Two `ft_memset` cases are both index `4`. |
| `kind` | string | How to judge the case. One of the kinds below. |
| `call` | string | Human-readable invocation. Display this. Do not eval it. |
| `args` | array | The inputs. Empty array when the case has no separated inputs. |
| `expected` | object or `null` | The oracle. `null` means the file does not store a literal oracle. |
| `source` | string | Path of the original test, relative to the francinette-image repo. |
| `line` | number | 1-based line in `source`. |
| `bonus` | boolean | `true` only when `part` is `bonus`. List functions (`ft_lst*`) are filed as `bonus` here. Libft v19.2 treats them as mandatory. |

Optional keys, omit-if-absent:

| Key | When it appears |
| --- | --- |
| `group` | printf category (`d`, `s`, `x`, `X`, `%`, `+`, `-`, `.`, `#`, `0`, `space`, `mix`, …) or a get_next_line file group (`files/nl`, `Invalid fd`, `multiple fd`, `stdin`). |
| `stream` | `stdout` or `stderr`. Only on `war-machine` cases. |
| `notes` | One sentence about that case. |
| `generator` | The loop or fuzzer that was not expanded into separate cases. |
| `body` | C source of an alelievr check, a hardcore driver, or a multi-line war-machine branch. |

## `args` and `expected`

Both use the same value object: `{"type": "<type>", "value": <value>}`.

`expected` may instead be JSON `null`.

`value` for `int` is a **string of decimal digits**, optional leading `-`. It is never a JSON number. `0x` forms were already converted. Read it with a base-10 integer parse.

`value` for `bool` is the string `"true"` or `"false"`, not a JSON boolean.

`value` for `char` is a string of one character. That character may be a newline, a NUL (`"\u0000"`), or any other byte.

`value` for `str` is a string. It may be empty, and it may contain NULs and newlines. Keep them. Do not trim.

`value` for `null`, and for expected type `end`, is JSON `null`.

`value` for `lines` is an array of strings. The trailing NULL of a `ft_split` result is already removed. `["hello!"]` means one string, then NULL.

`value` for `expr` is C source text left as text (`INT_MAX`, `sizeof(long)`, `'a' - 1`, `dest`, `mem`, `ptr`, `fd`, `fd[0]`). Do not eval unknown expressions.

### Arg types

| type | value | How to pass it |
| --- | --- | --- |
| `str` | string | `char *` pointing at those bytes, then a NUL after the JSON string. A NUL inside the string is a real `'\0'` in the middle. |
| `char` | one character | Pass that byte as an `int` argument (`ft_isalpha`, `ft_memset` fill, and so on). |
| `int` | decimal string | Pass `int(value)`. |
| `null` | `null` | Pass a NULL pointer. |
| `expr` | C text | See the known symbols below. Anything else is not a literal input. |

### Expected types

| type | Pass condition |
| --- | --- |
| `str` | Returned string equals `value`, including a trailing newline when `value` has one. |
| `char` | Returned byte equals `value`. |
| `int` | Returned number equals `int(value)`. |
| `bool` | `value` `"true"` means the return is non-zero. `"false"` means the return is zero. This is not a check for the number `1`. |
| `null` | Return pointer is NULL. |
| `lines` | `ft_split`-style array equals `value`, then a NULL slot. |
| `stdout` | Those exact bytes were written to stdout. Do not add or strip a newline. |
| `stderr` | Same, on stderr. |
| `end` | `get_next_line` returns NULL. |
| `expr` | Not a literal. The suite compared against another buffer (often the libc twin, such as `mem_std`). |
| JSON `null` | No stored oracle. The `kind` says what to compare against. |

If both `expected.type` and `stream` exist, they name the same stream. `stream` is only present for war-machine. `ft_put*_fd` cases from fsoares use `expected.type` `stdout` and have no `stream` key. That stdout is the bytes written to the fd.

## Known `expr` symbols

| value | Meaning |
| --- | --- |
| `INT_MAX` | `2147483647` |
| `INT_MIN` | `-2147483648` |
| `EOF` | Only with the note `String of one byte. That byte is EOF, then NUL.` Build a 2-byte buffer: `(char)EOF`, then `'\0'`. Pass that buffer. |
| `e` in a Tripouille `call` | The note says `e` is the five-byte string tab, newline, vertical tab, form feed, carriage return: `"\t\n\v\f\r"`. The arg itself may still be an expression such as `(e + "1").c_str()`. |

Any other `expr` (`dest`, `mem`, `ptr`, `src`, `sizeof(long)`, `'a' - 1`, `fd`, `fd[0]`, `add`) is harness state from the original C. Do not invent a buffer for it unless a rule below names that case.

## `kind`

### `compare_libc`

Call the student's function and the libc function with the same args. Same return, and same bytes written into any output buffer.

`function` is `ft_atoi`. The libc name is `atoi`. For `ft_printf`, the libc function is `printf`. `args[0]` is the format string. The rest are the values. Compare both the written stdout and the returned `int`.

`expected` is set when the suite hard-coded the result (`lines` for `ft_split`, `stdout` for the `ft_put*` family). When `expected` is `null`, libc is the oracle.

Skip the case when any arg has type `expr` and it is not in the known-symbol table. `ft_atoi(INT_MAX)` is runnable. `ft_memset(mem, 'x', 0)` is not, because `mem` is a harness buffer.

Example, runnable, oracle is libc:

```json
{
  "id": "libft/fsoares/ft_atoi/0001",
  "function": "ft_atoi",
  "kind": "compare_libc",
  "call": "ft_atoi(\" \\t\\u000b\\n\\r\\f123\")",
  "args": [{ "type": "str", "value": " \t\u000b\n\r\f123" }],
  "expected": null
}
```

The parsed string value is space, tab, vertical tab, newline, CR, form feed, then `123`.

Example, oracle is stored:

```json
{
  "function": "ft_split",
  "kind": "compare_libc",
  "args": [
    { "type": "str", "value": "hello!" },
    { "type": "char", "value": " " }
  ],
  "expected": { "type": "lines", "value": ["hello!"] }
}
```

### `expression`

Tripouille. `call` is the check that was written in C++. `args` and `expected` are filled only when that check was a direct call.

- Args all literal, `expected.type` is `bool`, `int`, `char`, `str`, or `null`: call `function` with `args` and compare to `expected`.
- Otherwise show `call` and do not eval it. `ft_lst*` checks are often in this second group (`call` is `l->content == (void*)1` with empty `args`).

```json
{
  "function": "ft_isalpha",
  "kind": "expression",
  "call": "ft_isalpha('a' - 1)",
  "args": [{ "type": "expr", "value": "'a' - 1" }],
  "expected": { "type": "bool", "value": "false" }
}
```

`'a' - 1` is an expression. Either parse that tiny pattern (`char` minus an int) or skip it. A literal case looks like `ft_isalpha('a')` with arg type `char` and expected bool `"true"`.

```json
{
  "function": "ft_atoi",
  "kind": "expression",
  "call": "ft_atoi((e + \"1\").c_str())",
  "args": [{ "type": "expr", "value": "(e + \"1\").c_str()" }],
  "expected": { "type": "int", "value": "1" },
  "notes": "Identifier e is the string \"\\t\\n\\v\\f\\r\"."
}
```

Build `e + "1"` from the note, then compare the return to `1`.

### `stdout`

war-machine. `expected.value` is the exact bytes of that case. `stream` is `stdout` or `stderr`. Odd-numbered `ft_putchar_fd`, `ft_putstr_fd`, `ft_putendl_fd`, and `ft_putnbr_fd` cases use stderr. Compare bytes. A missing final newline is intentional.

```json
{
  "function": "ft_atoi",
  "kind": "stdout",
  "call": "ft_atoi(\"0\")",
  "args": [{ "type": "str", "value": "0" }],
  "expected": { "type": "stdout", "value": "0" },
  "stream": "stdout"
}
```

If `call` contains ` for `, it is one case for a whole loop, not one call. Example: `ft_isalpha(i) for i in 0..47`. The range is inclusive. ` exclusive` in the call means the end is excluded. `expected` is the concatenated output of every iteration, printed the way that function's `main.c` prints. Use `source` and `line` for the print wrapper. `body`, when present, is that branch.

### `lines`

`get_next_line`. One object is one read.

Keep array order inside a `group`. Do not sort by `index`.

`group` starting with `files/` is one file, opened once, then the cases in order:

1. Walk the cases in that group in array order.
2. `expected.type` `str`: the next `get_next_line` return equals `value`.
3. `expected.type` `end`: the next return is NULL.

Rebuild a missing fixture by concatenating the `str` values in order and writing nothing for `end`. Open that buffer as the fd. Exception: `files/42_with_nl` contains both branches of a `BUFFER_SIZE` check. Use this sequence when `BUFFER_SIZE` is not 42: the case at line 61 (`index` `1`, the long line), then the case whose expected value is `"1"`, then the following `end`. When `BUFFER_SIZE` is 42: the long line, then a raw one-byte read of `'1'` (that read is not a case), then the `end` at line 64.

`Invalid fd`: each case is independent. Arg `1000` and arg `-1` must return NULL. The third case's arg is the expr `fd` (an open of `files/empty` passed to `get_next_line` with a NULL line pointer in the original). Treat a NULL output pointer as a failure if you do not model that call.

`stdin`: ten reads on fd 0. The bytes are the same sequence as `files/alternate_line_nl_with_nl`.

`multiple fd` (bonus): 19 reads. Map the expr args as follows, and keep the integer args as invalid fds that must return NULL.

| arg value | file |
| --- | --- |
| `fd[0]` | `files/41_with_nl` |
| `fd[1]` | `files/42_with_nl` |
| `fd[2]` | `files/43_with_nl` |
| `fd[3]` | `files/nl` |
| integer `1000` … `1007` | invalid fd, expected type `end` |

```json
{
  "kind": "lines",
  "call": "get_next_line(fd)",
  "args": [{ "type": "expr", "value": "fd" }],
  "expected": { "type": "str", "value": "\n" },
  "group": "files/nl"
}
```

The next case in that group has `expected.type` `end`.

### `sandbox` and `speed`

alelievr. `call` is the explanation (`basic memset test (fill a buffer with 'A')`). `args` is empty. `expected` is `null`. `body` is the C check, not a list of inputs. `speed` compares timing against libc. These are not data cases. Show `call`, or compile `body` from `source`.

### `fuzzer` and `generated`

One record per fuzz driver or unexpanded loop. `generator` is the description. `index` is `fuzz` or `generated`. There is no input list to run. Skip them in an automated run, or compile the original file at `source`.

`generated` is only the random `fsoares` loops (`ft_strlen`, `ft_memcpy`, `ft_memchr`). Fixed loops were already expanded into normal cases.

### `crash` and `guard`

`fsoares` only. `index` is `crash` or `guard`. `call` is `libc_crash_atoi()` or `part2_guard_substr()`. `args` is empty. The original helper lives outside this JSON. Skip them, or open `source`.

`crash`: the student function must match libc on inputs where libc itself crashes.

`guard`: NULL pointer and allocation failure.

## Suites

| project | suite | What a case is |
| --- | --- | --- |
| `libft` | `fsoares` | `compare_libc`, plus `crash`, `guard`, and three `generated` loops. |
| `libft` | `Tripouille` | `expression`. |
| `libft` | `war-machine` | `stdout` with exact bytes. `part` comes from the folder: `part1`, `part2`, `bonus`, `additional`. |
| `libft` | `alelievr` | `sandbox` or `speed`. `index` is a name such as `basic`. |
| `libft` | `alelievr-hardcore` | One `fuzzer` per old libc function. |
| `ft_printf` | `printfTester` | `compare_libc` against `printf`. Filter with `group`. |
| `ft_printf` | `ft_printf_test` | Same. `group` is the C function that contains the case (`test_pft_string`, `generated_test`, `main`, …). `bonus` is true for cases inside the bonus ifdef. |
| `ft_printf` | `unit-test` | One `generated` record. Converters are in `group` (`cspdiuxX`). Sample strings are in `args`. Formats are built at runtime. |
| `get_next_line` | `gnlTester` | `lines`. `part` is `mandatory` or `bonus`. |

`part` values you will see:

| part | Where |
| --- | --- |
| `part1`, `part2` | Current libft mandatory functions. |
| `bonus` | `ft_lst*` and get_next_line bonus. |
| `additional` | Old war-machine functions (`ft_islower`, `ft_strcapitalize`, …). |
| `extra` | alelievr functions that are not in part1, part2, or the list API (`ft_memccpy`, `ft_strcat`, …). |
| `mandatory` | `ft_printf` cases that are not bonus, and mandatory `get_next_line`. |

## Filters

```python
atoi = [t for t in cases if t["function"] == "ft_atoi" and t["suite"] == "fsoares"]
printf_d = [t for t in cases if t["suite"] == "printfTester" and t.get("group") == "d"]
runnable = [
    t for t in cases
    if t["kind"] in {"compare_libc", "expression", "stdout", "lines"}
    and all(a["type"] != "expr" or a["value"] in {"INT_MAX", "INT_MIN", "EOF"} for a in t["args"])
]
```

Identity is `id`. Display text is `call`. Inputs are `args`. Oracle is `expected`, or libc when `expected` is `null` and `kind` is `compare_libc`.

## Do this, in order

1. Reject the file if `schema` is not `francinette-tests/1`.
2. Read `tests`. Ignore every other top-level key except as documentation.
3. Group by `project`, then `function`, then `suite`.
4. Run a case only when its `kind` and its arg types are in the runnable rules above.
5. Compare bytes exactly for `stdout`, `stderr`, and `str`.
6. For `get_next_line`, replay one `group` in array order.
7. Skip `sandbox`, `speed`, `fuzzer`, `generated`, `crash`, and `guard`, and skip cases whose `expr` args are not in the known-symbol table.
