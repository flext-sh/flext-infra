"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Generator, Mapping
from contextlib import ExitStack, contextmanager
from itertools import chain
from pathlib import Path
from typing import ClassVar, Protocol

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)


class _RuleDeltaOptions(m.ArbitraryTypesModel):
    """Optional scope and authentication inputs for one rule delta comparison."""

    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    inventory: t.VariadicTuple[t.Pair[str, str]] = m.Field(
        default=(),
        description="Declared repository and rule pairs included in the delta.",
    )
    repository_root: Path | None = m.Field(
        default=None,
        description="Root resolving text finding paths into the topology.",
    )
    projects: t.SequenceOf[Path] = m.Field(
        default=(),
        description="Declared project topology owning text findings.",
    )
    publication_chain: t.VariadicTuple[m.Infra.CodegenStagedFile] | None = m.Field(
        default=None,
        description="Authenticated staged publication receipts.",
    )


class _RuleDeltaSpec(Protocol):
    """Read-only structural contract for rule delta comparison options."""

    @property
    def inventory(self) -> t.VariadicTuple[t.Pair[str, str]]: ...

    @property
    def repository_root(self) -> Path | None: ...

    @property
    def projects(self) -> t.SequenceOf[Path]: ...

    @property
    def publication_chain(
        self,
    ) -> t.VariadicTuple[m.Infra.CodegenStagedFile] | None: ...


_EMPTY_RULE_DELTA_OPTIONS = _RuleDeltaOptions()


