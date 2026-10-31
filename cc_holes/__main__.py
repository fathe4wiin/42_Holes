"""python -m cc_holes launches the UI. A path argument runs libft and prints the rows."""

import sys
from pathlib import Path

from cc_holes.app import HolesApp
from cc_holes.runner import Done, Log, Update, run_libft


def cli(folder: str) -> int:
    code = 0
    for event in run_libft(Path(folder)):
        if isinstance(event, Log):
            print(event.text)
        elif isinstance(event, Update):
            row = event.row
            print(
                f"{row.function:<16} pass {row.passed:<4} fail {row.failed:<4} "
                f"warn {row.warned:<4} {row.note}"
            )
        elif isinstance(event, Done):
            if event.error:
                print(event.error)
                return 2
            print(
                f"\npass {event.passed}  fail {event.failed}  warn {event.warned}"
            )
            if event.missing:
                print("missing from libft.h: " + ", ".join(event.missing))
            if event.log_path:
                print(f"log: {event.log_path}")
            code = 1 if event.failed else 0
    return code


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        HolesApp().run()
        return 0
    if args[0] in {"-h", "--help"}:
        print("python3 holes.py")
        print("python3 holes.py /path/to/libft")
        return 0
    return cli(args[0])


if __name__ == "__main__":
    raise SystemExit(main())
