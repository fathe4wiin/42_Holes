# 42_Holes

a TUI project to test your 42 project, made by student for students

It grades one project folder per run, by circle. Circle 00 is libft. Circle 01 is get_next_line, ft_printf, and push_swap. Circle 02 is py-module-00 through py-module-04.

## Run

Open the menu:

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash
```

Grade one folder:

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash -s -- ~/libft
```

The script installs `textual` for your user if it is missing, then starts `holes.py`. A piped run keeps a checkout in `~/.cache/42_holes`.

From a clone you already have:

```sh
./run.sh
./run.sh ~/libft
python3 holes.py
python3 holes.py ~/push_swap
```

Exit 1 if any call failed. Exit 2 if the build or the setup failed. A warning does not fail the run.

## You need

Python 3 with pip, git, gcc, and make. `strlcpy`, `strlcat`, and `strnstr` are compared with libbsd (`-lbsd`).

push_swap and get_next_line also need valgrind. A leak is a fail. libft and ft_printf are not leak-checked.

A Python module also wants `flake8` on that interpreter. A missing flake8 is one warning.

libft, ft_printf, and push_swap want a Makefile. get_next_line wants `get_next_line.c` and `get_next_line.h` at the folder root. A Python module wants the exercise files in `ex0/`, `ex1/`, and so on. A copy at the folder root is also accepted.

## What is graded

| Circle | Project | Subject |
| --- | --- | --- |
| 00 | libft | v19.2 |
| 01 | get_next_line | v14.3 |
| 01 | ft_printf | v12.1 |
| 01 | push_swap | v1.2 |
| 02 | py-module-00 Growing Code | v3.0 |
| 02 | py-module-01 Code Cultivation | v3.2 |
| 02 | py-module-02 Garden Guardian | v3.0 |
| 02 | py-module-03 Data Quest | v3.1 |
| 02 | py-module-04 Data Archivist | v3.0 |

libft part 1 must match libc, including a crash. Both crashing on the same undefined call is a pass. libc crashed and your function returned: warn. Your function crashed and libc did not: fail. The `is*` functions must return 0 or 1. Lists are mandatory part 3.

ft_printf compares stdout and the return value with `printf`. Mandatory is `cspdiuxX%` with no flags. Bonus is the flags `-0.` and a minimum width, then `#`, `+`, and space. Bonus fails are still reported when mandatory is not perfect.

get_next_line is compiled at `BUFFER_SIZE` 1 and 42. The newline stays on the line. A pipe whose write end stays open must return at the newline. A missing bonus is a warning. Valgrind checks a full read at `BUFFER_SIZE` 1. The open pipe is skipped, because the leftover buffer is still in use.

push_swap is checked with `subjects/checker_linux`. No arguments prints nothing. `push_swap 4 5` is two integers and is graded as a sort. Errors are `Error` and a newline on stderr, with nothing on stdout. Three numbers or fewer must also be the shortest sequence. `--bench` writes the disorder, the strategy name, and the complexity to stderr. 100 numbers must stay under 2000 operations. 500 under 12000. Valgrind checks the small runs. `make bonus` builds `checker`. A missing checker is a warning. The checker prints `OK` only when stack a is sorted and stack b is empty. `checker 99 1 2 3 4` with `pb` is `KO`. An empty line, a trailing space, or an instruction with no newline is `Error`.

Each Python exercise is one row. `flake8` runs on the `*.py` files. A violation is a fail. The module is detected from `ex0/` plus its first exercise file. Press `g` in the TUI for the per-exercise rules.

## What the rows mean

| Result | Meaning |
| --- | --- |
| Pass | Your result matched the subject, libc, or `checker_linux`. Both crashing on the same undefined call is a pass. |
| Fail | The call ran and differed, your function crashed where libc did not, or valgrind reported a leak. The process exits 1. |
| Warn | libc crashed and your function returned, a call the subject does not define crashed, or a bonus file is missing. A warning does not fail the run. |

After a graded run, `42_holes.log` in the project folder lists failures and warnings only.

## Keys

On the home card: `a` available tests, `g` guide, `c` credits, `q` quit. Arrows move. Enter opens the row.

`a` opens the circle list. Enter on circle 00 or 01 opens that circle's projects. Enter on circle 02 opens the Python modules. Escape goes back one screen.

On the results table: Escape back, `g` guide, `r` run again, `q` quit. Highlight a row to read its failures and warnings.

## Coming next

Circle 02 is its own screen so the Python list can grow to about 12 modules. The next modules are added in `PY_MODULES` in `cc_holes/py_run.py`. py-module-00 through py-module-04 are the ones graded today. A module that is not in that list is not graded.
