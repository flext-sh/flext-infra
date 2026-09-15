"""Public release publish-phase behavior tests.

Publishing consumes only the build receipt: every artifact is re-hashed, the
GitHub release carries exactly those files, and the package index receives
them through trusted publishing. GitHub and the index are external services,
so the command contract is proven against recorded invocations.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_tests import tm

from tests import TestsFlextInfraUtilities as u, c, m, t


class TestsFlextInfraReleasePublish:
    """Behavior contract for the public release publish phase."""

    def _built_workspace(self, tmp_path: Path) -> t.Pair[Path, m.Infra.BuildReport]:
        """Build one member and return the workspace with its verified receipt."""
        project_name = "flext-a"
        workspace = u.Tests.create_release_workspace(
            tmp_path,
            project_names=(project_name, *c.Tests.RELEASE_INTERNAL_DEPENDENCIES),
            initialize_project_git=True,
        )
        notes = workspace / "docs" / "releases"
        notes.mkdir(parents=True)
        (notes / "v0.1.0.md").write_text("# Release v0.1.0\n", encoding="utf-8")
        tm.that(
            u.Tests.run_release_main(
                workspace, "--phase", "build", "--projects", project_name, "--apply"
            ),
            eq=0,
        )
        report_path = (
            u.Tests.release_report_dir(workspace, c.Tests.RELEASE_VERSION_BASE)
            / c.Infra.RELEASE_REPORT_FILENAME
        )
        return workspace, m.Infra.BuildReport.model_validate_json(
            report_path.read_text(encoding="utf-8")
        )

    def _shim_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Put recording shims for the external CLIs first on PATH."""
        bin_dir = tmp_path / "bin"
        u.Tests.cli_shim(bin_dir, c.Infra.GH)
        u.Tests.cli_shim(bin_dir, c.Infra.UV)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        return bin_dir

    def test_dry_run_verifies_the_receipt_without_effects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dry run proves the receipt and calls no external service."""
        workspace, _report = self._built_workspace(tmp_path)
        bin_dir = self._shim_path(tmp_path, monkeypatch)

        tm.that(u.Tests.run_release_main(workspace, "--phase", "publish"), eq=0)
        tm.that((bin_dir / f"{c.Infra.GH}.log").exists(), eq=False)

    def test_tampered_artifact_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An artifact whose bytes no longer match the receipt never leaves."""
        workspace, report = self._built_workspace(tmp_path)
        self._shim_path(tmp_path, monkeypatch)
        artifact = Path(report.records[0].artifacts[0].path)
        artifact.write_bytes(artifact.read_bytes() + b"\n")

        tm.that(
            u.Tests.run_release_main(workspace, "--phase", "publish", "--apply"), ne=0
        )

    def test_missing_receipt_is_refused(self, tmp_path: Path) -> None:
        """Publishing without a build receipt has nothing attested to upload."""
        workspace = u.Tests.create_release_workspace(tmp_path)

        tm.that(
            u.Tests.run_release_main(workspace, "--phase", "publish", "--apply"), ne=0
        )

    def test_github_release_carries_exactly_the_receipt_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The release is created with the receipt's wheel and sdist, nothing else."""
        workspace, report = self._built_workspace(tmp_path)
        bin_dir = self._shim_path(tmp_path, monkeypatch)

        result = u.Tests.run_release_main(workspace, "--phase", "publish", "--apply")

        tm.that(result, eq=0)
        recorded = (bin_dir / f"{c.Infra.GH}.log").read_text(encoding="utf-8")
        tm.that(recorded, has="release create v0.1.0 ")
        for artifact in report.records[0].artifacts:
            tm.that(recorded, has=artifact.path)
        tm.that(recorded, has="--notes-file")
        tm.that((bin_dir / f"{c.Infra.UV}.log").exists(), eq=False)

    def test_index_upload_uses_trusted_publishing_per_wave(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--index`` uploads the verified artifacts through trusted publishing."""
        workspace, report = self._built_workspace(tmp_path)
        bin_dir = self._shim_path(tmp_path, monkeypatch)

        result = u.Tests.run_release_main(
            workspace, "--phase", "publish", "--apply", "--index"
        )

        tm.that(result, eq=0)
        recorded = (bin_dir / f"{c.Infra.UV}.log").read_text(encoding="utf-8")
        tm.that(recorded, has="publish --no-config --publish-url ")
        tm.that(recorded, has=f"--check-url {c.Infra.PYPI_SIMPLE_INDEX_URL}")
        tm.that(recorded, has="--trusted-publishing always")
        for artifact in report.records[0].artifacts:
            tm.that(recorded, has=artifact.path)


__all__: list[str] = ["TestsFlextInfraReleasePublish"]
