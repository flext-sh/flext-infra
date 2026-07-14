"""Command payload mixin for flext-infra service bases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import t


class FlextInfraCommandPayloadMixin:
    """Private MRO payload builder for shared command services."""

    if TYPE_CHECKING:
        workspace_root: Path
        apply_changes: bool
        check_only: bool
        dry_run: bool
        fail_fast: bool
        output_format: str
        project_filter: str | None
        report_path: Path | None
        output_dir: Path | None

    def command_payload(self) -> t.JsonMapping:
        """Return the normalized shared command payload once."""
        payload: t.MutableJsonMapping = {
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
            "check_only": self.check_only,
            "dry_run": self.dry_run,
            "fail_fast": self.fail_fast,
            "output_format": self.output_format,
        }
        if self.project_filter is not None:
            payload["project_filter"] = self.project_filter
        if self.report_path is not None:
            payload["report_path"] = str(self.report_path)
        if self.output_dir is not None:
            payload["output_dir"] = str(self.output_dir)
        return payload


__all__: list[str] = ["FlextInfraCommandPayloadMixin"]
