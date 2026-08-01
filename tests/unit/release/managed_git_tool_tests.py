"""Generic exact-Git executable release behavior tests."""

from __future__ import annotations

import tarfile
from pathlib import Path

from flext_infra import m, main, p, u
from flext_infra.release.managed_git_tool import FlextInfraManagedGitToolRelease
from flext_tests import tm


class _ManagedGitToolHarness(FlextInfraManagedGitToolRelease):
    """Expose inherited release stages as a typed test-only integration harness."""

    @classmethod
    def build(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
    ) -> p.Result[bool]:
        """Execute the real deterministic build stage."""
        return cls._build_managed_git_tool(spec, stage)

    @classmethod
    def probe(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
    ) -> p.Result[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]]:
        """Execute every real staged-runtime probe."""
        return cls._probe_managed_git_tool(spec, stage)

    @classmethod
    def finish(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
        probes: tuple[m.Infra.ManagedGitToolProbeReceipt, ...],
        temporary_root: Path,
        *,
        apply: bool,
    ) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        """Persist and activate, or return the non-mutating dry-run receipt."""
        return cls._finish_managed_git_tool_release(
            spec, stage, probes, temporary_root, apply=apply
        )

    @classmethod
    def persist(
        cls,
        receipt: m.Infra.ManagedGitToolReleaseReceipt,
        stage: m.Infra.ManagedGitToolSourceStage,
        temporary_root: Path,
    ) -> p.Result[bool]:
        """Persist one already-probed immutable release set."""
        return cls._persist_managed_git_tool(receipt, stage, temporary_root)

    @classmethod
    def validate_spec(cls, spec: m.Infra.ManagedGitToolRelease) -> p.Result[bool]:
        """Validate one exact release manifest."""
        return cls._validate_managed_git_tool_spec(spec)

    @classmethod
    def validate_source_archive(cls, path: Path) -> p.Result[bool]:
        """Validate one Git source archive boundary."""
        return cls._validate_git_source_archive(path)


