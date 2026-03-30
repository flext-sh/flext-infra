"""Centralized CLI runner for flext_infra.deps."""

from __future__ import annotations

import importlib
import sys
from types import MappingProxyType
from typing import ClassVar

from flext_infra import output, t, u


class FlextInfraCliDeps:
    """Canonical CLI surface for dependency-management commands."""

    _SUBCOMMAND_MODULES: t.StrMapping = MappingProxyType({
        "detect": "flext_infra.deps.detector",
        "extra-paths": "flext_infra.deps.extra_paths",
        "internal-sync": "flext_infra.deps.internal_sync",
        "modernize": "flext_infra.deps.modernizer",
        "path-sync": "flext_infra.deps.path_sync",
    })
    _VALUE_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--workspace",
        "--project",
        "--projects",
        "--format",
        "--output",
        "-o",
        "--limits",
        "--mode",
    })

    @classmethod
    def _find_subcommand_index(cls, argv: t.StrSequence) -> int | None:
        """Locate the deps subcommand without consuming its forwarded flags."""
        index = 0
        while index < len(argv):
            token = argv[index]
            normalized = token.split("=", 1)[0]
            if normalized in cls._VALUE_FLAGS:
                index += 1 if "=" in token else 2
                continue
            if token.startswith("-"):
                index += 1
                continue
            if token in cls._SUBCOMMAND_MODULES:
                return index
            index += 1
        return None

    @classmethod
    def run(cls, args: t.StrSequence | None = None) -> int:
        """Dispatch to the appropriate deps subcommand."""
        raw_args = list(args) if args is not None else sys.argv[1:]
        parser, _ = u.Infra.create_subcommand_parser(
            "flext-infra deps",
            "Dependency management services",
            subcommands={
                "detect": "Detect runtime vs dev dependencies",
                "extra-paths": "Synchronize pyright/mypy extraPaths",
                "internal-sync": "Synchronize internal FLEXT dependencies",
                "modernize": "Modernize workspace pyproject files",
                "path-sync": "Rewrite internal FLEXT dependency paths",
            },
            include_apply=False,
        )
        if not raw_args or raw_args[0] in {"-h", "--help"}:
            parser.print_help()
            return 0
        command_index = cls._find_subcommand_index(raw_args)
        if command_index is None:
            _ = parser.parse_args(raw_args)
            parser.print_help()
            return 0
        subcommand = raw_args[command_index]
        if subcommand not in cls._SUBCOMMAND_MODULES:
            output.error(f"flext-infra deps: unknown subcommand '{subcommand}'")
            parser.print_help()
            return 1
        forwarded_args = [
            token for idx, token in enumerate(raw_args) if idx != command_index
        ]
        sys.argv = [f"flext-infra deps {subcommand}", *forwarded_args]
        module = importlib.import_module(cls._SUBCOMMAND_MODULES[subcommand])
        exit_code = module.main()
        return int(exit_code) if exit_code is not None else 0
