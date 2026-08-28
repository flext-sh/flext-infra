# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _utilities as _utilities
    from . import basemk as basemk
    from . import check as check
    from . import codegen as codegen
    from . import codemod as codemod
    from . import container as container
    from . import deps as deps
    from . import detectors as detectors
    from . import discovery as discovery
    from . import docs as docs
    from . import github as github
    from . import io as io
    from . import refactor as refactor
    from . import release as release
    from . import transformers as transformers
    from . import validate as validate
    from . import workspace as workspace
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .check.tests_workspace_check import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from .cli_what_selector_tests import TestsFlextInfraCliWhatSelector
    from .fixtures import (
        deptry_report_payload,
        models_resource,
        modernizer_workspace,
        modernizer_workspace_with_projects,
        real_docs_project,
        real_makefile_project,
        real_python_package,
        real_toml_project,
        real_workspace,
        rope_workspace,
        services_resource,
        tool_config_document,
    )
    from .fixtures_git import real_git_repo
    from .runner_service import RealSubprocessRunner
    from .test_custom_handler_policy_is_profile_aware import (
        TestsFlextInfraCustomHandlerPolicyIsProfileAware,
    )
    from .test_custom_make_surface_is_derived import (
        TestsFlextInfraCustomMakeSurfaceIsDerived,
    )
    from .test_custom_make_surface_is_single import (
        TestsFlextInfraCustomMakeSurfaceIsSingle,
    )
    from .test_custom_surface_never_shadows_public_verbs import (
        TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs,
    )
    from .test_flext_service_base_alias import (
        test_service_base_generic_alias_flext_is_permitted,
    )
    from .test_gitignore_is_generated_from_ssot import (
        TestsFlextInfraGitignoreIsGeneratedFromSsot,
    )
    from .test_infra_constants_core import TestsFlextInfraInfraConstantsCore
    from .test_infra_constants_extra import TestsFlextInfraInfraConstantsExtra
    from .test_infra_git_identity_submodules import TestInfraGitIdentitySubmodules
    from .test_infra_main import TestsFlextInfraInfraMain
    from .test_infra_maintenance_cli import TestsFlextInfraInfraMaintenanceCli
    from .test_infra_maintenance_init import TestsFlextInfraInfraMaintenanceInit
    from .test_infra_maintenance_main import TestsFlextInfraInfraMaintenanceMain
    from .test_infra_maintenance_python_version import (
        TestsFlextInfraInfraMaintenancePythonVersion,
    )
    from .test_infra_paths import TestsFlextInfraInfraPaths
    from .test_infra_patterns_core import TestsFlextInfraInfraPatternsCore
    from .test_infra_patterns_extra import TestsFlextInfraInfraPatternsExtra
    from .test_infra_protocols import TestsFlextInfraInfraProtocols
    from .test_infra_public_api import TestsFlextInfraPublicApi
    from .test_infra_refactor_rope_migrations import (
        TestsFlextInfraInfraRefactorRopeMigrations,
    )
    from .test_infra_reporting_core import TestsFlextInfraInfraReportingCore
    from .test_infra_reporting_extra import TestsFlextInfraInfraReportingExtra
    from .test_infra_root_export_contract import TestsFlextInfraRootExportContract
    from .test_infra_rope_imports import TestsFlextInfraRopeImports
    from .test_infra_rope_service import TestsFlextInfraInfraRopeService
    from .test_infra_selection import TestsFlextInfraInfraSelection
    from .test_infra_typings import TestsFlextInfraInfraTypings
    from .test_infra_utilities import TestsFlextInfraInfraUtilities
    from .test_infra_version_core import TestsFlextInfraInfraVersionCore
    from .test_infra_version_extra import TestsFlextInfraInfraVersionExtra
    from .test_infra_versioning import TestsFlextInfraInfraVersioning
    from .test_infra_workspace_orchestrator import (
        TestsFlextInfraInfraWorkspaceOrchestrator,
        orchestrator,
    )
    from .test_lockfile_is_tracked_at_the_resolution_root import (
        TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot,
    )
    from .test_make_parse_is_side_effect_free import (
        TestsFlextInfraMakeParseIsSideEffectFree,
    )
    from .test_make_surface_never_silences_failures import (
        TestsFlextInfraMakeSurfaceNeverSilencesFailures,
    )
    from .test_pyproject_conform_preserves_lint_scope import (
        TestsFlextInfraPyprojectConformPreservesLintScope,
    )
    from .test_pyproject_conform_topology_sources import (
        TestsFlextInfraPyprojectConformTopologySources,
    )
    from .test_python_selector_render import TestsFlextInfraPythonSelectorRender
    from .test_version_diag import test_version_diag
    from .test_version_diag2 import test_version_full_import
    from .test_workspace_check_scope import TestsFlextInfraWorkspaceCheckScope
    from .workspace.worktree_fixture import WorktreeFixture
    from .workspace_factory import TestsFlextInfraWorkspaceFactory
