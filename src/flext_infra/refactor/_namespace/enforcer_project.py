"""Per-project namespace enforcement — extracted concern of the namespace enforcer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, u
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.refactor import FlextInfraNamespaceRelocationCascade


class FlextInfraRefactorNamespaceEnforcerProject:
    """Project complete workspace observations onto one project's report.

    Only relocation progress uses namespace scope; catalog counts never do.
    Both snapshots bracket all repairs, including cross-project consumer rewires.
    """

    if TYPE_CHECKING:
        _repository_root: Path

    def _enforce_project(
        self,
        *,
        project_root: Path,
        py_files: Sequence[Path],
        before: m.Infra.ModScanReport,
        after: m.Infra.ModScanReport,
        rule_deltas: tuple[m.Infra.ViolationsRuleDelta, ...],
    ) -> m.Infra.ProjectEnforcementReport:
        """Compare one project's observations bracketing the whole workspace repair.

        Returns:
            The resulting ``m.Infra.ProjectEnforcementReport``.

        """
        scan_root = self._repository_root
        cascade = FlextInfraNamespaceRelocationCascade()
        findings = cascade.findings_from_report(
            project_root, py_files, before.entries, scan_root=scan_root
        )
        after_findings = cascade.findings_from_report(
            project_root,
            cascade.scoped_py_files(project_root),
            after.entries,
            scan_root=scan_root,
        )
        relocation_deltas = u.Infra.rule_deltas(
            FlextInfraModGateEngine.recounted(tuple(entry for _, entry in findings)),
            FlextInfraModGateEngine.recounted(
                tuple(entry for _, entry in after_findings)
            ),
        )
        return m.Infra.ProjectEnforcementReport(
            project=project_root.name,
            project_root=str(project_root),
            rule_deltas=rule_deltas,
            relocation_findings=len(after_findings),
            relocation_resolved=sum(row.resolved for row in relocation_deltas),
            relocation_persisted=sum(row.persisted for row in relocation_deltas),
            relocation_introduced=sum(row.introduced for row in relocation_deltas),
            files_scanned=len(py_files),
        )


__all__: list[str] = ["FlextInfraRefactorNamespaceEnforcerProject"]
