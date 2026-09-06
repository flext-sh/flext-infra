# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import integration as integration
    from . import refactor as refactor
    from . import unit as unit
    from flext_tests import FlextTestsConstants, d, e, h, r, td, tf, tk, tm, tv, x
    from typing import ClassVar, Final, TYPE_CHECKING

    from .base import TestsFlextInfraServiceBase, TestsFlextInfraServiceBase as s
    from .constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from .models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from .protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from .typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from .unit.check.tests_workspace_check import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from .unit.fixtures import (
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
    from .unit.fixtures_git import real_git_repo
    from .unit.runner_service import RealSubprocessRunner
    from .unit.workspace.worktree_fixture import WorktreeFixture
    from .unit.workspace_factory import TestsFlextInfraWorkspaceFactory
    from .utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u
__all__: tuple[str, ...] = (
    "TYPE_CHECKING",
    "ClassVar",
    "Final",
    "FlextTestsConstants",
    "MappingProxyType",
    "RealSubprocessRunner",
    "TestsFlextInfraConstants",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraWorkspaceFactory",
    "WorktreeFixture",
    "c",
    "d",
    "deptry_report_payload",
    "e",
    "h",
    "integration",
    "m",
    "models_resource",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "p",
    "r",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "refactor",
    "rope_workspace",
    "s",
    "services_resource",
    "t",
    "td",
    "test_workspace_check_main_returns_error_without_projects",
    "tf",
    "tk",
    "tm",
    "tool_config_document",
    "tv",
    "u",
    "unit",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".base": ("TestsFlextInfraServiceBase", "s"),
            ".constants": ("TestsFlextInfraConstants", "c"),
            ".integration": ("integration",),
            ".models": ("TestsFlextInfraModels", "m"),
            ".protocols": ("TestsFlextInfraProtocols", "p"),
            ".refactor": ("refactor",),
            ".typings": ("TestsFlextInfraTypes", "t"),
            ".unit": ("unit",),
            ".unit.check.tests_workspace_check": (
                "test_workspace_check_main_returns_error_without_projects",
            ),
            ".unit.fixtures": (
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
            ".unit.fixtures_git": ("real_git_repo",),
            ".unit.runner_service": ("RealSubprocessRunner",),
            ".unit.workspace.worktree_fixture": ("WorktreeFixture",),
            ".unit.workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
            ".utilities": ("TestsFlextInfraUtilities", "u"),
            "flext_tests": (
                "FlextTestsConstants",
                "d",
                "e",
                "h",
                "r",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "x",
            ),
            "types": ("MappingProxyType",),
            "typing": ("ClassVar", "Final", "TYPE_CHECKING"),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
