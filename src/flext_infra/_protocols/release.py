# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/release
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase, FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_infra import c, t
    from flext_infra._protocols._git import FlextInfraProtocolsGitWorktreeState


class FlextInfraProtocolsRelease:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ReleaseOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        phase: c.Infra.ReleasePhase
        index: bool
        pr_title: str
        ownership: FlextInfraProtocolsGitWorktreeState.GitLaneOwnershipReceipt | None

    @runtime_checkable
    class ReleaseRunCommand(
        FlextInfraProtocolsBase.CommandContext, ReleaseOptions, Protocol
    ):
        """Structural data contract projected from the owning model."""

        projects: Sequence[str] | None
        checkpoint_ref: t.NonEmptyStr | None

    @runtime_checkable
    class GithubReleaseAsset(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Native asset filename."""
            ...

        @property
        def digest(self) -> str | None:
            """Native digest, if available."""
            ...

        @property
        def state(self) -> t.NonEmptyStr:
            """Native upload state."""
            ...

    @runtime_checkable
    class GithubReleaseAssets(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def assets(self) -> tuple[FlextInfraProtocolsRelease.GithubReleaseAsset, ...]:
            """All release assets across API pages."""
            ...

    @runtime_checkable
    class GithubReleaseIdentity(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.PositiveInt:
            """Native release identifier."""
            ...

        @property
        def tag_name(self) -> t.NonEmptyStr:
            """Exact release tag."""
            ...

        @property
        def draft(self) -> bool:
            """Whether the release is an unpublished draft."""
            ...

    @runtime_checkable
    class GithubReleaseInventory(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def releases(
            self,
        ) -> tuple[FlextInfraProtocolsRelease.GithubReleaseIdentity, ...]:
            """All repository releases across API pages."""
            ...

    @runtime_checkable
    class SourceSnapshot(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid:
            """Source commit object ID."""
            ...

        @property
        def source_date_epoch(self) -> t.NonNegativeInt:
            """Source commit Unix epoch."""
            ...

    @runtime_checkable
    class BuildPolicy(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def build_constraints_path(self) -> t.Infra.ReleaseAbsolutePath:
            """Snapshotted build constraints absolute path."""
            ...

        @property
        def build_constraints_sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Pinned build constraint policy SHA-256."""
            ...

        @property
        def gitleaks_policy_path(self) -> t.Infra.ReleaseAbsolutePath:
            """Snapshotted Gitleaks policy absolute path."""
            ...

        @property
        def gitleaks_policy_sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Trusted Gitleaks policy SHA-256."""
            ...

    @runtime_checkable
    class BuildArtifact(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath:
            """Artifact absolute path."""
            ...

        @property
        def kind(self) -> t.Infra.ReleaseArtifactKind:
            """Wheel or sdist."""
            ...

        @property
        def sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Artifact SHA-256 digest."""
            ...

    @runtime_checkable
    class ArtifactExpectation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr:
            """Distribution name."""
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Distribution version."""
            ...

        @property
        def license_sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Committed source LICENSE SHA-256."""
            ...

        @property
        def allowed_roots(self) -> t.StrTuple:
            """Validated public source roots in the sdist."""
            ...

        @property
        def versions(self) -> Mapping[str, str]:
            """Resolved internal dependency versions."""
            ...

    @runtime_checkable
    class BuildRecord(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath:
            """Project absolute path."""
            ...

        @property
        def exit_code(self) -> t.StrictInt:
            """Artifact build command exit code, including signals."""
            ...

        @property
        def log(self) -> t.Infra.ReleaseAbsolutePath:
            """Build log absolute path."""
            ...

        @property
        def artifacts(self) -> tuple[FlextInfraProtocolsRelease.BuildArtifact, ...]:
            """Validated wheel and sdist artifacts."""
            ...

        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid | None:
            """Source commit object ID."""
            ...

        @property
        def source_date_epoch(self) -> t.NonNegativeInt | None:
            """Source commit Unix epoch."""
            ...

        @property
        def source_license_sha256(self) -> t.Infra.ReleaseArtifactSha256 | None:
            """Committed source LICENSE SHA-256."""
            ...

    @runtime_checkable
    class ReleasePlan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def current(self) -> t.NonEmptyStr:
            """Version declared by pyproject.toml."""
            ...

        @property
        def next(self) -> t.NonEmptyStr:
            """Version to release."""
            ...

        @property
        def bump(self) -> c.Infra.VersionBump:
            """Bump derived from merged PRs."""
            ...

        @property
        def previous_tag(self) -> t.NonEmptyStr | None:
            """Latest release tag, if any."""
            ...

        @property
        def merges(self) -> tuple[str, ...]:
            """Merged PR subjects since previous_tag."""
            ...

        @property
        def declared(self) -> bool:
            """Structural member projected from the owning model.

            ``next`` is the declared version itself (first release, finalized pre-
            release, or a version written beyond the last tag): decided when it was
            written, still untagged.
            """
            ...

        @property
        def tag(self) -> str:
            """Tag that will identify ``next``."""
            ...

        @property
        def releasable(self) -> bool:
            """Structural member projected from the owning model.

            Whether a release commit is due: a declared release, or a real bump.
            """
            ...

    @runtime_checkable
    class BuildReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> t.NonEmptyStr:
            """Release version."""
            ...

        @property
        def total(self) -> t.NonNegativeInt:
            """Total projects attempted."""
            ...

        @property
        def failures(self) -> t.NonNegativeInt:
            """Total projects with non-zero exit."""
            ...

        @property
        def records(self) -> tuple[FlextInfraProtocolsRelease.BuildRecord, ...]:
            """Per-project build records."""
            ...

        @property
        def dry_run(self) -> bool:
            """Metadata-only build report."""
            ...

        @property
        def build_constraints_sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Pinned build constraint policy SHA-256."""
            ...

        @property
        def gitleaks_policy_sha256(self) -> t.Infra.ReleaseArtifactSha256:
            """Trusted Gitleaks policy SHA-256."""
            ...

    @runtime_checkable
    class ReleasePhaseDispatchConfig(
        FlextInfraProtocolsMixins.ProjectNamesListMixin,
        FlextInfraProtocolsMixins.RepositoryRootPathMixin,
        FlextInfraProtocolsMixins.VersionTagMixin,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        dry_run: bool
        phase: c.Infra.ReleasePhase
        index: bool
        pr_title: str


__all__: list[str] = [
    "FlextInfraProtocolsRelease",
]
