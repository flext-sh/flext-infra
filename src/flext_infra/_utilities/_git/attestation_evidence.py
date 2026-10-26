"""Original gate evidence admission owned by the signed gate attestation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesBase
from flext_infra._utilities._git import FlextInfraUtilitiesGitRepo


class FlextInfraUtilitiesGitAttestationEvidenceMixin(FlextInfraUtilitiesGitRepo):
    """Admit original receipts and producer reports before a gate is attested."""

    @classmethod
    def git_require_green_check_receipt(
        cls,
        repo_root: Path,
        make: m.Infra.MakeSpec,
    ) -> p.Result[Path]:
        """Prove the newest same-partition check covers the global candidate.

        Tests run only on a green check (the workflow's ``tests`` row requires
        ``check``). The current context selects the gate partition, not project
        or file coverage. Its newest receipt must carry original digest-bound,
        unfiltered coverage of the canonical global topology and every applicable
        gate, remain clean, match HEAD, and postdate changed working-tree paths.
        Older reports without producer coverage proof require a new check.

        Returns:
            The approving receipt, or the first reason tests must refuse.

        """
        refuse = "tests run only on a green check: "
        gates = FlextInfraUtilitiesBase.selected_check_gates(
            make, c.Infra.CheckGateSet.CHECK
        )
        directory = repo_root / make.gate_receipts_directory
        runs = sorted(directory.iterdir(), reverse=True) if directory.is_dir() else []
        for run in runs:
            start = run / c.Infra.GATE_CAPTURE_START_FILENAME
            if not start.is_file():
                continue
            started = m.Infra.GateCaptureStart.model_validate_json(start.read_bytes())
            if started.gate != c.Infra.VERB_CHECK or tuple(
                started.intent.requested_gates
            ) != tuple(gates):
                continue
            result = run / c.Infra.GATE_CAPTURE_RESULT_FILENAME
            if not result.is_file():
                return r[Path].fail(
                    f"{refuse}the newest check {run.name} never completed",
                )
            capture = m.Infra.GateCaptureReport.model_validate_json(
                result.read_bytes(),
            )
            if capture.receipt is None:
                return r[Path].fail(
                    f"{refuse}the newest check {run.name} has no receipt: "
                    + "; ".join(issue.message for issue in capture.issues),
                )
            receipt = run / c.Infra.GATE_ORIGINAL_RECEIPT_FILENAME
            evidence = m.Infra.GateCommandEvidence.model_validate_json(
                receipt.read_bytes(),
            )
            return cls._green_receipt_admission(repo_root, receipt, evidence, capture)
        return r[Path].fail(
            f"{refuse}no check receipt of gates {','.join(gates)} under "
            f"{directory}; run make check first",
        )

    @classmethod
    def _green_receipt_admission(
        cls,
        repo_root: Path,
        receipt: Path,
        evidence: m.Infra.GateCommandEvidence,
        capture: m.Infra.GateCaptureReport,
    ) -> p.Result[Path]:
        refuse = f"tests run only on a green check: {receipt.parent.name} "
        if (
            capture.issues
            or capture.process.raw_return_code != 0
            or evidence.native_outcome is not c.Infra.ToolOutcome.CLEAN
        ):
            return r[Path].fail(
                f"{refuse}is red (exit {capture.process.raw_return_code}, "
                f"outcome {evidence.native_outcome}); fix it and rerun make check",
            )
        opened = cls._open_repo(repo_root)
        if opened.failure:
            return r[Path].from_failure(opened)
        repo = opened.value
        head = repo.head.commit.hexsha
        if evidence.after_commit_sha != head:
            return r[Path].fail(
                f"{refuse}approved {evidence.after_commit_sha}, HEAD is {head}; "
                "rerun make check",
            )
        changed: set[str] = {
            path
            for diff in (repo.index.diff(None), repo.index.diff(head))
            for item in diff
            for path in (item.a_path, item.b_path)
            if path is not None
        }
        changed.update(repo.untracked_files)
        completed = datetime.fromisoformat(evidence.completed_at)
        for relative in sorted(changed):
            path = repo_root / relative
            if path.is_file() and (
                datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) > completed
            ):
                return r[Path].fail(
                    f"{refuse}predates the change to {relative}; rerun make check",
                )
        return r[Path].ok(receipt)

    @classmethod
    def _original_gate_evidence(
        cls,
        repo_root: Path,
        request: m.Infra.GateAttestationCreateRequest
        | m.Infra.GateAttestationVerifyRequest,
    ) -> p.Result[t.Pair[m.Infra.GateCommandEvidence, m.Infra.GateReportEvidence]]:
        result_type = r[t.Pair[m.Infra.GateCommandEvidence, m.Infra.GateReportEvidence]]
        path = (
            request.receipt
            if request.receipt.is_absolute()
            else repo_root / request.receipt
        )
        if ".." in path.parts or not path.is_relative_to(repo_root):
            return result_type.fail(
                "original receipt must remain inside its repository"
            )
        original = u.Cli.atomic_read_binary_file_state(path, required=True)
        if original.failure:
            return result_type.from_failure(original)
        content = original.value.content
        if content is None:
            return result_type.fail("required original receipt has no captured bytes")
        try:
            evidence = m.Infra.GateCommandEvidence.model_validate_json(
                content,
            )
        except ValueError as exc:
            return result_type.fail(str(exc), exception=exc)
        return result_type.ok((
            evidence,
            m.Infra.GateReportEvidence(
                path=path.relative_to(repo_root),
                digest=f"sha256:{u.Cli.sha256_bytes(content)}",
                kind=c.Infra.GateEvidenceReportKind.RECEIPT,
            ),
        ))

    @classmethod
    def _accepted_gate_evidence(
        cls,
        repo_root: Path,
        evidence: m.Infra.GateExecutionFacts,
    ) -> p.Result[bool]:
        process = evidence.process
        digest_matches = evidence.result_digest == (
            f"sha256:{u.Cli.sha256_content(process.model_dump_json(round_trip=True))}"
        )
        process_incomplete = (
            process.timed_out
            or process.forwarded_signal is not None
            or process.raw_return_code < 0
            or process.raw_return_code not in {0, 1}
        )
        if (
            not digest_matches
            or evidence.native_outcome == c.Infra.ToolOutcome.ERROR
            or process_incomplete
            or (
                evidence.native_outcome == c.Infra.ToolOutcome.CLEAN
                and process.raw_return_code != 0
            )
        ):
            return r[bool].fail(
                "original gate execution has no complete accepted evidence"
            )
        observed = cls._original_report_outcome(repo_root, evidence)
        if observed.failure:
            return r[bool].from_failure(observed)
        if observed.value != evidence.native_outcome:
            return r[bool].fail(
                "original native classification differs from its reports"
            )
        if (
            evidence.policy == c.Infra.GateAcceptancePolicy.CLEAN
            and observed.value != c.Infra.ToolOutcome.CLEAN
        ):
            return r[bool].fail(
                "original reports have findings under clean-quality policy"
            )
        return r[bool].ok(value=True)

    @classmethod
    def _original_report_outcome(
        cls,
        repo_root: Path,
        evidence: m.Infra.GateExecutionFacts,
    ) -> p.Result[c.Infra.ToolOutcome]:
        """Derive completeness from original typed producer reports.

        Returns:
            The resulting ``p.Result[c.Infra.ToolOutcome]``.

        """
        result_type = r[c.Infra.ToolOutcome]
        try:
            return cls._producer_report_outcome(repo_root, evidence)
        except ValueError as exc:
            return result_type.fail(str(exc), exception=exc)

    @classmethod
    def _producer_report_outcome(
        cls,
        repo_root: Path,
        evidence: m.Infra.GateExecutionFacts,
    ) -> p.Result[c.Infra.ToolOutcome]:
        """Dispatch original evidence to its declared producer contract.

        Returns:
            The producer classification or its first admission failure.

        """
        result_type = r[c.Infra.ToolOutcome]
        if evidence.gate == c.Infra.VERB_CHECK:
            return cls._original_check_outcome(repo_root, evidence)
        if evidence.gate == c.Infra.VERB_TEST:
            return cls._original_test_outcome(repo_root, evidence)
        return result_type.fail(
            f"original report admission is not wired for stage: {evidence.gate}",
        )

    @classmethod
    def _original_check_outcome(
        cls,
        repo_root: Path,
        evidence: m.Infra.GateExecutionFacts,
    ) -> p.Result[c.Infra.ToolOutcome]:
        result_type = r[c.Infra.ToolOutcome]
        if (
            not evidence.intent.requested_gates
            or evidence.intent.test_selection is not None
        ):
            return result_type.fail("checker proof has unrelated producer intent")
        source = cls._report_contract_bytes(
            repo_root,
            evidence.reports,
            c.Infra.GateEvidenceReportKind.CHECK_SARIF,
        )
        if source.failure:
            return result_type.from_failure(source)
        report = m.Infra.SarifReport.model_validate_json(source.value)
        if (
            report.properties is None
            or tuple(report.properties.requested_gates)
            != evidence.intent.requested_gates
        ):
            return result_type.fail(
                "checker report differs from original requested gates"
            )
        return cls._check_report_outcome(report)

    @classmethod
    def _original_test_outcome(
        cls,
        repo_root: Path,
        evidence: m.Infra.GateExecutionFacts,
    ) -> p.Result[c.Infra.ToolOutcome]:
        result_type = r[c.Infra.ToolOutcome]
        selection = evidence.intent.test_selection
        if selection is None or evidence.intent.requested_gates:
            return result_type.fail("test proof has unrelated producer intent")
        source = cls._report_contract_bytes(
            repo_root,
            evidence.reports,
            c.Infra.GateEvidenceReportKind.PYTEST_CONTEXT,
        )
        if source.failure:
            return result_type.from_failure(source)
        context = m.Infra.PytestRunContext.model_validate_json(source.value)
        if context.execution_mode != selection.execution_mode:
            return result_type.fail("test report differs from original operation")
        return cls._pytest_report_outcome(
            repo_root,
            evidence.reports,
            evidence.process,
        )

    @staticmethod
    def _check_report_outcome(
        report: m.Infra.SarifReport,
    ) -> p.Result[c.Infra.ToolOutcome]:
        summary = report.properties
        if summary is None or not summary.targets or not summary.results:
            return r[c.Infra.ToolOutcome].fail(
                "check report has no completed target inventory"
            )
        if not summary.complete:
            return r[c.Infra.ToolOutcome].fail(
                "check report target accounting is incomplete"
            )
        executions = tuple(
            execution
            for result in summary.results
            for execution in result.gates.values()
        )
        if any(
            execution.outcome == c.Infra.ToolOutcome.ERROR
            or any(
                issue.code == c.Infra.ToolOutcome.ERROR for issue in execution.issues
            )
            for execution in executions
        ):
            return r[c.Infra.ToolOutcome].fail(
                "check report contains an operational failure"
            )
        return r[c.Infra.ToolOutcome].ok(
            c.Infra.ToolOutcome.FINDINGS
            if any(
                execution.outcome == c.Infra.ToolOutcome.FINDINGS or execution.issues
                for execution in executions
            )
            else c.Infra.ToolOutcome.CLEAN,
        )

    @classmethod
    def _pytest_report_outcome(
        cls,
        repo_root: Path,
        reports: t.SequenceOf[m.Infra.GateReportEvidence],
        expected_process: m.Cli.ProcessOutcome,
    ) -> p.Result[c.Infra.ToolOutcome]:
        result_type = r[c.Infra.ToolOutcome]
        process_source = cls._report_contract_bytes(
            repo_root,
            reports,
            c.Infra.GateEvidenceReportKind.PYTEST_PROCESS,
        )
        accounting_source = cls._report_contract_bytes(
            repo_root,
            reports,
            c.Infra.GateEvidenceReportKind.PYTEST_ACCOUNTING,
        )
        diagnostics_source = cls._report_contract_bytes(
            repo_root,
            reports,
            c.Infra.GateEvidenceReportKind.PYTEST_DIAGNOSTICS,
        )
        for source in (process_source, accounting_source, diagnostics_source):
            if source.failure:
                return result_type.from_failure(source)
        process = m.Cli.ProcessOutcome.model_validate_json(process_source.value)
        accounting = m.Infra.TestmonRunAccounting.model_validate_json(
            accounting_source.value
        )
        diagnostics = m.Infra.PytestDiagnostics.model_validate_json(
            diagnostics_source.value
        )
        process_valid = (
            process == expected_process
            and not process.timed_out
            and process.forwarded_signal is None
            and process.raw_return_code in {0, 1}
        )
        accounting_valid = (
            accounting.inventory_count is not None
            and bool(accounting.executed_count)
            and accounting.executed_count == accounting.reported_count
            and accounting.executed_count + accounting.deselected_count
            == accounting.inventory_count
        )
        diagnostics_valid = (
            len(diagnostics.reported_node_ids) == accounting.reported_count
            and not diagnostics.error_count
            and not diagnostics.collection_failed_count
            and not diagnostics.collection_skipped_count
            and diagnostics.skipped_count <= len(diagnostics.connectivity_skip_cases)
        )
        if not (process_valid and accounting_valid and diagnostics_valid):
            return result_type.fail(
                "test reports contain incomplete or operational execution"
            )
        return result_type.ok(
            c.Infra.ToolOutcome.FINDINGS
            if diagnostics.failed_count
            or diagnostics.warning_count
            or diagnostics.skipped_count
            else c.Infra.ToolOutcome.CLEAN,
        )

    @classmethod
    def _report_contract_bytes(
        cls,
        repo_root: Path,
        reports: t.SequenceOf[m.Infra.GateReportEvidence],
        kind: c.Infra.GateEvidenceReportKind,
    ) -> p.Result[bytes]:
        selected = tuple(report for report in reports if report.kind == kind)
        if len(selected) != 1:
            return r[bytes].fail(f"one original {kind} report is required")
        return cls._report_bytes(repo_root, selected[0])

    @staticmethod
    def _report_bytes(
        repo_root: Path,
        report: m.Infra.GateReportEvidence,
    ) -> p.Result[bytes]:
        original = u.Cli.atomic_read_binary_file_state(
            repo_root / report.path, required=True
        )
        if original.failure:
            return r[bytes].from_failure(original)
        content = original.value.content
        if content is None:
            return r[bytes].fail(
                f"required report has no captured bytes: {report.path}"
            )
        if f"sha256:{u.Cli.sha256_bytes(content)}" != report.digest:
            return r[bytes].fail(
                f"original report digest does not match: {report.path}"
            )
        return r[bytes].ok(content)

    @classmethod
    def _verified_report_evidence(
        cls,
        repo_root: Path,
        reports: t.SequenceOf[m.Infra.GateReportEvidence],
    ) -> p.Result[bool]:
        for report in reports:
            original = cls._report_bytes(repo_root, report)
            if original.failure:
                return r[bool].from_failure(original)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesGitAttestationEvidenceMixin"]
