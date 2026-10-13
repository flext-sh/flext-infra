"""SSH-signed Git gate attestation owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import platform
import re
import shlex
import sys
from collections.abc import Callable
from datetime import UTC, datetime
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
    def git_signing_identity(
        cls,
        request: m.Infra.GitRepoRequest,
    ) -> p.Result[m.Infra.GitSigningIdentityReport]:
        """Read only native signing references and their effective provenance.

        No signing/default-key command, key file or credential helper is invoked.

        Returns:
            Declared public metadata and each native configuration query outcome.
        """
        root = request.repo_root.expanduser().resolve()
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        if identity.failure:
            return r[m.Infra.GitSigningIdentityReport].from_failure(identity)
        observations: list[m.Infra.GitSigningConfigObservation] = []
        for key in c.Infra.GIT_SIGNING_CONFIGURATION_KEYS:
            observed = cls._signing_config_observation(root, key)
            if observed.failure:
                return r[m.Infra.GitSigningIdentityReport].from_failure(observed)
            observations.append(observed.value)
        signing_format, signing_key, allowed_signers = observations
        if not signing_key.value or not allowed_signers.value:
            return r[m.Infra.GitSigningIdentityReport].fail(
                "native Git signing configuration declares an empty key "
                "or trust reference",
            )
        inline = (
            signing_format.value == "ssh"
            and signing_key.value is not None
            and signing_key.value.startswith("key::")
        )
        return r[m.Infra.GitSigningIdentityReport].ok(
            m.Infra.GitSigningIdentityReport(
                repo_root=root,
                signing_format=signing_format.value,
                key_path=(
                    Path(signing_key.value)
                    if signing_format.value == "ssh"
                    and signing_key.value is not None
                    and not inline
                    else None
                ),
                inline_public_key=inline,
                public_fingerprint=None,
                allowed_signers_path=(
                    Path(allowed_signers.value)
                    if allowed_signers.value is not None
                    else None
                ),
                observations=tuple(observations),
            ),
        )

    @staticmethod
    def _signing_config_observation(
        root: Path,
        key: str,
    ) -> p.Result[m.Infra.GitSigningConfigObservation]:
        """Read one exact Git setting using its NUL-delimited native protocol.

        Returns:
            The effective scope/origin/value, or a native absent-key observation.
        """
        query = u.Cli.run_raw(
            ("git", "config", "get", "--null", "--show-origin", "--show-scope", key),
            cwd=root,
        )
        if query.failure:
            return r[m.Infra.GitSigningConfigObservation].from_failure(query)
        output = query.value
        process = m.Cli.ProcessOutcome.model_validate(
            output.outcome,
            from_attributes=True,
        )
        if (
            not process.timed_out
            and process.forwarded_signal is None
            and process.raw_return_code == 1
            and not output.stdout
            and not output.stderr
        ):
            return r[m.Infra.GitSigningConfigObservation].ok(
                m.Infra.GitSigningConfigObservation(
                    key=key,
                    scope=None,
                    origin=None,
                    value=None,
                    process=process,
                ),
            )
        if not u.Cli.process_succeeded(process):
            if not output.stderr:
                return r[m.Infra.GitSigningConfigObservation].fail(
                    f"native Git signing query failed: {key}; "
                    f"raw_return_code={process.raw_return_code}; "
                    f"timed_out={process.timed_out}; "
                    f"forwarded_signal={process.forwarded_signal}",
                )
            return r[m.Infra.GitSigningConfigObservation].fail(
                output.stderr,
            )
        fields = output.stdout.split("\0")
        match fields:
            case [scope, origin, value, ""] if scope and origin:
                pass
            case _:
                return r[m.Infra.GitSigningConfigObservation].fail(
                    "native Git signing configuration returned malformed origin data",
                )
        return r[m.Infra.GitSigningConfigObservation].ok(
            m.Infra.GitSigningConfigObservation(
                key=key,
                scope=scope,
                origin=origin,
                value=value,
                process=process,
            ),
        )

    @classmethod
    def git_capture_gate(
        cls,
        request: m.Infra.GateCaptureRequest,
        *,
        inputs: m.Infra.CodegenInputs,
        load_inputs: Callable[[Path], p.Result[m.Infra.CodegenInputs]],
    ) -> p.Result[m.Infra.GateCaptureReport]:
        """Execute the original checker once and retain its native evidence.

        Returns:
            The resulting ``p.Result[m.Infra.GateCaptureReport]``.
        """
        root = request.repository_root.resolve()
        directory = inputs.spec.make.gate_receipts_directory
        if directory.is_absolute() or ".." in directory.parts:
            return r[m.Infra.GateCaptureReport].fail(
                "gate receipts directory must remain repository-relative",
            )
        started = datetime.now(tz=UTC)
        run_id = started.strftime("%Y%m%dT%H%M%S.%fZ") + f"-{os.getpid()}"
        report_root = root / directory / run_id
        u.Cli.ensure_dir(report_root).unwrap()
        command = (
            sys.executable,
            "-m",
            "flext_infra",
            "check",
            "run",
            "--repository-root",
            str(root),
            "--gates",
            request.gates,
            "--reports-dir",
            str(report_root / c.Infra.VERB_CHECK),
        )
        native_request = m.Infra.RunCommand.model_validate(
            {"repository_root": root, "gates": request.gates},
        )
        started_capture = cls.git_begin_gate_capture(
            root,
            c.Infra.VERB_CHECK,
            command,
            m.Infra.GateExecutionIntent(requested_gates=tuple(native_request.gates)),
            inputs=inputs,
            runtime_identity=sys.version,
        )
        u.Cli.atomic_write_text_file(
            report_root / c.Infra.GATE_CAPTURE_START_FILENAME,
            started_capture.model_dump_json(round_trip=True) + "\n",
        ).unwrap()
        native = u.Cli.run_to_file(
            command,
            report_root / "execution.log",
            cwd=root,
            options=m.Cli.ProcessOptions(live=True),
        )
        if native.failure:
            return r[m.Infra.GateCaptureReport].from_failure(native)
        process = m.Cli.ProcessOutcome.model_validate(
            native.value, from_attributes=True
        )
        report_paths = tuple(
            sorted(
                (report_root / c.Infra.VERB_CHECK).rglob(
                    c.Infra.CHECK_REPORT_SARIF_FILENAME
                )
            )
        )
        reports = cls.git_capture_report_bindings(
            root,
            tuple(
                (path, c.Infra.GateEvidenceReportKind.CHECK_SARIF)
                for path in report_paths
            ),
        ).unwrap()
        return cls.git_finish_gate_capture(
            m.Infra.GateCaptureFinishRequest(
                started=started_capture,
                process=process,
                reports=reports,
                report_root=report_root,
                runtime_identity=sys.version,
            ),
            inputs=load_inputs(root),
        )

    @classmethod
    def git_begin_gate_capture(
        cls,
        root: Path,
        gate: str,
        command: t.StrTuple,
        intent: m.Infra.GateExecutionIntent,
        *,
        inputs: m.Infra.CodegenInputs,
        runtime_identity: str,
    ) -> m.Infra.GateCaptureStart:
        """Inspect the candidate before its original producer executes.

        Returns:
            The retained pre-execution capture record.

        """
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        policy = c.Infra.GateAcceptancePolicy(inputs.spec.make.gate_acceptance_policy)
        return m.Infra.GateCaptureStart(
            repository_root=root,
            gate=gate,
            command=command,
            intent=intent,
            repository=(identity.value.origin_remote if identity.success else None),
            commit_sha=identity.value.head_oid if identity.success else None,
            tree_sha=cls._repo(root).head.commit.tree.hexsha
            if identity.success
            else None,
            dirty=(
                cls._repo(root).is_dirty(untracked_files=False)
                if identity.success
                else None
            ),
            issue=identity.error if identity.failure else None,
            context_digest=cls._gate_capture_context_digest(
                gate,
                intent,
                inputs,
                runtime_identity,
            ),
            policy=policy,
            policy_digest=f"sha256:{u.Cli.sha256_content(policy)}",
            started_at=datetime.now(tz=UTC).isoformat(),
        )

    @staticmethod
    def _gate_capture_context_digest(
        gate: str,
        intent: m.Infra.GateExecutionIntent,
        inputs: m.Infra.CodegenInputs,
        runtime_identity: str,
    ) -> str:
        """Bind effective target configuration and native runtime without paths.

        Returns:
            The digest of the effective configuration and execution context.
        """
        sources = "\n".join(
            f"{source.path.name}:"
            + (
                u.Cli.sha256_bytes(source.content)
                if source.content is not None
                else "absent"
            )
            for source in inputs.sources
        )
        material = "\n".join((
            sys.version,
            platform.platform(),
            gate,
            runtime_identity,
            intent.model_dump_json(round_trip=True),
            inputs.spec.model_dump_json(round_trip=True),
            sources,
        ))
        return f"sha256:{u.Cli.sha256_content(material)}"

    @classmethod
    def _candidate_unsettled(
        cls,
        started: m.Infra.GateCaptureStart,
        *,
        head_oid: str | None,
        origin_remote: str | None,
        root: Path,
    ) -> bool:
        """Report whether the candidate moved, dirtied, or lacks an origin.

        Returns:
            The resulting ``bool``.

        """
        repo = cls._repo(root)
        dirty = started.dirty is not False or repo.is_dirty(untracked_files=False)
        moved = (
            started.commit_sha != head_oid
            or started.tree_sha != repo.head.commit.tree.hexsha
        )
        relocated = started.repository != origin_remote
        return dirty or moved or relocated or started.repository is None

    @classmethod
    def git_finish_gate_capture(
        cls,
        request: m.Infra.GateCaptureFinishRequest,
        *,
        inputs: p.Result[m.Infra.CodegenInputs],
    ) -> p.Result[m.Infra.GateCaptureReport]:
        """Publish original native facts without rerunning or accepting the stage.

        Returns:
            The retained capture report or its first failure.

        """
        started = request.started
        root = started.repository_root
        after = cls.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        issue = started.issue
        if issue is None and inputs.failure:
            issue = inputs.error
        elif issue is None and after.failure:
            issue = after.error
        elif issue is None and cls._candidate_unsettled(
            started,
            head_oid=after.value.head_oid,
            origin_remote=after.value.origin_remote,
            root=root,
        ):
            issue = (
                "original gate candidate is dirty, changed or has no declared origin"
            )
        elif (
            issue is None
            and started.context_digest
            != cls._gate_capture_context_digest(
                started.gate,
                started.intent,
                inputs.value,
                request.runtime_identity,
            )
        ):
            issue = (
                "original gate configuration or native runtime changed during execution"
            )
        receipt: Path | None = None
        if issue is None:
            captured = cls._captured_gate_evidence(
                started, request.process, request.reports
            )
            if captured.failure:
                issue = captured.error
            else:
                receipt = request.report_root / c.Infra.GATE_ORIGINAL_RECEIPT_FILENAME
                u.Cli.atomic_write_text_file(
                    receipt,
                    captured.value.model_dump_json(round_trip=True) + "\n",
                ).unwrap()
        result = m.Infra.GateCaptureReport(
            process=request.process,
            receipt=receipt,
            issues=(
                (
                    m.Infra.Issue(
                        file=str(root),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        severity="error",
                        message=issue,
                    ),
                )
                if issue is not None
                else ()
            ),
        )
        u.Cli.atomic_write_text_file(
            request.report_root / c.Infra.GATE_CAPTURE_RESULT_FILENAME,
            result.model_dump_json(round_trip=True) + "\n",
        ).unwrap()
        return r[m.Infra.GateCaptureReport].ok(result)

    @staticmethod
    def git_capture_report_bindings(
        root: Path,
        paths: t.VariadicTuple[t.Pair[Path, c.Infra.GateEvidenceReportKind]],
    ) -> p.Result[t.VariadicTuple[m.Infra.GateReportEvidence]]:
        """Capture producer-owned report bytes through the atomic read owner.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.GateReportEvidence]]``.
        """
        reports: list[m.Infra.GateReportEvidence] = []
        for path, kind in paths:
            content = (
                u.Cli
                .atomic_read_binary_file_state(path, required=True)
                .unwrap()
                .content
            )
            if content is None:
                return r[t.VariadicTuple[m.Infra.GateReportEvidence]].fail(
                    f"required original checker report has no captured bytes: {path}",
                )
            reports.append(
                m.Infra.GateReportEvidence(
                    path=path.relative_to(root),
                    digest=f"sha256:{u.Cli.sha256_bytes(content)}",
                    kind=kind,
                )
            )
        return r[t.VariadicTuple[m.Infra.GateReportEvidence]].ok(tuple(reports))

    @classmethod
    def _captured_gate_evidence(
        cls,
        started: m.Infra.GateCaptureStart,
        process: m.Cli.ProcessOutcome,
        reports: t.VariadicTuple[m.Infra.GateReportEvidence],
    ) -> p.Result[m.Infra.GateCommandEvidence]:
        """Bind the original producer reports to the observed candidate.

        Returns:
            The resulting ``p.Result[m.Infra.GateCommandEvidence]``.
        """
        if not reports:
            return r[m.Infra.GateCommandEvidence].fail(
                "original producer has no complete report inventory",
            )
        if (
            started.repository is None
            or started.commit_sha is None
            or started.tree_sha is None
        ):
            return r[m.Infra.GateCommandEvidence].fail(
                "original candidate identity is absent"
            )
        evidence = m.Infra.GateCommandEvidence(
            gate=started.gate,
            process=process,
            native_outcome=c.Infra.ToolOutcome.ERROR,
            intent=started.intent,
            policy=started.policy,
            policy_digest=started.policy_digest,
            context_digest=started.context_digest,
            reports=reports,
            result_digest=f"sha256:{
                u.Cli.sha256_content(process.model_dump_json(round_trip=True))
            }",
            started_at=started.started_at,
            completed_at=datetime.now(tz=UTC).isoformat(),
            command_digest=f"sha256:{u.Cli.sha256_content(shlex.join(started.command))}",
            repository=FlextInfraUtilitiesGitRemote.canonical_origin_remote(
                started.repository
            ),
            commit_sha=started.commit_sha,
            tree_sha=started.tree_sha,
        )
        classified = cls._original_report_outcome(started.repository_root, evidence)
        if classified.failure:
            return r[m.Infra.GateCommandEvidence].from_failure(classified)
        return r[m.Infra.GateCommandEvidence].ok(
            evidence.model_copy(update={"native_outcome": classified.value}),
        )

    @classmethod
    def _attestation_tag(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        repository: str,
    ) -> str:
        repository_digest = u.Cli.sha256_content(repository)
        context = u.Cli.sha256_content(
            f"{request.context_digest}\n{request.policy}\n{request.policy_digest}",
        )
        return (
            f"{cls._TAG_PREFIX}/{repository_digest}/{request.commit_sha}/"
            f"{context}/{request.expected_gates[0]}"
        )

    @classmethod
    def _attestation_predicate(
        cls,
        request: m.Infra.GateAttestationCreateRequest,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:

        repo_root = Path(request.workspace).expanduser().resolve()
        identity = cls._attestation_candidate(repo_root)
        if identity.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(identity)
        repo = cls._repo(repo_root)
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
        receipt_matches = (
            evidence.commit_sha == identity.value.head_oid
            and evidence.tree_sha == repo.head.commit.tree.hexsha
            and evidence.repository == repository
            and evidence.context_digest == request.context_digest
        )
        policy_matches = (
            evidence.policy == request.policy
            and evidence.policy_digest == request.policy_digest
            and tuple(request.gates) == (evidence.gate,)
        )
        if not (receipt_matches and policy_matches):
            return r[m.Infra.GateAttestationPredicate].fail(
                "original gate receipt does not match candidate, context or stage",
            )
        for validation in (
            lambda: cls._accepted_gate_evidence(repo_root, evidence),
            lambda: cls._verified_report_evidence(repo_root, evidence.reports),
        ):
            checked = validation()
            if checked.failure:
                return r[m.Infra.GateAttestationPredicate].from_failure(checked)
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
    def _attestation_candidate(
        cls,
        repo_root: Path,
    ) -> p.Result[m.Infra.GitIdentityReport]:
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return identity
        if cls._repo(repo_root).is_dirty(untracked_files=False):
            return r[m.Infra.GitIdentityReport].fail(
                "gate attestation requires a clean committed worktree",
            )
        return identity

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
        serialized = u.Cli.json_dumps(
            predicate.model_dump(mode="json", round_trip=True),
            sort_keys=True,
        )
        if serialized.failure:
            return r[m.Infra.GateAttestationReport].from_failure(serialized)
        verification_request = m.Infra.GateAttestationVerifyRequest(
            workspace=str(repo_root),
            allowed_signers=str(allowed),
            commit_sha=predicate.commit_sha,
            context_digest=predicate.context_digest,
            expected_gates=predicate.covered_gates,
            policy=predicate.commands[0].policy,
            policy_digest=predicate.commands[0].policy_digest,
        )
        return cls._publish_gate_tag(verification_request, predicate, serialized.value)

    @classmethod
    def _publish_gate_tag(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        predicate: m.Infra.GateAttestationPredicate,
        serialized: str,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        repo = cls._repo(repo_root)
        tag = cls._attestation_tag(request, predicate.repository)
        try:
            if tag in {item.name for item in repo.tags}:
                existing = cls._verified_gate_predicate(
                    request,
                    repo_root,
                    allowed,
                    tag,
                )
                if existing.failure:
                    return r[m.Infra.GateAttestationReport].from_failure(existing)
                if existing.value != predicate:
                    return r[m.Infra.GateAttestationReport].fail(
                        f"existing immutable stage proof differs from original "
                        f"evidence: {tag}",
                    )
                return r[m.Infra.GateAttestationReport].ok(
                    cls._attestation_report(tag, predicate, reused=True),
                )
            repo.git.tag(
                "--sign",
                "--annotate",
                "--message",
                serialized,
                tag,
                predicate.commit_sha,
            )
        except (GitCommandError, OSError, ValueError) as exc:
            return r[m.Infra.GateAttestationReport].fail(str(exc), exception=exc)
        verified = cls._verified_gate_predicate(
            request,
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
        tag = cls._attestation_tag(request, repository)
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
        return cls._verify_predicate_evidence(request, predicate, verification.value)

    @classmethod
    def _verify_predicate_evidence(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        predicate: m.Infra.GateAttestationPredicate,
        output: p.Cli.CommandOutput,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        repo_root = Path(request.workspace).expanduser().resolve()
        checked = cls._attestation_predicate_from_value(
            repo_root,
            predicate,
            request.commit_sha,
        )
        if checked.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(checked)
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
        for validation in (
            lambda: cls._verified_original_receipt(repo_root, predicate),
            lambda: cls._accepted_gate_evidence(repo_root, facts),
        ):
            checked = validation()
            if checked.failure:
                return r[m.Infra.GateAttestationPredicate].from_failure(checked)
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
                    exclude={"repository", "commit_sha", "tree_sha"},
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
