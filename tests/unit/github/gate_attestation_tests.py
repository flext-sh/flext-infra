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
from flext_cli import u as cli_u

from flext_infra import c, m, p
from tests import tm, u


class TestsFlextInfraGithubGateAttestation:
    """Behavior tests for local SSH-signed gate attestations."""

    @staticmethod
    def _signed_repository(root: Path) -> Path:
        u.Tests.git_bootstrap(root, ("init", "-b", c.Infra.GIT_MAIN))
        for key, value in (
            ("user.name", "Attestation Test"),
            ("user.email", "attestation@example.test"),
            ("gpg.format", "ssh"),
            ("commit.gpgsign", "false"),
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
            cli_u.Cli.run_raw(
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
            f"{c.Infra.CLI_GROUP_CHECK} {c.Infra.VERB_RUN} "
            f"--repository-root . --gates {c.Infra.LINT}\n"
            "ATTEST_PROBE_DELAY ?= 0\n",
            encoding="utf-8",
        )
        (root / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n",
            encoding="utf-8",
        )
        (root / "consumer.py").write_text("import os\n", encoding="utf-8")
        tm.ok(
            u.Infra.git_add_paths(
                m.Infra.GitPathsRequest(
                    repo_root=root,
                    paths=("Makefile", "pyproject.toml", "tracked.txt", "consumer.py"),
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

    @classmethod
    def _request(cls, root: Path) -> m.Infra.GateAttestationCreateRequest:
        """Capture one real Make/check run before the signer consumes evidence."""
        started = datetime.now(UTC)
        output = tm.ok(cli_u.Cli.run_raw(["make", c.Infra.VERB_CHECK], cwd=root))
        completed = datetime.now(UTC)
        reports_dir = m.Infra.RunCommand(repository_root=root).reports_dir_path
        sarif = next(reports_dir.rglob(c.Infra.CHECK_REPORT_SARIF_FILENAME))
        report = m.Infra.SarifReport.model_validate_json(sarif.read_bytes())
        assert report.properties is not None
        native = report.properties.results[0].gates[c.Infra.LINT].outcome
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        assert identity.origin_remote is not None
        policy = c.Infra.GateAcceptancePolicy.COMPLETE_EXECUTION
        context_digest = (
            f"sha256:{cli_u.Cli.sha256_content(sys.version + sys.platform)}"
        )
        policy_digest = f"sha256:{cli_u.Cli.sha256_content(policy.value)}"
        evidence = m.Infra.GateCommandEvidence(
            gate=c.Infra.VERB_CHECK,
            command=f"make {c.Infra.VERB_CHECK}",
            cwd=str(root),
            process=m.Cli.ProcessOutcome.model_validate(
                output.outcome, from_attributes=True
            ),
            native_outcome=native,
            policy=policy,
            repository=u.Infra.canonical_origin_remote(identity.origin_remote),
            commit_sha=identity.head_oid,
            tree_sha=cls._rev_parse(root, "HEAD^{tree}"),
            context_digest=context_digest,
            policy_digest=policy_digest,
            reports=(
                m.Infra.GateReportEvidence(
                    path=sarif.relative_to(root),
                    digest=f"sha256:{cli_u.Cli.sha256_bytes(sarif.read_bytes())}",
                    kind=c.Infra.GateEvidenceReportKind.CHECK_SARIF,
                ),
            ),
            result_digest=f"sha256:{cli_u.Cli.sha256_content(output.stdout + output.stderr)}",
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
        )
        receipt = root / c.Infra.REPORTS_DIR_NAME / "original-check.json"
        tm.ok(
            cli_u.Cli.atomic_write_text_file(
                receipt, evidence.model_dump_json(round_trip=True)
            )
        )
        return m.Infra.GateAttestationCreateRequest(
            workspace=str(root),
            signer="attester@example.test",
            gates=(c.Infra.VERB_CHECK,),
            receipt=receipt,
            allowed_signers=str(root / "allowed_signers"),
            context_digest=context_digest,
            policy=policy,
            policy_digest=policy_digest,
        )

    @staticmethod
    def _verify(
        root: Path,
        allowed_signers: Path,
        commit_sha: str,
        *gates: str,
    ) -> p.Result[m.Infra.GateAttestationReport]:
        return u.Infra.git_verify_gate_attestation(
            m.Infra.GateAttestationVerifyRequest(
                workspace=str(root),
                allowed_signers=str(allowed_signers),
                expected_gates=gates,
                commit_sha=commit_sha,
                context_digest=f"sha256:{cli_u.Cli.sha256_content(sys.version + sys.platform)}",
                policy=c.Infra.GateAcceptancePolicy.COMPLETE_EXECUTION,
                policy_digest=(
                    "sha256:"
                    + cli_u.Cli.sha256_content(
                        c.Infra.GateAcceptancePolicy.COMPLETE_EXECUTION.value,
                    )
                ),
            ),
        )

    def test_signed_gate_attestation_round_trip_is_local(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test signed gate attestation round trip is local."""
        allowed_signers = signed_repository_factory(tmp_path)
        created = u.Infra.git_create_gate_attestation(self._request(tmp_path))

        tm.ok(created)
        head = self._head(tmp_path)
        tm.that(self._rev_parse(tmp_path, f"{created.unwrap().tag}^{{}}"), eq=head)
        verified = self._verify(tmp_path, allowed_signers, head, c.Infra.VERB_CHECK)
        tm.ok(verified)
        tm.that(verified.unwrap().signer, eq="attester@example.test")

    def test_publication_reuses_original_proof_without_running_make_again(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Repeated publication verifies the same object and leaves execution untouched."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        before = (tmp_path / "invocations.txt").read_bytes()
        created = tm.ok(u.Infra.git_create_gate_attestation(request))
        reused = tm.ok(u.Infra.git_create_gate_attestation(request))

        tm.that(created.reused, eq=False)
        tm.that(reused.reused, eq=True)
        tm.that(reused.tag, eq=created.tag)
        tm.that((tmp_path / "invocations.txt").read_bytes(), eq=before)

    def test_original_findings_keep_their_real_nonzero_exit_in_signed_evidence(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Completed Ruff findings prove execution without claiming quality passed."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        tm.that(source.process.raw_return_code != 0, eq=True)
        tm.that(source.native_outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.ok(u.Infra.git_create_gate_attestation(request))
        destination = tmp_path / c.Infra.REPORTS_DIR_NAME / "verified-proof.json"
        verified = u.Infra.git_verify_gate_attestation(
            m.Infra.GateAttestationVerifyRequest(
                workspace=str(tmp_path),
                allowed_signers=str(allowed),
                expected_gates=request.gates,
                commit_sha=self._head(tmp_path),
                context_digest=request.context_digest,
                policy=request.policy,
                policy_digest=request.policy_digest,
                output=str(destination),
            ),
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

    def test_modified_original_report_cannot_publish_a_proof(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """The signer refuses changed producer bytes instead of recomputing a gate."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        report = tmp_path / source.reports[0].path
        report.write_text("{}\n", encoding="utf-8")

        tm.fail(u.Infra.git_create_gate_attestation(request))
        tm.that(
            (tmp_path / "invocations.txt").read_text(encoding="utf-8").splitlines(),
            eq=["executed"],
        )

    def test_context_change_does_not_reuse_the_original_stage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """A proof for another exact context remains outside required coverage."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(request))

        tm.fail(
            u.Infra.git_verify_gate_attestation(
                m.Infra.GateAttestationVerifyRequest(
                    workspace=str(tmp_path),
                    allowed_signers=str(allowed),
                    expected_gates=request.gates,
                    commit_sha=self._head(tmp_path),
                    context_digest=f"sha256:{cli_u.Cli.sha256_content('different runtime context')}",
                    policy=request.policy,
                    policy_digest=request.policy_digest,
                ),
            ),
        )

    def test_missing_original_report_cannot_reuse_a_signed_stage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """A valid signature cannot replace the required original artifacts."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        tm.ok(u.Infra.git_create_gate_attestation(request))
        (tmp_path / source.reports[0].path).unlink()

        tm.fail(
            self._verify(tmp_path, allowed, self._head(tmp_path), c.Infra.VERB_CHECK)
        )

    def test_untrusted_signing_key_cannot_verify_an_existing_stage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Native SSH verification rejects an unrelated key under the same principal."""
        allowed = signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(request))
        foreign = tmp_path / "foreign-signing-key"
        tm.ok(
            cli_u.Cli.run_raw(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(foreign)],
                cwd=tmp_path,
            ),
        )
        allowed.write_text(
            "attester@example.test "
            + foreign.with_suffix(".pub").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        tm.fail(
            self._verify(tmp_path, allowed, self._head(tmp_path), c.Infra.VERB_CHECK)
        )

    def test_real_make_timeout_cannot_borrow_an_earlier_complete_report(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Original reaped timeout state remains operational failure under either policy."""
        signed_repository_factory(tmp_path)
        request = self._request(tmp_path)
        source = m.Infra.GateCommandEvidence.model_validate_json(
            request.receipt.read_bytes()
        )
        started = datetime.now(UTC)
        command = ["make", c.Infra.VERB_CHECK, "ATTEST_PROBE_DELAY=2"]
        interrupted = tm.ok(cli_u.Cli.run_raw(command, cwd=tmp_path, timeout=1))
        tm.that(interrupted.outcome.timed_out, eq=True)
        updated = source.model_copy(
            update={
                "command": " ".join(command),
                "process": m.Cli.ProcessOutcome.model_validate(
                    interrupted.outcome,
                    from_attributes=True,
                ),
                "started_at": started.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
        tm.ok(
            cli_u.Cli.atomic_write_text_file(
                request.receipt,
                updated.model_dump_json(round_trip=True),
            ),
        )

        tm.fail(u.Infra.git_create_gate_attestation(request))
        tm.that(
            (tmp_path / "invocations.txt").read_text(encoding="utf-8").splitlines(),
            eq=["executed", "executed"],
        )

    def test_gate_attestation_normalizes_network_remote_git_suffix(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test gate attestation normalizes network remote git suffix."""
        allowed_signers = signed_repository_factory(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(self._request(tmp_path)))
        remote = tm.ok(
            u.Infra.git_remote_url(m.Infra.GitRemoteUrlRequest(repo_root=tmp_path)),
        ).text
        u.Tests.git_bootstrap(
            tmp_path,
            ("remote", "set-url", c.Infra.GIT_ORIGIN, remote.removesuffix(".git")),
        )

        tm.ok(
            self._verify(
                tmp_path,
                allowed_signers,
                self._head(tmp_path),
                c.Infra.VERB_CHECK,
            ),
        )

    def test_gate_attestation_verifies_selected_commit_with_equal_tree(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test gate attestation verifies selected commit with equal tree."""
        allowed_signers = signed_repository_factory(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(self._request(tmp_path)))
        selected_sha = self._head(tmp_path)
        selected_tree = self._rev_parse(tmp_path, "HEAD^{tree}")
        tm.ok(
            u.Infra.git_commit(
                m.Infra.GitCommitRequest(
                    repo_root=tmp_path,
                    message="test: later equal-tree commit",
                ),
            ),
        )
        tm.that(self._rev_parse(tmp_path, "HEAD^{tree}"), eq=selected_tree)

        verified = self._verify(
            tmp_path,
            allowed_signers,
            selected_sha,
            c.Infra.VERB_CHECK,
        )
        tm.ok(verified)
        tm.that(verified.unwrap().commit_sha, eq=selected_sha)

    def test_gate_attestation_keeps_an_unpublished_stage_out_of_coverage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test gate attestation rejects incomplete coverage."""
        allowed_signers = signed_repository_factory(tmp_path)
        tm.ok(u.Infra.git_create_gate_attestation(self._request(tmp_path)))

        verified = self._verify(
            tmp_path,
            allowed_signers,
            self._head(tmp_path),
            c.Infra.VERB_TEST,
        )

        tm.fail(verified)

    def test_gate_attestation_rejects_duplicate_gate_coverage(
        self,
        tmp_path: Path,
        signed_repository_factory: Callable[[Path], Path],
    ) -> None:
        """Test gate attestation rejects duplicate gate coverage."""
        _allowed_signers = signed_repository_factory(tmp_path)
        values = self._request(tmp_path).model_dump()
        values["gates"] = (c.Infra.VERB_CHECK, c.Infra.VERB_CHECK)

        with pytest.raises(ValueError):
            m.Infra.GateAttestationCreateRequest.model_validate(values)
