"""Typed contracts for isolated worktree command transactions.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m
from flext_infra import t


class FlextInfraModelsWorktree:
    """Declaration-only models for transactional fix and codegen execution."""

    class LintSnapshot(m.ContractModel):
        """Captured diagnostics from one lint tool invocation."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        tool: Annotated[t.NonEmptyStr, m.Field(description="Canonical tool name")]
        exit_code: Annotated[int, m.Field(description="Tool process exit code")]
        errors: Annotated[
            t.NonNegativeInt, m.Field(description="Detected error count")
        ] = 0
        warnings: Annotated[
            t.NonNegativeInt, m.Field(description="Detected warning count")
        ] = 0
        output: Annotated[str, m.Field(description="Combined captured tool output")] = (
            ""
        )

    class RepositoryDelta(m.ContractModel):
        """Operation-only patch for one repository in a workspace transaction."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        relative_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository path relative to the workspace root"),
        ]
        source_root: Annotated[
            Path, m.Field(description="Original repository worktree root")
        ]
        worktree_root: Annotated[
            Path, m.Field(description="Temporary repository worktree root")
        ]
        checkpoint_sha: Annotated[
            t.NonEmptyStr, m.Field(description="Synthetic dirty-state checkpoint SHA")
        ]
        changed_files: Annotated[
            t.StrSequence, m.Field(description="Files changed by the isolated command")
        ] = ()
        # mro-wkii.17.26 (codex): keep Git patches byte-exact across validation.
        patch: Annotated[
            t.StrictBytes,
            m.Field(description="Binary Git patch relative to the checkpoint"),
        ] = b""

    class RepositoryWorktree(m.ContractModel):
        """One source repository paired with its isolated worktree checkpoint."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        relative_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository path relative to the workspace root"),
        ]
        source_root: Annotated[
            Path, m.Field(description="Original repository worktree root")
        ]
        worktree_root: Annotated[
            Path, m.Field(description="Temporary detached repository worktree root")
        ]
        checkpoint_sha: Annotated[
            t.NonEmptyStr, m.Field(description="Current isolated checkpoint SHA")
        ]

    class WorktreeTransactionRequest(m.ContractModel):
        """Validated request for one isolated command transaction."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        workspace_root: Annotated[
            Path, m.Field(description="Canonical source workspace root")
        ]
        command: Annotated[
            t.StrSequence, m.Field(description="Command arguments after the CLI group")
        ]
        # NOTE (multi-agent): an empty scope preserves explicit workspace-wide runs;
        # selected commands carry repository paths through every transaction phase.
        selected_repositories: Annotated[
            t.StrSequence,
            m.Field(description="Repositories selected relative to the workspace root"),
        ] = ()
        apply_patch: Annotated[
            bool, m.Field(description="Apply a validated operation patch to source")
        ] = False
        timeout_seconds: Annotated[
            t.PositiveInt, m.Field(description="Command and lint timeout in seconds")
        ]

    class WorktreeTransactionReport(m.ArbitraryTypesModel):
        """Complete evidence for one isolated worktree transaction."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        transaction_id: Annotated[
            t.NonEmptyStr, m.Field(description="Unique transaction identifier")
        ]
        command: Annotated[
            t.StrSequence, m.Field(description="Command executed inside the worktree")
        ]
        worktree_root: Annotated[
            Path, m.Field(description="Temporary root removed after evidence capture")
        ]
        command_output: Annotated[
            m.Cli.CommandOutput, m.Field(description="Isolated command process output")
        ]
        import_probe: Annotated[
            m.Cli.CommandOutput,
            m.Field(description="Fresh public-package import probe output"),
        ]
        lint_before: Annotated[
            t.VariadicTuple[FlextInfraModelsWorktree.LintSnapshot],
            m.Field(description="Lint diagnostics at the dirty checkpoint"),
        ] = ()
        lint_after: Annotated[
            t.VariadicTuple[FlextInfraModelsWorktree.LintSnapshot],
            m.Field(description="Lint diagnostics after isolated execution"),
        ] = ()
        repositories: Annotated[
            t.VariadicTuple[FlextInfraModelsWorktree.RepositoryDelta],
            m.Field(description="Per-repository operation patches"),
        ] = ()
        breakage_detected: Annotated[
            bool, m.Field(description="Whether execution introduced breakage")
        ] = False
        applied: Annotated[
            bool, m.Field(description="Whether every checked patch was applied")
        ] = False
        summary: Annotated[
            t.NonEmptyStr, m.Field(description="Human-readable transaction outcome")
        ]


__all__: list[str] = ["FlextInfraModelsWorktree"]
