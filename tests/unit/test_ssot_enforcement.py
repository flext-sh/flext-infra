"""SSOT enforcement: no duplicate utility implementations across the workspace."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests import t

WORKSPACE = Path(__file__).resolve().parents[3]  # flext/ root

# Methods that must have exactly ONE implementation across the workspace.
SSOT_METHODS = [
    ("sha256_content", "flext_cli"),
    ("sha256_file", "flext_cli"),
    ("json_read", "flext_cli"),
    ("json_write", "flext_cli"),
    ("json_parse", "flext_cli"),
]

# MRO parent chain: child -> parent.  A child MUST NOT re-implement a method
# from any of its parents' _utilities/ directories.
_MRO_CHAIN: t.SequenceOf[t.Pair[str, str]] = [
    ("flext_cli", "flext_core"),
    ("flext_infra", "flext_core"),
    ("flext_infra", "flext_cli"),
]

# Methods that legitimately have different semantics across packages (e.g.,
# ``run`` for CLI execution vs service execution, ``to_str`` with different
# input types).  Keyed by (child_package, parent_package) -> frozenset of names.
_ALLOWED_OVERLAPS: t.MappingKV[t.Pair[str, str], frozenset[str]] = {
    ("flext_cli", "flext_core"): frozenset({"run", "to_str"}),
}


def _find_method_definitions(
    method_name: str,
    search_dirs: t.SequenceOf[Path],
) -> t.MutableSequenceOf[str]:
    """Find all static/class methods with exact name in _utilities/ dirs."""
    found: t.MutableSequenceOf[str] = []
    for search_dir in search_dirs:
        utils_dir = search_dir / "_utilities"
        if not utils_dir.exists():
            continue
        for py_file in utils_dir.rglob("*.py"):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            found.extend(
                f"{py_file.relative_to(WORKSPACE)}"
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == method_name
            )
    return found


def _collect_utility_methods(src_dir: Path) -> t.MutableMappingKV[str, str]:
    """Return {method_name: relative_path} for all public methods in _utilities/."""
    utils_dir = src_dir / "_utilities"
    methods: t.MutableMappingKV[str, str] = {}
    if not utils_dir.exists():
        return methods
    for py_file in utils_dir.rglob("*.py"):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                methods[node.name] = str(py_file.relative_to(WORKSPACE))
    return methods


@pytest.mark.parametrize(
    ("method", "canonical_package"),
    SSOT_METHODS,
    ids=[m for m, _ in SSOT_METHODS],
)
def test_no_duplicate_utility_implementations(
    method: str,
    canonical_package: str,
) -> None:
    """Each utility method must have exactly one implementation in its canonical package."""
    search_dirs = (
        WORKSPACE / "flext-core" / "src" / "flext_core",
        WORKSPACE / "flext-cli" / "src" / "flext_cli",
        WORKSPACE / "flext-infra" / "src" / "flext_infra",
    )
    definitions = _find_method_definitions(method, search_dirs)
    canonical_defs = [d for d in definitions if canonical_package in d]
    duplicate_defs = [d for d in definitions if canonical_package not in d]

    assert len(canonical_defs) >= 1, (
        f"{method} not found in canonical package {canonical_package}"
    )
    assert len(duplicate_defs) == 0, (
        f"{method} has duplicate implementations outside {canonical_package}: {duplicate_defs}"
    )


def _src_dir_for(package: str) -> Path:
    """Resolve the src directory for a flext package name."""
    project = package.replace("_", "-")
    return WORKSPACE / project / "src" / package


@pytest.mark.parametrize(
    ("child", "parent"),
    _MRO_CHAIN,
    ids=[f"{c}_shadows_{p}" for c, p in _MRO_CHAIN],
)
def test_no_utility_method_shadows_parent(child: str, parent: str) -> None:
    """A child _utilities/ MUST NOT re-implement a method from its parent facade."""
    parent_methods = _collect_utility_methods(_src_dir_for(parent))
    child_methods = _collect_utility_methods(_src_dir_for(child))
    allowed = _ALLOWED_OVERLAPS.get((child, parent), frozenset())
    collisions = {
        name: (child_methods[name], parent_methods[name])
        for name in child_methods
        if name in parent_methods and name not in allowed
    }
    assert len(collisions) == 0, (
        f"{child} _utilities/ shadows {len(collisions)} method(s) from {parent}: "
        + ", ".join(
            f"{name} (child={cp}, parent={pp})" for name, (cp, pp) in collisions.items()
        )
    )
