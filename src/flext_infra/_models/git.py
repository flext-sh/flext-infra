"""Typed Git request/report contracts for flext-infra public Git API."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m
from flext_infra import t


class FlextInfraModelsGit:
    """Declaration-only models for Git facade and FlextInfraGitService."""

    class GitCaptureRequest(m.ContractModel):
        """One git capture invocation (stdout text on success)."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        repo_root: Annotated[Path, m.Field(description="Repository worktree root")]
        arguments: Annotated[
            t.StrSequence, m.Field(description="Git argv after the binary name")
        ]

    class GitStatusReport(m.ContractModel):
        """Porcelain status snapshot for one repository."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        repo_root: Annotated[Path, m.Field(description="Repository worktree root")]
        porcelain: Annotated[
            str, m.Field(description="Raw git status --porcelain output")
        ]
        dirty: Annotated[bool, m.Field(description="Whether the worktree is dirty")]

    class GitPrimaryRootReport(m.ContractModel):
        """Resolved primary worktree root."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        primary_root: Annotated[
            Path, m.Field(description="Canonical primary worktree root")
        ]

    class GitOperationReport(m.ContractModel):
        """Human-readable outcome for FlextInfraGitService.execute."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        summary: Annotated[t.NonEmptyStr, m.Field(description="Outcome summary")]
        primary_root: Annotated[
            Path | None, m.Field(description="Primary root when resolved")
        ] = None
        porcelain: Annotated[
            str | None, m.Field(description="Status porcelain when requested")
        ] = None


__all__: list[str] = ["FlextInfraModelsGit"]
