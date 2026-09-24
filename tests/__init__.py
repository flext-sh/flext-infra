# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_cli import cli
    from flext_tests import (
        active_rules,
        api,
        config,
        discover_repository_root,
        install_local_packages,
        load_infra_report,
        settings,
        split_csv,
        td,
        tf,
        tk,
        tm,
        tv,
    )

    from flext_core import core, d, e, h, lazy_attribute, r, x
    from flext_infra import docs_main, infra, main

    from . import integration, refactor, unit
    from .base import TestsFlextInfraServiceBase, TestsFlextInfraServiceBase as s
    from .constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from .constants_scan import TestsFlextInfraConstantsScanMixin
    from .models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from .protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from .typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from .utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u
    from .utilities_codegen import TestsFlextInfraUtilitiesCodegenMixin
    from .utilities_deps import TestsFlextInfraUtilitiesDepsMixin
    from .utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixtureMixin
    from .utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
    from .utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixtureMixin
    from .utilities_fixture_workspace import (
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
    )
    from .utilities_gates import TestsFlextInfraUtilitiesGatesMixin
    from .utilities_git import TestsFlextInfraUtilitiesGitMixin
    from .utilities_promoted import TestsFlextInfraUtilitiesPromotedMixin
    from .utilities_release import TestsFlextInfraUtilitiesReleaseMixin
    from .utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
    from .utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin
    from .utilities_toml import TestsFlextInfraUtilitiesTomlMixin
    from .utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsScanMixin",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesCodegenMixin",
    "TestsFlextInfraUtilitiesDepsMixin",
    "TestsFlextInfraUtilitiesDocsFixtureMixin",
    "TestsFlextInfraUtilitiesGatesMixin",
    "TestsFlextInfraUtilitiesGitMixin",
    "TestsFlextInfraUtilitiesProjectFixtureMixin",
    "TestsFlextInfraUtilitiesPromotedMixin",
    "TestsFlextInfraUtilitiesReleaseMixin",
    "TestsFlextInfraUtilitiesReplayRunnerMixin",
    "TestsFlextInfraUtilitiesReplaySequenceMixin",
    "TestsFlextInfraUtilitiesTomlMixin",
    "TestsFlextInfraUtilitiesToolingFixtureMixin",
    "TestsFlextInfraUtilitiesWorkspaceEnvMixin",
    "TestsFlextInfraUtilitiesWorkspaceFixtureMixin",
    "active_rules",
    "api",
    "c",
    "d",
    "discover_repository_root",
    "docs_main",
    "e",
    "h",
    "integration",
    "m",
    "p",
    "r",
    "refactor",
    "s",
    "settings",
    "split_csv",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
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
            ".constants_scan": ("TestsFlextInfraConstantsScanMixin",),
            ".integration": ("integration",),
            ".models": ("TestsFlextInfraModels", "m"),
            ".protocols": ("TestsFlextInfraProtocols", "p"),
            ".refactor": ("refactor",),
            ".typings": ("TestsFlextInfraTypes", "t"),
            ".unit": ("unit",),
            ".utilities": ("TestsFlextInfraUtilities", "u"),
            ".utilities_codegen": ("TestsFlextInfraUtilitiesCodegenMixin",),
            ".utilities_deps": ("TestsFlextInfraUtilitiesDepsMixin",),
            ".utilities_fixture_docs": ("TestsFlextInfraUtilitiesDocsFixtureMixin",),
            ".utilities_fixture_project": (
                "TestsFlextInfraUtilitiesProjectFixtureMixin",
            ),
            ".utilities_fixture_tooling": (
                "TestsFlextInfraUtilitiesToolingFixtureMixin",
            ),
            ".utilities_fixture_workspace": (
                "TestsFlextInfraUtilitiesWorkspaceFixtureMixin",
            ),
            ".utilities_gates": ("TestsFlextInfraUtilitiesGatesMixin",),
            ".utilities_git": ("TestsFlextInfraUtilitiesGitMixin",),
            ".utilities_promoted": ("TestsFlextInfraUtilitiesPromotedMixin",),
            ".utilities_release": ("TestsFlextInfraUtilitiesReleaseMixin",),
            ".utilities_replay": ("TestsFlextInfraUtilitiesReplayRunnerMixin",),
            ".utilities_replay_sequence": (
                "TestsFlextInfraUtilitiesReplaySequenceMixin",
            ),
            ".utilities_toml": ("TestsFlextInfraUtilitiesTomlMixin",),
            ".utilities_workspace_env": ("TestsFlextInfraUtilitiesWorkspaceEnvMixin",),
            "flext_cli": ("cli",),
            "flext_core": ("core", "d", "e", "h", "lazy_attribute", "r", "x"),
            "flext_infra": ("docs_main", "infra", "main"),
            "flext_tests": (
                "active_rules",
                "api",
                "config",
                "discover_repository_root",
                "install_local_packages",
                "load_infra_report",
                "settings",
                "split_csv",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
