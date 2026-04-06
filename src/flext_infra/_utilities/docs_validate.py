"""Validation helpers for docs services."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from pathlib import Path

from pydantic import ValidationError

from flext_cli import FlextCliUtilitiesJson as _CliJson
from flext_core import u
from flext_infra import (
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsScope,
    c,
    m,
    t,
)


class FlextInfraUtilitiesDocsValidate(_CliJson):
    """Reusable validation helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_has_adr_reference(skill_path: Path) -> bool:
        """Return whether a skill file contains an ADR reference."""
        text = skill_path.read_text(
            encoding=c.Infra.Encoding.DEFAULT, errors=c.Infra.IGNORE
        )
        return "adr" in text.lower()

    @staticmethod
    def docs_extract_required_skills(
        payload: t.ValueOrModel,
    ) -> t.ContainerList | None:
        """Extract the configured required skills list from architecture config."""
        if not u.is_mapping(payload):
            return None
        docs_validation = payload.get("docs_validation")
        if not isinstance(docs_validation, Mapping):
            return None
        configured = docs_validation.get("required_skills")
        return configured if isinstance(configured, list) else None

    @staticmethod
    def docs_load_required_skills(workspace_root: Path) -> t.StrSequence | None:
        """Load the required skills list from the architecture config."""
        config = workspace_root / "docs/architecture/architecture_config.json"
        if not config.exists():
            return []
        payload_result = FlextInfraUtilitiesDocsValidate.json_read(config)
        if payload_result.is_failure:
            return None
        configured = FlextInfraUtilitiesDocsValidate.docs_extract_required_skills(
            payload_result.value,
        )
        if configured is None:
            return []
        try:
            values = t.Infra.STR_SEQ_ADAPTER.validate_python(configured, strict=True)
        except ValidationError:
            return []
        return [str(item) for item in values if item]

    @staticmethod
    def docs_missing_required_paths(scope: m.Infra.DocScope) -> t.StrSequence:
        """Return required docs paths that are still missing from one scope."""
        if scope.name == c.Infra.ReportKeys.ROOT:
            required = [
                "README.md",
                "docs/README.md",
                "docs/index.md",
                "docs/architecture/README.md",
                "docs/guides/README.md",
                "docs/projects/README.md",
                "docs/api-reference/README.md",
                "docs/api-reference/generated/overview.md",
                "docs/projects/generated/catalog.md",
                "mkdocs.yml",
            ]
        else:
            required = list(FlextInfraUtilitiesDocsScope.required_project_files())
        missing: MutableSequence[str] = []
        for rel_path in sorted(set(required)):
            if not (scope.path / rel_path).exists():
                missing.append(rel_path)
        return missing

    @staticmethod
    def docs_contract_messages(scope: m.Infra.DocScope) -> t.StrSequence:
        """Return public API contract problems for one governed project scope."""
        if scope.name == c.Infra.ReportKeys.ROOT or not scope.package_name:
            return []
        messages: MutableSequence[str] = []
        init_path = (
            scope.path
            / c.Infra.Paths.DEFAULT_SRC_DIR
            / scope.package_name
            / c.Infra.Files.INIT_PY
        )
        if not init_path.exists():
            messages.append(
                "missing public package init: "
                f"{init_path.relative_to(scope.path).as_posix()}"
            )
            return messages
        contract = FlextInfraUtilitiesDocsApi.public_contract(
            scope.path,
            scope.package_name,
        )
        if not contract.get("modules") and not contract.get("exports"):
            messages.append("empty public API contract from package exports")
        return messages

    @staticmethod
    def docs_write_todo(
        scope: m.Infra.DocScope,
        *,
        apply_mode: bool,
    ) -> bool:
        """Write the standard ``TODOS.md`` helper file when requested."""
        if scope.name == c.Infra.ReportKeys.ROOT or not apply_mode:
            return False
        path = scope.path / "TODOS.md"
        content = (
            "# TODOS\n\n"
            "- [ ] Resolve documentation validation findings from "
            "`.reports/docs/validate-report.md`.\n"
        )
        _ = path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
        return True

    @staticmethod
    def docs_write_validate_reports(
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Persist the standard validate summary and markdown report."""
        _ = FlextInfraUtilitiesDocsValidate.json_write(
            scope.report_dir / "validate-summary.json",
            {c.Infra.ReportKeys.SUMMARY: report.model_dump(mode="json")},
        )
        _ = FlextInfraUtilitiesDocs.write_markdown(
            scope.report_dir / "validate-report.md",
            [
                "# Docs Validate Report",
                "",
                f"Scope: {report.scope}",
                f"Result: {report.result}",
                f"Message: {report.message}",
                f"TODO written: {int(report.todo_written)}",
            ],
        )


__all__ = ["FlextInfraUtilitiesDocsValidate"]
