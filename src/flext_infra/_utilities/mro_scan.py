"""MRO migration scanner utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import t
from flext_infra._models.mro_scan import FlextInfraModelsMroScan
from flext_infra._utilities.mro_scan_catalog import FlextInfraUtilitiesMroScanCatalog
from flext_infra._utilities.mro_scan_source import FlextInfraUtilitiesMroScanSource


class FlextInfraUtilitiesRefactorMroScan:
    """Scan project sources for declarations movable into MRO facade classes."""

    @classmethod
    def scan_workspace(
        cls,
        *,
        workspace_root: Path,
        target: str,
        project_names: t.StrSequence | None = None,
    ) -> tuple[t.SequenceOf[FlextInfraModelsMroScan.MROScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        normalized = target.strip().lower()
        if not FlextInfraUtilitiesMroScanCatalog.target_supported(normalized):
            return ((), 0)

        results: list[FlextInfraModelsMroScan.MROScanReport] = []
        scanned = 0
        specs = FlextInfraUtilitiesMroScanCatalog.target_specs(normalized)
        for project_root in FlextInfraUtilitiesMroScanCatalog.project_roots(
            workspace_root.resolve(), project_names
        ):
            for file_path in FlextInfraUtilitiesMroScanCatalog.python_files(
                project_root
            ):
                for spec in specs:
                    if not FlextInfraUtilitiesMroScanCatalog.matches_target(
                        file_path, spec
                    ):
                        continue
                    scanned += 1
                    report = cls.scan_file(
                        file_path=file_path, project_root=project_root, target_spec=spec
                    )
                    if report is not None and report.candidates:
                        results.append(report)
        return (tuple(results), scanned)

    @staticmethod
    def scan_file(
        *,
        file_path: Path,
        project_root: Path,
        target_spec: FlextInfraModelsMroScan.MROTargetSpec,
    ) -> FlextInfraModelsMroScan.MROScanReport | None:
        """Scan one Python file and return migration candidates."""
        source = file_path.read_text(encoding="utf-8")
        facade = FlextInfraUtilitiesMroScanSource.find_facade(source, target_spec)
        if not facade:
            return None

        candidates = FlextInfraUtilitiesMroScanSource.candidates(source, target_spec)
        if not candidates:
            return None

        return FlextInfraModelsMroScan.MROScanReport(
            file=str(file_path.resolve()),
            module=FlextInfraUtilitiesMroScanCatalog.module_name(
                file_path, project_root
            ),
            constants_class=facade,
            facade_alias=target_spec.family_alias,
            candidates=tuple(candidates),
        )


__all__: list[str] = ["FlextInfraUtilitiesRefactorMroScan"]