__all__: tuple[str, ...] = (
    "RealSubprocessRunner",
    "TestInfraGitIdentitySubmodules",
    "TestsFlextInfraCliWhatSelector",
    "TestsFlextInfraCustomHandlerPolicyIsProfileAware",
    "TestsFlextInfraCustomMakeSurfaceIsDerived",
    "TestsFlextInfraCustomMakeSurfaceIsSingle",
    "TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs",
    "TestsFlextInfraGitignoreIsGeneratedFromSsot",
    "TestsFlextInfraInfraConstantsCore",
    "TestsFlextInfraInfraConstantsExtra",
    "TestsFlextInfraInfraMain",
    "TestsFlextInfraInfraMaintenanceCli",
    "TestsFlextInfraInfraMaintenanceInit",
    "TestsFlextInfraInfraMaintenanceMain",
    "TestsFlextInfraInfraMaintenancePythonVersion",
    "TestsFlextInfraInfraPaths",
    "TestsFlextInfraInfraPatternsCore",
    "TestsFlextInfraInfraPatternsExtra",
    "TestsFlextInfraInfraProtocols",
    "TestsFlextInfraInfraRefactorRopeMigrations",
    "TestsFlextInfraInfraReportingCore",
    "TestsFlextInfraInfraReportingExtra",
    "TestsFlextInfraInfraRopeService",
    "TestsFlextInfraInfraSelection",
    "TestsFlextInfraInfraTypings",
    "TestsFlextInfraInfraUtilities",
    "TestsFlextInfraInfraVersionCore",
    "TestsFlextInfraInfraVersionExtra",
    "TestsFlextInfraInfraVersioning",
    "TestsFlextInfraInfraWorkspaceOrchestrator",
    "TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot",
    "TestsFlextInfraMakeParseIsSideEffectFree",
    "TestsFlextInfraMakeSurfaceNeverSilencesFailures",
    "TestsFlextInfraPublicApi",
    "TestsFlextInfraPyprojectConformPreservesLintScope",
    "TestsFlextInfraPyprojectConformTopologySources",
    "TestsFlextInfraPythonSelectorRender",
    "TestsFlextInfraRootExportContract",
    "TestsFlextInfraRopeImports",
    "TestsFlextInfraWorkspaceCheckScope",
    "TestsFlextInfraWorkspaceFactory",
    "WorktreeFixture",
    "_utilities",
    "basemk",
    "c",
    "check",
    "codegen",
    "codemod",
    "container",
    "d",
    "deps",
    "deptry_report_payload",
    "detectors",
    "discovery",
    "docs",
    "e",
    "github",
    "h",
    "io",
    "m",
    "models_resource",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "orchestrator",
    "p",
    "r",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "refactor",
    "release",
    "rope_workspace",
    "s",
    "services_resource",
    "t",
    "td",
    "test_service_base_generic_alias_flext_is_permitted",
    "test_version_diag",
    "test_version_full_import",
    "test_workspace_check_main_returns_error_without_projects",
    "tf",
    "tk",
    "tm",
    "tool_config_document",
    "transformers",
    "tv",
    "u",
    "validate",
    "workspace",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._utilities": ("_utilities",),
            ".basemk": ("basemk",),
            ".check": ("check",),
            ".check.tests_workspace_check": (
                "test_workspace_check_main_returns_error_without_projects",
            ),
            ".cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
            ".codegen": ("codegen",),
            ".codemod": ("codemod",),
            ".container": ("container",),
            ".deps": ("deps",),
            ".detectors": ("detectors",),
            ".discovery": ("discovery",),
            ".docs": ("docs",),
            ".fixtures": (
                "deptry_report_payload",
                "models_resource",
                "modernizer_workspace",
                "modernizer_workspace_with_projects",
                "real_docs_project",
                "real_makefile_project",
                "real_python_package",
                "real_toml_project",
                "real_workspace",
                "rope_workspace",
                "services_resource",
                "tool_config_document",
            ),
            ".fixtures_git": ("real_git_repo",),
            ".github": ("github",),
            ".io": ("io",),
            ".refactor": ("refactor",),
            ".release": ("release",),
            ".runner_service": ("RealSubprocessRunner",),
            ".test_custom_handler_policy_is_profile_aware": (
                "TestsFlextInfraCustomHandlerPolicyIsProfileAware",
            ),
            ".test_custom_make_surface_is_derived": (
                "TestsFlextInfraCustomMakeSurfaceIsDerived",
            ),
            ".test_custom_make_surface_is_single": (
                "TestsFlextInfraCustomMakeSurfaceIsSingle",
            ),
            ".test_custom_surface_never_shadows_public_verbs": (
                "TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs",
            ),
            ".test_flext_service_base_alias": (
                "test_service_base_generic_alias_flext_is_permitted",
            ),
            ".test_gitignore_is_generated_from_ssot": (
                "TestsFlextInfraGitignoreIsGeneratedFromSsot",
            ),
            ".test_infra_constants_core": ("TestsFlextInfraInfraConstantsCore",),
            ".test_infra_constants_extra": ("TestsFlextInfraInfraConstantsExtra",),
            ".test_infra_git_identity_submodules": ("TestInfraGitIdentitySubmodules",),
            ".test_infra_main": ("TestsFlextInfraInfraMain",),
            ".test_infra_maintenance_cli": ("TestsFlextInfraInfraMaintenanceCli",),
            ".test_infra_maintenance_init": ("TestsFlextInfraInfraMaintenanceInit",),
            ".test_infra_maintenance_main": ("TestsFlextInfraInfraMaintenanceMain",),
            ".test_infra_maintenance_python_version": (
                "TestsFlextInfraInfraMaintenancePythonVersion",
            ),
            ".test_infra_paths": ("TestsFlextInfraInfraPaths",),
            ".test_infra_patterns_core": ("TestsFlextInfraInfraPatternsCore",),
            ".test_infra_patterns_extra": ("TestsFlextInfraInfraPatternsExtra",),
            ".test_infra_protocols": ("TestsFlextInfraInfraProtocols",),
            ".test_infra_public_api": ("TestsFlextInfraPublicApi",),
            ".test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".test_infra_reporting_core": ("TestsFlextInfraInfraReportingCore",),
            ".test_infra_reporting_extra": ("TestsFlextInfraInfraReportingExtra",),
            ".test_infra_root_export_contract": ("TestsFlextInfraRootExportContract",),
            ".test_infra_rope_imports": ("TestsFlextInfraRopeImports",),
            ".test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".test_infra_selection": ("TestsFlextInfraInfraSelection",),
            ".test_infra_typings": ("TestsFlextInfraInfraTypings",),
            ".test_infra_utilities": ("TestsFlextInfraInfraUtilities",),
            ".test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".test_infra_versioning": ("TestsFlextInfraInfraVersioning",),
            ".test_infra_workspace_orchestrator": (
                "TestsFlextInfraInfraWorkspaceOrchestrator",
                "orchestrator",
            ),
            ".test_lockfile_is_tracked_at_the_resolution_root": (
                "TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot",
            ),
            ".test_make_parse_is_side_effect_free": (
                "TestsFlextInfraMakeParseIsSideEffectFree",
            ),
            ".test_make_surface_never_silences_failures": (
                "TestsFlextInfraMakeSurfaceNeverSilencesFailures",
            ),
            ".test_pyproject_conform_preserves_lint_scope": (
                "TestsFlextInfraPyprojectConformPreservesLintScope",
            ),
            ".test_pyproject_conform_topology_sources": (
                "TestsFlextInfraPyprojectConformTopologySources",
            ),
            ".test_python_selector_render": ("TestsFlextInfraPythonSelectorRender",),
            ".test_version_diag": ("test_version_diag",),
            ".test_version_diag2": ("test_version_full_import",),
            ".test_workspace_check_scope": ("TestsFlextInfraWorkspaceCheckScope",),
            ".transformers": ("transformers",),
            ".validate": ("validate",),
            ".workspace": ("workspace",),
            ".workspace.worktree_fixture": ("WorktreeFixture",),
            ".workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
