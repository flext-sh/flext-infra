"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
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

from collections import Counter, defaultdict
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import ClassVar

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesProtectedEditLinting
from flext_infra._utilities._git.semantic_identity import (
    FlextInfraUtilitiesGitSemanticIdentity,
)


class FlextInfraUtilitiesRefactor:
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

    _EMPTY_RULE_DELTA_OPTIONS: ClassVar[m.Infra.RuleDeltaOptions] = (
        m.Infra.RuleDeltaOptions()
    )

    @staticmethod
    def publish_mod_native_artifact(
        root: Path, staged_path: Path
    ) -> m.Cli.AtomicFileReceipt:
        """Retain exact scanner bytes before disposing its operation staging.

        Args:
            root: The scan root owning the native artifact store.
            staged_path: The operation staging path holding scanner bytes.

        Returns:
            The retained native artifact receipt in its content-addressed
            store.

        Raises:
            ValueError: When the staged artifact lacks its authenticated
                digest or the store already holds different bytes.

        """
        staged = u.Cli.atomic_read_binary_file_receipt(
            staged_path, required=True
        ).unwrap()
        if staged.sha256 is None:
            msg = "native artifact lacks its authenticated digest"
            raise ValueError(msg)
        directory = root / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH.parent / "native"
        u.Cli.ensure_dir(directory).unwrap()
        before = u.Cli.atomic_read_binary_file_receipt(
            directory / staged.sha256
        ).unwrap()
        if before.device is None:
            return u.Cli.atomic_publish_staged_binary_file_receipt_guarded(
                before, staged
            ).unwrap()
        if before.sha256 != staged.sha256 or before.size != staged.size:
            msg = "native artifact digest path contains different bytes"
            raise ValueError(msg)
        return before

    @staticmethod
    @contextmanager
    def mod_native_readers(
        artifacts: tuple[m.Cli.AtomicFileReceipt, ...],
    ) -> Generator[Mapping[Path, p.Cli.AtomicFileReader]]:
        """Retain one authenticated descriptor per artifact for one consumer pass.

        Args:
            artifacts: The authenticated artifact receipts being read.

        Yields:
            One authenticated binary reader per artifact path.

        Raises:
            ValueError: When the artifact inventory has duplicate paths.

        """
        with ExitStack() as stack:
            readers = {
                artifact.path: stack.enter_context(
                    u.Cli.atomic_binary_file_reader(artifact)
                )
                for artifact in artifacts
            }
            if len(readers) != len(artifacts):
                msg = "mod native artifact inventory has duplicate paths"
                raise ValueError(msg)

            yield readers

    @staticmethod
    def mod_native_payload(
        finding: m.Infra.ModScanFinding,
        readers: Mapping[Path, p.Cli.AtomicFileReader],
    ) -> t.JsonMapping:
        """Hydrate one complete native record explicitly through its retained reader.

        Args:
            finding: The native scan finding owning the record.
            readers: The retained authenticated readers by artifact path.

        Returns:
            The hydrated native record payload.

        Raises:
            ValueError: When the finding lacks its artifact or the hydrated
                record differs from its captured evidence.

        """
        receipt = finding.native_receipt
        if receipt is None:
            msg = "mod finding lacks its authenticated native artifact"
            raise ValueError(msg)
        record = finding.native_record
        content = readers[receipt.path].read_range(record.offset, record.length)
        if u.Cli.sha256_bytes(content) != record.sha256:
            msg = "mod native record digest differs from its captured evidence"
            raise ValueError(msg)
        payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_json(content)
        identity_admitted = (
            payload.get("ruleId") == finding.rule_id
            and payload.get("text") == finding.text
            and payload.get("range") == finding.range
        )
        content_admitted = (
            payload.get("replacement") == finding.replacement
            and payload.get("severity") == finding.severity
            and payload.get("replacementOffsets")
            == (
                None
                if finding.replacement_offsets is None
                else finding.replacement_offsets.model_dump()
            )
        )
        if not (identity_admitted and content_admitted):
            msg = "mod operational fields differ from their native record"
            raise ValueError(msg)
        return payload

    @staticmethod
    def violations_totals[FindingT: m.Infra.ModOccurrence](
        report: m.Infra.ModScanCounts[FindingT],
    ) -> m.Infra.ViolationsTotals:
        """Capture native totals without service behavior in data models.

        Returns:
            The measured totals from the complete native report.

        """
        return m.Infra.ViolationsTotals(
            findings=report.findings,
            **{
                field: getattr(report, field)
                for field in c.Infra.MOD_SCAN_CLASS_COUNT_FIELDS.values()
            },
        )

    @staticmethod
    def _finding_repository(
        entry: m.Infra.ModOccurrence | m.Infra.ModTextFinding,
        repository_root: Path | None,
        topology: Sequence[Path],
    ) -> str:
        """Resolve the repository owner of one native finding.

        Args:
            entry: Native scan or text finding being counted.
            repository_root: Root resolving text finding paths into the
                declared topology.
            topology: Declared project topology ordered by path depth.

        Returns:
            The repository name owning the finding.

        Raises:
            ValueError: When a text finding lacks declared project topology
                or falls outside it.

        """
        if isinstance(entry, m.Infra.ModOccurrence):
            return entry.repository
        if repository_root is None:
            msg = "text comparison requires declared project topology"
            raise ValueError(msg)
        path = (repository_root / entry.file).resolve()
        owner = next(
            (project for project in topology if path.is_relative_to(project)),
            None,
        )
        if owner is None:
            msg = f"text finding outside declared topology: {entry.file}"
            raise ValueError(msg)
        return owner.name

    @classmethod
    def _report_occurrence_indexes[FindingT: m.Infra.ModOccurrence](
        cls,
        report: m.Infra.ModOccurrenceReport[FindingT]
        | m.Infra.ModScanEvidence
        | m.Infra.ModTextReport,
        repository_root: Path | None,
        topology: Sequence[Path],
    ) -> tuple[
        MutableMapping[tuple[str, str], MutableMapping[tuple[str, str], int]],
        MutableMapping[tuple[str, str], list[int]],
    ]:
        """Count one report's lexical occurrences and entry positions.

        Args:
            report: Native report whose entries are counted.
            repository_root: Root resolving text finding paths into the
                declared topology.
            topology: Declared project topology ordered by path depth.

        Returns:
            The occurrence counter and entry position index per repository
            and rule key.

        """
        occurrences: MutableMapping[
            tuple[str, str], MutableMapping[tuple[str, str], int]
        ] = defaultdict(Counter)
        positions: MutableMapping[tuple[str, str], list[int]] = defaultdict(list)
        entries: Sequence[m.Infra.ModOccurrence | m.Infra.ModTextFinding] = (
            report.entries
        )
        for index, entry in enumerate(entries):
            repository = cls._finding_repository(entry, repository_root, topology)
            key = (repository, entry.rule_id)
            occurrences[key][str(entry.file), entry.text] += 1
            positions[key].append(index)
        return occurrences, positions

    @staticmethod
    def _rule_delta_rows(
        engine: str,
        counters: Sequence[
            MutableMapping[tuple[str, str], MutableMapping[tuple[str, str], int]]
        ],
        indexes: Sequence[MutableMapping[tuple[str, str], list[int]]],
        inventory: tuple[tuple[str, str], ...],
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Build the per-repository and per-rule occurrence deltas.

        Args:
            engine: Native engine name shared by both measured reports.
            counters: Before and after occurrence counters per rule key.
            indexes: Before and after entry position indexes per rule key.
            inventory: Declared repository and rule pairs included.

        Returns:
            One occurrence delta for every declared or observed rule key.

        """
        before_entries, after_entries = counters
        deltas: list[m.Infra.ViolationsRuleDelta] = []
        for key in sorted(
            set(inventory) | before_entries.keys() | after_entries.keys()
        ):
            repository, rule_id = key
            original, final = before_entries[key], after_entries[key]
            persisted = sum(
                min(original[identity], final[identity])
                for identity in original.keys() & final.keys()
            )
            before_count, after_count = sum(original.values()), sum(final.values())
            deltas.append(
                m.Infra.ViolationsRuleDelta(
                    repository=repository,
                    rule_id=rule_id,
                    engine=engine,
                    before=before_count,
                    after=after_count,
                    resolved=before_count - persisted,
                    persisted=persisted,
                    introduced=after_count - persisted,
                    semantic_correspondence_proven=False,
                    before_entries=tuple(indexes[0][key]),
                    after_entries=tuple(indexes[1][key]),
                )
            )
        return tuple(deltas)

    @staticmethod
    def rule_deltas[FindingT: m.Infra.ModOccurrence](
        before: m.Infra.ModOccurrenceReport[FindingT]
        | m.Infra.ModScanEvidence
        | m.Infra.ModTextReport,
        after: m.Infra.ModOccurrenceReport[FindingT]
        | m.Infra.ModScanEvidence
        | m.Infra.ModTextReport,
        *,
        options: m.Infra.RuleDeltaOptions = _EMPTY_RULE_DELTA_OPTIONS,
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare the lexical occurrences of two reports of one native engine.

        Args:
            before: Baseline native report from the measured engine.
            after: Final native report from the same engine.
            options: Frozen scope and authentication options for the delta.

        Returns:
            Per-repository and per-rule occurrence deltas.

        Raises:
            ValueError: Native engines differ, or a text finding lacks project
                ownership.

        """
        engine = "ast-grep" if isinstance(before, m.Infra.ModScanCounts) else "text"
        if isinstance(before, m.Infra.ModScanCounts) != isinstance(
            after, m.Infra.ModScanCounts
        ):
            msg = "rule comparison requires the same native engine"
            raise ValueError(msg)
        topology = sorted(
            options.projects, key=lambda item: len(item.parts), reverse=True
        )
        measured = [
            FlextInfraUtilitiesRefactor._report_occurrence_indexes(
                report,
                options.repository_root,
                topology,
            )
            for report in (before, after)
        ]
        return FlextInfraUtilitiesRefactor._rule_delta_rows(
            engine,
            [occurrences for occurrences, _positions in measured],
            [positions for _occurrences, positions in measured],
            options.inventory,
        )

    @staticmethod
    def _project_scope_elected(
        stage: m.Infra.ViolationsSweepStage,
        project: Path,
        before: m.Infra.ViolationsSweepSources,
    ) -> bool:
        """Whether the stage repository root falls inside the audited scope.

        Args:
            stage: Sweep stage owning the audited repository root.
            project: Audited project repository root.
            before: Baseline audit snapshot declaring the scope.

        Returns:
            Whether one scope target resolves to the audited project.

        """
        topology = sorted(
            before.repository_roots, key=lambda item: len(item.parts), reverse=True
        )
        return any(
            next(
                (
                    candidate
                    for candidate in topology
                    if (stage.repository_root / target).is_relative_to(candidate)
                ),
                None,
            )
            == project.resolve()
            for target in before.scope
        )

    @staticmethod
    def _engine_coverage(
        project: Path,
        before: m.Infra.ViolationsSweepSources,
        after: m.Infra.ViolationsSweepSources,
        lint_failures: Sequence[str],
        *,
        ast_observed: bool,
    ) -> tuple[m.Infra.ViolationsEngineCoverage, ...]:
        """Build the per-engine observation coverage receipts for one project.

        Args:
            project: Audited project repository root.
            before: Baseline audit snapshot.
            after: Final audit snapshot.
            ast_observed: Whether elected AST rules were actually scanned.
            lint_failures: Native lint execution failures joined into causes.

        Returns:
            Every engine's actual observation coverage disposition.

        """
        text_observed = before.text_report is not None and after.text_report is not None
        lint_observed = before.lint is not None and after.lint is not None
        return (
            m.Infra.ViolationsEngineCoverage(
                repository=project.name,
                engine="ast-grep",
                status="incomplete" if ast_observed else "NOT_EXECUTED",
                cause=(
                    "elected rules scanned; wholly unelected catalog membership "
                    "is not exposed by the native plan"
                    if ast_observed
                    else "effective plan or native scan unavailable"
                ),
            ),
            m.Infra.ViolationsEngineCoverage(
                repository=project.name,
                engine="text",
                status="incomplete" if text_observed else "NOT_EXECUTED",
                cause=(
                    "native text report lacks effective per-project "
                    "zero-rule audit metadata"
                ),
            ),
            m.Infra.ViolationsEngineCoverage(
                repository=project.name,
                engine="ruff",
                status="incomplete" if lint_observed else "NOT_EXECUTED",
                cause=(
                    "; ".join(lint_failures)
                    or "lint snapshots lack complete native rule IDs "
                    "and per-project zero-rule applicability metadata"
                ),
            ),
            m.Infra.ViolationsEngineCoverage(
                repository=project.name,
                engine="census",
                status="NOT_EXECUTED",
                cause="no native census rule audit collected by violations-sweep",
            ),
        )

    @staticmethod
    def violations_audit_comparison(
        project: Path,
        stage: m.Infra.ViolationsSweepStage,
        inventory: m.Infra.CodemodRulePlan | None,
    ) -> m.Infra.ViolationsSweepStage:
        """Compare native rule and collateral observations without aggregate masking.

        Returns:
            The stage receipt with every rule's actual disposition and collateral.

        """
        if stage.audit_before is None or stage.audit_after is None:
            return stage.model_copy(
                update={
                    "error": stage.error or "native audit snapshot unavailable",
                    "rule_evaluations": tuple(
                        m.Infra.ViolationsRuleEvaluation(
                            repository=project.name,
                            rule_id=rule.id,
                            catalog_digest=rule.digest,
                            provider=rule.provider,
                            resource=rule.resource,
                            detection_only=not rule.fixable,
                            status="NOT_EXECUTED",
                            delta=None,
                            error=stage.error or "native audit snapshot unavailable",
                        )
                        for rule in inventory.rules
                    )
                    if inventory is not None
                    else (),
                    "engine_coverage": tuple(
                        m.Infra.ViolationsEngineCoverage(
                            repository=project.name,
                            engine=engine,
                            status="NOT_EXECUTED",
                            cause=stage.error or "native audit snapshot unavailable",
                        )
                        for engine in ("ast-grep", "text", "ruff", "census")
                    ),
                }
            )
        before, after = stage.audit_before, stage.audit_after
        elected = before.plan.project_rule_ids.get(project.resolve())
        has_sources = FlextInfraUtilitiesRefactor._project_scope_elected(
            stage, project, before
        )
        catalog = {
            rule.id: rule
            for plan in (inventory, before.plan)
            if plan is not None
            for rule in plan.rules
        }
        deltas = (
            FlextInfraUtilitiesRefactor.rule_deltas(
                before.ast_report,
                after.ast_report,
                options=m.Infra.RuleDeltaOptions(
                    inventory=tuple(
                        (project.name, rule_id)
                        for rule_id in elected or ()
                        if has_sources
                    ),
                ),
            )
            if before.source_verified
            and after.source_verified
            and before.ast_report is not None
            and after.ast_report is not None
            else ()
        )
        rows = {row.rule_id: row for row in deltas if row.repository == project.name}
        evaluations = tuple(
            m.Infra.ViolationsRuleEvaluation(
                repository=project.name,
                rule_id=rule_id,
                catalog_digest=catalog[rule_id].digest if rule_id in catalog else None,
                provider=catalog[rule_id].provider if rule_id in catalog else None,
                resource=catalog[rule_id].resource if rule_id in catalog else None,
                detection_only=(
                    not catalog[rule_id].fixable if rule_id in catalog else None
                ),
                status=(
                    "NOT_EXECUTED"
                    if elected is None
                    else "failed"
                    if rule_id not in catalog
                    else "failed"
                    if not has_sources and rule_id in rows
                    else "not_applicable"
                    if not has_sources
                    else "failed"
                    if rule_id in rows and rule_id not in elected
                    else "observed"
                    if rule_id in elected and rule_id in rows
                    else "failed"
                    if rule_id in elected
                    else "not_applicable"
                ),
                delta=(
                    rows.get(rule_id)
                    if has_sources and elected is not None and rule_id in elected
                    else None
                ),
                error=(
                    "project absent from effective rule plan"
                    if elected is None
                    else "native rule absent from authenticated catalog"
                    if rule_id not in catalog
                    else "no governed AST source targets; native rule NOT_EXECUTED"
                    if not has_sources
                    else "rule not elected by this project's native plan"
                    if rule_id not in elected
                    else None
                    if rule_id in rows
                    else stage.error or "native AST rule scan NOT_EXECUTED"
                ),
            )
            for rule_id in sorted(set(catalog) | set(rows))
        )
        deltas += (
            FlextInfraUtilitiesRefactor.rule_deltas(
                before.text_report,
                after.text_report,
                options=m.Infra.RuleDeltaOptions(
                    repository_root=stage.repository_root,
                    projects=before.repository_roots,
                ),
            )
            if before.source_verified
            and after.source_verified
            and before.text_report is not None
            and after.text_report is not None
            else ()
        )
        evaluations += tuple(
            m.Infra.ViolationsRuleEvaluation(
                repository=row.repository,
                rule_id=row.rule_id,
                engine=row.engine,
                status="observed",
                delta=row,
                error=None,
            )
            for row in deltas
            if row.engine == "text" and row.repository == project.name
        )
        lint_failures = tuple(
            f"{path}: {error}"
            for snapshot in (before, after)
            for path, receipt in (snapshot.lint or {}).items()
            for error in FlextInfraUtilitiesProtectedEditLinting.lint_execution_errors(
                receipt
            )
        )
        coverage = FlextInfraUtilitiesRefactor._engine_coverage(
            project,
            before,
            after,
            lint_failures,
            ast_observed=(
                before.source_verified
                and after.source_verified
                and has_sources
                and elected is not None
                and before.ast_report is not None
                and after.ast_report is not None
            ),
        )
        lint = {
            path: FlextInfraUtilitiesProtectedEditLinting.lint_new_errors(
                (before.lint or {}).get(path, {}),
                findings,
            )
            for path, findings in (after.lint or {}).items()
        }
        introduced_text = (
            FlextInfraUtilitiesRefactor.text_introduced_findings(
                before.text_report, after.text_report
            )
            if before.text_report is not None and after.text_report is not None
            else None
        )
        source_inventory_unchanged = (
            before.sha256 == after.sha256
            and before.plan == after.plan
            and before.scope == after.scope
            and before.repository_roots == after.repository_roots
        )
        incomplete = "; ".join(
            row.cause for row in coverage if row.status != "observed" and row.cause
        )
        error = (
            stage.error
            or "; ".join((*before.observation_errors, *after.observation_errors))
            or "; ".join(lint_failures)
            or next(
                (
                    cause
                    for cause, failed in (
                        (
                            "read-only rule audit changed source",
                            not source_inventory_unchanged
                            and stage.verb in {"audit", "audit-rules"},
                        ),
                        ("elected rule catalog changed", before.plan != after.plan),
                        (
                            "declared project topology changed",
                            before.repository_roots != after.repository_roots,
                        ),
                        (
                            "source removal lacks an authenticated candidate plan",
                            bool(set(before.sha256) - set(after.sha256)),
                        ),
                        (
                            "scan declaration or catalog bytes changed",
                            any(
                                digest != after.sha256.get(path)
                                for path, digest in before.sha256.items()
                                if Path(path).suffix in {".yaml", ".yml", ".toml"}
                                or Path(path).name == c.Infra.GITMODULES
                            ),
                        ),
                        (
                            "native rule observation unavailable",
                            any(
                                row.status in {"failed", "NOT_EXECUTED"}
                                for row in evaluations
                            ),
                        ),
                        (
                            "introduced native finding occurrences",
                            any(row.introduced for row in deltas)
                            or any(lint.values())
                            or bool(introduced_text),
                        ),
                        (incomplete, stage.verb == "comparison" and bool(incomplete)),
                    )
                    if failed
                ),
                None,
            )
        )
        return stage.model_copy(
            update={
                "introduced_text": introduced_text,
                "source_inventory_unchanged": source_inventory_unchanged,
                "rule_evaluations": evaluations,
                "engine_coverage": coverage,
                "introduced_lint": (
                    lint if before.lint is not None and after.lint is not None else None
                ),
                "inspection_error": error or incomplete,
                "error": error,
            }
        )

    @staticmethod
    def text_introduced_findings(
        before: m.Infra.ModTextReport,
        after: m.Infra.ModTextReport,
    ) -> tuple[m.Infra.ModTextFinding, ...]:
        """Consume baseline text occurrences once, never collapsing duplicates.

        Returns:
            Actual native text findings introduced relative to the baseline.

        """
        remaining = Counter(
            (entry.file, entry.rule_id, entry.text) for entry in before.entries
        )
        introduced: list[m.Infra.ModTextFinding] = []
        for entry in after.entries:
            identity = (entry.file, entry.rule_id, entry.text)
            if remaining[identity]:
                remaining[identity] -= 1
            else:
                introduced.append(entry)
        return tuple(introduced)

    @staticmethod
    def string_list(value: t.JsonValue | None) -> Sequence[str]:
        """Normalize policy fields that should contain string collections.

        Returns:
            The resulting ``Sequence[str]``.

        Raises:
            TypeError: If expected list value.

        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        validated: p.Result[Sequence[str]] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            value,
        )
        if validated.failure:
            msg = f"expected list value: {validated.error}"
            raise TypeError(msg) from validated.exception
        return list(validated.value)

    @staticmethod
    def normalize_module_path(path_value: str | Path) -> str:
        """Normalize module path.

        Returns:
            The resulting ``str``.

        """
        path = Path(str(path_value).replace("\\", "/"))
        parts = path.parts
        if c.Infra.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path.as_posix().lstrip("./")

    @staticmethod
    def write_impact_map(
        results: Sequence[m.Infra.Result],
        output_path: Path,
    ) -> p.Result[bool]:
        """Write refactor impact map JSON to disk.

        Returns:
            The resulting ``p.Result[bool]``.

        """
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
            ],
        }
        normalized_payload: t.JsonValue = u.json_value_adapter().validate_python(
            payload,
        )
        write_result = u.Cli.json_write(output_path, normalized_payload)
        if write_result.failure:
            return r[bool].from_failure(write_result)
        return r[bool].ok(value=True)

    @staticmethod
    def mod_scan_inputs[FindingT: m.Infra.ModOccurrence](
        report: m.Infra.ModOccurrenceReport[FindingT],
    ) -> m.Infra.CodemodBindingSnapshot:
        """Union the captured finding sources once per operation.

        Args:
            report: Completed mod scan whose entries carry captured states.

        Returns:
            One snapshot of each entry's captured source state.

        """
        return m.Infra.CodemodBindingSnapshot(
            states=tuple(
                entry.source_state
                for entry in report.entries
                if entry.source_state is not None
            )
        )

    @staticmethod
    def publish_mod_scan_evidence(
        root: Path,
        report: m.Infra.ModScanReport,
        *,
        publication: m.Infra.ModScanPublication,
    ) -> p.Result[m.Infra.ModScanEvidenceReceipt]:
        """Atomically replace the complete structured evidence for one mod scan.

        Args:
            root: The scan root owning the published evidence report.
            report: The completed native scan being published.
            publication: The publication declaration naming the report.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanEvidenceReceipt]``.

        """
        evidence = FlextInfraUtilitiesRefactor.mod_scan_evidence(
            root, report, publication=publication
        )
        return FlextInfraUtilitiesRefactor.publish_mod_scan_evidence_receipt(
            root, evidence, publication=publication
        )

    @staticmethod
    def mod_scan_evidence(
        root: Path,
        report: m.Infra.ModScanReport,
        *,
        publication: m.Infra.ModScanPublication,
    ) -> m.Infra.ModScanEvidence:
        """Normalize live scan references through the canonical closed inventory.

        Returns:
            The persistent audit contract, not live operational epoch handles.

        Raises:
            ValueError: When a native finding lacks its authenticated artifact.

        """
        repository_totals = Counter(dict.fromkeys(publication.repositories, 0))
        rule_totals = Counter(dict.fromkeys(publication.rule_ids, 0))
        class_totals = Counter(dict.fromkeys(c.Infra.ModScanFindingClass, 0))
        for entry in report.entries:
            if entry.native_receipt is None:
                msg = "mod evidence finding lacks its native artifact"
                raise ValueError(msg)
            repository_totals[entry.repository] += 1
            rule_totals[entry.rule_id] += 1
            class_totals[entry.classification] += 1
        artifacts = {
            artifact.path: index
            for index, artifact in enumerate(report.native_artifacts)
        }
        references: list[m.Infra.ModScanFindingReference] = []
        for entry in report.entries:
            if entry.native_receipt is None:
                msg = f"mod evidence finding lacks its native artifact: {entry.file}"
                raise ValueError(msg)
            references.append(
                m.Infra.ModScanFindingReference(
                    **entry.model_dump(exclude_computed_fields=True),
                    source_path=(
                        entry.source_state.path
                        if entry.source_state is not None
                        else None
                    ),
                    native_artifact=artifacts[entry.native_receipt.path],
                )
            )
        return m.Infra.ModScanEvidence.model_validate({
            "schema_version": c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
            "native_artifacts": report.native_artifacts,
            "inputs": FlextInfraUtilitiesRefactor.mod_scan_inputs(report),
            c.HandlerMode.COMMAND: publication.command,
            "root": root.resolve(),
            "scope": tuple(publication.scope),
            "totals_by_class": class_totals,
            "totals_by_repository": dict(sorted(repository_totals.items())),
            "totals_by_rule": dict(sorted(rule_totals.items())),
            "entries": tuple(references),
        })

    @staticmethod
    def publish_mod_scan_evidence_receipt(
        root: Path,
        evidence: m.Infra.ModScanEvidence,
        *,
        publication: m.Infra.ModScanPublication,
    ) -> p.Result[m.Infra.ModScanEvidenceReceipt]:
        """Publish the same normalized evidence used by read-only audit snapshots.

        Returns:
            The canonical atomic publication receipt and its validated payload.

        """
        if (
            evidence.root != root.resolve()
            or evidence.scope != tuple(publication.scope)
            or evidence.command != publication.command
            or set(evidence.totals_by_repository)
            != set(publication.repositories)
            | {entry.repository for entry in evidence.entries}
            or set(evidence.totals_by_rule)
            != set(publication.rule_ids) | {entry.rule_id for entry in evidence.entries}
        ):
            return r[m.Infra.ModScanEvidenceReceipt].fail(
                "normalized scan evidence differs from its publication declaration"
            )
        content = (
            evidence.model_dump_json(
                indent=2, exclude=set(type(evidence).model_computed_fields)
            )
            + "\n"
        ).encode(c.DEFAULT_ENCODING)
        report_path = root.resolve() / publication.relative_path
        published = FlextInfraUtilitiesRefactor._published_mod_scan_bytes(
            report_path,
            content,
        )
        if published.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(published)
        return r[m.Infra.ModScanEvidenceReceipt].ok(
            m.Infra.ModScanEvidenceReceipt(
                path=report_path,
                sha256=u.Cli.sha256_bytes(content),
                evidence=evidence,
            ),
        )

    @staticmethod
    def _published_mod_scan_bytes(
        report_path: Path,
        content: bytes,
    ) -> p.Result[bool]:
        """Atomically publish one mod scan report and verify its bytes.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        prepared = u.Cli.ensure_dir(report_path.parent)
        if prepared.failure:
            return r[bool].from_failure(prepared)
        before = u.Cli.atomic_read_binary_file_state(report_path, required=False)
        if before.failure:
            return r[bool].from_failure(before)
        written = u.Cli.atomic_write_binary_file_guarded(
            before.value,
            content,
            permission_mode=c.Infra.MOD_SCAN_REPORT_MODE,
        )
        if written.failure:
            return r[bool].from_failure(written)
        published = u.Cli.atomic_read_binary_file_state(report_path, required=True)
        if published.failure:
            return r[bool].from_failure(published)
        if (
            published.value.content != content
            or published.value.mode != c.Infra.MOD_SCAN_REPORT_MODE
        ):
            return r[bool].fail(
                f"published mod evidence differs from planned bytes: {report_path}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def refactor_report_evidence_root(root: Path) -> p.Result[Path]:
        """Elect the existing Git control plane without mutating source inputs.

        Returns:
            The exact worktree Git directory, or the original identity failure.

        """
        return FlextInfraUtilitiesGitSemanticIdentity.exact_worktree_git_dir(root)

    @staticmethod
    def publish_refactor_report_evidence(
        root: Path,
        report: m.ContractModel | m.ArbitraryTypesModel,
        *,
        relative_path: Path,
    ) -> p.Result[Path]:
        """Atomically publish one refactor verb's structured report receipt.

        Mirrors the mod evidence receipt's write discipline (ensure directory,
        guarded atomic write, byte-exact read-back) for the refactor verbs that
        own a single report document. Persist reconstructable facts; computed
        views are derived by the typed report consumer.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        content = (report.model_dump_json(indent=2, round_trip=True) + "\n").encode(
            c.DEFAULT_ENCODING,
        )
        storage = FlextInfraUtilitiesRefactor.refactor_report_evidence_root(root)
        if storage.failure:
            return r[Path].from_failure(storage)
        report_path = storage.value / relative_path
        return FlextInfraUtilitiesRefactor._published_mod_scan_bytes(
            report_path, content
        ).map(lambda _published: report_path)


__all__: list[str] = ["FlextInfraUtilitiesRefactor"]
