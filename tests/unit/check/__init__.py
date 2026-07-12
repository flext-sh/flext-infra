# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.check.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.check import (
        abstraction_boundary_gate_tests as abstraction_boundary_gate_tests,
        extended_gate_bandit_markdown_tests as extended_gate_bandit_markdown_tests,
        extended_gate_mypy_pyright_tests as extended_gate_mypy_pyright_tests,
        extended_runners_ruff_tests as extended_runners_ruff_tests,
        extended_workspace_init_tests as extended_workspace_init_tests,
        fix_pyrefly_config_tests as fix_pyrefly_config_tests,
        gate_registry_tests as gate_registry_tests,
        loc_cap_gate_tests as loc_cap_gate_tests,
        main_tests as main_tests,
        silent_failure_gate_tests as silent_failure_gate_tests,
        smells_gate_tests as smells_gate_tests,
        tests_workspace_check as tests_workspace_check,
    )
    from tests.unit.check.enforcement_fixer_orchestrator_tests import (
        TestsEnforcementFixerOrchestrator as TestsEnforcementFixerOrchestrator,
    )
    from tests.unit.check.extended_cli_entry_tests import (
        TestWorkspaceCheckCLI as TestWorkspaceCheckCLI,
    )
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPublicBehavior as TestConfigFixerPublicBehavior,
    )
    from tests.unit.check.extended_config_fixer_tests import (
        TestConfigFixerExecute as TestConfigFixerExecute,
        TestConfigFixerProcessFile as TestConfigFixerProcessFile,
        TestConfigFixerRun as TestConfigFixerRun,
        TestConfigFixerToArray as TestConfigFixerToArray,
    )
    from tests.unit.check.extended_error_reporting_tests import (
        TestGateErrorReportingPublicBehavior as TestGateErrorReportingPublicBehavior,
    )
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted as TestCheckIssueFormatted,
        TestProjectResultProperties as TestProjectResultProperties,
        TestRunCommandGateParsing as TestRunCommandGateParsing,
        TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import (
        TestsExtendedProjectRunners as TestsExtendedProjectRunners,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.check.extended_run_projects_tests import (
        TestRunProjectsPublicBehavior as TestRunProjectsPublicBehavior,
    )
    from tests.unit.check.extended_runners_extra_tests import (
        TestExtendedRunnerExtras as TestExtendedRunnerExtras,
    )
    from tests.unit.check.extended_runners_tests import (
        TestRunnerPublicBehavior as TestRunnerPublicBehavior,
    )
    from tests.unit.check.init_tests import TestFlextInfraCheck as TestFlextInfraCheck
    from tests.unit.check.pyrefly_tests import (
        TestFlextInfraConfigFixer as TestFlextInfraConfigFixer,
    )
    from tests.unit.check.tests_cli import (
        TestWorkspaceCheckCli as TestWorkspaceCheckCli,
    )
    from tests.unit.check.workspace_tests import (
        TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
