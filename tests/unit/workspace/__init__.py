# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_detector_owns_no_project_registry import (
        TestsDetectorOwnsNoProjectRegistry,
    )
    from .test_docs_contract_toc_placement import (
        test_toc_is_inserted_after_h1_preceded_by_html_comment,
        test_toc_without_h1_injects_documentation_heading,
    )
    from .test_docs_scope_worktree import (
        test_project_scope_uses_declared_name_inside_worktree_lane,
    )
    from .test_environment_provenance import (
        TestsFlextInfraWorkspaceEnvironmentProvenance,
    )
    from .test_facade_environment_sync import (
        TestsFlextInfraFacadeBaseMk,
        TestsFlextInfraFacadeEnvironmentSync,
    )
    from .test_main import TestsFlextInfraWorkspaceMain, workspace_main
    from .test_repository_local_topology import TestsRepositoryLocalTopology
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
    "TestsRepositoryLocalTopology",
    "TestsWorkspaceRootMakeContract",
    "WorktreeFixture",
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
    "test_project_scope_uses_declared_name_inside_worktree_lane",
    "test_toc_is_inserted_after_h1_preceded_by_html_comment",
    "test_toc_without_h1_injects_documentation_heading",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "workspace_main",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_detector_owns_no_project_registry": (
                "TestsDetectorOwnsNoProjectRegistry",
            ),
            ".test_docs_contract_toc_placement": (
                "test_toc_is_inserted_after_h1_preceded_by_html_comment",
                "test_toc_without_h1_injects_documentation_heading",
            ),
            ".test_docs_scope_worktree": (
                "test_project_scope_uses_declared_name_inside_worktree_lane",
            ),
            ".test_environment_provenance": (
                "TestsFlextInfraWorkspaceEnvironmentProvenance",
            ),
            ".test_facade_environment_sync": (
                "TestsFlextInfraFacadeBaseMk",
                "TestsFlextInfraFacadeEnvironmentSync",
            ),
            ".test_main": ("TestsFlextInfraWorkspaceMain", "workspace_main"),
            ".test_repository_local_topology": ("TestsRepositoryLocalTopology",),
            ".test_vscode": ("TestsFlextInfraCodegenVscode",),
            ".test_workspace_root_make_contract": ("TestsWorkspaceRootMakeContract",),
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
