"""Exact remote Git source acquisition for managed executable releases."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.release._managed_git_tool_contract import (
    FlextInfraManagedGitToolContractMixin,
)


class FlextInfraManagedGitToolSourceMixin(FlextInfraManagedGitToolContractMixin):
    """Validate one generic manifest and acquire its exact committed source."""

    @classmethod
    def _prepare_managed_git_source(
        cls, spec: m.Infra.ManagedGitToolRelease, temporary_root: Path
    ) -> p.Result[m.Infra.ManagedGitToolSourceStage]:
        validated = cls._validate_managed_git_tool_spec(spec)
        if validated.failure:
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                validated.error or "managed Git tool manifest is invalid"
            )
        git_result = cls._resolve_git_executable()
        if git_result.failure:
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                git_result.error or "Git resolution failed"
            )
        checkout = temporary_root / "checkout"
        output_root = temporary_root / "output"
        for directory in (checkout, output_root):
            ensured = u.Cli.ensure_dir(directory)
            if ensured.failure:
                return r[m.Infra.ManagedGitToolSourceStage].fail(
                    ensured.error or f"create managed release path failed: {directory}"
                )
        git = git_result.value
        commands: tuple[t.StrSequence, ...] = (
            ("init", "--quiet"),
            ("remote", "add", "origin", spec.source_url),
            ("fetch", "--depth=1", "--no-tags", "--force", "origin", spec.commit_oid),
            ("checkout", "--quiet", "--detach", "--force", spec.commit_oid),
        )
        for command in commands:
            result = cls._run_git(git, checkout, command)
            if result.failure:
                return r[m.Infra.ManagedGitToolSourceStage].fail(
                    result.error or f"Git source acquisition failed: {command[0]}"
                )
        for command, expected, label in (
            (("remote", "get-url", "origin"), spec.source_url, "source URL"),
            (("rev-parse", "HEAD^{commit}"), spec.commit_oid, "commit OID"),
            (("cat-file", "-t", spec.commit_oid), "commit", "object type"),
        ):
            observed = cls._run_git(git, checkout, command)
            if observed.failure or observed.value.stdout.strip() != expected:
                detail = (
                    observed.error
                    if observed.failure
                    else observed.value.stdout.strip()
                )
                return r[m.Infra.ManagedGitToolSourceStage].fail(
                    f"managed Git {label} mismatch: {detail}"
                )
        status = cls._run_git(git, checkout, ("status", "--porcelain"))
        if status.failure or status.value.stdout.strip():
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                status.error or "managed Git source checkout is dirty"
            )
        if (checkout / ".gitmodules").exists():
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                "managed Git source contains undeclared nested repositories"
            )
        epoch = cls._run_git(
            git, checkout, ("show", "-s", "--format=%ct", spec.commit_oid)
        )
        if epoch.failure or not epoch.value.stdout.strip().isdigit():
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                epoch.error or "managed Git commit epoch is invalid"
            )
        archive = temporary_root / c.Infra.MANAGED_GIT_TOOL_SOURCE_ARCHIVE_FILENAME
        archived = cls._run_git(
            git,
            checkout,
            ("archive", "--format=tar", f"--output={archive}", spec.commit_oid),
        )
        if archived.failure:
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                archived.error or "managed Git archive failed"
            )
        archive_validation = cls._validate_git_source_archive(archive)
        if archive_validation.failure:
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                archive_validation.error or "managed Git archive validation failed"
            )
        source_root = (checkout / spec.source_subdirectory).resolve()
        if not source_root.is_relative_to(checkout) or not source_root.is_dir():
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                f"managed Git source subdirectory is absent: {spec.source_subdirectory}"
            )
        artifact_path = (output_root / spec.artifact.build_path).resolve()
        if not artifact_path.is_relative_to(output_root):
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                "managed Git artifact resolves outside the output root"
            )
        ensured_parent = u.Cli.ensure_dir(artifact_path.parent)
        if ensured_parent.failure:
            return r[m.Infra.ManagedGitToolSourceStage].fail(
                ensured_parent.error or "managed Git artifact parent creation failed"
            )
        return r[m.Infra.ManagedGitToolSourceStage].ok(
            m.Infra.ManagedGitToolSourceStage(
                checkout_root=checkout,
                source_root=source_root,
                output_root=output_root,
                artifact_path=artifact_path,
                snapshot=m.Infra.SourceSnapshot(
                    commit_oid=spec.commit_oid,
                    source_date_epoch=int(epoch.value.stdout.strip()),
                ),
                source_archive_sha256=u.Cli.sha256_file(archive),
            )
        )


__all__: list[str] = ["FlextInfraManagedGitToolSourceMixin"]
