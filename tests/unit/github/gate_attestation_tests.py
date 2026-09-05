"""Behavior tests for local SSH-signed gate attestations."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_cli import u as cli_u
from flext_infra import m, p, u
from flext_tests import tm
from tests import u as test_u


def _signed_repository(
    root: Path, *, remote_suffix: str = ".git"
) -> tuple[Path, Path, str]:
    root.mkdir(parents=True, exist_ok=True)
    key_path = root / "signing_key"
    tm.ok(
        cli_u.Cli.run_raw(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
            cwd=root,
        )
    )
    (root / "tracked.txt").write_text("attested\n", encoding="utf-8")
    (root / "Makefile").write_text(
        ".PHONY: gen check test\n"
        "gen:\n\t@printf 'gen ok\\n'\n"
        "check:\n\t@printf 'check ok\\n'\n"
        "test:\n\t@printf 'test ok\\n'\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        "[project]\nname='fixture'\n", encoding="utf-8"
    )
    provider = test_u.Tests.provider()
    test_u.Tests.initialize_git_repo(
        root,
        origin_url=(f"{provider.base_url.rstrip('/')}/gate-attestation{remote_suffix}"),
        config_values={
            "user.name": "Attestation Test",
            "user.email": "attestation@example.test",
            "gpg.format": "ssh",
            "commit.gpgsign": "false",
            "user.signingkey": str(key_path),
        },
    )
    allowed_signers = root / "allowed_signers"
    public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
    allowed_signers.write_text(
        f"attester@example.test {public_key}\n", encoding="utf-8"
    )
    head = tm.ok(
        u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=root))
    ).oid
    return root, allowed_signers, head


def _request(root: Path) -> m.Infra.GateAttestationCreateRequest:
    return m.Infra.GateAttestationCreateRequest(
        workspace=str(root),
        signer="attester@example.test",
        gates=("gen", "check", "test"),
    )


def _verify(
    root: Path, allowed_signers: Path, commit_sha: str, *gates: str
) -> p.Result[m.Infra.GateAttestationReport]:
    return u.Infra.git_verify_gate_attestation(
        m.Infra.GateAttestationVerifyRequest(
            workspace=str(root),
            allowed_signers=str(allowed_signers),
            expected_gates=gates,
            commit_sha=commit_sha,
        )
    )


def test_signed_gate_attestation_round_trip_is_local(tmp_path: Path) -> None:
    repository, allowed_signers, head = _signed_repository(tmp_path)
    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.ok(created)
    tm.that(created.unwrap().tag, eq=f"attest/gates/v1/{head}")
    tagged = tm.ok(
        u.Infra.git_resolve_commit(
            m.Infra.GitCommitishRequest(
                repo_root=repository, commitish=created.unwrap().tag
            )
        )
    )
    tm.that(tagged.oid, eq=head)
    verified = _verify(tmp_path, allowed_signers, head, "gen", "check", "test")
    tm.ok(verified)
    tm.that(verified.unwrap().signer, eq="attester@example.test")


def test_gate_attestation_normalizes_network_remote_git_suffix(tmp_path: Path) -> None:
    _repository, allowed_signers, head = _signed_repository(tmp_path, remote_suffix="")
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))

    tm.ok(_verify(tmp_path, allowed_signers, head, "gen", "check", "test"))


def test_gate_attestation_verifies_selected_commit_with_equal_tree(
    tmp_path: Path,
) -> None:
    repository, allowed_signers, selected_sha = _signed_repository(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))
    later = tm.ok(
        u.Infra.git_commit(
            m.Infra.GitCommitRequest(
                repo_root=repository, message="test: later equal-tree commit"
            )
        )
    )
    tm.that(later.oid, ne=selected_sha)

    verified = _verify(tmp_path, allowed_signers, selected_sha, "gen", "check", "test")
    tm.ok(verified)
    tm.that(verified.unwrap().commit_sha, eq=selected_sha)


def test_gate_attestation_rejects_incomplete_coverage(tmp_path: Path) -> None:
    _repository, allowed_signers, head = _signed_repository(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))

    verified = _verify(tmp_path, allowed_signers, head, "check")

    tm.fail(verified)
    tm.that(verified.error or "", has="exactly match")


def test_gate_attestation_rejects_duplicate_gate_coverage(tmp_path: Path) -> None:
    _repository, _allowed_signers, _head = _signed_repository(tmp_path)
    values = _request(tmp_path).model_dump()
    values["gates"] = ("gen", "check", "test", "test")

    with pytest.raises(ValueError, match="gates must be unique"):
        m.Infra.GateAttestationCreateRequest.model_validate(values)
