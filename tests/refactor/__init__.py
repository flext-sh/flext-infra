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
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
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
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "models_resource": "tests.refactor.test_rope_semantic",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "rope_workspace": "tests.refactor.test_rope_semantic",
    "s": ("flext_core.service", "FlextService"),
    "services_resource": "tests.refactor.test_rope_semantic",
    "t": ("flext_core.typings", "FlextTypes"),
    "test_rope_find_occurrences_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_module_syntax_error_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_project_wrapper": "tests.refactor.test_rope_stubs",
    "test_rope_semantic": "tests.refactor.test_rope_semantic",
    "test_rope_stubs": "tests.refactor.test_rope_stubs",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
