"""Centralized CLI runner for flext_infra.check."""

from __future__ import annotations

from flext_infra import FlextInfraWorkspaceChecker, t


class FlextInfraCliCheck:
    """Canonical CLI surface for the check group."""

    @staticmethod
    def run(args: t.StrSequence | None = None) -> int:
        """Run the check group through the canonical workspace checker CLI."""
        return FlextInfraWorkspaceChecker.run_cli(args)
