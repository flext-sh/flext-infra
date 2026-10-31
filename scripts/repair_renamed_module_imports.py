"""Repair imports of modules renamed inside one governed source tree.

For every fully-qualified ``from <module> import ...`` statement whose module
no longer resolves, the repairer elects the renamed module whose declared
top-level classes intersect the imported names, then rewrites the statement.
Derived from live content, never from a hand-kept rename table; repeatable
until a fixpoint (second run rewrites nothing).

Usage:
    python scripts/repair_renamed_module_imports.py <source-root> [...]
    e.g. python scripts/repair_renamed_module_imports.py flext-infra/src

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

CLASS_RE = re.compile(r"^class (\w+)", re.MULTILINE)
IMPORT_RE = re.compile(r"from (flext(?:_\w+)*(?:\.\w+)+) import")


def module_classes(path: Path) -> set[str]:
    """Return the top-level class names one module declares."""
    try:
        return set(CLASS_RE.findall(path.read_text(encoding="utf-8")))
    except OSError:
        return set()


def module_exists(root: Path, dotted: str) -> bool:
    """Whether one dotted module resolves inside a source root.

    Returns:
        The resulting ``bool``.

    """
    path = root.joinpath(*dotted.split("."))
    return path.with_suffix(".py").exists() or (path / "__init__.py").exists()


def bound_names(text: str, dotted: str) -> set[str]:
    """Return the identifiers one import statement binds."""
    groups = re.findall(rf"from {re.escape(dotted)} import \(?([^)\n]*)", text)
    bound: set[str] = set()
    for group in groups:
        for name in group.split(","):
            identifier = name.strip().rstrip(",").split(" as ")[0]
            if identifier and identifier.isidentifier():
                bound.add(identifier)
    return bound


def stem_variants(root: Path, dotted: str) -> list[str]:
    """Return existing stem variants of one unresolvable module.

    The rename wave normalizes ``rope_<x>`` to ``<x>``; a mid-flight tree has
    both directions, so the variant that exists on disk is the destination.

    """
    parent, _, stem = dotted.rpartition(".")
    variants = (stem.removeprefix("rope_"), f"rope_{stem}")
    return [
        f"{parent}.{other}"
        for other in variants
        if other != stem and module_exists(root, f"{parent}.{other}")
    ]


def renamed_destination(
    dotted: str,
    text: str,
    packages: list[Path],
    index: dict[frozenset[str], list[Path]],
) -> str | None:
    """Return the single module whose declared classes the import binds.

    Returns:
        The destination dotted path, or ``None`` when absent or ambiguous.

    """
    bound = bound_names(text, dotted)
    if not bound:
        return None
    tail = dotted.rpartition(".")[2]
    matches = [
        path
        for classes, paths in index.items()
        if bound & classes
        for path in paths
        if f"/{tail}." in str(path) or path.stem == tail
    ]
    if len(matches) != 1:
        return None
    candidate = matches[0]
    pkg_root = next((pkg for pkg in packages if candidate.is_relative_to(pkg)), None)
    if pkg_root is None:
        return None
    relative = candidate.relative_to(pkg_root)
    return ".".join([relative.parts[0], *relative.with_suffix("").parts[1:]])


def repaired_text(
    text: str, packages: list[Path], index: dict[frozenset[str], list[Path]]
) -> str:
    """Return one module's source with every stale import rewritten."""
    changed = text
    for match in IMPORT_RE.finditer(text):
        dotted = match.group(1)
        if any(module_exists(root, dotted) for root in packages):
            continue
        for root in packages:
            for variant in stem_variants(root, dotted):
                changed = changed.replace(dotted, variant)
        if changed != text:
            continue
        destination = renamed_destination(dotted, text, packages, index)
        if destination is not None:
            changed = changed.replace(dotted, destination)
    return changed


def main(argv: list[str]) -> int:
    """Rewrite stale module imports to their renamed destinations.

    Returns:
        Process exit code: always 0; findings are reported on stdout.

    """
    roots = [Path(a) for a in argv] or [Path.cwd()]
    packages = [root for root in roots if root.is_dir()]
    files = [path for pkg in packages for path in pkg.rglob("*.py")]
    index: dict[frozenset[str], list[Path]] = defaultdict(list)
    for path in files:
        declared = module_classes(path)
        if declared:
            index[frozenset(declared)].append(path)
    fixed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        changed = repaired_text(text, packages, index)
        if changed != text:
            path.write_text(changed, encoding="utf-8")
            fixed += 1
            sys.stdout.write(f"repaired {path}\n")
    sys.stdout.write(f"rewrote {fixed} files\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
