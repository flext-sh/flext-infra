"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_cli import r, u
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraUtilitiesRefactor:
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

    @staticmethod
    def entry_list(value: t.Infra.InfraValue | None) -> t.SequenceOf[t.StrMapping]:
        """Normalize class-nesting settings entries to a strict list."""
        if value is None:
            return []
        try:
            entries: t.SequenceOf[t.StrMapping] = (
                t.Infra.STR_MAPPING_SEQ_ADAPTER.validate_python(value)
            )
        except c.ValidationError:
            msg = "class nesting entries must be a list"
            raise ValueError(msg) from None
        else:
            return entries

    @staticmethod
    def string_list(value: t.Infra.InfraValue | None) -> t.StrSequence:
        """Normalize policy fields that should contain string collections."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        try:
            return list(t.Infra.STR_SEQ_ADAPTER.validate_python(value))
        except TypeError as exc:
            msg = "expected list value"
            raise TypeError(msg) from exc
        except c.ValidationError as exc:
            msg = "expected list value"
            raise TypeError(msg) from exc

    @staticmethod
    def normalize_module_path(path_value: str | Path) -> str:
        """Normalize module path."""
        path = Path(str(path_value).replace("\\", "/"))
        parts = path.parts
        if c.Infra.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path.as_posix().lstrip("./")

    @staticmethod
    def module_owns_nested_class(
        source: str, *, namespace: str, nested_name: str
    ) -> bool:
        """Return whether a module defines ``namespace.nested_name`` itself.

        Consumer propagation rewrites ``from module import Old`` to import the
        surviving namespace.  The owner module is different: it already binds
        that namespace locally, so rewriting an unrelated/shadowed import to
        the same name would create a duplicate binding and a type error.
        """
        module = ast.parse(source)
        return any(
            statement.name == namespace
            and any(
                isinstance(child, ast.ClassDef) and child.name == nested_name
                for child in statement.body
            )
            for statement in module.body
            if isinstance(statement, ast.ClassDef)
        )

    @staticmethod
    def write_impact_map(
        results: t.SequenceOf[m.Infra.Result], output_path: Path
    ) -> p.Result[bool]:
        """Write refactor impact map JSON to disk."""
        payload = {
            "files": [
                {
                    "path": str(item.file_path),
                    "success": item.success,
                    "modified": item.modified,
                    "error": item.error,
                    "changes": list(item.changes),
                }
                for item in results
            ]
        }
        normalized_payload: t.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_python(
            payload
        )
        write_result = u.Cli.json_write(output_path, normalized_payload)
        if write_result.failure:
            return r[bool].fail(write_result.error or "impact map write failed")
        return r[bool].ok(True)

    @staticmethod
    def publish_mod_scan_evidence(
        root: Path,
        report: m.Infra.ModScanReport,
        *,
        command: c.Infra.ModScanCommand,
        scope: t.StrSequence,
    ) -> p.Result[m.Infra.ModScanEvidenceReceipt]:
        """Atomically replace the complete structured evidence for one mod scan."""
        repository_totals: dict[str, int] = {}
        rule_totals: dict[str, int] = {}
        for finding in report.entries:
            repository_totals[finding.repository] = (
                repository_totals.get(finding.repository, 0) + 1
            )
            rule_totals[finding.rule_id] = rule_totals.get(finding.rule_id, 0) + 1
        evidence = m.Infra.ModScanEvidence(
            schema_version=c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
            command=command,
            root=root.resolve(),
            scope=tuple(scope),
            findings=report.findings,
            actionable=report.nodes,
            detection_only=report.findings - report.nodes,
            totals_by_repository=dict(sorted(repository_totals.items())),
            totals_by_rule=dict(sorted(rule_totals.items())),
            entries=report.entries,
        )
        content = (
            evidence.model_dump_json(indent=2) + "\n"
        ).encode(c.Cli.ENCODING_DEFAULT)
        report_path = root.resolve() / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH
        prepared = u.Cli.ensure_dir(report_path.parent)
        if prepared.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(prepared)
        before = u.Cli.atomic_read_binary_file_state(report_path, required=False)
        if before.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(before)
        written = u.Cli.atomic_write_binary_file_guarded(
            before.value,
            content,
            permission_mode=c.Infra.MOD_SCAN_REPORT_MODE,
        )
        if written.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(written)
        published = u.Cli.atomic_read_binary_file_state(report_path, required=True)
        if published.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(published)
        if (
            published.value.content != content
            or published.value.mode != c.Infra.MOD_SCAN_REPORT_MODE
        ):
            return r[m.Infra.ModScanEvidenceReceipt].fail(
                f"published mod evidence differs from planned bytes: {report_path}"
            )
        return r[m.Infra.ModScanEvidenceReceipt].ok(
            m.Infra.ModScanEvidenceReceipt(
                path=report_path,
                sha256=u.Cli.sha256_bytes(content),
                evidence=evidence,
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesRefactor"]
