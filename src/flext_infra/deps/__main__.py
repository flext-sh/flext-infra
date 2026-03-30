"""CLI entry point for dependency management services.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import sys
from types import MappingProxyType

from flext_infra import output, t, u

_SUBCOMMAND_MODULES: t.StrMapping = MappingProxyType({
    "detect": "flext_infra.deps.detector",
    "extra-paths": "flext_infra.deps.extra_paths",
    "internal-sync": "flext_infra.deps.internal_sync",
    "modernize": "flext_infra.deps.modernizer",
    "path-sync": "flext_infra.deps.path_sync",
})
_VALUE_FLAGS: frozenset[str] = frozenset({
    "--workspace",
    "--project",
    "--projects",
    "--format",
    "--output",
    "-o",
    "--limits",
    "--mode",
})


class FlextInfraDepsCommand:
    """CLI entry point for dependency management operations."""

    @staticmethod
    def _find_subcommand_index(argv: t.StrSequence) -> int | None:
        """Locate the deps subcommand without consuming its forwarded flags."""
        index = 0
        while index < len(argv):
            token = argv[index]
            normalized = token.split("=", 1)[0]
            if normalized in _VALUE_FLAGS:
                index += 1 if "=" in token else 2
                continue
            if token.startswith("-"):
                index += 1
                continue
            if token in _SUBCOMMAND_MODULES:
                return index
            index += 1
        return None

    @staticmethod
    def run(argv: t.StrSequence | None = None) -> int:
        """Dispatch to the appropriate deps subcommand."""
        raw_args = list(argv) if argv is not None else sys.argv[1:]
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
        command_index = FlextInfraDepsCommand._find_subcommand_index(raw_args)
        if command_index is None:
            _ = parser.parse_args(raw_args)
            parser.print_help()
            return 0
        subcommand = raw_args[command_index]
        if subcommand not in _SUBCOMMAND_MODULES:
            output.error(f"flext-infra deps: unknown subcommand '{subcommand}'")
            parser.print_help()
            return 1
        forwarded_args = [
            token for idx, token in enumerate(raw_args) if idx != command_index
        ]
        sys.argv = [f"flext-infra deps {subcommand}", *forwarded_args]
        module = importlib.import_module(_SUBCOMMAND_MODULES[subcommand])
        exit_code = module.main()
        return int(exit_code) if exit_code is not None else 0


def _main_impl(argv: t.StrSequence | None = None) -> int:
    return FlextInfraDepsCommand.run(argv)


def main() -> int:
    """Dispatch to the appropriate deps subcommand."""
    return u.Infra.run_cli(_main_impl)


if __name__ == "__main__":
    sys.exit(main())
