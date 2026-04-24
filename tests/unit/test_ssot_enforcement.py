"""SSOT enforcement: no duplicate utility implementations across the workspace."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests import c, t


def _workspace_root() -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[c.Infra.Tests.SsotEnforcement.WORKSPACE_ROOT_PARENT_DEPTH]
    )


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
                f"{py_file.relative_to(_workspace_root())}"
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
                methods[node.name] = str(py_file.relative_to(_workspace_root()))
    return methods


@pytest.mark.parametrize(
    ("method", "canonical_package"),
    c.Infra.Tests.SsotEnforcement.SSOT_METHODS,
    ids=[m for m, _ in c.Infra.Tests.SsotEnforcement.SSOT_METHODS],
)
def test_no_duplicate_utility_implementations(
    method: str,
    canonical_package: str,
) -> None:
    """Each utility method must have exactly one implementation in its canonical package."""
    search_dirs = (
        _workspace_root() / "flext-core" / "src" / "flext_core",
        _workspace_root() / "flext-cli" / "src" / "flext_cli",
        _workspace_root() / "flext-infra" / "src" / "flext_infra",
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
    return _workspace_root() / project / "src" / package


@pytest.mark.parametrize(
    ("child", "parent"),
    c.Infra.Tests.SsotEnforcement.MRO_CHAIN,
    ids=[
        f"{child}_shadows_{parent}"
        for child, parent in c.Infra.Tests.SsotEnforcement.MRO_CHAIN
    ],
)
def test_no_utility_method_shadows_parent(child: str, parent: str) -> None:
    """A child _utilities/ MUST NOT re-implement a method from its parent facade."""
    parent_methods = _collect_utility_methods(_src_dir_for(parent))
    child_methods = _collect_utility_methods(_src_dir_for(child))
    allowed = c.Infra.Tests.SsotEnforcement.ALLOWED_OVERLAPS.get(
        (child, parent),
        frozenset(),
    )
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
