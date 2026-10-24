"""Accessor candidate validation, publication and report rendering.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.refactor import (
    FlextInfraAccessorMigrationRewriteMixin,
    FlextInfraAccessorOriginResolver,
)
from flext_infra.transformers import FlextInfraSemanticPublication

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraAccessorMigrationReportMixin(FlextInfraAccessorMigrationRewriteMixin):
    """Compose a complete accessor candidate before any shared-source write."""

    @staticmethod
    def _accumulate_lint_totals(
        totals: MutableMapping[str, int],
        snapshot: t.Infra.LintSnapshot[m.Infra.LintGateResult],
    ) -> None:
        """Accumulate lint totals."""
        for tool, receipt in snapshot.items():
            totals[tool] = totals.get(tool, 0) + len(receipt.errors)

    def _plan_files(
        self,
        rope_project: t.Infra.RopeProject,
        py_files: t.SequenceOf[Path],
        *,
        params: m.Infra.AccessorMigrationInput,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.SemanticFilePlan],
            t.SequenceOf[m.Infra.AccessorMigrationFile],
        ]
    ]:
        """Capture the original sources and plan all rewrites without effects.

        Returns:
            Existing typed publication plans and unvalidated per-file evidence.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.SemanticFilePlan],
                t.SequenceOf[m.Infra.AccessorMigrationFile],
            ]
        ]
        states: dict[Path, m.Cli.AtomicFileState] = {}
        for state in inputs:
            if states.setdefault(state.path, state) != state:
                return result_type.fail(
                    f"accessor input snapshots disagree: {state.path}"
                )
        for py_file in py_files:
            observed = u.Cli.atomic_read_binary_file_state(py_file, required=True)
            if observed.failure:
                return result_type.from_failure(observed)
            state = observed.value
            if state.content is None or state.mode is None:
                return result_type.fail(
                    f"accessor source has no bytes or mode: {py_file}"
                )
            if states.setdefault(state.path, state) != state:
                return result_type.fail(
                    f"accessor source changed since preflight: {py_file}"
                )
        reports: list[m.Infra.AccessorMigrationFile] = []
        plans: list[m.Infra.SemanticFilePlan] = []
        resolver = FlextInfraAccessorOriginResolver(
            rope_project, namespace=params.namespace, module=params.module
        )
        for py_file in py_files:
            state = states[py_file.resolve()]
            if state.content is None:
                return result_type.fail(f"accessor source has no bytes: {py_file}")
            source = state.content.decode(c.DEFAULT_ENCODING)
            updated_source, changes = self._apply_automated_rewrites(
                rope_project, py_file, source, resolver=resolver
            )
            automated = tuple(change for change in changes if change.automated)
            warnings = (
                *resolver.collect_manual_warnings(
                    rope_project, py_file, source, rules=self._AUTOMATED_RULES
                ),
                *(change for change in changes if not change.automated),
            )
            reports.append(
                m.Infra.AccessorMigrationFile(
                    file=str(py_file),
                    automated_changes=automated,
                    warnings=warnings,
                    diff=self._diff(py_file, source, updated_source)
                    if automated
                    else "",
                    lint_before={},
                    lint_after={},
                    new_lint_errors={},
                )
            )
            if updated_source != source:
                plans.append(
                    m.Infra.SemanticFilePlan(
                        project=u.Infra.project_root(py_file) or params.repository_root,
                        path=state.path,
                        before=state,
                        desired_content=updated_source.encode(c.DEFAULT_ENCODING),
                        desired_mode=state.mode,
                        changes=tuple(change.original_name for change in automated),
                    )
                )
        return result_type.ok((tuple(plans), tuple(reports)))

    def _process_files(
        self,
        rope_project: t.Infra.RopeProject,
        py_files: t.SequenceOf[Path],
        *,
        params: m.Infra.AccessorMigrationInput,
        source_preview: p.Infra.SourcePreview,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[t.SequenceOf[m.Infra.AccessorMigrationFile]]:
        """Validate the whole coupled candidate before its single publication.

        Returns:
            Measured per-file evidence or the original protected failure.

        """
        result_type = r[t.SequenceOf[m.Infra.AccessorMigrationFile]]
        planned = self._plan_files(rope_project, py_files, params=params, inputs=inputs)
        if planned.failure:
            return result_type.from_failure(planned)
        plans, reports = planned.value
        if not plans:
            return result_type.ok(reports)
        updates = {
            plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
            for plan in plans
            if plan.desired_content is not None
        }
        staged = FlextInfraStagedPackage.plan_sources(params.repository_root, updates)
        if staged.failure:
            return result_type.from_failure(staged)
        gates = tuple(params.gates) or tuple(u.Infra.snapshot_lint_gates())
        checked = self.validate_candidate(staged.value, source_preview, gates)
        if checked.failure:
            return result_type.from_failure(checked)
        if params.apply:
            published = FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans, repository_root=params.repository_root
            )
            if published.failure:
                return result_type.from_failure(published)
        return result_type.ok(self._candidate_reports(reports, checked.value, gates))

    @staticmethod
    def _candidate_reports(
        reports: t.SequenceOf[m.Infra.AccessorMigrationFile],
        evidence: t.Pair[
            t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
            t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
        ],
        gates: t.StrSequence,
    ) -> t.SequenceOf[m.Infra.AccessorMigrationFile]:
        """Attach the measured batch evidence to the existing report model.

        Returns:
            Per-file reports retaining explicit not-executed empty snapshots.

        """
        before, after = evidence
        tools = tuple(u.Infra.selected_lint_tool_names(gates))
        return tuple(
            m.Infra.AccessorMigrationFile.model_validate({
                **report.model_dump(),
                "lint_tools": tools,
                "lint_before": before[Path(report.file)],
                "lint_after": after[Path(report.file)],
                "new_lint_errors": u.Infra.lint_new_errors(
                    before[Path(report.file)], after[Path(report.file)]
                ),
            })
            if report.automated_changes
            else report
            for report in reports
        )

    @staticmethod
    def validate_candidate(
        plan: m.Infra.StageSourcePlan,
        source_preview: p.Infra.SourcePreview,
        gates: t.StrSequence,
    ) -> p.Result[
        t.Pair[
            t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
            t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
        ]
    ]:
        """Validate changed and unchanged Python consumers in one staged view.

        Returns:
            Original/candidate lint evidence, or a pre-publication rejection.

        """
        paths = tuple(
            state.path
            for state in plan.inputs
            if state.content is not None
            and state.path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
        )
        scopes = plan.workspaces or (plan.workspace,)
        before = {
            path: snapshot
            for root in scopes
            for path, snapshot in u.Infra.lint_snapshots(
                tuple(path for path in paths if path.is_relative_to(root)),
                root,
                gates=gates,
            ).items()
        }

        def validate(
            view_root: Path,
            candidates: t.MappingKV[Path, Path],
        ) -> t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]]:
            staged_paths = {
                path: candidates.get(path, view_root / path.relative_to(plan.workspace))
                for path in dict.fromkeys((*paths, *plan.updates))
                if path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
                and (path not in plan.updates or plan.updates[path] is not None)
            }
            snapshots = {
                path: snapshot
                for root in scopes
                for path, snapshot in u.Infra.lint_snapshots(
                    tuple(
                        candidate
                        for path, candidate in staged_paths.items()
                        if path.is_relative_to(root)
                    ),
                    view_root / root.relative_to(plan.workspace),
                    gates=gates,
                ).items()
            }
            return {
                path: snapshots[candidate] for path, candidate in staged_paths.items()
            }

        previewed = source_preview.preview_sources(
            plan.workspace,
            plan.updates,
            validate,
            options=m.Infra.CodegenSourcePreviewOptions(
                workspaces=plan.workspaces,
                modes=plan.modes,
            ),
        )
        if previewed.failure:
            return r[
                t.Pair[
                    t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
                    t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
                ]
            ].from_failure(previewed)
        execution_errors = tuple(
            f"{path}: {error}"
            for path in set(before) | set(previewed.value)
            for snapshot in (before.get(path, {}), previewed.value.get(path, {}))
            for error in u.Infra.lint_execution_errors(snapshot)
        )
        errors = execution_errors + tuple(
            f"{path}: {tool}: {line}"
            for path in previewed.value
            for tool, lines in u.Infra.lint_new_errors(
                before.get(path, {}), previewed.value[path]
            ).items()
            for line in lines
        )
        result_type = r[
            t.Pair[
                t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
                t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
            ]
        ]
        if errors:
            return result_type.fail(
                "accessor candidate rejected before publication:\n" + "\n".join(errors)
            )
        return result_type.ok((before, previewed.value))

    @staticmethod
    def _diff(py_file: Path, before: str, after: str) -> str:
        """Diff.

        Returns:
            The resulting ``str``.

        """
        diff_lines = u.Infra.unified_diff_lines(
            before,
            after,
            fromfile=f"a/{py_file}",
            tofile=f"b/{py_file}",
            max_lines=80,
        )
        return "".join(diff_lines)

    @staticmethod
    def render_text(report: m.Infra.AccessorMigrationReport) -> str:
        """Render an accessor migration report as CLI text.

        Returns:
            The resulting ``str``.

        """
        lines: t.MutableSequenceOf[str] = [
            "Accessor Migration",
            f"workspace: {report.workspace}",
            f"mode: {'dry-run' if report.dry_run else 'apply'}",
            f"files_scanned: {report.files_scanned}",
            f"files_with_changes: {report.files_with_changes}",
            f"automated_changes: {report.automated_change_count}",
            f"warnings: {report.warning_count}",
            f"lint_tools: {', '.join(report.lint_tools)}",
        ]
        for tool in report.lint_tools:
            if tool not in report.lint_before_totals:
                lines.append(f"lint-totals:{tool} not-executed (no automated rewrites)")
                continue
            lines.append(
                f"lint-totals:{tool} "
                f"before={report.lint_before_totals.get(tool, 0)} "
                f"after={report.lint_after_totals.get(tool, 0)} "
                f"new={report.new_lint_error_totals.get(tool, 0)}",
            )
        for file_report in report.files:
            lines.append(f"\n{file_report.file}")
            for change in file_report.automated_changes:
                lines.append(
                    f"  auto:{change.line} {change.original_name} "
                    f"-> {change.replacement_name}",
                )
            for warning in file_report.warnings:
                target = (
                    f" -> {warning.replacement_name}"
                    if warning.replacement_name
                    else ""
                )
                lines.append(f"  warn:{warning.line} {warning.original_name}{target}")
                lines.append(f"    {warning.reason}")
            for tool in file_report.lint_tools:
                receipt = file_report.lint_after.get(tool)
                issues = (
                    (
                        *receipt.errors,
                        *(
                            (receipt.execution_error,)
                            if receipt.execution_error
                            else ()
                        ),
                    )
                    if receipt is not None
                    else ("not executed",)
                )
                lines.append(f"  lint-after:{tool}")
                lines.extend(
                    tuple(f"    {issue}" for issue in issues[:4]) or ("    ok",)
                )
            for tool in file_report.lint_tools:
                issues = tuple(file_report.new_lint_errors.get(tool, ()))
                if not issues:
                    continue
                lines.append(f"  new-lint:{tool}")
                lines.extend(f"    {issue}" for issue in issues[:4])
            if file_report.diff:
                lines.append("  diff:")
                lines.extend(
                    f"    {line}"
                    for line in file_report.diff.rstrip().splitlines()[:40]
                )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraAccessorMigrationReportMixin"]
