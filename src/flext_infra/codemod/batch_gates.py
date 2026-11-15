"""Gate measurement and ast-grep batch execution for the mod safety circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.codemod import FlextInfraModReplacements
from flext_infra.codemod._gates import FlextInfraModGateScanner


class FlextInfraModGateEngine(FlextInfraModGateScanner):
    """Execute ast-grep rewrites and measure the catalog findings they leave."""

    @classmethod
    def apply_report(
        cls,
        root: Path,
        report: p.Infra.ModOccurrenceReport[p.Infra.ModScanFinding],
        *,
        exact_replacements: bool = False,
    ) -> p.Result[bool]:
        """Publish the admitted native report only under its original input CAS.

        Returns:
            Real publication acceptance or the first stale-input failure.

        """
        if not isinstance(report, m.Infra.ModScanReport):
            return r[bool].fail(
                "publication requires an authenticated native scan report"
            )
        captured = tuple(
            entry.source_state
            for entry in report.entries
            if entry.actionable and entry.source_state is not None
        )
        verified = u.Cli.atomic_verify_binary_file_states(
            captured,
            nonsecret_source_paths=tuple(
                dict.fromkeys(Path(state.path) for state in captured)
            ),
        )
        if verified.failure:
            return r[bool].from_failure(verified)
        return FlextInfraModReplacements.publish(
            root, cls.authored(report), exact_replacements=exact_replacements
        )

    @classmethod
    def _native_scan_report(
        cls,
        root: Path,
        plan: p.Infra.CodemodRulePlan,
        targets: Sequence[str],
        context: p.Infra.ModScanSourceContext,
        *,
        artifact_root: Path | None = None,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Combine every elected provider's complete ordered native occurrences.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanReport]``.

        """
        rules_by_id = {rule.id: rule for rule in plan.rules}
        root = root.resolve()
        artifact_root = root if artifact_root is None else artifact_root.resolve()
        native_targets = tuple(
            target for target in targets if Path(target).suffix != ".pyi"
        )
        with tempfile.TemporaryDirectory(prefix="mod-native-catalog-") as directory:
            reports: list[p.Infra.ModScanReport] = []
            for project, project_targets in u.Infra.project_targets(
                plan, native_targets
            ):
                resolved_project = (
                    project
                    if context.project_source_roots is None
                    else context.project_source_roots[project]
                ).resolve()
                if not resolved_project.is_relative_to(root):
                    return r[p.Infra.ModScanReport].fail(
                        f"native scan project escapes workspace root: "
                        f"{resolved_project}"
                    )
                stage = Path(directory) / str(len(reports))
                try:
                    ruleset = u.Infra.codemod_stage_scan_ruleset(
                        u.Infra.project_plan(plan, project), stage
                    )
                except ValueError as exc:
                    reports.append(
                        cls.recounted(()).model_copy(
                            update={"native_failures": (str(exc),)}
                        )
                    )
                    break
                sys.stderr.write(
                    f"mod: ast-grep project={project.name} "
                    f"provider={ruleset.provider} rules={len(ruleset.rule_ids)}\n",
                )
                sys.stderr.flush()
                projected = cls._ruleset_report(
                    root,
                    ruleset,
                    rules_by_id,
                    (project_targets, context),
                    artifact_root=artifact_root / resolved_project.relative_to(root),
                )
                if projected.failure:
                    return r[p.Infra.ModScanReport].from_failure(projected)
                reports.append(projected.value)
            failures = tuple(
                failure for report in reports for failure in report.native_failures
            )
            scanned = r[p.Infra.ModScanReport].ok(
                cls.recounted(
                    tuple(entry for report in reports for entry in report.entries),
                    native_artifacts=tuple(
                        artifact
                        for report in reports
                        for artifact in report.native_artifacts
                    ),
                ).model_copy(update={"native_failures": failures})
            )
            path_findings = u.Infra.codemod_path_findings(
                root, tuple(context.inventory), plan.rules
            )
            if not path_findings:
                return scanned
            path_report = Path(directory) / "owned-path.jsonl"
            u.Cli.atomic_write_text_file(
                path_report,
                "".join(finding.model_dump_json() + "\n" for finding in path_findings),
            ).unwrap()
            artifact = u.Infra.publish_mod_native_artifact(artifact_root, path_report)
            admitted_paths = cls._parse_findings(
                artifact.path,
                root,
                ({rule.id: rule.resource for rule in plan.rules}, frozenset()),
                context,
                artifact,
            )
            if admitted_paths.failure:
                return admitted_paths
            return r[p.Infra.ModScanReport].ok(
                cls.recounted(
                    (*scanned.value.entries, *admitted_paths.value.entries),
                    native_artifacts=(*scanned.value.native_artifacts, artifact),
                ).model_copy(update={"native_failures": failures})
            )

    @classmethod
    def _publish_scan(
        cls,
        root: Path,
        report: p.Infra.ModScanReport,
        publication: p.Infra.ModScanPublication,
        *,
        exact_replacements: bool,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Publish full evidence before any authorized source replacement.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanReport]``.

        """
        sys.stderr.write(f"mod: publish evidence findings={report.findings}\n")
        sys.stderr.flush()
        receipt = u.Infra.publish_mod_scan_evidence(
            root, report, publication=publication
        )
        if receipt.failure:
            return r[p.Infra.ModScanReport].from_failure(receipt)
        cls._report_evidence(receipt.value)
        if publication.command == c.Infra.ModScanCommand.APPLY and report.actionable:
            published = cls.apply_report(
                root,
                report,
                exact_replacements=exact_replacements,
            )
            if published.failure:
                return r[p.Infra.ModScanReport].from_failure(published)
        return r[p.Infra.ModScanReport].ok(report)

    @classmethod
    def _scan_focused(
        cls,
        root: Path,
        plan: p.Infra.CodemodRulePlan,
        *,
        fix: bool,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Scan a focused plan only on the files its selection matches.

        Returns:
            The located report when nothing matches, else the focused scan of
            the matched files.

        """
        selected = frozenset(plan.selected_rule_ids or ())
        located = cls.scan(
            root,
            fix=False,
            selection=u.Infra.codemod_plan_restricted(plan, selected).model_copy(
                update={"selected_rule_ids": None}
            ),
        )
        if located.failure or not located.value.files:
            return located
        return cls.scan(
            root,
            fix=fix,
            selection=plan,
            source_files=tuple(
                sorted(root.resolve() / path for path in located.value.files)
            ),
        )

    @classmethod
    def scan(
        cls,
        root: Path,
        *,
        fix: bool,
        selection: Sequence[str] | p.Infra.CodemodRulePlan | None = None,
        source_files: Sequence[Path] | None = None,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Scan or apply every ruleset elected by the composed rule-plan SSOT.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanReport]``.

        """
        if selection is None or isinstance(selection, Sequence):
            with u.Infra.codemod_workspace_snapshot(root) as snapshot:
                planned = u.Infra.codemod_rule_plan(snapshot, rule_ids=selection)
            if planned.failure:
                return r[p.Infra.ModScanReport].from_failure(planned)
            plan = planned.value
        else:
            plan = selection
            if root.resolve() not in plan.project_rule_ids:
                return r[p.Infra.ModScanReport].fail(
                    "precomposed scan plan requires its governed root and owns rule "
                    "selection"
                )
        if plan.selected_rule_ids is not None and source_files is None:
            return cls._scan_focused(root, plan, fix=fix)
        rules_by_id = {rule.id: rule for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root, source_files=source_files)
        sys.stderr.write(
            f"mod: ast-grep {'apply' if fix else 'scan'} "
            f"providers={len(plan.rulesets)} rules={len(plan.rules)}\n",
        )
        sys.stderr.flush()
        cls._require_regular_stub_leaves(root, targets)
        scanned = cls.native_findings(root, plan, targets).flat_map(cls._completed_scan)
        if scanned.failure:
            return r[p.Infra.ModScanReport].from_failure(scanned)
        complete_report = scanned.value.model_copy(
            update={
                "repository_root": root.resolve(),
                "source_files": (
                    tuple(path.resolve() for path in source_files)
                    if source_files is not None
                    else None
                ),
                "rule_plan": plan,
            }
        )
        declared = cls._validate_expected_receipts(plan.rules, complete_report)
        if declared.failure:
            return r[p.Infra.ModScanReport].from_failure(declared)
        return cls._publish_scan(
            root,
            complete_report,
            m.Infra.ModScanPublication(
                command=(
                    c.Infra.ModScanCommand.APPLY if fix else c.Infra.ModScanCommand.SCAN
                ),
                scope=targets,
                repositories=tuple(project.name for project in plan.project_rule_ids),
                rule_ids=tuple(rules_by_id),
            ),
            exact_replacements=False,
        )

    @classmethod
    def _require_regular_stub_leaves(cls, root: Path, targets: Sequence[str]) -> None:
        """Refuse a selected stub leaf that is not a regular file."""
        for stub in sorted(cls._scan_source_paths(root, targets)):
            if stub.suffix == ".pyi":
                u.Cli.atomic_read_binary_file_state(stub, required=True).unwrap()

    @staticmethod
    def _completed_scan(
        report: p.Infra.ModScanReport,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Admit only a report whose scanners all completed; mod never applies a part.

        Returns:
            The report, or the stopped scanners' blocking failures.

        """
        if report.native_failures:
            return r[p.Infra.ModScanReport].fail("\n".join(report.native_failures))
        return r[p.Infra.ModScanReport].ok(report)

    @classmethod
    def native_findings(
        cls,
        root: Path,
        plan: p.Infra.CodemodRulePlan,
        targets: Sequence[str],
        *,
        runner: p.Cli.CommandRunner = u.Cli,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Scan targets with every elected ruleset; check and mod share this route.

        Returns:
            Every elected native and owned-path finding, or the first failure.

        """
        context = m.Infra.ModScanSourceContext(
            inventory={
                path: None
                if path.suffix == ".pyi"
                else u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in sorted(cls._scan_source_paths(root, targets))
            },
            repository_roots=tuple(
                sorted(plan.project_rule_ids, key=cls._path_depth, reverse=True)
            ),
            runner=runner,
        )
        scanned = cls._native_scan_report(root, plan, targets, context)
        if scanned.failure:
            return r[p.Infra.ModScanReport].from_failure(scanned)
        return r[p.Infra.ModScanReport].ok(
            cls._elected(
                root,
                scanned.value,
                {rule.id: rule for rule in plan.rules},
                plan.project_rule_ids,
            ).model_copy(update={"native_failures": scanned.value.native_failures})
        )

    @staticmethod
    def _candidate_scan_states(
        candidate: p.Infra.StageSourcePlan,
        view_root: Path,
    ) -> p.Result[tuple[p.Cli.AtomicFileState, ...]]:
        """Authenticate each staged effect against its declared original witness.

        Returns:
            Actual staged receipts rebound to logical paths for binding analysis.

        """
        result_type = r[tuple[p.Cli.AtomicFileState, ...]]
        declared = {file.path: file for file in candidate.declared_files}
        originals = {state.path: state for state in candidate.inputs}
        if len(declared) != len(candidate.declared_files) or set(declared) != set(
            candidate.updates
        ):
            return result_type.fail("semantic scan candidate effects are not declared")
        for path, source in candidate.updates.items():
            effect = declared[path]
            original = originals.get(path)
            content = None if source is None else source.encode(c.DEFAULT_ENCODING)
            if (
                effect.desired_content != content
                or original is None
                or effect.before != original
            ):
                return result_type.fail(
                    "semantic scan candidate effect differs from its declaration: "
                    f"{path}"
                )
        states: list[p.Cli.AtomicFileState] = []
        for original in candidate.inputs:
            if not original.path.is_relative_to(candidate.workspace):
                states.append(original)
                continue
            effect = declared.get(original.path)
            staged = u.Cli.atomic_read_binary_file_state(
                view_root / original.path.relative_to(candidate.workspace)
            )
            if (
                staged.failure
                or staged.value.content
                != (original.content if effect is None else effect.desired_content)
                or staged.value.mode
                != (original.mode if effect is None else effect.desired_mode)
            ):
                return (
                    result_type.from_failure(staged)
                    if staged.failure
                    else result_type.fail(
                        "semantic scan staged effect differs from its declaration: "
                        f"{original.path}"
                    )
                )
            states.append(staged.value.model_copy(update={"path": original.path}))
        return result_type.ok(tuple(states))

    @classmethod
    def scan_candidate(
        cls,
        root: Path,
        view_root: Path,
        candidate: p.Infra.StageSourcePlan,
        *,
        selection: Sequence[str] | p.Infra.CodemodRulePlan | None = None,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Scan an immutable overlay with the original catalog and logical policy.

        Returns:
            Selected findings authenticated to candidate bytes and bindings.

        """
        root = root.resolve()
        captured = cls._candidate_scan_states(candidate, view_root)
        if captured.failure:
            return r[p.Infra.ModScanReport].from_failure(captured)
        view_root /= root.relative_to(candidate.workspace)
        if selection is None or isinstance(selection, Sequence):
            with u.Infra.codemod_workspace_snapshot(root) as snapshot:
                plan = u.Infra.codemod_rule_plan(snapshot, rule_ids=selection).unwrap()
        else:
            plan = selection
        staged_plan = plan.model_copy(
            update={
                "project_rule_ids": {
                    view_root / project.relative_to(root): rule_ids
                    for project, rule_ids in plan.project_rule_ids.items()
                }
            }
        )
        states = captured.value
        owned_sources = u.Infra.facade_original_sources(root, states)
        context = m.Infra.ModScanSourceContext(
            inventory={
                view_root / state.path.relative_to(root): state.model_copy(
                    update={"path": view_root / state.path.relative_to(root)}
                )
                for state in states
                if state.path in owned_sources
            },
            project_source_roots={
                project: view_root / project.relative_to(root)
                for project in plan.project_rule_ids
            },
            repository_roots=tuple(
                sorted(
                    staged_plan.project_rule_ids,
                    key=cls._path_depth,
                    reverse=True,
                )
            ),
        )
        logical = {state.path: state for state in states}
        entries: list[p.Infra.ModScanFinding] = []
        scanned = cls._native_scan_report(
            view_root,
            plan,
            u.Infra.ast_grep_scan_targets(view_root),
            context,
            artifact_root=root,
        ).flat_map(cls._completed_scan)
        if scanned.failure:
            return r[p.Infra.ModScanReport].from_failure(scanned)
        report = cls._elected(
            view_root,
            scanned.value,
            {rule.id: rule for rule in plan.rules},
            staged_plan.project_rule_ids,
        )
        for entry in report.entries:
            relative = (
                entry.file.relative_to(view_root)
                if entry.file.is_absolute()
                else entry.file
            )
            entries.append(
                entry.model_copy(
                    update={
                        "file": relative,
                        "repository": cls._finding_repository(
                            relative,
                            sorted(
                                plan.project_rule_ids,
                                key=cls._path_depth,
                                reverse=True,
                            ),
                            root,
                        ),
                        "source_state": logical[(root / relative).resolve()],
                    }
                )
            )
        report = cls.recounted(
            tuple(entries),
            native_artifacts=report.native_artifacts,
        )
        sys.stderr.write(
            "mod: candidate logical repositories="
            f"{','.join(sorted({entry.repository for entry in entries}))}\n"
        )
        current = cls._validate_expected_receipts(plan.rules, report)
        if current.failure:
            return r[p.Infra.ModScanReport].from_failure(current)
        return u.Cli.atomic_verify_binary_file_states(candidate.inputs).map(
            lambda _: report
        )


__all__: list[str] = ["FlextInfraModGateEngine"]
