# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.refactor.test_rope_semantic as _tests_refactor_test_rope_semantic

    test_rope_semantic = _tests_refactor_test_rope_semantic
    import tests.refactor.test_rope_stubs as _tests_refactor_test_rope_stubs
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

    test_rope_stubs = _tests_refactor_test_rope_stubs
    from tests.refactor.test_rope_stubs import (
        test_rope_find_occurrences_wrapper,
        test_rope_module_syntax_error_wrapper,
        test_rope_project_wrapper,
    )

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "TestFindDefinitionOffset": (
        "tests.refactor.test_rope_semantic",
        "TestFindDefinitionOffset",
    ),
    "TestGetClassBases": ("tests.refactor.test_rope_semantic", "TestGetClassBases"),
    "TestGetClassMethods": ("tests.refactor.test_rope_semantic", "TestGetClassMethods"),
    "TestGetModuleClasses": (
        "tests.refactor.test_rope_semantic",
        "TestGetModuleClasses",
    ),
    "TestGetModuleImports": (
        "tests.refactor.test_rope_semantic",
        "TestGetModuleImports",
    ),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "models_resource": ("tests.refactor.test_rope_semantic", "models_resource"),
    "r": ("flext_core.result", "FlextResult"),
    "rope_workspace": ("tests.refactor.test_rope_semantic", "rope_workspace"),
    "s": ("flext_core.service", "FlextService"),
    "services_resource": ("tests.refactor.test_rope_semantic", "services_resource"),
    "test_rope_find_occurrences_wrapper": (
        "tests.refactor.test_rope_stubs",
        "test_rope_find_occurrences_wrapper",
    ),
    "test_rope_module_syntax_error_wrapper": (
        "tests.refactor.test_rope_stubs",
        "test_rope_module_syntax_error_wrapper",
    ),
    "test_rope_project_wrapper": (
        "tests.refactor.test_rope_stubs",
        "test_rope_project_wrapper",
    ),
    "test_rope_semantic": "tests.refactor.test_rope_semantic",
    "test_rope_stubs": "tests.refactor.test_rope_stubs",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "TestFindDefinitionOffset",
    "TestGetClassBases",
    "TestGetClassMethods",
    "TestGetModuleClasses",
    "TestGetModuleImports",
    "d",
    "e",
    "h",
    "models_resource",
    "r",
    "rope_workspace",
    "s",
    "services_resource",
    "test_rope_find_occurrences_wrapper",
    "test_rope_module_syntax_error_wrapper",
    "test_rope_project_wrapper",
    "test_rope_semantic",
    "test_rope_stubs",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
