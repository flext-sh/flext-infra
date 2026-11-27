"""Finding validation, classification, and JSONL parsing for codemods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import closing
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod._gates import FlextInfraModGateRunner


class FlextInfraModGateFindings(FlextInfraModGateRunner):
    """Validate and classify ast-grep JSONL findings and expected receipts."""

    @staticmethod
    def _validate_finding_receipt(
        stderr: p.Cli.AtomicFileReceipt, errors: int
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

    @classmethod
    def _elected(
        cls,
        root: Path,
        report: p.Infra.ModScanReport,
        rules_by_id: Mapping[str, p.Infra.CodemodRule],
        project_rule_ids: Mapping[Path, Sequence[str]],
    ) -> p.Infra.ModScanReport:
        """Keep each source's findings of its nearest governed project's plan.

        Returns:
            The elected findings, grouped by owning project, recounted.

        """
        elected = {
            project: frozenset(rule_ids)
            for project, rule_ids in project_rule_ids.items()
        }
        projects = sorted(elected, key=cls._path_depth, reverse=True)
        physical_root = root.resolve()
        grouped: MutableMapping[Path, list[p.Infra.ModScanFinding]] = {}
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
        return cls.recounted(
            tuple(entry for entries in grouped.values() for entry in entries),
            native_artifacts=report.native_artifacts,
        )

    @staticmethod
    def recounted(
        entries: tuple[p.Infra.ModScanFinding, ...],
        *,
        native_artifacts: tuple[p.Cli.AtomicFileReceipt, ...] | None = None,
    ) -> p.Infra.ModScanReport:
        """Return the scan report of exactly these findings, classes recounted.

        Returns:
            The scan report of exactly these findings, classes recounted.

        """
        artifacts = (
            tuple(
                entry.native_receipt
                for entry in entries
                if entry.native_receipt is not None
            )
            if native_artifacts is None
            else native_artifacts
        )
        return m.Infra.ModScanReport(
            files=frozenset(entry.file for entry in entries),
            entries=entries,
            native_artifacts=tuple(
                {artifact.path: artifact for artifact in artifacts}.values()
            ),
        )

    @classmethod
    def authored[FindingT: p.Infra.ModOccurrence](
        cls, report: p.Infra.ModOccurrenceReport[FindingT]
    ) -> p.Infra.ModOccurrenceReport[FindingT]:
        """Return the findings mod may rewrite: a generated source is never one.

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
        rules: Sequence[p.Infra.CodemodRule],
        report: p.Infra.ModScanReport,
    ) -> p.Result[bool]:
        """Require every declared finding-count receipt to match exactly.

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
    ) -> p.Result[tuple[Path, p.Cli.AtomicFileState | None]]:
        """Associate a finding with its source's current state.

        Returns:
            The ``(file_path, state)`` pair, without a state for a linked stub
            leaf, or the drift failure.

        """
        outcome = r[tuple[Path, p.Cli.AtomicFileState | None]]
        file_path = Path(file)
        if u.Infra.codemod_source_path(root, file_path).is_symlink():
            return outcome.ok((file_path, None))
        resolved_file = (root / file_path).resolve()
        observed = u.Cli.atomic_read_binary_file_state(resolved_file, required=True)
        if observed.failure and not resolved_file.exists():
            return outcome.fail(
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
        context: p.Infra.ModScanSourceContext,
        native: tuple[p.Infra.ModNativeRecord, p.Cli.AtomicFileReceipt],
    ) -> p.Result[p.Infra.ModScanFinding]:
        """Validate one JSONL finding into a typed, authenticated entry.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanFinding]``.

        """
        finding = record[1]
        rule_files_by_id, fixable_ids = plan
        rule_id = finding.get("ruleId")
        contract_error = cls._finding_contract_error(
            finding, record[0], rule_files_by_id
        )
        if contract_error is not None:
            return r[p.Infra.ModScanFinding].fail(contract_error)
        severity = finding.get("severity")
        match severity:
            case "error" | "warning" | "info" | "hint":
                pass
            case _:
                return r[p.Infra.ModScanFinding].fail(
                    f"invalid ast-grep finding severity: {record[0]}"
                )
        raw_replacement = finding.get("replacement")
        replacement = raw_replacement if isinstance(raw_replacement, str) else None
        native_file = str(finding.get("file"))
        authenticated: p.Result[tuple[Path, p.Cli.AtomicFileState | None]] | None = (
            context.authenticated.get(native_file)
        )
        if authenticated is None:
            authenticated = cls._authenticated_snapshot(root, native_file)
        file_path = Path(native_file)
        if file_path not in context.repositories:
            context.repositories[file_path] = cls._finding_repository(
                file_path, context.repository_roots, root
            )
        if authenticated.failure:
            if authenticated.error_code != c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE:
                return r[p.Infra.ModScanFinding].from_failure(authenticated)
            snapshot = None
            actionable = False
            classification = c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT
        else:
            file_path, snapshot = authenticated.value
            if snapshot is not None and snapshot.content is None:
                return r[p.Infra.ModScanFinding].fail(
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
                return r[p.Infra.ModScanFinding].from_failure(classified)
            actionable, classification = classified.value
        return r[p.Infra.ModScanFinding].ok(
            m.Infra.ModScanFinding.model_validate({
                "rule_file": (str(rule_files_by_id[str(rule_id)].resolve())),
                "rule_id": (str(rule_id)),
                "repository": (context.repositories[file_path]),
                "file": (file_path),
                "source_owner": (
                    "generator"
                    if snapshot is not None
                    and snapshot.content is not None
                    and snapshot.content.startswith(
                        c.Infra.AUTOGEN_MARKER.encode(c.DEFAULT_ENCODING)
                    )
                    else "authored"
                ),
                "source_state": (snapshot),
                "range": (
                    u.json_mapping_adapter().validate_python(
                        finding.get("range"),
                    )
                ),
                "text": (str(finding.get("text"))),
                "message": (
                    native_message
                    if isinstance(native_message := finding.get("message"), str)
                    else None
                ),
                "replacement": (replacement),
                "actionable": (actionable),
                "classification": (classification),
                "severity": (severity),
                "origin": (
                    c.Infra.ModFindingOrigin.OWNED_PATH
                    if finding.get("origin") == "owned-path"
                    else c.Infra.ModFindingOrigin.AST_GREP
                ),
                "replacement_offsets": (
                    m.Infra.ModReplacementOffsets.model_validate(
                        finding["replacementOffsets"]
                    )
                    if "replacementOffsets" in finding
                    else None
                ),
                "native_record": (native[0]),
                "native_receipt": (native[1]),
            }),
        )

    @staticmethod
    def _native_records(stdout: Path) -> Generator[tuple[int, bytes]]:
        """Frame native JSONL records across authenticated byte-block boundaries.

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
        context: p.Infra.ModScanSourceContext,
        native_receipt: p.Cli.AtomicFileReceipt,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanReport]``.

        """
        entries: list[p.Infra.ModScanFinding] = []
        with closing(cls._native_records(stdout)) as lines:
            for offset, raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue
                parsed = u.Cli.json_loads(line)
                if parsed.failure:
                    return r[p.Infra.ModScanReport].from_failure(parsed)
                if not isinstance(parsed.value, Mapping):
                    return r[p.Infra.ModScanReport].fail(
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
                    return r[p.Infra.ModScanReport].from_failure(entry)
                entries.append(entry.value)
        return r.ok(
            cls.recounted(
                tuple(entries),
                native_artifacts=(native_receipt,),
            ),
        )


__all__: list[str] = ["FlextInfraModGateFindings"]
