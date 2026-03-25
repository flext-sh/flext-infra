# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.refactor.test_rope_project import (
        TestHookCallOrdering,
        TestInitRopeProject,
        TestRopeHooks,
        TestRopeProjectProperty,
        engine,
        fake_workspace,
    )
    from tests.refactor.test_rope_semantic import (
        TestGetClassBases,
        TestGetClassMethods,
        TestGetModuleClasses,
        TestGetModuleImports,
        models_resource,
        rope_workspace,
        services_resource,
    )
    from tests.refactor.test_rope_stubs import (
        test_rope_find_occurrences_import,
        test_rope_import,
        test_rope_rename_import,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestGetClassBases": ["tests.refactor.test_rope_semantic", "TestGetClassBases"],
    "TestGetClassMethods": ["tests.refactor.test_rope_semantic", "TestGetClassMethods"],
    "TestGetModuleClasses": [
        "tests.refactor.test_rope_semantic",
        "TestGetModuleClasses",
    ],
    "TestGetModuleImports": [
        "tests.refactor.test_rope_semantic",
        "TestGetModuleImports",
    ],
    "TestHookCallOrdering": [
        "tests.refactor.test_rope_project",
        "TestHookCallOrdering",
    ],
    "TestInitRopeProject": ["tests.refactor.test_rope_project", "TestInitRopeProject"],
    "TestRopeHooks": ["tests.refactor.test_rope_project", "TestRopeHooks"],
    "TestRopeProjectProperty": [
        "tests.refactor.test_rope_project",
        "TestRopeProjectProperty",
    ],
    "engine": ["tests.refactor.test_rope_project", "engine"],
    "fake_workspace": ["tests.refactor.test_rope_project", "fake_workspace"],
    "models_resource": ["tests.refactor.test_rope_semantic", "models_resource"],
    "rope_workspace": ["tests.refactor.test_rope_semantic", "rope_workspace"],
    "services_resource": ["tests.refactor.test_rope_semantic", "services_resource"],
    "test_rope_find_occurrences_import": [
        "tests.refactor.test_rope_stubs",
        "test_rope_find_occurrences_import",
    ],
    "test_rope_import": ["tests.refactor.test_rope_stubs", "test_rope_import"],
    "test_rope_rename_import": [
        "tests.refactor.test_rope_stubs",
        "test_rope_rename_import",
    ],
}

__all__ = [
    "TestGetClassBases",
    "TestGetClassMethods",
    "TestGetModuleClasses",
    "TestGetModuleImports",
    "TestHookCallOrdering",
    "TestInitRopeProject",
    "TestRopeHooks",
    "TestRopeProjectProperty",
    "engine",
    "fake_workspace",
    "models_resource",
    "rope_workspace",
    "services_resource",
    "test_rope_find_occurrences_import",
    "test_rope_import",
    "test_rope_rename_import",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
