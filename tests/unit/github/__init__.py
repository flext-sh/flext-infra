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
        StubLinter,
        StubPrManager,
        StubProjectInfo,
        StubReporting,
        StubRunner,
        StubSelector,
        StubSyncer,
        StubTemplates,
        StubUtilities,
        StubVersioning,
        StubWorkspaceManager,
    )

    _stubs_extra = _tests_unit_github__stubs_extra
    import tests.unit.github.main_cli_tests as _tests_unit_github_main_cli_tests

    main_cli_tests = _tests_unit_github_main_cli_tests
    import tests.unit.github.main_dispatch_tests as _tests_unit_github_main_dispatch_tests
    from tests.unit.github.main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )

    main_dispatch_tests = _tests_unit_github_main_dispatch_tests
    import tests.unit.github.main_integration_tests as _tests_unit_github_main_integration_tests
    from tests.unit.github.main_dispatch_tests import TestRunPrWorkspace

    main_integration_tests = _tests_unit_github_main_integration_tests
    import tests.unit.github.main_tests as _tests_unit_github_main_tests
    from tests.unit.github.main_integration_tests import TestMain

    main_tests = _tests_unit_github_main_tests
    from tests.unit.github.main_tests import TestRunLint, TestRunPr, TestRunWorkflows

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
_LAZY_IMPORTS = {
    "StubCommandOutput": ("tests.unit.github._stubs", "StubCommandOutput"),
    "StubJsonIo": ("tests.unit.github._stubs", "StubJsonIo"),
    "StubLinter": ("tests.unit.github._stubs", "StubLinter"),
    "StubPrManager": ("tests.unit.github._stubs", "StubPrManager"),
    "StubProjectInfo": ("tests.unit.github._stubs", "StubProjectInfo"),
    "StubReporting": ("tests.unit.github._stubs", "StubReporting"),
    "StubRunner": ("tests.unit.github._stubs", "StubRunner"),
    "StubSelector": ("tests.unit.github._stubs", "StubSelector"),
    "StubSyncer": ("tests.unit.github._stubs", "StubSyncer"),
    "StubTemplates": ("tests.unit.github._stubs", "StubTemplates"),
    "StubUtilities": ("tests.unit.github._stubs", "StubUtilities"),
    "StubVersioning": ("tests.unit.github._stubs", "StubVersioning"),
    "StubWorkspaceManager": ("tests.unit.github._stubs", "StubWorkspaceManager"),
    "TestMain": ("tests.unit.github.main_integration_tests", "TestMain"),
    "TestRunLint": ("tests.unit.github.main_tests", "TestRunLint"),
    "TestRunPr": ("tests.unit.github.main_tests", "TestRunPr"),
    "TestRunPrWorkspace": (
        "tests.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ),
    "TestRunWorkflows": ("tests.unit.github.main_tests", "TestRunWorkflows"),
    "_stubs": "tests.unit.github._stubs",
    "_stubs_extra": "tests.unit.github._stubs_extra",
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main_cli_tests": "tests.unit.github.main_cli_tests",
    "main_dispatch_tests": "tests.unit.github.main_dispatch_tests",
    "main_integration_tests": "tests.unit.github.main_integration_tests",
    "main_tests": "tests.unit.github.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_main_returns_nonzero_on_unknown": (
        "tests.unit.github.main_cli_tests",
        "test_main_returns_nonzero_on_unknown",
    ),
    "test_main_returns_zero_on_help": (
        "tests.unit.github.main_cli_tests",
        "test_main_returns_zero_on_help",
    ),
    "test_pr_workspace_accepts_repeated_project_options": (
        "tests.unit.github.main_cli_tests",
        "test_pr_workspace_accepts_repeated_project_options",
    ),
    "u": ("flext_core.utilities", "FlextUtilities"),
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
    "StubTemplates",
    "StubUtilities",
    "StubVersioning",
    "StubWorkspaceManager",
    "TestMain",
    "TestRunLint",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunWorkflows",
    "_stubs",
    "_stubs_extra",
    "c",
    "d",
    "e",
    "h",
    "m",
    "main_cli_tests",
    "main_dispatch_tests",
    "main_integration_tests",
    "main_tests",
    "p",
    "r",
    "s",
    "t",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_zero_on_help",
    "test_pr_workspace_accepts_repeated_project_options",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
