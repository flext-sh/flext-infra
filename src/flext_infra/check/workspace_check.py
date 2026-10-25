"""FLEXT infrastructure workspace checker.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.check import (
    FlextInfraGateRegistry,
    FlextInfraWorkspaceCheckGatesMixin,
    FlextInfraWorkspaceCheckReportsMixin,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_infra.workspace.runtime_dependencies import (
    FlextInfraRuntimeDependencyCollector,
)


class FlextInfraWorkspaceChecker(
    FlextInfraServiceBase[bool],
    FlextInfraWorkspaceCheckGatesMixin,
    FlextInfraWorkspaceCheckReportsMixin,
):
    """Run workspace quality gates and generate reports."""

    _repository_root: Path = m.PrivateAttr()
    _registry: FlextInfraGateRegistry = m.PrivateAttr()
    _default_reports_dir: Path = m.PrivateAttr()
    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
        arbitrary_types_allowed=True,
    )

    @override
    def model_post_init(self, __context: t.ScalarMapping | None, /) -> None:
        """Initialize private gate state from validated service fields."""
        super().model_post_init(__context)
        self._repository_root = self.repository_root
        self._registry = FlextInfraGateRegistry(
            project_gates=u.Infra
            .load_codegen_inputs(self.repository_root)
            .unwrap()
            .spec.make.project_check_gates
        )
        self._default_reports_dir = u.Cli.resolve_report_dir(
            self._repository_root,
            c.Infra.PROJECT,
            c.Infra.VERB_CHECK,
        )

    @staticmethod
    def parse_tool_args(raw: str | None) -> t.StrSequence:
        """Parse extra gate arguments passed as a shell-style string.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if raw is None:
            return list[str]()
        return [item for item in shlex.split(raw) if item]

    def resolve_gates(self, gates: t.StrSequence) -> p.Result[list[str]]:
        """Validate exact, unique requested gate names without normalization.

        Returns:
            The resulting ``p.Result[list[str]]``.

        """
        if not gates:
            return r[list[str]].fail("ERROR: at least one quality gate is required")
        resolved: list[str] = []
        for gate in gates:
            if not gate or gate != gate.strip():
                return r[list[str]].fail(f"ERROR: invalid gate name {gate!r}")
            if gate not in self._registry.gate_ids:
                return r[list[str]].fail(f"ERROR: unknown gate '{gate}'")
            if gate in resolved:
                return r[list[str]].fail(f"ERROR: duplicate gate '{gate}'")
            resolved.append(gate)
        return r[list[str]].ok(list(resolved))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return r[bool].fail("Use execute_command() directly")

    def execute_payload(self, params: m.Infra.RunCommand) -> p.Result[bool]:
        """Execute quality gates from the canonical check command payload.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return self._execute_payload(params)

    def execute_report(
        self, params: m.Infra.RunCommand
    ) -> p.Result[m.Infra.CheckReportSummary]:
        """Return this invocation's typed facts, retaining failed gate verdicts."""
        return self._execute_report(params)

    def execute_integrity(self, params: m.Infra.RunCommand) -> p.Result[bool]:
        """Select runtime and declared project integrity in the same checker.

        Returns:
            Success flag of the integrity check execution.

        """
        policy = u.Infra.load_codegen_inputs(params.repository_root).unwrap().spec.make
        gates = (
            c.Infra.RUNTIME_INTEGRITY,
            *(gate.name for gate in policy.project_check_gates if gate.integrity),
        )
        return self._execute_payload(params.model_copy(update={"gates": gates}))

    def _execute_payload(
        self,
        params: m.Infra.RunCommand,
    ) -> p.Result[bool]:
        """Judge the typed report produced by the one native execution.

        Returns:
            Success flag from the summarized project results.

        """
        report = self._execute_report(params)
        if report.failure:
            return r[bool].from_failure(report)
        if not report.value.complete:
            return r[bool].fail("quality check target accounting is incomplete")
        return self._summarize_project_results(
            report.value.results, report.value.targets
        )

    def _execute_report(
        self,
        params: m.Infra.RunCommand,
    ) -> p.Result[m.Infra.CheckReportSummary]:
        """Execute the native gates in the invoking runtime.

        Returns:
            The complete native checker result.

        """
        selected_files_result = self._resolve_selected_files(params)
        if selected_files_result.failure:
            return r[m.Infra.CheckReportSummary].from_failure(selected_files_result)
        selected_files = selected_files_result.value
        project_targets_result = self._resolve_project_targets(params, selected_files)
        if project_targets_result.failure:
            return r[m.Infra.CheckReportSummary].from_failure(project_targets_result)
        project_targets = project_targets_result.value
        # An omitted gate selection resolves the requested gate set from the
        # typed Make spec at runtime, never from a generated projection.
        gates = list(
            params.gates
            or u.Infra.selected_check_gates(
                u.Infra.load_codegen_inputs(params.repository_root).unwrap().spec.make,
                params.gate_set,
            )
        )
        destination = params.report_output
        before = (
            None
            if destination is None
            else u.Cli.atomic_read_binary_file_state(
                destination, required=False
            ).unwrap()
            if destination.is_absolute() and destination.parent.is_dir()
            else None
        )
        refusal = self._report_output_refusal(destination, before)
        if refusal is not None:
            return r[m.Infra.CheckReportSummary].fail(refusal)
        if selected_files:
            u.Cli.info(
                f"file-gate: source={selected_files[0]} gates={gates} "
                "selection=CLI:check run --gates"
            )
        gate_ctx = m.Infra.GateContext(
            repository_root=params.repository_root,
            reports_dir=params.reports_dir_path,
            apply_fixes=params.apply,
            check_only=params.check_only,
            fail_fast=params.fail_fast,
            ruff_args=tuple(self.parse_tool_args(params.ruff_args)),
            pyright_args=tuple(self.parse_tool_args(params.pyright_args)),
            selected_files=selected_files,
            runtime_dependency_collector=FlextInfraRuntimeDependencyCollector(
                python=Path(sys.executable),
                development_only=(),
            ),
            # Applicability and every gate of this invocation share each
            # repository's Git scope facts instead of re-reading Git.
            scope_facts=u.Infra.ScopeFacts(),
        )
        return self.run_projects_report(
            project_targets,
            gates,
            gate_ctx,
            report_output_state=before,
        )

    @staticmethod
    def _report_output_refusal(
        destination: Path | None,
        before: m.Cli.AtomicFileState | None,
    ) -> str | None:
        """Refuse a report destination this invocation cannot exclusively own.

        Returns:
            Why the destination is refused, or ``None`` for an absent or
            exclusively ownable destination.

        """
        if destination is None:
            return None
        if before is None:
            return (
                "check report output requires an absolute path in an existing directory"
            )
        if before.content is not None:
            return f"check report output already exists: {destination}"
        return None

    @classmethod
    def _resolve_selected_files(
        cls,
        params: m.Infra.RunCommand,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Resolve the optional ``--file`` selection into one repository file.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        if params.file is None:
            return r[t.VariadicTuple[Path]].ok(())
        if not params.gates:
            return r[t.VariadicTuple[Path]].fail(
                "--file requires explicit canonical --gates selection"
            )
        requested = u.Infra.normalize_sequence_values(params.projects)
        if (
            params.apply
            or params.ruff_args is not None
            or params.pyright_args is not None
            or (requested and tuple(requested) != (".",))
        ):
            return r[t.VariadicTuple[Path]].fail(
                "file-gate requires read-only local selection without tool overrides",
            )
        return cls._resolve_repository_file(params.repository_root, params.file)

    @staticmethod
    def _resolve_repository_file(
        repository_root: Path,
        raw: str,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Resolve a literal repository-relative source file without symlinks.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        relative = Path(raw)
        if (
            not raw
            or raw != raw.strip()
            or relative.is_absolute()
            or any(part in {"", ".", ".."} for part in raw.split("/"))
        ):
            return r[t.VariadicTuple[Path]].fail(
                f"invalid literal repository-relative FILE: {raw!r}"
            )
        root = repository_root.resolve(strict=True)
        selected = root / relative
        current = root
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                return r[t.VariadicTuple[Path]].fail(
                    f"FILE has a symlink component: {current}"
                )
        if (
            not selected.is_file()
            or not selected.resolve(strict=True).is_relative_to(root)
            or selected.suffix not in {".py", ".pyi"}
        ):
            return r[t.VariadicTuple[Path]].fail(
                f"FILE is not an existing repository file: {selected}"
            )
        return r[t.VariadicTuple[Path]].ok((selected,))

    @staticmethod
    def _summarize_project_results(
        results: t.SequenceOf[m.Infra.ProjectResult],
        project_targets: t.SequenceOf[m.Infra.CheckProjectTarget],
    ) -> p.Result[bool]:
        """Fail unless every requested project executed and passed.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if len(results) != len(project_targets):
            return r[bool].fail(
                "quality checks did not execute every requested project: "
                f"{len(results)}/{len(project_targets)}",
            )
        failed_projects = [project for project in results if not project.passed]
        if failed_projects:
            failed_names = ", ".join(project.project for project in failed_projects)
            total_findings = sum(
                len(execution.issues)
                for project in failed_projects
                for execution in project.gates.values()
            )
            return r[bool].fail(
                f"quality checks failed for: {failed_names} "
                f"({total_findings} findings; see the check summary and reports)",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _resolve_project_targets(
        params: m.Infra.RunCommand,
        selected_files: t.VariadicTuple[Path],
    ) -> p.Result[t.SequenceOf[m.Infra.CheckProjectTarget]]:
        """Resolve the selected projects from the declared workspace topology.

        An omitted selection covers only the invoked repository under scope
        ``self``. Scope ``all`` adds every governed member the workspace
        declares in ``.gitmodules``, resolved by the workspace detector, so a
        workspace verb processes all members in one pass. A literal file
        selects only its deepest declared project owner.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CheckProjectTarget]]``.

        """
        if selected_files:
            discovered = u.Infra.resolve_projects(params.repository_root, ())
            if discovered.failure:
                return r[t.SequenceOf[m.Infra.CheckProjectTarget]].from_failure(
                    discovered,
                )
            owners = [
                project
                for project in discovered.value
                if selected_files[0].is_relative_to(project.path)
            ]
            if not owners:
                return r[t.SequenceOf[m.Infra.CheckProjectTarget]].fail(
                    f"FILE has no declared project owner: {selected_files[0]}",
                )
            owner = max(owners, key=lambda project: len(project.path.parts))
            return r[t.SequenceOf[m.Infra.CheckProjectTarget]].ok((
                m.Infra.CheckProjectTarget(name=owner.name, path=owner.path),
            ))
        requested = u.Infra.normalize_sequence_values(params.projects)
        if requested:
            return r[t.SequenceOf[m.Infra.CheckProjectTarget]].ok(
                tuple(
                    m.Infra.CheckProjectTarget(
                        name=project_name,
                        path=params.repository_root / project_name,
                    )
                    for project_name in requested
                ),
            )
        return FlextInfraWorkspaceChecker._scoped_targets(params)

    @staticmethod
    def _scoped_targets(
        params: m.Infra.RunCommand,
    ) -> p.Result[t.SequenceOf[m.Infra.CheckProjectTarget]]:
        """Resolve an omitted project selection from the requested scope.

        Returns:
            The invoked repository under ``self``; it and every governed
            member under ``all``.

        """
        result_type = r[t.SequenceOf[m.Infra.CheckProjectTarget]]
        root_target = m.Infra.CheckProjectTarget(
            name=params.repository_root.name,
            path=params.repository_root,
        )
        # The contract stores enum values; StrEnum members compare equal.
        scope = c.Infra.CodegenConformScope(params.scope)
        if scope is c.Infra.CodegenConformScope.SELF:
            return result_type.ok((root_target,))
        if scope is not c.Infra.CodegenConformScope.ALL:
            return result_type.fail(
                f"check run accepts scope self or all, not {scope.value}",
            )
        return FlextInfraWorkspaceDetector.load_workspace_spec(
            params.repository_root,
        ).map(
            lambda workspace: (
                root_target,
                *(
                    m.Infra.CheckProjectTarget(
                        name=member.name,
                        path=params.repository_root / member.path,
                    )
                    for member in u.Infra.mutable_flext_members(workspace)
                ),
            ),
        )

    def format(self, project_dir: Path) -> p.Result[m.Infra.GateResult]:
        """Run format checks for one project.

        Returns:
            The resulting ``p.Result[m.Infra.GateResult]``.

        """
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.FORMAT, project_dir).result,
        )

    def lint(self, project_dir: Path) -> p.Result[m.Infra.GateResult]:
        """Run lint checks for one project.

        Returns:
            The resulting ``p.Result[m.Infra.GateResult]``.

        """
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.LINT, project_dir).result,
        )

    def run_project(
        self,
        project: str,
        gates: t.StrSequence,
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
        """Run selected gates for one project.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.ProjectResult]]``.

        """
        return self.run_projects([project], list(gates))

    def run_projects(
        self,
        projects: t.StrSequence | t.SequenceOf[m.Infra.CheckProjectTarget],
        gates: t.StrSequence,
        ctx: m.Infra.GateContext | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
        """Expose project results from the same invocation-owned report.

        Returns:
            The project results of the invocation report.

        """
        return self.run_projects_report(projects, gates, ctx).map(
            lambda summary: summary.results
        )

    def run_projects_report(
        self,
        projects: t.StrSequence | t.SequenceOf[m.Infra.CheckProjectTarget],
        gates: t.StrSequence,
        ctx: m.Infra.GateContext | None = None,
        report_output_state: m.Cli.AtomicFileState | None = None,
    ) -> p.Result[m.Infra.CheckReportSummary]:
        """Run selected gates in one exclusively owned invocation report directory.

        The context carries the report base, the fail-fast policy and the
        invocation's shared facts; without one the checker's defaults apply.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.ProjectResult]]``.

        """
        resolved_gates_result = self.resolve_gates(gates)
        if resolved_gates_result.failure:
            return r[m.Infra.CheckReportSummary].from_failure(
                resolved_gates_result,
            )
        resolved_gates = resolved_gates_result.value
        targets = self._project_targets(projects)
        if not targets:
            return r[m.Infra.CheckReportSummary].fail(
                "quality check selected no projects",
            )
        unrunnable = [
            str(target.path / c.PYPROJECT_FILENAME)
            for target in targets
            if not (target.path / c.PYPROJECT_FILENAME).is_file()
        ]
        if unrunnable:
            return r[m.Infra.CheckReportSummary].fail(
                "quality check selected projects without a pyproject: "
                + ", ".join(unrunnable),
            )
        base_ctx = ctx or m.Infra.GateContext(
            repository_root=self._repository_root,
            reports_dir=self._default_reports_dir,
            fail_fast=c.Infra.CHECK_FAIL_FAST_DEFAULT,
            scope_facts=u.Infra.ScopeFacts(),
        )
        dir_ensure = u.Cli.ensure_dir(base_ctx.reports_dir)
        if dir_ensure.failure:
            return r[m.Infra.CheckReportSummary].from_failure(dir_ensure)
        # One invocation owns one report leaf: concurrent checks never
        # overwrite each other's receipt.
        report_base = base_ctx.reports_dir / u.generate_id()
        report_base.mkdir(exist_ok=False)
        effective_ctx = base_ctx.model_copy(update={"reports_dir": report_base})
        requested_gates = tuple(resolved_gates)
        report_targets = tuple(
            m.Infra.CheckProjectTarget(
                name=target.path.name,
                path=target.path.resolve(),
                applicable_gates=(
                    requested_gates
                    if effective_ctx.selected_files
                    else self._registry.applicable_gate_ids(
                        requested_gates, target.path, effective_ctx
                    )
                ),
            )
            for target in targets
        )
        reached: dict[Path, m.Infra.ProjectResult] = {}
        current_summary = m.Infra.CheckReportSummary(
            requested_gates=requested_gates,
            targets=report_targets,
            results=(),
            selected_files=tuple(effective_ctx.selected_files),
        )

        def publish_summary(summary: m.Infra.CheckReportSummary) -> None:
            """Retain this invocation's current facts through the existing writers."""
            nonlocal current_summary, report_output_state
            if report_output_state is not None:
                # The external publication fence runs before the first gate too:
                # a competing destination cannot authorize any gate effects.
                report_output_state = self._publish_invocation_summary(
                    summary,
                    report_output_state,
                )
            self._write_reports(report_base, summary).unwrap()
            current_summary = summary

        publish_summary(current_summary)

        def publish_progress(project_dir: Path, project: m.Infra.ProjectResult) -> None:
            reached[project_dir.resolve()] = project
            publish_summary(
                m.Infra.CheckReportSummary(
                    requested_gates=requested_gates,
                    targets=report_targets,
                    results=tuple(
                        reached[target.path]
                        for target in report_targets
                        if target.path in reached
                    ),
                    selected_files=tuple(effective_ctx.selected_files),
                ),
            )

        effective_ctx = effective_ctx.model_copy(
            update={"check_progress": publish_progress}
        )
        # The loop consumes the applicability elected above: one owner
        # computation per invocation, never a second content scan.
        outcome = self._run_project_loop(
            report_targets,
            resolved_gates,
            effective_ctx,
            fail_fast=effective_ctx.fail_fast,
        )
        summary = m.Infra.CheckReportSummary(
            requested_gates=requested_gates,
            targets=report_targets,
            results=tuple(outcome.results),
            # A file-scoped run never claims whole-project quality.
            selected_files=tuple(effective_ctx.selected_files),
        )
        # Preserve a changed returned result without repeating an identical
        # last-gate or zero-applicable-gate publication.
        if summary.results != current_summary.results:
            publish_summary(summary)
        self._print_summary(report_base, outcome, summary)
        return r[m.Infra.CheckReportSummary].ok(summary)

    def _project_targets(
        self,
        projects: t.StrSequence | t.SequenceOf[m.Infra.CheckProjectTarget],
    ) -> t.SequenceOf[m.Infra.CheckProjectTarget]:
        """Return typed project targets from public names or internal selections.

        Returns:
            Typed project targets from public names or internal selections.

        """
        targets: list[m.Infra.CheckProjectTarget] = []
        for project in projects:
            if isinstance(project, m.Infra.CheckProjectTarget):
                targets.append(project)
                continue
            targets.append(
                m.Infra.CheckProjectTarget(
                    name=project,
                    path=self._repository_root / project,
                ),
            )
        return tuple(targets)


__all__: list[str] = ["FlextInfraWorkspaceChecker"]
