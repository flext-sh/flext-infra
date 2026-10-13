"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from collections.abc import MutableMapping
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
            actionable=report.actionable,
            detection_only=report.detection_only,
            non_actionable_with_fix=report.non_actionable_with_fix,
        )

    @staticmethod
    def rule_deltas(
        before: m.Infra.ModScanReport | m.Infra.ModTextReport,
        after: m.Infra.ModScanReport | m.Infra.ModTextReport,
        *,
        inventory: tuple[tuple[str, str], ...] = (),
        repository_root: Path | None = None,
        projects: t.SequenceOf[Path] = (),
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare lexical multiplicities, without asserting semantic correspondence.

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
        snapshots: list[list[tuple[str, str, str, str]]] = []
        for report in (before, after):
            identities: list[tuple[str, str, str, str]] = []
            for entry in report.entries:
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
                            for project in sorted(
                                projects, key=lambda item: len(item.parts), reverse=True
                            )
                            if path.is_relative_to(project)
                        ),
                        None,
                    )
                    if owner is None:
                        msg = f"text finding outside declared topology: {entry.file}"
                        raise ValueError(msg)
                    repository = owner.name
                identities.append((
                    repository,
                    entry.rule_id,
                    str(entry.file),
                    entry.text,
                ))
            snapshots.append(identities)
        before_entries, after_entries = (Counter(entries) for entries in snapshots)
        deltas: list[m.Infra.ViolationsRuleDelta] = []
        for repository, rule_id in sorted(
            set(inventory) | {key[:2] for key in before_entries | after_entries}
        ):
            keys = {
                key
                for key in before_entries | after_entries
                if key[:2] == (repository, rule_id)
            }
            persisted = sum(
                min(before_entries[key], after_entries[key]) for key in keys
            )
            before_count = sum(before_entries[key] for key in keys)
            after_count = sum(after_entries[key] for key in keys)
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
                    before_entries=tuple(
                        index
                        for index, key in enumerate(snapshots[0])
                        if key[:2] == (repository, rule_id)
                    ),
                    after_entries=tuple(
                        index
                        for index, key in enumerate(snapshots[1])
                        if key[:2] == (repository, rule_id)
                    ),
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
        has_sources = any(
            next(
                (
                    candidate
                    for candidate in sorted(
                        before.repository_roots,
                        key=lambda item: len(item.parts),
                        reverse=True,
                    )
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
        text_deltas = (
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
            for row in text_deltas
            if row.repository == project.name
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
            for error in FlextInfraUtilitiesProtectedEditLinting.lint_execution_errors(receipt)
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
        introduced = (
            FlextInfraUtilitiesRefactor.text_introduced_findings(
                before.text_report,
                after.text_report,
            )
            if before.text_report is not None and after.text_report is not None
            else None
        )
        unchanged = (
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
                            not unchanged and stage.verb in {"audit", "audit-rules"},
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
                            any(row.introduced for row in (*deltas, *text_deltas))
                            or any(lint.values())
                            or bool(introduced),
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
                "rule_evaluations": evaluations,
                "engine_coverage": coverage,
                "introduced_lint": (
                    lint if before.lint is not None and after.lint is not None else None
                ),
                "introduced_text": introduced,
                "source_inventory_unchanged": unchanged,
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
        totals = FlextInfraUtilitiesRefactor._validated_mod_scan_totals(report)
        if totals.failure:
            return r[m.Infra.ModScanEvidenceReceipt].from_failure(totals)
        repository_totals, rule_totals, class_totals = totals.value
        repository_totals = (
            dict.fromkeys(publication.repositories, 0) | repository_totals
        )
        rule_totals = dict.fromkeys(publication.rule_ids, 0) | rule_totals
        evidence = m.Infra.ModScanEvidence(
            schema_version=c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
            command=publication.command,
            root=root.resolve(),
            scope=tuple(publication.scope),
            findings=report.findings,
            actionable=report.actionable,
            detection_only=report.detection_only,
            non_actionable_with_fix=report.non_actionable_with_fix,
            totals_by_class=class_totals,
            totals_by_repository=dict(sorted(repository_totals.items())),
            totals_by_rule=dict(sorted(rule_totals.items())),
            entries=report.entries,
        )
        content = (evidence.model_dump_json(indent=2) + "\n").encode(
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
    def _validated_mod_scan_totals(
        report: m.Infra.ModScanReport,
    ) -> p.Result[
        t.Triple[
            MutableMapping[str, int],
            MutableMapping[str, int],
            MutableMapping[c.Infra.ModScanFindingClass, int],
        ]
    ]:
        """Validate one report's classification invariant and count its totals.

        Returns:
            The resulting ``p.Result`` of repository, rule, and class totals.

        """
        result_type = r[
            t.Triple[
                MutableMapping[str, int],
                MutableMapping[str, int],
                MutableMapping[c.Infra.ModScanFindingClass, int],
            ]
        ]
        classified = (
            report.actionable
            + report.detection_only
            + report.non_actionable_with_fix
            + report.deferred
        )
        if classified != report.findings or report.findings != len(report.entries):
            return result_type.fail(
                "mod scan classification invariant failed: "
                f"findings={report.findings} entries={len(report.entries)} "
                f"classified={classified}",
            )
        repository_totals: MutableMapping[str, int] = {}
        rule_totals: MutableMapping[str, int] = {}
        class_totals: MutableMapping[c.Infra.ModScanFindingClass, int] = dict.fromkeys(
            c.Infra.ModScanFindingClass,
            0,
        )
        for finding in report.entries:
            repository_totals[finding.repository] = (
                repository_totals.get(finding.repository, 0) + 1
            )
            rule_totals[finding.rule_id] = rule_totals.get(finding.rule_id, 0) + 1
            class_totals[finding.classification] += 1
        expected_class_totals = {
            c.Infra.ModScanFindingClass.ACTIONABLE: report.actionable,
            c.Infra.ModScanFindingClass.DETECTION_ONLY: report.detection_only,
            c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX: (
                report.non_actionable_with_fix
            ),
            c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT: report.deferred,
        }
        if class_totals != expected_class_totals:
            return result_type.fail(
                "mod scan entry classification differs from report totals: "
                f"entries={class_totals} report={expected_class_totals}",
            )
        return result_type.ok((repository_totals, rule_totals, class_totals))

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
