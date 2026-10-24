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
from base64 import b64decode
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from git import GitCommandError

from flext_infra import c, m, p, r, settings, t
from flext_infra._utilities import FlextInfraUtilitiesBase
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitSemanticIdentityMixin,
    FlextInfraUtilitiesGitWorktreeIO,
)
from flext_infra._utilities._git.attestation_evidence import (
    FlextInfraUtilitiesGitAttestationEvidenceMixin,
)
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)


class FlextInfraUtilitiesGitAttestationMixin(
    FlextInfraUtilitiesGitAttestationEvidenceMixin,
    FlextInfraUtilitiesGitSemanticIdentityMixin,
):
    """Create and verify immutable SSH-signed gate tags."""

    _TAG_PREFIX: ClassVar[str] = (
        "attest/gates/"
        + c.Infra.GateAttestationSchema.V3.value.rsplit("/", maxsplit=1)[-1]
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
        observations: list[m.Infra.GitSigningConfigObservation] = []
        for key in c.Infra.GIT_SIGNING_CONFIGURATION_KEYS:
            observed = cls._signing_config_observation(root, key)
            if observed.failure:
                return r[m.Infra.GitSigningIdentityReport].from_failure(observed)
            observations.append(observed.value)
        signing_format, signing_key, allowed_signers = observations
        if any(item.value is not None and not item.value for item in observations):
            return r[m.Infra.GitSigningIdentityReport].fail(
                "native Git signing configuration declares an empty reference",
            )
        if signing_format.value not in {None, "openpgp", "x509", "ssh"}:
            return r[m.Infra.GitSigningIdentityReport].fail(
                "native Git signing configuration declares an unsupported format",
            )
        key = signing_key.value
        trust = allowed_signers.value
        ssh = signing_format.value == "ssh"
        inline = ssh and key is not None and key.startswith(("key::", "ssh-"))
        if inline and key is not None:
            try:
                cls._validate_inline_ssh_key(key)
            except ValueError as error:
                return r[m.Infra.GitSigningIdentityReport].fail(
                    "native Git signing configuration declares a malformed public key",
                    exception=error,
                )
        return r[m.Infra.GitSigningIdentityReport].ok(
            m.Infra.GitSigningIdentityReport(
                repo_root=root,
                signing_format=signing_format.value,
                key_path=Path(key) if ssh and key is not None and not inline else None,
                inline_public_key=inline,
                public_fingerprint=None,
                allowed_signers_path=Path(trust) if trust is not None else None,
                observations=tuple(observations),
            ),
        )

    @staticmethod
    def _validate_inline_ssh_key(key: str) -> None:
        """Decode one inline SSH public key envelope and verify its key material.

        Raises:
            ValueError: If the envelope does not split into a key kind plus
                base64 payload, the payload is not valid base64, or the
                decoded blob does not start with its declared key kind.

        """
        kind, encoded, *_ = key.removeprefix("key::").split(maxsplit=2)
        blob = b64decode(encoded, validate=True)
        size = int.from_bytes(blob[:4], "big")
        if len(blob) <= 4 + size or blob[4 : 4 + size] != kind.encode("ascii"):
            msg = "malformed SSH public key envelope"
            raise ValueError(msg)

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
        scope: str | None
        origin: str | None
        value: str | None
        if (
            not process.timed_out
            and process.forwarded_signal is None
            and process.raw_return_code == 1
            and not output.stdout
            and not output.stderr
        ):
            scope = origin = value = None
        elif not u.Cli.process_succeeded(process):
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
        else:
            match output.stdout.split("\0"):
                case [scope, origin, value, ""] if scope and origin:
                    pass
                case _:
                    return r[m.Infra.GitSigningConfigObservation].fail(
                        "native Git signing configuration returned "
                        "malformed origin data",
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
        read_runtime_identity: Callable[[t.StrSequence], p.Result[str]],
    ) -> p.Result[m.Infra.GateCaptureReport]:
        """Execute the original checker once and retain its native evidence.

        Optional measurement profiles that checker through the shared CLI owner,
        preserving the same arguments, outcome and invocation directory.

        Returns:
            The resulting ``p.Result[m.Infra.GateCaptureReport]``.

        """
        root = request.repository_root.resolve()
        gates = request.gates or ",".join(
            FlextInfraUtilitiesBase.selected_check_gates(
                inputs.spec.make, c.Infra.CheckGateSet.CHECK
            )
        )
        if not gates:
            return r[m.Infra.GateCaptureReport].fail(
                "no active check gates remain in the selected context",
            )
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
            *(
                (
                    "flext_infra._profile_entry",
                    str(report_root / c.Infra.CHECK_PROFILE_FILENAME),
                )
                if settings.Infra.profile
                else ("flext_infra",)
            ),
            "check",
            "run",
            "--repository-root",
            str(root),
            "--gates",
            gates,
            "--reports-dir",
            str(report_root / c.Infra.VERB_CHECK),
            *(
                ("--report-output", str(request.report_output))
                if request.report_output is not None
                else ()
            ),
        )
        native_request = m.Infra.RunCommand.model_validate(
            {"repository_root": root, "gates": gates},
        )
        started_capture = cls.git_begin_gate_capture(
            m.Infra.GateCaptureBeginRequest(
                repository_root=root,
                gate=c.Infra.VERB_CHECK,
                command=command,
                intent=m.Infra.GateExecutionIntent(
                    requested_gates=tuple(native_request.gates),
                ),
                runtime_identity=read_runtime_identity(native_request.gates).unwrap(),
            ),
            inputs=inputs,
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
                runtime_identity=read_runtime_identity(native_request.gates).unwrap(),
            ),
            inputs=load_inputs(root),
        )

    @classmethod
    def git_begin_gate_capture(
        cls,
        request: m.Infra.GateCaptureBeginRequest,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> m.Infra.GateCaptureStart:
        """Inspect the candidate before its original producer executes.

        Returns:
            The retained pre-execution capture record.

        """
        root = request.repository_root
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        policy = c.Infra.GateAcceptancePolicy(inputs.spec.make.gate_acceptance_policy)
        return m.Infra.GateCaptureStart(
            repository_root=root,
            gate=request.gate,
            command=request.command,
            intent=request.intent,
            repository=(identity.value.origin_remote if identity.success else None),
            commit_sha=identity.value.head_oid if identity.success else None,
            tree_sha=cls._repo(root).commit(identity.value.head_oid).tree.hexsha
            if identity.success and identity.value.head_oid is not None
            else None,
            dirty=identity.value.dirty if identity.success else None,
            runtime_identity=request.runtime_identity,
            issue=identity.error if identity.failure else None,
            context_digest=cls._gate_capture_context_digest(
                request.gate,
                request.intent,
                inputs,
                request.runtime_identity,
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
        issue: str | None = None
        if inputs.failure:
            issue = inputs.error
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
                started,
                request.process,
                request.reports,
                after.value if after.success else None,
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
                        locations=(),
                        related_locations=(),
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
        after: m.Infra.GitIdentityReport | None,
    ) -> p.Result[m.Infra.GateCommandEvidence]:
        """Bind the original producer reports to the observed candidate.

        Returns:
            The resulting ``p.Result[m.Infra.GateCommandEvidence]``.

        """
        if not reports:
            return r[m.Infra.GateCommandEvidence].fail(
                "original producer has no complete report inventory",
            )
        evidence = m.Infra.GateCommandEvidence(
            scope="workspace",
            runtime_identity=started.runtime_identity,
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
            repository=started.repository,
            commit_sha=started.commit_sha,
            tree_sha=started.tree_sha,
            dirty=started.dirty,
            after_repository=after.origin_remote if after is not None else None,
            after_commit_sha=after.head_oid if after is not None else None,
            after_tree_sha=(
                cls._repo(started.repository_root).commit(after.head_oid).tree.hexsha
                if after is not None and after.head_oid is not None
                else None
            ),
            after_dirty=after.dirty if after is not None else None,
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
        receipt_digest: str,
    ) -> str:
        context = u.Cli.sha256_content(
            f"{request.context_digest}\n{request.policy}\n{request.policy_digest}",
        )
        return (
            f"{cls._TAG_PREFIX}/{receipt_digest.removeprefix('sha256:')}/"
            f"{context}/{request.expected_gates[0]}"
        )

    @staticmethod
    def _attestation_paths(
        request: m.Infra.GateAttestationCreateRequest
        | m.Infra.GateAttestationVerifyRequest,
    ) -> p.Result[t.Pair[Path, Path]]:
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        if not allowed.is_file():
            return r[t.Pair[Path, Path]].fail(
                f"allowed_signers file not found: {allowed}",
            )
        return r[t.Pair[Path, Path]].ok((repo_root, allowed))

    @classmethod
    def _attestation_predicate(
        cls,
        request: m.Infra.GateAttestationCreateRequest,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:

        repo_root = Path(request.workspace).expanduser().resolve()
        repo = cls._repo(repo_root)
        evidence_result = cls._original_gate_evidence(repo_root, request)
        if evidence_result.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(evidence_result)
        evidence, receipt = evidence_result.value
        receipt_matches = evidence.context_digest == request.context_digest
        policy_matches = (
            evidence.policy == request.policy
            and evidence.policy_digest == request.policy_digest
            and tuple(request.gates) == (evidence.gate,)
        )
        if not (receipt_matches and policy_matches):
            return r[m.Infra.GateAttestationPredicate].fail(
                "original workspace receipt does not match context or stage",
            )
        for validation in (
            lambda: cls._accepted_gate_evidence(repo_root, evidence),
            lambda: cls._verified_report_evidence(repo_root, evidence.reports),
        ):
            checked = validation()
            if checked.failure:
                return r[m.Infra.GateAttestationPredicate].from_failure(checked)
        toolchain = cls._toolchain_digest(repo_root, context)
        source = cls._report_bytes(repo_root, receipt)
        if source.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(source)
        with FlextInfraUtilitiesGitWorktreeIO.git_stdin(source.value) as stream:
            anchor = repo.git.hash_object("--stdin", istream=stream)
        predicate = m.Infra.GateAttestationPredicate(
            anchor_oid=anchor,
            signer=request.signer,
            toolchain_digest=toolchain,
            context_digest=evidence.context_digest,
            receipt=receipt,
            covered_gates=request.gates,
            commands=(evidence,),
        )
        return cls._attestation_predicate_from_value(repo_root, predicate, context).map(
            lambda _: predicate
        )

    @classmethod
    def _toolchain_digest(
        cls,
        repo_root: Path,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> str:
        inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repo_root
        ).unwrap()
        consumed = [inputs.spec.model_dump_json(round_trip=True)]
        consumed.extend(
            f"{source.path.name}:"
            + (
                u.Cli.sha256_bytes(source.content)
                if source.content is not None
                else "absent"
            )
            for source in inputs.sources
        )
        for path in (context.pyproject_path, context.lock_path):
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if state.content is None:
                msg = f"selected resolver input has no bytes: {path}"
                raise ValueError(msg)
            consumed.append(
                f"runtime:{path.relative_to(context.runtime_root).as_posix()}:"
                f"{u.Cli.sha256_bytes(state.content)}"
            )
        return f"sha256:{u.Cli.sha256_content('\n'.join(consumed))}"

    @classmethod
    def git_create_gate_attestation(
        cls,
        request: m.Infra.GateAttestationCreateRequest,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Sign original workspace execution on its selected Git storage anchor.

        Args:
            request: The validated request for the original workspace receipt.
            context: The elected runtime context the caller resolved at the
                workspace boundary; its toolchain inputs are hashed into the
                predicate's trust anchor.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationReport]``.

        """
        paths = cls._attestation_paths(request)
        if paths.failure:
            return r[m.Infra.GateAttestationReport].from_failure(paths)
        repo_root, allowed = paths.value
        predicate_result = cls._attestation_predicate(request, context)
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
            receipt=request.receipt,
            context_digest=predicate.context_digest,
            expected_gates=predicate.covered_gates,
            policy=predicate.commands[0].policy,
            policy_digest=predicate.commands[0].policy_digest,
        )
        return cls._publish_gate_tag(
            verification_request, predicate, serialized.value, context
        )

    @classmethod
    def _create_gate_tag(
        cls,
        repo_root: Path,
        tag: str,
        predicate: m.Infra.GateAttestationPredicate,
        serialized: str,
    ) -> p.Result[str]:
        source = cls._report_bytes(repo_root, predicate.receipt)
        if source.failure:
            return r[str].from_failure(source)
        repo = cls._repo(repo_root)
        with FlextInfraUtilitiesGitWorktreeIO.git_stdin(source.value) as stream:
            stored = repo.git.hash_object("-w", "--stdin", istream=stream)
        if stored != predicate.anchor_oid:
            return r[str].fail(
                "stored receipt blob differs from the validated original"
            )
        repo.git.tag(
            "--sign",
            "--annotate",
            "--message",
            serialized,
            tag,
            predicate.anchor_oid,
        )
        return r[str].ok(tag)

    @classmethod
    def _publish_gate_tag(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        predicate: m.Infra.GateAttestationPredicate,
        serialized: str,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        repo = cls._repo(repo_root)
        tag = cls._attestation_tag(request, predicate.receipt.digest)
        try:
            reused = tag in {item.name for item in repo.tags}
            if not reused:
                created = cls._create_gate_tag(repo_root, tag, predicate, serialized)
                if created.failure:
                    return r[m.Infra.GateAttestationReport].from_failure(created)
        except (GitCommandError, OSError, ValueError) as exc:
            return r[m.Infra.GateAttestationReport].fail(str(exc), exception=exc)
        verified = cls._verified_gate_predicate(
            request,
            repo_root,
            allowed,
            tag,
            context,
        )
        if verified.failure:
            return r[m.Infra.GateAttestationReport].from_failure(verified)
        if reused:
            stored = verified.value.model_dump(mode="json", round_trip=True)
            current = predicate.model_dump(mode="json", round_trip=True)
            fields = sorted(
                name
                for name in stored.keys() | current.keys()
                if stored.get(name) != current.get(name)
            )
            if fields:
                return r[m.Infra.GateAttestationReport].fail(
                    f"existing immutable stage proof differs from original "
                    f"evidence: {tag}; fields={','.join(fields)}",
                )
        return r[m.Infra.GateAttestationReport].ok(
            cls._attestation_report(tag, verified.value, reused=reused)
        )

    @classmethod
    def git_verify_gate_attestation(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Verify signature, original workspace receipt, and exact gate coverage.

        Args:
            request: The verification request carrying the expected digest.
            context: The current runtime context the caller resolved at the
                workspace boundary; hashing it must reproduce the attested
                toolchain digest or verification fails.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationReport]``.

        """
        paths = cls._attestation_paths(request)
        if paths.failure:
            return r[m.Infra.GateAttestationReport].from_failure(paths)
        repo_root, allowed = paths.value
        original = cls._original_gate_evidence(repo_root, request)
        if original.failure:
            return r[m.Infra.GateAttestationReport].from_failure(original)
        tag = cls._attestation_tag(request, original.value[1].digest)
        predicate_result = cls._verified_gate_predicate(
            request,
            repo_root,
            allowed,
            tag,
            context,
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
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        """Verify the tag signature and gate coverage against the predicate.

        Returns:
            The resulting ``p.Result[m.Infra.GateAttestationPredicate]``.

        """
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
        predicate_result = cls._predicate_from_tag(repo_root, tag)
        if predicate_result.failure:
            return r[m.Infra.GateAttestationPredicate].from_failure(predicate_result)
        predicate = predicate_result.value
        return cls._verify_predicate_evidence(
            request,
            predicate,
            verification.value,
            context,
        )

    @classmethod
    def _verify_predicate_evidence(
        cls,
        request: m.Infra.GateAttestationVerifyRequest,
        predicate: m.Infra.GateAttestationPredicate,
        output: p.Cli.CommandOutput,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        repo_root = Path(request.workspace).expanduser().resolve()
        checked = cls._attestation_predicate_from_value(
            repo_root,
            predicate,
            context,
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
        anchor = cls._repo(repo_root).rev_parse(predicate.anchor_oid)
        if anchor.type != "blob" or anchor.data_stream.read() != source.value:
            return r[bool].fail("attestation anchor is not the original receipt bytes")
        try:
            original = m.Infra.GateCommandEvidence.model_validate_json(source.value)
        except ValueError as exc:
            return r[bool].fail(str(exc), exception=exc)
        if original != predicate.commands[0]:
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
        message = tag_ref.tag.message.split(cls._SSH_SIGNATURE_MARKER, maxsplit=1)[0]
        try:
            predicate = m.Infra.GateAttestationPredicate.model_validate_json(message)
        except ValueError as exc:
            return r[m.Infra.GateAttestationPredicate].fail(str(exc), exception=exc)
        target = tag_ref.tag.object
        if target.type != "blob" or target.hexsha != predicate.anchor_oid:
            return r[m.Infra.GateAttestationPredicate].fail(
                "attestation tag target is not its original receipt blob"
            )
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _attestation_predicate_from_value(
        cls,
        repo_root: Path,
        predicate: m.Infra.GateAttestationPredicate,
        context: p.Infra.GateAttestationRuntimeContext,
    ) -> p.Result[bool]:

        actual_toolchain = cls._toolchain_digest(repo_root, context)
        facts = predicate.commands[0]
        inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repo_root
        )
        if inputs.failure:
            return r[bool].from_failure(inputs)
        actual_context = cls._gate_capture_context_digest(
            facts.gate, facts.intent, inputs.value, facts.runtime_identity
        )
        mismatches = tuple(
            field
            for field, matches in (
                ("toolchain", predicate.toolchain_digest == actual_toolchain),
                ("context", predicate.context_digest == actual_context),
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
            anchor_oid=predicate.anchor_oid,
            signer=predicate.signer,
            covered_gates=predicate.covered_gates,
            context_digest=predicate.context_digest,
            reused=reused,
        )


__all__: list[str] = ["FlextInfraUtilitiesGitAttestationMixin"]
