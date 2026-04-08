# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import tests.unit._utilities as _tests_unit__utilities

    _utilities = _tests_unit__utilities
    import tests.unit.basemk as _tests_unit_basemk

    basemk = _tests_unit_basemk
    import tests.unit.check as _tests_unit_check
    from tests.unit.basemk import basemk_main

    check = _tests_unit_check
    import tests.unit.codegen as _tests_unit_codegen
    from tests.unit.check import (
        RunProjectsMock,
        Spy,
        create_check_project_iter_stub,
        create_check_project_stub,
        create_checker_project,
        create_fake_run_projects,
        create_fake_run_raw,
        create_gate_context,
        create_gate_execution,
        make_issue,
        make_project,
        patch_gate_run,
        patch_gate_run_sequence,
        patch_python_dir_detection,
        run_command_failure_check,
        run_gate_check,
    )

    codegen = _tests_unit_codegen
    import tests.unit.container as _tests_unit_container
    from tests.unit.codegen import FlextInfraCodegenTestProjectFactory

    container = _tests_unit_container
    import tests.unit.deps as _tests_unit_deps

    deps = _tests_unit_deps
    import tests.unit.discovery as _tests_unit_discovery

    discovery = _tests_unit_discovery
    import tests.unit.docs as _tests_unit_docs

    docs = _tests_unit_docs
    import tests.unit.github as _tests_unit_github

    github = _tests_unit_github
    import tests.unit.io as _tests_unit_io
    from tests.unit.github import (
        StubCommandOutput,
        StubJsonIo,
        StubLinter,
        StubPrManager,
        StubProjectInfo,
        StubReporting,
        StubRunner,
        StubSelector,
        StubSyncer,
        StubUtilities,
        StubVersioning,
        StubWorkspaceManager,
    )

    io = _tests_unit_io
    import tests.unit.refactor as _tests_unit_refactor

    refactor = _tests_unit_refactor
    import tests.unit.release as _tests_unit_release
    from tests.unit.refactor import (
        FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP,
        BrokenRule,
        EngineSafetyStub,
        refactor_main,
    )

    release = _tests_unit_release
    import tests.unit.test_infra_constants_core as _tests_unit_test_infra_constants_core
    from tests.unit.release import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
        workspace_root,
    )

    test_infra_constants_core = _tests_unit_test_infra_constants_core
    import tests.unit.test_infra_constants_extra as _tests_unit_test_infra_constants_extra

    test_infra_constants_extra = _tests_unit_test_infra_constants_extra
    import tests.unit.test_infra_git as _tests_unit_test_infra_git

    test_infra_git = _tests_unit_test_infra_git
    import tests.unit.test_infra_init_lazy_core as _tests_unit_test_infra_init_lazy_core

    test_infra_init_lazy_core = _tests_unit_test_infra_init_lazy_core
    import tests.unit.test_infra_init_lazy_submodules as _tests_unit_test_infra_init_lazy_submodules

    test_infra_init_lazy_submodules = _tests_unit_test_infra_init_lazy_submodules
    import tests.unit.test_infra_main as _tests_unit_test_infra_main

    test_infra_main = _tests_unit_test_infra_main
    import tests.unit.test_infra_maintenance_cli as _tests_unit_test_infra_maintenance_cli

    test_infra_maintenance_cli = _tests_unit_test_infra_maintenance_cli
    import tests.unit.test_infra_maintenance_init as _tests_unit_test_infra_maintenance_init

    test_infra_maintenance_init = _tests_unit_test_infra_maintenance_init
    import tests.unit.test_infra_maintenance_main as _tests_unit_test_infra_maintenance_main

    test_infra_maintenance_main = _tests_unit_test_infra_maintenance_main
    import tests.unit.test_infra_maintenance_python_version as _tests_unit_test_infra_maintenance_python_version

    test_infra_maintenance_python_version = (
        _tests_unit_test_infra_maintenance_python_version
    )
    import tests.unit.test_infra_paths as _tests_unit_test_infra_paths

    test_infra_paths = _tests_unit_test_infra_paths
    import tests.unit.test_infra_patterns_core as _tests_unit_test_infra_patterns_core

    test_infra_patterns_core = _tests_unit_test_infra_patterns_core
    import tests.unit.test_infra_patterns_extra as _tests_unit_test_infra_patterns_extra

    test_infra_patterns_extra = _tests_unit_test_infra_patterns_extra
    import tests.unit.test_infra_protocols as _tests_unit_test_infra_protocols

    test_infra_protocols = _tests_unit_test_infra_protocols
    import tests.unit.test_infra_reporting_core as _tests_unit_test_infra_reporting_core

    test_infra_reporting_core = _tests_unit_test_infra_reporting_core
    import tests.unit.test_infra_reporting_extra as _tests_unit_test_infra_reporting_extra

    test_infra_reporting_extra = _tests_unit_test_infra_reporting_extra
    import tests.unit.test_infra_selection as _tests_unit_test_infra_selection

    test_infra_selection = _tests_unit_test_infra_selection
    import tests.unit.test_infra_typings as _tests_unit_test_infra_typings

    test_infra_typings = _tests_unit_test_infra_typings
    import tests.unit.test_infra_utilities as _tests_unit_test_infra_utilities

    test_infra_utilities = _tests_unit_test_infra_utilities
    import tests.unit.test_infra_version_core as _tests_unit_test_infra_version_core

    test_infra_version_core = _tests_unit_test_infra_version_core
    import tests.unit.test_infra_version_extra as _tests_unit_test_infra_version_extra

    test_infra_version_extra = _tests_unit_test_infra_version_extra
    import tests.unit.test_infra_versioning as _tests_unit_test_infra_versioning

    test_infra_versioning = _tests_unit_test_infra_versioning
    import tests.unit.test_infra_workspace_cli as _tests_unit_test_infra_workspace_cli

    test_infra_workspace_cli = _tests_unit_test_infra_workspace_cli
    import tests.unit.test_infra_workspace_detector as _tests_unit_test_infra_workspace_detector

    test_infra_workspace_detector = _tests_unit_test_infra_workspace_detector
    import tests.unit.test_infra_workspace_init as _tests_unit_test_infra_workspace_init

    test_infra_workspace_init = _tests_unit_test_infra_workspace_init
    import tests.unit.test_infra_workspace_main as _tests_unit_test_infra_workspace_main

    test_infra_workspace_main = _tests_unit_test_infra_workspace_main
    import tests.unit.test_infra_workspace_migrator as _tests_unit_test_infra_workspace_migrator
    from tests.unit.test_infra_workspace_main import workspace_main

    test_infra_workspace_migrator = _tests_unit_test_infra_workspace_migrator
    import tests.unit.test_infra_workspace_migrator_deps as _tests_unit_test_infra_workspace_migrator_deps

    test_infra_workspace_migrator_deps = _tests_unit_test_infra_workspace_migrator_deps
    import tests.unit.test_infra_workspace_migrator_dryrun as _tests_unit_test_infra_workspace_migrator_dryrun

    test_infra_workspace_migrator_dryrun = (
        _tests_unit_test_infra_workspace_migrator_dryrun
    )
    import tests.unit.test_infra_workspace_migrator_errors as _tests_unit_test_infra_workspace_migrator_errors

    test_infra_workspace_migrator_errors = (
        _tests_unit_test_infra_workspace_migrator_errors
    )
    import tests.unit.test_infra_workspace_migrator_internal as _tests_unit_test_infra_workspace_migrator_internal

    test_infra_workspace_migrator_internal = (
        _tests_unit_test_infra_workspace_migrator_internal
    )
    import tests.unit.test_infra_workspace_migrator_pyproject as _tests_unit_test_infra_workspace_migrator_pyproject

    test_infra_workspace_migrator_pyproject = (
        _tests_unit_test_infra_workspace_migrator_pyproject
    )
    import tests.unit.test_infra_workspace_orchestrator as _tests_unit_test_infra_workspace_orchestrator

    test_infra_workspace_orchestrator = _tests_unit_test_infra_workspace_orchestrator
    import tests.unit.test_infra_workspace_sync as _tests_unit_test_infra_workspace_sync

    test_infra_workspace_sync = _tests_unit_test_infra_workspace_sync
    import tests.unit.test_ssot_enforcement as _tests_unit_test_ssot_enforcement
    from tests.unit.test_infra_workspace_sync import SetupFn

    test_ssot_enforcement = _tests_unit_test_ssot_enforcement
    import tests.unit.transformers as _tests_unit_transformers
    from tests.unit.test_ssot_enforcement import SSOT_METHODS, WORKSPACE

    transformers = _tests_unit_transformers
    import tests.unit.validate as _tests_unit_validate

    validate = _tests_unit_validate
    import tests.unit.workspace as _tests_unit_workspace

    workspace = _tests_unit_workspace
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "tests.unit._utilities",
        "tests.unit.basemk",
        "tests.unit.check",
        "tests.unit.codegen",
        "tests.unit.container",
        "tests.unit.deps",
        "tests.unit.discovery",
        "tests.unit.docs",
        "tests.unit.github",
        "tests.unit.io",
        "tests.unit.refactor",
        "tests.unit.release",
        "tests.unit.transformers",
        "tests.unit.validate",
        "tests.unit.workspace",
    ),
    {
        "SSOT_METHODS": ("tests.unit.test_ssot_enforcement", "SSOT_METHODS"),
        "SetupFn": ("tests.unit.test_infra_workspace_sync", "SetupFn"),
        "WORKSPACE": ("tests.unit.test_ssot_enforcement", "WORKSPACE"),
        "_utilities": "tests.unit._utilities",
        "basemk": "tests.unit.basemk",
        "check": "tests.unit.check",
        "codegen": "tests.unit.codegen",
        "container": "tests.unit.container",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "deps": "tests.unit.deps",
        "discovery": "tests.unit.discovery",
        "docs": "tests.unit.docs",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "github": "tests.unit.github",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "io": "tests.unit.io",
        "r": ("flext_core.result", "FlextResult"),
        "refactor": "tests.unit.refactor",
        "release": "tests.unit.release",
        "s": ("flext_core.service", "FlextService"),
        "test_infra_constants_core": "tests.unit.test_infra_constants_core",
        "test_infra_constants_extra": "tests.unit.test_infra_constants_extra",
        "test_infra_git": "tests.unit.test_infra_git",
        "test_infra_init_lazy_core": "tests.unit.test_infra_init_lazy_core",
        "test_infra_init_lazy_submodules": "tests.unit.test_infra_init_lazy_submodules",
        "test_infra_main": "tests.unit.test_infra_main",
        "test_infra_maintenance_cli": "tests.unit.test_infra_maintenance_cli",
        "test_infra_maintenance_init": "tests.unit.test_infra_maintenance_init",
        "test_infra_maintenance_main": "tests.unit.test_infra_maintenance_main",
        "test_infra_maintenance_python_version": "tests.unit.test_infra_maintenance_python_version",
        "test_infra_paths": "tests.unit.test_infra_paths",
        "test_infra_patterns_core": "tests.unit.test_infra_patterns_core",
        "test_infra_patterns_extra": "tests.unit.test_infra_patterns_extra",
        "test_infra_protocols": "tests.unit.test_infra_protocols",
        "test_infra_reporting_core": "tests.unit.test_infra_reporting_core",
        "test_infra_reporting_extra": "tests.unit.test_infra_reporting_extra",
        "test_infra_selection": "tests.unit.test_infra_selection",
        "test_infra_typings": "tests.unit.test_infra_typings",
        "test_infra_utilities": "tests.unit.test_infra_utilities",
        "test_infra_version_core": "tests.unit.test_infra_version_core",
        "test_infra_version_extra": "tests.unit.test_infra_version_extra",
        "test_infra_versioning": "tests.unit.test_infra_versioning",
        "test_infra_workspace_cli": "tests.unit.test_infra_workspace_cli",
        "test_infra_workspace_detector": "tests.unit.test_infra_workspace_detector",
        "test_infra_workspace_init": "tests.unit.test_infra_workspace_init",
        "test_infra_workspace_main": "tests.unit.test_infra_workspace_main",
        "test_infra_workspace_migrator": "tests.unit.test_infra_workspace_migrator",
        "test_infra_workspace_migrator_deps": "tests.unit.test_infra_workspace_migrator_deps",
        "test_infra_workspace_migrator_dryrun": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_infra_workspace_migrator_errors": "tests.unit.test_infra_workspace_migrator_errors",
        "test_infra_workspace_migrator_internal": "tests.unit.test_infra_workspace_migrator_internal",
        "test_infra_workspace_migrator_pyproject": "tests.unit.test_infra_workspace_migrator_pyproject",
        "test_infra_workspace_orchestrator": "tests.unit.test_infra_workspace_orchestrator",
        "test_infra_workspace_sync": "tests.unit.test_infra_workspace_sync",
        "test_ssot_enforcement": "tests.unit.test_ssot_enforcement",
        "transformers": "tests.unit.transformers",
        "validate": "tests.unit.validate",
        "workspace": "tests.unit.workspace",
        "workspace_main": ("tests.unit.test_infra_workspace_main", "workspace_main"),
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)

