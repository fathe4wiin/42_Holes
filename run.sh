#!/usr/bin/env bash
# Launch 42_Holes. From a checkout this uses that folder.
# Piped from curl, it clones https://github.com/fathe4wiin/42_Holes and runs that.
set -euo pipefail

REPO="https://github.com/fathe4wiin/42_Holes.git"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/42_holes"

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "42_Holes needs $1."
}

need python3
need git
need gcc
need make

root=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fi

if [[ ! -f "${root}/holes.py" ]]; then
  if [[ ! -d "$CACHE/.git" ]]; then
    mkdir -p "$(dirname -- "$CACHE")"
    git clone --depth 1 "$REPO" "$CACHE"
  else
    git -C "$CACHE" pull --ff-only --quiet
  fi
  root="$CACHE"
fi

if ! python3 -c 'import textual' >/dev/null 2>&1; then
  python3 -m pip install --user 'textual>=8.2' \
    || die "Could not install textual. Run: python3 -m pip install --user 'textual>=8.2'"
fi

# curl | bash reads this script on stdin. Redirect on the exec line so
# bash does not try to read the rest of the script from the terminal.
launch() {
  if [[ -t 0 ]]; then
    exec python3 "$root/holes.py" "$@"
  fi
  exec python3 "$root/holes.py" "$@" </dev/tty \
    || die "42_Holes needs a terminal."
}
launch "$@"
