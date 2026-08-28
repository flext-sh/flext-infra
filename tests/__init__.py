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
    from flext_infra import d, e, h, r, x
    from flext_tests import td, tf, tk, tm, tv
    from re import re

    from .base import TestsFlextInfraServiceBase, TestsFlextInfraServiceBase as s
    from .conftest import (
        infra_git,
        infra_git_repo,
        infra_io,
        infra_path,
        infra_patterns,
        infra_public_root,
        infra_reporting,
        infra_safe_command_output,
        infra_selection,
        infra_subprocess,
        infra_test_workspace,
        infra_toml,
        pytest_ignore_collect,
        pytest_plugins,
        rope_project,
    )
    from .constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from .models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from .protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from .typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from .utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u
__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "c",
    "d",
    "e",
    "h",
    "infra_git",
    "infra_git_repo",
    "infra_io",
    "infra_path",
    "infra_patterns",
    "infra_public_root",
    "infra_reporting",
    "infra_safe_command_output",
    "infra_selection",
    "infra_subprocess",
    "infra_test_workspace",
    "infra_toml",
    "integration",
    "m",
    "p",
    "pytest_ignore_collect",
    "pytest_plugins",
    "r",
    "re",
    "refactor",
    "rope_project",
    "s",
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
            ".conftest": (
                "infra_git",
                "infra_git_repo",
                "infra_io",
                "infra_path",
                "infra_patterns",
                "infra_public_root",
                "infra_reporting",
                "infra_safe_command_output",
                "infra_selection",
                "infra_subprocess",
                "infra_test_workspace",
                "infra_toml",
                "pytest_ignore_collect",
                "pytest_plugins",
                "rope_project",
            ),
            ".constants": ("TestsFlextInfraConstants", "c"),
            ".integration": ("integration",),
            ".models": ("TestsFlextInfraModels", "m"),
            ".protocols": ("TestsFlextInfraProtocols", "p"),
            ".refactor": ("refactor",),
            ".typings": ("TestsFlextInfraTypes", "t"),
            ".unit": ("unit",),
            ".utilities": ("TestsFlextInfraUtilities", "u"),
            "flext_infra": ("d", "e", "h", "r", "x"),
            "flext_tests": ("td", "tf", "tk", "tm", "tv"),
            "re": ("re",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
