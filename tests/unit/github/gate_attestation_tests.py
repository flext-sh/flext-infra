"""Behavior tests for SSH-signed gate attestations."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path

from git import Repo
import pytest

from flext_cli import u as cli_u
from flext_infra import m, u
from flext_tests import tm

_OPEN_REPOSITORIES: list[Repo] = []


@pytest.fixture(autouse=True)
def _close_git_repositories() -> Iterator[None]:
    yield
    while _OPEN_REPOSITORIES:
        _OPEN_REPOSITORIES.pop().close()


def _signed_repository(root: Path) -> tuple[Repo, Repo, Path]:
    repo = Repo.init(root)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Attestation Test")
        config.set_value("user", "email", "attestation@example.test")
        config.set_value("gpg", "format", "ssh")
        config.set_value("commit", "gpgsign", "false")
    remote = Repo.init(root.parent / f"{root.name}-remote.git", bare=True)
    _OPEN_REPOSITORIES.extend((repo, remote))
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
    repo.index.add([
        "Makefile",
        "pyproject.toml",
        "tracked.txt",
    ])
    repo.index.commit("test: create base revision")
    base_branch = repo.active_branch.name
    repo.create_head("source-518").checkout()
    (root / "source.txt").write_text("source 518\n", encoding="utf-8")
    repo.index.add(["source.txt"])
    source_sha = repo.index.commit("test: source PR 518 head").hexsha
    repo.heads[base_branch].checkout()
    repo.git.merge("--no-ff", "--no-edit", "source-518")
    manifest = root / ".github" / "attestations" / "promotion-sources.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps([{"pr": 518, "head_sha": source_sha, "bead": "flext-13z9y"}]),
        encoding="utf-8",
    )
    repo.index.add([".github/attestations/promotion-sources.json"])
    repo.index.commit("test: record promotion source")
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
    tm.that(verified.unwrap().sources[0].pr, eq=518)


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


def test_gate_attestation_rejects_duplicate_gate_coverage(tmp_path: Path) -> None:
    _repo, _remote, _allowed_signers = _signed_repository(tmp_path)
    values = _request(tmp_path).model_dump()
    values["gates"] = ("gen", "check", "test", "test")

    with pytest.raises(ValueError, match="gates must be unique"):
        m.Infra.GateAttestationCreateRequest.model_validate(values)


def test_gate_attestation_removes_local_tag_when_atomic_push_fails(
    tmp_path: Path,
) -> None:
    repo, _remote, _allowed_signers = _signed_repository(tmp_path)
    repo.remote("origin").set_url(str(tmp_path / "missing-remote.git"))

    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.fail(created)
    tm.that(tuple(tag.name for tag in repo.tags), eq=())


def test_gate_attestation_requires_committed_promotion_manifest(tmp_path: Path) -> None:
    repo, _remote, _allowed_signers = _signed_repository(tmp_path)
    repo.index.remove([".github/attestations/promotion-sources.json"], working_tree=True)
    repo.index.commit("test: remove source manifest")

    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.fail(created)


def test_gate_attestation_rejects_source_without_no_ff_merge(tmp_path: Path) -> None:
    repo, _remote, _allowed_signers = _signed_repository(tmp_path)
    manifest = tmp_path / ".github" / "attestations" / "promotion-sources.json"
    base_sha = repo.git.rev_parse("HEAD~2")
    manifest.write_text(
        json.dumps([{"pr": 518, "head_sha": base_sha, "bead": "flext-13z9y"}]),
        encoding="utf-8",
    )
    repo.index.add([".github/attestations/promotion-sources.json"])
    repo.index.commit("test: forge source topology")

    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.fail(created)
    tm.that(created.error or "", has="no-ff merge parent")
