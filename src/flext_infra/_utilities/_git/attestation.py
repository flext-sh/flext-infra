"""SSH-signed Git gate attestation owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from git import GitCommandError

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesGitRemote
from flext_infra._utilities._git import FlextInfraUtilitiesGitSemanticIdentityMixin


class FlextInfraUtilitiesGitAttestationMixin(
    FlextInfraUtilitiesGitSemanticIdentityMixin,
):
    """Create and verify immutable SSH-signed gate tags."""

    _TAG_PREFIX: ClassVar[str] = (
        "attest/gates/"
        + c.Infra.GateAttestationSchema.V2.value.rsplit("/", maxsplit=1)[-1]
    )
    _SSH_SIGNATURE_MARKER: ClassVar[str] = "\n-----BEGIN SSH SIGNATURE-----"

    @classmethod
    def _attestation_tag(
        cls,
        commit_sha: str,
        repository: str,
        context_digest: str,
        gate: str,
        policy: c.Infra.GateAcceptancePolicy,
        policy_digest: str,
    ) -> str:
        repository_digest = u.Cli.sha256_content(repository)
        context = u.Cli.sha256_content(
            f"{context_digest}\n{policy}\n{policy_digest}",
        )
        return f"{cls._TAG_PREFIX}/{repository_digest}/{commit_sha}/{context}/{gate}"

    @classmethod
    def _attestation_predicate(
        cls,
        request: m.Infra.GateAttestationCreateRequest,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:

        repo_root = Path(request.workspace).expanduser().resolve()
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(identity)
        repo = cls._repo(repo_root)
        if repo.is_dirty(untracked_files=False):
            return r[m.Infra.GateAttestationPredicate].fail(
                "gate attestation requires a clean committed worktree",
            )
        evidence_result = cls._original_gate_evidence(repo_root, request)
        if evidence_result.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(evidence_result)
        evidence, receipt = evidence_result.value
        origin = identity.value.origin_remote
        if origin is None:
            return r[m.Infra.GateAttestationPredicate].fail(
                "gate attestation requires the candidate's declared origin",
            )
        repository = FlextInfraUtilitiesGitRemote.canonical_origin_remote(origin)
        if (
            evidence.commit_sha != identity.value.head_oid
            or evidence.tree_sha != repo.head.commit.tree.hexsha
            or evidence.repository != repository
            or evidence.context_digest != request.context_digest
            or evidence.policy != request.policy
            or evidence.policy_digest != request.policy_digest
            or tuple(request.gates) != (evidence.gate,)
        ):
            return r[m.Infra.GateAttestationPredicate].fail(
                "original gate receipt does not match candidate, context or stage",
            )
        accepted = cls._accepted_gate_evidence(repo_root, evidence)
        if accepted.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(accepted)
        reports = cls._verified_report_evidence(repo_root, evidence.reports)
        if reports.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(reports)
        toolchain = cls._toolchain_digest(repo_root)
        predicate = m.Infra.GateAttestationPredicate(
            repository=repository,
            commit_sha=identity.value.head_oid,
            tree_sha=repo.head.commit.tree.hexsha,
            signer=request.signer,
            toolchain_digest=toolchain,
            context_digest=evidence.context_digest,
            receipt=receipt,
            covered_gates=request.gates,
            commands=(
                m.Infra.GateExecutionFacts.model_validate(
                    evidence.model_dump(
                        exclude={
                            "command",
                            "cwd",
                            "repository",
                            "commit_sha",
                            "tree_sha",
                        },
                        round_trip=True,
                    ),
                ),
            ),
        )
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _original_gate_evidence(
        cls,
        repo_root: Path,
        request: m.Infra.GateAttestationCreateRequest,
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
        if (
            process.timed_out
            or process.forwarded_signal is not None
            or process.raw_return_code < 0
            or evidence.native_outcome == c.Infra.ToolOutcome.ERROR
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
        """Derive completeness from original typed producer reports."""
        result_type = r[c.Infra.ToolOutcome]
        try:
            if evidence.gate == c.Infra.VERB_CHECK:
                source = cls._report_contract_bytes(
                    repo_root,
                    evidence.reports,
                    c.Infra.GateEvidenceReportKind.CHECK_SARIF,
                )
                if source.failure:
                    return result_type.from_failure(source)
                return cls._check_report_outcome(
                    m.Infra.SarifReport.model_validate_json(source.value),
                )
            if evidence.gate == c.Infra.VERB_TEST:
                return cls._pytest_report_outcome(repo_root, evidence.reports)
            return result_type.fail(
                f"original report admission is not wired for stage: {evidence.gate}",
            )
        except ValueError as exc:
            return result_type.fail(str(exc), exception=exc)

    @staticmethod
    def _check_report_outcome(
        report: m.Infra.SarifReport,
    ) -> p.Result[c.Infra.ToolOutcome]:
        summary = report.properties
        if summary is None or not summary.targets or not summary.results:
            return r[c.Infra.ToolOutcome].fail(
                "check report has no completed target inventory"
            )
        if (
            len(summary.targets) != len(summary.results)
            or tuple(target.name for target in summary.targets)
            != tuple(result.project for result in summary.results)
            or not summary.requested_gates
            or any(
                set(result.gates) != set(summary.requested_gates)
                for result in summary.results
            )
        ):
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
        if (
            process.timed_out
            or process.forwarded_signal is not None
            or process.raw_return_code not in {0, 1}
            or accounting.inventory_count is None
            or not accounting.executed_count
            or accounting.executed_count != accounting.reported_count
            or accounting.executed_count + accounting.deselected_count
            != accounting.inventory_count
            or len(diagnostics.reported_node_ids) != accounting.reported_count
            or diagnostics.error_count
            or diagnostics.collection_failed_count
            or diagnostics.collection_skipped_count
            or diagnostics.skipped_count > len(diagnostics.connectivity_skip_cases)
        ):
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

    @classmethod
    def _toolchain_digest(cls, repo_root: Path, commit_sha: str | None = None) -> str:

        repo = cls._repo(repo_root)
        commit = repo.commit(commit_sha) if commit_sha is not None else repo.head.commit
        names = (
            ".mise.toml",
            ".python-version",
            "pyproject.toml",
            "uv.lock",
            "mise.lock",
            "config",
        )
        tracked: list[str] = []
        for name in names:
            # An optional toolchain file absent from this commit contributes
            # nothing to the digest; its absence is read, not caught.
            if name not in commit.tree:
                continue
            blob = commit.tree / name
            tracked.append(f"{name}:{blob.hexsha}")
        content = "\n".join(tracked)
        return f"sha256:{u.Cli.sha256_content(content)}"

    @classmethod
    def git_create_gate_attestation(
        cls,
        request: m.Infra.GateAttestationCreateRequest,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Create the exact signed tag for a validated HEAD predicate.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationReport]``.

        """
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        if not allowed.is_file():
            return r[m.Infra.GateAttestationReport].fail(
                f"allowed_signers file not found: {allowed}",
            )
        predicate_result = cls._attestation_predicate(request)
        if predicate_result.failure:
            return r[m.Infra.GateAttestationReport].from_failure(predicate_result)
        predicate = predicate_result.value
        tag = cls._attestation_tag(
            predicate.commit_sha,
            predicate.repository,
            predicate.context_digest,
            predicate.covered_gates[0],
            predicate.commands[0].policy,
            predicate.commands[0].policy_digest,
        )
        serialized = u.Cli.json_dumps(
            predicate.model_dump(mode="json", round_trip=True),
            sort_keys=True,
        )
        if serialized.failure:
            return r[m.Infra.GateAttestationReport].from_failure(serialized)
        repo = cls._repo(repo_root)
        verification_request = m.Infra.GateAttestationVerifyRequest(
            workspace=str(repo_root),
            allowed_signers=str(allowed),
            commit_sha=predicate.commit_sha,
            context_digest=predicate.context_digest,
            expected_gates=predicate.covered_gates,
            policy=predicate.commands[0].policy,
            policy_digest=predicate.commands[0].policy_digest,
        )
        try:
            if tag in {item.name for item in repo.tags}:
                existing = cls._verified_gate_predicate(
                    verification_request,
                    repo_root,
                    allowed,
                    tag,
                )
                if existing.failure:
                    return r[m.Infra.GateAttestationReport].from_failure(existing)
                if existing.value != predicate:
                    return r[m.Infra.GateAttestationReport].fail(
                        f"existing immutable stage proof differs from original evidence: {tag}",
                    )
                return r[m.Infra.GateAttestationReport].ok(
                    cls._attestation_report(tag, predicate, reused=True),
                )
            repo.git.tag(
                "--sign",
                "--annotate",
                "--message",
                serialized.value,
                tag,
                predicate.commit_sha,
            )
        except (GitCommandError, OSError, ValueError) as exc:
            return r[m.Infra.GateAttestationReport].fail(str(exc), exception=exc)
        verified = cls._verified_gate_predicate(
            verification_request,
            repo_root,
            allowed,
            tag,
        )
        if verified.failure:
            return r[m.Infra.GateAttestationReport].from_failure(verified)
        return r[m.Infra.GateAttestationReport].ok(
            cls._attestation_report(tag, verified.value)
        )

    @classmethod
    def git_verify_gate_attestation(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Verify signature, signer, HEAD identity, and exact gate coverage.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationReport]``.

        """
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        if not allowed.is_file():
            return r[m.Infra.GateAttestationReport].fail(
                f"allowed_signers file not found: {allowed}",
            )
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return r[m.Infra.GateAttestationReport].from_failure(identity)
        origin = identity.value.origin_remote
        if origin is None:
            return r[m.Infra.GateAttestationReport].fail(
                "candidate has no declared origin"
            )
        repository = FlextInfraUtilitiesGitRemote.canonical_origin_remote(origin)
        tag = cls._attestation_tag(
            request.commit_sha,
            repository,
            request.context_digest,
            request.expected_gates[0],
            request.policy,
            request.policy_digest,
        )
        predicate_result = cls._verified_gate_predicate(
            request,
            repo_root,
            allowed,
            tag,
        )
        if predicate_result.failure:
            return r[m.Infra.GateAttestationReport].from_failure(predicate_result)
        predicate = predicate_result.value
        published = cls._published_attestation_report(request, predicate)
        if published.failure:
            return r[m.Infra.GateAttestationReport].from_failure(published)
        return r[m.Infra.GateAttestationReport].ok(
            cls._attestation_report(tag, predicate),
        )

    @classmethod
    def _verified_gate_predicate(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        repo_root: Path,
        allowed: Path,
        tag: str,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        """Verify the tag signature and gate coverage against the predicate.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationPredicate]``.

        """
        commit_sha = request.commit_sha
        verification = u.Cli.run_raw(
            [
                "git",
                "-c",
                "gpg.format=ssh",
                "-c",
                f"gpg.ssh.allowedSignersFile={allowed}",
                "verify-tag",
                "--raw",
                tag,
            ],
            cwd=repo_root,
        )
        if verification.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(verification)
        if not u.Cli.process_succeeded(verification.value.outcome):
            return r[m.Infra.GateAttestationPredicate].fail(
                f"git verify-tag failed: {verification.value.stdout}"
                f"{verification.value.stderr}",
            )
        predicate_result = cls._predicate_from_tag(repo_root, tag, commit_sha)
        if predicate_result.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(predicate_result)
        predicate = predicate_result.value
        checked = cls._attestation_predicate_from_value(
            repo_root,
            predicate,
            commit_sha,
        )
        if checked.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(checked)
        output = verification.value
        match = re.search(
            r'^Good "git" signature for (\S+) with ',
            f"{output.stdout}\n{output.stderr}",
            flags=re.MULTILINE,
        )
        if match is None or match.group(1) != predicate.signer:
            return r[m.Infra.GateAttestationPredicate].fail(
                f"verified signature does not identify signer: {predicate.signer}",
            )
        if tuple(request.expected_gates) != tuple(predicate.covered_gates):
            return r[m.Infra.GateAttestationPredicate].fail(
                "attestation gate coverage does not exactly match required gates",
            )
        facts = predicate.commands[0]
        if (
            predicate.context_digest != request.context_digest
            or facts.context_digest != request.context_digest
            or facts.policy != request.policy
            or facts.policy_digest != request.policy_digest
        ):
            return r[m.Infra.GateAttestationPredicate].fail(
                "attestation context or policy does not match the required stage",
            )
        original = cls._verified_original_receipt(repo_root, predicate)
        if original.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(original)
        accepted = cls._accepted_gate_evidence(repo_root, facts)
        if accepted.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(accepted)
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _verified_original_receipt(
        cls,
        repo_root: Path,
        predicate: m.Infra.GateAttestationPredicate,
    ) -> p.Result[bool]:
        if predicate.receipt.kind != c.Infra.GateEvidenceReportKind.RECEIPT:
            return r[bool].fail("signed proof has no original producer receipt")
        source = cls._report_bytes(repo_root, predicate.receipt)
        if source.failure:
            return r[bool].from_failure(source)
        try:
            original = m.Infra.GateCommandEvidence.model_validate_json(source.value)
            public = m.Infra.GateExecutionFacts.model_validate(
                original.model_dump(
                    exclude={"command", "cwd", "repository", "commit_sha", "tree_sha"},
                    round_trip=True,
                ),
            )
        except ValueError as exc:
            return r[bool].fail(str(exc), exception=exc)
        if (
            original.commit_sha != predicate.commit_sha
            or original.tree_sha != predicate.tree_sha
            or original.repository != predicate.repository
            or public != predicate.commands[0]
        ):
            return r[bool].fail(
                "signed summary differs from its original producer receipt"
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _published_attestation_report(
        request: m.Infra.GateAttestationVerifyRequest,
        predicate: m.Infra.GateAttestationPredicate,
    ) -> p.Result[bool]:
        """Write the attestation report when the request names an output path.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if request.output is None:
            return r[bool].ok(value=True)
        serialized = u.Cli.json_dumps(
            predicate.model_dump(mode="json", round_trip=True),
            sort_keys=True,
        )
        if serialized.failure:
            return r[bool].from_failure(serialized)
        written = u.Cli.atomic_write_text_file(
            Path(request.output).expanduser().resolve(),
            serialized.value,
        )
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    @classmethod
    def _predicate_from_tag(
        cls,
        repo_root: Path,
        tag: str,
        commit_sha: str,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:

        try:
            tag_ref = next(
                item for item in cls._repo(repo_root).tags if item.name == tag
            )
        except (OSError, StopIteration) as exc:
            return r[m.Infra.GateAttestationPredicate].fail(str(exc), exception=exc)
        if tag_ref.tag is None:
            return r[m.Infra.GateAttestationPredicate].fail(
                f"attestation is not an annotated tag: {tag}",
            )
        target = tag_ref.commit.hexsha
        if target != commit_sha:
            return r[m.Infra.GateAttestationPredicate].fail(
                "attestation tag target does not equal selected commit: "
                f"{target} != {commit_sha}",
            )
        message = tag_ref.tag.message.split(cls._SSH_SIGNATURE_MARKER, maxsplit=1)[0]
        try:
            predicate = m.Infra.GateAttestationPredicate.model_validate_json(message)
        except ValueError as exc:
            return r[m.Infra.GateAttestationPredicate].fail(str(exc), exception=exc)
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _attestation_predicate_from_value(
        cls,
        repo_root: Path,
        predicate: m.Infra.GateAttestationPredicate,
        commit_sha: str,
    ) -> p.Result[bool]:

        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return r[bool].from_failure(identity)
        repo = cls._repo(repo_root)
        commit = repo.commit(commit_sha)
        tree_sha = commit.tree.hexsha
        origin = identity.value.origin_remote
        if origin is None:
            return r[bool].fail("selected candidate has no declared origin")
        actual_repository = FlextInfraUtilitiesGitRemote.canonical_origin_remote(origin)
        actual_toolchain = cls._toolchain_digest(repo_root, commit_sha)
        mismatches = tuple(
            field
            for field, matches in (
                ("repository", predicate.repository == actual_repository),
                ("commit", predicate.commit_sha == commit_sha),
                ("tree", predicate.tree_sha == tree_sha),
                ("toolchain", predicate.toolchain_digest == actual_toolchain),
            )
            if not matches
        )
        if mismatches:
            return r[bool].fail(
                "attestation does not match selected candidate: "
                + ", ".join(mismatches),
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _attestation_report(
        tag: str,
        predicate: m.Infra.GateAttestationPredicate,
        *,
        reused: bool = False,
    ) -> m.Infra.GateAttestationReport:
        return m.Infra.GateAttestationReport(
            tag=tag,
            commit_sha=predicate.commit_sha,
            tree_sha=predicate.tree_sha,
            signer=predicate.signer,
            covered_gates=predicate.covered_gates,
            context_digest=predicate.context_digest,
            reused=reused,
        )


__all__: list[str] = ["FlextInfraUtilitiesGitAttestationMixin"]
