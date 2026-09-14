# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.workspace package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_beads_environment_sync import TestsFlextInfraBeadsEnvironmentSync
    from .test_detector_owns_no_project_registry import (
        TestsFlextInfraDetectorOwnsNoProjectRegistry,
    )
    from .test_docs_contract_toc_placement import (
        TestsFlextInfraDocsContractTocPlacement,
    )
    from .test_docs_scope_worktree import TestsFlextInfraDocsScopeWorktree
    from .test_environment_provenance import (
        TestsFlextInfraWorkspaceEnvironmentProvenance,
    )
    from .test_facade_environment_sync import TestsFlextInfraFacadeEnvironmentSync
    from .test_flext_worktree_binding import TestsFlextInfraWorktreeBinding
    from .test_lane_owns_an_isolated_environment import (
        TestsFlextInfraLaneOwnsAnIsolatedEnvironment,
    )
    from .test_main import TestsFlextInfraWorkspaceMain
    from .test_mise_distribution_policy import TestsFlextInfraMiseDistributionPolicy
    from .test_provider_resolution_ssh_remotes import (
        TestsFlextInfraProviderResolutionAcceptsSshRemotes,
    )
    from .test_repository_local_topology import TestsFlextInfraRepositoryLocalTopology
    from .test_vscode import TestsFlextInfraCodegenVscode
    from .test_worktree_add_is_unprovisioned import (
        TestsFlextInfraWorktreeAddIsUnprovisioned,
    )
    from .test_worktree_provisioning_gitlinks import (
        TestsFlextInfraWorktreeProvisioningGitlinks,
    )
    from .test_worktree_security_boundaries import (
        TestsFlextInfraWorktreeSecurityBoundaries,
    )
__all__: tuple[str, ...] = (
    "TestsFlextInfraBeadsEnvironmentSync",
    "TestsFlextInfraCodegenVscode",
    "TestsFlextInfraDetectorOwnsNoProjectRegistry",
    "TestsFlextInfraDocsContractTocPlacement",
    "TestsFlextInfraDocsScopeWorktree",
    "TestsFlextInfraFacadeEnvironmentSync",
    "TestsFlextInfraLaneOwnsAnIsolatedEnvironment",
    "TestsFlextInfraMiseDistributionPolicy",
    "TestsFlextInfraProviderResolutionAcceptsSshRemotes",
    "TestsFlextInfraRepositoryLocalTopology",
    "TestsFlextInfraWorkspaceEnvironmentProvenance",
    "TestsFlextInfraWorkspaceMain",
    "TestsFlextInfraWorktreeAddIsUnprovisioned",
    "TestsFlextInfraWorktreeBinding",
    "TestsFlextInfraWorktreeProvisioningGitlinks",
    "TestsFlextInfraWorktreeSecurityBoundaries",
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
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_beads_environment_sync": ("TestsFlextInfraBeadsEnvironmentSync",),
            ".test_detector_owns_no_project_registry": (
                "TestsFlextInfraDetectorOwnsNoProjectRegistry",
            ),
            ".test_docs_contract_toc_placement": (
                "TestsFlextInfraDocsContractTocPlacement",
            ),
            ".test_docs_scope_worktree": ("TestsFlextInfraDocsScopeWorktree",),
            ".test_environment_provenance": (
                "TestsFlextInfraWorkspaceEnvironmentProvenance",
            ),
            ".test_facade_environment_sync": ("TestsFlextInfraFacadeEnvironmentSync",),
            ".test_flext_worktree_binding": ("TestsFlextInfraWorktreeBinding",),
            ".test_lane_owns_an_isolated_environment": (
                "TestsFlextInfraLaneOwnsAnIsolatedEnvironment",
            ),
            ".test_main": ("TestsFlextInfraWorkspaceMain",),
            ".test_mise_distribution_policy": (
                "TestsFlextInfraMiseDistributionPolicy",
            ),
            ".test_provider_resolution_ssh_remotes": (
                "TestsFlextInfraProviderResolutionAcceptsSshRemotes",
            ),
            ".test_repository_local_topology": (
                "TestsFlextInfraRepositoryLocalTopology",
            ),
            ".test_vscode": ("TestsFlextInfraCodegenVscode",),
            ".test_worktree_add_is_unprovisioned": (
                "TestsFlextInfraWorktreeAddIsUnprovisioned",
            ),
            ".test_worktree_provisioning_gitlinks": (
                "TestsFlextInfraWorktreeProvisioningGitlinks",
            ),
            ".test_worktree_security_boundaries": (
                "TestsFlextInfraWorktreeSecurityBoundaries",
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
