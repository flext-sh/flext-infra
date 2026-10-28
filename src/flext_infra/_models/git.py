"""Typed Git request/report contracts for flext-infra public Git API.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models import (
    FlextInfraModelsGitLaneInputs,
    FlextInfraModelsGitLaneOwnership,
)
from flext_infra._models._git import (
    FlextInfraModelsGitIdentity,
    FlextInfraModelsGitWorktreeFacts,
    FlextInfraModelsGitWorktreeState,
)


class FlextInfraModelsGit(
    FlextInfraModelsGitLaneOwnership,
    FlextInfraModelsGitIdentity,
    FlextInfraModelsGitWorktreeFacts,
    FlextInfraModelsGitWorktreeState,
):
    """Declaration-only models for Git facade and FlextInfraGitService.

    Composed via FLEXT with FlextInfraModelsGitIdentity (GitIdentityReport).
    """

    class GitRepoRequest(m.ContractModel):
        """One repository path for a monomorphic Git query."""

        repo_root: Annotated[Path, m.Field(description="Repository worktree root")]

    class GitSigningConfigObservation(m.ContractModel):
        """Native configuration origin and outcome without exporting key material."""

        key: Annotated[
            t.NonEmptyStr, m.Field(description="Inspected native Git setting")
        ]
        scope: Annotated[
            str | None, m.Field(description="Native effective config scope")
        ]
        origin: Annotated[
            str | None, m.Field(description="Native effective config origin")
        ]
        value: Annotated[
            str | None,
            m.Field(
                exclude=True, description="Private native config value for projection"
            ),
        ] = None
        process: Annotated[
            m.Cli.ProcessOutcome, m.Field(description="Original native query outcome")
        ]

    class GitSigningIdentityReport(m.ContractModel):
        """Read-only signing references; no private files or command execution."""

        repo_root: Annotated[Path, m.Field(description="Inspected repository root")]
        signing_format: Annotated[
            str | None, m.Field(description="Declared native signing format")
        ]
        key_path: Annotated[
            Path | None, m.Field(description="Declared file key reference, unread")
        ]
        inline_public_key: Annotated[
            bool,
            m.Field(description="Git literal public reference: key:: or raw ssh-"),
        ]
        public_fingerprint: Annotated[
            str | None,
            m.Field(description="Verified public fingerprint, unknown until verified"),
        ]
        allowed_signers_path: Annotated[
            Path | None, m.Field(description="Declared public trust file, unread")
        ]
        observations: Annotated[
            tuple[FlextInfraModelsGit.GitSigningConfigObservation, ...],
            m.Field(
                description="Native origin, scope and raw outcome for every setting"
            ),
        ]

    class GitLaneEvidence(m.ContractModel):
        """Repository-bound coordinator receipt, never a cleanup instruction."""

        repo_root: Annotated[Path, m.Field(description="Receipt repository identity")]
        captured_at: Annotated[
            t.AwareDatetime,
            m.Field(description="Receipt capture time"),
        ]
        pull_requests: Annotated[
            tuple[FlextInfraModelsGitLaneInputs.GitLanePullRequest, ...] | None,
            m.Field(description="Observed PRs; None means not selected/unknown"),
        ] = None
        beads: Annotated[
            tuple[FlextInfraModelsGitLaneOwnership.GitLaneBead, ...] | None,
            m.Field(description="Observed Beads; None means not selected/unknown"),
        ] = None

    class GitLaneReport(m.ContractModel):
        """Full read-only inventory and all refusals from one invocation."""

        repo_root: Annotated[Path, m.Field(description="Inspected repository")]
        integration_branch: Annotated[
            str,
            m.Field(description="Resolved integration branch"),
        ] = ""
        integration_oid: Annotated[
            str,
            m.Field(description="Proven live integration tip"),
        ] = ""
        inventory: Annotated[
            tuple[str, ...],
            m.Field(description="Full exact Git artifact inventory"),
        ] = ()
        findings: Annotated[
            tuple[str, ...],
            m.Field(description="All refusals and inconclusive evidence"),
        ] = ()
        violations: Annotated[
            tuple[FlextInfraModelsGitLaneInputs.GitLaneViolation, ...],
            m.Field(description="Classified violations from the single evaluator"),
        ] = ()

    class GitLaneFacts(m.ContractModel):
        """Native stash/ref observations; no base selection or classification."""

        repo_root: Annotated[Path, m.Field(description="Inspected Git repository")]
        stash_oids: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="All stash commit identities"),
        ] = ()
        refs: Annotated[
            tuple[FlextInfraModelsGitLaneInputs.GitLaneRef, ...],
            m.Field(description="All observed local and configured remote references"),
        ] = ()
        read_errors: Annotated[
            tuple[str, ...],
            m.Field(description="Exact first failures per native read"),
        ] = ()

    class GitStatusRequest(GitRepoRequest):
        """Request porcelain status for one repository."""

    class GitStatusReport(m.ContractModel):
        """Porcelain status snapshot for one repository."""

        repo_root: Annotated[Path, m.Field(description="Repository worktree root")]
        porcelain: Annotated[
            str,
            m.Field(description="Raw git status --porcelain output"),
        ]
        dirty: Annotated[bool, m.Field(description="Whether the worktree is dirty")]

    class GitPrimaryRootReport(m.ContractModel):
        """Resolved primary worktree root."""

        primary_root: Annotated[
            Path,
            m.Field(description="Canonical primary worktree root"),
        ]

    class GitRootReport(m.ContractModel):
        """Resolved workspace or superproject root."""

        repository_root: Annotated[
            Path,
            m.Field(description="Workspace or superproject root"),
        ]

    class GitOidReport(m.ContractModel):
        """Resolved Git object id."""

        oid: Annotated[t.NonEmptyStr, m.Field(description="Git object id (hex)")]

    class GitTextReport(m.ContractModel):
        """Captured Git stdout text for one semantic operation."""

        text: Annotated[str, m.Field(description="Captured stdout text")]

    class GitBytesReport(m.ContractModel):
        """Captured Git stdout bytes for one semantic operation."""

        payload: Annotated[bytes, m.Field(description="Captured stdout bytes")]

    class GitBoolReport(m.ContractModel):
        """Boolean outcome for one semantic Git predicate."""

        value: Annotated[bool, m.Field(description="Predicate result")]

    class GitWorktreeEntry(m.ContractModel):
        """One registered worktree checkout from Git's canonical registry."""

        path: Annotated[Path, m.Field(description="Registered worktree root")]
        head: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Checked-out commit oid; absent for a bare worktree"),
        ] = None
        branch: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Checked-out branch short name; absent when detached"),
        ] = None
        detached: Annotated[bool, m.Field(description="Whether HEAD is detached")] = (
            False
        )
        bare: Annotated[
            bool,
            m.Field(description="Whether this is the bare main worktree"),
        ] = False
        locked: Annotated[
            bool,
            m.Field(description="Whether the worktree is locked"),
        ] = False

    class GitWorktreeListReport(m.ContractModel):
        """Git's worktree registry, parsed once, plus its raw porcelain contract."""

        root: Annotated[
            Path,
            m.Field(description="Repository the registry was read for"),
        ]
        entries: Annotated[
            tuple[FlextInfraModelsGit.GitWorktreeEntry, ...],
            m.Field(description="Every registered worktree, primary first"),
        ]
        porcelain: Annotated[
            str,
            m.Field(description="Raw git worktree list --porcelain output"),
        ]

    class GitBranchRequest(GitRepoRequest):
        """Repository plus branch name for branch-scoped operations."""

        branch: Annotated[t.NonEmptyStr, m.Field(description="Branch name")]

    class GitRefRequest(GitRepoRequest):
        """Repository plus exact Git ref name."""

        reference: Annotated[t.NonEmptyStr, m.Field(description="Exact Git ref")]

    class GitCommitishRequest(GitRepoRequest):
        """Repository plus commit-ish for resolve/ancestor/merge ops."""

        commitish: Annotated[t.NonEmptyStr, m.Field(description="Commit-ish")]

    class GitAncestryRequest(GitRepoRequest):
        """Repository plus the ancestor and descendant an ancestry proof relates.

        ``descendant`` defaults to ``HEAD``, so the HEAD-bound proof every
        existing consumer relied on is the same single owner generalized to an
        arbitrary pair; there is no separate pair verb.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        ancestor: Annotated[t.NonEmptyStr, m.Field(description="Candidate ancestor")]
        descendant: Annotated[
            t.NonEmptyStr,
            m.Field(default="HEAD", description="Candidate descendant"),
        ] = "HEAD"

    class GitPathPairRequest(GitRepoRequest):
        """Repository plus source/target relative paths."""

        source: Annotated[t.NonEmptyStr, m.Field(description="Source path relative")]
        target: Annotated[t.NonEmptyStr, m.Field(description="Target path relative")]

    class GitRelativePathRequest(GitRepoRequest):
        """Repository plus one relative path."""

        relative_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Path relative to repo root"),
        ]

    class GitDeleteRefRequest(GitRepoRequest):
        """Delete a ref when it still points at an expected oid."""

        reference: Annotated[t.NonEmptyStr, m.Field(description="Exact Git ref")]
        expected_oid: Annotated[
            t.NonEmptyStr,
            m.Field(description="Expected tip oid for CAS delete"),
        ]

    class GitPushRequest(GitRepoRequest):
        """Push a local commit-ish (HEAD by default) to a remote branch ref."""

        remote: Annotated[t.NonEmptyStr, m.Field(description="Remote name")] = "origin"
        branch: Annotated[t.NonEmptyStr, m.Field(description="Branch to publish")]
        source: Annotated[
            t.NonEmptyStr,
            m.Field(description="Local commit-ish pushed to the remote branch"),
        ] = "HEAD"

    class GitRemoteRequest(GitRepoRequest):
        """One repository plus one remote name."""

        remote: Annotated[t.NonEmptyStr, m.Field(description="Remote name")] = "origin"

    class GitRemoteBranchRequest(GitRemoteRequest):
        """One remote branch, optionally bound to its expected tip oid."""

        branch: Annotated[t.NonEmptyStr, m.Field(description="Remote branch name")]
        expected_oid: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Remote tip the mutation is leased on"),
        ] = None

    class GitLaneOwnershipRequest(GitRemoteRequest):
        """Authenticate an existing retained checkpoint, without publishing state."""

        checkpoint_ref: Annotated[
            t.NonEmptyStr, m.Field(description="Existing dedicated checkpoint ref")
        ]
        expected_tip: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Previously observed integration tip, when selected"),
        ] = None

    class GitLaneVerificationRequest(GitRemoteRequest):
        """Read-only admission and census against the live integration tip."""

        declared: Annotated[
            str | None, m.Field(description="Governing integration declaration")
        ] = None
        evidence_file: Annotated[
            Path | None, m.Field(description="Coordinator ownership receipt")
        ] = None
        governance_file: Annotated[
            Path | None, m.Field(description="Coordination governance SSOT")
        ] = None
        read_pull_requests: Annotated[
            bool, m.Field(description="Authorize public PR ownership reads")
        ] = False
        read_beads: Annotated[
            bool, m.Field(description="Authorize declared Beads ownership reads")
        ] = False
        operation: Annotated[
            Literal["verify", "create", "retire"],
            m.Field(description="Boundary being verified, not an effect selector"),
        ] = "verify"
        candidate: Annotated[
            t.NonEmptyStr, m.Field(description="Commit requiring integration ancestry")
        ] = "HEAD"
        expected_tip: Annotated[
            t.NonEmptyStr | None, m.Field(description="Previously observed tip")
        ] = None
        ownership: Annotated[
            FlextInfraModelsGitWorktreeState.GitLaneOwnershipReceipt | None,
            m.Field(
                description="Required integrated preservation receipt for creation"
            ),
        ] = None

        @m.model_validator(mode="after")
        def _validate_ownership_selection(self) -> Self:
            """Reject competing receipt and live ownership evidence sources.

            Returns:
                The validated instance.

            Raises:
                ValueError: If an ownership receipt competes with authorized
                    live sources.

            """
            if self.evidence_file is not None and (
                self.read_pull_requests or self.read_beads
            ):
                msg = "select either an ownership receipt or authorized live sources"
                raise ValueError(msg)
            return self

    class GitRefHeadsRequest(GitRepoRequest):
        """List every ref below one namespace.

        Namespaces include ``refs/heads`` and ``refs/remotes/origin``.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        namespace: Annotated[t.NonEmptyStr, m.Field(description="Ref namespace")]

    class GitRefHeadsReport(m.ContractModel):
        """Short ref names below one namespace mapped to their tip oids."""

        heads: Annotated[
            Mapping[str, str],
            m.Field(description="Name relative to the namespace -> tip oid"),
        ]

    class GitOidListReport(m.ContractModel):
        """Ordered Git object ids."""

        oids: Annotated[Sequence[str], m.Field(description="Object ids in order")]

    class GitBranchCreateRequest(GitRepoRequest):
        """Create one branch at a start point, optionally switching to it."""

        branch: Annotated[t.NonEmptyStr, m.Field(description="New branch name")]
        start: Annotated[
            t.NonEmptyStr,
            m.Field(description="Commit-ish the branch starts at"),
        ] = "HEAD"
        switch: Annotated[
            bool,
            m.Field(description="Switch the worktree to it, carrying local changes"),
        ] = False

    class GitStashDropRequest(GitRepoRequest):
        """Drop the stash entry whose commit is exactly ``oid``."""

        oid: Annotated[t.NonEmptyStr, m.Field(description="Stash commit oid")]

    class GitMergeProbeRequest(GitRepoRequest):
        """Ask whether merging ``commitish`` into ``base`` would change nothing."""

        base: Annotated[t.NonEmptyStr, m.Field(description="Merge target commit-ish")]
        commitish: Annotated[t.NonEmptyStr, m.Field(description="Merged commit-ish")]

    class GitTimestampReport(m.ContractModel):
        """One Unix timestamp in seconds."""

        epoch_seconds: Annotated[
            t.NonNegativeInt,
            m.Field(description="Seconds since the Unix epoch"),
        ]

    class GitWorktreeAddRequest(m.ContractModel):
        """Add a development worktree lane."""

        repo_root: Annotated[Path, m.Field(description="Primary repository root")]
        lane: Annotated[Path, m.Field(description="Absolute lane worktree path")]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Lane branch name")]
        base: Annotated[
            t.NonEmptyStr,
            m.Field(description="Base commit-ish when creating branch"),
        ]
        track_remote: Annotated[
            bool,
            m.Field(description="Track origin/<branch> when creating"),
        ] = False
        local_branch_exists: Annotated[
            bool,
            m.Field(description="Whether refs/heads/<branch> already exists"),
        ] = False

    class GitNumstatReport(m.ContractModel):
        """HEAD commit subject plus parent..HEAD numstat text."""

        subject: Annotated[str, m.Field(description="HEAD commit subject")]
        numstat: Annotated[str, m.Field(description="git diff --numstat HEAD~1 HEAD")]

    class GitFingerprintInputsReport(m.ContractModel):
        """Byte-exact inputs for workspace fingerprinting."""

        paths_z: Annotated[
            bytes,
            m.Field(description="NUL-delimited ls-files path list"),
        ]
        index_z: Annotated[
            bytes,
            m.Field(description="NUL-delimited ls-files --stage list"),
        ]
        head: Annotated[bytes, m.Field(description="HEAD oid bytes or UNBORN")]

    class GitUpdateIndexGitlinkRequest(GitRepoRequest):
        """Stage one gitlink (mode 160000) into the index."""

        oid: Annotated[t.NonEmptyStr, m.Field(description="Gitlink commit oid")]
        relative_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Gitlink path relative to repo"),
        ]

    class GitPathsRequest(GitRepoRequest):
        """Repository plus multiple relative paths for add/restore operations."""

        paths: Annotated[
            Sequence[t.NonEmptyStr],
            m.Field(description="Relative paths to operate on"),
        ]

    class GitCommitRequest(GitRepoRequest):
        """Repository plus commit message for staging a commit."""

        message: Annotated[t.NonEmptyStr, m.Field(description="Commit message")]

    class GitRemoteUrlRequest(GitRepoRequest):
        """Repository plus optional remote name for URL resolution."""

        remote: Annotated[t.NonEmptyStr, m.Field(description="Remote name")] = "origin"

    class GitSubmoduleContractRequest(m.ContractModel):
        """Superproject plus one declared submodule path for contract reads."""

        repo_root: Annotated[Path, m.Field(description="Superproject worktree root")]
        member_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Submodule path relative to the superproject root"),
        ]

    class GitLaneRequest(GitRepoRequest):
        """One publication lane: ``branch`` carried from ``base`` to a pull request."""

        branch: Annotated[t.NonEmptyStr, m.Field(description="Lane branch")]
        base: Annotated[
            t.NonEmptyStr,
            m.Field(description="Integration branch the lane starts from and targets"),
        ]
        subject: Annotated[
            t.NonEmptyStr,
            m.Field(description="Commit subject and pull-request title"),
        ]
        body_file: Annotated[Path, m.Field(description="Pull-request body file")]
        ownership: Annotated[
            FlextInfraModelsGitWorktreeState.GitLaneOwnershipReceipt | None,
            m.Field(
                description="Live retained and integrated prior owned repository state"
            ),
        ] = None

    class GitIndexScope(m.ContractModel):
        """One explicitly selected native index in the current request only."""

        repo_root: Path = m.Field(description="Exact repository owning the scope")
        index_file: Path = m.Field(description="Git owner's isolated native index")

    class GitCheckoutPathsRequest(GitRepoRequest):
        """Repository plus optional paths for checkout/restore operations."""

        paths: Annotated[
            Sequence[t.NonEmptyStr],
            m.Field(description="Relative paths to restore; empty restores all"),
        ] = ()


__all__: list[str] = ["FlextInfraModelsGit"]
