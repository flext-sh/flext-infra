"""Committed-source preparation and isolated build environment policy."""

from __future__ import annotations

import tarfile
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, u

from ._release_artifact_metadata import FlextInfraReleaseArtifactMetadataMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraReleaseArtifactSourceMixin(FlextInfraReleaseArtifactMetadataMixin):
    """Prepare immutable source snapshots under trusted release policies."""

    @staticmethod
    def _scan_staged_source(
        stage_path: Path, gitleaks_config_path: Path
    ) -> p.Result[bool]:
        """Scan committed staged source with the canonical secret scanner."""
        config_result = u.Cli.files_read_text(gitleaks_config_path)
        if config_result.failure or not config_result.value.strip():
            return r[bool].fail(
                config_result.error
                or f"release Gitleaks policy is empty: {gitleaks_config_path}"
            )
        scan_result = u.Cli.run_raw(
            [
                c.Infra.GITLEAKS,
                "dir",
                "--config",
                str(gitleaks_config_path),
                "--gitleaks-ignore-path",
                str(gitleaks_config_path.parent),
                "--no-banner",
                "--no-color",
                "--redact=100",
                "--exit-code",
                str(c.Infra.GITLEAKS_LEAK_EXIT_CODE),
                "--ignore-gitleaks-allow",
                str(stage_path),
            ],
            cwd=gitleaks_config_path.parent,
            timeout=c.Infra.TIMEOUT_LONG,
            remove_env_keys=c.Infra.GITLEAKS_POLICY_ENV_KEYS,
        )
        if scan_result.failure:
            return r[bool].from_failure(scan_result)
        command = scan_result.value
        if command.outcome.raw_return_code == c.Infra.GITLEAKS_LEAK_EXIT_CODE:
            return r[bool].fail("gitleaks detected a secret in staged release source")
        if not u.Cli.process_succeeded(command.outcome):
            return r[bool].fail(
                f"gitleaks failed with exit code {command.outcome.raw_return_code}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _archive_project(
        project_path: Path, stage_path: Path
    ) -> p.Result[m.Infra.SourceSnapshot]:
        """Extract one immutable commit and return its modeled source identity."""
        status_result = u.Cli.capture(
            [c.Infra.GIT, "status", "--porcelain"],
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if status_result.failure:
            return r[m.Infra.SourceSnapshot].from_failure(status_result)
        if status_result.value.strip():
            return r[m.Infra.SourceSnapshot].fail(
                f"release project is dirty: {project_path}"
            )
        oid_result = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", f"{c.Infra.GIT_HEAD}^{{commit}}"],
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if oid_result.failure:
            return r[m.Infra.SourceSnapshot].from_failure(oid_result)
        oid = oid_result.value.strip()
        epoch_result = u.Cli.capture(
            [c.Infra.GIT, "show", "-s", "--format=%ct", oid],
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if epoch_result.failure:
            return r[m.Infra.SourceSnapshot].from_failure(epoch_result)
        source_date_epoch = epoch_result.value.strip()
        if not source_date_epoch.isdigit():
            return r[m.Infra.SourceSnapshot].fail(
                f"commit epoch is not an integer for {project_path}: {source_date_epoch}"
            )
        archive_path = stage_path.parent / f"{stage_path.name}.tar"
        archive_result = u.Cli.run_checked(
            [c.Infra.GIT, "archive", "--format=tar", f"--output={archive_path}", oid],
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if archive_result.failure:
            return r[m.Infra.SourceSnapshot].from_failure(archive_result)
        try:
            with tarfile.open(archive_path, "r") as archive:
                extracted = u.Infra.materialize_tar_tree(archive, stage_path)
                if extracted.failure:
                    return r[m.Infra.SourceSnapshot].from_failure(extracted)
        except (OSError, tarfile.TarError) as exc:
            return r[m.Infra.SourceSnapshot].fail(
                f"extract committed release source failed: {exc}", exception=exc
            )
        try:
            snapshot = m.Infra.SourceSnapshot(
                commit_oid=oid, source_date_epoch=int(source_date_epoch)
            )
        except c.ValidationError as exc:
            return r[m.Infra.SourceSnapshot].fail_op(
                "validate committed release source identity", exc
            )
        return r[m.Infra.SourceSnapshot].ok(snapshot)

    @staticmethod
    def _write_release_text(path: Path, content: str) -> p.Result[bool]:
        """Write release text through the Result-based filesystem boundary."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op(
                f"create release output directory {path.parent}", exc
            )
        return u.Cli.files_write_text(path, content)


__all__: list[str] = ["FlextInfraReleaseArtifactSourceMixin"]
