"""Immutable release artifact construction from committed source snapshots."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, t, u

from ._release_artifact_execution import FlextInfraReleaseArtifactExecutionMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraReleaseArtifactBuildMixin(FlextInfraReleaseArtifactExecutionMixin):
    """Build registry-safe artifacts from committed project sources.

    ``versions`` maps every internal distribution the build can see to the
    version its own repository declares; release metadata pins internal
    dependencies to those declared versions, never to this project's version.
    """

    def _render_release_metadata(
        self,
        *,
        project: str,
        stage_path: Path,
        output_dir: Path,
        version: str,
        versions: t.StrMapping,
    ) -> p.Result[bool]:
        """Render validated registry metadata into stage and audit output."""
        pyproject_path = stage_path / c.Infra.PYPROJECT_FILENAME
        source_result = u.Cli.files_read_text(pyproject_path)
        if source_result.failure:
            return r[bool].from_failure(source_result)
        render_result = self._release_pyproject(source_result.value, version, versions)
        if render_result.failure:
            return r[bool].from_failure(render_result)
        for path in (
            pyproject_path,
            output_dir / "metadata" / f"{project}-pyproject.toml",
        ):
            write_result = self._write_release_text(path, render_result.value)
            if write_result.failure:
                return r[bool].from_failure(write_result)
        return r[bool].ok(True)

    def _stage_release_source(
        self,
        *,
        project: str,
        project_path: Path,
        stage_path: Path,
        output_dir: Path,
        gitleaks_config_path: Path,
        version: str,
        versions: t.StrMapping,
    ) -> p.Result[t.Pair[m.Infra.SourceSnapshot, str]]:
        """Stage and validate committed source, returning epoch and license digest."""
        archive_result = self._archive_project(project_path, stage_path)
        if archive_result.failure:
            return r[t.Pair[m.Infra.SourceSnapshot, str]].from_failure(archive_result)
        for result in (
            self._validate_staged_source(stage_path),
            self._scan_staged_source(stage_path, gitleaks_config_path),
        ):
            if result.failure:
                return r[t.Pair[m.Infra.SourceSnapshot, str]].from_failure(result)
        license_result = self._source_license_digest(stage_path)
        if license_result.failure:
            return r[t.Pair[m.Infra.SourceSnapshot, str]].from_failure(license_result)
        metadata_result = self._render_release_metadata(
            project=project,
            stage_path=stage_path,
            output_dir=output_dir,
            version=version,
            versions=versions,
        )
        if metadata_result.failure:
            return r[t.Pair[m.Infra.SourceSnapshot, str]].from_failure(metadata_result)
        return r[t.Pair[m.Infra.SourceSnapshot, str]].ok((
            archive_result.value,
            license_result.value,
        ))

    def _validated_artifact_models(
        self,
        *,
        temporary_dist: Path,
        output_dir: Path,
        project: str,
        version: str,
        versions: t.StrMapping,
        license_sha256: str,
    ) -> p.Result[t.SequenceOf[m.Infra.BuildArtifact]]:
        """Validate a complete artifact set and persist it atomically."""
        built_result = self._build_artifact_paths(temporary_dist)
        if built_result.failure:
            return r[t.SequenceOf[m.Infra.BuildArtifact]].from_failure(built_result)
        validated: t.MutableSequenceOf[
            t.Triple[Path, t.Infra.ReleaseArtifactKind, t.Infra.ReleaseArtifactSha256]
        ] = []
        for source in built_result.value:
            validation = self._validate_artifact(
                source, project, version, license_sha256, versions
            )
            if validation.failure:
                return r[t.SequenceOf[m.Infra.BuildArtifact]].from_failure(validation)
            kind, digest = validation.value
            validated.append((source, kind, digest))
        persistence_result = self._persist_artifact_set(
            validated, output_dir / "artifacts" / project
        )
        if persistence_result.failure:
            return r[t.SequenceOf[m.Infra.BuildArtifact]].from_failure(
                persistence_result
            )
        return r[t.SequenceOf[m.Infra.BuildArtifact]].ok(
            tuple(
                m.Infra.BuildArtifact(
                    path=str(destination.resolve()), kind=kind, sha256=digest
                )
                for (_, kind, digest), destination in zip(
                    validated, persistence_result.value, strict=True
                )
            )
        )

    def _successful_release_record(
        self,
        *,
        project: str,
        project_path: Path,
        output_dir: Path,
        version: str,
        versions: t.StrMapping,
        license_sha256: str,
        snapshot: m.Infra.SourceSnapshot,
        temporary_dist: Path,
        log_path: Path,
    ) -> p.Result[m.Infra.BuildRecord]:
        """Finalize validated artifacts into one successful build record."""
        artifacts_result = self._validated_artifact_models(
            temporary_dist=temporary_dist,
            output_dir=output_dir,
            project=project,
            version=version,
            versions=versions,
            license_sha256=license_sha256,
        )
        if artifacts_result.failure:
            return r[m.Infra.BuildRecord].from_failure(artifacts_result)
        return r[m.Infra.BuildRecord].ok(
            self._build_record(
                project=project,
                project_path=project_path,
                log_path=log_path,
                exit_code=0,
                artifacts=artifacts_result.value,
                snapshot=snapshot,
                source_license_sha256=license_sha256,
            )
        )

    def _built_release_record(
        self,
        *,
        project: str,
        project_path: Path,
        output_dir: Path,
        build_constraints_path: Path,
        version: str,
        versions: t.StrMapping,
        snapshot: m.Infra.SourceSnapshot,
        license_sha256: str,
        stage_path: Path,
        temporary_dist: Path,
        log_path: Path,
    ) -> p.Result[m.Infra.BuildRecord]:
        """Execute, validate, and record one non-dry release build."""
        build_result = self._execute_release_build(
            stage_path=stage_path,
            temporary_dist=temporary_dist,
            build_constraints_path=build_constraints_path,
            source_date_epoch=snapshot.source_date_epoch,
            log_path=log_path,
        )
        if build_result.failure:
            return r[m.Infra.BuildRecord].from_failure(build_result)
        command = build_result.value
        if not u.Cli.process_succeeded(command.outcome):
            return r[m.Infra.BuildRecord].ok(
                self._build_record(
                    project=project,
                    project_path=project_path,
                    log_path=log_path,
                    exit_code=command.outcome.raw_return_code,
                    snapshot=snapshot,
                    source_license_sha256=license_sha256,
                )
            )
        return self._successful_release_record(
            project=project,
            project_path=project_path,
            output_dir=output_dir,
            version=version,
            versions=versions,
            license_sha256=license_sha256,
            snapshot=snapshot,
            temporary_dist=temporary_dist,
            log_path=log_path,
        )

    def _dry_run_release_record(
        self,
        *,
        project: str,
        project_path: Path,
        log_path: Path,
        snapshot: m.Infra.SourceSnapshot,
        source_license_sha256: str,
    ) -> p.Result[m.Infra.BuildRecord]:
        """Persist and return one metadata-only dry-run record."""
        write_result = self._write_release_text(
            log_path, f"release metadata staged and validated: {project}\n"
        )
        if write_result.failure:
            return r[m.Infra.BuildRecord].from_failure(write_result)
        return r[m.Infra.BuildRecord].ok(
            self._build_record(
                project=project,
                project_path=project_path,
                log_path=log_path,
                exit_code=0,
                snapshot=snapshot,
                source_license_sha256=source_license_sha256,
            )
        )

    def _build_release_record(
        self,
        *,
        project: str,
        project_path: Path,
        output_dir: Path,
        build_constraints_path: Path,
        gitleaks_config_path: Path,
        version: str,
        versions: t.StrMapping,
        dry_run: bool,
    ) -> p.Result[m.Infra.BuildRecord]:
        """Build and validate one project from its committed Git snapshot."""
        try:
            with TemporaryDirectory(prefix=f"{project}-", dir=output_dir) as temporary:
                return self._build_staged_record(
                    project=project,
                    project_path=project_path,
                    output_dir=output_dir,
                    build_constraints_path=build_constraints_path,
                    gitleaks_config_path=gitleaks_config_path,
                    version=version,
                    versions=versions,
                    dry_run=dry_run,
                    temporary_root=Path(temporary),
                )
        except OSError as exc:
            return r[m.Infra.BuildRecord].fail_op(
                f"manage temporary release build for {project}", exc
            )

    def _build_staged_record(
        self,
        *,
        project: str,
        project_path: Path,
        output_dir: Path,
        build_constraints_path: Path,
        gitleaks_config_path: Path,
        version: str,
        versions: t.StrMapping,
        dry_run: bool,
        temporary_root: Path,
    ) -> p.Result[m.Infra.BuildRecord]:
        """Build one release record inside an owned temporary directory."""
        log_path = output_dir / f"build-{project}.log"
        stage_path = temporary_root / "source"
        stage_result = self._stage_release_source(
            project=project,
            project_path=project_path,
            stage_path=stage_path,
            output_dir=output_dir,
            gitleaks_config_path=gitleaks_config_path,
            version=version,
            versions=versions,
        )
        if stage_result.failure:
            return r[m.Infra.BuildRecord].from_failure(stage_result)
        snapshot, license_sha256 = stage_result.value
        if dry_run:
            return self._dry_run_release_record(
                project=project,
                project_path=project_path,
                log_path=log_path,
                snapshot=snapshot,
                source_license_sha256=license_sha256,
            )
        return self._built_release_record(
            project=project,
            project_path=project_path,
            output_dir=output_dir,
            build_constraints_path=build_constraints_path,
            version=version,
            versions=versions,
            snapshot=snapshot,
            license_sha256=license_sha256,
            stage_path=stage_path,
            temporary_dist=temporary_root / "dist",
            log_path=log_path,
        )


__all__: list[str] = ["FlextInfraReleaseArtifactBuildMixin"]
