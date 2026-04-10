"""Helpers for routing legacy entrypoints into the canonical infra CLI."""

from __future__ import annotations

import importlib
import sys

from flext_infra import t


class FlextInfraUtilitiesCliDispatch:
    """Route legacy module entrypoints through ``flext_infra.cli``."""

    @staticmethod
    def run_group(group: str, argv: t.StrSequence | None = None) -> int:
        """Execute one canonical CLI group with optional forwarded arguments."""
        cli_module = importlib.import_module("flext_infra.cli")
        forwarded = list(argv) if argv is not None else sys.argv[1:]
        return cli_module.main([group, *forwarded])

    @staticmethod
    def run_command(
        group: str,
        command: str,
        argv: t.StrSequence | None = None,
    ) -> int:
        """Execute one canonical CLI command with optional forwarded arguments."""
        cli_module = importlib.import_module("flext_infra.cli")
        forwarded = list(argv) if argv is not None else sys.argv[1:]
        return cli_module.main([group, command, *forwarded])


__all__ = ["FlextInfraUtilitiesCliDispatch"]
