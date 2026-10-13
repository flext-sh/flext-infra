"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from itertools import chain
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)


class FlextInfraUtilitiesRefactor:
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

    @staticmethod
    def violations_totals(report: m.Infra.ModScanReport) -> m.Infra.ViolationsTotals:
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
    def rule_deltas(
        before: m.Infra.ModScanReport | m.Infra.ModTextReport,
        after: m.Infra.ModScanReport | m.Infra.ModTextReport,
        *,
        inventory: tuple[tuple[str, str], ...] = (),
        repository_root: Path | None = None,
        projects: t.SequenceOf[Path] = (),
        publication_chain: tuple[m.Infra.CodegenStagedFile, ...] | None = None,
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare lexical occurrences, or prove module absence through publication.

        Without a publication chain the comparison is explicitly lexical. A supplied
        chain is never replaced by guessed correspondence when authentication fails.

        Returns:
            Per-repository and per-rule occurrence deltas.

        Raises:
            ValueError: Native engines differ or a text finding lacks project ownership.
        """
        engine = "ast-grep" if isinstance(before, m.Infra.ModScanReport) else "text"
        if isinstance(before, m.Infra.ModScanReport) != isinstance(
            after, m.Infra.ModScanReport
        ):
            msg = "rule comparison requires the same native engine"
            raise ValueError(msg)
        endpoints: dict[Path, tuple[m.Cli.AtomicFileState, m.Cli.AtomicFileState]] = {}
        sources: list[dict[Path, m.Cli.AtomicFileState]] = []
        if publication_chain is not None:
            if not isinstance(before, m.Infra.ModScanReport) or not isinstance(
                after, m.Infra.ModScanReport
            ):
                msg = "semantic correspondence requires native AST findings"
                raise ValueError(msg)
            catalog: dict[tuple[str, str], tuple[str | None, bool]] = {}
            for report in (before, after):
                if report.source_states is None:
                    msg = "semantic correspondence lacks complete source inventory"
                    raise ValueError(msg)
                indexed: dict[Path, m.Cli.AtomicFileState] = {}
                for state in report.source_states:
                    if indexed.setdefault(state.path, state) != state:
                        msg = f"scan inventory identity disagrees: {state.path}"
                        raise ValueError(msg)
                for entry in report.entries:
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
                        msg = (f"finding differs from complete scan inventory: "
                               f"{entry.file}")
                        raise ValueError(msg)
                sources.append(indexed)
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
            for path in sorted(
                sources[0].keys() | sources[1].keys() | endpoints.keys()
            ):
                original, final = endpoints.get(
                    path, (sources[0].get(path), sources[0].get(path))
                )
                expected_before = (
                    original
                    if original is not None and original.content is not None
                    else None
                )
                if (
                    sources[0].get(path) != expected_before
                    or sources[1].get(path) != final
                ):
                    cause = (
                        "original source identity drift"
                        if sources[0].get(path) != expected_before
                        else "unexplained removal"
                        if sources[1].get(path) is None
                        else "final source identity drift"
                    )
                    msg = f"publication {cause}: {path}"
                    raise ValueError(msg)
        proven: set[tuple[str, str]] = set()
        topology = sorted(projects, key=lambda item: len(item.parts), reverse=True)
        counters: t.ListOf[
            t.MutableMappingKV[t.Pair[str, str], t.MutableMappingKV[t.Pair[str, str], int]]
        ] = []
        indexes: t.ListOf[t.MutableMappingKV[t.Pair[str, str], t.ListOf[int]]] = []
        for report in (before, after):
            occurrences: t.MutableMappingKV[
                t.Pair[str, str], t.MutableMappingKV[t.Pair[str, str], int]
            ] = defaultdict(Counter)
            positions: t.MutableMappingKV[t.Pair[str, str], t.ListOf[int]] = defaultdict(list)
            for index, entry in enumerate(report.entries):
                if isinstance(entry, m.Infra.ModScanFinding):
                    repository = entry.repository
                else:
                    if repository_root is None:
                        msg = "text comparison requires declared project topology"
                        raise ValueError(msg)
                    path = (repository_root / entry.file).resolve()
                    owner = next(
                        (
                            project
                            for project in topology
                            if path.is_relative_to(project)
                        ),
                        None,
                    )
                    if owner is None:
                        msg = f"text finding outside declared topology: {entry.file}"
                        raise ValueError(msg)
                    repository = owner.name
                text = entry.text
                if (
                    publication_chain is not None
                    and isinstance(entry, m.Infra.ModScanFinding)
                    and entry.module_absence
                ):
                    state = entry.source_state
                    offsets = entry.range.get("byteOffset")
                    if (
                        state is None
                        or state.content is None
                        or not entry.catalog_digest
                    ):
                        msg = f"module occurrence lacks authentication: {entry.file}"
                        raise ValueError(msg)
                    if not isinstance(offsets, Mapping):
                        msg = f"module occurrence lacks native range: {entry.file}"
                        raise ValueError(msg)
                    start, end = offsets.get("start"), offsets.get("end")
                    # The Python module predicate owns the root; spans may omit trivia.
                    if (
                        not isinstance(start, int)
                        or isinstance(start, bool)
                        or not isinstance(end, int)
                        or isinstance(end, bool)
                        or not 0 <= start <= end <= len(state.content)
                        or state.content[start:end]
                        != entry.text.encode(c.DEFAULT_ENCODING)
                    ):
                        msg = f"module occurrence is not the native root: {entry.file}"
                        raise ValueError(msg)
                    text = f"module-absence:{entry.catalog_digest}"
                    proven.add((repository, entry.rule_id))
                key = (repository, entry.rule_id)
                occurrences[key][str(entry.file), text] += 1
                positions[key].append(index)
            counters.append(occurrences)
            indexes.append(positions)
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
            cause = stage.error or "native audit snapshot unavailable"
            return stage.model_copy(
                update={
                    "error": cause,
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
                            error=cause,
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
                            cause=cause,
                        )
                        for engine in ("ast-grep", "text", "ruff", "census")
                    ),
                }
            )
        before, after = stage.audit_before, stage.audit_after
        elected = before.plan.project_rule_ids.get(project.resolve())
        topology = sorted(
            before.repository_roots, key=lambda item: len(item.parts), reverse=True
        )
        has_sources = any(
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
                inventory=tuple(
                    (project.name, rule_id) for rule_id in elected or () if has_sources
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
                repository_root=stage.repository_root,
                projects=before.repository_roots,
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
        ast_observed = (
            before.source_verified
            and after.source_verified
            and has_sources
            and elected is not None
            and before.ast_report is not None
            and after.ast_report is not None
        )
        lint_failures = tuple(
            f"{path}: {error}"
            for snapshot in (before, after)
            for path, receipt in (snapshot.lint or {}).items()
            for error in FlextInfraUtilitiesProtectedEditLinting.lint_execution_errors(
                receipt
            )
        )
        coverage = (
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
    def publish_mod_scan_evidence(
        root: Path,
        report: m.Infra.ModScanReport,
        *,
        publication: m.Infra.ModScanPublication,
    ) -> p.Result[m.Infra.ModScanEvidenceReceipt]:
        """Atomically replace the complete structured evidence for one mod scan.

        Returns:
            The resulting ``p.Result[m.Infra.ModScanEvidenceReceipt]``.

        """
        repository_totals = Counter(dict.fromkeys(publication.repositories, 0))
        rule_totals = Counter(dict.fromkeys(publication.rule_ids, 0))
        class_totals = Counter(dict.fromkeys(c.Infra.ModScanFindingClass, 0))
        for entry in report.entries:
            repository_totals[entry.repository] += 1
            rule_totals[entry.rule_id] += 1
            class_totals[entry.classification] += 1
        evidence = m.Infra.ModScanEvidence.model_validate({
            "schema_version": c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
            "inputs": m.Infra.CodemodBindingSnapshot(
                states=tuple(
                    chain(
                        report.source_states or (),
                        (
                            entry.source_state
                            for entry in report.entries
                            if entry.source_state is not None
                        ),
                        chain.from_iterable(
                            {
                                id(entry.binding_states): entry.binding_states
                                for entry in report.entries
                            }.values()
                        ),
                    )
                )
            ),
            "command": publication.command,
            "root": root.resolve(),
            "scope": tuple(publication.scope),
            "totals_by_class": class_totals,
            "totals_by_repository": dict(sorted(repository_totals.items())),
            "totals_by_rule": dict(sorted(rule_totals.items())),
            "entries": tuple(
                m.Infra.ModScanFindingReference(
                    **{name: getattr(entry, name) for name in type(entry).model_fields},
                    source_path=(
                        entry.source_state.path
                        if entry.source_state is not None
                        else None
                    ),
                    binding_paths=tuple(state.path for state in entry.binding_states),
                )
                for entry in report.entries
            ),
        })
        content = (
            evidence.model_dump_json(
                indent=2, exclude=set(type(evidence).model_computed_fields)
            )
            + "\n"
        ).encode(
            c.DEFAULT_ENCODING,
        )
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
