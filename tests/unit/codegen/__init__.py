# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .lazy_init_bootstrap_package_tests import (
        TestsFlextInfraLazyInitBootstrapPackage,
    )
    from .lazy_init_fixture_settings_tests import (
        TestsFlextInfraLazyInitFixtureSettingsCollision,
    )
    from .lazy_init_generation_tests import TestsFlextInfraCodegenGeneration
    from .lazy_init_helpers_tests import TestsFlextInfraLazyInitHelpers
    from .lazy_init_process_tests import TestsFlextInfraLazyInitProcessing
    from .lazy_init_registry_wrapper_tests import TestsFlextInfraLazyInitCleanup
    from .lazy_init_runtime_tests import TestsFlextInfraLazyInitRuntime
    from .lazy_init_service_tests import TestsFlextInfraCodegenLazyInitService
    from .lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from .lazy_init_transforms_tests import TestsFlextInfraLazyInitTransforms
    from .make_test_selector_tests import TestsMakeTestSelector
    from .scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from .test_codegen_artifact_ssot import (
        CodegenSpec,
        TestsCodegenArtifactSsot,
        codegen,
    )
    from .test_codegen_beads_projection import TestsCodegenBeadsProjection
    from .test_codegen_conform_progress import TestsFlextInfraCodegenConformProgress
    from .test_codegen_hook_conformance import TestGitHookConformance
    from .test_codegen_linked_worktree_manifest import TestCodegenLinkedWorktreeTopology
    from .test_codegen_make_environment import TestsCodegenMakeEnvironment
    from .test_codegen_pyproject_conform import TestsFlextInfraCodegenPyprojectConform
    from .test_codegen_uv_exclude_newer_overlay import TestCodegenUvExcludeNewerOverlay
    from .test_managed_conflicts import TestsFlextInfraCodegenManagedConflicts
    from .test_managed_maintenance_headers import (
        TestsFlextInfraManagedMaintenanceHeaders,
    )
    from .test_review_mro_vw2w_template_contracts import TestsReviewTemplateContracts
    from .test_vscode_owner_merge import TestsVscodeOwnerMerge
    from .test_workspace_root_setup_submodules import TestsWorkspaceRootSetupSubmodules
__all__: tuple[str, ...] = (
    "CodegenSpec",
    "TestAllDirectoriesScanned",
    "TestCheckOnlyMode",
    "TestCodegenLinkedWorktreeTopology",
    "TestCodegenUvExcludeNewerOverlay",
    "TestEdgeCases",
    "TestExcludedDirectories",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestGitHookConformance",
    "TestsCodegenArtifactSsot",
    "TestsCodegenBeadsProjection",
    "TestsCodegenMakeEnvironment",
    "TestsFlextInfraCodegenConformProgress",
    "TestsFlextInfraCodegenGeneration",
    "TestsFlextInfraCodegenLazyInitService",
    "TestsFlextInfraCodegenManagedConflicts",
    "TestsFlextInfraCodegenPyprojectConform",
    "TestsFlextInfraLazyInitBootstrapPackage",
    "TestsFlextInfraLazyInitCleanup",
    "TestsFlextInfraLazyInitFixtureSettingsCollision",
    "TestsFlextInfraLazyInitHelpers",
    "TestsFlextInfraLazyInitProcessing",
    "TestsFlextInfraLazyInitRuntime",
    "TestsFlextInfraLazyInitTransforms",
    "TestsFlextInfraManagedMaintenanceHeaders",
    "TestsMakeTestSelector",
    "TestsReviewTemplateContracts",
    "TestsVscodeOwnerMerge",
    "TestsWorkspaceRootSetupSubmodules",
    "c",
    "codegen",
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
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".lazy_init_bootstrap_package_tests": (
                "TestsFlextInfraLazyInitBootstrapPackage",
            ),
            ".lazy_init_fixture_settings_tests": (
                "TestsFlextInfraLazyInitFixtureSettingsCollision",
            ),
            ".lazy_init_generation_tests": ("TestsFlextInfraCodegenGeneration",),
            ".lazy_init_helpers_tests": ("TestsFlextInfraLazyInitHelpers",),
            ".lazy_init_process_tests": ("TestsFlextInfraLazyInitProcessing",),
            ".lazy_init_registry_wrapper_tests": ("TestsFlextInfraLazyInitCleanup",),
            ".lazy_init_runtime_tests": ("TestsFlextInfraLazyInitRuntime",),
            ".lazy_init_service_tests": ("TestsFlextInfraCodegenLazyInitService",),
            ".lazy_init_tests": (
                "TestAllDirectoriesScanned",
                "TestCheckOnlyMode",
                "TestEdgeCases",
                "TestExcludedDirectories",
            ),
            ".lazy_init_transforms_tests": ("TestsFlextInfraLazyInitTransforms",),
            ".make_test_selector_tests": ("TestsMakeTestSelector",),
            ".scaffolder_naming_tests": (
                "TestGeneratedClassNamingConvention",
                "TestGeneratedFilesAreValidPython",
            ),
            ".test_codegen_artifact_ssot": (
                "CodegenSpec",
                "TestsCodegenArtifactSsot",
                "codegen",
            ),
            ".test_codegen_beads_projection": ("TestsCodegenBeadsProjection",),
            ".test_codegen_conform_progress": (
                "TestsFlextInfraCodegenConformProgress",
            ),
            ".test_codegen_hook_conformance": ("TestGitHookConformance",),
            ".test_codegen_linked_worktree_manifest": (
                "TestCodegenLinkedWorktreeTopology",
            ),
            ".test_codegen_make_environment": ("TestsCodegenMakeEnvironment",),
            ".test_codegen_pyproject_conform": (
                "TestsFlextInfraCodegenPyprojectConform",
            ),
            ".test_codegen_uv_exclude_newer_overlay": (
                "TestCodegenUvExcludeNewerOverlay",
            ),
            ".test_managed_conflicts": ("TestsFlextInfraCodegenManagedConflicts",),
            ".test_managed_maintenance_headers": (
                "TestsFlextInfraManagedMaintenanceHeaders",
            ),
            ".test_review_mro_vw2w_template_contracts": (
                "TestsReviewTemplateContracts",
            ),
            ".test_vscode_owner_merge": ("TestsVscodeOwnerMerge",),
            ".test_workspace_root_setup_submodules": (
                "TestsWorkspaceRootSetupSubmodules",
            ),
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
