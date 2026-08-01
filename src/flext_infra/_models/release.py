"""Domain models for the release subpackage."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from packaging.version import InvalidVersion, Version

from flext_cli import m
from flext_core import u
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsRelease:
    """Models for release management."""

    class SourceSnapshot(m.StrictBoundaryModel):
        """Immutable committed source identity used by one project build."""

        commit_oid: Annotated[
            t.Infra.ReleaseCommitOid, m.Field(description="Source commit object ID")
        ]
        source_date_epoch: Annotated[
            t.NonNegativeInt, m.Field(description="Source commit Unix epoch")
        ]

    class ManagedGitToolEnvironmentVariable(m.StrictBoundaryModel):
        """One explicit environment entry supplied to a managed build."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^[A-Z_][A-Z0-9_]*$", description="Environment key"),
        ]
        value: Annotated[str, m.Field(description="Environment value")]

    class ManagedGitToolProbe(m.StrictBoundaryModel):
        """One staged-artifact command and its required output fragments."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^[a-z0-9][a-z0-9._-]*$", description="Probe name"),
        ]
        command: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Argument-vector probe command"),
        ]
        expected_output_contains: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Required output fragments"),
        ]

    class ManagedGitToolArtifact(m.StrictBoundaryModel):
        """One source-built executable and its immutable activation contract."""

        build_path: Annotated[
            Path, m.Field(description="Build-output path relative to the output root")
        ]
        install_path: Annotated[
            Path, m.Field(description="Absolute executable activation path")
        ]
        sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Expected executable SHA-256"),
        ]

    class ManagedGitToolRelease(m.StrictBoundaryModel):
        """Exact Git source, deterministic build, probe, and activation contract."""

        release_name: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[a-z0-9][a-z0-9._-]*$",
                description="Consumer-owned release identifier",
            ),
        ]
        source_url: Annotated[
            t.NonEmptyStr, m.Field(description="Official HTTPS Git repository URL")
        ]
        commit_oid: Annotated[
            t.Infra.ReleaseCommitOid, m.Field(description="Exact source commit OID")
        ]
        source_subdirectory: Annotated[
            Path, m.Field(description="Build root relative to the repository root")
        ] = Path()
        build_command: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Argument-vector build command"),
        ]
        build_environment: Annotated[
            tuple[FlextInfraModelsRelease.ManagedGitToolEnvironmentVariable, ...],
            m.Field(description="Explicit deterministic build environment"),
        ] = ()
        artifact: Annotated[
            FlextInfraModelsRelease.ManagedGitToolArtifact,
            m.Field(description="Single atomically activated executable"),
        ]
        probes: Annotated[
            tuple[FlextInfraModelsRelease.ManagedGitToolProbe, ...],
            m.Field(min_length=1, description="Required staged-runtime probes"),
        ]
        artifact_store: Annotated[
            Path, m.Field(description="Absolute immutable artifact-set root")
        ]

    class ManagedGitToolSourceStage(m.StrictBoundaryModel):
        """Validated temporary paths and provenance for one exact Git source."""

        checkout_root: Annotated[
            Path, m.Field(description="Isolated detached Git checkout")
        ]
        source_root: Annotated[Path, m.Field(description="Configured build root")]
        output_root: Annotated[Path, m.Field(description="Isolated build output root")]
        artifact_path: Annotated[
            Path, m.Field(description="Expected staged executable path")
        ]
        snapshot: Annotated[
            FlextInfraModelsRelease.SourceSnapshot,
            m.Field(description="Exact commit identity and epoch"),
        ]
        source_archive_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Validated Git archive SHA-256"),
        ]

    class ManagedGitToolProbeReceipt(m.StrictBoundaryModel):
        """Observed output and digest for one successful runtime probe."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Probe name")]
        command: Annotated[
            tuple[t.NonEmptyStr, ...], m.Field(description="Executed argument vector")
        ]
        stdout: Annotated[str, m.Field(description="Probe standard output")]
        stderr: Annotated[str, m.Field(description="Probe standard error")]
        output_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="SHA-256 of stdout and stderr"),
        ]

    class ManagedGitToolArtifactReceipt(m.StrictBoundaryModel):
        """Content and path proof for one persisted executable."""

        store_path: Annotated[
            Path, m.Field(description="Immutable persisted executable path")
        ]
        install_path: Annotated[
            Path, m.Field(description="Configured executable activation path")
        ]
        sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Verified executable SHA-256"),
        ]
        size: Annotated[
            t.NonNegativeInt, m.Field(description="Executable size in bytes")
        ]

    class ManagedGitToolReleaseReceipt(m.StrictBoundaryModel):
        """Complete provenance and activation proof for a managed Git tool."""

        release_name: Annotated[
            t.NonEmptyStr, m.Field(description="Consumer-owned release identifier")
        ]
        source_url: Annotated[
            t.NonEmptyStr, m.Field(description="Verified official source URL")
        ]
        commit_oid: Annotated[
            t.Infra.ReleaseCommitOid, m.Field(description="Verified source commit OID")
        ]
        source_date_epoch: Annotated[
            t.NonNegativeInt, m.Field(description="Source commit Unix epoch")
        ]
        source_archive_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Validated source archive SHA-256"),
        ]
        artifact: Annotated[
            FlextInfraModelsRelease.ManagedGitToolArtifactReceipt,
            m.Field(description="Persisted executable proof"),
        ]
        probes: Annotated[
            tuple[FlextInfraModelsRelease.ManagedGitToolProbeReceipt, ...],
            m.Field(min_length=1, description="Staged-runtime probe evidence"),
        ]
        receipt_path: Annotated[
            Path, m.Field(description="Configured immutable receipt path")
        ]

    class ManagedGitToolReleaseResult(m.StrictBoundaryModel):
        """Observable persistence and activation outcome for one release."""

        receipt: Annotated[
            FlextInfraModelsRelease.ManagedGitToolReleaseReceipt,
            m.Field(description="Validated provenance and runtime-probe receipt"),
        ]
        persisted: Annotated[
            bool, m.Field(description="Whether the immutable artifact set is present")
        ]
        activated: Annotated[
            bool, m.Field(description="Whether the configured executable is active")
        ]

    class BuildPolicy(m.StrictBoundaryModel):
        """Immutable policy snapshot used by every build in one report."""

        build_constraints_path: Annotated[
            t.Infra.ReleaseAbsolutePath,
            m.Field(description="Snapshotted build constraints absolute path"),
        ]
        build_constraints_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Pinned build constraint policy SHA-256"),
        ]
        gitleaks_policy_path: Annotated[
            t.Infra.ReleaseAbsolutePath,
            m.Field(description="Snapshotted Gitleaks policy absolute path"),
        ]
        gitleaks_policy_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Trusted Gitleaks policy SHA-256"),
        ]

    class BuildArtifact(m.StrictBoundaryModel):
        """Immutable artifact emitted by one release build."""

        path: Annotated[
            t.Infra.ReleaseAbsolutePath, m.Field(description="Artifact absolute path")
        ]
        kind: Annotated[
            t.Infra.ReleaseArtifactKind, m.Field(description="wheel or sdist")
        ]
        sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Artifact SHA-256 digest"),
        ]

        @u.model_validator(mode="after")
        def validate_kind_filename(self) -> Self:
            """Require the declared artifact kind to match its immutable filename."""
            name = Path(self.path).name
            valid = (self.kind == "wheel" and name.endswith(".whl")) or (
                self.kind == "sdist" and name.endswith(".tar.gz")
            )
            if not valid:
                msg = f"artifact kind does not match filename: {self.kind}={name}"
                raise ValueError(msg)
            return self

    class BuildRecord(mm.ProjectNameMixin, m.StrictBoundaryModel):
        """Base model for build result data."""

        path: Annotated[
            t.Infra.ReleaseAbsolutePath, m.Field(description="Project absolute path")
        ]
        exit_code: Annotated[
            t.StrictInt,
            m.Field(description="Artifact build command exit code, including signals"),
        ]
        log: Annotated[
            t.Infra.ReleaseAbsolutePath, m.Field(description="Build log absolute path")
        ]
        artifacts: Annotated[
            t.VariadicTuple[FlextInfraModelsRelease.BuildArtifact],
            m.Field(default=(), description="Validated wheel and sdist artifacts"),
        ]
        commit_oid: Annotated[
            t.Infra.ReleaseCommitOid | None,
            m.Field(default=None, description="Source commit object ID"),
        ] = None
        source_date_epoch: Annotated[
            t.NonNegativeInt | None,
            m.Field(default=None, description="Source commit Unix epoch"),
        ] = None
        source_license_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256 | None,
            m.Field(default=None, description="Committed source LICENSE SHA-256"),
        ] = None

        @u.model_validator(mode="after")
        def validate_provenance(self) -> Self:
            """Require source provenance to be complete whenever it is available."""
            values = (
                self.commit_oid,
                self.source_date_epoch,
                self.source_license_sha256,
            )
            if any(value is None for value in values) and any(
                value is not None for value in values
            ):
                msg = "build record source provenance must be complete"
                raise ValueError(msg)
            return self

    class ReleaseSpec(mm.VersionTagMixin, m.ArbitraryTypesModel):
        """Release descriptor with version, tag, and bump metadata."""

        bump_type: Annotated[t.NonEmptyStr, m.Field(description="Release bump type")]

        @u.model_validator(mode="after")
        def validate_identity(self) -> Self:
            """Require canonical PEP 440 version and its exact v-prefixed tag."""
            try:
                parsed = Version(self.version)
            except InvalidVersion as exc:
                msg = f"invalid PEP 440 release version: {self.version}"
                raise ValueError(msg) from exc
            if str(parsed) != self.version or self.tag != f"v{self.version}":
                msg = f"release version/tag mismatch: {self.version} != {self.tag}"
                raise ValueError(msg)
            return self

    class BuildReport(m.StrictBoundaryModel):
        """Aggregated build report payload written to JSON."""

        version: Annotated[t.NonEmptyStr, m.Field(description="Release version")]
        total: Annotated[
            t.NonNegativeInt, m.Field(description="Total projects attempted")
        ]
        failures: Annotated[
            t.NonNegativeInt, m.Field(description="Total projects with non-zero exit")
        ]
        records: Annotated[
            t.VariadicTuple[FlextInfraModelsRelease.BuildRecord],
            m.Field(default=(), description="Per-project build records"),
        ]
        dry_run: Annotated[bool, m.Field(description="Metadata-only build report")]
        build_constraints_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Pinned build constraint policy SHA-256"),
        ]
        gitleaks_policy_sha256: Annotated[
            t.Infra.ReleaseArtifactSha256,
            m.Field(description="Trusted Gitleaks policy SHA-256"),
        ]

        @u.model_validator(mode="after")
        def validate_manifest(self) -> Self:
            """Require totals, project identity, outcomes, and artifacts to agree."""
            if self.total != len(self.records):
                msg = "build report total does not match record count"
                raise ValueError(msg)
            failures = sum(record.exit_code != 0 for record in self.records)
            if self.failures != failures:
                msg = "build report failures do not match record outcomes"
                raise ValueError(msg)
            projects = tuple(record.project for record in self.records)
            if len(projects) != len(set(projects)):
                msg = "build report contains duplicate projects"
                raise ValueError(msg)
            if not self.dry_run and not self.records:
                msg = "non-dry build report contains no projects"
                raise ValueError(msg)
            for record in self.records:
                kinds = {artifact.kind for artifact in record.artifacts}
                paths = tuple(artifact.path for artifact in record.artifacts)
                if record.exit_code != 0 and record.artifacts:
                    msg = f"failed build contains artifacts: {record.project}"
                    raise ValueError(msg)
                if record.exit_code == 0 and self.dry_run and record.artifacts:
                    msg = f"dry-run build contains artifacts: {record.project}"
                    raise ValueError(msg)
                if (
                    record.exit_code == 0
                    and not self.dry_run
                    and (
                        len(record.artifacts) != len(kinds)
                        or len(paths) != len(set(paths))
                        or kinds != {"wheel", "sdist"}
                    )
                ):
                    msg = f"successful build lacks wheel and sdist: {record.project}"
                    raise ValueError(msg)
                if record.exit_code == 0 and record.commit_oid is None:
                    msg = f"successful build lacks source provenance: {record.project}"
                    raise ValueError(msg)
            return self

    class ReleaseOrchestratorConfig(
        mm.ProjectNamesOptionalMixin,
        mm.WorkspaceRootPathMixin,
        mm.VersionTagMixin,
        mm.AutomationMixin,
        m.ArbitraryTypesModel,
    ):
        """Configuration for release workflow execution."""

        dry_run: Annotated[bool, m.Field(description="Dry run flag")] = False
        phases: Annotated[t.StrSequence, m.Field(description="Ordered list of phases")]
        create_branches: Annotated[
            bool, m.Field(description="Create branches flag")
        ] = True
        next_dev: Annotated[bool, m.Field(description="Next dev flag")] = False
        next_bump: Annotated[str, m.Field(description="Next bump")] = "minor"

    class ReleasePhaseDispatchConfig(
        mm.ProjectNamesListMixin,
        mm.WorkspaceRootPathMixin,
        mm.VersionTagMixin,
        mm.AutomationMixin,
        m.ArbitraryTypesModel,
    ):
        """Configuration for single release phase dispatch."""

        dry_run: Annotated[bool, m.Field(description="Dry run flag")] = False
        phase: Annotated[t.NonEmptyStr, m.Field(description="Release phase")]


__all__: list[str] = ["FlextInfraModelsRelease"]
