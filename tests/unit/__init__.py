# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit._utilities import *
    from tests.unit.basemk import *
    from tests.unit.check import *
    from tests.unit.codegen import *
    from tests.unit.container import *
    from tests.unit.deps import *
    from tests.unit.discovery import *
    from tests.unit.docs import *
    from tests.unit.github import *
    from tests.unit.io import *
    from tests.unit.refactor import *
    from tests.unit.release import *
    from tests.unit.test_infra_constants_core import (
        TestFlextInfraConstantsExcludedNamespace,
        TestFlextInfraConstantsFilesNamespace,
        TestFlextInfraConstantsGatesNamespace,
        TestFlextInfraConstantsPathsNamespace,
        TestFlextInfraConstantsStatusNamespace,
    )
    from tests.unit.test_infra_constants_extra import (
        TestFlextInfraConstantsAlias,
        TestFlextInfraConstantsCheckNamespace,
        TestFlextInfraConstantsConsistency,
        TestFlextInfraConstantsEncodingNamespace,
        TestFlextInfraConstantsGithubNamespace,
        TestFlextInfraConstantsImmutability,
    )
    from tests.unit.test_infra_git import (
        TestFlextInfraGitService,
        TestGitPush,
        TestGitTagOperations,
        TestRemovedCompatibilityMethods,
        git_repo,
    )
    from tests.unit.test_infra_init_lazy_core import TestFlextInfraInitLazyLoading
    from tests.unit.test_infra_init_lazy_submodules import (
        TestFlextInfraSubmoduleInitLazyLoading,
    )
    from tests.unit.test_infra_main import (
        test_main_all_groups_defined,
        test_main_group_descriptions_are_present,
        test_main_help_flag_returns_zero,
        test_main_returns_error_when_no_args,
        test_main_unknown_group_returns_error,
    )
    from tests.unit.test_infra_maintenance_cli import (
        test_maintenance_rejects_apply_flag,
    )
    from tests.unit.test_infra_maintenance_init import TestFlextInfraMaintenance
    from tests.unit.test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess,
        main,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestDiscoverProjects,
        TestEnforcerExecute,
        TestEnsurePythonVersionFile,
        TestReadRequiredMinor,
        TestWorkspaceRoot,
    )
    from tests.unit.test_infra_paths import TestFlextInfraPathResolver
    from tests.unit.test_infra_patterns_core import (
        TestFlextInfraPatternsMarkdown,
        TestFlextInfraPatternsTooling,
    )
    from tests.unit.test_infra_patterns_extra import (
        TestFlextInfraPatternsEdgeCases,
        TestFlextInfraPatternsPatternTypes,
    )
    from tests.unit.test_infra_protocols import TestFlextInfraProtocolsImport
    from tests.unit.test_infra_reporting_core import TestFlextInfraReportingServiceCore
    from tests.unit.test_infra_reporting_extra import (
        TestFlextInfraReportingServiceExtra,
    )
    from tests.unit.test_infra_selection import TestFlextInfraUtilitiesSelection
    from tests.unit.test_infra_subprocess_core import (
        runner,
        test_capture_cases,
        test_run_cases,
        test_run_raw_cases,
    )
    from tests.unit.test_infra_subprocess_extra import TestFlextInfraCommandRunnerExtra
    from tests.unit.test_infra_toml_io import (
        TestFlextInfraTomlDocument,
        TestFlextInfraTomlHelpers,
        TestFlextInfraTomlRead,
    )
    from tests.unit.test_infra_typings import TestFlextInfraTypesImport
    from tests.unit.test_infra_utilities import TestFlextInfraUtilitiesImport
    from tests.unit.test_infra_version_core import TestFlextInfraVersionClass
    from tests.unit.test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo,
    )
    from tests.unit.test_infra_versioning import (
        service,
        test_bump_version_invalid,
        test_bump_version_result_type,
        test_bump_version_valid,
        test_current_workspace_version,
        test_parse_semver_invalid,
        test_parse_semver_result_type,
        test_parse_semver_valid,
        test_replace_project_version,
    )
    from tests.unit.test_infra_workspace_cli import (
        test_workspace_cli_migrate_command,
        test_workspace_cli_migrate_output_contains_summary,
        test_workspace_cli_rejects_migrate_flags_for_detect,
    )
    from tests.unit.test_infra_workspace_detector import (
        TestDetectorBasicDetection,
        TestDetectorGitRunScenarios,
        TestDetectorRepoNameExtraction,
        detector,
    )
    from tests.unit.test_infra_workspace_init import TestFlextInfraWorkspace
    from tests.unit.test_infra_workspace_main import (
        TestMainCli,
        TestRunDetect,
        TestRunMigrate,
        TestRunOrchestrate,
        TestRunSync,
        workspace_main,
    )
    from tests.unit.test_infra_workspace_migrator import (
        test_migrator_apply_updates_project_files,
        test_migrator_discovery_failure,
        test_migrator_dry_run_reports_changes_without_writes,
        test_migrator_execute_returns_failure,
        test_migrator_handles_missing_pyproject_gracefully,
        test_migrator_no_changes_needed,
        test_migrator_preserves_custom_makefile_content,
        test_migrator_workspace_root_not_exists,
        test_migrator_workspace_root_project_detection,
    )
    from tests.unit.test_infra_workspace_migrator_deps import (
        test_migrate_makefile_not_found_non_dry_run,
        test_migrate_pyproject_flext_core_non_dry_run,
        test_migrator_has_flext_core_dependency_in_poetry,
        test_migrator_has_flext_core_dependency_poetry_deps_not_table,
        test_migrator_has_flext_core_dependency_poetry_table_missing,
        test_workspace_migrator_error_handling_on_invalid_workspace,
        test_workspace_migrator_makefile_not_found_dry_run,
        test_workspace_migrator_makefile_read_error,
        test_workspace_migrator_pyproject_write_error,
    )
    from tests.unit.test_infra_workspace_migrator_dryrun import (
        test_migrator_flext_core_dry_run,
        test_migrator_flext_core_project_skipped,
        test_migrator_gitignore_already_normalized_dry_run,
        test_migrator_makefile_not_found_dry_run,
        test_migrator_makefile_read_failure,
        test_migrator_pyproject_not_found_dry_run,
    )
    from tests.unit.test_infra_workspace_migrator_errors import (
        TestMigratorReadFailures,
        TestMigratorWriteFailures,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestMigratorEdgeCases,
        TestMigratorInternalMakefile,
        TestMigratorInternalPyproject,
    )
    from tests.unit.test_infra_workspace_migrator_pyproject import (
        TestMigratorDryRun,
        TestMigratorFlextCore,
        TestMigratorPoetryDeps,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestOrchestratorBasic,
        TestOrchestratorFailures,
        TestOrchestratorGateNormalization,
        orchestrator,
    )
    from tests.unit.test_infra_workspace_sync import (
        SetupFn,
        svc,
        test_atomic_write_fail,
        test_atomic_write_ok,
        test_cli_forwards_canonical_root,
        test_cli_result_by_project_root,
        test_gitignore_entry_scenarios,
        test_gitignore_sync_failure,
        test_gitignore_write_failure,
        test_sync_basemk_scenarios,
        test_sync_error_scenarios,
        test_sync_regenerates_project_makefile_without_legacy_passthrough,
        test_sync_root_validation,
        test_sync_success_scenarios,
        test_sync_updates_project_makefile_for_standalone_project,
        test_sync_updates_workspace_makefile_for_workspace_root,
        test_workspace_makefile_generator_declares_canonical_workspace_variables,
        test_workspace_makefile_generator_reuses_mod_and_boot_feedback,
        test_workspace_makefile_generator_sanitizes_orchestrator_env,
    )
    from tests.unit.validate import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = merge_lazy_imports(
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
        "tests.unit.validate",
    ),
    {
        "SetupFn": "tests.unit.test_infra_workspace_sync",
        "TestDetectorBasicDetection": "tests.unit.test_infra_workspace_detector",
        "TestDetectorGitRunScenarios": "tests.unit.test_infra_workspace_detector",
        "TestDetectorRepoNameExtraction": "tests.unit.test_infra_workspace_detector",
        "TestDiscoverProjects": "tests.unit.test_infra_maintenance_python_version",
        "TestEnforcerExecute": "tests.unit.test_infra_maintenance_python_version",
        "TestEnsurePythonVersionFile": "tests.unit.test_infra_maintenance_python_version",
        "TestFlextInfraCommandRunnerExtra": "tests.unit.test_infra_subprocess_extra",
        "TestFlextInfraConstantsAlias": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsCheckNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsConsistency": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsEncodingNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsExcludedNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsFilesNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGatesNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGithubNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsImmutability": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsPathsNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsStatusNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraGitService": "tests.unit.test_infra_git",
        "TestFlextInfraInitLazyLoading": "tests.unit.test_infra_init_lazy_core",
        "TestFlextInfraMaintenance": "tests.unit.test_infra_maintenance_init",
        "TestFlextInfraPathResolver": "tests.unit.test_infra_paths",
        "TestFlextInfraPatternsEdgeCases": "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsMarkdown": "tests.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsPatternTypes": "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsTooling": "tests.unit.test_infra_patterns_core",
        "TestFlextInfraProtocolsImport": "tests.unit.test_infra_protocols",
        "TestFlextInfraReportingServiceCore": "tests.unit.test_infra_reporting_core",
        "TestFlextInfraReportingServiceExtra": "tests.unit.test_infra_reporting_extra",
        "TestFlextInfraSubmoduleInitLazyLoading": "tests.unit.test_infra_init_lazy_submodules",
        "TestFlextInfraTomlDocument": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlHelpers": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlRead": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTypesImport": "tests.unit.test_infra_typings",
        "TestFlextInfraUtilitiesImport": "tests.unit.test_infra_utilities",
        "TestFlextInfraUtilitiesSelection": "tests.unit.test_infra_selection",
        "TestFlextInfraVersionClass": "tests.unit.test_infra_version_core",
        "TestFlextInfraVersionModuleLevel": "tests.unit.test_infra_version_extra",
        "TestFlextInfraVersionPackageInfo": "tests.unit.test_infra_version_extra",
        "TestFlextInfraWorkspace": "tests.unit.test_infra_workspace_init",
        "TestGitPush": "tests.unit.test_infra_git",
        "TestGitTagOperations": "tests.unit.test_infra_git",
        "TestMainCli": "tests.unit.test_infra_workspace_main",
        "TestMaintenanceMainEnforcer": "tests.unit.test_infra_maintenance_main",
        "TestMaintenanceMainSuccess": "tests.unit.test_infra_maintenance_main",
        "TestMigratorDryRun": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorEdgeCases": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorFlextCore": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorInternalMakefile": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalPyproject": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorPoetryDeps": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorReadFailures": "tests.unit.test_infra_workspace_migrator_errors",
        "TestMigratorWriteFailures": "tests.unit.test_infra_workspace_migrator_errors",
        "TestOrchestratorBasic": "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorFailures": "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorGateNormalization": "tests.unit.test_infra_workspace_orchestrator",
        "TestReadRequiredMinor": "tests.unit.test_infra_maintenance_python_version",
        "TestRemovedCompatibilityMethods": "tests.unit.test_infra_git",
        "TestRunDetect": "tests.unit.test_infra_workspace_main",
        "TestRunMigrate": "tests.unit.test_infra_workspace_main",
        "TestRunOrchestrate": "tests.unit.test_infra_workspace_main",
        "TestRunSync": "tests.unit.test_infra_workspace_main",
        "TestWorkspaceRoot": "tests.unit.test_infra_maintenance_python_version",
        "_utilities": "tests.unit._utilities",
        "basemk": "tests.unit.basemk",
        "check": "tests.unit.check",
        "codegen": "tests.unit.codegen",
        "container": "tests.unit.container",
        "deps": "tests.unit.deps",
        "detector": "tests.unit.test_infra_workspace_detector",
        "discovery": "tests.unit.discovery",
        "docs": "tests.unit.docs",
        "git_repo": "tests.unit.test_infra_git",
        "github": "tests.unit.github",
        "io": "tests.unit.io",
        "main": "tests.unit.test_infra_maintenance_main",
        "orchestrator": "tests.unit.test_infra_workspace_orchestrator",
        "refactor": "tests.unit.refactor",
        "release": "tests.unit.release",
        "runner": "tests.unit.test_infra_subprocess_core",
        "service": "tests.unit.test_infra_versioning",
        "svc": "tests.unit.test_infra_workspace_sync",
        "test_atomic_write_fail": "tests.unit.test_infra_workspace_sync",
        "test_atomic_write_ok": "tests.unit.test_infra_workspace_sync",
        "test_bump_version_invalid": "tests.unit.test_infra_versioning",
        "test_bump_version_result_type": "tests.unit.test_infra_versioning",
        "test_bump_version_valid": "tests.unit.test_infra_versioning",
        "test_capture_cases": "tests.unit.test_infra_subprocess_core",
        "test_cli_forwards_canonical_root": "tests.unit.test_infra_workspace_sync",
        "test_cli_result_by_project_root": "tests.unit.test_infra_workspace_sync",
        "test_current_workspace_version": "tests.unit.test_infra_versioning",
        "test_gitignore_entry_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_gitignore_sync_failure": "tests.unit.test_infra_workspace_sync",
        "test_gitignore_write_failure": "tests.unit.test_infra_workspace_sync",
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
        "test_infra_subprocess_core": "tests.unit.test_infra_subprocess_core",
        "test_infra_subprocess_extra": "tests.unit.test_infra_subprocess_extra",
        "test_infra_toml_io": "tests.unit.test_infra_toml_io",
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
        "test_main_all_groups_defined": "tests.unit.test_infra_main",
        "test_main_group_descriptions_are_present": "tests.unit.test_infra_main",
        "test_main_help_flag_returns_zero": "tests.unit.test_infra_main",
        "test_main_returns_error_when_no_args": "tests.unit.test_infra_main",
        "test_main_unknown_group_returns_error": "tests.unit.test_infra_main",
        "test_maintenance_rejects_apply_flag": "tests.unit.test_infra_maintenance_cli",
        "test_migrate_makefile_not_found_non_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_pyproject_flext_core_non_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_apply_updates_project_files": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_discovery_failure": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_dry_run_reports_changes_without_writes": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_execute_returns_failure": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_flext_core_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_project_skipped": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_gitignore_already_normalized_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_handles_missing_pyproject_gracefully": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_has_flext_core_dependency_in_poetry": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_deps_not_table": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_table_missing": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_makefile_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_read_failure": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_no_changes_needed": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_preserves_custom_makefile_content": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_pyproject_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_workspace_root_not_exists": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_project_detection": "tests.unit.test_infra_workspace_migrator",
        "test_parse_semver_invalid": "tests.unit.test_infra_versioning",
        "test_parse_semver_result_type": "tests.unit.test_infra_versioning",
        "test_parse_semver_valid": "tests.unit.test_infra_versioning",
        "test_replace_project_version": "tests.unit.test_infra_versioning",
        "test_run_cases": "tests.unit.test_infra_subprocess_core",
        "test_run_raw_cases": "tests.unit.test_infra_subprocess_core",
        "test_sync_basemk_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_error_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_regenerates_project_makefile_without_legacy_passthrough": "tests.unit.test_infra_workspace_sync",
        "test_sync_root_validation": "tests.unit.test_infra_workspace_sync",
        "test_sync_success_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_project_makefile_for_standalone_project": "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_workspace_makefile_for_workspace_root": "tests.unit.test_infra_workspace_sync",
        "test_workspace_cli_migrate_command": "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_output_contains_summary": "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_rejects_migrate_flags_for_detect": "tests.unit.test_infra_workspace_cli",
        "test_workspace_makefile_generator_declares_canonical_workspace_variables": "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_reuses_mod_and_boot_feedback": "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_sanitizes_orchestrator_env": "tests.unit.test_infra_workspace_sync",
        "test_workspace_migrator_error_handling_on_invalid_workspace": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_read_error": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_pyproject_write_error": "tests.unit.test_infra_workspace_migrator_deps",
        "validate": "tests.unit.validate",
        "workspace_main": "tests.unit.test_infra_workspace_main",
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
