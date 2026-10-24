"""Static enforcement catalog gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraEnforcementCatalogGate(FlextInfraGate):
    """Fail when the enforcement catalog names an owner that does not exist."""

    gate_id: ClassVar[str] = c.Infra.ENFORCEMENT_CATALOG
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Load the catalog through its owner and report the first owner gap.

        Returns:
            The gate execution with one issue per unresolved catalog load.

        """
        started = time.monotonic()
        loaded = u.Infra.enforcement_catalog()
        issues = (
            ()
            if loaded.success
            else (
                m.Infra.Issue(
                    file=str(c.Infra.ENFORCEMENT_CATALOG_RELPATH),
                    line=0,
                    column=0,
                    code=self.gate_id,
                    message=loaded.error or "enforcement catalog failed to load",
                    severity=c.Infra.GateSeverity.ERROR.value,
                ),
            )
        )
        raw = (
            f"rules={len(loaded.value.rules)}"
            if loaded.success
            else "\n".join(issue.formatted for issue in issues)
        )
        return self._build_check_gate_execution(
            project_dir,
            passed=loaded.success,
            issues=issues,
            evidence=self._publish_raw_receipt(ctx, raw),
            started=started,
        )


__all__: list[str] = ["FlextInfraEnforcementCatalogGate"]
