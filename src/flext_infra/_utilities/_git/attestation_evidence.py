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
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitRepo,
    FlextInfraUtilitiesGitSemanticIdentity,
)


class FlextInfraUtilitiesGitAttestationEvidence(FlextInfraUtilitiesGitRepo):
    """Admit original receipts and producer reports before a gate is attested."""

    @classmethod
    def git_require_green_check_receipt(
        cls,
        repo_root: Path,
        make: m.Infra.MakeSpec,
        *,
        plan_global_targets: p.Infra.GlobalCheckTargetPlanner,
        phase: c.Infra.CheckPhase = c.Infra.CheckPhase.COMPLETE,
    ) -> p.Result[Path]:
        """Prove the newest same-partition check covers the global candidate.

        Initial tests require primary source admission; complete-check callers
        retain the full contract. The current context selects the gate partition,
        not project or file coverage. Its newest receipt carries digest-bound,
        unfiltered coverage of the canonical global topology and every applicable
        gate, match the admitted HEAD/status, and postdate changed working-tree paths.
        Older reports without producer coverage proof require a new check.

        Returns:
            The approving receipt, or the first reason tests must refuse.

        """
        refuse = f"tests run only on a green check: {phase} phase: "
        gates = FlextInfraUtilitiesBase.selected_check_gates(
            make, c.Infra.CheckGateSet.CHECK, phase=phase
        )
        directory = repo_root / make.gate_receipts_directory
        runs = sorted(directory.iterdir(), reverse=True) if directory.is_dir() else []
        for run in runs:
            start = run / c.Infra.GATE_CAPTURE_START_FILENAME
            if not start.is_file():
                continue
            started = m.Infra.GateCaptureStart.model_validate_json(start.read_bytes())
            if started.gate != c.Infra.VERB_CHECK or started.intent.phase != phase:
                continue
            if tuple(started.intent.requested_gates) != tuple(gates):
                return r[Path].fail(
                    f"{refuse}the newest check {run.name} differs from the "
                    "current phase gate inventory; run the declared phase again",
                )
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
            original_facts_mismatch = (
                capture.receipt,
                started.repository_root,
                evidence.gate,
                evidence.intent,
                evidence.started_at,
                evidence.context_digest,
                evidence.runtime_identity,
                evidence.policy,
                evidence.policy_digest,
                evidence.process,
            ) != (
                receipt,
                repo_root,
                started.gate,
                started.intent,
                started.started_at,
                started.context_digest,
                started.runtime_identity,
                started.policy,
                started.policy_digest,
                capture.process,
            )
            if original_facts_mismatch:
                return r[Path].fail(
                    f"{refuse}the newest check {run.name} "
                    "has mismatched original facts",
                )
            return cls._green_receipt_admission(
                repo_root,
                receipt,
                evidence,
                capture,
                plan_global_targets=plan_global_targets,
            )
        return r[Path].fail(
            f"{refuse}no check receipt of gates {','.join(gates)} under "
            f"{directory}; run make check first for complete acceptance, or "
            "workspace check --phase primary for initial source admission",
        )

    @classmethod
    def _green_receipt_admission(
        cls,
        repo_root: Path,
        receipt: Path,
        evidence: m.Infra.GateCommandEvidence,
        capture: m.Infra.GateCaptureReport,
        *,
        plan_global_targets: p.Infra.GlobalCheckTargetPlanner,
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
        accepted = cls._accepted_gate_evidence(
            repo_root, evidence, phase=evidence.intent.phase
        )
        if accepted.failure:
            return r[Path].from_failure(accepted)
        coverage = cls._green_receipt_coverage(
            repo_root, receipt, evidence, plan_global_targets=plan_global_targets
        )
        if coverage.failure:
            return r[Path].from_failure(coverage)
        return cls._green_receipt_currentness(
            repo_root, receipt, evidence, coverage.value
        )

    @classmethod
    def _green_receipt_coverage(
        cls,
        repo_root: Path,
        receipt: Path,
        evidence: m.Infra.GateCommandEvidence,
        *,
        plan_global_targets: p.Infra.GlobalCheckTargetPlanner,
    ) -> p.Result[t.VariadicTuple[m.Infra.CheckProjectTarget]]:
        """Require complete unfiltered coverage of the current native gate plan.

        Returns:
            Accepted coverage or the first original report or topology failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CheckProjectTarget]]
        refuse = f"tests run only on a green check: {receipt.parent.name} "
        source = cls._report_contract_bytes(
            repo_root, evidence.reports, c.Infra.GateEvidenceReportKind.CHECK_SARIF
        )
        if source.failure:
            return result_type.from_failure(source)
        summary = m.Infra.SarifReport.model_validate_json(source.value).properties
        if (
            summary is None
            or summary.global_targets is None
            or summary.selected_files
            or not summary.complete
        ):
            return result_type.fail(
                f"{refuse}has no complete unfiltered global coverage; rerun make check",
            )
        planned = plan_global_targets(evidence.intent.requested_gates)
        if planned.failure:
            return result_type.from_failure(planned)
        expected = tuple(
            (target.name, target.path, tuple(target.applicable_gates))
            for target in planned.value
        )
        for inventory in (summary.global_targets, summary.targets):
            if (
                tuple(
                    (target.name, target.path, tuple(target.applicable_gates))
                    for target in inventory
                )
                != expected
            ):
                return result_type.fail(
                    f"{refuse}does not cover the current global topology and "
                    "applicable gates; rerun make check",
                )
        return result_type.ok(summary.targets)

    @classmethod
    def _green_receipt_currentness(
        cls,
        repo_root: Path,
        receipt: Path,
        evidence: m.Infra.GateCommandEvidence,
        targets: t.VariadicTuple[m.Infra.CheckProjectTarget],
    ) -> p.Result[Path]:
        """Require original HEAD/status and freshness for every covered repository.

        A root gitlink directory cannot prove a member's source currentness.
        Consume each actual target's pre-gate identity from the digest-bound
        producer report, and run the same native changed-file loop per root.
        Changed inputs must predate the original candidate checkpoint, including
        inputs already dirty when the check began.
        Missing original identities require a new check, never a current probe
        substituted as the original observation.

        Returns:
            The approving receipt or the first candidate-currentness failure.

        """
        refuse = f"tests run only on a green check: {receipt.parent.name} "
        started = datetime.fromisoformat(evidence.started_at)
        for target in targets:
            original = target.source_identity
            if original is None or original.repo_root != target.path:
                return r[Path].fail(
                    f"{refuse}has no original source identity for {target.path}; "
                    "rerun make check",
                )
            observed = FlextInfraUtilitiesGitSemanticIdentity.exact_worktree_root(
                target.path
            )
            if observed.failure:
                return r[Path].from_failure(observed)
            current = observed.value
            if (
                (
                    current.git_dir,
                    current.common_dir,
                    current.head_oid,
                    current.porcelain,
                )
                != (
                    original.git_dir,
                    original.common_dir,
                    original.head_oid,
                    original.porcelain,
                )
                or original.head_oid is None
                or (
                    target.path == repo_root
                    and (
                        original.head_oid != evidence.commit_sha
                        or original.head_oid != evidence.after_commit_sha
                    )
                )
            ):
                return r[Path].fail(
                    f"{refuse}source identity or HEAD changed in {target.path}; "
                    "rerun make check",
                )
            freshness = cls._green_target_paths_currentness(original, started, refuse)
            if freshness.failure:
                return r[Path].from_failure(freshness)
        return r[Path].ok(receipt)

    @classmethod
    def _green_target_paths_currentness(
        cls,
        original: m.Infra.GitIdentityReport,
        started: datetime,
        refuse: str,
    ) -> p.Result[Path]:
        """Check native changed paths against the original candidate checkpoint.

        Returns:
            The repository root or its first unsafe or newer changed path.

        """
        opened = cls._open_repo(original.repo_root)
        if opened.failure:
            return r[Path].from_failure(opened)
        repo = opened.value
        changed: set[str] = {
            path
            for diff in (repo.index.diff(None), repo.index.diff(original.head_oid))
            for item in diff
            for path in (item.a_path, item.b_path)
            if path is not None
        }
        changed.update(repo.untracked_files)
        for relative in sorted(changed):
            path = original.repo_root / relative
            if path.is_symlink() or any(
                (original.repo_root / parent).is_symlink()
                for parent in Path(relative).parents
            ):
                return r[Path].fail(
                    f"{refuse}changed path traverses a symlink: {path}",
                )
            if path.is_file() and (
                datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) > started
            ):
                return r[Path].fail(
                    f"{refuse}predates the change to {path}; rerun make check",
                )
        return r[Path].ok(original.repo_root)

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
        *,
        phase: c.Infra.CheckPhase = c.Infra.CheckPhase.COMPLETE,
    ) -> p.Result[bool]:
        if evidence.gate == c.Infra.VERB_CHECK and evidence.intent.phase != phase:
            return r[bool].fail(
                "original checker phase does not prove required stage acceptance"
            )
        process = evidence.process
        digest_matches = evidence.result_digest == (
            "sha256:" + u.Cli.sha256_content(process.model_dump_json(round_trip=True))
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
            or report.properties.phase != evidence.intent.phase
            or tuple(report.properties.requested_gates)
            != evidence.intent.requested_gates
        ):
            return result_type.fail(
                "checker report differs from original phase or requested gates"
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


__all__: list[str] = ["FlextInfraUtilitiesGitAttestationEvidence"]
