"""Behavior tests for local SSH-signed gate attestations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config, m, p
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, t, tm, u


class TestsFlextInfraGithubGateAttestation:
    """Behavior tests for local SSH-signed gate attestations."""

    @staticmethod
    def _context(root: Path) -> m.Infra.WorkspaceRuntimeContext:
        """Elect the runtime context at the workspace boundary for the root.

        Returns:
            The resulting ``m.Infra.WorkspaceRuntimeContext``.

        """
        return tm.ok(
            FlextInfraWorkspaceDetector.resolution_context(
                root.expanduser().resolve(),
            ),
        )

    @staticmethod
    def _runtime_identity(gate_ids: t.StrSequence) -> p.Result[str]:
        """Read real installed provenance and selected native scanner identities.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return FlextInfraGateRegistry.default().runtime_identity(
            gate_ids,
            installed_identity=(
                FlextInfraWorkspaceEnvironmentProvenance.installed_toolchain_identity()
            ),
        )

    @staticmethod
    def _signed_repository(root: Path) -> Path:
        u.Tests.git_bootstrap(root, ("init", "-b", c.Infra.GIT_MAIN))
        for key, value in (
            ("user.name", "Attestation Test"),
            ("user.email", "attestation@example.test"),
            ("gpg.format", "ssh"),
            ("commit.gpgsign", c.ParserBooleanToken.FALSE),
        ):
            u.Tests.git_bootstrap(root, ("config", key, value))
        u.Tests.git_bootstrap(
            root,
            (
                "remote",
                "add",
                c.Infra.GIT_ORIGIN,
                "https://github.example/flext/fixture.git",
            ),
        )
        key_path = root / "signing_key"
        tm.ok(
            u.Cli.run_raw(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
                cwd=root,
            ),
        )
        u.Tests.git_bootstrap(root, ("config", "user.signingkey", str(key_path)))
        (root / "tracked.txt").write_text("attested\n", encoding="utf-8")
        (root / "Makefile").write_text(
            f".PHONY: {c.Infra.VERB_CHECK}\n"
            f"{c.Infra.VERB_CHECK}:\n"
            "\t@printf 'executed\\n' >> invocations.txt\n"
            "\t@sleep $(ATTEST_PROBE_DELAY)\n"
            f"\t@{quote(sys.executable)} -m flext_infra "
            f"{c.Infra.CLI_GROUP_WORKSPACE} capture-gate "
            f"--repository-root . --gates {c.Infra.LINT}\n"
            "ATTEST_PROBE_DELAY ?= 0\n",
            encoding="utf-8",
        )
        u.Tests.WorktreeFixture.write_python_project(root, "fixture")
        source = root / c.Infra.DEFAULT_SRC_DIR
        (source / "consumer.py").write_text("import os\n", encoding="utf-8")
        # Resolver inputs remain untracked: execution proof binds their live bytes.
        context = TestsFlextInfraGithubGateAttestation._context(root)
        context.resolution_root.mkdir(parents=True, exist_ok=True)
        context.pyproject_path.write_bytes((root / c.PYPROJECT_FILENAME).read_bytes())
        context.lock_path.write_text("version = 1\n", encoding="utf-8")
        tm.ok(
            u.Infra.git_add_paths(
                m.Infra.GitPathsRequest(
                    repo_root=root,
                    paths=(
                        "Makefile",
                        c.PYPROJECT_FILENAME,
                        "tracked.txt",
                        c.Infra.DEFAULT_SRC_DIR,
                    ),
                ),
            ),
        )
        tm.ok(
            u.Infra.git_commit(
                m.Infra.GitCommitRequest(
                    repo_root=root,
                    message="test: create base revision",
                ),
            ),
        )
        allowed_signers = root / "allowed_signers"
        public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
        allowed_signers.write_text(
            f"attester@example.test {public_key}\n",
            encoding="utf-8",
        )
        return allowed_signers

    @staticmethod
    def _head(root: Path) -> str:
        oid: str = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=root)),
        ).oid
        return oid

    @staticmethod
    def _rev_parse(root: Path, commitish: str) -> str:
        oid: str = tm.ok(
            u.Infra.git_rev_parse(
                m.Infra.GitCommitishRequest(repo_root=root, commitish=commitish),
            ),
        ).oid
        return oid

    @pytest.fixture
    def signed_repository_factory(self) -> Callable[[Path], Path]:
        """Create one SSH-signing fixture repository per test invocation.

        Returns:
            The resulting ``Callable[[Path], Path]``.

        """
        return self._signed_repository

    @pytest.mark.parametrize("phase", tuple(c.Infra.CheckPhase))
    def test_original_capture_publishes_distinct_receipts_with_stable_context(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        phase: c.Infra.CheckPhase,
    ) -> None:
        """The original public capture binds each run without changing its status."""
        signed_repository_factory(tmp_path)
        request = m.Infra.GateCaptureRequest(
            repository_root=tmp_path,
            gates=c.Infra.LINT if phase == c.Infra.CheckPhase.COMPLETE else None,
            phase=phase,
        )
        first = tm.ok(
            u.Infra.git_capture_gate(
                request,
                inputs=tm.ok(u.Infra.load_codegen_inputs(tmp_path)),
                load_inputs=u.Infra.load_codegen_inputs,
                read_runtime_identity=self._runtime_identity,
            )
        )
        second = tm.ok(
            u.Infra.git_capture_gate(
                request,
                inputs=tm.ok(u.Infra.load_codegen_inputs(tmp_path)),
                load_inputs=u.Infra.load_codegen_inputs,
                read_runtime_identity=self._runtime_identity,
            )
        )
        first_receipt = tm.not_none(first.receipt)
        second_receipt = tm.not_none(second.receipt)
        tm.that(first_receipt != second_receipt, truth=True)
        first_evidence = m.Infra.GateCommandEvidence.model_validate_json(
            first_receipt.read_bytes(),
        )
        second_evidence = m.Infra.GateCommandEvidence.model_validate_json(
            second_receipt.read_bytes(),
        )
        tm.that(first_evidence.process == first.process, truth=True)
        tm.that(second_evidence.process == second.process, truth=True)
        tm.that(first_evidence.intent.phase, eq=phase)
        tm.that(second_evidence.intent.phase, eq=phase)
        tm.that(
            first_evidence.context_digest == second_evidence.context_digest, truth=True
        )
        tm.that(
            first_evidence.native_outcome == c.Infra.ToolOutcome.FINDINGS, truth=True
        )
        tm.that(first.process.raw_return_code != 0, truth=True)
        tm.that(first.issues, truth=False)
        for report in first_evidence.reports:
            tm.that(
                report.path.is_relative_to(first_receipt.parent.relative_to(tmp_path)),
                truth=True,
            )
            digest = u.Cli.sha256_bytes((tmp_path / report.path).read_bytes())
            tm.that(report.digest == f"sha256:{digest}", truth=True)
            summary = tm.not_none(
                m.Infra.SarifReport.model_validate_json(
                    (tmp_path / report.path).read_bytes()
                ).properties
            )
            tm.that(summary.phase, eq=phase)
            tm.that(
                tuple(summary.requested_gates), eq=first_evidence.intent.requested_gates
            )

    @staticmethod
    @pytest.mark.parametrize("literal_prefix", [None, "", "key::"])
    def test_signing_identity_reads_only_native_public_references(
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        literal_prefix: str | None,
    ) -> None:
        """Public identity queries preserve provenance without exporting key bytes."""
        allowed = signed_repository_factory(tmp_path)
        key_path = tmp_path / "signing_key"
        if literal_prefix is not None:
            public = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
            u.Tests.git_bootstrap(
                tmp_path,
                ("config", "user.signingkey", literal_prefix + public),
            )
        metadata = tm.ok(u.Infra.read_project_metadata_result(tmp_path))
        tm.that(metadata.project.version, eq=config.Infra.initial_project_version)
        tm.that(
            metadata.project.requires_python,
            eq=config.Infra.codegen.toolchain.python_required_version,
        )
        key_path = tmp_path / "signing_key"
        public = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
        if literal_prefix is not None:
            u.Tests.git_bootstrap(
                tmp_path,
                ("config", "user.signingkey", literal_prefix + public),
            )
        u.Tests.git_bootstrap(
            tmp_path,
            ("config", "gpg.ssh.allowedSignersFile", str(allowed)),
        )
        report = tm.ok(
            u.Infra.git_signing_identity(
                m.Infra.GitRepoRequest(repo_root=tmp_path),
            )
        )
        tm.that(report.signing_format, eq="ssh")
        tm.that(report.key_path, eq=key_path if literal_prefix is None else None)
        tm.that(report.inline_public_key, eq=literal_prefix is not None)
        tm.that(report.allowed_signers_path, eq=allowed)
        tm.that(report.public_fingerprint, eq=None)
        tm.that(
            tuple(item.key for item in report.observations),
            eq=c.Infra.GIT_SIGNING_CONFIGURATION_KEYS,
        )
        for item in report.observations:
            tm.that(item.scope, eq="local")
            tm.that(tm.not_none(item.origin).startswith("file:"), truth=True)
            tm.that(item.process.raw_return_code, eq=0)
        encoded = report.model_dump_json(round_trip=True)
        tm.that(encoded, lacks=["BEGIN OPENSSH PRIVATE KEY", '"value"'])
        tm.that(public not in encoded, truth=True)
        restored = m.Infra.GitSigningIdentityReport.model_validate_json(encoded)
        tm.that(restored.key_path, eq=report.key_path)
        tm.that(restored.allowed_signers_path, eq=report.allowed_signers_path)

    @staticmethod
    @pytest.mark.parametrize("literal_prefix", ["", "key::"])
    @pytest.mark.parametrize(
        "corruption",
        ["empty", "missing-payload", "encoding", "type", "truncated"],
    )
    def test_signing_identity_rejects_malformed_inline_public_declarations(
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        literal_prefix: str,
        corruption: str,
    ) -> None:
        """Native literal prefixes never send malformed public text into a Path."""
        signed_repository_factory(tmp_path)
        public = (tmp_path / "signing_key.pub").read_text(encoding="utf-8").strip()
        kind, encoded, *_ = public.split(maxsplit=2)
        match corruption:
            case "empty":
                payload = ""
            case "missing-payload":
                payload = kind
            case "encoding":
                payload = f"{kind} !{encoded}"
            case "type":
                payload = f"{kind}-invalid {encoded}"
            case "truncated":
                payload = f"{kind} {encoded[:4]}"
            case _:
                tm.reject(corruption)
        u.Tests.git_bootstrap(
            tmp_path,
            ("config", "user.signingkey", literal_prefix + payload),
        )
        failed = u.Infra.git_signing_identity(
            m.Infra.GitRepoRequest(repo_root=tmp_path)
        )
        tm.fail(failed)
        error = tm.not_none(failed.error)
        if payload:
            tm.that(payload not in error, truth=True)

    @staticmethod
    @pytest.mark.parametrize(
        "declarations",
        [
            (),
            (("gpg.format", "ssh"),),
            (("gpg.format", "openpgp"),),
            (("gpg.format", "x509"),),
        ],
    )
    def test_public_signing_observation_preserves_undeclared_native_facts(
        tmp_path: Path,
        declarations: tuple[t.Pair[str, str], ...],
    ) -> None:
        """Native absence is observable, not selection of a signing capability."""
        u.Tests.git_bootstrap(tmp_path, ("init", "-b", c.Infra.GIT_MAIN))
        u.Tests.git_bootstrap(
            tmp_path, ("config", "commit.gpgsign", c.ParserBooleanToken.FALSE)
        )
        u.Tests.initialize_git_repo(tmp_path)
        isolated = tmp_path / "isolated.gitconfig"
        isolated.write_text("", encoding="utf-8")
        for key, value in declarations:
            u.Tests.git_bootstrap(tmp_path, ("config", key, value))
        native = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    "flext_infra",
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "signing-identity",
                    "--repo-root",
                    str(tmp_path),
                ],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        "GIT_CONFIG_GLOBAL": str(isolated),
                        "GIT_CONFIG_SYSTEM": str(isolated),
                    },
                    remove_env_keys=u.Tests.isolated_git_keys(),
                ),
            ),
        )
        process = m.Cli.ProcessOutcome.model_validate(
            native.outcome,
            from_attributes=True,
        )
        tm.that(u.Cli.process_succeeded(process), truth=True, msg=native.stderr)
        report = m.Infra.GitSigningIdentityReport.model_validate_json(native.stdout)
        tm.that(
            tuple(item.key for item in report.observations)
            == (c.Infra.GIT_SIGNING_CONFIGURATION_KEYS),
            truth=True,
        )
        for observation in report.observations:
            declared = next(
                (value for key, value in declarations if key == observation.key),
                None,
            )
            tm.that(
                observation.process.raw_return_code == (1 if declared is None else 0),
                truth=True,
            )
            tm.that(
                observation.scope == (None if declared is None else "local"), truth=True
            )
            tm.that(observation.origin is None, eq=declared is None)
        tm.that(
            report.signing_format
            == next(
                (value for key, value in declarations if key == "gpg.format"),
                None,
            ),
            truth=True,
        )
        tm.that(report.key_path, none=True)
        tm.that(report.allowed_signers_path, none=True)
        tm.that(report.public_fingerprint, none=True)
        tm.that(report.inline_public_key, truth=False)
        tm.that('"value"' not in native.stdout, truth=True)
        tm.that(isolated.read_bytes(), truth=False)

    @staticmethod
    @pytest.mark.parametrize(
        ("key", "value"),
        [
            *((key, "") for key in c.Infra.GIT_SIGNING_CONFIGURATION_KEYS),
            ("gpg.format", "unsupported"),
        ],
    )
    def test_signing_identity_rejects_invalid_native_declarations(
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        key: str,
        value: str,
    ) -> None:
        """Empty references and unsupported formats never become absent facts."""
        signed_repository_factory(tmp_path)
        u.Tests.git_bootstrap(tmp_path, ("config", key, value))
        tm.fail(
            u.Infra.git_signing_identity(m.Infra.GitRepoRequest(repo_root=tmp_path))
        )

    @staticmethod
    def test_signing_identity_preserves_native_invalid_configuration_failure(
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Malformed physical fixture config remains a native Git failure."""
        signed_repository_factory(tmp_path)
        configuration = tmp_path / c.GIT_DIR_NAME / "config"
        configuration.write_text(
            configuration.read_text(encoding="utf-8") + "\n[broken\n",
            encoding="utf-8",
        )
        native = tm.ok(
            u.Cli.run_raw(
                (
                    "git",
                    "config",
                    "get",
                    "--null",
                    "--show-origin",
                    "--show-scope",
                    c.Infra.GIT_SIGNING_CONFIGURATION_KEYS[0],
                ),
                cwd=tmp_path,
            )
        )
        process = m.Cli.ProcessOutcome.model_validate(
            native.outcome,
            from_attributes=True,
        )
        tm.that(u.Cli.process_succeeded(process), truth=False)
        tm.that(native.stderr, empty=False)
        failed = u.Infra.git_signing_identity(
            m.Infra.GitRepoRequest(repo_root=tmp_path)
        )
        tm.fail(failed)
        tm.that(failed.error, eq=native.stderr)

    def test_capture_uses_target_policy_and_configuration_context(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Uncommitted target config is a bound input, not ambient policy."""
        signed_repository_factory(tmp_path)
        config_dir = tmp_path / c.Infra.CODEGEN_CONFIG_DIR
        config_dir.mkdir()
        declaration = config_dir / c.Infra.CODEGEN_CONFIG_FILENAME
        request = m.Infra.GateCaptureRequest(
            repository_root=tmp_path,
            gates=c.Infra.LINT,
        )
        observed: list[m.Infra.GateCommandEvidence] = []
        for policy in c.Infra.GateAcceptancePolicy:
            declaration.write_text(
                "Infra:\n  codegen:\n    make:\n"
                f"      gate_acceptance_policy: {policy.value}\n"
                f"      gate_receipts_directory: .reports/{policy.value}\n",
                encoding="utf-8",
            )
            inputs = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
            captured = tm.ok(
                u.Infra.git_capture_gate(
                    request,
                    inputs=inputs,
                    load_inputs=u.Infra.load_codegen_inputs,
                    read_runtime_identity=self._runtime_identity,
                )
            )
            receipt = tm.not_none(captured.receipt)
            tm.that(
                receipt.is_relative_to(
                    tmp_path / inputs.spec.make.gate_receipts_directory
                ),
                truth=True,
            )
            evidence = m.Infra.GateCommandEvidence.model_validate_json(
                receipt.read_bytes(),
            )
            tm.that(
                evidence.policy,
                eq=inputs.spec.make.gate_acceptance_policy,
            )
            tm.that(evidence.process, eq=captured.process)
            tm.that(
                receipt.read_text(encoding="utf-8"),
                lacks=[str(tmp_path), "gate_acceptance_policy:"],
            )
            observed.append(evidence)
        tm.that(len({item.context_digest for item in observed}), eq=len(observed))
        tm.that(len({item.commit_sha for item in observed}) == 1, truth=True)

    @staticmethod
    def test_signing_identity_does_not_open_missing_key_or_trust_files(
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """A declared unavailable file remains a reference, never verified trust."""
        signed_repository_factory(tmp_path)
        missing_key = tmp_path / "unavailable-key"
        missing_trust = tmp_path / "unavailable-trust"
        for setting, path in (
            ("user.signingkey", missing_key),
            ("gpg.ssh.allowedSignersFile", missing_trust),
        ):
            u.Tests.git_bootstrap(tmp_path, ("config", setting, str(path)))
        report = tm.ok(
            u.Infra.git_signing_identity(
                m.Infra.GitRepoRequest(repo_root=tmp_path),
            )
        )
        tm.that(report.key_path, eq=missing_key)
        tm.that(report.allowed_signers_path, eq=missing_trust)
        tm.that(report.public_fingerprint, eq=None)
        tm.fail(missing_key.exists())
        tm.fail(missing_trust.exists())

    @pytest.mark.parametrize("missing", ["key", "trust"])
    def test_selected_attestation_still_requires_real_signing_material(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        missing: str,
    ) -> None:
        """Read-only discovery cannot satisfy explicitly selected native signing."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        unavailable = tmp_path / f"unavailable-{missing}"
        if missing == "key":
            u.Tests.git_bootstrap(
                tmp_path,
                ("config", "user.signingkey", str(unavailable)),
            )
        else:
            request = request.model_copy(update={"allowed_signers": str(unavailable)})
        failed = u.Infra.git_create_gate_attestation(
            request,
            self._context(tmp_path),
        )
        tm.fail(failed)
        tm.that(str(unavailable) in tm.not_none(failed.error), truth=True)
        tm.that(unavailable.exists(), truth=False)
        if missing == "trust":
            verification = u.Infra.git_verify_gate_attestation(
                m.Infra.GateAttestationVerifyRequest(
                    workspace=request.workspace,
                    allowed_signers=request.allowed_signers,
                    expected_gates=request.gates,
                    receipt=request.receipt,
                    context_digest=request.context_digest,
                    policy=request.policy,
                    policy_digest=request.policy_digest,
                ),
                self._context(tmp_path),
            )
            tm.fail(verification)
            tm.that(str(unavailable) in tm.not_none(verification.error), truth=True)

    @pytest.mark.parametrize("has_origin", [False, True])
    def test_dirty_workspace_publishes_original_execution_evidence(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        *,
        has_origin: bool,
    ) -> None:
        """Tracked and untracked WIP remain truthful, non-gating observations."""
        signed_repository_factory(tmp_path)
        if not has_origin:
            u.Tests.git_bootstrap(tmp_path, ("remote", "remove", c.Infra.GIT_ORIGIN))
        (tmp_path / "tracked.txt").write_text("uncommitted\n", encoding="utf-8")
        (tmp_path / "untracked.txt").write_text("shared\n", encoding="utf-8")
        captured = tm.ok(
            u.Infra.git_capture_gate(
                m.Infra.GateCaptureRequest(
                    repository_root=tmp_path,
                    gates=c.Infra.LINT,
                ),
                inputs=tm.ok(u.Infra.load_codegen_inputs(tmp_path)),
                load_inputs=u.Infra.load_codegen_inputs,
                read_runtime_identity=self._runtime_identity,
            )
        )
        tm.that(captured.process.raw_return_code != 0, truth=True)
        receipt = tm.not_none(captured.receipt)
        tm.that(captured.issues, empty=True)
        evidence = m.Infra.GateCommandEvidence.model_validate_json(receipt.read_bytes())
        tm.that(evidence.scope, eq="workspace")
        tm.that(evidence.dirty, eq=True)
        tm.that(evidence.after_dirty, eq=True)
        tm.that(evidence.repository is not None, eq=has_origin)
        tm.that(evidence.after_repository is not None, eq=has_origin)
        tm.that(evidence.process, eq=captured.process)
        tm.that(tuple(tmp_path.rglob(c.Infra.CHECK_REPORT_SARIF_FILENAME)), truth=True)

    def test_capture_does_not_require_a_committed_git_identity(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """An unborn workspace captures and signs receipt bytes without a commit."""
        u.Tests.git_bootstrap(tmp_path, ("init", "-b", c.Infra.GIT_MAIN))
        u.Tests.WorktreeFixture.write_python_project(tmp_path, "fixture")
        (tmp_path / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "import os\n", encoding=c.DEFAULT_ENCODING
        )
        context = self._context(tmp_path)
        context.resolution_root.mkdir(parents=True, exist_ok=True)
        context.pyproject_path.write_bytes(
            (tmp_path / c.PYPROJECT_FILENAME).read_bytes()
        )
        context.lock_path.write_text("version = 1\n", encoding=c.DEFAULT_ENCODING)
        captured = tm.ok(
            u.Infra.git_capture_gate(
                m.Infra.GateCaptureRequest(
                    repository_root=tmp_path, gates=c.Infra.LINT
                ),
                inputs=tm.ok(u.Infra.load_codegen_inputs(tmp_path)),
                load_inputs=u.Infra.load_codegen_inputs,
                read_runtime_identity=self._runtime_identity,
            )
        )
        receipt = tm.not_none(captured.receipt)
        evidence = m.Infra.GateCommandEvidence.model_validate_json(receipt.read_bytes())
        tm.that(evidence.commit_sha, none=True)
        tm.that(evidence.tree_sha, none=True)
        tm.that(evidence.dirty, none=True)
        tm.that(evidence.after_commit_sha, none=True)
        tm.that(evidence.after_dirty, none=True)
        tm.that(evidence.process, eq=captured.process)
        tm.that(captured.issues, empty=True)
        signer = tmp_path.with_name(tmp_path.name + "-signer")
        signer.mkdir()
        allowed = signed_repository_factory(signer)
        for key, value in (
            ("user.name", "Workspace Signer"),
            ("user.email", "workspace@example.test"),
            ("gpg.format", "ssh"),
            ("user.signingkey", str(signer / "signing_key")),
        ):
            u.Tests.git_bootstrap(tmp_path, ("config", key, value))
        tm.ok(u.Infra.git_signing_identity(m.Infra.GitRepoRequest(repo_root=tmp_path)))
        request = m.Infra.GateAttestationCreateRequest(
            workspace=str(tmp_path),
            signer="attester@example.test",
            gates=(evidence.gate,),
            receipt=receipt,
            allowed_signers=str(allowed),
            context_digest=evidence.context_digest,
            policy=evidence.policy,
            policy_digest=evidence.policy_digest,
        )
        created = tm.ok(u.Infra.git_create_gate_attestation(request, context))
        verified = tm.ok(
            self._verify(tmp_path, allowed, request.receipt, evidence.gate)
        )
        tm.that(verified.anchor_oid, eq=created.anchor_oid)
        tm.that(self._rev_parse(tmp_path, f"{created.tag}^{{}}"), eq=created.anchor_oid)
        tm.fail(u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=tmp_path)))

    def test_changed_consumed_configuration_requires_scope_revalidation(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Git movement is irrelevant but changed effective inputs are not."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        directory = tmp_path / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir(exist_ok=True)
        (directory / c.Infra.CODEGEN_CONFIG_FILENAME).write_text(
            "Infra:\n  codegen:\n    make:\n"
            "      gate_receipts_directory: .reports/changed-scope\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.fail(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))

    @classmethod
    def _request(cls, root: Path) -> m.Infra.GateAttestationCreateRequest:
        """Consume the receipt automatically emitted by the original Make run.

        Returns:
            The resulting ``m.Infra.GateAttestationCreateRequest``.

        """
        receipts = (
            root
            / tm.ok(u.Infra.load_codegen_inputs(root)).spec.make.gate_receipts_directory
        )
        previous = set(receipts.rglob(c.Infra.GATE_ORIGINAL_RECEIPT_FILENAME))
        tm.ok(u.Cli.run_raw(["make", c.Infra.VERB_CHECK], cwd=root))
        published = (
            set(receipts.rglob(c.Infra.GATE_ORIGINAL_RECEIPT_FILENAME)) - previous
        )
        tm.that(len(published) == 1, truth=True)
        receipt = published.pop()
        evidence = m.Infra.GateCommandEvidence.model_validate_json(receipt.read_bytes())
        return m.Infra.GateAttestationCreateRequest(
            workspace=str(root),
            signer="attester@example.test",
            gates=(c.Infra.VERB_CHECK,),
            receipt=receipt,
            allowed_signers=str(root / "allowed_signers"),
            context_digest=evidence.context_digest,
            policy=evidence.policy,
            policy_digest=evidence.policy_digest,
        )

    @staticmethod
    def _verify(
        root: Path,
        allowed_signers: Path,
        receipt: Path,
        *gates: str,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        evidence = m.Infra.GateCommandEvidence.model_validate_json(receipt.read_bytes())
        return u.Infra.git_verify_gate_attestation(
            m.Infra.GateAttestationVerifyRequest(
                workspace=str(root),
                allowed_signers=str(allowed_signers),
                expected_gates=gates,
                receipt=receipt,
                context_digest=evidence.context_digest,
                policy=evidence.policy,
                policy_digest=evidence.policy_digest,
            ),
            TestsFlextInfraGithubGateAttestation._context(root),
        )

    @pytest.mark.parametrize("change", ["none", "republish", "remote-suffix", "commit"])
    def test_signed_gate_attestation_round_trip_is_local(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        change: str,
    ) -> None:
        """Original receipt proof survives republication and unrelated Git changes."""
        allowed_signers = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        context = self._context(tmp_path)
        created = tm.ok(
            u.Infra.git_create_gate_attestation(request, context),
        )
        tm.that(
            self._rev_parse(tmp_path, f"{created.tag}^{{}}"),
            eq=created.anchor_oid,
        )
        if change == "republish":
            before = (tmp_path / "invocations.txt").read_bytes()
            reused = tm.ok(u.Infra.git_create_gate_attestation(request, context))
            tm.fail(created.reused)
            tm.ok(reused.reused)
            tm.that(reused.tag, eq=created.tag)
            tm.that((tmp_path / "invocations.txt").read_bytes(), eq=before)
        elif change == "remote-suffix":
            remote = tm.ok(
                u.Infra.git_remote_url(m.Infra.GitRemoteUrlRequest(repo_root=tmp_path)),
            ).text
            u.Tests.git_bootstrap(
                tmp_path,
                (
                    "remote",
                    "set-url",
                    c.Infra.GIT_ORIGIN,
                    remote.removesuffix(c.GIT_DIR_NAME),
                ),
            )
        elif change == "commit":
            selected_tree = self._rev_parse(tmp_path, "HEAD^{tree}")
            unrelated = tmp_path / "another-lane.txt"
            unrelated.write_text("new work\n", encoding=c.DEFAULT_ENCODING)
            tm.ok(
                u.Infra.git_add_paths(
                    m.Infra.GitPathsRequest(repo_root=tmp_path, paths=(unrelated.name,))
                )
            )
            tm.ok(
                u.Infra.git_commit(
                    m.Infra.GitCommitRequest(
                        repo_root=tmp_path,
                        message="test: later unrelated fixture commit",
                    ),
                ),
            )
            tm.that(self._rev_parse(tmp_path, "HEAD^{tree}"), ne=selected_tree)
        verified = tm.ok(
            self._verify(tmp_path, allowed_signers, request.receipt, c.Infra.VERB_CHECK)
        )
        tm.that(verified.signer, eq="attester@example.test")
        tm.that(verified.anchor_oid, eq=created.anchor_oid)

    @pytest.mark.parametrize("has_origin", [False, True])
    def test_original_findings_keep_their_real_nonzero_exit_in_signed_evidence(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        *,
        has_origin: bool,
    ) -> None:
        """Completed Ruff findings prove execution without claiming quality passed."""
        allowed = signed_repository_factory(tmp_path)
        if not has_origin:
            u.Tests.git_bootstrap(tmp_path, ("remote", "remove", c.Infra.GIT_ORIGIN))
        (tmp_path / "tracked.txt").write_text(
            "working copy\n", encoding=c.DEFAULT_ENCODING
        )
        (tmp_path / "untracked.txt").write_text("shared\n", encoding=c.DEFAULT_ENCODING)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        tm.ok(source.process.raw_return_code != 0)
        tm.that(source.native_outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(source.dirty, eq=True)
        tm.that(source.scope, eq="workspace")
        tm.ok(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))
        destination = tmp_path / c.Infra.REPORTS_DIR_NAME / "verified-proof.json"
        verified = u.Infra.git_verify_gate_attestation(
            m.Infra.GateAttestationVerifyRequest(
                workspace=str(tmp_path),
                allowed_signers=str(allowed),
                expected_gates=request.gates,
                receipt=request.receipt,
                context_digest=request.context_digest,
                policy=request.policy,
                policy_digest=request.policy_digest,
                output=str(destination),
            ),
            self._context(tmp_path),
        )
        tm.ok(verified)
        predicate = m.Infra.GateAttestationPredicate.model_validate_json(
            destination.read_bytes()
        )
        tm.that(
            predicate.commands[0].process.raw_return_code,
            eq=source.process.raw_return_code,
        )
        tm.that(predicate.commands[0].native_outcome, eq=source.native_outcome)
        tm.that(destination.read_text(encoding="utf-8"), lacks=str(tmp_path))

    @pytest.mark.parametrize("corruption", ["modified", "missing"])
    def test_original_report_integrity_is_required_for_proof(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        corruption: str,
    ) -> None:
        """Publication and signed reuse require unchanged original producer bytes."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        report = tmp_path / source.reports[0].path
        if corruption == "modified":
            report.write_text("{}\n", encoding="utf-8")
            tm.fail(
                u.Infra.git_create_gate_attestation(request, self._context(tmp_path))
            )
        else:
            tm.ok(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))
            report.unlink()
            tm.fail(
                self._verify(tmp_path, allowed, request.receipt, c.Infra.VERB_CHECK)
            )
        tm.that(
            (tmp_path / "invocations.txt").read_text(encoding="utf-8").splitlines(),
            eq=["executed"],
        )

    @pytest.mark.parametrize("mismatch", ["context", "stage"])
    def test_verification_requires_original_context_and_stage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
        mismatch: str,
    ) -> None:
        """Another exact context or unpublished stage remains outside coverage."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))
        digest = (
            f"sha256:{u.Cli.sha256_content('different runtime context')}"
            if mismatch == "context"
            else request.context_digest
        )

        tm.fail(
            u.Infra.git_verify_gate_attestation(
                m.Infra.GateAttestationVerifyRequest(
                    workspace=str(tmp_path),
                    allowed_signers=str(allowed),
                    expected_gates=(
                        request.gates if mismatch == "context" else (c.Infra.VERB_TEST,)
                    ),
                    receipt=request.receipt,
                    context_digest=digest,
                    policy=request.policy,
                    policy_digest=request.policy_digest,
                ),
                self._context(tmp_path),
            ),
        )

    def test_untrusted_signing_key_cannot_verify_an_existing_stage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Native SSH verification rejects an unrelated key under the same principal."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))
        foreign = tmp_path / "foreign-signing-key"
        tm.ok(
            u.Cli.run_raw(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(foreign)],
                cwd=tmp_path,
            ),
        )
        allowed.write_text(
            "attester@example.test "
            + foreign.with_suffix(".pub").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        tm.fail(self._verify(tmp_path, allowed, request.receipt, c.Infra.VERB_CHECK))

    def test_real_make_timeout_cannot_borrow_an_earlier_complete_report(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """A reaped timeout cannot borrow an earlier complete report."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        started = datetime.now(UTC)
        command = ["make", c.Infra.VERB_CHECK, "ATTEST_PROBE_DELAY=2"]
        command_digest = f"sha256:{u.Cli.sha256_content(' '.join(command))}"
        interrupted = tm.ok(u.Cli.run_raw(command, cwd=tmp_path, timeout=1))
        tm.ok(interrupted.outcome.timed_out)
        updated = source.model_copy(
            update={
                "command_digest": command_digest,
                "process": m.Cli.ProcessOutcome.model_validate(
                    interrupted.outcome,
                    from_attributes=True,
                ),
                "started_at": started.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                request.receipt,
                updated.model_dump_json(round_trip=True),
            ),
        )

        tm.fail(u.Infra.git_create_gate_attestation(request, self._context(tmp_path)))
        tm.that(
            (tmp_path / "invocations.txt").read_text(encoding="utf-8").splitlines(),
            eq=["executed", "executed"],
        )

    def test_gate_attestation_rejects_duplicate_gate_coverage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test gate attestation rejects duplicate gate coverage."""
        _allowed_signers = signed_repository_factory(tmp_path)
        values = self._request(tmp_path).model_dump()
        values["gates"] = (c.Infra.VERB_CHECK, c.Infra.VERB_CHECK)

        with pytest.raises(ValueError, match="at most 1 item"):
            m.Infra.GateAttestationCreateRequest.model_validate(values)
