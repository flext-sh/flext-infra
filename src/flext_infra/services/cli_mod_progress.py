"""Mod progress rendered at the CLI transport boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time

from flext_cli import cli

from flext_infra import m


class FlextInfraCliModProgress:
    """Render mod progress at the CLI transport boundary, timed per phase."""

    def __init__(self) -> None:
        """Start the run clock at the composition root."""
        self._started = time.monotonic()
        self._phase = self._started

    def emit(self, message: str) -> None:
        """Show the current mod phase with the closing phase's duration.

        Each phase lasts from its message to the next one, so every line
        reports how long the previous phase took and the run's total.
        """
        now = time.monotonic()
        cli.display_text(
            f"{message} [previous phase {now - self._phase:.1f}s, "
            f"total {now - self._started:.1f}s]"
        )
        self._phase = now

    @staticmethod
    def emit_rename(report: m.Infra.ApplyRenamesReport) -> None:
        """Show one completed CSV campaign."""
        cli.display_text(FlextInfraCliModProgress.render_rename(report))

    @staticmethod
    def render_rename(report: m.Infra.ApplyRenamesReport) -> str:
        """Render native published paths and pending edit spans.

        Returns:
            The resulting ``str``.

        """
        return (
            f"{report.label}: {report.files_changed} published file(s), "
            f"{report.occurrences} pending source edit(s), "
            f"{report.files_scanned} scanned file(s)"
            + (f"\n{report.preview_diff}" if report.preview_diff else "")
        )


__all__: list[str] = ["FlextInfraCliModProgress"]
