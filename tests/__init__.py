# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.conftest as _tests_conftest

    conftest = _tests_conftest
    import tests.constants as _tests_constants
    from tests.conftest import pytest_plugins

    constants = _tests_constants
    import tests.fixtures as _tests_fixtures
    from tests.constants import FlextInfraTestConstants, FlextInfraTestConstants as c

    fixtures = _tests_fixtures
    import tests.fixtures_git as _tests_fixtures_git
    from tests.fixtures import (
        real_docs_project,
        real_makefile_project,
        real_python_package,
        real_toml_project,
        real_workspace,
    )

    fixtures_git = _tests_fixtures_git
    import tests.git_service as _tests_git_service
    from tests.fixtures_git import real_git_repo

    git_service = _tests_git_service
    import tests.helpers as _tests_helpers
    from tests.git_service import RealGitService

    helpers = _tests_helpers
    import tests.models as _tests_models
    from tests.helpers import FlextInfraTestHelpers

    models = _tests_models
    import tests.protocols as _tests_protocols
    from tests.models import FlextInfraTestModels, FlextInfraTestModels as m

    protocols = _tests_protocols
    import tests.runner_service as _tests_runner_service
    from tests.protocols import FlextInfraTestProtocols, FlextInfraTestProtocols as p

    runner_service = _tests_runner_service
    import tests.scenarios as _tests_scenarios
    from tests.runner_service import RealSubprocessRunner

    scenarios = _tests_scenarios
    import tests.test_infra_refactor_rope_migrations as _tests_test_infra_refactor_rope_migrations
    from tests.scenarios import (
        DependencyScenario,
        DependencyScenarios,
        GitScenario,
        GitScenarios,
        SubprocessScenario,
        SubprocessScenarios,
        WorkspaceScenario,
        WorkspaceScenarios,
    )

    test_infra_refactor_rope_migrations = _tests_test_infra_refactor_rope_migrations
    import tests.typings as _tests_typings

    typings = _tests_typings
    import tests.utilities as _tests_utilities
    from tests.typings import FlextInfraTestTypes, FlextInfraTestTypes as t
    from tests.unit.basemk.test_engine import basemk_main
    from tests.unit.check._shared_fixtures import (
        RunProjectsMock,
        create_check_project_iter_stub,
        create_check_project_stub,
        create_checker_project,
        create_fake_run_projects,
        create_fake_run_raw,
        create_gate_context,
        create_gate_execution,
        patch_gate_run,
        patch_gate_run_sequence,
        patch_python_dir_detection,
        run_gate_check,
    )
    from tests.unit.check._stubs import Spy, make_issue, make_project
    from tests.unit.check.extended_gate_go_cmd_tests import run_command_failure_check
    from tests.unit.codegen._project_factory import FlextInfraCodegenTestProjectFactory
    from tests.unit.github._stubs import (
        StubCommandOutput,
        StubJsonIo,
        StubProjectInfo,
        StubReporting,
        StubRunner,
        StubSelector,
        StubVersioning,
    )
    from tests.unit.github._stubs_extra import (
        StubLinter,
        StubPrManager,
        StubSyncer,
        StubUtilities,
        StubWorkspaceManager,
    )
    from tests.unit.refactor.test_infra_refactor_engine import BrokenRule
    from tests.unit.refactor.test_infra_refactor_namespace_source import (
        FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP,
    )
    from tests.unit.refactor.test_infra_refactor_safety import EngineSafetyStub
    from tests.unit.refactor.test_main_cli import refactor_main
    from tests.unit.release._stubs import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
        workspace_root,
    )
    from tests.unit.test_infra_workspace_main import workspace_main
    from tests.unit.test_infra_workspace_sync import SetupFn
    from tests.unit.test_ssot_enforcement import SSOT_METHODS, WORKSPACE

    utilities = _tests_utilities
    import tests.workspace_factory as _tests_workspace_factory
    from tests.utilities import FlextInfraTestUtilities, FlextInfraTestUtilities as u

    workspace_factory = _tests_workspace_factory
    import tests.workspace_scenarios as _tests_workspace_scenarios
    from tests.workspace_factory import WorkspaceFactory

    workspace_scenarios = _tests_workspace_scenarios
    from tests.workspace_scenarios import (
        BrokenScenario,
        EmptyScenario,
        FullScenario,
        MinimalScenario,
    )

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "BrokenRule": ("tests.unit.refactor.test_infra_refactor_engine", "BrokenRule"),
    "BrokenScenario": ("tests.workspace_scenarios", "BrokenScenario"),
    "DependencyScenario": ("tests.scenarios", "DependencyScenario"),
    "DependencyScenarios": ("tests.scenarios", "DependencyScenarios"),
    "EmptyScenario": ("tests.workspace_scenarios", "EmptyScenario"),
    "EngineSafetyStub": (
        "tests.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ),
    "FAMILY_FILE_MAP": (
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_FILE_MAP",
    ),
    "FAMILY_SUFFIX_MAP": (
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_SUFFIX_MAP",
    ),
    "FakeReporting": ("tests.unit.release._stubs", "FakeReporting"),
    "FakeSelection": ("tests.unit.release._stubs", "FakeSelection"),
    "FakeSubprocess": ("tests.unit.release._stubs", "FakeSubprocess"),
    "FakeUtilsNamespace": ("tests.unit.release._stubs", "FakeUtilsNamespace"),
    "FakeVersioning": ("tests.unit.release._stubs", "FakeVersioning"),
    "FlextInfraCodegenTestProjectFactory": (
        "tests.unit.codegen._project_factory",
        "FlextInfraCodegenTestProjectFactory",
    ),
    "FlextInfraTestConstants": ("tests.constants", "FlextInfraTestConstants"),
    "FlextInfraTestHelpers": ("tests.helpers", "FlextInfraTestHelpers"),
    "FlextInfraTestModels": ("tests.models", "FlextInfraTestModels"),
    "FlextInfraTestProtocols": ("tests.protocols", "FlextInfraTestProtocols"),
    "FlextInfraTestTypes": ("tests.typings", "FlextInfraTestTypes"),
    "FlextInfraTestUtilities": ("tests.utilities", "FlextInfraTestUtilities"),
    "FullScenario": ("tests.workspace_scenarios", "FullScenario"),
    "GitScenario": ("tests.scenarios", "GitScenario"),
    "GitScenarios": ("tests.scenarios", "GitScenarios"),
    "MinimalScenario": ("tests.workspace_scenarios", "MinimalScenario"),
    "RealGitService": ("tests.git_service", "RealGitService"),
    "RealSubprocessRunner": ("tests.runner_service", "RealSubprocessRunner"),
    "RunProjectsMock": ("tests.unit.check._shared_fixtures", "RunProjectsMock"),
    "SSOT_METHODS": ("tests.unit.test_ssot_enforcement", "SSOT_METHODS"),
    "SetupFn": ("tests.unit.test_infra_workspace_sync", "SetupFn"),
    "Spy": ("tests.unit.check._stubs", "Spy"),
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
    "SubprocessScenario": ("tests.scenarios", "SubprocessScenario"),
    "SubprocessScenarios": ("tests.scenarios", "SubprocessScenarios"),
    "WORKSPACE": ("tests.unit.test_ssot_enforcement", "WORKSPACE"),
    "WorkspaceFactory": ("tests.workspace_factory", "WorkspaceFactory"),
    "WorkspaceScenario": ("tests.scenarios", "WorkspaceScenario"),
    "WorkspaceScenarios": ("tests.scenarios", "WorkspaceScenarios"),
    "basemk_main": ("tests.unit.basemk.test_engine", "basemk_main"),
    "c": ("tests.constants", "FlextInfraTestConstants"),
    "conftest": "tests.conftest",
    "constants": "tests.constants",
    "create_check_project_iter_stub": (
        "tests.unit.check._shared_fixtures",
        "create_check_project_iter_stub",
    ),
    "create_check_project_stub": (
        "tests.unit.check._shared_fixtures",
        "create_check_project_stub",
    ),
    "create_checker_project": (
        "tests.unit.check._shared_fixtures",
        "create_checker_project",
    ),
    "create_fake_run_projects": (
        "tests.unit.check._shared_fixtures",
        "create_fake_run_projects",
    ),
    "create_fake_run_raw": ("tests.unit.check._shared_fixtures", "create_fake_run_raw"),
    "create_gate_context": ("tests.unit.check._shared_fixtures", "create_gate_context"),
    "create_gate_execution": (
        "tests.unit.check._shared_fixtures",
        "create_gate_execution",
    ),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixtures": "tests.fixtures",
    "fixtures_git": "tests.fixtures_git",
    "git_service": "tests.git_service",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "helpers": "tests.helpers",
    "m": ("tests.models", "FlextInfraTestModels"),
    "make_issue": ("tests.unit.check._stubs", "make_issue"),
    "make_project": ("tests.unit.check._stubs", "make_project"),
    "models": "tests.models",
    "p": ("tests.protocols", "FlextInfraTestProtocols"),
    "patch_gate_run": ("tests.unit.check._shared_fixtures", "patch_gate_run"),
    "patch_gate_run_sequence": (
        "tests.unit.check._shared_fixtures",
        "patch_gate_run_sequence",
    ),
    "patch_python_dir_detection": (
        "tests.unit.check._shared_fixtures",
        "patch_python_dir_detection",
    ),
    "protocols": "tests.protocols",
    "pytest_plugins": ("tests.conftest", "pytest_plugins"),
    "r": ("flext_core.result", "FlextResult"),
    "real_docs_project": ("tests.fixtures", "real_docs_project"),
    "real_git_repo": ("tests.fixtures_git", "real_git_repo"),
    "real_makefile_project": ("tests.fixtures", "real_makefile_project"),
    "real_python_package": ("tests.fixtures", "real_python_package"),
    "real_toml_project": ("tests.fixtures", "real_toml_project"),
    "real_workspace": ("tests.fixtures", "real_workspace"),
    "refactor_main": ("tests.unit.refactor.test_main_cli", "refactor_main"),
    "run_command_failure_check": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ),
    "run_gate_check": ("tests.unit.check._shared_fixtures", "run_gate_check"),
    "runner_service": "tests.runner_service",
    "s": ("flext_core.service", "FlextService"),
    "scenarios": "tests.scenarios",
    "t": ("tests.typings", "FlextInfraTestTypes"),
    "test_infra_refactor_rope_migrations": "tests.test_infra_refactor_rope_migrations",
    "typings": "tests.typings",
    "u": ("tests.utilities", "FlextInfraTestUtilities"),
    "utilities": "tests.utilities",
    "workspace_factory": "tests.workspace_factory",
    "workspace_main": ("tests.unit.test_infra_workspace_main", "workspace_main"),
    "workspace_root": ("tests.unit.release._stubs", "workspace_root"),
    "workspace_scenarios": "tests.workspace_scenarios",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "SSOT_METHODS",
    "WORKSPACE",
    "BrokenRule",
    "BrokenScenario",
    "DependencyScenario",
    "DependencyScenarios",
    "EmptyScenario",
    "EngineSafetyStub",
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "FlextInfraCodegenTestProjectFactory",
    "FlextInfraTestConstants",
    "FlextInfraTestHelpers",
    "FlextInfraTestModels",
    "FlextInfraTestProtocols",
    "FlextInfraTestTypes",
    "FlextInfraTestUtilities",
    "FullScenario",
    "GitScenario",
    "GitScenarios",
    "MinimalScenario",
    "RealGitService",
    "RealSubprocessRunner",
    "RunProjectsMock",
    "SetupFn",
    "Spy",
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
    "SubprocessScenario",
    "SubprocessScenarios",
    "WorkspaceFactory",
    "WorkspaceScenario",
    "WorkspaceScenarios",
    "basemk_main",
    "c",
    "conftest",
    "constants",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_context",
    "create_gate_execution",
    "d",
    "e",
    "fixtures",
    "fixtures_git",
    "git_service",
    "h",
    "helpers",
    "m",
    "make_issue",
    "make_project",
    "models",
    "p",
    "patch_gate_run",
    "patch_gate_run_sequence",
    "patch_python_dir_detection",
    "protocols",
    "pytest_plugins",
    "r",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "refactor_main",
    "run_command_failure_check",
    "run_gate_check",
    "runner_service",
    "s",
    "scenarios",
    "t",
    "test_infra_refactor_rope_migrations",
    "typings",
    "u",
    "utilities",
    "workspace_factory",
    "workspace_main",
    "workspace_root",
    "workspace_scenarios",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
