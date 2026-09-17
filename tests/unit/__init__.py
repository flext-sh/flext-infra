# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import (
        _utilities,
        check,
        codegen,
        codemod,
        container,
        deps,
        detectors,
        discovery,
        docs,
        gates,
        github,
        io,
        maintenance,
        promoted,
        refactor,
        release,
        transformers,
        validate,
        workspace,
    )
    from .fixtures import (
        cached_runner_project,
        deptry_report_payload,
        models_resource,
        modernizer_workspace,
        modernizer_workspace_with_projects,
        policy_violation_project,
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
    from .test_cli_repository_root_contract import (
        TestsFlextInfraCliRepositoryRootContract,
    )
    from .test_cprofile_entry import TestsFlextInfraCprofileEntry
    from .test_custom_handler_policy_is_profile_aware import (
        TestsFlextInfraCustomHandlerPolicyIsProfileAware,
    )
    from .test_custom_make_surface_is_derived import (
        TestsFlextInfraCustomMakeSurfaceIsDerived,
    )
    from .test_custom_surface_never_shadows_public_verbs import (
        TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs,
    )
    from .test_flext_service_base_alias import TestsFlextInfraServiceBaseAlias
    from .test_git_fixture_isolation import TestsFlextInfraGitFixtureIsolation
    from .test_gitignore_is_generated_from_ssot import (
        TestsFlextInfraGitignoreIsGeneratedFromSsot,
    )
    from .test_infra_git_identity_submodules import TestsFlextInfraGitIdentitySubmodules
    from .test_infra_maintenance_cli import TestsFlextInfraInfraMaintenanceCli
    from .test_infra_maintenance_init import TestsFlextInfraInfraMaintenanceInit
    from .test_infra_maintenance_main import TestsFlextInfraInfraMaintenanceMain
    from .test_infra_maintenance_python_version import (
        TestsFlextInfraInfraMaintenancePythonVersion,
    )
    from .test_infra_public_api import TestsFlextInfraPublicApi
    from .test_infra_refactor_rope_migrations import (
        TestsFlextInfraInfraRefactorRopeMigrations,
    )
    from .test_infra_rope_service import TestsFlextInfraInfraRopeService
    from .test_infra_version_core import TestsFlextInfraInfraVersionCore
    from .test_infra_version_extra import TestsFlextInfraInfraVersionExtra
    from .test_lockfile_policy_projection import TestsFlextInfraLockfilePolicyProjection
    from .test_make_parse_is_side_effect_free import (
        TestsFlextInfraMakeParseIsSideEffectFree,
    )
    from .test_pyproject_conform_preserves_lint_scope import (
        TestsFlextInfraPyprojectConformPreservesLintScope,
    )
    from .test_pyproject_conform_topology_sources import (
        TestsFlextInfraPyprojectConformTopologySources,
    )
    from .test_version_diag import TestsFlextInfraVersionDiag
    from .test_version_diag2 import TestsFlextInfraVersionDiagExtra
    from .workspace_factory import TestsFlextInfraWorkspaceFactory
__all__: tuple[str, ...] = (
    "RealSubprocessRunner",
    "TestsFlextInfraCliRepositoryRootContract",
    "TestsFlextInfraCprofileEntry",
    "TestsFlextInfraCustomHandlerPolicyIsProfileAware",
    "TestsFlextInfraCustomMakeSurfaceIsDerived",
    "TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs",
    "TestsFlextInfraGitFixtureIsolation",
    "TestsFlextInfraGitIdentitySubmodules",
    "TestsFlextInfraGitignoreIsGeneratedFromSsot",
    "TestsFlextInfraInfraMaintenanceCli",
    "TestsFlextInfraInfraMaintenanceInit",
    "TestsFlextInfraInfraMaintenanceMain",
    "TestsFlextInfraInfraMaintenancePythonVersion",
    "TestsFlextInfraInfraRefactorRopeMigrations",
    "TestsFlextInfraInfraRopeService",
    "TestsFlextInfraInfraVersionCore",
    "TestsFlextInfraInfraVersionExtra",
    "TestsFlextInfraLockfilePolicyProjection",
    "TestsFlextInfraMakeParseIsSideEffectFree",
    "TestsFlextInfraPublicApi",
    "TestsFlextInfraPyprojectConformPreservesLintScope",
    "TestsFlextInfraPyprojectConformTopologySources",
    "TestsFlextInfraServiceBaseAlias",
    "TestsFlextInfraVersionDiag",
    "TestsFlextInfraVersionDiagExtra",
    "TestsFlextInfraWorkspaceFactory",
    "_utilities",
    "cached_runner_project",
    "check",
    "codegen",
    "codemod",
    "container",
    "deps",
    "deptry_report_payload",
    "detectors",
    "discovery",
    "docs",
    "gates",
    "github",
    "io",
    "maintenance",
    "models_resource",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "policy_violation_project",
    "promoted",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "refactor",
    "release",
    "rope_workspace",
    "services_resource",
    "tool_config_document",
    "transformers",
    "validate",
    "workspace",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._utilities": ("_utilities",),
            ".check": ("check",),
            ".codegen": ("codegen",),
            ".codemod": ("codemod",),
            ".container": ("container",),
            ".deps": ("deps",),
            ".detectors": ("detectors",),
            ".discovery": ("discovery",),
            ".docs": ("docs",),
            ".fixtures": (
                "cached_runner_project",
                "deptry_report_payload",
                "models_resource",
                "modernizer_workspace",
                "modernizer_workspace_with_projects",
                "policy_violation_project",
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
            ".gates": ("gates",),
            ".github": ("github",),
            ".io": ("io",),
            ".maintenance": ("maintenance",),
            ".promoted": ("promoted",),
            ".refactor": ("refactor",),
            ".release": ("release",),
            ".runner_service": ("RealSubprocessRunner",),
            ".test_cli_repository_root_contract": (
                "TestsFlextInfraCliRepositoryRootContract",
            ),
            ".test_cprofile_entry": ("TestsFlextInfraCprofileEntry",),
            ".test_custom_handler_policy_is_profile_aware": (
                "TestsFlextInfraCustomHandlerPolicyIsProfileAware",
            ),
            ".test_custom_make_surface_is_derived": (
                "TestsFlextInfraCustomMakeSurfaceIsDerived",
            ),
            ".test_custom_surface_never_shadows_public_verbs": (
                "TestsFlextInfraCustomSurfaceNeverShadowsPublicVerbs",
            ),
            ".test_flext_service_base_alias": ("TestsFlextInfraServiceBaseAlias",),
            ".test_git_fixture_isolation": ("TestsFlextInfraGitFixtureIsolation",),
            ".test_gitignore_is_generated_from_ssot": (
                "TestsFlextInfraGitignoreIsGeneratedFromSsot",
            ),
            ".test_infra_git_identity_submodules": (
                "TestsFlextInfraGitIdentitySubmodules",
            ),
            ".test_infra_maintenance_cli": ("TestsFlextInfraInfraMaintenanceCli",),
            ".test_infra_maintenance_init": ("TestsFlextInfraInfraMaintenanceInit",),
            ".test_infra_maintenance_main": ("TestsFlextInfraInfraMaintenanceMain",),
            ".test_infra_maintenance_python_version": (
                "TestsFlextInfraInfraMaintenancePythonVersion",
            ),
            ".test_infra_public_api": ("TestsFlextInfraPublicApi",),
            ".test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".test_lockfile_policy_projection": (
                "TestsFlextInfraLockfilePolicyProjection",
            ),
            ".test_make_parse_is_side_effect_free": (
                "TestsFlextInfraMakeParseIsSideEffectFree",
            ),
            ".test_pyproject_conform_preserves_lint_scope": (
                "TestsFlextInfraPyprojectConformPreservesLintScope",
            ),
            ".test_pyproject_conform_topology_sources": (
                "TestsFlextInfraPyprojectConformTopologySources",
            ),
            ".test_version_diag": ("TestsFlextInfraVersionDiag",),
            ".test_version_diag2": ("TestsFlextInfraVersionDiagExtra",),
            ".transformers": ("transformers",),
            ".validate": ("validate",),
            ".workspace": ("workspace",),
            ".workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
