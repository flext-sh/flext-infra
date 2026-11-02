# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraProtocolsGit:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class GitRepoRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path

    @runtime_checkable
    class GitSigningConfigObservation(Protocol):
        """Structural data contract projected from the owning model."""

        key: t.NonEmptyStr
        scope: str | None
        origin: str | None
        value: str | None = ...
        process: p.Cli.ProcessOutcome

    @runtime_checkable
    class GitSigningIdentityReport(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        signing_format: str | None
        key_path: Path | None
        inline_public_key: bool
        public_fingerprint: str | None
        allowed_signers_path: Path | None
        observations: tuple[FlextInfraProtocolsGit.GitSigningConfigObservation, ...]

    @runtime_checkable
    class GitLaneEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        captured_at: t.AwareDatetime
        pull_requests: tuple[p.Infra.GitLanePullRequest, ...] | None = ...
        beads: tuple[p.Infra.GitLaneBead, ...] | None = ...

    @runtime_checkable
    class GitLaneReport(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        integration_branch: str = ...
        integration_oid: str = ...
        inventory: tuple[str, ...] = ...
        findings: tuple[str, ...] = ...
        violations: tuple[p.Infra.GitLaneViolation, ...] = ...

    @runtime_checkable
    class GitLaneFacts(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        stash_oids: tuple[t.NonEmptyStr, ...] = ...
        refs: tuple[p.Infra.GitLaneRef, ...] = ...
        read_errors: tuple[str, ...] = ...

    @runtime_checkable
    class GitStatusRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path

    @runtime_checkable
    class GitStatusReport(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        porcelain: Annotated[str, t.StringConstraints(strip_whitespace=False)]
        dirty: bool

    @runtime_checkable
    class GitPrimaryRootReport(Protocol):
        """Structural data contract projected from the owning model."""

        primary_root: Path

    @runtime_checkable
    class GitRootReport(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path

    @runtime_checkable
    class GitOidReport(Protocol):
        """Structural data contract projected from the owning model."""

        oid: t.NonEmptyStr

    @runtime_checkable
    class GitTextReport(Protocol):
        """Structural data contract projected from the owning model."""

        text: str

    @runtime_checkable
    class GitBytesReport(Protocol):
        """Structural data contract projected from the owning model."""

        payload: bytes

    @runtime_checkable
    class GitBoolReport(Protocol):
        """Structural data contract projected from the owning model."""

        value: bool

    @runtime_checkable
    class GitWorktreeEntry(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        head: t.NonEmptyStr | None = ...
        branch: t.NonEmptyStr | None = ...
        detached: bool = ...
        bare: bool = ...
        locked: bool = ...

    @runtime_checkable
    class GitWorktreeListReport(Protocol):
        """Structural data contract projected from the owning model."""

        root: Path
        entries: tuple[FlextInfraProtocolsGit.GitWorktreeEntry, ...]
        porcelain: str

    @runtime_checkable
    class GitBranchRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        branch: t.NonEmptyStr

    @runtime_checkable
    class GitRefRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        reference: t.NonEmptyStr

    @runtime_checkable
    class GitCommitishRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        commitish: t.NonEmptyStr

    @runtime_checkable
    class GitAncestryRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        ancestor: t.NonEmptyStr
        descendant: t.NonEmptyStr = ...

    @runtime_checkable
    class GitPathPairRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        source: t.NonEmptyStr
        target: t.NonEmptyStr

    @runtime_checkable
    class GitRelativePathRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        relative_path: t.NonEmptyStr

    @runtime_checkable
    class GitDeleteRefRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        reference: t.NonEmptyStr
        expected_oid: t.NonEmptyStr

    @runtime_checkable
    class GitPushRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...
        branch: t.NonEmptyStr
        source: t.NonEmptyStr = ...

    @runtime_checkable
    class GitRemoteRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...

    @runtime_checkable
    class GitRemoteBranchRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...
        branch: t.NonEmptyStr
        expected_oid: t.NonEmptyStr | None = ...

    @runtime_checkable
    class GitLaneOwnershipRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...
        checkpoint_ref: t.NonEmptyStr
        expected_tip: t.NonEmptyStr | None = ...

    @runtime_checkable
    class GitLaneVerificationRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...
        declared: str | None = ...
        evidence_file: Path | None = ...
        governance_file: Path | None = ...
        read_pull_requests: bool = ...
        read_beads: bool = ...
        operation: Literal["verify", "create", "retire"] = ...
        candidate: t.NonEmptyStr = ...
        expected_tip: t.NonEmptyStr | None = ...
        ownership: p.Infra.GitLaneOwnershipReceipt | None = ...

    @runtime_checkable
    class GitRefHeadsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        namespace: t.NonEmptyStr

    @runtime_checkable
    class GitRefHeadsReport(Protocol):
        """Structural data contract projected from the owning model."""

        heads: Mapping[str, str]

    @runtime_checkable
    class GitOidListReport(Protocol):
        """Structural data contract projected from the owning model."""

        oids: Sequence[str]

    @runtime_checkable
    class GitBranchCreateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        branch: t.NonEmptyStr
        start: t.NonEmptyStr = ...
        switch: bool = ...

    @runtime_checkable
    class GitStashDropRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        oid: t.NonEmptyStr

    @runtime_checkable
    class GitMergeProbeRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        base: t.NonEmptyStr
        commitish: t.NonEmptyStr

    @runtime_checkable
    class GitTimestampReport(Protocol):
        """Structural data contract projected from the owning model."""

        epoch_seconds: t.NonNegativeInt

    @runtime_checkable
    class GitWorktreeAddRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        lane: Path
        branch: t.NonEmptyStr
        base: t.NonEmptyStr
        track_remote: bool = ...
        local_branch_exists: bool = ...

    @runtime_checkable
    class GitNumstatReport(Protocol):
        """Structural data contract projected from the owning model."""

        subject: str
        numstat: str

    @runtime_checkable
    class GitFingerprintInputsReport(Protocol):
        """Structural data contract projected from the owning model."""

        paths_z: bytes
        index_z: bytes
        head: bytes

    @runtime_checkable
    class GitUpdateIndexGitlinkRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        oid: t.NonEmptyStr
        relative_path: t.NonEmptyStr

    @runtime_checkable
    class GitPathsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        paths: Sequence[t.NonEmptyStr]

    @runtime_checkable
    class GitCommitRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        message: t.NonEmptyStr

    @runtime_checkable
    class GitRemoteUrlRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        remote: t.NonEmptyStr = ...

    @runtime_checkable
    class GitSubmoduleContractRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        member_path: t.NonEmptyStr

    @runtime_checkable
    class GitLaneRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        branch: t.NonEmptyStr
        base: t.NonEmptyStr
        subject: t.NonEmptyStr
        body_file: Path
        ownership: p.Infra.GitLaneOwnershipReceipt | None = ...

    @runtime_checkable
    class GitIndexScope(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path = ...
        index_file: Path = ...

    @runtime_checkable
    class GitCheckoutPathsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        paths: Sequence[t.NonEmptyStr] = ...


__all__: list[str] = [
    "FlextInfraProtocolsGit",
]
