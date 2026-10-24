"""Native ast-grep execution, finding contracts and scan-report shaping.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import closing
from pathlib import Path

from flext_infra import c, m, p, r, settings, t, u


class FlextInfraModGateEngineFindingsMixin:
    """Run native ast-grep and validate its findings into recounted reports."""

    @staticmethod
    def _run_tool(
        root: Path,
        command: t.StrSequence,
        *,
        streams: t.Pair[Path, Path],
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
    def recounted(
        entries: t.VariadicTuple[m.Infra.ModScanFinding],
        *,
        source_states: tuple[m.Cli.AtomicFileState, ...] | None = None,
        native_artifacts: tuple[m.Cli.AtomicFileReceipt, ...] | None = None,
    ) -> m.Infra.ModScanReport:
        """Return the scan report of exactly these findings, classes recounted.

        Returns:
            The scan report of exactly these findings, classes recounted.

        """
        return m.Infra.ModScanReport(
            files=frozenset(entry.file for entry in entries),
            entries=entries,
            source_states=source_states,
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
        record: t.Pair[str, t.MappingKV[str, t.JsonValue]],
        root: Path,
        plan: t.Pair[Mapping[str, Path], frozenset[str]],
        context: m.Infra.ModScanSourceContext,
        native: t.Pair[m.Infra.ModNativeRecord, m.Cli.AtomicFileReceipt],
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
                root, native_file, context.source_states
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
                and any(
                    snapshot.content.startswith(header.encode(c.DEFAULT_ENCODING))
                    for header in c.Infra.AUTOGEN_HEADERS
                )
                else "authored",
                source_state=snapshot,
                range=t.Cli.JSON_MAPPING_ADAPTER.validate_python(
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
    def _native_records(stdout: Path) -> Generator[t.Pair[int, bytes]]:
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
        plan: t.Pair[Mapping[str, Path], frozenset[str]],
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
                native_artifacts=(native_receipt,),
            ),
        )


__all__: list[str] = ["FlextInfraModGateEngineFindingsMixin"]
