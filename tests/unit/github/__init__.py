# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.github import (
        main_cli_tests as main_cli_tests,
        main_dispatch_tests as main_dispatch_tests,
        main_integration_tests as main_integration_tests,
        main_tests as main_tests,
    )
    from tests.unit.github.main_cli_tests import (
        test_main_returns_nonzero_on_unknown as test_main_returns_nonzero_on_unknown,
        test_main_returns_zero_on_help as test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options as test_pr_workspace_accepts_repeated_project_options,
    )
    from tests.unit.github.main_dispatch_tests import (
        TestRunPrWorkspace as TestRunPrWorkspace,
    )
    from tests.unit.github.main_integration_tests import TestMain as TestMain
    from tests.unit.github.main_tests import (
        TestRunLint as TestRunLint,
        TestRunPr as TestRunPr,
        TestRunWorkflows as TestRunWorkflows,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestMain": ["tests.unit.github.main_integration_tests", "TestMain"],
    "TestRunLint": ["tests.unit.github.main_tests", "TestRunLint"],
    "TestRunPr": ["tests.unit.github.main_tests", "TestRunPr"],
    "TestRunPrWorkspace": [
        "tests.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ],
    "TestRunWorkflows": ["tests.unit.github.main_tests", "TestRunWorkflows"],
    "main_cli_tests": ["tests.unit.github.main_cli_tests", ""],
    "main_dispatch_tests": ["tests.unit.github.main_dispatch_tests", ""],
    "main_integration_tests": ["tests.unit.github.main_integration_tests", ""],
    "main_tests": ["tests.unit.github.main_tests", ""],
    "test_main_returns_nonzero_on_unknown": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_nonzero_on_unknown",
    ],
    "test_main_returns_zero_on_help": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_zero_on_help",
    ],
    "test_pr_workspace_accepts_repeated_project_options": [
        "tests.unit.github.main_cli_tests",
        "test_pr_workspace_accepts_repeated_project_options",
    ],
}

_EXPORTS: Sequence[str] = [
    "TestMain",
    "TestRunLint",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunWorkflows",
    "main_cli_tests",
    "main_dispatch_tests",
    "main_integration_tests",
    "main_tests",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_zero_on_help",
    "test_pr_workspace_accepts_repeated_project_options",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
