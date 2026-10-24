"""Gate measurement and ast-grep batch execution for the mod safety circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import tempfile
from functools import partial
from pathlib import Path
from time import monotonic

import flext_cli

from flext_infra import c, m, p, r, settings, t, u
from flext_infra._config import FlextInfraConfig
from flext_infra.codemod import (
    FlextInfraCodemodSnapshotReconciler,
    FlextInfraModReplacements,
)
from flext_infra.codemod._batch_gates_findings import (
    FlextInfraModGateEngineFindingsMixin,
)
from flext_infra.codemod._batch_gates_fixtures import (
    FlextInfraModGateEngineFixturesMixin,
)


class FlextInfraModGateEngine(
    FlextInfraModGateEngineFixturesMixin,
    FlextInfraModGateEngineFindingsMixin,
):
    """Execute ast-grep rewrites and measure the catalog findings they leave."""

    @staticmethod
    def _progress(message: str, due: float = 0) -> float:
        """Emit a causal progress row at the configured heartbeat interval.

        Returns:
            The next monotonic deadline for an interval progress row.

        """
        now = monotonic()
        if now < due:
            return due
        sys.stderr.write(f"mod: {message}\n")
        sys.stderr.flush()
        return now + flext_cli.settings.cli_process_heartbeat_seconds

    @staticmethod
    def _path_depth(path: Path) -> int:
        """Return path depth for deterministic deepest-owner selection.

        Returns:
            Path depth for deterministic deepest-owner selection.

        """
        return len(path.parts)

    @staticmethod
    def _validate_finding_receipt(
        stderr: m.Cli.AtomicFileReceipt, errors: int
    ) -> p.Result[bool]:
        """Authenticate ast-grep's exact error-finding stderr receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected = (
            "\n".join((
                c.Infra.AST_GREP_ERROR_FINDING_RECEIPT.format(count=errors),
                c.Infra.AST_GREP_ERROR_FINDING_HELP,
            ))
            + "\n\n"
        ).encode(c.DEFAULT_ENCODING)
        if stderr.size is None:
            return r[bool].fail(
                f"ast-grep finding receipt has no authenticated size: {stderr.path}"
            )
        with u.Cli.atomic_binary_file_reader(stderr) as reader:
            actual = reader.read_range(0, stderr.size)
            if actual != expected:
                return r[bool].fail(
                    f"ast-grep finding receipt mismatch: parsed_errors={errors} "
                    f"expected={expected!r} actual_bytes={actual!r} "
                    f"actual={stderr.path} "
                    f"size={stderr.size} sha256={stderr.sha256}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _admitted(
        root: Path,
        report: m.Infra.ModScanReport,
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
        project_rule_ids: t.MappingKV[Path, t.StrSequence],
        candidate_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> m.Infra.ModScanReport:
        """Evaluate each source against its nearest governed project's plan.

        Returns:
            Findings admitted by their own project's rules and semantic context.

        """
        elected = {
            project: frozenset(rule_ids)
            for project, rule_ids in project_rule_ids.items()
        }
        projects = sorted(
            elected, key=FlextInfraModGateEngine._path_depth, reverse=True
        )
        grouped: t.MutableMappingKV[Path, list[m.Infra.ModScanFinding]] = {}
        owners: t.MutableMappingKV[Path, t.Pair[Path, Path]] = {}
        for entry in report.entries:
            if entry.file not in owners:
                source = (
                    entry.source_state.path
                    if entry.source_state is not None
                    else u.Infra.codemod_source_path(root, entry.file)
                )
                owners[entry.file] = (
                    source,
                    next(
                        project
                        for project in projects
                        if source.is_relative_to(project)
                    ),
                )
            source, owner = owners[entry.file]
            if entry.rule_id in elected[owner]:
                grouped.setdefault(owner, []).append(
                    entry.model_copy(
                        update={
                            "file": source,
                            "catalog_digest": rules_by_id[entry.rule_id].digest,
                            "module_absence": rules_by_id[entry.rule_id].module_absence,
                        }
                    )
                )
        facts: t.MutableMappingKV[Path, m.Infra.CodemodProjectFacts] = {}
        inputs: list[m.Cli.AtomicFileState] = []
        selections: list[m.Infra.CodemodBindingProject] = []
        for project, entries in grouped.items():
            facts[project] = u.Infra.codemod_project_facts(
                project,
                tuple(
                    rules_by_id[rule_id]
                    for rule_id in dict.fromkeys(entry.rule_id for entry in entries)
                ),
            )
            selected = m.Infra.CodemodBindingSnapshot(
                states=tuple(
                    entry.source_state
                    for entry in entries
                    if entry.rule_id in facts[project].binding_rule_ids
                    and entry.source_state is not None
                )
            )
            inputs.extend(selected.states)
            if selected.states:
                selections.append(
                    m.Infra.CodemodBindingProject(
                        root=project,
                        source_paths=tuple(state.path for state in selected.states),
                        modules=facts[project].binding_modules,
                    )
                )
        sys.stderr.write(
            f"mod: capture bindings projects={len(selections)} sources={len(inputs)}\n"
        )
        sys.stderr.flush()
        for selection in selections:
            sys.stderr.write(
                f"mod: capture project={selection.root.name} "
                f"owners={','.join(selection.modules)}\n"
            )
        sys.stderr.flush()
        snapshot = u.Infra.codemod_binding_snapshot(
            root,
            candidate_states or tuple(inputs),
            projects=tuple(selections),
        )
        sys.stderr.write(
            f"mod: capture bindings completed inputs={len(snapshot.states)}\n"
        )
        sys.stderr.flush()
        admitted: list[m.Infra.ModScanFinding] = []
        epoch = u.Infra.codemod_source_epoch(snapshot)
        with u.Infra.mod_native_readers(report.native_artifacts) as readers:
            for project, entries in grouped.items():
                selected = FlextInfraModGateEngine._admitted_project(
                    project,
                    FlextInfraModGateEngine.recounted(tuple(entries)),
                    rules_by_id,
                    (facts[project], epoch),
                    readers,
                )
                admitted.extend(
                    entry.model_copy(
                        update={"file": entry.file.relative_to(root.resolve())}
                    )
                    for entry in selected.entries
                )
        return FlextInfraModGateEngine.recounted(
            tuple(admitted),
            source_states=report.source_states,
            native_artifacts=report.native_artifacts,
        )

    @staticmethod
    def _admitted_project(
        root: Path,
        report: m.Infra.ModScanReport,
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
        context: t.Pair[m.Infra.CodemodProjectFacts, m.Infra.CodemodSourceEpoch],
        readers: t.MappingKV[Path, p.Cli.AtomicFileReader],
    ) -> m.Infra.ModScanReport:
        """Keep the findings whose rule's project context holds, recounted.

        A rule's ``metadata.context`` binds captured metavariables to project
        predicates ast-grep cannot see (standard library, own package, runtime
        closure, the file's declared facade family); the syntactic match is a
        finding only when every condition holds.

        Returns:
            The resulting ``m.Infra.ModScanReport``.

        """
        facts, epoch = context
        sys.stderr.write(
            f"mod: admit repository={root.name} findings={report.findings}\n"
        )
        sys.stderr.flush()
        snapshot = epoch.snapshot
        with u.Infra.codemod_binding_project(root, epoch) as (project, sources):
            entries = tuple(
                entry.model_copy(update={"binding_states": snapshot.states})
                if entry.rule_id in facts.binding_rule_ids
                else entry
                for entry in report.entries
                if u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=root,
                        rule=rules_by_id[entry.rule_id],
                        file_path=entry.file,
                        captures=FlextInfraModGateEngine._captures(
                            u.Infra.mod_native_payload(entry, readers)
                        ),
                        facts=facts,
                        snapshot=snapshot,
                    ),
                    project=project,
                    sources=sources,
                )
            )
        FlextInfraModGateEngine._progress(
            f"admission finish accepted={len(entries)}/{len(report.entries)}",
        )
        admitted = tuple(entries)
        if admitted == report.entries:
            return report
        return FlextInfraModGateEngine.recounted(
            entries,
            source_states=report.source_states,
            native_artifacts=report.native_artifacts,
        )

    @staticmethod
    def _report_evidence(receipt: m.Infra.ModScanEvidenceReceipt) -> None:
        """Print bounded totals and the authenticated full-evidence identity."""
        evidence = receipt.evidence
        sys.stderr.write(f"mod: findings total={evidence.findings}\n")
        for finding_class, count in evidence.totals_by_class.items():
            sys.stderr.write(
                f"mod: findings class={finding_class.value} count={count}\n",
            )
        for repository, count in evidence.totals_by_repository.items():
            sys.stderr.write(f"mod: findings repository={repository} count={count}\n")
        for rule_id, count in evidence.totals_by_rule.items():
            sys.stderr.write(f"mod: findings rule={rule_id} count={count}\n")
        sys.stderr.write(
            f"mod: findings report={receipt.path} sha256={receipt.sha256}\n",
        )
        sys.stderr.flush()

    @classmethod
    def _ruleset_report(
        cls,
        root: Path,
        ruleset: m.Infra.CodemodRuleset,
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
        selection: t.Pair[t.StrSequence, m.Infra.ModScanSourceContext],
        *,
        artifact_root: Path,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Collect one provider's complete native findings before shared admission.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        targets, context = selection
        ruleset_files = {
            rule_id: rules_by_id[rule_id].resource for rule_id in ruleset.rule_ids
        }
        scan_command = u.Infra.ast_grep_scan_command(
            ruleset.config,
            rule_ids=ruleset.rule_ids,
            targets=targets,
            json_stream=True,
        )
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="mod-native-", dir=settings.work_dir
        ) as directory:
            stdout_file, stderr_file = (
                Path(directory) / "stdout",
                Path(directory) / "stderr",
            )
            run = cls._run_tool(
                root,
                scan_command,
                streams=(stdout_file, stderr_file),
                artifact_root=artifact_root,
                finding_exit_code=1,
            )
            if run.failure:
                return r[m.Infra.ModScanReport].from_failure(run)
            sys.stderr.write(f"mod: parse native JSONL file={stdout_file}\n")
            sys.stderr.flush()
            artifact = u.Infra.publish_mod_native_artifact(artifact_root, stdout_file)
            report = cls._parse_findings(
                artifact.path,
                root,
                (ruleset_files, frozenset(ruleset.fixable_rule_ids)),
                context,
                artifact,
            ).unwrap()
            sys.stderr.write(f"mod: native findings={report.findings}\n")
            sys.stderr.flush()
            stderr = u.Infra.publish_mod_native_artifact(artifact_root, stderr_file)
            if run.value.raw_return_code != 0:
                error_findings = sum(
                    entry.severity == "error" for entry in report.entries
                )
                if not error_findings:
                    return r[m.Infra.ModScanReport].fail(
                        "ast-grep finding exit has no error-severity occurrence"
                    )
                cls._validate_finding_receipt(stderr, error_findings).unwrap()
            report = cls.recounted(
                report.entries,
                source_states=report.source_states,
                native_artifacts=tuple(
                    {
                        receipt.path: receipt
                        for receipt in (*report.native_artifacts, stderr)
                    }.values()
                ),
            )
        return r[m.Infra.ModScanReport].ok(report)

    @staticmethod
    def _scan_source_paths(root: Path, targets: t.StrSequence) -> frozenset[Path]:
        """Enumerate the native selection through its canonical Python file owner.

        Args:
            root: The root directory of the project being scanned.
            targets: The sequence of target paths to enumerate.

        Returns:
            A frozenset of resolved Python file paths within the target directories.

        """
        return frozenset(
            path.resolve()
            for target in targets
            for path in (
                u.Infra.iter_directory_python_files(root / target)
                if (root / target).is_dir()
                else (root / target,)
            )
        )

    @staticmethod
    def _catalog_paths(
        root: Path,
        plan: m.Infra.CodemodRulePlan,
    ) -> tuple[Path, ...]:
        """Name the elected catalog and configuration inputs without scanning code.

        Returns:
            Canonical rule resources, configuration layers and project declarations.

        """
        paths = {rule.resource.resolve() for rule in plan.rules}
        paths.update(FlextInfraConfig.ssot_config_dir().glob("*.yaml"))
        for ruleset in plan.rulesets:
            paths.add(ruleset.config.resolve())
            directories = FlextInfraCodemodSnapshotReconciler.scanner_directories(
                ruleset.config.parent
            )
            for directory in (*directories.rule_dirs, *directories.util_dirs):
                paths.update(
                    path.resolve() for path in directory.rglob("*") if path.is_file()
                )
        for project in plan.project_rule_ids:
            paths.add(project / c.PYPROJECT_FILENAME)
            paths.add(project / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME)
            paths.update(
                state.path
                for state in u.Infra.load_codegen_inputs(project).unwrap().sources
            )
        paths.add(root / c.Infra.GITMODULES)
        return tuple(sorted(paths))

    @classmethod
    def _verify_scan_membership(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
        _candidate_root: Path,
    ) -> p.Result[bool]:
        """Verify the original selection and catalog before or after owned effects.

        Returns:
            Current membership and catalog proof, without requiring old output bytes.

        """
        plan = report.rule_plan
        if (
            report.repository_root != root.resolve()
            or report.source_states is None
            or report.catalog_states is None
            or plan is None
        ):
            return r[bool].fail("native scan report lacks authenticated inputs")
        targets = u.Infra.ast_grep_scan_targets(root, source_files=report.source_files)
        if cls._scan_source_paths(root, targets) != frozenset(
            state.path for state in report.source_states
        ):
            return r[bool].fail("native scan source membership changed")
        current: t.MutableMappingKV[t.Pair[str, str], m.Infra.CodemodRule] = {}
        for ruleset in plan.rulesets:
            catalog = u.Infra.codemod_catalog_rules(ruleset.provider, ruleset.config)
            if catalog.failure:
                return r[bool].from_failure(catalog)
            for rule in catalog.value:
                if rule.id not in ruleset.rule_ids:
                    continue
                key = (rule.provider, rule.id)
                if key in current and current[key] != rule:
                    return r[bool].fail("native scan catalog membership changed")
                current[key] = rule
        if (
            len(current) != len(plan.rules)
            or any(current.get((rule.provider, rule.id)) != rule for rule in plan.rules)
            or cls._catalog_paths(root, plan)
            != tuple(state.path for state in report.catalog_states)
        ):
            return r[bool].fail("native scan catalog membership changed")
        return u.Cli.atomic_verify_binary_file_states(report.catalog_states)

    @classmethod
    def _verify_scan_inputs(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Authenticate exact original scan and binding bytes before publication.

        Returns:
            The first input failure or the complete current report proof.

        """
        membership = cls._verify_scan_membership(root, report, root)
        if membership.failure:
            return membership
        if report.source_states is None:
            return r[bool].fail("native scan report lacks authenticated source inputs")
        verified = u.Cli.atomic_verify_binary_file_states((
            *report.source_states,
            *(state for entry in report.entries for state in entry.binding_states),
        ))
        if verified.failure:
            return verified
        with u.Infra.mod_native_readers(report.native_artifacts) as readers:
            for entry in report.entries:
                u.Infra.mod_native_payload(entry, readers)
        return r[bool].ok(value=True)

    @classmethod
    def apply_report(
        cls,
        root: Path,
        report: m.Infra.ModOccurrenceReport[m.Infra.ModScanFinding],
        *,
        exact_replacements: bool = False,
        published_plans: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
    ) -> p.Result[bool]:
        """Publish the admitted native report only under its original input CAS.

        Returns:
            Real publication acceptance or the first stale-input failure.

        """
        if not isinstance(report, m.Infra.ModScanReport):
            return r[bool].fail(
                "publication requires an authenticated native scan report"
            )
        verified = cls._verify_scan_inputs(root, report)
        if verified.failure:
            return verified
        return FlextInfraModReplacements.publish(
            root,
            cls.authored(report),
            exact_replacements=exact_replacements,
            published_plans=published_plans,
            verification=(
                partial(cls._verify_scan_inputs, root, report),
                partial(cls._verify_scan_membership, root, report),
            ),
        )

    @classmethod
    def _native_scan_report(
        cls,
        root: Path,
        plan: m.Infra.CodemodRulePlan,
        targets: t.StrSequence,
        context: m.Infra.ModScanSourceContext,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Combine every elected provider's complete ordered native occurrences.

        Args:
            root: The root directory of the project being scanned.
            plan: The codemod rule plan containing rules and rulesets.
            targets: The sequence of target paths to scan.
            context: The source context for the scan.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        rules_by_id = {rule.id: rule for rule in plan.rules}
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="mod-native-catalog-", dir=settings.work_dir
        ) as directory:
            ruleset = u.Infra.codemod_stage_scan_ruleset(plan, Path(directory))
            sys.stderr.write(
                f"mod: ast-grep provider={ruleset.provider} "
                f"rules={len(ruleset.rule_ids)}\n",
            )
            sys.stderr.flush()
            return cls._ruleset_report(
                root, ruleset, rules_by_id, (targets, context), artifact_root=root
            )

    @classmethod
    def _publish_scan(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
        publication: m.Infra.ModScanPublication,
        *,
        exact_replacements: bool,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Publish full evidence before any authorized source replacement.

        Args:
            root: The root directory of the project being scanned.
            report: The complete scan report containing all findings.
            publication: The publication context for the scan.
            exact_replacements: Whether to apply only exact replacements.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        sys.stderr.write(f"mod: publish evidence findings={report.findings}\n")
        sys.stderr.flush()
        receipt = u.Infra.publish_mod_scan_evidence(
            root, report, publication=publication
        )
        if receipt.failure:
            return r[m.Infra.ModScanReport].from_failure(receipt)
        cls._report_evidence(receipt.value)
        if publication.command is c.Infra.ModScanCommand.APPLY:
            published = cls.apply_report(
                root,
                report,
                exact_replacements=exact_replacements,
            )
            if published.failure:
                return r[m.Infra.ModScanReport].from_failure(published)
        return r[m.Infra.ModScanReport].ok(report)

    @classmethod
    def scan(
        cls,
        root: Path,
        *,
        fix: bool,
        rule_ids: t.StrSequence | None = None,
        plan: m.Infra.CodemodRulePlan | None = None,
        source_files: t.SequenceOf[Path] | None = None,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply every ruleset elected by the composed rule-plan SSOT.

        Complete evidence retains generated findings; only the authored projection
        reaches publication, without granting permission to rewrite generated bytes.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        if plan is None:
            planned = u.Infra.codemod_rule_plan(root, rule_ids=rule_ids)
            if planned.failure:
                return r[m.Infra.ModScanReport].from_failure(planned)
            plan = planned.value
        elif rule_ids is not None or root.resolve() not in plan.project_rule_ids:
            return r[m.Infra.ModScanReport].fail(
                "precomposed scan plan requires its governed root and owns rule "
                "selection"
            )
        rules_by_id = {rule.id: rule for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root, source_files=source_files)
        source_states = {
            path: u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in sorted(cls._scan_source_paths(root, targets))
        }
        context = m.Infra.ModScanSourceContext(
            source_states=source_states,
            repository_roots=tuple(
                sorted(plan.project_rule_ids, key=cls._path_depth, reverse=True)
            ),
        )
        catalog_states = tuple(
            u.Cli.atomic_read_binary_file_state(path).unwrap()
            for path in cls._catalog_paths(root.resolve(), plan)
        )
        sys.stderr.write(
            f"mod: ast-grep {'apply' if fix else 'scan'} "
            f"providers={len(plan.rulesets)} rules={len(plan.rules)}\n",
        )
        sys.stderr.flush()
        scanned = cls._native_scan_report(root, plan, targets, context)
        if scanned.failure:
            return r[m.Infra.ModScanReport].from_failure(scanned)
        complete_report = cls._admitted(
            root,
            scanned.value,
            rules_by_id,
            plan.project_rule_ids,
        )
        complete_report = complete_report.model_copy(
            update={
                "repository_root": root.resolve(),
                "source_files": (
                    tuple(path.resolve() for path in source_files)
                    if source_files is not None
                    else None
                ),
                "rule_plan": plan,
                "catalog_states": catalog_states,
            }
        )
        current = cls._verify_scan_inputs(root, complete_report)
        if current.failure:
            return r[m.Infra.ModScanReport].from_failure(current)
        declared = cls._validate_expected_receipts(plan.rules, complete_report)
        if declared.failure:
            return r[m.Infra.ModScanReport].from_failure(declared)
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
            exact_replacements=rule_ids is not None,
        )

    @classmethod
    def scan_candidate(
        cls,
        root: Path,
        view_root: Path,
        candidate: m.Infra.StageSourcePlan,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan an immutable overlay with the original catalog and logical policy.

        Returns:
            Full-catalog findings authenticated to candidate bytes and bindings.

        """
        plan = u.Infra.codemod_rule_plan(root).unwrap()
        rules_by_id = {rule.id: rule for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root)
        states = tuple(
            state.model_copy(
                update={
                    "content": candidate.updates[state.path].encode(c.DEFAULT_ENCODING)
                    if state.path in candidate.updates
                    else state.content,
                }
            )
            for state in candidate.inputs
        )
        source_states = tuple(
            state
            for state in states
            if state.content is not None
            and state.path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
        )
        physical = {
            view_root
            / state.path.relative_to(
                root.resolve()
            ): u.Cli.atomic_read_binary_file_state(
                view_root / state.path.relative_to(root.resolve()), required=True
            ).unwrap()
            for state in source_states
        }
        context = m.Infra.ModScanSourceContext(
            source_states=physical,
            repository_roots=tuple(
                sorted(
                    u.Infra.governed_project_roots(view_root),
                    key=cls._path_depth,
                    reverse=True,
                )
            ),
        )
        logical = {state.path: state for state in states}
        entries: list[m.Infra.ModScanFinding] = []
        artifacts: t.MutableMappingKV[Path, m.Cli.AtomicFileReceipt] = {}
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="mod-native-catalog-", dir=settings.work_dir
        ) as directory:
            ruleset = u.Infra.codemod_stage_scan_ruleset(plan, Path(directory))
            scanned = cls._ruleset_report(
                view_root, ruleset, rules_by_id, (targets, context), artifact_root=root
            )
            if scanned.failure:
                return r[m.Infra.ModScanReport].from_failure(scanned)
            artifacts.update(
                (artifact.path, artifact) for artifact in scanned.value.native_artifacts
            )
            for entry in scanned.value.entries:
                relative = (
                    entry.file.relative_to(view_root)
                    if entry.file.is_absolute()
                    else entry.file
                )
                entries.append(
                    entry.model_copy(
                        update={
                            "file": relative,
                            "source_state": logical[(root / relative).resolve()],
                        }
                    )
                )
        report = cls._admitted(
            root,
            cls.recounted(
                tuple(entries),
                source_states=source_states,
                native_artifacts=tuple(artifacts.values()),
            ),
            rules_by_id,
            plan.project_rule_ids,
            source_states,
        )
        declared = cls._validate_expected_receipts(plan.rules, report)
        if declared.failure:
            return r[m.Infra.ModScanReport].from_failure(declared)
        return r[m.Infra.ModScanReport].ok(report)


__all__: list[str] = ["FlextInfraModGateEngine"]
