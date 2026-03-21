# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes


if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .main_dispatch_tests import TestRunPrWorkspace
    from .main_integration_tests import TestMain
    from .main_tests import (
        TestRunLint,
        TestRunWorkflows,
        main,
        run_lint,
        run_pr,
        run_pr_workspace,
        run_workflows,
    )
    from .pr_cli_tests import TestMainFunction, TestParseArgs, TestSelectorFunction
    from .pr_init_tests import TestGithubInit
    from .pr_operations_tests import (
        TestChecks,
        TestClose,
        TestMerge,
        TestTriggerRelease,
        TestView,
    )
    from .pr_tests import TestCreate, TestFlextInfraPrManager, TestStatus
    from .pr_workspace_orchestrate_tests import TestOrchestrate, TestStaticMethods
    from .pr_workspace_tests import (
        TestCheckpoint,
        TestFlextInfraPrWorkspaceManager,
        TestRunPr,
    )
    from .workflows_tests import (
        TestFlextInfraWorkflowSyncer,
        TestRenderTemplate,
        TestSyncOperation,
        TestSyncProject,
    )
    from .workflows_workspace_tests import TestSyncWorkspace, TestWriteReport

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestCheckpoint": ("tests.infra.unit.github.pr_workspace_tests", "TestCheckpoint"),
    "TestChecks": ("tests.infra.unit.github.pr_operations_tests", "TestChecks"),
    "TestClose": ("tests.infra.unit.github.pr_operations_tests", "TestClose"),
    "TestCreate": ("tests.infra.unit.github.pr_tests", "TestCreate"),
    "TestFlextInfraPrManager": ("tests.infra.unit.github.pr_tests", "TestFlextInfraPrManager"),
    "TestFlextInfraPrWorkspaceManager": ("tests.infra.unit.github.pr_workspace_tests", "TestFlextInfraPrWorkspaceManager"),
    "TestFlextInfraWorkflowSyncer": ("tests.infra.unit.github.workflows_tests", "TestFlextInfraWorkflowSyncer"),
    "TestGithubInit": ("tests.infra.unit.github.pr_init_tests", "TestGithubInit"),
    "TestMain": ("tests.infra.unit.github.main_integration_tests", "TestMain"),
    "TestMainFunction": ("tests.infra.unit.github.pr_cli_tests", "TestMainFunction"),
    "TestMerge": ("tests.infra.unit.github.pr_operations_tests", "TestMerge"),
    "TestOrchestrate": ("tests.infra.unit.github.pr_workspace_orchestrate_tests", "TestOrchestrate"),
    "TestParseArgs": ("tests.infra.unit.github.pr_cli_tests", "TestParseArgs"),
    "TestRenderTemplate": ("tests.infra.unit.github.workflows_tests", "TestRenderTemplate"),
    "TestRunLint": ("tests.infra.unit.github.main_tests", "TestRunLint"),
    "TestRunPr": ("tests.infra.unit.github.pr_workspace_tests", "TestRunPr"),
    "TestRunPrWorkspace": ("tests.infra.unit.github.main_dispatch_tests", "TestRunPrWorkspace"),
    "TestRunWorkflows": ("tests.infra.unit.github.main_tests", "TestRunWorkflows"),
    "TestSelectorFunction": ("tests.infra.unit.github.pr_cli_tests", "TestSelectorFunction"),
    "TestStaticMethods": ("tests.infra.unit.github.pr_workspace_orchestrate_tests", "TestStaticMethods"),
    "TestStatus": ("tests.infra.unit.github.pr_tests", "TestStatus"),
    "TestSyncOperation": ("tests.infra.unit.github.workflows_tests", "TestSyncOperation"),
    "TestSyncProject": ("tests.infra.unit.github.workflows_tests", "TestSyncProject"),
    "TestSyncWorkspace": ("tests.infra.unit.github.workflows_workspace_tests", "TestSyncWorkspace"),
    "TestTriggerRelease": ("tests.infra.unit.github.pr_operations_tests", "TestTriggerRelease"),
    "TestView": ("tests.infra.unit.github.pr_operations_tests", "TestView"),
    "TestWriteReport": ("tests.infra.unit.github.workflows_workspace_tests", "TestWriteReport"),
    "main": ("tests.infra.unit.github.main_tests", "main"),
    "run_lint": ("tests.infra.unit.github.main_tests", "run_lint"),
    "run_pr": ("tests.infra.unit.github.main_tests", "run_pr"),
    "run_pr_workspace": ("tests.infra.unit.github.main_tests", "run_pr_workspace"),
    "run_workflows": ("tests.infra.unit.github.main_tests", "run_workflows"),
}

__all__ = [
    "TestCheckpoint",
    "TestChecks",
    "TestClose",
    "TestCreate",
    "TestFlextInfraPrManager",
    "TestFlextInfraPrWorkspaceManager",
    "TestFlextInfraWorkflowSyncer",
    "TestGithubInit",
    "TestMain",
    "TestMainFunction",
    "TestMerge",
    "TestOrchestrate",
    "TestParseArgs",
    "TestRenderTemplate",
    "TestRunLint",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunWorkflows",
    "TestSelectorFunction",
    "TestStaticMethods",
    "TestStatus",
    "TestSyncOperation",
    "TestSyncProject",
    "TestSyncWorkspace",
    "TestTriggerRelease",
    "TestView",
    "TestWriteReport",
    "main",
    "run_lint",
    "run_pr",
    "run_pr_workspace",
    "run_workflows",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