class TestsManagedGitToolRelease:
    """Prove fail-closed build, probe, persistence, and activation behavior."""

    _COMMIT_OID = "a" * 40
    _SOURCE_ARCHIVE_SHA256 = "b" * 64

    @classmethod
    def _spec(
        cls, temporary_root: Path, *, artifact_sha256: str
    ) -> m.Infra.ManagedGitToolRelease:
        """Build one generic manifest from fixture-owned absolute paths."""
        return m.Infra.ManagedGitToolRelease(
            release_name="fixture-tool",
            source_url="https://example.test/fixture/tool.git",
            commit_oid=cls._COMMIT_OID,
            source_subdirectory=Path(),
            build_command=(
                "/usr/bin/install",
                "-m",
                "755",
                "{source}/fixture-tool",
                "{artifact}",
            ),
            artifact=m.Infra.ManagedGitToolArtifact(
                build_path=Path("fixture-tool"),
                install_path=temporary_root / "venv" / "bin" / "fixture-tool",
                sha256=artifact_sha256,
            ),
            probes=(
                m.Infra.ManagedGitToolProbe(
                    name="public-version",
                    command=("{artifact}", "--version"),
                    expected_output_contains=("fixture-tool 1.0",),
                ),
            ),
            artifact_store=temporary_root / "immutable-store",
        )

    @classmethod
    def _stage(
        cls, temporary_root: Path
    ) -> tuple[m.Infra.ManagedGitToolSourceStage, str]:
        """Create one real source executable and isolated output stage."""
        checkout = temporary_root / "checkout"
        output = temporary_root / "output"
        checkout.mkdir()
        output.mkdir()
        source = checkout / "fixture-tool"
        source.write_text("#!/bin/sh\nprintf 'fixture-tool 1.0\\n'\n", encoding="utf-8")
        source.chmod(0o755)
        digest = u.Cli.sha256_file(source)
        return (
            m.Infra.ManagedGitToolSourceStage(
                checkout_root=checkout,
                source_root=checkout,
                output_root=output,
                artifact_path=output / "fixture-tool",
                snapshot=m.Infra.SourceSnapshot(
                    commit_oid=cls._COMMIT_OID, source_date_epoch=1_700_000_000
                ),
                source_archive_sha256=cls._SOURCE_ARCHIVE_SHA256,
            ),
            digest,
        )

    @staticmethod
    def test_public_cli_exposes_managed_git_tool_help() -> None:
        """Expose the generic release route without a consumer identity."""
        tm.that(main(["release", "managed-git-tool", "--help"]), eq=0)

    @classmethod
    def test_real_build_probe_persist_activate_and_idempotence(
        cls, tmp_path: Path
    ) -> None:
        """Build and probe a real executable, then activate one immutable set."""
        stage, digest = cls._stage(tmp_path)
        spec = cls._spec(tmp_path, artifact_sha256=digest)

        built = _ManagedGitToolHarness.build(spec, stage)
        tm.ok(built)
        probes = _ManagedGitToolHarness.probe(spec, stage)
        tm.ok(probes)

        first = _ManagedGitToolHarness.finish(
            spec, stage, probes.value, tmp_path, apply=True
        )
        tm.ok(first)
        tm.that(first.value.persisted, eq=True)
        tm.that(first.value.activated, eq=True)
        tm.that(first.value.receipt.commit_oid, eq=cls._COMMIT_OID)
        tm.that(first.value.receipt.artifact.sha256, eq=digest)
        tm.that(spec.artifact.install_path.is_file(), eq=True)
        tm.that(u.Cli.sha256_file(spec.artifact.install_path), eq=digest)

        second = _ManagedGitToolHarness.finish(
            spec, stage, probes.value, tmp_path, apply=True
        )
        tm.ok(second)
        tm.that(second.value.receipt, eq=first.value.receipt)

    @classmethod
    def test_dry_run_never_persists_or_activates(cls, tmp_path: Path) -> None:
        """Run the real build and probes while leaving consumer paths untouched."""
        stage, digest = cls._stage(tmp_path)
        spec = cls._spec(tmp_path, artifact_sha256=digest)
        tm.ok(_ManagedGitToolHarness.build(spec, stage))
        probes = _ManagedGitToolHarness.probe(spec, stage)
        tm.ok(probes)

        result = _ManagedGitToolHarness.finish(
            spec, stage, probes.value, tmp_path, apply=False
        )

        tm.ok(result)
        tm.that(result.value.persisted, eq=False)
        tm.that(result.value.activated, eq=False)
        tm.that(spec.artifact_store.exists(), eq=False)
        tm.that(spec.artifact.install_path.exists(), eq=False)

    @classmethod
    def test_digest_mismatch_reports_observed_digest(cls, tmp_path: Path) -> None:
        """Fail before probes and report the deterministic observed build digest."""
        stage, observed_digest = cls._stage(tmp_path)
        spec = cls._spec(tmp_path, artifact_sha256="0" * 64)

        result = _ManagedGitToolHarness.build(spec, stage)

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has=observed_digest)

    @classmethod
    def test_immutable_store_rejects_tampering(cls, tmp_path: Path) -> None:
        """Reject an existing exact-commit set whose executable was modified."""
        stage, digest = cls._stage(tmp_path)
        spec = cls._spec(tmp_path, artifact_sha256=digest)
        tm.ok(_ManagedGitToolHarness.build(spec, stage))
        probes = _ManagedGitToolHarness.probe(spec, stage)
        tm.ok(probes)
        first = _ManagedGitToolHarness.finish(
            spec, stage, probes.value, tmp_path, apply=True
        )
        tm.ok(first)
        first.value.receipt.artifact.store_path.write_text(
            "tampered\n", encoding="utf-8"
        )

        collision = _ManagedGitToolHarness.persist(first.value.receipt, stage, tmp_path)

        tm.that(collision.failure, eq=True)
        tm.that(collision.error or "", has="immutable artifact collision")

    @classmethod
    def test_manifest_rejects_non_https_and_duplicate_environment(
        cls, tmp_path: Path
    ) -> None:
        """Reject decorated sources and ambiguous build environment ownership."""
        _, digest = cls._stage(tmp_path)
        spec = cls._spec(tmp_path, artifact_sha256=digest)
        invalid_source = spec.model_copy(
            update={"source_url": "http://user@example.test/tool.git?ref=main"}
        )
        invalid_environment = spec.model_copy(
            update={
                "build_environment": (
                    m.Infra.ManagedGitToolEnvironmentVariable(
                        name="PATH", value="/bin"
                    ),
                    m.Infra.ManagedGitToolEnvironmentVariable(
                        name="PATH", value="/usr/bin"
                    ),
                )
            }
        )

        source_result = _ManagedGitToolHarness.validate_spec(invalid_source)
        environment_result = _ManagedGitToolHarness.validate_spec(invalid_environment)

        tm.that(source_result.failure, eq=True)
        tm.that(source_result.error or "", has="credential-free HTTPS")
        tm.that(environment_result.failure, eq=True)
        tm.that(environment_result.error or "", has="duplicate names")

    @staticmethod
    def test_git_source_archive_rejects_links(tmp_path: Path) -> None:
        """Reject source archives that could escape through a symbolic link."""
        archive_path = tmp_path / "source.tar"
        with tarfile.open(archive_path, "w") as archive:
            member = tarfile.TarInfo("linked-tool")
            member.type = tarfile.SYMTYPE
            member.linkname = "outside"
            archive.addfile(member)

        result = _ManagedGitToolHarness.validate_source_archive(archive_path)

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="contains a link")
