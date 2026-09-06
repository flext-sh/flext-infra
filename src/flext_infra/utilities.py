"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u
from flext_infra._utilities._rope.pep695_patch import FlextInfraUtilitiesRopePep695Patch
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities.class_nesting import FlextInfraUtilitiesClassNesting
from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
from flext_infra._utilities.compatibility_aliases import (
    FlextInfraUtilitiesCompatibilityAliases,
)
from flext_infra._utilities.deferred_self_reference_ast import (
    FlextInfraUtilitiesDeferredSelfReference,
)
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit
from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix
from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from flext_infra._utilities.managed_conflicts import FlextInfraUtilitiesManagedConflicts
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.namespace_analysis import (
    FlextInfraUtilitiesRefactorNamespaceFlext,
)
from flext_infra._utilities.namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra._utilities.namespace_facades import (
    FlextInfraUtilitiesRefactorNamespaceFacades,
)
from flext_infra._utilities.namespace_moves import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra._utilities.private_imports import FlextInfraUtilitiesPrivateImports
from flext_infra._utilities.process import FlextInfraUtilitiesProcess
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra._utilities.pyrefly import FlextInfraUtilitiesPyrefly
from flext_infra._utilities.pyproject_conform import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities.qualified_names import FlextInfraUtilitiesQualifiedNames
from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
from flext_infra._utilities.release import FlextInfraUtilitiesRelease
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
from flext_infra._utilities.resource_limits import FlextInfraUtilitiesResourceLimits
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities.rope_class_move import FlextInfraUtilitiesRopeClassMove
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities.rope_module_patch import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities.rope_structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
from flext_infra._utilities.silent_failure_ast import (
    FlextInfraUtilitiesSilentFailureAst,
)
from flext_infra._utilities.transformer_header import (
    FlextInfraUtilitiesTransformerHeader,
)
from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
from flext_infra._utilities.worktree_lifecycle import FlextInfraWorktreeLifecycle
from flext_infra._utilities.worktree_provisioning import FlextInfraWorktreeProvisioning
from flext_infra._utilities.workspace_fingerprint import (
    FlextInfraUtilitiesWorkspaceFingerprint,
)
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration


class FlextInfraUtilities(u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import m, u

        u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=Path(".")))
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(repository_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesClassNesting,
        FlextInfraUtilitiesProcess,
        FlextInfraUtilitiesResourceLimits,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCompatibilityAliases,
        FlextInfraUtilitiesCodegenNamespace,
        FlextInfraUtilitiesPyprojectConform,
        FlextInfraUtilitiesPyrefly,
        FlextInfraUtilitiesProjectManagedArtifacts,
        FlextInfraUtilitiesQualifiedNames,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeAnalysisWorkspace,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeClassMove,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeInventory,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeModulePatch,
        FlextInfraUtilitiesRopeRuntime,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesRopeStructure,
        FlextInfraUtilitiesRopePep695Patch,
        FlextInfraUtilitiesTransformerHeader,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesDocsApi,
        FlextInfraUtilitiesDocsAudit,
        FlextInfraUtilitiesDocsBuild,
        FlextInfraUtilitiesDocsContract,
        FlextInfraUtilitiesDocsFix,
        FlextInfraUtilitiesDocsGenerate,
        FlextInfraUtilitiesDocsRender,
        FlextInfraUtilitiesDocsScope,
        FlextInfraUtilitiesDocsValidate,
        FlextInfraUtilitiesDependencies,
        FlextInfraUtilitiesDeferredSelfReference,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesManagedConflicts,
        FlextInfraUtilitiesPrivateImports,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesRefactorNamespaceFlext,
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceFacades,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRepository,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesSilentFailureAst,
        FlextInfraUtilitiesVersioning,
        FlextInfraWorktreeLifecycle,
        FlextInfraWorktreeProvisioning,
        FlextInfraUtilitiesWorkspaceFingerprint,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""

        _rope_pep695_patch_applied: bool = (
            FlextInfraUtilitiesRopePep695Patch.apply() or True
        )


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
