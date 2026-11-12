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

from flext_cli import FlextCliProtocols

from flext_infra._protocols import (
    FlextInfraProtocolsGitLaneInputs,
    FlextInfraProtocolsGitLaneOwnership,
)
from flext_infra._protocols._git import (
    FlextInfraProtocolsGitIdentity,
    FlextInfraProtocolsGitWorktreeFacts,
    FlextInfraProtocolsGitWorktreeState,
)

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t


class FlextInfraProtocolsGit(
    FlextInfraProtocolsGitLaneOwnership,
    FlextInfraProtocolsGitLaneInputs,
    FlextInfraProtocolsGitIdentity,
    FlextInfraProtocolsGitWorktreeFacts,
    FlextInfraProtocolsGitWorktreeState,
):
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitRepoRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Repository worktree root."""
            ...

    @runtime_checkable
    class GitSigningConfigObservation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr:
            """Inspected native Git setting."""
            ...

        @property
        def scope(self) -> str | None:
            """Native effective config scope."""
            ...

        @property
        def origin(self) -> str | None:
            """Native effective config origin."""
            ...

        @property
        def value(self) -> str | None:
            """Private native config value for projection."""
            ...

        @property
        def process(self) -> p.Cli.ProcessOutcome:
            """Original native query outcome."""
            ...

    @runtime_checkable
    class GitSigningIdentityReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Inspected repository root."""
            ...

        @property
        def signing_format(self) -> str | None:
            """Declared native signing format."""
            ...

        @property
        def key_path(self) -> Path | None:
            """Declared file key reference, unread."""
            ...

        @property
        def inline_public_key(self) -> bool:
            """Git literal public reference: key:: or raw ssh-."""
            ...

        @property
        def public_fingerprint(self) -> str | None:
            """Verified public fingerprint, unknown until verified."""
            ...

        @property
        def allowed_signers_path(self) -> Path | None:
            """Declared public trust file, unread."""
            ...

        @property
        def observations(
            self,
        ) -> tuple[FlextInfraProtocolsGit.GitSigningConfigObservation, ...]:
            """Native origin, scope and raw outcome for every setting."""
            ...

    @runtime_checkable
    class GitLaneEvidence(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Receipt repository identity."""
            ...

        @property
        def captured_at(self) -> t.AwareDatetime:
            """Receipt capture time."""
            ...

        @property
        def pull_requests(
            self,
        ) -> tuple[FlextInfraProtocolsGitLaneInputs.GitLanePullRequest, ...] | None:
            """Observed PRs; None means not selected/unknown."""
            ...

        @property
        def beads(
            self,
        ) -> tuple[FlextInfraProtocolsGitLaneOwnership.GitLaneBead, ...] | None:
            """Observed Beads; None means not selected/unknown."""
            ...

    @runtime_checkable
    class GitLaneReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Inspected repository."""
            ...

        @property
        def integration_branch(self) -> str:
            """Resolved integration branch."""
            ...

        @property
        def integration_oid(self) -> str:
            """Proven live integration tip."""
            ...

        @property
        def inventory(self) -> tuple[str, ...]:
            """Full exact Git artifact inventory."""
            ...

        @property
        def findings(self) -> tuple[str, ...]:
            """All refusals and inconclusive evidence."""
            ...

        @property
        def violations(
            self,
        ) -> tuple[FlextInfraProtocolsGitLaneInputs.GitLaneViolation, ...]:
            """Classified violations from the single evaluator."""
            ...

    @runtime_checkable
    class GitLaneFacts(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Inspected Git repository."""
            ...

        @property
        def stash_oids(self) -> tuple[t.NonEmptyStr, ...]:
            """All stash commit identities."""
            ...

        @property
        def refs(self) -> tuple[FlextInfraProtocolsGitLaneInputs.GitLaneRef, ...]:
            """All observed local and configured remote references."""
            ...

        @property
        def read_errors(self) -> tuple[str, ...]:
            """Exact first failures per native read."""
            ...

    @runtime_checkable
    class GitStatusRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class GitStatusReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Repository worktree root."""
            ...

        @property
        def porcelain(self) -> str:
            """Raw git status --porcelain output."""
            ...

        @property
        def dirty(self) -> bool:
            """Whether the worktree is dirty."""
            ...

    @runtime_checkable
    class GitPrimaryRootReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def primary_root(self) -> Path:
            """Canonical primary worktree root."""
            ...

    @runtime_checkable
    class GitRootReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Workspace or superproject root."""
            ...

    @runtime_checkable
    class GitOidReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oid(self) -> t.NonEmptyStr:
            """Git object id (hex)."""
            ...

    @runtime_checkable
    class GitTextReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def text(self) -> str:
            """Captured stdout text."""
            ...

    @runtime_checkable
    class GitBytesReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def payload(self) -> bytes:
            """Captured stdout bytes."""
            ...

    @runtime_checkable
    class GitBoolReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def value(self) -> bool:
            """Predicate result."""
            ...

    @runtime_checkable
    class GitWorktreeEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Registered worktree root."""
            ...

        @property
        def head(self) -> t.NonEmptyStr | None:
            """Checked-out commit oid; absent for a bare worktree."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr | None:
            """Checked-out branch short name; absent when detached."""
            ...

        @property
        def detached(self) -> bool:
            """Whether HEAD is detached."""
            ...

        @property
        def bare(self) -> bool:
            """Whether this is the bare main worktree."""
            ...

        @property
        def locked(self) -> bool:
            """Whether the worktree is locked."""
            ...

    @runtime_checkable
    class GitWorktreeListReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Repository the registry was read for."""
            ...

        @property
        def entries(self) -> tuple[FlextInfraProtocolsGit.GitWorktreeEntry, ...]:
            """Every registered worktree, primary first."""
            ...

        @property
        def porcelain(self) -> str:
            """Raw git worktree list --porcelain output."""
            ...

    @runtime_checkable
    class GitBranchRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> t.NonEmptyStr:
            """Branch name."""
            ...

    @runtime_checkable
    class GitRefRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def reference(self) -> t.NonEmptyStr:
            """Exact Git ref."""
            ...

    @runtime_checkable
    class GitCommitishRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def commitish(self) -> t.NonEmptyStr:
            """Commit-ish."""
            ...

    @runtime_checkable
    class GitAncestryRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def ancestor(self) -> t.NonEmptyStr:
            """Candidate ancestor."""
            ...

        @property
        def descendant(self) -> t.NonEmptyStr:
            """Candidate descendant."""
            ...

    @runtime_checkable
    class GitPathPairRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> t.NonEmptyStr:
            """Source path relative."""
            ...

        @property
        def target(self) -> t.NonEmptyStr:
            """Target path relative."""
            ...

    @runtime_checkable
    class GitRelativePathRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> t.NonEmptyStr:
            """Path relative to repo root."""
            ...

    @runtime_checkable
    class GitDeleteRefRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def reference(self) -> t.NonEmptyStr:
            """Exact Git ref."""
            ...

        @property
        def expected_oid(self) -> t.NonEmptyStr:
            """Expected tip oid for CAS delete."""
            ...

    @runtime_checkable
    class GitPushRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def remote(self) -> t.NonEmptyStr:
            """Remote name."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr:
            """Branch to publish."""
            ...

        @property
        def source(self) -> t.NonEmptyStr:
            """Local commit-ish pushed to the remote branch."""
            ...

    @runtime_checkable
    class GitRemoteRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def remote(self) -> t.NonEmptyStr:
            """Remote name."""
            ...

    @runtime_checkable
    class GitRemoteBranchRequest(GitRemoteRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> t.NonEmptyStr:
            """Remote branch name."""
            ...

        @property
        def expected_oid(self) -> t.NonEmptyStr | None:
            """Remote tip the mutation is leased on."""
            ...

    @runtime_checkable
    class GitLaneOwnershipRequest(GitRemoteRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checkpoint_ref(self) -> t.NonEmptyStr:
            """Existing dedicated checkpoint ref."""
            ...

        @property
        def expected_tip(self) -> t.NonEmptyStr | None:
            """Previously observed integration tip, when selected."""
            ...

    @runtime_checkable
    class GitLaneVerificationRequest(GitRemoteRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declared(self) -> str | None:
            """Governing integration declaration."""
            ...

        @property
        def evidence_file(self) -> Path | None:
            """Coordinator ownership receipt."""
            ...

        @property
        def governance_file(self) -> Path | None:
            """Coordination governance SSOT."""
            ...

        @property
        def read_pull_requests(self) -> bool:
            """Authorize public PR ownership reads."""
            ...

        @property
        def read_beads(self) -> bool:
            """Authorize declared Beads ownership reads."""
            ...

        @property
        def operation(self) -> Literal["verify", "create", "retire"]:
            """Boundary being verified, not an effect selector."""
            ...

        @property
        def candidate(self) -> t.NonEmptyStr:
            """Commit requiring integration ancestry."""
            ...

        @property
        def expected_tip(self) -> t.NonEmptyStr | None:
            """Previously observed tip."""
            ...

        @property
        def ownership(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitLaneOwnershipReceipt | None:
            """Required integrated preservation receipt for creation."""
            ...

    @runtime_checkable
    class GitRefHeadsRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def namespace(self) -> t.NonEmptyStr:
            """Ref namespace."""
            ...

    @runtime_checkable
    class GitRefHeadsReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def heads(self) -> Mapping[str, str]:
            """Name relative to the namespace -> tip oid."""
            ...

    @runtime_checkable
    class GitOidListReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oids(self) -> Sequence[str]:
            """Object ids in order."""
            ...

    @runtime_checkable
    class GitBranchCreateRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> t.NonEmptyStr:
            """New branch name."""
            ...

        @property
        def start(self) -> t.NonEmptyStr:
            """Commit-ish the branch starts at."""
            ...

        @property
        def switch(self) -> bool:
            """Switch the worktree to it, carrying local changes."""
            ...

    @runtime_checkable
    class GitStashDropRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oid(self) -> t.NonEmptyStr:
            """Stash commit oid."""
            ...

    @runtime_checkable
    class GitMergeProbeRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def base(self) -> t.NonEmptyStr:
            """Merge target commit-ish."""
            ...

        @property
        def commitish(self) -> t.NonEmptyStr:
            """Merged commit-ish."""
            ...

    @runtime_checkable
    class GitTimestampReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def epoch_seconds(self) -> t.NonNegativeInt:
            """Seconds since the Unix epoch."""
            ...

    @runtime_checkable
    class GitWorktreeAddRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Primary repository root."""
            ...

        @property
        def lane(self) -> Path:
            """Absolute lane worktree path."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr:
            """Lane branch name."""
            ...

        @property
        def base(self) -> t.NonEmptyStr:
            """Base commit-ish when creating branch."""
            ...

        @property
        def track_remote(self) -> bool:
            """Track origin/<branch> when creating."""
            ...

        @property
        def local_branch_exists(self) -> bool:
            """Whether refs/heads/<branch> already exists."""
            ...

    @runtime_checkable
    class GitNumstatReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def subject(self) -> str:
            """HEAD commit subject."""
            ...

        @property
        def numstat(self) -> str:
            """Git diff --numstat HEAD~1 HEAD."""
            ...

    @runtime_checkable
    class GitFingerprintInputsReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paths_z(self) -> bytes:
            """NUL-delimited ls-files path list."""
            ...

        @property
        def index_z(self) -> bytes:
            """NUL-delimited ls-files --stage list."""
            ...

        @property
        def head(self) -> bytes:
            """HEAD oid bytes or UNBORN."""
            ...

    @runtime_checkable
    class GitUpdateIndexGitlinkRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def oid(self) -> t.NonEmptyStr:
            """Gitlink commit oid."""
            ...

        @property
        def relative_path(self) -> t.NonEmptyStr:
            """Gitlink path relative to repo."""
            ...

    @runtime_checkable
    class GitPathsRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paths(self) -> Sequence[t.NonEmptyStr]:
            """Relative paths to operate on."""
            ...

    @runtime_checkable
    class GitCommitRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def message(self) -> t.NonEmptyStr:
            """Commit message."""
            ...

    @runtime_checkable
    class GitRemoteUrlRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def remote(self) -> t.NonEmptyStr:
            """Remote name."""
            ...

    @runtime_checkable
    class GitSubmoduleContractRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Superproject worktree root."""
            ...

        @property
        def member_path(self) -> t.NonEmptyStr:
            """Submodule path relative to the superproject root."""
            ...

    @runtime_checkable
    class GitLaneRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> t.NonEmptyStr:
            """Lane branch."""
            ...

        @property
        def base(self) -> t.NonEmptyStr:
            """Integration branch the lane starts from and targets."""
            ...

        @property
        def subject(self) -> t.NonEmptyStr:
            """Commit subject and pull-request title."""
            ...

        @property
        def body_file(self) -> Path:
            """Pull-request body file."""
            ...

    @runtime_checkable
    class GitIndexScope(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Exact repository owning the scope."""
            ...

        @property
        def index_file(self) -> Path:
            """Git owner's isolated native index."""
            ...

    @runtime_checkable
    class GitCheckoutPathsRequest(GitRepoRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paths(self) -> Sequence[t.NonEmptyStr]:
            """Relative paths to restore; empty restores all."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGit",
]
