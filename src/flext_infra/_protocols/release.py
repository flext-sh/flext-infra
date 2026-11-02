# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/release
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsRelease:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ReleaseOptions(Protocol):
        """Structural data contract projected from the owning model."""

        phase: c.Infra.ReleasePhase
        index: bool
        pr_title: str
        ownership: p.Infra.GitLaneOwnershipReceipt | None

    @runtime_checkable
    class ReleaseRunCommand(Protocol):
        """Structural data contract projected from the owning model."""

        phase: c.Infra.ReleasePhase
        index: bool
        pr_title: str
        ownership: p.Infra.GitLaneOwnershipReceipt | None
        repository_root: Path
        apply_changes: bool
        check_only: bool
        dry_run: bool
        output_format: str
        project_filter: str | None
        report_path: Path | None
        output_dir: Path | None

        @property
        def root(self) -> Path: ...
        @property
        def effective_dry_run(self) -> bool: ...

        projects: Sequence[str] | None
        checkpoint_ref: t.NonEmptyStr | None

    @runtime_checkable
    class GithubReleaseAsset(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def digest(self) -> str | None: ...
        @property
        def state(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GithubReleaseAssets(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def assets(self) -> tuple[p.Infra.GithubReleaseAsset, ...]: ...

    @runtime_checkable
    class GithubReleaseIdentity(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.PositiveInt: ...
        @property
        def tag_name(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GithubReleaseInventory(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def releases(self) -> tuple[p.Infra.GithubReleaseIdentity, ...]: ...

    @runtime_checkable
    class SourceSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid: ...
        @property
        def source_date_epoch(self) -> t.NonNegativeInt: ...

    @runtime_checkable
    class BuildPolicy(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def build_constraints_path(self) -> t.Infra.ReleaseAbsolutePath: ...
        @property
        def build_constraints_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...
        @property
        def gitleaks_policy_path(self) -> t.Infra.ReleaseAbsolutePath: ...
        @property
        def gitleaks_policy_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

    @runtime_checkable
    class BuildArtifact(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath: ...
        @property
        def kind(self) -> t.Infra.ReleaseArtifactKind: ...
        @property
        def sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

    @runtime_checkable
    class ArtifactExpectation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr: ...
        @property
        def version(self) -> t.NonEmptyStr: ...
        @property
        def license_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...
        @property
        def allowed_roots(self) -> t.StrTuple: ...
        @property
        def versions(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class BuildRecord(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath: ...
        @property
        def exit_code(self) -> t.StrictInt: ...
        @property
        def log(self) -> t.Infra.ReleaseAbsolutePath: ...
        @property
        def artifacts(self) -> tuple[p.Infra.BuildArtifact, ...]: ...
        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid | None: ...
        @property
        def source_date_epoch(self) -> t.NonNegativeInt | None: ...
        @property
        def source_license_sha256(self) -> t.Infra.ReleaseArtifactSha256 | None: ...

    @runtime_checkable
    class ReleasePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def current(self) -> t.NonEmptyStr: ...
        @property
        def next(self) -> t.NonEmptyStr: ...
        @property
        def bump(self) -> c.Infra.VersionBump: ...
        @property
        def previous_tag(self) -> t.NonEmptyStr | None: ...
        @property
        def merges(self) -> tuple[str, ...]: ...
        @property
        def declared(self) -> bool: ...
        @property
        def tag(self) -> str: ...
        @property
        def releasable(self) -> bool: ...

    @runtime_checkable
    class BuildReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> t.NonEmptyStr: ...
        @property
        def total(self) -> t.NonNegativeInt: ...
        @property
        def failures(self) -> t.NonNegativeInt: ...
        @property
        def records(self) -> tuple[p.Infra.BuildRecord, ...]: ...
        @property
        def dry_run(self) -> bool: ...
        @property
        def build_constraints_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...
        @property
        def gitleaks_policy_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

    @runtime_checkable
    class ReleasePhaseDispatchConfig(Protocol):
        """Structural data contract projected from the owning model."""

        version: str
        tag: str
        repository_root: Path
        project_names: Sequence[str]
        dry_run: bool
        phase: c.Infra.ReleasePhase
        index: bool
        pr_title: str


__all__: list[str] = [
    "FlextInfraProtocolsRelease",
]
