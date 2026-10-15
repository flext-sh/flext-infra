"""Gate measurement and ast-grep batch execution for the mod safety circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import stat
import sys
import tempfile
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from time import monotonic

import flext_cli

from flext_infra import c, config, m, p, r, settings, t, u
from flext_infra.codemod import (
    FlextInfraCodemodSnapshotReconciler,
    FlextInfraModReplacements,
)


class FlextInfraModGateEngine:
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

    @classmethod
    def validate_rule_fixtures(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Verify every fixture against its committed snapshots; never rewrite them.

        A drifted or missing snapshot fails ``ast-grep test``; a snapshot of a
        removed rule or deleted test case fails the owned-inventory check. The
        change they record is made explicit by ``make mod-snapshots`` and lands
        as a reviewed commit, so ``make mod`` cannot accept rewritten output.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for config_root, owner_rules, owner_is_governed in cls._fixture_owners(
            root,
            rules,
        ):
            if owner_is_governed:
                active_rule_ids: set[str] = set()
                for rule in owner_rules:
                    rule_ids, _fixable_ids = u.Infra.ast_grep_rule_contract(rule)
                    active_rule_ids.update(rule_ids)
                stale = FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                    config_root,
                    frozenset(active_rule_ids),
                )
                if stale:
                    return r[bool].fail(
                        "ast-grep snapshots record no current rule test:\n"
                        + "\n".join(stale)
                        + f"\n{c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT}",
                    )
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-fixtures-",
                dir=settings.work_dir,
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                )
                cls._materialize_split_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                tested = cls._run_tool(
                    temp_root,
                    (
                        c.Infra.SG,
                        c.Infra.TEST,
                        c.Infra.SG_CONFIG_FLAG,
                        str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                    ),
                )
                if tested.failure:
                    remedy = (
                        c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT
                        if owner_is_governed
                        else (
                            f"inherited rule provider {config_root} ships these "
                            "fixtures; repair them in its owner repository"
                        )
                    )
                    return r[bool].fail(f"{tested.error}\n{remedy}")
        return r.ok(value=True)

    @classmethod
    def refresh_rule_snapshots(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
        *,
        apply: bool,
    ) -> p.Result[t.StrSequence]:
        """Regenerate every governed owner's snapshots from its rule tests.

        The explicit counterpart of the verifying ``validate_rule_fixtures``:
        snapshots are projections of the declared test cases, rebuilt from
        scratch so removed rules and deleted cases leave no residue. The
        returned changes are the reviewed diff; inherited providers keep the
        snapshots their owner ships.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        changes: list[str] = []
        for config_root, owner_rules, owner_is_governed in cls._fixture_owners(
            root,
            rules,
        ):
            if not owner_is_governed:
                continue
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-snapshots-",
                dir=settings.work_dir,
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                    regenerate_snapshots=True,
                )
                cls._materialize_split_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                cls._run_tool(
                    temp_root,
                    (
                        c.Infra.SG,
                        c.Infra.TEST,
                        c.Infra.SG_UPDATE_ALL,
                        c.Infra.SG_CONFIG_FLAG,
                        str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                    ),
                ).unwrap()
                cls._run_tool(
                    temp_root,
                    (
                        c.Infra.SG,
                        c.Infra.TEST,
                        c.Infra.SG_CONFIG_FLAG,
                        str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                    ),
                ).unwrap()
                changes.extend(
                    cls._publish_regenerated_snapshots(
                        config_root=config_root,
                        temp_root=temp_root,
                        apply=apply,
                    ),
                )
        return r[t.StrSequence].ok(tuple(changes))

    @staticmethod
    def _governs(governed_root: Path, config_root: Path) -> bool:
        """Whether the governed repository itself tracks this rule provider.

        Git owns the answer for each declared first-party repository. Installed
        providers remain read-only; a workspace can refresh the catalogs its
        declared member repositories track.

        Returns:
            The resulting ``bool``.

        """
        provider = (config_root / c.Infra.CODEMOD_CONFIG_FILENAME).resolve()
        for owner in sorted(
            u.Infra.governed_project_roots(governed_root),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if provider.is_relative_to(owner):
                return (
                    u.Infra
                    .git_is_tracked(
                        m.Infra.GitRelativePathRequest(
                            repo_root=owner,
                            relative_path=provider.relative_to(owner).as_posix(),
                        ),
                    )
                    .unwrap()
                    .value
                )
        return False

    @classmethod
    def _fixture_owners(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
    ) -> t.SequenceOf[t.Triple[Path, t.SequenceOf[Path], bool]]:
        """Group rules by fixture owner and mark the owners this root governs.

        Returns:
            The resulting ``t.SequenceOf[t.Triple[Path, t.SequenceOf[Path], bool]]``.

        Raises:
            ValueError: If discovered ast-grep rules have no fixture owner; or if rule
                fixture scratch must be outside its source root.

        """
        governed_roots = tuple(
            project.resolve() for project in u.Infra.governed_project_roots(root)
        )
        rules_by_owner: MutableMapping[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        if not rules_by_owner:
            msg = "discovered ast-grep rules have no fixture owner"
            raise ValueError(msg)
        scratch = settings.work_dir
        owners: list[t.Triple[Path, t.SequenceOf[Path], bool]] = []
        for config_root, owner_rules in sorted(rules_by_owner.items()):
            if scratch.resolve().is_relative_to(config_root.resolve()):
                msg = "rule fixture scratch must be outside its source root"
                raise ValueError(msg)
            owners.append((
                config_root,
                tuple(owner_rules),
                any(
                    cls._governs(governed_root, config_root)
                    for governed_root in governed_roots
                ),
            ))
        scratch.mkdir(parents=True, exist_ok=True)
        return tuple(owners)

    @staticmethod
    def stage_rule_fixture_root(
        *,
        config_root: Path,
        temp_root: Path,
        regenerate_snapshots: bool = False,
    ) -> None:
        """Copy declared ast-grep inputs only, rejecting links and special files.

        Raises:
            ValueError: If ast-grep fixture must be a regular file or directory.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        snapshot_roots = {
            directory / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            for directory in directories.test_dirs
        }
        pending = [config_root / c.Infra.CODEMOD_CONFIG_FILENAME]
        pending.extend((
            *directories.rule_dirs,
            *directories.util_dirs,
            *directories.test_dirs,
        ))
        files: set[Path] = set()
        folders: set[Path] = set()
        while pending:
            path = pending.pop()
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                if path in folders:
                    continue
                folders.add(path)
                pending.extend(path.iterdir())
            elif stat.S_ISREG(mode):
                files.add(path)
            else:
                msg = f"ast-grep fixture must be a regular file or directory: {path}"
                raise ValueError(msg)
        temp_root.mkdir()
        for directory in sorted(folders):
            (temp_root / directory.relative_to(config_root)).mkdir(
                parents=True,
                exist_ok=True,
            )
        for source in sorted(files):
            if (
                regenerate_snapshots
                and source.parent in snapshot_roots
                and source.name.endswith(c.Infra.CODEMOD_SNAPSHOT_SUFFIX)
            ):
                # Owned projections are regenerated from all declared test cases.
                # Foreign providers retain their snapshots for verification.
                continue
            shutil.copy2(
                source,
                temp_root / source.relative_to(config_root),
                follow_symlinks=False,
            )

    @classmethod
    def _materialize_split_rule_files(
        cls,
        *,
        config_root: Path,
        temp_root: Path,
        owner_rules: t.SequenceOf[Path],
    ) -> None:
        """Replace multi-document rule files with single-document temp copies.

        Raises:
            RuntimeError: If ``parsed.failure``; or if ast-grep rule document missing
                required id.

        """
        source_rules = set(owner_rules)
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        for directory in (*directories.rule_dirs, *directories.util_dirs):
            source_rules.update(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}"))
        for rule in sorted(source_rules):
            documents = u.Cli.yaml_parse_documents(
                u.Cli.files_read_text(rule).unwrap()
            ).unwrap()
            if len(documents) <= 1:
                continue
            temp_rule = temp_root / rule.relative_to(config_root)
            temp_rule.unlink()
            for document in documents:
                rule_id = document.get(c.Infra.CODEMOD_RULE_TEST_ID_KEY)
                if not isinstance(rule_id, str) or not rule_id:
                    msg = f"ast-grep rule document missing required id: {rule}"
                    raise RuntimeError(msg)
                u.Cli.yaml_dump(
                    temp_rule.with_name(f"{rule_id}{c.Infra.CODEMOD_RULE_SUFFIX}"),
                    document,
                ).unwrap()

    @staticmethod
    def _publish_regenerated_snapshots(
        *,
        config_root: Path,
        temp_root: Path,
        apply: bool,
    ) -> t.StrSequence:
        """Mirror only regenerated snapshot files back to source; report each change.

        Rules, utilities and tests are inputs of the regeneration and are never
        written back. A committed snapshot the regeneration did not produce
        belongs to a removed rule or test and is removed with the rest.

        Returns:
            The resulting ``t.StrSequence``.

        """
        pattern = f"*{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
        changes: list[str] = []
        for test_dir in FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        ).test_dirs:
            source_dir = test_dir / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            regenerated_dir = temp_root / source_dir.relative_to(config_root)
            regenerated = {path.name: path for path in regenerated_dir.glob(pattern)}
            committed = {path.name: path for path in source_dir.glob(pattern)}
            for name in sorted(regenerated.keys() | committed.keys()):
                target = source_dir / name
                produced = regenerated.get(name)
                if produced is None:
                    changes.append(f"removed {target}")
                    if apply:
                        target.unlink()
                    continue
                content = produced.read_text(encoding=c.DEFAULT_ENCODING)
                current = committed.get(name)
                if current is not None and (
                    current.read_text(encoding=c.DEFAULT_ENCODING) == content
                ):
                    continue
                changes.append(
                    f"{'created' if current is None else 'updated'} {target}",
                )
                if apply:
                    u.Cli.atomic_write_text_file(target, content).unwrap()
        return tuple(changes)

    @staticmethod
    def _run_tool(
        root: Path,
        command: t.StrSequence,
        *,
        finding_exit_code: int | None = None,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run one AST tool and preserve its documented finding status.

        Resolve and authenticate in Make's declared tool-owning invocation
        context first. Execute the absolute managed binary in the consumer
        directory, so neither a shim nor that directory can select another tool.

        Returns:
            The resulting ``p.Result[p.Cli.CommandOutput]``.

        """
        # Make owns the invocation context; root is only the scanned consumer.
        binary = u.Infra.managed_mise_binary(command[0], Path.cwd())
        if binary.failure:
            return r[p.Cli.CommandOutput].from_failure(binary)
        sys.stderr.write(
            f"mod: start {' '.join(command[:2])} args={max(0, len(command) - 2)}\n",
        )
        sys.stderr.flush()
        run = u.Cli.run_raw(
            (str(binary.value), *command[1:]),
            cwd=root,
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if run.failure:
            return r[p.Cli.CommandOutput].from_failure(run)
        output = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={output.outcome.raw_return_code} "
            f"duration={output.duration:.2f}s\n",
        )
        sys.stderr.flush()
        if output.outcome.raw_return_code != 0:
            if (
                output.outcome.raw_return_code == finding_exit_code
                and output.stdout.strip()
            ):
                return r[p.Cli.CommandOutput].ok(output)
            detail = "\n".join(
                stream.strip()
                for stream in (output.stdout, output.stderr)
                if stream.strip()
            )
            return r[p.Cli.CommandOutput].fail(
                f"{command[0]} exited with code "
                f"{output.outcome.raw_return_code}: {detail}",
            )
        stderr = output.stderr.strip()
        if stderr:
            return r[p.Cli.CommandOutput].fail(stderr)
        return r[p.Cli.CommandOutput].ok(output)

    @staticmethod
    def _path_depth(path: Path) -> int:
        """Return path depth for deterministic deepest-owner selection.

        Returns:
            Path depth for deterministic deepest-owner selection.

        """
        return len(path.parts)

    @staticmethod
    def _validate_finding_receipt(stderr: str, errors: int) -> p.Result[bool]:
        """Authenticate ast-grep's exact error-finding stderr receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected = "\n".join((
            c.Infra.AST_GREP_ERROR_FINDING_RECEIPT.format(count=errors),
            c.Infra.AST_GREP_ERROR_FINDING_HELP,
        ))
        receipt = stderr.strip()
        if receipt != expected:
            return r[bool].fail(
                f"ast-grep finding receipt mismatch: parsed_errors={errors} "
                f"expected={expected!r} actual={receipt!r}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _admitted(
        root: Path,
        report: m.Infra.ModScanReport,
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
    ) -> m.Infra.ModScanReport:
        """Keep the findings whose rule's project context holds, recounted.

        A rule's ``metadata.context`` binds captured metavariables to project
        predicates ast-grep cannot see (standard library, own package, runtime
        closure, the file's declared facade family); the syntactic match is a
        finding only when every condition holds.

        Returns:
            The resulting ``m.Infra.ModScanReport``.

        """
        matched_rules = tuple(
            rules_by_id[rule_id]
            for rule_id in dict.fromkeys(entry.rule_id for entry in report.entries)
        )
        FlextInfraModGateEngine._progress(
            f"facts start rules={len(matched_rules)} findings={len(report.entries)}",
        )
        facts = u.Infra.codemod_project_facts(root, matched_rules)
        FlextInfraModGateEngine._progress(
            f"facts finish predicates={len(facts.predicates)}",
        )
        occurrence_rules = tuple(
            rule
            for rule in matched_rules
            if any(
                condition.predicate
                in {
                    c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                    c.Infra.CodemodContextPredicate.SAME_BINDING,
                    c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
                    c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
                }
                for condition in rule.context
            )
        )
        selected_ids = {rule.id for rule in occurrence_rules}
        states = tuple(
            entry.source_state
            for entry in report.entries
            if entry.rule_id in selected_ids and entry.source_state is not None
        )
        FlextInfraModGateEngine._progress(
            f"binding admissions start findings={len(report.entries)} "
            f"rules={len(selected_ids)}",
        )
        admissions: list[m.Infra.CodemodAdmission] = []
        due = 0.0
        for index, entry in enumerate(report.entries, start=1):
            if entry.rule_id not in selected_ids:
                continue
            due = FlextInfraModGateEngine._progress(
                f"binding admissions finding={index}/{len(report.entries)} "
                f"file={entry.file} rule={entry.rule_id}",
                due,
            )
            admissions.append(
                m.Infra.CodemodAdmission(
                    root=root,
                    rule=rules_by_id[entry.rule_id],
                    file_path=entry.file,
                    captures=FlextInfraModGateEngine._captures(entry.payload),
                    facts=facts,
                ),
            )
        FlextInfraModGateEngine._progress(
            f"binding admissions finish admissions={len(admissions)}",
        )
        snapshot = (
            u.Infra.codemod_binding_snapshot(
                root,
                states,
                tuple(
                    condition.arg[0]
                    for rule in occurrence_rules
                    for condition in rule.context
                    if condition.predicate
                    is c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL
                ),
                admissions=tuple(admissions),
            )
            if states
            else None
        )
        closed = snapshot or m.Infra.CodemodBindingSnapshot(states=())
        FlextInfraModGateEngine._progress(
            f"admission start findings={len(report.entries)} "
            f"binding_sources={len(closed.states)}",
        )
        entries: list[m.Infra.ModScanFinding] = []
        with u.Infra.codemod_binding_project(root, closed) as (project, sources):
            due = 0.0
            for index, entry in enumerate(report.entries, start=1):
                due = FlextInfraModGateEngine._progress(
                    f"admission finding={index}/{len(report.entries)} "
                    f"file={entry.file} rule={entry.rule_id} "
                    f"accepted={len(entries)}",
                    due,
                )
                if u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=root,
                        rule=rules_by_id[entry.rule_id],
                        file_path=entry.file,
                        captures=FlextInfraModGateEngine._captures(entry.payload),
                        facts=facts,
                        snapshot=snapshot,
                    ),
                    project=project,
                    sources=sources,
                ):
                    entries.append(
                        entry.model_copy(update={"binding_states": snapshot.states})
                        if snapshot is not None and entry.rule_id in selected_ids
                        else entry,
                    )
        FlextInfraModGateEngine._progress(
            f"admission finish accepted={len(entries)}/{len(report.entries)}",
        )
        admitted = tuple(entries)
        if admitted == report.entries:
            return report
        return FlextInfraModGateEngine.recounted(
            admitted,
            scan_inputs=report.scan_inputs,
        )

    @staticmethod
    def recounted(
        entries: t.VariadicTuple[m.Infra.ModScanFinding],
        *,
        scan_inputs: m.Infra.ModScanInputs | None = None,
    ) -> m.Infra.ModScanReport:
        """Return the scan report of exactly these findings, classes recounted.

        Returns:
            The scan report of exactly these findings, classes recounted.

        """
        classes = [entry.classification for entry in entries]
        return m.Infra.ModScanReport(
            findings=len(entries),
            actionable=classes.count(c.Infra.ModScanFindingClass.ACTIONABLE),
            detection_only=classes.count(c.Infra.ModScanFindingClass.DETECTION_ONLY),
            non_actionable_with_fix=classes.count(
                c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX,
            ),
            files=frozenset(entry.file for entry in entries),
            entries=entries,
            scan_inputs=scan_inputs,
        )

    @classmethod
    def authored(cls, report: m.Infra.ModScanReport) -> m.Infra.ModScanReport:
        """Return the findings mod may rewrite: a generated source is never one.

        A generator finding stays blocking evidence for its generator; it never
        holds back the rewrites of the authored sources.

        Returns:
            The findings mod may rewrite: a generated source is never one.

        """
        return cls.recounted(
            tuple(
                entry for entry in report.entries if entry.source_owner != "generator"
            ),
            scan_inputs=report.scan_inputs,
        )

    @staticmethod
    def _captures(payload: t.JsonMapping) -> t.JsonMapping:
        """Return one finding's single and transformed metavariables.

        Returns:
            One finding's single and transformed metavariables.

        """
        meta = payload.get("metaVariables")
        captures: t.MutableMappingKV[str, t.JsonValue] = {}
        if isinstance(meta, Mapping):
            for group in ("single", "transformed"):
                values = meta.get(group)
                if isinstance(values, Mapping):
                    captures.update(values)
        return captures

    @staticmethod
    def _validate_expected_receipts(
        rules: t.SequenceOf[m.Infra.CodemodRule],
        report: m.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Require every declared finding-count receipt to match exactly.

        Same contract the sed-by-list phase owns for text rules: a rule that
        declares how many findings it must produce turns silent drift into a
        loud failure. A guard that stops matching, or a pattern that starts
        over-matching after an unrelated edit, is otherwise invisible — the
        cascade simply rewrites more or less than its author proved. Rules
        that declare no receipt are unconstrained.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        counts: MutableMapping[str, int] = {}
        for entry in report.entries:
            counts[entry.rule_id] = counts.get(entry.rule_id, 0) + 1
        for rule in rules:
            if rule.expected is None:
                continue
            observed = counts.get(rule.id, 0)
            if observed != rule.expected:
                return r[bool].fail(
                    f"ast-grep rule {rule.id} declares {rule.expected} "
                    f"finding(s), scan produced {observed}",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _finding_contract_error(
        finding: t.MappingKV[str, t.JsonValue],
        line: str,
        rule_files_by_id: Mapping[str, Path],
    ) -> str | None:
        """Return one JSONL finding's contract violation, or ``None`` when valid.

        Returns:
            The canonical failure message for the first violated contract field.

        """
        rule_id = finding.get("ruleId")
        text = finding.get("text")
        file = finding.get("file")
        source_range = finding.get("range")
        raw_replacement = finding.get("replacement")
        severity = finding.get("severity")
        if not isinstance(rule_id, str) or rule_id not in rule_files_by_id:
            return f"invalid ast-grep finding contract: {line}"
        if not isinstance(text, str) or not isinstance(file, str):
            return f"invalid ast-grep finding contract: {line}"
        if not isinstance(source_range, Mapping):
            return f"invalid ast-grep finding contract: {line}"
        if raw_replacement is not None and not isinstance(raw_replacement, str):
            return f"invalid ast-grep finding contract: {line}"
        if severity not in {"error", "warning", "info", "hint"}:
            return f"invalid ast-grep finding severity: {line}"
        return None

    @staticmethod
    def _authenticated_snapshot(
        root: Path,
        file: str,
        source_states: Mapping[Path, m.Cli.AtomicFileState],
    ) -> p.Result[t.Pair[Path, m.Cli.AtomicFileState]]:
        """Associate a finding with the scan's already authenticated source state.

        Complete input verification brackets parsing and admission; individual
        findings retain the captured bytes without repeating physical reads.

        Returns:
            The resulting ``(file_path, snapshot)`` pair for the unchanged source.

        """
        file_path = Path(file)
        resolved_file = (root / file_path).resolve()
        snapshot = source_states.get(resolved_file)
        if snapshot is None or snapshot.content is None:
            return r[t.Pair[Path, m.Cli.AtomicFileState]].fail(
                f"finding has no authenticated source snapshot: {resolved_file}",
            )
        return r[t.Pair[Path, m.Cli.AtomicFileState]].ok((file_path, snapshot))

    @staticmethod
    def _classified_finding(
        rule_id: str,
        fixable_ids: frozenset[str],
        text: str,
        replacement: str | None,
        line: str,
    ) -> p.Result[t.Pair[bool, c.Infra.ModScanFindingClass]]:
        """Classify one finding against its rule's fix contract.

        Returns:
            The resulting ``(actionable, classification)`` pair.

        """
        outcome = r[t.Pair[bool, c.Infra.ModScanFindingClass]]
        if rule_id not in fixable_ids:
            if replacement is not None:
                return outcome.fail(
                    f"detection-only ast-grep finding has replacement: {line}",
                )
            return outcome.ok((False, c.Infra.ModScanFindingClass.DETECTION_ONLY))
        if not isinstance(replacement, str):
            return outcome.fail(f"fixable ast-grep finding lacks replacement: {line}")
        if text != replacement:
            return outcome.ok((True, c.Infra.ModScanFindingClass.ACTIONABLE))
        return outcome.ok((False, c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX))

    @classmethod
    def _line_finding(
        cls,
        line: str,
        finding: t.MappingKV[str, t.JsonValue],
        root: Path,
        plan: t.Pair[Mapping[str, Path], frozenset[str]],
        states: t.Pair[Mapping[Path, m.Cli.AtomicFileState], t.SequenceOf[Path]],
    ) -> p.Result[m.Infra.ModScanFinding]:
        """Validate one JSONL finding into a typed, authenticated entry.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanFinding]``.

        """
        rule_files_by_id, fixable_ids = plan
        source_states, repository_roots = states
        rule_id = finding.get("ruleId")
        contract_error = cls._finding_contract_error(finding, line, rule_files_by_id)
        if contract_error is not None:
            return r[m.Infra.ModScanFinding].fail(contract_error)
        authenticated = cls._authenticated_snapshot(
            root,
            str(finding.get("file")),
            source_states,
        )
        if authenticated.failure:
            return r[m.Infra.ModScanFinding].from_failure(authenticated)
        file_path, snapshot = authenticated.value
        if snapshot.content is None:
            return r[m.Infra.ModScanFinding].fail(
                f"authenticated snapshot has no content: {file_path}",
            )
        raw_replacement = finding.get("replacement")
        replacement = raw_replacement if isinstance(raw_replacement, str) else None
        classified = cls._classified_finding(
            str(rule_id),
            fixable_ids,
            str(finding.get("text")),
            replacement,
            line,
        )
        if classified.failure:
            return r[m.Infra.ModScanFinding].from_failure(classified)
        actionable, classification = classified.value
        repository = next(
            (
                candidate.name
                for candidate in repository_roots
                if file_path.is_relative_to(candidate)
            ),
            root.resolve().name,
        )
        return r[m.Infra.ModScanFinding].ok(
            m.Infra.ModScanFinding(
                rule_file=str(rule_files_by_id[str(rule_id)].resolve()),
                rule_id=str(rule_id),
                repository=repository,
                file=file_path,
                source_owner="generator"
                if snapshot.content.decode(c.DEFAULT_ENCODING).startswith(
                    c.Infra.AUTOGEN_HEADERS,
                )
                else "authored",
                source_state=snapshot,
                range=t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    finding.get("range"),
                ),
                text=str(finding.get("text")),
                replacement=replacement,
                actionable=actionable,
                classification=classification,
                payload=t.Cli.JSON_MAPPING_ADAPTER.validate_python(finding),
            ),
        )

    @classmethod
    def _parse_findings(
        cls,
        stdout: str,
        root: Path,
        rule_files_by_id: Mapping[str, Path],
        fixable_ids: frozenset[str],
        source_states: Mapping[Path, m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        counts: MutableMapping[c.Infra.ModScanFindingClass, int] = dict.fromkeys(
            c.Infra.ModScanFindingClass,
            0,
        )
        files: set[Path] = set()
        entries: list[m.Infra.ModScanFinding] = []
        repository_roots = tuple(
            sorted(
                u.Infra.governed_project_roots(root),
                key=cls._path_depth,
                reverse=True,
            ),
        )
        lines = stdout.splitlines()
        cls._progress(f"parse start lines={len(lines)} sources={len(source_states)}")
        due = 0.0
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            parsed = u.Cli.json_parse(line)
            if parsed.failure:
                return r[m.Infra.ModScanReport].from_failure(parsed)
            if not isinstance(parsed.value, Mapping):
                return r[m.Infra.ModScanReport].fail(
                    f"ast-grep JSONL finding is not an object: {line}",
                )
            entry = cls._line_finding(
                line,
                parsed.value,
                root,
                (rule_files_by_id, fixable_ids),
                (source_states, repository_roots),
            )
            if entry.failure:
                return r[m.Infra.ModScanReport].from_failure(entry)
            entries.append(entry.value)
            counts[entry.value.classification] += 1
            files.add(entry.value.file)
            due = cls._progress(
                f"parse finding={len(entries)} file={entry.value.file} "
                f"rule={entry.value.rule_id}",
                due,
            )
        cls._progress(f"parse finish findings={len(entries)} files={len(files)}")
        return r.ok(
            m.Infra.ModScanReport(
                findings=len(entries),
                actionable=counts[c.Infra.ModScanFindingClass.ACTIONABLE],
                detection_only=counts[c.Infra.ModScanFindingClass.DETECTION_ONLY],
                non_actionable_with_fix=counts[
                    c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX
                ],
                files=frozenset(files),
                entries=tuple(entries),
            ),
        )

    @staticmethod
    def _report_evidence(receipt: m.Infra.ModScanEvidenceReceipt) -> None:
        """Print bounded totals and the authenticated full-evidence identity."""
        evidence = receipt.evidence
        sys.stderr.write(
            "mod: findings "
            f"total={evidence.findings} actionable={evidence.actionable} "
            f"detection_only={evidence.detection_only} "
            f"non_actionable_with_fix={evidence.non_actionable_with_fix}\n",
        )
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
        rule_files_by_id: t.MappingKV[str, Path],
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
        targets: t.StrSequence,
        source_states: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan one elected ruleset over the governed targets, then admit.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        ruleset_files = {
            rule_id: rule_files_by_id[rule_id] for rule_id in ruleset.rule_ids
        }
        scan_command = u.Infra.ast_grep_scan_command(
            ruleset.config,
            rule_ids=ruleset.rule_ids,
            targets=targets,
            json_stream=True,
        )
        run = cls._run_tool(
            root,
            scan_command,
            finding_exit_code=1,
        )
        if run.failure:
            return r[m.Infra.ModScanReport].from_failure(run)
        cls._progress(f"scan source verification start files={len(source_states)}")
        verified = u.Cli.atomic_verify_binary_file_states(
            tuple(source_states.values()),
        )
        if verified.failure:
            return r[m.Infra.ModScanReport].from_failure(verified)
        cls._progress(f"scan source verification finish files={len(source_states)}")
        report = cls._parse_findings(
            run.value.stdout,
            root,
            ruleset_files,
            frozenset(ruleset.fixable_rule_ids),
            source_states,
        ).unwrap()
        if run.value.outcome.raw_return_code != 0:
            error_findings = sum(
                entry.payload.get("severity") == "error" for entry in report.entries
            )
            cls._validate_finding_receipt(run.value.stderr, error_findings).unwrap()
        return r[m.Infra.ModScanReport].ok(cls._admitted(root, report, rules_by_id))

    @staticmethod
    def _catalog_paths(
        root: Path,
        plan: m.Infra.CodemodRulePlan,
    ) -> t.VariadicTuple[Path]:
        """Elect physical catalog and project metadata inputs from their owners.

        Returns:
            Every config, rule, utility and governed manifest input path.

        """
        paths = {rule.resource.resolve() for rule in plan.rules}
        paths.update(path.resolve() for path in config._config_files())
        for ruleset in plan.rulesets:
            paths.add(ruleset.config.resolve())
            directories = FlextInfraCodemodSnapshotReconciler.scanner_directories(
                ruleset.config.parent,
            )
            for directory in (*directories.rule_dirs, *directories.util_dirs):
                paths.update(
                    path.resolve()
                    for path in directory.rglob("*")
                    if path.is_file()
                )
        paths.update(
            (project / c.PYPROJECT_FILENAME).resolve()
            for project in u.Infra.governed_project_roots(root)
        )
        for project in u.Infra.governed_project_roots(root):
            workspace_manifest = u.Infra.workspace_manifest_path(project)
            if workspace_manifest.is_file():
                paths.add(workspace_manifest.resolve())
        manifest = root / c.Infra.GITMODULES
        if manifest.is_file():
            paths.add(manifest.resolve())
        return tuple(sorted(paths))

    @classmethod
    def _capture_sources(
        cls,
        root: Path,
        targets: t.StrSequence,
    ) -> t.MappingKV[Path, m.Cli.AtomicFileState]:
        """Authenticate each source once for all providers in one scan.

        Returns:
            Atomic states indexed by their resolved source paths.

        """
        source_paths = tuple(sorted({root / target for target in targets}))
        cls._progress(f"source capture start files={len(source_paths)}")
        source_states: dict[Path, m.Cli.AtomicFileState] = {}
        due = 0.0
        for index, path in enumerate(source_paths, start=1):
            due = cls._progress(
                f"source capture file={index}/{len(source_paths)} "
                f"path={path.relative_to(root)}",
                due,
            )
            source_states[path.resolve()] = u.Cli.atomic_read_binary_file_state(
                path,
                required=True,
            ).unwrap()
        cls._progress(f"source capture finish files={len(source_states)}")
        return source_states

    @classmethod
    def _verify_scan_membership(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Reject scope or catalog changes without rejecting published source bytes.

        Returns:
            The first native failure or the authenticated unchanged input set.

        """
        inputs = report.scan_inputs
        if inputs is None:
            return r[bool].fail("mod report has no authenticated scan inputs")
        if inputs.root != root.resolve():
            return r[bool].fail("mod report belongs to a different workspace root")
        if tuple(u.Infra.ast_grep_scan_targets(root)) != tuple(inputs.scope):
            return r[bool].fail("mod scan target scope changed")
        if {(root / target).resolve() for target in inputs.scope} != {
            state.path for state in inputs.source_states
        }:
            return r[bool].fail("mod scan source input scope changed")
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return r[bool].from_failure(planned)
        plan = planned.value
        digest = u.Cli.sha256_bytes(
            plan.model_dump_json().encode(c.DEFAULT_ENCODING),
        )
        if digest != inputs.plan_digest:
            return r[bool].fail("mod scan elected rule plan changed")
        if cls._catalog_paths(root, plan) != tuple(
            state.path for state in inputs.catalog_states
        ):
            return r[bool].fail("mod scan catalog input scope changed")
        return u.Cli.atomic_verify_binary_file_states(inputs.catalog_states)

    @classmethod
    def _verify_scan_inputs(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Authenticate unchanged scan membership and all original source bytes.

        Returns:
            The first membership or physical source failure.

        """
        membership = cls._verify_scan_membership(root, report)
        if membership.failure:
            return membership
        inputs = report.scan_inputs
        if inputs is None:
            return r[bool].fail("mod report has no authenticated scan inputs")
        return u.Cli.atomic_verify_binary_file_states((
            *inputs.source_states,
            *(state for entry in report.entries for state in entry.binding_states),
        ))

    @classmethod
    def apply_report(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Publish one admitted unchanged scan through the existing CAS publisher.

        Returns:
            The first proof/publication failure or accepted syntax publication.

        """
        verified = cls._verify_scan_inputs(root, report)
        if verified.failure:
            return r[bool].from_failure(verified)
        cls._progress(f"syntax publication start actionable={report.actionable}")
        published = FlextInfraModReplacements.publish(
            root,
            report,
            preflight=lambda: cls._verify_scan_inputs(root, report),
            validator=lambda: cls._verify_scan_membership(root, report),
        )
        if published.failure:
            return r[bool].from_failure(published)
        cls._progress("syntax publication finish")
        return published

    @classmethod
    def scan(cls, root: Path, *, fix: bool) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply every ruleset elected by the composed rule-plan SSOT.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return r[m.Infra.ModScanReport].from_failure(planned)
        plan = planned.value
        reports: list[m.Infra.ModScanReport] = []
        rule_files_by_id = {rule.id: rule.resource for rule in plan.rules}
        rules_by_id = {rule.id: rule for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root)
        catalog_states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in cls._catalog_paths(root, plan)
        )
        source_states = cls._capture_sources(root, targets)
        inputs = m.Infra.ModScanInputs(
            root=root.resolve(),
            scope=tuple(targets),
            plan_digest=u.Cli.sha256_bytes(
                plan.model_dump_json().encode(c.DEFAULT_ENCODING),
            ),
            source_states=tuple(source_states.values()),
            catalog_states=catalog_states,
        )
        sys.stderr.write(
            f"mod: ast-grep {'apply' if fix else 'scan'} "
            f"providers={len(plan.rulesets)} rules={len(plan.rules)}\n",
        )
        sys.stderr.flush()
        for ruleset in plan.rulesets:
            ruleset_run = cls._ruleset_report(
                root,
                ruleset,
                rule_files_by_id,
                rules_by_id,
                targets,
                source_states,
            )
            if ruleset_run.failure:
                return r[m.Infra.ModScanReport].from_failure(ruleset_run)
            reports.append(ruleset_run.value)
        complete_report = cls.recounted(
            tuple(entry for report in reports for entry in report.entries),
            scan_inputs=inputs,
        )
        declared = cls._validate_expected_receipts(plan.rules, complete_report)
        if declared.failure:
            return r[m.Infra.ModScanReport].from_failure(declared)
        verified = cls._verify_scan_inputs(root, complete_report)
        if verified.failure:
            return r[m.Infra.ModScanReport].from_failure(verified)
        cls._progress(f"evidence publication start findings={complete_report.findings}")
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            complete_report,
            command=(
                c.Infra.ModScanCommand.APPLY if fix else c.Infra.ModScanCommand.SCAN
            ),
            scope=targets,
        )
        if receipt.failure:
            return r[m.Infra.ModScanReport].from_failure(receipt)
        cls._report_evidence(receipt.value)
        if fix:
            published = cls.apply_report(root, complete_report)
            if published.failure:
                return r[m.Infra.ModScanReport].from_failure(published)
        return r[m.Infra.ModScanReport].ok(complete_report)


__all__: list[str] = ["FlextInfraModGateEngine"]
