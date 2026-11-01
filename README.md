# 42_Holes

a TUI project to test your 42 project, made by student for students

It grades a libft against the current subject (v19.2), and an ft_printf against subject v12.1. Part 1 of libft is compared with libc, including calls where libc crashes. A crash there is a warning when your function returns, and a failure when yours crashes and libc does not.

## Run

Open the menu:

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash
```

Grade one project folder (the folder that contains the Makefile):

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash -s -- ~/libft
```

The script installs `textual` for your user if it is missing, then starts `holes.py`. A piped run keeps a checkout in `~/.cache/42_holes`.

From a clone you already have:

```sh
./run.sh
./run.sh ~/libft
```

## You need

Python 3 with pip, git, gcc, and make. `strlcpy`, `strlcat`, and `strnstr` are compared with libbsd (`-lbsd`).

## What the rows mean

| Result | Meaning |
| --- | --- |
| Pass | Your result matched the subject or libc. Both crashing on the same undefined call is a pass. |
| Fail | The call ran and differed, or your function crashed where libc did not. The process exits 1. |
| Warn | libc crashed and your function returned, or a call the subject does not define crashed. A warning does not fail the run. |

`ft_printf` compares stdout and the return value with `printf`. Mandatory is `cspdiuxX%` with no flags. Bonus is the flags `-0.` and a minimum width, then `#`, `+`, and space. `make bonus` is run before the bonus calls. `get_next_line` is listed. Its runner is not built yet.

After a graded run, `42_holes.log` in the project folder lists failures and warnings only.

## Keys

On the home card: `a` available tests, `g` guide, `c` credits, `q` quit. Arrows move. Enter opens the row.

On the results table: Escape back, `g` guide, `r` run again, `q` quit. Highlight a row to read its failures and warnings.
