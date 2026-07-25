"""Generic symbol-rename engine driven by a CSV substitution list.

One reusable engine for ANY ``old,new`` rename list — not tied to a specific
domain. Each CSV is a self-contained SSOT; this script is the single mechanism
that applies any of them. A new rename campaign adds a new CSV, never a new
script or a parallel ast-grep rule.

CSV schema: a header ``old,new`` then one ``old,new`` pair per line.

Application is prefix-safe and idempotent:
* pairs are applied longest-old-first so a short name (``files_read_yaml``)
  never shadows a longer one (``files_read_yaml_model``);
* pass 1 rewrites real code nodes via ``ast-grep run -p <old> -r <new>``
  (AST-aware, exact word boundaries), executed through ``u.Cli.run_raw``;
* pass 2 rewrites the same token inside comments and docstrings with a
  word-boundary regex, which ast-grep code patterns do not visit;
* a domain-first name never re-matches, so re-running is a no-op.

Usage:
    apply_renames.py --csv <list.csv> --check <dir>...   # report, no writes
    apply_renames.py --csv <list.csv> --apply <dir>...   # rewrite in place
"""  # ruff:ignore[implicit-namespace-package]

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from flext_cli import u

_SKIP_DIRS = {
    "__pycache__",
    "legado",
    "legacy",
    ".git",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
# Binary / generated extensions never rewritten (regenerable, not source text).
_SKIP_SUFFIXES = {
    ".db",
    ".pyc",
    ".pyo",
    ".so",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".whl",
    ".lock",
    ".bak",
}
_ASTGREP = "ast-grep"


def _pairs(csv_path: Path) -> list[tuple[str, str]]:
    """Load ``(old, new)`` pairs from ``csv_path``, longest-old first."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["old", "new"]:
            message = (
                f"{csv_path}: header must be exactly 'old,new', got {reader.fieldnames}"
            )
            raise SystemExit(message)
        rows = [(r["old"].strip(), r["new"].strip()) for r in reader]
    for old, new in rows:
        if not old or not new:
            message = f"{csv_path}: empty old/new in a row"
            raise SystemExit(message)
    return sorted(rows, key=lambda p: len(p[0]), reverse=True)


def _text_files(roots: list[str]) -> list[Path]:
    """Return every text file under ``roots``, skipping vendored/binary trees."""
    out: list[Path] = []
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if _SKIP_DIRS & set(path.parts):
                continue
            if path.suffix in _SKIP_SUFFIXES:
                continue
            out.append(path)
    return out


def _check(files: list[Path], pairs: list[tuple[str, str]]) -> int:
    """Report every ``old`` occurrence across all text files without writing."""
    hits = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for old, _ in pairs:
            for match in re.finditer(rf"\b{re.escape(old)}\b", text):
                line = text.count("\n", 0, match.start()) + 1
                u.Cli.emit_raw(f"{path}:{line}: {old}\n")
                hits += 1
    return hits


def _apply(files: list[Path], roots: list[str], pairs: list[tuple[str, str]]) -> int:
    """Rewrite Python code via ast-grep, then every text file via regex."""
    # Pass 1: AST-aware code rewrite via ast-grep over the .py roots only.
    for old, new in pairs:
        u.Cli.run_raw([_ASTGREP, "run", "-p", old, "-r", new, "-U", *roots])
    # Pass 2: word-boundary regex over ALL text files (comments, docstrings,
    # .toml lint messages, .md docs) that ast-grep code patterns never visit.
    changed = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_text = text
        for old, new in pairs:
            new_text = re.sub(rf"\b{re.escape(old)}\b", new, new_text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    """Parse arguments and run the check or apply pass over the CSV list."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="path to an old,new rename list")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report only")
    mode.add_argument("--apply", action="store_true", help="rewrite in place")
    parser.add_argument("roots", nargs="+", help="directories to scan")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        message = f"csv not found: {csv_path}"
        raise SystemExit(message)

    pairs = _pairs(csv_path)
    files = _text_files(args.roots)
    label = csv_path.stem

    if args.check:
        hits = _check(files, pairs)
        u.Cli.emit_raw(f"{label}: {hits} occurrence(s) across {len(files)} file(s)\n")
        return 1 if hits else 0

    changed = _apply(files, args.roots, pairs)
    u.Cli.emit_raw(f"{label}: rewrote {changed} file(s) across {len(files)} scanned\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
