"""Normalize module names that repeat their parent package prefix.

FLEXT naming law: the module stem must not repeat its package name —
``_rope/class_move.py`` under package ``_rope`` duplicates the namespace
segment. This repairer renames each offending module to the stripped stem
(``class_move.py``), rewrites every textual reference to the old dotted path
(imports, lazy maps, string spec references) across the governed tree, and
reports the movement for the follow-up ``make gen`` convergence.

Derived from the live tree, never from a hand-kept rename table; repeatable
until a fixpoint (second run renames nothing).

Usage:
    python scripts/normalize_module_names.py <package-root> [...]
    e.g. python scripts/normalize_module_names.py src/flext_infra/_utilities

SPDX-License-Identifier: MIT

Copyright (c) 2026 FLEXT Team. All rights reserved.
"""

from __future__ import annotations

import subprocess  # ruff: ignore[suspicious-subprocess-import] — git mv orchestration for governed renames
import sys
from pathlib import Path

_SOURCE_SUFFIX = "*.py"
_SOURCE_EXTENSION = ".py"


def _git_root() -> Path:
    """Walk up from the working directory to the enclosing git repository.

    Returns:
        The repository root (the first ancestor owning a ``.git`` entry).

    Raises:
        SystemExit: When no git repository encloses the working directory.

    """
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    message = "normalize: no git repository above the working directory"
    raise SystemExit(message)


def normalize_stem(package_dir: Path, stem: str) -> str:
    """Strip the parent package prefix from one module stem.

    Args:
        package_dir: The module's parent package directory.
        stem: The module's current file stem.

    Returns:
        The normalized stem (prefix stripped; unchanged when no repetition).

    """
    parent = package_dir.name.lstrip("_")
    if parent and stem.lower().startswith(parent.lower()):
        return stem[len(parent) :].lstrip("_") or stem
    return stem


def rename_map(package_root: Path) -> dict[Path, Path]:
    """Compute old→new paths for every module repeating its package prefix.

    Args:
        package_root: The tree whose immediate and nested packages are scanned.

    Returns:
        The rename map, empty when the tree is already normalized.

    """
    renames: dict[Path, Path] = {}
    for path in sorted(package_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        package_dir = path.parent
        new_stem = normalize_stem(package_dir, path.stem)
        if new_stem == path.stem:
            continue
        renames[path] = package_dir / f"{new_stem}{_SOURCE_EXTENSION}"
    return renames


def dotted_variants(root: Path, path: Path) -> list[str]:
    """Return the plausible dotted module identities for one source file.

    A path under ``<root>/<pkg>/<...>/<module>.py`` resolves as both the
    package-qualified spelling (``<pkg>.<...>.<module>``) and the bare
    relative spelling (``<...>.<module>``) — consumers import both forms.

    Returns:
        The dotted identities, longest first.

    """
    relative = path.relative_to(root).with_suffix("")
    parts = relative.parts
    qualified = ".".join(parts)
    bare = ".".join(parts[1:]) if len(parts) > 1 else qualified
    return [qualified, bare] if bare != qualified else [qualified]


def rewrite_references(
    tree_roots: list[Path],
    old_identities: list[str],
    new_identities: list[str],
) -> int:
    """Rewrite every textual reference to the old dotted paths.

    Args:
        tree_roots: Roots scanned for Python sources to patch.
        old_identities: The retired dotted module paths (longest first).
        new_identities: The replacement dotted paths (same order).

    Returns:
        The number of files changed.

    """
    changed = 0
    for tree in tree_roots:
        for path in sorted(tree.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            updated = text
            for old, new in zip(old_identities, new_identities, strict=True):
                updated = updated.replace(old, new)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                changed += 1
    return changed


def main(argv: list[str]) -> int:
    """Rename prefix-repeating modules and rewrite their references.

    Returns:
        Process exit code: 0 when the tree is normalized.

    """
    root = _git_root()
    packages = [Path(a) for a in argv] or [
        root
        / "src"
        / next(
            iter(
                child.name
                for child in (root / "src").iterdir()
                if child.is_dir() and not child.name.startswith(".")
            )
        )
    ]
    renames: dict[Path, Path] = {}
    for package in packages:
        renames.update(rename_map(package))
    if not renames:
        sys.stderr.write("normalize: tree already normalized\n")
        return 0
    tree_roots = [
        root / directory
        for directory in ("src", "tests", "scripts", "examples")
        if (root / directory).is_dir()
    ]
    for old, new in sorted(renames.items()):
        old_identities = dotted_variants(old.parents[1], old)
        new_identities = dotted_variants(new.parents[1], new)
        git_binary = Path(sys.executable).parents[1] / "git"
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [str(git_binary), "mv", str(old), str(new)],
            check=True,
        )
        changed = rewrite_references(tree_roots, old_identities, new_identities)
        sys.stderr.write(
            f"normalize: {old} -> {new} ({changed} files patched)\n",
        )
    sys.stderr.write(f"normalize: {len(renames)} modules renamed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
