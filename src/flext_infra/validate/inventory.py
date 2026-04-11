"""Scripts inventory generation service.

Generates script inventory artifacts for workspace governance,
cataloging all scripts and their wiring status.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, s, t, u


class FlextInfraInventoryService(s[bool]):
    """Generates and manages scripts inventory for workspace governance.

    Scans the workspace for Python and Bash scripts and produces
    structured inventory, wiring, and external-candidate reports.
    """

    output_dir: Annotated[
        Path | None,
        Field(default=None, description="Output directory for reports"),
    ] = None

    def generate(
        self,
        workspace_root: Path,
        *,
        output_dir: Path | None = None,
    ) -> r[m.Infra.InventoryReport]:
        """Build and write scripts inventory reports.

        Args:
            workspace_root: Root of the workspace to scan.
            output_dir: Optional directory for reports. Defaults to
                ``workspace_root / ".reports"``.

        Returns:
            r with combined inventory metadata.

        """
        try:
            root = workspace_root.resolve()
            scripts_dir = root / c.Infra.DIR_SCRIPTS
            scripts: t.StrSequence = []
            if scripts_dir.exists():
                scripts = sorted(
                    path.relative_to(root).as_posix()
                    for path in scripts_dir.rglob("*")
                    if path.is_file() and path.suffix in {c.Infra.EXT_PYTHON, ".sh"}
                )
            now = datetime.now(UTC).isoformat()
            scripts_infra: list[t.Cli.JsonValue] = list(scripts)
            inventory: t.Cli.JsonMapping = {
                "generated_at": now,
                "repo_root": str(root),
                "total_scripts": len(scripts),
                "scripts": scripts_infra,
            }
            wiring: t.Cli.JsonMapping = {
                "generated_at": now,
                "root_makefile": [c.Infra.MAKEFILE_FILENAME],
                "unwired_scripts": list[t.Cli.JsonValue](),
            }
            external: t.Cli.JsonMapping = {
                "generated_at": now,
                "candidates": list[t.Cli.JsonValue](),
            }
            reports_dir = output_dir or root / c.Infra.REPORTS_DIR_NAME
            written: MutableSequence[str] = []
            inventory_path = reports_dir / "scripts-infra--json--scripts-inventory.json"
            wiring_path = reports_dir / "scripts-infra--json--scripts-wiring.json"
            external_path = (
                reports_dir / "scripts-infra--json--external-scripts-candidates.json"
            )
            write_result = u.Cli.json_write(inventory_path, inventory, sort_keys=True)
            if write_result.failure:
                return r[m.Infra.InventoryReport].fail(
                    write_result.error or "write failed",
                )
            written.append(str(inventory_path))
            write_result = u.Cli.json_write(wiring_path, wiring, sort_keys=True)
            if write_result.failure:
                return r[m.Infra.InventoryReport].fail(
                    write_result.error or "write failed",
                )
            written.append(str(wiring_path))
            write_result = u.Cli.json_write(external_path, external, sort_keys=True)
            if write_result.failure:
                return r[m.Infra.InventoryReport].fail(
                    write_result.error or "write failed",
                )
            written.append(str(external_path))
            result = m.Infra.InventoryReport(
                total_scripts=len(scripts),
                reports_written=written,
            )
            return r[m.Infra.InventoryReport].ok(result)
        except (OSError, TypeError, ValueError) as exc:
            return r[m.Infra.InventoryReport].fail(
                f"inventory generation failed: {exc}",
            )

    @override
    def execute(self) -> r[bool]:
        """Execute the inventory CLI flow."""
        return self.generate(
            self.workspace_root,
            output_dir=self.output_dir,
        ).map(lambda _: True)


__all__ = ["FlextInfraInventoryService"]
