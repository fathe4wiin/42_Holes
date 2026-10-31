"""Load francinette-tests.json. The file is a catalog, not source code."""

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "francinette-tests.json"
SCHEMA = "francinette-tests/1"


class CatalogError(Exception):
    """The catalog file cannot be used."""


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Parse the catalog. Strings are already decoded by the JSON parser."""
    if not CATALOG_PATH.is_file():
        raise CatalogError(f"Missing {CATALOG_PATH.name}")
    try:
        with CATALOG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"{CATALOG_PATH.name} is not valid JSON ({exc})") from exc
    if data.get("schema") != SCHEMA:
        raise CatalogError(
            f"Schema is {data.get('schema')!r}. This tester expects {SCHEMA}."
        )
    tests = data.get("tests")
    if not isinstance(tests, list):
        raise CatalogError("The catalog has no tests list.")
    return data


def project_names(data: dict) -> list[str]:
    """Known projects first, then anything else the catalog added."""
    counts = data.get("counts", {}).get("by_project", {})
    ordered = ["libft", "ft_printf", "get_next_line"]
    names = [name for name in ordered if name in counts]
    names.extend(sorted(name for name in counts if name not in names))
    return names


def project_tests(data: dict, project: str) -> list[dict]:
    return [case for case in data["tests"] if case.get("project") == project]
