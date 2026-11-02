# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/git
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import t
from flext_infra._protocols._git.identity import FlextInfraProtocolsGitIdentity
from flext_infra._protocols._git.worktree_facts import (
    FlextInfraProtocolsGitWorktreeFacts,
)
from flext_infra._protocols._git.worktree_state import (
    FlextInfraProtocolsGitWorktreeState,
)
from flext_infra._protocols.git_lane_ownership import (
    FlextInfraProtocolsGitLaneOwnership,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsGit(
    FlextInfraProtocolsGitLaneOwnership,
    FlextInfraProtocolsGitIdentity,
    FlextInfraProtocolsGitWorktreeFacts,
    FlextInfraProtocolsGitWorktreeState,
):
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitRepoRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...

    @runtime_checkable
    class GitSigningConfigObservation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr: ...
        @property
        def scope(self) -> str | None: ...
        @property
        def origin(self) -> str | None: ...
        @property
        def value(self) -> str | None: ...
        @property
        def process(self) -> p.Cli.ProcessOutcome: ...

    @runtime_checkable
    class GitSigningIdentityReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def signing_format(self) -> str | None: ...
        @property
        def key_path(self) -> Path | None: ...
        @property
        def inline_public_key(self) -> bool: ...
        @property
        def public_fingerprint(self) -> str | None: ...
        @property
        def allowed_signers_path(self) -> Path | None: ...
        @property
        def observations(self) -> tuple[p.Infra.GitSigningConfigObservation, ...]: ...

    @runtime_checkable
    class GitLaneEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def captured_at(self) -> t.AwareDatetime: ...
        @property
        def pull_requests(self) -> tuple[p.Infra.GitLanePullRequest, ...] | None: ...
        @property
        def beads(self) -> tuple[p.Infra.GitLaneBead, ...] | None: ...

    @runtime_checkable
    class GitLaneReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def integration_branch(self) -> str: ...
        @property
        def integration_oid(self) -> str: ...
        @property
        def inventory(self) -> tuple[str, ...]: ...
        @property
        def findings(self) -> tuple[str, ...]: ...
        @property
        def violations(self) -> tuple[p.Infra.GitLaneViolation, ...]: ...

    @runtime_checkable
    class GitLaneFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def stash_oids(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def refs(self) -> tuple[p.Infra.GitLaneRef, ...]: ...
        @property
        def read_errors(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class GitStatusRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...

    @runtime_checkable
    class GitStatusReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def porcelain(self) -> str: ...
        @property
        def dirty(self) -> bool: ...

    @runtime_checkable
    class GitPrimaryRootReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def primary_root(self) -> Path: ...

    @runtime_checkable
    class GitRootReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...

    @runtime_checkable
    class GitOidReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oid(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitTextReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def text(self) -> str: ...

    @runtime_checkable
    class GitBytesReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def payload(self) -> bytes: ...

    @runtime_checkable
    class GitBoolReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def value(self) -> bool: ...

    @runtime_checkable
    class GitWorktreeEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def head(self) -> t.NonEmptyStr | None: ...
        @property
        def branch(self) -> t.NonEmptyStr | None: ...
        @property
        def detached(self) -> bool: ...
        @property
        def bare(self) -> bool: ...
        @property
        def locked(self) -> bool: ...

    @runtime_checkable
    class GitWorktreeListReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path: ...
        @property
        def entries(self) -> tuple[p.Infra.GitWorktreeEntry, ...]: ...
        @property
        def porcelain(self) -> str: ...

    @runtime_checkable
    class GitBranchRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRefRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def reference(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitCommitishRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def commitish(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitAncestryRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def ancestor(self) -> t.NonEmptyStr: ...
        @property
        def descendant(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitPathPairRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def source(self) -> t.NonEmptyStr: ...
        @property
        def target(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRelativePathRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def relative_path(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitDeleteRefRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def reference(self) -> t.NonEmptyStr: ...
        @property
        def expected_oid(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitPushRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def source(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRemoteRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRemoteBranchRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def expected_oid(self) -> t.NonEmptyStr | None: ...

    @runtime_checkable
    class GitLaneOwnershipRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...
        @property
        def checkpoint_ref(self) -> t.NonEmptyStr: ...
        @property
        def expected_tip(self) -> t.NonEmptyStr | None: ...

    @runtime_checkable
    class GitLaneVerificationRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...
        @property
        def declared(self) -> str | None: ...
        @property
        def evidence_file(self) -> Path | None: ...
        @property
        def governance_file(self) -> Path | None: ...
        @property
        def read_pull_requests(self) -> bool: ...
        @property
        def read_beads(self) -> bool: ...
        @property
        def operation(self) -> Literal["verify", "create", "retire"]: ...
        @property
        def candidate(self) -> t.NonEmptyStr: ...
        @property
        def expected_tip(self) -> t.NonEmptyStr | None: ...
        @property
        def ownership(self) -> p.Infra.GitLaneOwnershipReceipt | None: ...

    @runtime_checkable
    class GitRefHeadsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def namespace(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRefHeadsReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def heads(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class GitOidListReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oids(self) -> Sequence[str]: ...

    @runtime_checkable
    class GitBranchCreateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def start(self) -> t.NonEmptyStr: ...
        @property
        def switch(self) -> bool: ...

    @runtime_checkable
    class GitStashDropRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def oid(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitMergeProbeRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def base(self) -> t.NonEmptyStr: ...
        @property
        def commitish(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitTimestampReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def epoch_seconds(self) -> t.NonNegativeInt: ...

    @runtime_checkable
    class GitWorktreeAddRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def lane(self) -> Path: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def base(self) -> t.NonEmptyStr: ...
        @property
        def track_remote(self) -> bool: ...
        @property
        def local_branch_exists(self) -> bool: ...

    @runtime_checkable
    class GitNumstatReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def subject(self) -> str: ...
        @property
        def numstat(self) -> str: ...

    @runtime_checkable
    class GitFingerprintInputsReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paths_z(self) -> bytes: ...
        @property
        def index_z(self) -> bytes: ...
        @property
        def head(self) -> bytes: ...

    @runtime_checkable
    class GitUpdateIndexGitlinkRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def oid(self) -> t.NonEmptyStr: ...
        @property
        def relative_path(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitPathsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def paths(self) -> Sequence[t.NonEmptyStr]: ...

    @runtime_checkable
    class GitCommitRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def message(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitRemoteUrlRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitSubmoduleContractRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def member_path(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitLaneRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def base(self) -> t.NonEmptyStr: ...
        @property
        def subject(self) -> t.NonEmptyStr: ...
        @property
        def body_file(self) -> Path: ...
        @property
        def ownership(self) -> p.Infra.GitLaneOwnershipReceipt | None: ...

    @runtime_checkable
    class GitIndexScope(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def index_file(self) -> Path: ...

    @runtime_checkable
    class GitCheckoutPathsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def paths(self) -> Sequence[t.NonEmptyStr]: ...


__all__: list[str] = [
    "FlextInfraProtocolsGit",
]
