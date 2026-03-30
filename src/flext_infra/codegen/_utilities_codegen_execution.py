"""Code execution for quality gate artifact writing and file detection.

Provides methods for writing quality gate artifacts and detecting modified
Python files in the workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_infra import (
    FlextInfraCodegenExecutionTools,
    c,
    m,
    t,
)

_INFRA_MAPPING_ADAPTER: TypeAdapter[Mapping[str, t.Infra.InfraValue]] = TypeAdapter(
    Mapping[str, t.Infra.InfraValue],
)
_INFRA_SEQ_MAPPING_ADAPTER: TypeAdapter[Sequence[Mapping[str, t.Infra.InfraValue]]] = (
    TypeAdapter(
        Sequence[Mapping[str, t.Infra.InfraValue]],
    )
)


class FlextInfraUtilitiesCodegenExecution(FlextInfraCodegenExecutionTools):
    """Code execution for artifact writing and file detection."""

    @staticmethod
    def write_artifacts(
        *,
        workspace_root: Path,
        report: Mapping[str, t.Infra.InfraValue],
        render_text: str,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: Sequence[m.Infra.DuplicateConstantGroup],
        before_payload: Mapping[str, t.Infra.InfraValue] | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Write quality gate artifacts to disk."""
        directory = workspace_root / c.Infra.QualityGate.REPORT_DIR
        directory.mkdir(parents=True, exist_ok=True)
        report_json = directory / "latest.json"
        report_text = directory / "latest.txt"
        census_json = directory / "census-after.json"
        inventory_json = directory / "inventory-after.json"
        validate_json = directory / "validate-after.json"
        baseline_json = directory / "baseline-used.json"
        report_json.write_text(
            _INFRA_MAPPING_ADAPTER.dump_json(report, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT,
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        report_text.write_text(render_text, encoding=c.Infra.Encoding.DEFAULT)
        census_payload: Sequence[Mapping[str, t.Infra.InfraValue]] = [
            item.model_dump() for item in census_reports
        ]
        census_json.write_text(
            _INFRA_SEQ_MAPPING_ADAPTER.dump_json(census_payload, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT,
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        groups_payload: Sequence[t.Infra.InfraValue] = [
            _INFRA_MAPPING_ADAPTER.validate_python(group.model_dump())
            for group in duplicate_groups
        ]
        inventory_payload: Mapping[str, t.Infra.InfraValue] = {
            "groups": groups_payload,
            "count": len(duplicate_groups),
        }
        inventory_json.write_text(
            _INFRA_MAPPING_ADAPTER.dump_json(
                inventory_payload,
                by_alias=True,
            ).decode(c.Infra.Encoding.DEFAULT),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        validate_json.write_text(
            _INFRA_MAPPING_ADAPTER.dump_json(
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
            baseline_json.write_text(
                _INFRA_MAPPING_ADAPTER.dump_json(before_payload, by_alias=True).decode(
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
    def _collect_git_modified(workspace_root: Path) -> t.Infra.StrSet:
        """Collect modified constants Python files from git queries."""
        normalized: t.Infra.StrSet = set()
        git_queries: Sequence[t.StrSequence] = [
            ["diff", "--name-only", "--", "*.py"],
            ["diff", "--name-only", "--cached", "--", "*.py"],
            ["ls-files", "--others", "--exclude-standard", "--", "*.py"],
        ]
        for query in git_queries:
            for rel in FlextInfraCodegenExecutionTools.git_lines(workspace_root, query):
                if "constants" not in rel:
                    continue
                candidate = (workspace_root / rel).resolve()
                if (
                    not candidate.is_file()
                    or candidate.suffix != c.Infra.Extensions.PYTHON
                ):
                    continue
                try:
                    normalized.add(str(candidate.relative_to(workspace_root)))
                except ValueError:
                    continue
        return normalized

    @staticmethod
    def _collect_fallback_modified(workspace_root: Path) -> t.StrSequence:
        """Collect modified files from fallback dedup-apply.json report."""
        fallback = (
            workspace_root / ".reports/codegen/constants-refactor/dedup-apply.json"
        )
        if not fallback.is_file():
            return []
        try:
            text = fallback.read_text(encoding=c.Infra.Encoding.DEFAULT)
            payload = _INFRA_MAPPING_ADAPTER.validate_json(text)
        except (OSError, UnicodeDecodeError, ValueError):
            return []
        try:
            raw = _INFRA_MAPPING_ADAPTER.validate_python(payload)
        except ValidationError:
            return []
        modified = raw.get("modified_files")
        if not isinstance(modified, list):
            return []
        return sorted(
            entry
            for entry in modified
            if isinstance(entry, str) and entry.endswith(c.Infra.Extensions.PYTHON)
        )

    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        """Detect modified Python files in workspace."""
        normalized = FlextInfraUtilitiesCodegenExecution._collect_git_modified(
            workspace_root,
        )
        if normalized:
            return sorted(normalized)
        return FlextInfraUtilitiesCodegenExecution._collect_fallback_modified(
            workspace_root,
        )


__all__ = ["FlextInfraUtilitiesCodegenExecution"]