__all__ = [
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "SSOT_METHODS",
    "WORKSPACE",
    "BrokenRule",
    "EngineSafetyStub",
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "FlextInfraCodegenTestProjectFactory",
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
    "_utilities",
    "basemk",
    "basemk_main",
    "check",
    "codegen",
    "container",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_context",
    "create_gate_execution",
    "d",
    "deps",
    "discovery",
    "docs",
    "e",
    "github",
    "h",
    "io",
    "make_issue",
    "make_project",
    "patch_gate_run",
    "patch_gate_run_sequence",
    "patch_python_dir_detection",
    "r",
    "refactor",
    "refactor_main",
    "release",
    "run_command_failure_check",
    "run_gate_check",
    "s",
    "test_infra_constants_core",
    "test_infra_constants_extra",
    "test_infra_git",
    "test_infra_init_lazy_core",
    "test_infra_init_lazy_submodules",
    "test_infra_main",
    "test_infra_maintenance_cli",
    "test_infra_maintenance_init",
    "test_infra_maintenance_main",
    "test_infra_maintenance_python_version",
    "test_infra_paths",
    "test_infra_patterns_core",
    "test_infra_patterns_extra",
    "test_infra_protocols",
    "test_infra_reporting_core",
    "test_infra_reporting_extra",
    "test_infra_selection",
    "test_infra_typings",
    "test_infra_utilities",
    "test_infra_version_core",
    "test_infra_version_extra",
    "test_infra_versioning",
    "test_infra_workspace_cli",
    "test_infra_workspace_detector",
    "test_infra_workspace_init",
    "test_infra_workspace_main",
    "test_infra_workspace_migrator",
    "test_infra_workspace_migrator_deps",
    "test_infra_workspace_migrator_dryrun",
    "test_infra_workspace_migrator_errors",
    "test_infra_workspace_migrator_internal",
    "test_infra_workspace_migrator_pyproject",
    "test_infra_workspace_orchestrator",
    "test_infra_workspace_sync",
    "test_ssot_enforcement",
    "transformers",
    "validate",
    "workspace",
    "workspace_main",
    "workspace_root",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