class FlextInfraUtilitiesRefactor:
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

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
    ) -> Generator[t.MappingKV[Path, p.Cli.AtomicFileReader]]:
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
        readers: t.MappingKV[Path, p.Cli.AtomicFileReader],
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
        payload = u.Cli.json_loads(content).unwrap()
        hydrated = isinstance(payload, Mapping)
        if not hydrated:
            msg = "mod native record is not a JSON object"
            raise ValueError(msg)
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
        report: m.Infra.ModOccurrenceReport[FindingT],
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
    def _indexed_source_states[FindingT: m.Infra.ModOccurrence](
        report: m.Infra.ModOccurrenceReport[FindingT],
    ) -> dict[Path, m.Cli.AtomicFileState]:
        """Index one report's captured source states by path.

        Args:
            report: Completed native scan owning the captured states.

        Returns:
            Source states indexed exactly once per path.

        Raises:
            ValueError: When the scan lacks a complete source inventory or
                two captured states disagree for one path.
        """
        if report.source_states is None:
            msg = "semantic correspondence lacks complete source inventory"
            raise ValueError(msg)
        indexed: dict[Path, m.Cli.AtomicFileState] = {}
        for state in report.source_states:
            if indexed.setdefault(state.path, state) != state:
                msg = f"scan inventory identity disagrees: {state.path}"
                raise ValueError(msg)
        return indexed

    @staticmethod
    def _admit_scan_entry(
        entry: m.Infra.ModOccurrence,
        catalog: dict[tuple[str, str], tuple[str | None, bool]],
        indexed: dict[Path, m.Cli.AtomicFileState],
    ) -> None:
        """Admit one scan finding against the established catalog correspondence.

        Args:
            entry: Native scan finding being admitted.
            catalog: Established repository and rule catalog correspondence.
            indexed: The report's source states indexed by path.

        Raises:
            ValueError: When the catalog correspondence changed or the
                finding differs from the complete scan inventory.
        """
        key = (entry.repository, entry.rule_id)
        descriptor = (entry.catalog_digest, entry.module_absence)
        if (
            not entry.catalog_digest
            or catalog.setdefault(key, descriptor) != descriptor
        ):
            msg = f"native catalog correspondence changed: {key}"
            raise ValueError(msg)
        if (
            entry.source_state is None
            or indexed.get(entry.source_state.path) != entry.source_state
        ):
            msg = f"finding differs from complete scan inventory: {entry.file}"
            raise ValueError(msg)

    @staticmethod
    def _publication_endpoints(
        publication_chain: tuple[m.Infra.CodegenStagedFile, ...],
    ) -> dict[Path, tuple[m.Cli.AtomicFileState, m.Cli.AtomicFileState]]:
        """Fold the publication chain into per-path before/after endpoints.

        Args:
            publication_chain: Authenticated staged publication receipts.

        Returns:
            Before and after file endpoints for every published path.

        Raises:
            ValueError: When publication identity continuity is broken or a
                receipt is not an admitted destination.
        """
        endpoints: dict[Path, tuple[m.Cli.AtomicFileState, m.Cli.AtomicFileState]] = {}
        for receipt in publication_chain:
            path = receipt.before.path
            previous = endpoints.get(path)
            if previous is not None and previous[1] != receipt.before:
                msg = f"publication identity continuity broken: {path}"
                raise ValueError(msg)
            if receipt.replacement is None or receipt.replacement.path != path:
                msg = f"publication receipt is not an admitted destination: {path}"
                raise ValueError(msg)
            endpoints[path] = (
                previous[0] if previous else receipt.before,
                receipt.replacement,
            )
        return endpoints

    @staticmethod
    def _admit_publication_identity(
        sources: t.SequenceOf[dict[Path, m.Cli.AtomicFileState]],
        endpoints: dict[Path, tuple[m.Cli.AtomicFileState, m.Cli.AtomicFileState]],
    ) -> None:
        """Prove each path's original and final source identity.

        Args:
            sources: Before and after source states indexed by path.
            endpoints: Before and after file endpoints per published path.

        Raises:
            ValueError: When the original or final source identity drifted,
                or a source was removed without authenticated provenance.
        """
        for path in sorted(sources[0].keys() | sources[1].keys() | endpoints.keys()):
            original, final = endpoints.get(
                path, (sources[0].get(path), sources[0].get(path))
            )
            expected_before = (
                original
                if original is not None and original.content is not None
                else None
            )
            if sources[0].get(path) != expected_before or sources[1].get(path) != final:
                cause = (
                    "original source identity drift"
                    if sources[0].get(path) != expected_before
                    else "unexplained removal"
                    if sources[1].get(path) is None
                    else "final source identity drift"
                )
                msg = f"publication {cause}: {path}"
                raise ValueError(msg)

    @classmethod
    def _authenticated_endpoints[FindingT: m.Infra.ModOccurrence](
        cls,
        before: m.Infra.ModOccurrenceReport[FindingT],
        after: m.Infra.ModOccurrenceReport[FindingT],
        publication_chain: tuple[m.Infra.CodegenStagedFile, ...],
    ) -> t.Pair[
        list[dict[Path, m.Cli.AtomicFileState]],
        dict[Path, tuple[m.Cli.AtomicFileState, m.Cli.AtomicFileState]],
    ]:
        """Authenticate scan inventories and the staged publication chain.

        Args:
            before: Baseline native report claiming provenance.
            after: Final native report claiming provenance.
            publication_chain: Authenticated staged publication receipts.

        Returns:
            The indexed source inventories and the publication endpoints.
        """
        sources: list[dict[Path, m.Cli.AtomicFileState]] = []
        catalog: dict[tuple[str, str], tuple[str | None, bool]] = {}
        for report in (before, after):
            indexed = cls._indexed_source_states(report)
            for entry in report.entries:
                cls._admit_scan_entry(entry, catalog, indexed)
            sources.append(indexed)
        endpoints = cls._publication_endpoints(publication_chain)
        cls._admit_publication_identity(sources, endpoints)
        return sources, endpoints

    @staticmethod
    def _finding_repository(
        entry: m.Infra.ModOccurrence | m.Infra.ModTextFinding,
        repository_root: Path | None,
        topology: t.SequenceOf[Path],
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

    @staticmethod
    def _admit_module_absence_state(
        entry: m.Infra.ModOccurrence,
    ) -> m.Cli.AtomicFileState:
        """Admit one module-absence finding's captured authentication.

        Args:
            entry: Native scan finding carrying the absence authentication.

        Returns:
            The captured source state backing the absence.

        Raises:
            ValueError: When the module occurrence lacks authentication.
        """
        state = entry.source_state
        if state is None or state.content is None or not entry.catalog_digest:
            msg = f"module occurrence lacks authentication: {entry.file}"
            raise ValueError(msg)
        return state

    @staticmethod
    def _module_absence_root(
        entry: m.Infra.ModOccurrence,
        state: m.Cli.AtomicFileState,
        repository: str,
        proven: set[tuple[str, str]],
        byte_offsets: t.JsonMapping,
    ) -> str:
        """Authenticate one module-absence root span and return its lexical text.

        Args:
            entry: Native scan finding carrying the absence authentication.
            state: The captured source state admitted for the finding.
            repository: Resolved repository owner of the finding.
            proven: Repository and rule pairs proven absent, updated in place.
            byte_offsets: The finding's validated native byte-offset mapping.

        Returns:
            The lexical occurrence text standing in for the absent module.

        Raises:
            ValueError: When the module occurrence is not the native root.
        """
        start, end = byte_offsets.get("start"), byte_offsets.get("end")
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            msg = f"module occurrence is not the native root: {entry.file}"
            raise ValueError(msg)
        content = state.content
        if (
            content is None
            or not 0 <= start <= end <= len(content)
            or content[start:end] != entry.text.encode(c.DEFAULT_ENCODING)
        ):
            msg = f"module occurrence is not the native root: {entry.file}"
            raise ValueError(msg)
        proven.add((repository, entry.rule_id))
        return f"module-absence:{entry.catalog_digest}"

    @classmethod
    def _report_occurrence_indexes(
        cls,
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence]
        | m.Infra.ModTextReport,
        repository_root: Path | None,
        topology: t.SequenceOf[Path],
        proven: set[tuple[str, str]],
        publication_chain: tuple[m.Infra.CodegenStagedFile, ...] | None,
    ) -> t.Pair[
        t.MutableMappingKV[t.Pair[str, str], t.MutableMappingKV[t.Pair[str, str], int]],
        t.MutableMappingKV[t.Pair[str, str], t.ListOf[int]],
    ]:
        """Count one report's lexical occurrences and entry positions.

        Args:
            report: Native report whose entries are counted.
            repository_root: Root resolving text finding paths into the
                declared topology.
            topology: Declared project topology ordered by path depth.
            proven: Repository and rule pairs proven absent, updated in place.
            publication_chain: Publication chain activating absence proof.

        Returns:
            The occurrence counter and entry position index per repository
            and rule key.

        Raises:
            ValueError: When a text finding lacks project ownership or a
                module absence lacks authentication or a native range.
        """
        occurrences: t.MutableMappingKV[
            t.Pair[str, str], t.MutableMappingKV[t.Pair[str, str], int]
        ] = defaultdict(Counter)
        positions: t.MutableMappingKV[t.Pair[str, str], t.ListOf[int]] = defaultdict(
            list
        )
        for index, entry in enumerate(report.entries):
            repository = cls._finding_repository(entry, repository_root, topology)
            text = entry.text
            if (
                publication_chain is not None
                and isinstance(entry, m.Infra.ModOccurrence)
                and entry.module_absence
            ):
                state = cls._admit_module_absence_state(entry)
                byte_offsets = entry.range.get("byteOffset")
                if not isinstance(byte_offsets, Mapping):
                    msg = f"module occurrence lacks native range: {entry.file}"
                    raise ValueError(msg)
                text = cls._module_absence_root(
                    entry, state, repository, proven, byte_offsets
                )
            key = (repository, entry.rule_id)
            occurrences[key][str(entry.file), text] += 1
            positions[key].append(index)
        return occurrences, positions

    @staticmethod
    def _rule_delta_rows(
        engine: str,
        counters: t.SequenceOf[
            t.MutableMappingKV[
                t.Pair[str, str], t.MutableMappingKV[t.Pair[str, str], int]
            ]
        ],
        indexes: t.SequenceOf[t.MutableMappingKV[t.Pair[str, str], t.ListOf[int]]],
        inventory: tuple[tuple[str, str], ...],
        proven: set[tuple[str, str]],
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Build the per-repository and per-rule occurrence deltas.

        Args:
            engine: Native engine name shared by both measured reports.
            counters: Before and after occurrence counters per rule key.
            indexes: Before and after entry position indexes per rule key.
            inventory: Declared repository and rule pairs included.
            proven: Repository and rule pairs with proven absence.

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
                    semantic_correspondence_proven=key in proven,
                    before_entries=tuple(indexes[0][key]),
                    after_entries=tuple(indexes[1][key]),
                )
            )
        return tuple(deltas)

    @staticmethod
    def rule_deltas[FindingT: m.Infra.ModOccurrence](
        before: m.Infra.ModOccurrenceReport[FindingT] | m.Infra.ModTextReport,
        after: m.Infra.ModOccurrenceReport[FindingT] | m.Infra.ModTextReport,
        *,
        options: _RuleDeltaSpec = _EMPTY_RULE_DELTA_OPTIONS,
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare lexical occurrences, or prove module absence through publication.

        Without a publication chain the comparison is explicitly lexical. A supplied
        chain is never replaced by guessed correspondence when authentication fails.

        Args:
            before: Baseline native report from the measured engine.
            after: Final native report from the same engine.
            options: Frozen scope and authentication options for the delta.

        Returns:
            Per-repository and per-rule occurrence deltas.

        Raises:
            ValueError: Native engines differ, a text finding lacks project
                ownership, or the publication chain fails authentication.
        """
        engine = (
            "ast-grep" if isinstance(before, m.Infra.ModOccurrenceReport) else "text"
        )
        if isinstance(before, m.Infra.ModOccurrenceReport) != isinstance(
            after, m.Infra.ModOccurrenceReport
        ):
            msg = "rule comparison requires the same native engine"
            raise ValueError(msg)
        publication_chain = options.publication_chain
        if publication_chain is not None:
            if not isinstance(before, m.Infra.ModOccurrenceReport) or not isinstance(
                after, m.Infra.ModOccurrenceReport
            ):
                msg = "semantic correspondence requires native AST findings"
                raise ValueError(msg)
            FlextInfraUtilitiesRefactor._authenticated_endpoints(
                before, after, publication_chain
            )
        proven: set[tuple[str, str]] = set()
        topology = sorted(
            options.projects, key=lambda item: len(item.parts), reverse=True
        )
        measured = [
            FlextInfraUtilitiesRefactor._report_occurrence_indexes(
                report,
                options.repository_root,
                topology,
                proven,
                publication_chain,
            )
            for report in (before, after)
        ]
        return FlextInfraUtilitiesRefactor._rule_delta_rows(
            engine,
            [occurrences for occurrences, _positions in measured],
            [positions for _occurrences, positions in measured],
            options.inventory,
            proven,
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
        lint_failures: t.SequenceOf[str],
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
                status="incomplete"
                if before.text_report is not None and after.text_report is not None
                else "NOT_EXECUTED",
                cause=(
                    "native text report lacks effective per-project "
                    "zero-rule audit metadata"
                ),
            ),
            m.Infra.ViolationsEngineCoverage(
                repository=project.name,
                engine="ruff",
                status="incomplete"
                if before.lint is not None and after.lint is not None
                else "NOT_EXECUTED",
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
                options=_RuleDeltaOptions(
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
                options=_RuleDeltaOptions(
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
    def string_list(value: t.JsonValue | None) -> t.StrSequence:
        """Normalize policy fields that should contain string collections.

        Returns:
            The resulting ``t.StrSequence``.

        Raises:
            TypeError: If expected list value.

        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        validated: p.Result[t.StrSequence] = u.validate_value(
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
        results: t.SequenceOf[m.Infra.Result],
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
        normalized_payload: t.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_python(
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
        """Union captured sources and distinct binding graphs once per operation.

        Args:
            report: Completed mod scan whose entries carry captured states.

        Returns:
            One binding snapshot uniting the report's source states with each
            distinct captured binding state.
        """
        bindings = {
            id(entry.binding_states): entry.binding_states for entry in report.entries
        }
        return m.Infra.CodemodBindingSnapshot(
            states=tuple(
                chain(
                    report.source_states or (),
                    (
                        entry.source_state
                        for entry in report.entries
                        if entry.source_state is not None
                    ),
                    chain.from_iterable(bindings.values()),
                )
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

        Raises:
            ValueError: When the report lacks a captured native artifact.
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
        bindings = {
            id(entry.binding_states): entry.binding_states for entry in report.entries
        }
        binding_paths = {
            identity: tuple(state.path for state in states)
            for identity, states in bindings.items()
        }
        graphs = {
            paths: index
            for index, paths in enumerate(dict.fromkeys(binding_paths.values()))
        }
        graph_ids = {
            identity: graphs[paths] for identity, paths in binding_paths.items()
        }
        artifacts = {
            artifact.path: index
            for index, artifact in enumerate(report.native_artifacts)
        }
        evidence = m.Infra.ModScanEvidence.model_validate({
            "schema_version": c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
            "binding_graphs": tuple(graphs),
            "native_artifacts": report.native_artifacts,
            "inputs": FlextInfraUtilitiesRefactor.mod_scan_inputs(report),
            "command": publication.command,
            "root": root.resolve(),
            "scope": tuple(publication.scope),
            "totals_by_class": class_totals,
            "totals_by_repository": dict(sorted(repository_totals.items())),
            "totals_by_rule": dict(sorted(rule_totals.items())),
            "entries": tuple(
                m.Infra.ModScanFindingReference(
                    **entry.model_dump(exclude_computed_fields=True),
                    source_path=(
                        entry.source_state.path
                        if entry.source_state is not None
                        else None
                    ),
                    binding_graph=graph_ids[id(entry.binding_states)],
                    native_artifact=artifacts[entry.native_receipt.path],
                )
                for entry in report.entries
            ),
        })
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
        report_path = root.resolve() / relative_path
        return FlextInfraUtilitiesRefactor._published_mod_scan_bytes(
            report_path, content
        ).map(lambda _published: report_path)


__all__: list[str] = ["FlextInfraUtilitiesRefactor"]
