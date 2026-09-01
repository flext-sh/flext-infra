"""Behavior tests for SSH-signed gate attestations."""

from __future__ import annotations

from pathlib import Path

from git import Repo

from flext_cli import u as cli_u
from flext_infra import m, u
from flext_tests import tm


def _signed_repository(root: Path) -> tuple[Repo, Repo, Path]:
    repo = Repo.init(root)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Attestation Test")
        config.set_value("user", "email", "attestation@example.test")
        config.set_value("gpg", "format", "ssh")
        config.set_value("commit", "gpgsign", "false")
    remote = Repo.init(root.parent / f"{root.name}-remote.git", bare=True)
    repo.create_remote("origin", str(remote.working_dir))
    key_path = root / "signing_key"
    generated = cli_u.Cli.run_raw([
        "ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)
    ], cwd=root)
    tm.ok(generated)
    with repo.config_writer() as config:
        config.set_value("user", "signingkey", str(key_path))
    (root / "tracked.txt").write_text("attested\n", encoding="utf-8")
    (root / "Makefile").write_text(
        ".PHONY: gen check test\n"
        "gen:\n\t@printf 'gen ok\\n'\n"
        "check:\n\t@printf 'check ok\\n'\n"
        "test:\n\t@printf 'test ok\\n'\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    repo.index.add(["Makefile", "pyproject.toml", "tracked.txt"])
    repo.index.commit("test: create attested revision")
    allowed_signers = root / "allowed_signers"
    public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
    allowed_signers.write_text(f"attester@example.test {public_key}\n", encoding="utf-8")
    return repo, remote, allowed_signers


def _request(root: Path) -> m.Infra.GateAttestationCreateRequest:
    return m.Infra.GateAttestationCreateRequest(
        workspace=str(root),
        bead="flext-13z9y",
        pull_request=517,
        integration_branch="0.12.0-dev",
        signer="attester@example.test",
        gates=("gen", "check", "test"),
    )


def test_signed_gate_attestation_round_trip(tmp_path: Path) -> None:
    repo, remote, allowed_signers = _signed_repository(tmp_path)
    created = u.Infra.git_create_gate_attestation(_request(tmp_path))
    tm.ok(created)
    tm.that(created.unwrap().tag, eq=f"attest/gates/v1/{repo.head.commit.hexsha}")
    tm.that(
        next(remote.iter_commits(created.unwrap().tag)).hexsha,
        eq=repo.head.commit.hexsha,
    )

    verified = u.Infra.git_verify_gate_attestation(
        m.Infra.GateAttestationVerifyRequest(
            workspace=str(tmp_path),
            allowed_signers=str(allowed_signers),
            expected_gates=("gen", "check", "test"),
        )
    )
    tm.ok(verified)
    tm.that(verified.unwrap().signer, eq="attester@example.test")


def test_gate_attestation_rejects_incomplete_coverage(tmp_path: Path) -> None:
    _repo, _remote, allowed_signers = _signed_repository(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))
    verified = u.Infra.git_verify_gate_attestation(
        m.Infra.GateAttestationVerifyRequest(
            workspace=str(tmp_path),
            allowed_signers=str(allowed_signers),
            expected_gates=("check",),
        )
    )
    tm.fail(verified)
    tm.that(verified.error or "", has="exactly match")


def test_gate_attestation_removes_local_tag_when_atomic_push_fails(
    tmp_path: Path,
) -> None:
    repo, _remote, _allowed_signers = _signed_repository(tmp_path)
    repo.remote("origin").set_url(str(tmp_path / "missing-remote.git"))

    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.fail(created)
    tm.that(tuple(tag.name for tag in repo.tags), eq=())
