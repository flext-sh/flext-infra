"""Behavior tests for fail-closed workspace editable provenance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def _workspace(root: Path, distribution: str = "sample-member") -> Path:
    root.mkdir()
    member = root / distribution
    (member / "src").mkdir(parents=True)
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "workspace.yaml").write_text(
        f"""
version: 2
name: sample
repository:
  name: sample
  distribution: sample
  provider: flext-sh
  url: https://github.com/flext-sh/sample.git
  branch: main
  path: .
  role: workspace-root
  state: active
  profile: workspace-root
  checkout: root
  codegen: conform
  package: false
  editable: false
  read_only: false
members:
  - name: {distribution}
    distribution: {distribution}
    provider: flext-sh
    url: https://github.com/flext-sh/{distribution}.git
    branch: main
    path: {distribution}
    role: workspace-member
    state: active
    profile: workspace-member
    checkout: submodule
    codegen: conform
    package: true
    editable: true
    read_only: false
content_only: []
exclusions: []
""".lstrip(),
        encoding="utf-8",
    )
    return root


def _installed_editable(
    site_packages: Path, distribution: str, *, direct_root: Path, source_root: Path
) -> None:
    site_packages.mkdir()
    normalized = distribution.replace("-", "_")
    dist_info = site_packages / f"{normalized}-1.0.dist-info"
    dist_info.mkdir()
    pth_name = f"_editable_impl_{normalized}.pth"
    (site_packages / pth_name).write_text(f"{source_root}\n", encoding="utf-8")
    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.4\nName: {distribution}\nVersion: 1.0\n", encoding="utf-8"
    )
    (dist_info / "direct_url.json").write_text(
        (f'{{"url":"{direct_root.as_uri()}","dir_info":{{"editable":true}}}}\n'),
        encoding="utf-8",
    )
    (dist_info / "RECORD").write_text(
        (
            f"{pth_name},,\n"
            f"{dist_info.name}/METADATA,,\n"
            f"{dist_info.name}/direct_url.json,,\n"
            f"{dist_info.name}/RECORD,,\n"
        ),
        encoding="utf-8",
    )


class TestsFlextInfraWorkspaceEnvironmentProvenance:
    """Validate real PEP 610 and distribution file metadata."""

    def test_accepts_exact_live_editable(self, tmp_path: Path) -> None:
        """Accept one exact PEP 610 editable installed from the live member."""
        workspace = _workspace(tmp_path / "workspace")
        member = workspace / "sample-member"
        site_packages = tmp_path / "site-packages"
        _installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=member / "src",
        )

        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace, metadata_paths=(str(site_packages),)
        )

        tm.ok(result, eq=1)

    def test_rejects_stale_direct_url(self, tmp_path: Path) -> None:
        """Reject an editable whose direct URL targets an obsolete checkout."""
        workspace = _workspace(tmp_path / "workspace")
        member = workspace / "sample-member"
        stale = tmp_path / "stale" / "sample-member"
        (stale / "src").mkdir(parents=True)
        site_packages = tmp_path / "site-packages"
        _installed_editable(
            site_packages,
            "sample-member",
            direct_root=stale,
            source_root=member / "src",
        )

        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace, metadata_paths=(str(site_packages),)
        )

        error = tm.fail(result)
        tm.that(error, has="direct_url mismatch")
        tm.that(error, has=f"expected={member}")
        tm.that(error, has=f"actual={stale}")

    def test_rejects_stale_pth_source(self, tmp_path: Path) -> None:
        """Reject an editable path file that exposes an obsolete source tree."""
        workspace = _workspace(tmp_path / "workspace")
        member = workspace / "sample-member"
        stale = tmp_path / "stale" / "sample-member"
        (stale / "src").mkdir(parents=True)
        site_packages = tmp_path / "site-packages"
        _installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=stale / "src",
        )

        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace, metadata_paths=(str(site_packages),)
        )

        error = tm.fail(result)
        tm.that(error, has="pth mismatch")
        tm.that(error, has=f"expected_root={member}")
        tm.that(error, has=f"actual={stale / 'src'}")

    def test_rejects_missing_distribution(self, tmp_path: Path) -> None:
        """Fail loud when a declared editable distribution is not installed."""
        workspace = _workspace(tmp_path / "workspace")
        site_packages = tmp_path / "site-packages"
        site_packages.mkdir()

        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace, metadata_paths=(str(site_packages),)
        )

        error = tm.fail(result)
        tm.that(error, has="distribution count mismatch")
        tm.that(error, has="distribution=sample-member")

    def test_request_model_uses_workspace_cli_alias(self, tmp_path: Path) -> None:
        """Parse the public workspace CLI flag into the canonical request field."""
        workspace = _workspace(tmp_path / "workspace")

        request = m.Infra.WorkspaceEnvironmentRequest.model_validate(
            {"workspace": workspace}
        )

        tm.that(request.workspace_root, eq=workspace)
