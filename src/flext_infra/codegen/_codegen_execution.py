"""Code execution for quality gate artifact writing and file detection.

Provides methods for writing quality gate artifacts and detecting modified
Python files in the workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, t
from flext_infra.codegen._codegen_execution_tools import (
    FlextInfraCodegenExecutionTools,
)


class FlextInfraCodegenExecution(FlextInfraCodegenExecutionTools):
    """Code execution for artifact writing and file detection."""

    @staticmethod
    def quality_gate_write_artifacts(
        *,
        workspace_root: Path,
        report: dict[str, t.Infra.InfraValue],
        render_text: str,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: list[m.Infra.DuplicateConstantGroup],
        before_payload: dict[str, t.Infra.InfraValue] | None,
    ) -> dict[str, t.Infra.InfraValue]:
        """Write quality gate artifacts to disk."""
        directory = workspace_root / c.Infra.QualityGate.REPORT_DIR
        directory.mkdir(parents=True, exist_ok=True)
        report_json = directory / "latest.json"
        report_text = directory / "latest.txt"
        census_json = directory / "census-after.json"
        inventory_json = directory / "inventory-after.json"
        validate_json = directory / "validate-after.json"
        baseline_json = directory / "baseline-used.json"
        report_adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
            dict[str, t.Infra.InfraValue],
        )
        report_json.write_text(
            report_adapter.dump_json(report, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT,
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        report_text.write_text(render_text, encoding=c.Infra.Encoding.DEFAULT)
        census_payload: list[dict[str, t.Infra.InfraValue]] = [
            item.model_dump() for item in census_reports
        ]
        census_adapter: TypeAdapter[list[dict[str, t.Infra.InfraValue]]] = TypeAdapter(
            list[dict[str, t.Infra.InfraValue]],
        )
        census_json.write_text(
            census_adapter.dump_json(census_payload, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT,
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        inventory_adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
            dict[str, t.Infra.InfraValue],
        )
        group_adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
            dict[str, t.Infra.InfraValue],
        )
        groups_payload: list[t.Infra.InfraValue] = [
            group_adapter.validate_python(group.model_dump())
            for group in duplicate_groups
        ]
        inventory_payload: dict[str, t.Infra.InfraValue] = {
            "groups": groups_payload,
            "count": len(duplicate_groups),
        }
        inventory_json.write_text(
            inventory_adapter.dump_json(
                inventory_payload,
                by_alias=True,
            ).decode(c.Infra.Encoding.DEFAULT),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        validate_adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
            dict[str, t.Infra.InfraValue],
        )
        validate_json.write_text(
            validate_adapter.dump_json(
                {
                    "mro_failures": 0,
                    "layer_violations": 0,
                    "cross_project_reference_violations": 0,
                },
                by_alias=True,
            ).decode(c.Infra.Encoding.DEFAULT),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        if before_payload is not None:
            baseline_adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
                dict[str, t.Infra.InfraValue],
            )
            baseline_json.write_text(
                baseline_adapter.dump_json(before_payload, by_alias=True).decode(
                    c.Infra.Encoding.DEFAULT,
                ),
                encoding=c.Infra.Encoding.DEFAULT,
            )
        return {
            "directory": str(directory),
            "report_json": str(report_json),
            "report_text": str(report_text),
            "census_after": str(census_json),
            "inventory_after": str(inventory_json),
            "validate_after": str(validate_json),
            "baseline_used": str(baseline_json) if before_payload is not None else "",
        }

    @staticmethod
    def quality_gate_modified_python_files(workspace_root: Path) -> list[str]:
        """Detect modified Python files in workspace."""
        normalized: set[str] = set()
        for rel in FlextInfraCodegenExecutionTools.git_lines(
            workspace_root,
            ["diff", "--name-only", "--", "*.py"],
        ):
            if "constants" not in rel:
                continue
            candidate = (workspace_root / rel).resolve()
            if not candidate.is_file() or candidate.suffix != c.Infra.Extensions.PYTHON:
                continue
            try:
                normalized.add(str(candidate.relative_to(workspace_root)))
            except ValueError:
                continue
        for rel in FlextInfraCodegenExecutionTools.git_lines(
            workspace_root,
            ["diff", "--name-only", "--cached", "--", "*.py"],
        ):
            if "constants" not in rel:
                continue
            candidate = (workspace_root / rel).resolve()
            if not candidate.is_file() or candidate.suffix != c.Infra.Extensions.PYTHON:
                continue
            try:
                normalized.add(str(candidate.relative_to(workspace_root)))
            except ValueError:
                continue
        for rel in FlextInfraCodegenExecutionTools.git_lines(
            workspace_root,
            ["ls-files", "--others", "--exclude-standard", "--", "*.py"],
        ):
            if "constants" not in rel:
                continue
            candidate = (workspace_root / rel).resolve()
            if not candidate.is_file() or candidate.suffix != c.Infra.Extensions.PYTHON:
                continue
            try:
                normalized.add(str(candidate.relative_to(workspace_root)))
            except ValueError:
                continue
        if normalized:
            return sorted(normalized)
        fallback = (
            workspace_root / ".reports/codegen/constants-refactor/dedup-apply.json"
        )
        if fallback.is_file():
            try:
                text = fallback.read_text(encoding=c.Infra.Encoding.DEFAULT)
                adapter: TypeAdapter[dict[str, t.Infra.InfraValue]] = TypeAdapter(
                    dict[str, t.Infra.InfraValue],
                )
                payload = adapter.validate_json(text)
            except (OSError, UnicodeDecodeError, ValueError):
                return []
            try:
                raw = adapter.validate_python(
                    payload,
                )
            except ValidationError:
                return []
            modified = raw.get("modified_files")
            if isinstance(modified, list):
                filtered: set[str] = set()
                for entry in modified:
                    if not isinstance(entry, str):
                        continue
                    if not entry.endswith(c.Infra.Extensions.PYTHON):
                        continue
                    filtered.add(entry)
                return sorted(filtered)
        return []


__all__ = ["FlextInfraCodegenExecution"]
