"""Derived enforcement catalog gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraEnforcementCatalogGate(FlextInfraGates):
    """Fail when an enforcement claim is duplicated or has no active owner."""

    gate_id: ClassVar[str] = c.Infra.ENFORCEMENT_CATALOG
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Derive the catalog from its owners and report the first defect.

        Returns:
            The gate execution with one issue for a failed derivation.

        """
        started = time.monotonic()
        loaded = u.Infra.enforcement_catalog()
        issues = (
            ()
            if loaded.success
            else (
                m.Infra.Issue(
                    file=str(c.Infra.CODEMOD_RULES_RELPATH),
                    line=0,
                    column=0,
                    code=self.gate_id,
                    message=loaded.error or "enforcement catalog derivation failed",
                    severity=c.Infra.GateSeverity.ERROR.value,
                ),
            )
        )
        raw = (
            f"claims={len(loaded.value.claims)}"
            if loaded.success
            else "\n".join(issue.formatted for issue in issues)
        )
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=loaded.success,
                issues=tuple(issues),
                raw_output=raw,
                started=started,
            ),
            ctx,
        )


__all__: list[str] = ["FlextInfraEnforcementCatalogGate"]
