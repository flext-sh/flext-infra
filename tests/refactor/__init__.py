# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra.test_rope_semantic import (
        TestFindDefinitionOffset,
        TestGetClassBases,
        TestGetClassMethods,
        TestGetModuleClasses,
        TestGetModuleImports,
        models_resource,
        rope_workspace,
        services_resource,
    )
    from flext_infra.test_rope_stubs import (
        test_rope_find_occurrences_wrapper,
        test_rope_project_wrapper,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_rope_semantic": (
            "TestFindDefinitionOffset",
            "TestGetClassBases",
            "TestGetClassMethods",
            "TestGetModuleClasses",
            "TestGetModuleImports",
            "models_resource",
            "rope_workspace",
            "services_resource",
        ),
        ".test_rope_stubs": (
            "test_rope_find_occurrences_wrapper",
            "test_rope_project_wrapper",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)

__all__ = [
    "TestFindDefinitionOffset",
    "TestGetClassBases",
    "TestGetClassMethods",
    "TestGetModuleClasses",
    "TestGetModuleImports",
    "models_resource",
    "rope_workspace",
    "services_resource",
    "test_rope_find_occurrences_wrapper",
    "test_rope_project_wrapper",
]
