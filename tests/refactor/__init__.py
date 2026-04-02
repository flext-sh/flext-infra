# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from tests.refactor import test_rope_semantic, test_rope_stubs
    from tests.refactor.test_rope_semantic import (
        TestFindDefinitionOffset,
        TestGetClassBases,
        TestGetClassMethods,
        TestGetModuleClasses,
        TestGetModuleImports,
        models_resource,
        rope_workspace,
        services_resource,
    )
    from tests.refactor.test_rope_stubs import (
        test_rope_find_occurrences_wrapper,
        test_rope_module_syntax_error_wrapper,
        test_rope_project_wrapper,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "TestFindDefinitionOffset": "tests.refactor.test_rope_semantic",
    "TestGetClassBases": "tests.refactor.test_rope_semantic",
    "TestGetClassMethods": "tests.refactor.test_rope_semantic",
    "TestGetModuleClasses": "tests.refactor.test_rope_semantic",
    "TestGetModuleImports": "tests.refactor.test_rope_semantic",
    "models_resource": "tests.refactor.test_rope_semantic",
    "rope_workspace": "tests.refactor.test_rope_semantic",
    "services_resource": "tests.refactor.test_rope_semantic",
    "test_rope_find_occurrences_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_module_syntax_error_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_project_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_semantic": "tests.refactor.test_rope_semantic",
    "test_rope_stubs": "tests.refactor.test_rope_stubs",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
