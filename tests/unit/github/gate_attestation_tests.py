"""Behavior tests for local SSH-signed gate attestations."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

from git import Repo
import pytest

from flext_cli import u as cli_u
from flext_infra import m, p, u
from flext_tests import tm


def _signed_repository(root: Path, repositories: list[Repo]) -> tuple[Repo, Path]:
    repo = Repo.init(root)
    repositories.append(repo)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Attestation Test")
        config.set_value("user", "email", "attestation@example.test")
        config.set_value("gpg", "format", "ssh")
        config.set_value("commit", "gpgsign", "false")
    repo.create_remote("origin", "https://github.example/flext/fixture.git")
    key_path = root / "signing_key"
    tm.ok(
        cli_u.Cli.run_raw(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
            cwd=root,
        )
    )
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
    (root / "pyproject.toml").write_text(
        "[project]\nname='fixture'\n", encoding="utf-8"
    )
    repo.index.add(["Makefile", "pyproject.toml", "tracked.txt"])
    repo.index.commit("test: create base revision")
    allowed_signers = root / "allowed_signers"
    public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
    allowed_signers.write_text(
        f"attester@example.test {public_key}\n", encoding="utf-8"
    )
    return repo, allowed_signers


@pytest.fixture
def signed_repository_factory() -> Iterator[Callable[[Path], tuple[Repo, Path]]]:
    """Create and close only repositories explicitly owned by one test."""
    repositories: list[Repo] = []

    def create(root: Path) -> tuple[Repo, Path]:
        return _signed_repository(root, repositories)

    yield create
    while repositories:
        repositories.pop().close()


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


def test_signed_gate_attestation_round_trip_is_local(
    tmp_path: Path, signed_repository_factory: Callable[[Path], tuple[Repo, Path]]
) -> None:
    repo, allowed_signers = signed_repository_factory(tmp_path)
    created = u.Infra.git_create_gate_attestation(_request(tmp_path))

    tm.ok(created)
    tm.that(created.unwrap().tag, eq=f"attest/gates/v1/{repo.head.commit.hexsha}")
    tm.that(repo.tags[created.unwrap().tag].commit.hexsha, eq=repo.head.commit.hexsha)
    verified = _verify(
        tmp_path, allowed_signers, repo.head.commit.hexsha, "gen", "check", "test"
    )
    tm.ok(verified)
    tm.that(verified.unwrap().signer, eq="attester@example.test")


def test_gate_attestation_normalizes_network_remote_git_suffix(
    tmp_path: Path, signed_repository_factory: Callable[[Path], tuple[Repo, Path]]
) -> None:
    repo, allowed_signers = signed_repository_factory(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))
    repo.remote("origin").set_url("https://github.example/flext/fixture")

    tm.ok(
        _verify(
            tmp_path, allowed_signers, repo.head.commit.hexsha, "gen", "check", "test"
        )
    )


def test_gate_attestation_verifies_selected_commit_with_equal_tree(
    tmp_path: Path, signed_repository_factory: Callable[[Path], tuple[Repo, Path]]
) -> None:
    repo, allowed_signers = signed_repository_factory(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))
    selected_sha = repo.head.commit.hexsha
    selected_tree = repo.head.commit.tree.hexsha
    repo.index.commit("test: later equal-tree commit")
    tm.that(repo.head.commit.tree.hexsha, eq=selected_tree)

    verified = _verify(tmp_path, allowed_signers, selected_sha, "gen", "check", "test")
    tm.ok(verified)
    tm.that(verified.unwrap().commit_sha, eq=selected_sha)


def test_gate_attestation_rejects_incomplete_coverage(
    tmp_path: Path, signed_repository_factory: Callable[[Path], tuple[Repo, Path]]
) -> None:
    repo, allowed_signers = signed_repository_factory(tmp_path)
    tm.ok(u.Infra.git_create_gate_attestation(_request(tmp_path)))

    verified = _verify(tmp_path, allowed_signers, repo.head.commit.hexsha, "check")

    tm.fail(verified)
    tm.that(verified.error or "", has="exactly match")


def test_gate_attestation_rejects_duplicate_gate_coverage(
    tmp_path: Path, signed_repository_factory: Callable[[Path], tuple[Repo, Path]]
) -> None:
    _repo, _allowed_signers = signed_repository_factory(tmp_path)
    values = _request(tmp_path).model_dump()
    values["gates"] = ("gen", "check", "test", "test")

    with pytest.raises(ValueError, match="gates must be unique"):
        m.Infra.GateAttestationCreateRequest.model_validate(values)
