# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.github._stubs import *
    from tests.unit.github.main_cli_tests import *
    from tests.unit.github.main_dispatch_tests import *
    from tests.unit.github.main_integration_tests import *
    from tests.unit.github.main_tests import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "StubCommandOutput": "tests.unit.github._stubs",
    "StubJsonIo": "tests.unit.github._stubs",
    "StubLinter": "tests.unit.github._stubs",
    "StubPrManager": "tests.unit.github._stubs",
    "StubProjectInfo": "tests.unit.github._stubs",
    "StubReporting": "tests.unit.github._stubs",
    "StubRunner": "tests.unit.github._stubs",
    "StubSelector": "tests.unit.github._stubs",
    "StubSyncer": "tests.unit.github._stubs",
    "StubTemplates": "tests.unit.github._stubs",
    "StubUtilities": "tests.unit.github._stubs",
    "StubVersioning": "tests.unit.github._stubs",
    "StubWorkspaceManager": "tests.unit.github._stubs",
    "TestMain": "tests.unit.github.main_integration_tests",
    "TestRunLint": "tests.unit.github.main_tests",
    "TestRunPr": "tests.unit.github.main_tests",
    "TestRunPrWorkspace": "tests.unit.github.main_dispatch_tests",
    "TestRunWorkflows": "tests.unit.github.main_tests",
    "_stubs": "tests.unit.github._stubs",
    "_stubs_extra": "tests.unit.github._stubs_extra",
    "main_cli_tests": "tests.unit.github.main_cli_tests",
    "main_dispatch_tests": "tests.unit.github.main_dispatch_tests",
    "main_integration_tests": "tests.unit.github.main_integration_tests",
    "main_tests": "tests.unit.github.main_tests",
    "test_main_returns_nonzero_on_unknown": "tests.unit.github.main_cli_tests",
    "test_main_returns_zero_on_help": "tests.unit.github.main_cli_tests",
    "test_pr_workspace_accepts_repeated_project_options": "tests.unit.github.main_cli_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
