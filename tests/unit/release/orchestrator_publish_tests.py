"""Public release receipt validation using real builds and artifact bytes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from json import dumps
from pathlib import Path

from flext_infra import config
from tests import c, m, t, tm, u


class TestsFlextInfraReleasePublish:
    """Behavior contract for the public release publish phase."""

    @staticmethod
    def test_dry_run_verifies_the_receipt_without_effects(tmp_path: Path) -> None:
        """Receipt validation preserves the artifacts produced by a real build."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        artifacts = {
            Path(artifact.path): Path(artifact.path).read_bytes()
            for record in report.records
            for artifact in record.artifacts
        }

        tm.that(u.Tests.run_release_main(workspace, "--phase", "publish"), eq=0)
        for path, content in artifacts.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    def test_tampered_artifact_is_refused(tmp_path: Path) -> None:
        """An artifact whose bytes no longer match the receipt never leaves."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        artifact = Path(report.records[0].artifacts[0].path)
        artifact.write_bytes(artifact.read_bytes() + b"\n")

        tm.that(
            u.Tests.run_release_main(workspace, "--phase", "publish", "--apply"),
            ne=0,
        )

    @staticmethod
    def test_member_sources_remain_bound_after_head_and_wip_advance(
        tmp_path: Path,
    ) -> None:
        """A workspace tag attests multiple independently versioned gitlinks."""
        workspace, report = u.Tests.create_tagged_release_build(
            tmp_path,
            projects=("flext-a", "flext-b"),
        )
        for record in report.records:
            project = Path(record.path)
            changed = project / "release-wip.txt"
            changed.write_text("committed after candidate\n", encoding="utf-8")
            u.Tests.commit_git_changes(project, "advance member after candidate")
            changed.write_text("uncommitted member WIP\n", encoding="utf-8")
        root_wip = workspace / "root-wip.txt"
        root_wip.write_text("committed after candidate\n", encoding="utf-8")
        u.Tests.commit_git_changes(workspace, "advance workspace after candidate")
        root_wip.write_text("uncommitted workspace WIP\n", encoding="utf-8")

        tm.that(u.Tests.run_release_main(workspace, "--phase", "publish"), eq=0)
        tm.that(root_wip.read_text(encoding="utf-8"), eq="uncommitted workspace WIP\n")
        for record in report.records:
            tm.that(
                (Path(record.path) / "release-wip.txt").read_text(encoding="utf-8"),
                eq="uncommitted member WIP\n",
            )

    @staticmethod
    def test_retargeted_tag_refuses_receipt_before_remote_effects(
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """Changing a candidate gitlink cannot publish an older member receipt."""
        workspace, report = u.Tests.create_tagged_release_build(tmp_path)
        record = report.records[0]
        project = Path(record.path)
        (project / "next.txt").write_text("next candidate\n", encoding="utf-8")
        u.Tests.commit_git_changes(project, "advance member")
        oid = u.Tests.git_capture(project, "rev-parse", "HEAD^{commit}").strip()
        u.Tests.git_bootstrap(
            workspace,
            ("update-index", "--cacheinfo", f"160000,{oid},{record.project}"),
        )
        u.Tests.git_bootstrap(workspace, ("commit", "-m", "advance candidate gitlink"))
        u.Tests.git_bootstrap(
            workspace,
            ("tag", "-f", c.Infra.TAG_FORMAT.format(version=report.version)),
        )

        tm.that(
            u.Tests.run_release_main(workspace, "--phase", "publish", "--apply"),
            ne=0,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="release source commit differs from tag")

    @staticmethod
    @c.Tests.MARK.parametrize("digest", [None, "sha256:" + "a" * 64])
    def test_native_asset_inventory_accepts_nullable_digest(digest: str | None) -> None:
        """GitHub's absent native digest remains explicit, not a verified hash."""
        inventory = m.Infra.GithubReleaseAssets.model_validate_json(
            dumps({
                "assets": [
                    {"name": "package.whl", "state": "uploaded", "digest": digest}
                ],
            })
        )
        tm.that(inventory.assets[0].digest, eq=digest)

    @staticmethod
    def test_missing_receipt_is_refused(tmp_path: Path) -> None:
        """Publishing without a build receipt has nothing attested to upload."""
        workspace = u.Tests.create_release_workspace(tmp_path)

        tm.that(
            u.Tests.run_release_main(workspace, "--phase", "publish", "--apply"),
            ne=0,
        )

    @staticmethod
    def test_index_request_cannot_override_policy(
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """The public manual route rejects a forbidden destination before receipts."""
        workspace = u.Tests.create_release_workspace(tmp_path)
        tm.that(
            u.Tests.run_release_main(
                workspace,
                "--phase",
                "publish",
                "--apply",
                "--index",
            ),
            ne=0,
        )
        captured = capsys.readouterr()
        tm.that(
            "package index publication is disabled by release policy"
            in captured.out + captured.err,
            eq=not config.Infra.release.publish_index,
        )
