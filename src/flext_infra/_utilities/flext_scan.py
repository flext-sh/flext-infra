"""FLEXT migration scanner utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra._models.flext_scan import FlextInfraModelsFlextScan
from flext_infra._utilities.flext_scan_catalog import (
    FlextInfraUtilitiesFlextScanCatalog,
)
from flext_infra._utilities.flext_scan_source import FlextInfraUtilitiesFlextScanSource

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.typings import t


class FlextInfraUtilitiesRefactorFlextScan:
    """Scan project sources for declarations movable into FLEXT facade classes."""

    @classmethod
    def scan_workspace(
        cls,
        *,
        workspace_root: Path,
        target: str,
        project_names: t.StrSequence | None = None,
    ) -> tuple[t.SequenceOf[FlextInfraModelsFlextScan.FLEXTScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        normalized = target.strip().lower()
        if not FlextInfraUtilitiesFlextScanCatalog.target_supported(normalized):
            return ((), 0)

        results: list[FlextInfraModelsFlextScan.FLEXTScanReport] = []
        scanned = 0
        specs = FlextInfraUtilitiesFlextScanCatalog.target_specs(normalized)
        for project_root in FlextInfraUtilitiesFlextScanCatalog.project_roots(
            workspace_root.resolve(), project_names
        ):
            for file_path in FlextInfraUtilitiesFlextScanCatalog.python_files(
                project_root
            ):
                for spec in specs:
                    if not FlextInfraUtilitiesFlextScanCatalog.matches_target(
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
        target_spec: FlextInfraModelsFlextScan.FLEXTTargetSpec,
    ) -> FlextInfraModelsFlextScan.FLEXTScanReport | None:
        """Scan one Python file and return migration candidates."""
        source = file_path.read_text(encoding="utf-8")
        facade = FlextInfraUtilitiesFlextScanSource.find_facade(source, target_spec)
        if not facade:
            return None

        candidates = FlextInfraUtilitiesFlextScanSource.candidates(source, target_spec)
        if not candidates:
            return None

        return FlextInfraModelsFlextScan.FLEXTScanReport(
            file=str(file_path.resolve()),
            module=FlextInfraUtilitiesFlextScanCatalog.module_name(
                file_path, project_root
            ),
            constants_class=facade,
            facade_alias=target_spec.family_alias,
            candidates=tuple(candidates),
        )


__all__: list[str] = ["FlextInfraUtilitiesRefactorFlextScan"]
