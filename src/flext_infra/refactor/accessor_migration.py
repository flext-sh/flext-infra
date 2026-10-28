"""Accessor migration orchestration for get_/set_/is_ modernization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import MutableMapping, Sequence
from typing import Annotated, override

from flext_cli import cli

from flext_infra import FlextInfraProjectSelectionServiceBase, c, m, p, r, t, u
from flext_infra.refactor import FlextInfraRefactorAccessor


class FlextInfraAccessorMigrationOrchestrator(
    FlextInfraProjectSelectionServiceBase[m.Infra.AccessorMigrationReport],
    m.Infra.ModuleSelectionMixin,
    m.Infra.NamespaceSelectionMixin,
    FlextInfraRefactorAccessor,
):
    """Dry-run/apply orchestrator for public accessor migration candidates."""

    source_preview: t.Port[p.Infra.SourcePreview] = m.Field(
        exclude=True,
        description="Injected authenticated source preview capability",
    )
    preview_limit: Annotated[
        int,
        m.Field(description="Maximum number of file previews to include in the report"),
    ] = 10
    gates: Annotated[
        str,
        m.Field(
            description=(
                "Comma-separated lint gates for preview/apply validation; empty"
                " selects the SSOT snapshot gates (make.check_gates_ci)."
            ),
        ),
    ] = ""

    @property
    def gate_names(self) -> Sequence[str]:
        """Normalized lint gate names."""
        return u.Infra.normalize_cli_values(self.gates)

    @property
    def lint_tool_names(self) -> Sequence[str]:
        """Selected lint tool names resolved from gate names."""
        return u.Infra.selected_lint_tool_names(self.gate_names)

    @override
    def execute(self) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Execute.

        Returns:
            The resulting ``p.Result[m.Infra.AccessorMigrationReport]``.

        """
        resolved = u.Infra.resolve_projects(
            self.repository_root,
            self.project_names if self.project_names is not None else (),
        )
        if resolved.failure:
            return r[m.Infra.AccessorMigrationReport].from_failure(resolved)
        iter_result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(
                project_roots=tuple(project.path for project in resolved.value),
            ),
        )
        if iter_result.failure:
            return r[m.Infra.AccessorMigrationReport].from_failure(iter_result)
        lint_before_totals: MutableMapping[str, int] = {}
        lint_after_totals: MutableMapping[str, int] = {}
        new_lint_error_totals: MutableMapping[str, int] = {}
        params = m.Infra.AccessorMigrationInput(
            repository_root=self.repository_root,
            projects=self.project_names,
            module=self.module,
            namespace=self.namespace,
            gates=tuple(self.gate_names),
            preview_limit=self.preview_limit,
            apply=not self.effective_dry_run,
        )
        with u.Infra.open_project(
            self.repository_root,
            project_roots=tuple(project.path for project in resolved.value),
        ) as rope_project:
            processed = self._process_files(
                rope_project,
                iter_result.value,
                params=params,
                source_preview=self.source_preview,
            )
            if processed.failure:
                return r[m.Infra.AccessorMigrationReport].from_failure(processed)
        for file_report in processed.value:
            self._accumulate_lint_totals(lint_before_totals, file_report.lint_before)
            self._accumulate_lint_totals(lint_after_totals, file_report.lint_after)
            for tool, errors in file_report.new_lint_errors.items():
                new_lint_error_totals[tool] = new_lint_error_totals.get(tool, 0) + len(
                    errors
                )
        report = m.Infra.AccessorMigrationReport(
            workspace=str(self.repository_root),
            dry_run=self.effective_dry_run,
            files_scanned=len(iter_result.value),
            files_with_changes=sum(
                bool(file.automated_changes) for file in processed.value
            ),
            automated_change_count=sum(
                len(file.automated_changes) for file in processed.value
            ),
            warning_count=sum(len(file.warnings) for file in processed.value),
            lint_tools=tuple(self.lint_tool_names),
            lint_before_totals=lint_before_totals,
            lint_after_totals=lint_after_totals,
            new_lint_error_totals=new_lint_error_totals,
            files=tuple(
                file
                for file in processed.value
                if file.automated_changes or file.warnings
            )[: self.preview_limit],
        )
        published = u.Infra.publish_refactor_report_evidence(
            self.repository_root,
            report,
            relative_path=c.Infra.ACCESSOR_MIGRATION_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            return r[m.Infra.AccessorMigrationReport].from_failure(published)
        return r[m.Infra.AccessorMigrationReport].ok(report)

    @classmethod
    def execute_payload(
        cls,
        params: m.Infra.AccessorMigrationInput,
        *,
        source_preview: p.Infra.SourcePreview,
    ) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Execute accessor migration from the validated command service.

        Returns:
            The resulting ``p.Result[m.Infra.AccessorMigrationReport]``.

        """
        result = cls(
            source_preview=source_preview,
            repository_root=params.repository_root,
            selected_projects=params.projects,
            apply_changes=params.apply,
            module=params.module,
            namespace=params.namespace,
            preview_limit=params.preview_limit,
            gates=",".join(params.gates),
        ).execute()
        if result.failure:
            return r[m.Infra.AccessorMigrationReport].from_failure(result)
        cli.display_text(cls.render_text(result.value))
        return r[m.Infra.AccessorMigrationReport].ok(result.value)


__all__: list[str] = ["FlextInfraAccessorMigrationOrchestrator"]
