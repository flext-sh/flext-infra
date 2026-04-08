# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.github._stubs as _tests_unit_github__stubs

    _stubs = _tests_unit_github__stubs
    import tests.unit.github._stubs_extra as _tests_unit_github__stubs_extra
    from tests.unit.github._stubs import (
        StubCommandOutput,
        StubJsonIo,
        StubProjectInfo,
        StubReporting,
        StubRunner,
        StubSelector,
        StubVersioning,
    )

    _stubs_extra = _tests_unit_github__stubs_extra
    import tests.unit.github.main_cli_tests as _tests_unit_github_main_cli_tests
    from tests.unit.github._stubs_extra import (
        StubLinter,
        StubPrManager,
        StubSyncer,
        StubUtilities,
        StubWorkspaceManager,
    )

    main_cli_tests = _tests_unit_github_main_cli_tests
    import tests.unit.github.main_dispatch_tests as _tests_unit_github_main_dispatch_tests

    main_dispatch_tests = _tests_unit_github_main_dispatch_tests
    import tests.unit.github.main_integration_tests as _tests_unit_github_main_integration_tests

    main_integration_tests = _tests_unit_github_main_integration_tests
    import tests.unit.github.main_tests as _tests_unit_github_main_tests

    main_tests = _tests_unit_github_main_tests
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "StubCommandOutput": ("tests.unit.github._stubs", "StubCommandOutput"),
    "StubJsonIo": ("tests.unit.github._stubs", "StubJsonIo"),
    "StubLinter": ("tests.unit.github._stubs_extra", "StubLinter"),
    "StubPrManager": ("tests.unit.github._stubs_extra", "StubPrManager"),
    "StubProjectInfo": ("tests.unit.github._stubs", "StubProjectInfo"),
    "StubReporting": ("tests.unit.github._stubs", "StubReporting"),
    "StubRunner": ("tests.unit.github._stubs", "StubRunner"),
    "StubSelector": ("tests.unit.github._stubs", "StubSelector"),
    "StubSyncer": ("tests.unit.github._stubs_extra", "StubSyncer"),
    "StubUtilities": ("tests.unit.github._stubs_extra", "StubUtilities"),
    "StubVersioning": ("tests.unit.github._stubs", "StubVersioning"),
    "StubWorkspaceManager": ("tests.unit.github._stubs_extra", "StubWorkspaceManager"),
    "_stubs": "tests.unit.github._stubs",
    "_stubs_extra": "tests.unit.github._stubs_extra",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "main_cli_tests": "tests.unit.github.main_cli_tests",
    "main_dispatch_tests": "tests.unit.github.main_dispatch_tests",
    "main_integration_tests": "tests.unit.github.main_integration_tests",
    "main_tests": "tests.unit.github.main_tests",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "StubCommandOutput",
    "StubJsonIo",
    "StubLinter",
    "StubPrManager",
    "StubProjectInfo",
    "StubReporting",
    "StubRunner",
    "StubSelector",
    "StubSyncer",
    "StubUtilities",
    "StubVersioning",
    "StubWorkspaceManager",
    "_stubs",
    "_stubs_extra",
    "d",
    "e",
    "h",
    "main_cli_tests",
    "main_dispatch_tests",
    "main_integration_tests",
    "main_tests",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
