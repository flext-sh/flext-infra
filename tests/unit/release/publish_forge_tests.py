"""Atomic draft-then-publish behavior through the injected release forge port.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.release import FlextInfraReleaseOrchestrator
from tests import TestsFlextInfraReleaseForgeMemory, c, m, p, tm, u


class TestsFlextInfraReleasePublishForge:
    """Publication is one commit point taken only after every asset verifies."""

    @staticmethod
    def _tag(report: m.Infra.BuildReport) -> str:
        """Return the release tag the receipt's version declares.

        Returns:
            The declared release tag.

        """
        return c.Infra.TAG_FORMAT.format(version=report.version)

    @staticmethod
    def _forge(
        workspace: Path,
        report: m.Infra.BuildReport,
        *,
        native_digest: bool = True,
        upload_state: str = "uploaded",
    ) -> TestsFlextInfraReleaseForgeMemory:
        """Bind an in-memory forge whose remote tag equals the local candidate.

        Returns:
            The in-memory forge for this candidate.

        """
        tag = TestsFlextInfraReleasePublishForge._tag(report)
        commit = u.Tests.git_capture(
            workspace,
            "rev-parse",
            f"refs/tags/{tag}^{{commit}}",
        )
        return TestsFlextInfraReleaseForgeMemory(
            commit.strip(),
            native_digest=native_digest,
            upload_state=upload_state,
        )

    @staticmethod
    def _publish(
        workspace: Path,
        forge: TestsFlextInfraReleaseForgeMemory,
    ) -> p.Result[bool]:
        """Run the public publish phase with the forge bound by injection.

        Returns:
            The publish phase result.

        """
        return FlextInfraReleaseOrchestrator(
            repository_root=workspace,
            apply_changes=True,
            phase=c.Infra.ReleasePhase.PUBLISH,
            release_forge=forge,
        ).execute()

    @staticmethod
    def _artifacts(report: m.Infra.BuildReport) -> tuple[Path, ...]:
        """Return every attested artifact path of the receipt.

        Returns:
            The attested artifact paths.

        """
        return tuple(
            Path(artifact.path)
            for record in report.records
            for artifact in record.artifacts
        )

    def test_new_release_is_drafted_uploaded_verified_then_published(
        self,
        tmp_path: Path,
    ) -> None:
        """A missing release becomes public only after its draft verifies."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)

        tm.ok(self._publish(workspace, forge))

        names = [f"upload:{path.name}" for path in self._artifacts(report)]
        tm.that(list(forge.effects), eq=["create-draft", *names, "publish"])
        tm.that(forge.releases[0].draft, eq=False)

    def test_identical_published_release_is_a_no_op(self, tmp_path: Path) -> None:
        """A published release holding exactly the attested assets is untouched."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        release = forge.seed_release(self._tag(report), draft=False)
        for path in self._artifacts(report):
            forge.seed_asset(
                release,
                path.name,
                path.read_bytes(),
                digest=f"sha256:{u.Cli.sha256_file(path)}",
            )

        tm.ok(self._publish(workspace, forge))
        tm.that(list(forge.effects), eq=[])

    def test_digest_mismatch_fails_before_publication(self, tmp_path: Path) -> None:
        """A differing remote asset refuses the run and nothing is published."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        release = forge.seed_release(self._tag(report), draft=True)
        first = self._artifacts(report)[0]
        forge.seed_asset(release, first.name, b"other", digest="sha256:" + "0" * 64)

        tm.fail(self._publish(workspace, forge), has="digest differs from receipt")
        tm.that(list(forge.effects), eq=[])
        tm.that(forge.releases[0].draft, eq=True)

    def test_asset_not_uploaded_fails_before_publication(
        self,
        tmp_path: Path,
    ) -> None:
        """An incomplete remote upload is never accepted as verified."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        release = forge.seed_release(self._tag(report), draft=True)
        first = self._artifacts(report)[0]
        forge.seed_asset(
            release,
            first.name,
            first.read_bytes(),
            digest=f"sha256:{u.Cli.sha256_file(first)}",
            state="starter",
        )

        tm.fail(self._publish(workspace, forge), has="is not uploaded")
        tm.that(list(forge.effects), eq=[])

    def test_draft_uploads_only_missing_assets(self, tmp_path: Path) -> None:
        """Verified draft assets are kept; only absent artifacts are uploaded."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        release = forge.seed_release(self._tag(report), draft=True)
        first, *rest = self._artifacts(report)
        forge.seed_asset(
            release,
            first.name,
            first.read_bytes(),
            digest=f"sha256:{u.Cli.sha256_file(first)}",
        )

        tm.ok(self._publish(workspace, forge))
        tm.that(
            list(forge.effects),
            eq=[*(f"upload:{path.name}" for path in rest), "publish"],
        )

    def test_published_release_missing_assets_fails(self, tmp_path: Path) -> None:
        """An immutable published release with absent assets is never mutated."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        forge.seed_release(self._tag(report), draft=False)

        tm.fail(self._publish(workspace, forge), has="lacks attested assets")
        tm.that(list(forge.effects), eq=[])

    @c.Tests.MARK.parametrize(("tampered", "succeeds"), [(False, True), (True, False)])
    def test_download_hash_fallback_verifies_bytes(
        self,
        tmp_path: Path,
        *,
        tampered: bool,
        succeeds: bool,
    ) -> None:
        """Without a native digest the downloaded bytes decide the verdict."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report)
        release = forge.seed_release(self._tag(report), draft=False)
        for path in self._artifacts(report):
            content = path.read_bytes() + (b"\n" if tampered else b"")
            forge.seed_asset(release, path.name, content, digest=None)

        published = self._publish(workspace, forge)

        tm.that(published.success, eq=succeeds)
        tm.that(list(forge.effects), eq=[])

    def test_unverified_upload_is_never_published(self, tmp_path: Path) -> None:
        """Publication waits for verification of the uploads themselves."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        forge = self._forge(workspace, report, upload_state="starter")

        tm.fail(self._publish(workspace, forge), has="is not uploaded")
        tm.that("publish" in forge.effects, eq=False)
        tm.that(forge.releases[0].draft, eq=True)
