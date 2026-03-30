# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.refactor import (
        test_rope_semantic as test_rope_semantic,
        test_rope_stubs as test_rope_stubs,
    )
    from tests.refactor.test_rope_semantic import (
        TestFindDefinitionOffset as TestFindDefinitionOffset,
        TestGetClassBases as TestGetClassBases,
        TestGetClassMethods as TestGetClassMethods,
        TestGetModuleClasses as TestGetModuleClasses,
        TestGetModuleImports as TestGetModuleImports,
        models_resource as models_resource,
        rope_workspace as rope_workspace,
        services_resource as services_resource,
    )
    from tests.refactor.test_rope_stubs import (
        test_rope_find_occurrences_import as test_rope_find_occurrences_import,
        test_rope_import as test_rope_import,
        test_rope_rename_import as test_rope_rename_import,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestFindDefinitionOffset": [
        "tests.refactor.test_rope_semantic",
        "TestFindDefinitionOffset",
    ],
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
    "test_rope_semantic": ["tests.refactor.test_rope_semantic", ""],
    "test_rope_stubs": ["tests.refactor.test_rope_stubs", ""],
}

_EXPORTS: Sequence[str] = [
    "TestFindDefinitionOffset",
    "TestGetClassBases",
    "TestGetClassMethods",
    "TestGetModuleClasses",
    "TestGetModuleImports",
    "models_resource",
    "rope_workspace",
    "services_resource",
    "test_rope_find_occurrences_import",
    "test_rope_import",
    "test_rope_rename_import",
    "test_rope_semantic",
    "test_rope_stubs",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
