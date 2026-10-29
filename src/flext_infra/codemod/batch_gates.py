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
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import closing
from pathlib import Path

from flext_infra import c, m, p, r, settings, t, u
from flext_infra.codemod import (
    FlextInfraCodemodSnapshotReconciler,
    FlextInfraModReplacements,
)


class FlextInfraModGateEngine:
    """Execute ast-grep rewrites and measure the catalog findings they leave."""

    @classmethod
    def validate_rule_fixtures(
        cls,
        root: Path,
        rules: Sequence[Path],
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
                cls._materialize_native_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                tested = cls._sg_test(temp_root, root)
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
        rules: Sequence[Path],
        *,
        apply: bool,
    ) -> p.Result[Sequence[str]]:
        """Regenerate every governed owner's snapshots from its rule tests.

        The explicit counterpart of the verifying ``validate_rule_fixtures``:
        snapshots are projections of the declared test cases, rebuilt from
        scratch so removed rules and deleted cases leave no residue. The
        returned changes are the reviewed diff; inherited providers keep the
        snapshots their owner ships.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

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
                cls._materialize_native_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                cls._sg_test(temp_root, root, c.Infra.SG_UPDATE_ALL).unwrap()
                cls._sg_test(temp_root, root).unwrap()
                changes.extend(
                    cls._publish_regenerated_snapshots(
                        config_root=config_root,
                        temp_root=temp_root,
                        apply=apply,
                    ),
                )
        return r[Sequence[str]].ok(tuple(changes))

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
        rules: Sequence[Path],
    ) -> Sequence[tuple[Path, Sequence[Path], bool]]:
        """Group rules by fixture owner and mark the owners this root governs.

        Returns:
            The resulting ``Sequence[tuple[Path, Sequence[Path], bool]]``.

        Raises:
            ValueError: If rule fixture scratch lies inside its source root.

        """
        governed_roots = tuple(
            project.resolve() for project in u.Infra.governed_project_roots(root)
        )
        # Only authored catalogs own fixtures: a selection of generated rules
        # elects no owner, and their renderer tests own their proof.
        rules_by_owner: MutableMapping[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        scratch = settings.work_dir
        owners: list[tuple[Path, Sequence[Path], bool]] = []
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
            TypeError: If ast-grep utilDirs must be a list.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        snapshot_roots = {
            directory / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            for directory in directories.test_dirs
        }
        # A catalog rule referencing a stable generated utility resolves it in
        # fixtures from the catalog's fixture values; the native stage never
        # reads them, so a project's own generated utility always wins there.
        fixture_utils = config_root / c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME
        pending = [config_root / c.Infra.CODEMOD_CONFIG_FILENAME]
        pending.extend((
            *directories.rule_dirs,
            *directories.util_dirs,
            *directories.test_dirs,
            *((fixture_utils,) if fixture_utils.is_dir() else ()),
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
        if fixture_utils.is_dir():
            staged_config = temp_root / c.Infra.CODEMOD_CONFIG_FILENAME
            payload = dict(u.Cli.yaml_safe_load(staged_config).unwrap())
            declared = payload.get(c.Infra.CODEMOD_UTIL_DIRS_KEY, [])
            if not isinstance(declared, list):
                msg = f"ast-grep utilDirs must be a list: {staged_config}"
                raise TypeError(msg)
            payload[c.Infra.CODEMOD_UTIL_DIRS_KEY] = (
                [*declared, c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME]
                if c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME not in declared
                else declared
            )
            u.Cli.yaml_dump(staged_config, payload).unwrap()

    @classmethod
    def _materialize_native_rule_files(
        cls,
        *,
        config_root: Path,
        temp_root: Path,
        owner_rules: Sequence[Path],
    ) -> None:
        """Stage every rule document in one native multi-document file.

        Every binding-sensitive utility a document references (catalog or
        fixture value) is embedded as its local, so a fixture binds
        metavariables exactly like the native scan. Global utility files
        retain their native single-document contract.

        Raises:
            RuntimeError: If an ast-grep rule document has no id.
            ValueError: If the fixture owner declares no rule directory.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        if not directories.rule_dirs:
            msg = f"fixture owner declares no native rule directory: {config_root}"
            raise ValueError(msg)
        source_rules = set(owner_rules)
        for directory in directories.rule_dirs:
            source_rules.update(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}"))
        cls._split_utility_files(config_root, temp_root, directories.util_dirs)
        bodies = cls._staged_utility_bodies((
            *(
                temp_root / item.relative_to(config_root)
                for item in directories.util_dirs
            ),
            temp_root / c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME,
        ))
        sensitive = u.Infra.codemod_binding_sensitive(bodies)
        rendered: list[t.JsonMapping] = []
        for rule in sorted(source_rules):
            documents = u.Cli.yaml_parse_documents(
                u.Cli.files_read_text(rule).unwrap()
            ).unwrap()
            temp_rule = temp_root / rule.relative_to(config_root)
            temp_rule.unlink()
            for document in documents:
                rule_id = document.get(c.Infra.CODEMOD_RULE_TEST_ID_KEY)
                if not isinstance(rule_id, str) or not rule_id:
                    msg = f"ast-grep rule document missing required id: {rule}"
                    raise RuntimeError(msg)
                rendered.append(
                    u.Infra.codemod_bound_document(document, bodies, sensitive)
                )
        if rendered:
            u.Infra.codemod_write_native_documents(
                temp_root
                / directories.rule_dirs[0].relative_to(config_root)
                / c.Infra.CODEMOD_NATIVE_RULE_BUNDLE_FILENAME,
                tuple(rendered),
            )

    @staticmethod
    def _split_utility_files(
        config_root: Path, temp_root: Path, util_dirs: Sequence[Path]
    ) -> None:
        """Replace each staged multi-document utility file with one file per id."""
        for directory in util_dirs:
            for utility in sorted(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")):
                documents = u.Cli.yaml_parse_documents(
                    u.Cli.files_read_text(utility).unwrap()
                ).unwrap()
                if len(documents) <= 1:
                    continue
                temp_utility = temp_root / utility.relative_to(config_root)
                temp_utility.unlink()
                for document in documents:
                    u.Infra.codemod_write_native_documents(
                        temp_utility.with_name(
                            f"{document['id']}{c.Infra.CODEMOD_RULE_SUFFIX}"
                        ),
                        (document,),
                    )

    @staticmethod
    def _staged_utility_bodies(
        directories: Sequence[Path],
    ) -> Mapping[str, t.JsonMapping]:
        """Read the rule body of every staged utility by its identity.

        Returns:
            Each utility's rule body keyed by its id.

        """
        bodies: MutableMapping[str, t.JsonMapping] = {}
        for directory in directories:
            if not directory.is_dir():
                continue
            for utility in sorted(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")):
                for document in u.Cli.yaml_parse_documents(
                    u.Cli.files_read_text(utility).unwrap()
                ).unwrap():
                    body = document.get("rule")
                    if isinstance(body, Mapping):
                        bodies[str(document["id"])] = body
        return bodies

    @staticmethod
    def _publish_regenerated_snapshots(
        *,
        config_root: Path,
        temp_root: Path,
        apply: bool,
    ) -> Sequence[str]:
        """Mirror only regenerated snapshot files back to source; report each change.

        Rules, utilities and tests are inputs of the regeneration and are never
        written back. A committed snapshot the regeneration did not produce
        belongs to a removed rule or test and is removed with the rest.

        Returns:
            The resulting ``Sequence[str]``.

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

    @classmethod
    def _sg_test(
        cls,
        temp_root: Path,
        artifact_root: Path,
        *flags: str,
    ) -> p.Result[p.Cli.ProcessOutcome]:
        """Run ``sg test`` against one staged rule-fixture root.

        Returns:
            The fully reaped ``sg test`` outcome.

        """
        return cls._run_tool(
            temp_root,
            (
                c.Infra.SG,
                c.Infra.TEST,
                c.Infra.SG_INCLUDE_OFF_FLAG,
                *flags,
                c.Infra.SG_CONFIG_FLAG,
                str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
            ),
            streams=(temp_root.parent / "stdout", temp_root.parent / "stderr"),
            artifact_root=artifact_root,
        )

    @staticmethod
    def _run_tool(
        root: Path,
        command: Sequence[str],
        *,
        streams: tuple[Path, Path],
        artifact_root: Path,
        finding_exit_code: int | None = None,
    ) -> p.Result[p.Cli.ProcessOutcome]:
        """Run one AST tool and preserve its documented finding status.

        Resolve and authenticate in Make's declared tool-owning invocation
        context first. Execute the absolute managed binary in the consumer
        directory, so neither a shim nor that directory can select another tool.

        Returns:
            The fully reaped outcome; streams remain in their caller-owned files.

        """
        stdout_file, stderr_file = streams
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
            stream_receipts = tuple(
                u.Infra.publish_mod_native_artifact(artifact_root, path)
                for path in (stdout_file, stderr_file)
            )
            detail = "\n".join(
                f"{channel}={receipt.path} size={receipt.size} sha256={receipt.sha256}"
                for channel, receipt in zip(
                    ("stdout", "stderr"), stream_receipts, strict=True
                )
            )
            return r[p.Cli.ProcessOutcome].fail(
                f"{command[0]} exited with code {outcome.raw_return_code} "
                f"timed_out={outcome.timed_out} "
                f"forwarded_signal={outcome.forwarded_signal}\n{detail}",
            )
        stderr = u.Cli.atomic_read_binary_file_receipt(
            stderr_file, required=True
        ).unwrap()
        if stderr.size != 0:
            receipt = u.Infra.publish_mod_native_artifact(artifact_root, stderr_file)
            return r[p.Cli.ProcessOutcome].fail(
                f"{command[0]} emitted unexpected stderr: {receipt.path} "
                f"size={receipt.size} sha256={receipt.sha256}"
            )
        return r[p.Cli.ProcessOutcome].ok(outcome)

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
    def _elected(
        root: Path,
        report: m.Infra.ModScanReport,
        rules_by_id: Mapping[str, m.Infra.CodemodRule],
        project_rule_ids: Mapping[Path, Sequence[str]],
    ) -> m.Infra.ModScanReport:
        """Keep each source's findings of its nearest governed project's plan.

        Every native match is a finding; the only selection is the rule
        election of the project that owns the source.

        Returns:
            The elected findings, grouped by owning project, recounted.

        """
        elected = {
            project: frozenset(rule_ids)
            for project, rule_ids in project_rule_ids.items()
        }
        projects = sorted(
            elected, key=FlextInfraModGateEngine._path_depth, reverse=True
        )
        physical_root = root.resolve()
        grouped: MutableMapping[Path, list[m.Infra.ModScanFinding]] = {}
        owners: MutableMapping[Path, tuple[Path, Path]] = {}
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
                            "file": source.relative_to(physical_root),
                            "catalog_digest": rules_by_id[entry.rule_id].digest,
                            "module_absence": rules_by_id[entry.rule_id].module_absence,
                        }
                    )
                )
        return FlextInfraModGateEngine.recounted(
            tuple(entry for entries in grouped.values() for entry in entries),
            native_artifacts=report.native_artifacts,
        )

    @staticmethod
    def recounted(
        entries: tuple[m.Infra.ModScanFinding, ...],
        *,
        native_artifacts: tuple[m.Cli.AtomicFileReceipt, ...] | None = None,
    ) -> m.Infra.ModScanReport:
        """Return the scan report of exactly these findings, classes recounted.

        Returns:
            The scan report of exactly these findings, classes recounted.

        """
        return m.Infra.ModScanReport(
            files=frozenset(entry.file for entry in entries),
            entries=entries,
            native_artifacts=(
                tuple(
                    {
                        entry.native_receipt.path: entry.native_receipt
                        for entry in entries
                        if entry.native_receipt is not None
                    }.values()
                )
                if native_artifacts is None
                else native_artifacts
            ),
        )

    @classmethod
    def authored[FindingT: m.Infra.ModOccurrence](
        cls, report: m.Infra.ModOccurrenceReport[FindingT]
    ) -> m.Infra.ModOccurrenceReport[FindingT]:
        """Return the findings mod may rewrite: a generated source is never one.

        A generator finding stays blocking evidence for its generator; it never
        holds back the rewrites of the authored sources.

        Returns:
            The findings mod may rewrite: a generated source is never one.

        """
        entries = tuple(
            entry for entry in report.entries if entry.source_owner != "generator"
        )
        return report.model_copy(
            update={
                "entries": entries,
                "files": frozenset(entry.file for entry in entries),
            }
        )

    @staticmethod
    def _validate_expected_receipts(
        rules: Sequence[m.Infra.CodemodRule],
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
        finding: Mapping[str, t.JsonValue],
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
        if not isinstance(rule_id, str) or rule_id not in rule_files_by_id:
            return f"invalid ast-grep finding contract: {line}"
        if not isinstance(text, str) or not isinstance(file, str):
            return f"invalid ast-grep finding contract: {line}"
        if not isinstance(source_range, Mapping):
            return f"invalid ast-grep finding contract: {line}"
        if raw_replacement is not None and not isinstance(raw_replacement, str):
            return f"invalid ast-grep finding contract: {line}"
        return None

    @staticmethod
    def _authenticated_snapshot(
        root: Path,
        file: str,
    ) -> p.Result[tuple[Path, m.Cli.AtomicFileState]]:
        """Associate a finding with its source's current state.

        Returns:
            The resulting ``(file_path, state)`` pair, or the drift failure.

        """
        file_path = Path(file)
        resolved_file = (root / file_path).resolve()
        observed = u.Cli.atomic_read_binary_file_state(resolved_file, required=True)
        if observed.failure and not resolved_file.exists():
            return r[tuple[Path, m.Cli.AtomicFileState]].fail(
                f"finding source vanished during scanning: {resolved_file}",
                error_code=c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE,
            )
        return observed.map(lambda state: (file_path, state))

    @staticmethod
    def _classified_finding(
        rule_id: str,
        fixable_ids: frozenset[str],
        text: str,
        replacement: str | None,
        line: str,
    ) -> p.Result[tuple[bool, c.Infra.ModScanFindingClass]]:
        """Classify one finding against its rule's fix contract.

        Returns:
            The resulting ``(actionable, classification)`` pair.

        """
        outcome = r[tuple[bool, c.Infra.ModScanFindingClass]]
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
        repository_roots: Sequence[Path],
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
        record: tuple[str, Mapping[str, t.JsonValue]],
        root: Path,
        plan: tuple[Mapping[str, Path], frozenset[str]],
        context: m.Infra.ModScanSourceContext,
        native: tuple[m.Infra.ModNativeRecord, m.Cli.AtomicFileReceipt],
    ) -> p.Result[m.Infra.ModScanFinding]:
        """Validate one JSONL finding into a typed, authenticated entry.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanFinding]``.

        """
        finding = record[1]
        rule_files_by_id, fixable_ids = plan
        rule_id = finding.get("ruleId")
        contract_error = cls._finding_contract_error(
            finding, record[0], rule_files_by_id
        )
        if contract_error is not None:
            return r[m.Infra.ModScanFinding].fail(contract_error)
        severity = finding.get("severity")
        match severity:
            case "error" | "warning" | "info" | "hint":
                pass
            case _:
                return r[m.Infra.ModScanFinding].fail(
                    f"invalid ast-grep finding severity: {record[0]}"
                )
        raw_replacement = finding.get("replacement")
        replacement = raw_replacement if isinstance(raw_replacement, str) else None
        native_file = str(finding.get("file"))
        if native_file not in context.authenticated:
            context.authenticated[native_file] = cls._authenticated_snapshot(
                root, native_file
            )
        authenticated = context.authenticated[native_file]
        file_path = Path(native_file)
        if file_path not in context.repositories:
            context.repositories[file_path] = cls._finding_repository(
                file_path, context.repository_roots, root
            )
        if authenticated.failure:
            if authenticated.error_code != c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE:
                return r[m.Infra.ModScanFinding].from_failure(authenticated)
            snapshot = None
            actionable = False
            classification = c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT
        else:
            file_path, snapshot = authenticated.value
            if snapshot.content is None:
                return r[m.Infra.ModScanFinding].fail(
                    f"authenticated snapshot has no content: {file_path}",
                )
            classified = cls._classified_finding(
                str(rule_id),
                fixable_ids,
                str(finding.get("text")),
                replacement,
                record[0],
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
                if snapshot is not None
                and snapshot.content is not None
                and snapshot.content.startswith(
                    c.Infra.AUTOGEN_HEADER.encode(c.DEFAULT_ENCODING)
                )
                else "authored",
                source_state=snapshot,
                range=u.json_mapping_adapter().validate_python(
                    finding.get("range"),
                ),
                text=str(finding.get("text")),
                message=(
                    native_message
                    if isinstance(native_message := finding.get("message"), str)
                    else None
                ),
                replacement=replacement,
                actionable=actionable,
                classification=classification,
                severity=severity,
                origin="owned-path"
                if finding.get("origin") == "owned-path"
                else "ast-grep",
                replacement_offsets=(
                    m.Infra.ModReplacementOffsets.model_validate(
                        finding["replacementOffsets"]
                    )
                    if "replacementOffsets" in finding
                    else None
                ),
                native_record=native[0],
                native_receipt=native[1],
            ),
        )

    @staticmethod
    def _native_records(stdout: Path) -> Generator[tuple[int, bytes]]:
        """Frame native JSONL records across authenticated byte-block boundaries.

        Args:
            stdout: The path to the standard output file containing JSONL records.

        Yields:
            Complete JSONL records as bytes.

        """
        pending = b""
        offset = 0
        with closing(u.Cli.atomic_iter_binary_file(stdout)) as chunks:
            for chunk in chunks:
                *complete, pending = (pending + chunk).split(b"\n")
                for line in complete:
                    yield offset, line
                    offset += len(line) + 1
        if pending:
            yield offset, pending

    @classmethod
    def _parse_findings(
        cls,
        stdout: Path,
        root: Path,
        plan: tuple[Mapping[str, Path], frozenset[str]],
        context: m.Infra.ModScanSourceContext,
        native_receipt: m.Cli.AtomicFileReceipt,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        entries: list[m.Infra.ModScanFinding] = []
        with closing(cls._native_records(stdout)) as lines:
            for offset, raw_line in lines:
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
                    (line.decode("utf-8"), parsed.value),
                    root,
                    plan,
                    context,
                    (
                        m.Infra.ModNativeRecord(
                            offset=offset,
                            length=len(raw_line),
                            sha256=u.Cli.sha256_bytes(raw_line),
                        ),
                        native_receipt,
                    ),
                )
                if entry.failure:
                    return r[m.Infra.ModScanReport].from_failure(entry)
                entries.append(entry.value)
        return r.ok(
            cls.recounted(
                tuple(entries),
                native_artifacts=(native_receipt,),
            ),
        )

    @staticmethod
    def _report_evidence(receipt: m.Infra.ModScanEvidenceReceipt) -> None:
        """Print bounded totals and the authenticated full-evidence identity."""
        evidence = receipt.evidence
        sys.stderr.write(f"mod: findings total={evidence.findings}\n")
        for finding_class, count in evidence.totals_by_class.items():
            # ModScanFindingClass is a StrEnum: its str form IS the value, so
            # the key prints correctly through JSON receipt round-trips too.
            sys.stderr.write(
                f"mod: findings class={finding_class} count={count}\n",
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
        rules_by_id: Mapping[str, m.Infra.CodemodRule],
        selection: tuple[Sequence[str], m.Infra.ModScanSourceContext],
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
                native_artifacts=tuple(
                    {
                        receipt.path: receipt
                        for receipt in (*report.native_artifacts, stderr)
                    }.values()
                ),
            )
        return r[m.Infra.ModScanReport].ok(report)

    @staticmethod
    def _scan_source_paths(root: Path, targets: Sequence[str]) -> frozenset[Path]:
        """Enumerate the native selection through its canonical Python file owner.

        Args:
            root: The root directory of the selected workspace scan.
            targets: The sequence of target paths to enumerate.

        Returns:
            Resolved Python paths, retaining prohibited lexical stub leaves.

        """
        return frozenset(
            path.absolute() if path.suffix == ".pyi" else path.resolve()
            for target in targets
            for path in (
                u.Infra.iter_directory_python_files(root / target, repository_root=root)
                if (root / target).suffix != ".pyi" and (root / target).is_dir()
                else (root / target,)
            )
        )

    @classmethod
    def apply_report(
        cls,
        root: Path,
        report: m.Infra.ModOccurrenceReport[m.Infra.ModScanFinding],
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
        # A stale report never publishes: every captured finding source must
        # still match its file before any effect.
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
        plan: m.Infra.CodemodRulePlan,
        targets: Sequence[str],
        context: m.Infra.ModScanSourceContext,
        *,
        artifact_root: Path | None = None,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Combine every elected provider's complete ordered native occurrences.

        Args:
            root: The root directory of the project being scanned.
            plan: The codemod rule plan containing rules and rulesets.
            targets: The sequence of target paths to scan.
            context: The source context for the scan and its physical project roots.
            artifact_root: Base owner for project-scoped native scan artifacts.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        rules_by_id = {rule.id: rule for rule in plan.rules}
        root = root.resolve()
        artifact_root = root if artifact_root is None else artifact_root.resolve()
        native_targets = tuple(
            target for target in targets if Path(target).suffix != ".pyi"
        )
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="mod-native-catalog-", dir=settings.work_dir
        ) as directory:
            entries: list[m.Infra.ModScanFinding] = []
            artifacts: list[m.Cli.AtomicFileReceipt] = []
            for project, project_targets in u.Infra.codemod_project_targets(
                plan, native_targets
            ):
                resolved_project = (
                    project
                    if context.project_source_roots is None
                    else context.project_source_roots[project]
                ).resolve()
                if not resolved_project.is_relative_to(root):
                    return r[m.Infra.ModScanReport].fail(
                        f"native scan project escapes workspace root: "
                        f"{resolved_project}"
                    )
                stage = Path(directory) / str(len(artifacts))
                ruleset = u.Infra.codemod_stage_scan_ruleset(
                    u.Infra.codemod_project_plan(plan, project), stage
                )
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
                    return r[m.Infra.ModScanReport].from_failure(projected)
                entries.extend(projected.value.entries)
                artifacts.extend(projected.value.native_artifacts)
            scanned = r[m.Infra.ModScanReport].ok(
                cls.recounted(tuple(entries), native_artifacts=tuple(artifacts))
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
            return r[m.Infra.ModScanReport].ok(
                cls.recounted(
                    (*scanned.value.entries, *admitted_paths.value.entries),
                    native_artifacts=(*scanned.value.native_artifacts, artifact),
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
        if publication.command == c.Infra.ModScanCommand.APPLY and report.actionable:
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
        selection: Sequence[str] | m.Infra.CodemodRulePlan | None = None,
        source_files: Sequence[Path] | None = None,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply every ruleset elected by the composed rule-plan SSOT.

        Complete evidence retains generated findings; only the authored projection
        reaches publication, without granting permission to rewrite generated bytes.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanReport]``.

        """
        if isinstance(selection, m.Infra.CodemodRulePlan):
            plan = selection
            if root.resolve() not in plan.project_rule_ids:
                return r[m.Infra.ModScanReport].fail(
                    "precomposed scan plan requires its governed root and owns rule "
                    "selection"
                )
        else:
            with u.Infra.codemod_workspace_snapshot(root) as snapshot:
                planned = u.Infra.codemod_rule_plan(snapshot, rule_ids=selection)
            if planned.failure:
                return r[m.Infra.ModScanReport].from_failure(planned)
            plan = planned.value
        rules_by_id = {rule.id: rule for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root, source_files=source_files)
        context = m.Infra.ModScanSourceContext(
            inventory={
                path: u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in sorted(cls._scan_source_paths(root, targets))
            },
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
        complete_report = cls._elected(
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
            }
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
            exact_replacements=selection is not None
            and not isinstance(selection, m.Infra.CodemodRulePlan),
        )

    @staticmethod
    def _candidate_scan_states(
        candidate: m.Infra.StageSourcePlan,
        view_root: Path,
    ) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
        """Authenticate each staged effect against its declared original witness.

        Returns:
            Actual staged receipts rebound to logical paths for binding analysis.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
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
        states: list[m.Cli.AtomicFileState] = []
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
        candidate: m.Infra.StageSourcePlan,
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan an immutable overlay with the original catalog and logical policy.

        Returns:
            Full-catalog findings authenticated to candidate bytes and bindings.

        """
        root = root.resolve()
        captured = cls._candidate_scan_states(candidate, view_root)
        if captured.failure:
            return r[m.Infra.ModScanReport].from_failure(captured)
        view_root /= root.relative_to(candidate.workspace)
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            plan = u.Infra.codemod_rule_plan(snapshot).unwrap()
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
        entries: list[m.Infra.ModScanFinding] = []
        scanned = cls._native_scan_report(
            view_root,
            plan,
            u.Infra.ast_grep_scan_targets(view_root),
            context,
            artifact_root=root,
        )
        if scanned.failure:
            return r[m.Infra.ModScanReport].from_failure(scanned)
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
            return r[m.Infra.ModScanReport].from_failure(current)
        return u.Cli.atomic_verify_binary_file_states(candidate.inputs).map(
            lambda _: report
        )


__all__: list[str] = ["FlextInfraModGateEngine"]
