"""Gate measurement and ast-grep batch execution for the mod safety circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import stat
import sys
import tempfile
import time
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import closing
from pathlib import Path

from flext_infra import c, m, p, r, settings, t, u
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler


class FlextInfraModGateEngine:
    """Execute ast-grep rewrites and measure the catalog findings they leave."""

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
                stale = FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                    config_root,
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
                    stdout_file=Path(temp_dir) / "stdout",
                    stderr_file=Path(temp_dir) / "stderr",
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
                    stdout_file=Path(temp_dir) / "stdout",
                    stderr_file=Path(temp_dir) / "stderr",
                ).unwrap()
                cls._run_tool(
                    temp_root,
                    (
                        c.Infra.SG,
                        c.Infra.TEST,
                        c.Infra.SG_CONFIG_FLAG,
                        str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                    ),
                    stdout_file=Path(temp_dir) / "stdout",
                    stderr_file=Path(temp_dir) / "stderr",
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
        stdout_file: Path,
        stderr_file: Path,
        finding_exit_code: int | None = None,
    ) -> p.Result[p.Cli.ProcessOutcome]:
        """Run one AST tool and preserve its documented finding status.

        Resolve and authenticate in Make's declared tool-owning invocation
        context first. Execute the absolute managed binary in the consumer
        directory, so neither a shim nor that directory can select another tool.

        Returns:
            The fully reaped outcome; streams remain in their caller-owned files.

        """
        # Consumer scratch directories never own the invocation's runtime tools.
        owner_root = u.Infra.runtime_environment_dir(
            Path.cwd(),
            runtime_root=type(settings).fetch_global().Infra.runtime_root,
        ).parent
        binary = u.Infra.managed_mise_binary(command[0], owner_root)
        if binary.failure:
            return r[p.Cli.ProcessOutcome].from_failure(binary)
        sys.stderr.write(
            f"mod: start {' '.join(command[:2])} args={max(0, len(command) - 2)}\n",
        )
        sys.stderr.flush()
        started = time.monotonic()
        run = u.Cli.run_to_file(
            (str(binary.value), *command[1:]),
            stdout_file,
            cwd=root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(stderr_file=stderr_file),
        )
        if run.failure:
            return r[p.Cli.ProcessOutcome].from_failure(run)
        outcome = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={outcome.raw_return_code} "
            f"duration={time.monotonic() - started:.2f}s "
            f"stdout_file={stdout_file}\n",
        )
        sys.stderr.flush()
        if not u.Cli.process_succeeded(outcome):
            if (
                outcome.raw_return_code == finding_exit_code
                and not outcome.timed_out
                and outcome.forwarded_signal is None
            ):
                return r[p.Cli.ProcessOutcome].ok(outcome)
            diagnostics: list[str] = []
            for path in (stdout_file, stderr_file):
                content = (
                    u.Cli
                    .atomic_read_binary_file_state(path, required=True)
                    .unwrap()
                    .content
                )
                if content is not None and content.strip():
                    diagnostics.append(content.decode("utf-8").strip())
            detail = "\n".join(diagnostics)
            return r[p.Cli.ProcessOutcome].fail(
                f"{command[0]} exited with code {outcome.raw_return_code}: {detail}",
            )
        stderr_bytes = (
            u.Cli
            .atomic_read_binary_file_state(stderr_file, required=True)
            .unwrap()
            .content
        )
        error = (
            f"ast-grep stderr stream is missing: {stderr_file}"
            if stderr_bytes is None
            else stderr_bytes.decode("utf-8").strip()
        )
        return (
            r[p.Cli.ProcessOutcome].fail(error)
            if error
            else r[p.Cli.ProcessOutcome].ok(outcome)
        )

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
        for project, entries in grouped.items():
            selected = FlextInfraModGateEngine._admitted_project(
                project,
                FlextInfraModGateEngine.recounted(tuple(entries)),
                rules_by_id,
                facts[project],
                epoch,
            )
            admitted.extend(
                entry.model_copy(
                    update={"file": entry.file.relative_to(root.resolve())}
                )
                for entry in selected.entries
            )
        return FlextInfraModGateEngine.recounted(
            tuple(admitted), source_states=report.source_states
        )

    @staticmethod
    def _admitted_project(
        root: Path,
        report: m.Infra.ModScanReport,
        rules_by_id: t.MappingKV[str, m.Infra.CodemodRule],
        facts: m.Infra.CodemodProjectFacts,
        epoch: m.Infra.CodemodSourceEpoch,
    ) -> m.Infra.ModScanReport:
        """Keep the findings whose rule's project context holds, recounted.

        A rule's ``metadata.context`` binds captured metavariables to project
        predicates ast-grep cannot see (standard library, own package, runtime
        closure, the file's declared facade family); the syntactic match is a
        finding only when every condition holds.

        Returns:
            The resulting ``m.Infra.ModScanReport``.

        """
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
                        captures=FlextInfraModGateEngine._captures(entry.payload),
                        facts=facts,
                        snapshot=snapshot,
                    ),
                    project=project,
                    sources=sources,
                )
            )
        if entries == report.entries:
            return report
        return FlextInfraModGateEngine.recounted(
            entries, source_states=report.source_states
        )

    @staticmethod
    def recounted(
        entries: t.VariadicTuple[m.Infra.ModScanFinding],
        *,
        source_states: tuple[m.Cli.AtomicFileState, ...] | None = None,
    ) -> m.Infra.ModScanReport:
        """Return the scan report of exactly these findings, classes recounted.

        Returns:
            The scan report of exactly these findings, classes recounted.

        """
        return m.Infra.ModScanReport(
            files=frozenset(entry.file for entry in entries),
            entries=entries,
            source_states=source_states,
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
        """Resolve one finding's file against the authenticated scan snapshots.

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
        observed = u.Cli.atomic_read_binary_file_state(resolved_file, required=True)
        if observed.failure:
            if not resolved_file.exists():
                return r[t.Pair[Path, m.Cli.AtomicFileState]].fail(
                    f"finding source vanished during scanning: {resolved_file}",
                    error_code=c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE,
                )
            return r[t.Pair[Path, m.Cli.AtomicFileState]].from_failure(observed)
        if observed.value.content != snapshot.content:
            return r[t.Pair[Path, m.Cli.AtomicFileState]].fail(
                f"finding source changed during scanning: {resolved_file}",
                error_code=c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE,
            )
        if observed.value != snapshot:
            return r[t.Pair[Path, m.Cli.AtomicFileState]].ok(
                (file_path, observed.value),
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

    @staticmethod
    def _finding_repository(
        file_path: Path,
        repository_roots: t.SequenceOf[Path],
        root: Path,
    ) -> str:
        """Return the governed repository name owning one finding path.

        Returns:
            The nearest governed repository name, else the scanned root name.

        """
        source_path = (root / file_path).resolve()
        return next(
            (
                candidate.name
                for candidate in repository_roots
                if source_path.is_relative_to(candidate)
            ),
            root.resolve().name,
        )

    @classmethod
    def _line_finding(
        cls,
        line: str,
        finding: t.MappingKV[str, t.JsonValue],
        root: Path,
        plan: t.Pair[Mapping[str, Path], frozenset[str]],
        context: m.Infra.ModScanSourceContext,
    ) -> p.Result[m.Infra.ModScanFinding]:
        """Validate one JSONL finding into a typed, authenticated entry.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanFinding]``.

        """
        rule_files_by_id, fixable_ids = plan
        rule_id = finding.get("ruleId")
        contract_error = cls._finding_contract_error(finding, line, rule_files_by_id)
        if contract_error is not None:
            return r[m.Infra.ModScanFinding].fail(contract_error)
        raw_replacement = finding.get("replacement")
        replacement = raw_replacement if isinstance(raw_replacement, str) else None
        native_file = str(finding.get("file"))
        if native_file not in context.authenticated:
            context.authenticated[native_file] = cls._authenticated_snapshot(
                root, native_file, context.source_states
            )
        authenticated = context.authenticated[native_file]
        file_path = Path(native_file)
        if file_path not in context.repositories:
            context.repositories[file_path] = cls._finding_repository(
                file_path, context.repository_roots, root
            )
        if authenticated.failure:
            if authenticated.error_code == c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE:
                return r[m.Infra.ModScanFinding].ok(
                    m.Infra.ModScanFinding(
                        rule_file=str(rule_files_by_id[str(rule_id)].resolve()),
                        rule_id=str(rule_id),
                        repository=context.repositories[file_path],
                        file=file_path,
                        range=t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                            finding.get("range"),
                        ),
                        text=str(finding.get("text")),
                        replacement=replacement,
                        actionable=False,
                        classification=c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT,
                        payload=t.Cli.JSON_MAPPING_ADAPTER.validate_python(finding),
                    ),
                )
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
        return r[m.Infra.ModScanFinding].ok(
            m.Infra.ModScanFinding(
                rule_file=str(rule_files_by_id[str(rule_id)].resolve()),
                rule_id=str(rule_id),
                repository=context.repositories[file_path],
                file=file_path,
                source_owner="generator"
                if any(
                    snapshot.content.startswith(header.encode(c.DEFAULT_ENCODING))
                    for header in c.Infra.AUTOGEN_HEADERS
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

    @staticmethod
    def _native_records(stdout: Path) -> Generator[bytes]:
        """Frame native JSONL records across authenticated byte-block boundaries.

        Args:
            stdout: The path to the standard output file containing JSONL records.

        Yields:
            Complete JSONL records as bytes.
        """
        pending = b""
        with closing(u.Cli.atomic_iter_binary_file(stdout)) as chunks:
            for chunk in chunks:
                *complete, pending = (pending + chunk).split(b"\n")
                yield from complete
        if pending:
            yield pending

    @classmethod
    def _parse_findings(
        cls,
        stdout: Path,
        root: Path,
        rule_files_by_id: Mapping[str, Path],
        fixable_ids: frozenset[str],
        context: m.Infra.ModScanSourceContext,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.
        """
        entries: list[m.Infra.ModScanFinding] = []
        with closing(cls._native_records(stdout)) as lines:
            for raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue
                parsed = u.Cli.json_loads(line)
                if parsed.failure:
                    return r[m.Infra.ModScanReport].from_failure(parsed)
                if not isinstance(parsed.value, Mapping):
                    return r[m.Infra.ModScanReport].fail(
                        f"ast-grep JSONL finding is not an object: {line!r}",
                    )
                entry = cls._line_finding(
                    line.decode("utf-8"),
                    parsed.value,
                    root,
                    (rule_files_by_id, fixable_ids),
                    context,
                )
                if entry.failure:
                    return r[m.Infra.ModScanReport].from_failure(entry)
                entries.append(entry.value)
        authenticated_states = dict(context.source_states)
        for authenticated in context.authenticated.values():
            if authenticated.failure:
                continue
            state = authenticated.value[1]
            observed = u.Cli.atomic_read_binary_file_state(
                state.path, required=True
            ).unwrap()
            if observed != state:
                return r[m.Infra.ModScanReport].fail(
                    f"finding source changed during admission: {state.path}",
                    error_code=c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE,
                )
            authenticated_states[state.path] = state
        return r.ok(
            cls.recounted(
                tuple(entries),
                source_states=tuple(authenticated_states.values()),
            ),
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
        targets: t.StrSequence,
        context: m.Infra.ModScanSourceContext,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Collect one provider's complete native findings before shared admission.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
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
                stdout_file=stdout_file,
                stderr_file=stderr_file,
                finding_exit_code=1,
            )
            if run.failure:
                return r[m.Infra.ModScanReport].from_failure(run)
            sys.stderr.write(f"mod: parse native JSONL file={stdout_file}\n")
            sys.stderr.flush()
            report = cls._parse_findings(
                stdout_file,
                root,
                ruleset_files,
                frozenset(ruleset.fixable_rule_ids),
                context,
            ).unwrap()
            sys.stderr.write(f"mod: native findings={report.findings}\n")
            sys.stderr.flush()
            if run.value.raw_return_code != 0:
                error_findings = sum(
                    entry.payload.get("severity") == "error" for entry in report.entries
                )
                if not error_findings:
                    return r[m.Infra.ModScanReport].fail(
                        "ast-grep finding exit has no error-severity occurrence"
                    )
                stderr = (
                    u.Cli
                    .atomic_read_binary_file_state(stderr_file, required=True)
                    .unwrap()
                    .content
                )
                if stderr is None:
                    return r[m.Infra.ModScanReport].fail(
                        f"ast-grep finding receipt is missing: {stderr_file}"
                    )
                cls._validate_finding_receipt(
                    stderr.decode("utf-8"), error_findings
                ).unwrap()
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
        reports: list[m.Infra.ModScanReport] = []
        rules_by_id = {rule.id: rule for rule in plan.rules}
        for ruleset in plan.rulesets:
            sys.stderr.write(
                f"mod: ast-grep provider={ruleset.provider} "
                f"rules={len(ruleset.rule_ids)}\n",
            )
            sys.stderr.flush()
            scanned = cls._ruleset_report(root, ruleset, rules_by_id, targets, context)
            if scanned.failure:
                return r[m.Infra.ModScanReport].from_failure(scanned)
            reports.append(scanned.value)
        return r[m.Infra.ModScanReport].ok(
            cls.recounted(
                tuple(entry for report in reports for entry in report.entries),
                source_states=tuple(context.source_states.values()),
            )
        )

    @classmethod
    def _publish_scan(
        cls,
        root: Path,
        report: m.Infra.ModScanReport,
        publication: m.Infra.ModScanPublication,
        *,
        exact_replacements: bool,
        published_plans: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Publish full evidence before any authorized source replacement.

        Args:
            root: The root directory of the project being scanned.
            report: The complete scan report containing all findings.
            publication: The publication context for the scan.
            exact_replacements: Whether to apply only exact replacements.
            published_plans: A mutable sequence to record published plans, if any.

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
            published = FlextInfraModReplacements.publish(
                root,
                cls.authored(report),
                exact_replacements=exact_replacements,
                published_plans=published_plans,
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
        published_plans: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
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
        sys.stderr.write(
            f"mod: ast-grep {'apply' if fix else 'scan'} "
            f"providers={len(plan.rulesets)} rules={len(plan.rules)}\n",
        )
        sys.stderr.flush()
        scanned = cls._native_scan_report(root, plan, targets, context)
        if scanned.failure:
            return r[m.Infra.ModScanReport].from_failure(scanned)
        verified = u.Cli.atomic_verify_binary_file_states(tuple(source_states.values()))
        if verified.failure:
            return r[m.Infra.ModScanReport].from_failure(verified)
        current_paths = cls._scan_source_paths(root, targets)
        if current_paths != set(
            source_states
        ) or targets != u.Infra.ast_grep_scan_targets(root, source_files=source_files):
            return r[m.Infra.ModScanReport].fail(
                "native scan source inventory changed: "
                f"{sorted(current_paths ^ set(source_states))}"
            )
        complete_report = cls._admitted(
            root,
            scanned.value,
            rules_by_id,
            plan.project_rule_ids,
        )
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
            published_plans=published_plans,
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
        for ruleset in plan.rulesets:
            scanned = cls._ruleset_report(
                view_root, ruleset, rules_by_id, targets, context
            )
            if scanned.failure:
                return r[m.Infra.ModScanReport].from_failure(scanned)
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
            cls.recounted(tuple(entries), source_states=source_states),
            rules_by_id,
            plan.project_rule_ids,
            source_states,
        )
        declared = cls._validate_expected_receipts(plan.rules, report)
        if declared.failure:
            return r[m.Infra.ModScanReport].from_failure(declared)
        return r[m.Infra.ModScanReport].ok(report)


__all__: list[str] = ["FlextInfraModGateEngine"]
