# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

from tests.unit._utilities import _LAZY_IMPORTS as _CHILD_LAZY_0
from tests.unit.basemk import _LAZY_IMPORTS as _CHILD_LAZY_1
from tests.unit.check import _LAZY_IMPORTS as _CHILD_LAZY_2
from tests.unit.codegen import _LAZY_IMPORTS as _CHILD_LAZY_3
from tests.unit.container import _LAZY_IMPORTS as _CHILD_LAZY_4
from tests.unit.deps import _LAZY_IMPORTS as _CHILD_LAZY_5
from tests.unit.discovery import _LAZY_IMPORTS as _CHILD_LAZY_6
from tests.unit.docs import _LAZY_IMPORTS as _CHILD_LAZY_7
from tests.unit.github import _LAZY_IMPORTS as _CHILD_LAZY_8
from tests.unit.io import _LAZY_IMPORTS as _CHILD_LAZY_9
from tests.unit.refactor import _LAZY_IMPORTS as _CHILD_LAZY_10
from tests.unit.release import _LAZY_IMPORTS as _CHILD_LAZY_11
from tests.unit.validate import _LAZY_IMPORTS as _CHILD_LAZY_12

if TYPE_CHECKING:
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
    from tests.unit.test_infra_constants_core import *
    from tests.unit.test_infra_constants_extra import *
    from tests.unit.test_infra_git import *
    from tests.unit.test_infra_init_lazy_core import *
    from tests.unit.test_infra_init_lazy_submodules import *
    from tests.unit.test_infra_main import *
    from tests.unit.test_infra_maintenance_cli import *
    from tests.unit.test_infra_maintenance_init import *
    from tests.unit.test_infra_maintenance_main import *
    from tests.unit.test_infra_maintenance_python_version import *
    from tests.unit.test_infra_paths import *
    from tests.unit.test_infra_patterns_core import *
    from tests.unit.test_infra_patterns_extra import *
    from tests.unit.test_infra_protocols import *
    from tests.unit.test_infra_reporting_core import *
    from tests.unit.test_infra_reporting_extra import *
    from tests.unit.test_infra_selection import *
    from tests.unit.test_infra_subprocess_core import *
    from tests.unit.test_infra_subprocess_extra import *
    from tests.unit.test_infra_toml_io import *
    from tests.unit.test_infra_typings import *
    from tests.unit.test_infra_utilities import *
    from tests.unit.test_infra_version_core import *
    from tests.unit.test_infra_version_extra import *
    from tests.unit.test_infra_versioning import *
    from tests.unit.test_infra_workspace_cli import *
    from tests.unit.test_infra_workspace_detector import *
    from tests.unit.test_infra_workspace_init import *
    from tests.unit.test_infra_workspace_main import *
    from tests.unit.test_infra_workspace_migrator import *
    from tests.unit.test_infra_workspace_migrator_deps import *
    from tests.unit.test_infra_workspace_migrator_dryrun import *
    from tests.unit.test_infra_workspace_migrator_errors import *
    from tests.unit.test_infra_workspace_migrator_internal import *
    from tests.unit.test_infra_workspace_migrator_pyproject import *
    from tests.unit.test_infra_workspace_orchestrator import *
    from tests.unit.test_infra_workspace_sync import *
    from tests.unit.validate import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    **_CHILD_LAZY_0,
    **_CHILD_LAZY_1,
    **_CHILD_LAZY_2,
    **_CHILD_LAZY_3,
    **_CHILD_LAZY_4,
    **_CHILD_LAZY_5,
    **_CHILD_LAZY_6,
    **_CHILD_LAZY_7,
    **_CHILD_LAZY_8,
    **_CHILD_LAZY_9,
    **_CHILD_LAZY_10,
    **_CHILD_LAZY_11,
    **_CHILD_LAZY_12,
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
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
