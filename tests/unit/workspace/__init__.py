# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import make_constants_tests as make_constants_tests
    from . import resolve_what_tests as resolve_what_tests
    from . import test_docs_contract_toc_placement as test_docs_contract_toc_placement
    from . import test_docs_scope_worktree as test_docs_scope_worktree
    from . import test_flext_worktree_binding as test_flext_worktree_binding
    from . import test_git_remote_identity as test_git_remote_identity
    from . import (
        test_lane_owns_an_isolated_environment as test_lane_owns_an_isolated_environment,
    )
    from . import test_worktree_add_contract as test_worktree_add_contract
    from . import (
        test_worktree_add_is_unprovisioned as test_worktree_add_is_unprovisioned,
    )
    from . import test_worktree_attached_repository as test_worktree_attached_repository
    from . import test_worktree_paths as test_worktree_paths
    from . import (
        test_worktree_provisioning_gitlinks as test_worktree_provisioning_gitlinks,
    )
    from . import test_worktree_removal as test_worktree_removal
    from . import test_worktree_security_boundaries as test_worktree_security_boundaries
    from . import test_worktree_topology as test_worktree_topology
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_detector_owns_no_project_registry import (
        TestsDetectorOwnsNoProjectRegistry,
    )
    from .test_environment_provenance import (
        TestsFlextInfraWorkspaceEnvironmentProvenance,
    )
    from .test_facade_environment_sync import (
        TestsFlextInfraFacadeBaseMk,
        TestsFlextInfraFacadeEnvironmentSync,
    )
    from .test_main import TestsFlextInfraWorkspaceMain
    from .test_manifest_v2_contract import TestsWorkspaceManifestV2Contract
    from .test_vscode import TestsFlextInfraCodegenVscode
    from .test_workspace_root_make_contract import TestsWorkspaceRootMakeContract
    from .worktree_fixture import WorktreeFixture
__all__: tuple[str, ...] = (
    "TestsDetectorOwnsNoProjectRegistry",
    "TestsFlextInfraCodegenVscode",
    "TestsFlextInfraFacadeBaseMk",
    "TestsFlextInfraFacadeEnvironmentSync",
    "TestsFlextInfraWorkspaceEnvironmentProvenance",
    "TestsFlextInfraWorkspaceMain",
    "TestsWorkspaceManifestV2Contract",
    "TestsWorkspaceRootMakeContract",
    "WorktreeFixture",
    "c",
    "d",
    "e",
    "h",
    "m",
    "make_constants_tests",
    "p",
    "r",
    "resolve_what_tests",
    "s",
    "t",
    "td",
    "test_docs_contract_toc_placement",
    "test_docs_scope_worktree",
    "test_flext_worktree_binding",
    "test_git_remote_identity",
    "test_lane_owns_an_isolated_environment",
    "test_worktree_add_contract",
    "test_worktree_add_is_unprovisioned",
    "test_worktree_attached_repository",
    "test_worktree_paths",
    "test_worktree_provisioning_gitlinks",
    "test_worktree_removal",
    "test_worktree_security_boundaries",
    "test_worktree_topology",
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
            ".make_constants_tests": ("make_constants_tests",),
            ".resolve_what_tests": ("resolve_what_tests",),
            ".test_detector_owns_no_project_registry": (
                "TestsDetectorOwnsNoProjectRegistry",
            ),
            ".test_docs_contract_toc_placement": ("test_docs_contract_toc_placement",),
            ".test_docs_scope_worktree": ("test_docs_scope_worktree",),
            ".test_environment_provenance": (
                "TestsFlextInfraWorkspaceEnvironmentProvenance",
            ),
            ".test_facade_environment_sync": (
                "TestsFlextInfraFacadeBaseMk",
                "TestsFlextInfraFacadeEnvironmentSync",
            ),
            ".test_flext_worktree_binding": ("test_flext_worktree_binding",),
            ".test_git_remote_identity": ("test_git_remote_identity",),
            ".test_lane_owns_an_isolated_environment": (
                "test_lane_owns_an_isolated_environment",
            ),
            ".test_main": ("TestsFlextInfraWorkspaceMain",),
            ".test_manifest_v2_contract": ("TestsWorkspaceManifestV2Contract",),
            ".test_vscode": ("TestsFlextInfraCodegenVscode",),
            ".test_workspace_root_make_contract": ("TestsWorkspaceRootMakeContract",),
            ".test_worktree_add_contract": ("test_worktree_add_contract",),
            ".test_worktree_add_is_unprovisioned": (
                "test_worktree_add_is_unprovisioned",
            ),
            ".test_worktree_attached_repository": (
                "test_worktree_attached_repository",
            ),
            ".test_worktree_paths": ("test_worktree_paths",),
            ".test_worktree_provisioning_gitlinks": (
                "test_worktree_provisioning_gitlinks",
            ),
            ".test_worktree_removal": ("test_worktree_removal",),
            ".test_worktree_security_boundaries": (
                "test_worktree_security_boundaries",
            ),
            ".test_worktree_topology": ("test_worktree_topology",),
            ".worktree_fixture": ("WorktreeFixture",),
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
