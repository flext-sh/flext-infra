"""Structural contracts for release models.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsRelease(Protocol):
    """Protocol-of-model contracts for release management."""

    @runtime_checkable
    class BuildArtifact(Protocol):
        """Immutable artifact emitted by one release build."""

        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath: ...

        @property
        def kind(self) -> t.Infra.ReleaseArtifactKind: ...

        @property
        def sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

    @runtime_checkable
    class BuildPolicy(Protocol):
        """Immutable policy snapshot used by every build in one report."""

        @property
        def build_constraints_path(self) -> t.Infra.ReleaseAbsolutePath: ...

        @property
        def build_constraints_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

        @property
        def gitleaks_policy_path(self) -> t.Infra.ReleaseAbsolutePath: ...

        @property
        def gitleaks_policy_sha256(self) -> t.Infra.ReleaseArtifactSha256: ...

    @runtime_checkable
    class BuildRecord(Protocol):
        """Build result data with complete source provenance."""

        @property
        def project(self) -> t.NonEmptyStr: ...

        @property
        def path(self) -> t.Infra.ReleaseAbsolutePath: ...

        @property
        def exit_code(self) -> t.StrictInt: ...

        @property
        def log(self) -> t.Infra.ReleaseAbsolutePath: ...

        @property
        def artifacts(
            self,
        ) -> t.VariadicTuple[FlextInfraProtocolsRelease.BuildArtifact]: ...

        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid | None: ...

        @property
        def source_date_epoch(self) -> t.NonNegativeInt | None: ...

        @property
        def source_license_sha256(
            self,
        ) -> t.Infra.ReleaseArtifactSha256 | None: ...

    @runtime_checkable
    class ReleaseOrchestratorConfig(Protocol):
        """Configuration for release workflow execution."""

        @property
        def project_names(self) -> t.StrSequence | None: ...

        @property
        def workspace_root(self) -> Path: ...

        @property
        def version(self) -> str: ...

        @property
        def tag(self) -> str: ...

        @property
        def push(self) -> bool: ...

        @property
        def dev_suffix(self) -> bool: ...

        @property
        def dry_run(self) -> bool: ...

        @property
        def phases(self) -> t.StrSequence: ...

        @property
        def create_branches(self) -> bool: ...

        @property
        def next_dev(self) -> bool: ...

        @property
        def next_bump(self) -> str: ...

    @runtime_checkable
    class ReleasePhaseDispatchConfig(Protocol):
        """Configuration for single release phase dispatch."""

        @property
        def project_names(self) -> t.StrSequence: ...

        @property
        def workspace_root(self) -> Path: ...

        @property
        def version(self) -> str: ...

        @property
        def tag(self) -> str: ...

        @property
        def push(self) -> bool: ...

        @property
        def dev_suffix(self) -> bool: ...

        @property
        def dry_run(self) -> bool: ...

        @property
        def phase(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class ReleaseSpec(Protocol):
        """Release descriptor with version, tag, and bump metadata."""

        @property
        def version(self) -> str: ...

        @property
        def tag(self) -> str: ...

        @property
        def bump_type(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class SourceSnapshot(Protocol):
        """Immutable committed source identity used by one project build."""

        @property
        def commit_oid(self) -> t.Infra.ReleaseCommitOid: ...

        @property
        def source_date_epoch(self) -> t.NonNegativeInt: ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsRelease",)
