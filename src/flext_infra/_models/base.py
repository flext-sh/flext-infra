"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from flext_cli import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class SummaryStats(m.ContractModel):
        """Bundled stats for summary output."""

        verb: str = m.Field(description="Verb label for the summary block")
        total: int = m.Field(description="Total processed items")
        success: int = m.Field(description="Successful items")
        failed: int = m.Field(description="Failed items")
        skipped: int = m.Field(description="Skipped items")
        elapsed: float = m.Field(description="Elapsed time in seconds")

    class ProjectFailureInfo(mm.ProjectNameMixin, m.ContractModel):
        """Bundled info for project failure output."""

        elapsed: Annotated[float, m.Field(description="Elapsed time in seconds")]
        log_path: Annotated[Path, m.Field(description="Path to the project log")]
        error_count: Annotated[int, m.Field(description="Total project errors")]
        errors: Annotated[
            t.StrSequence, m.Field(description="Rendered error excerpt lines")
        ]
        max_show: Annotated[int, m.Field(description="Maximum errors to render")] = 3

    class SafeExecutionResult(m.ContractModel):
        """Result of a safe execution pipeline run."""

        mode: Annotated[
            c.Infra.ExecutionMode, m.Field(description="Execution mode used")
        ]
        files_backed_up: Annotated[
            t.StrSequence,
            m.Field(description="Paths of files backed up before transform"),
        ]
        gate_results: Annotated[
            t.StrSequence, m.Field(description="Gate validation outcome summaries")
        ]
        rolled_back: Annotated[
            bool, m.Field(description="Whether rollback was performed")
        ]

    class ProtectedSourceWriteRequest(m.ContractModel):
        """Validated options for a single protected source write."""

        workspace: Annotated[
            Path, m.Field(description="Workspace root used for lint and pytest checks")
        ]
        updated_source: Annotated[
            str, m.Field(description="Replacement source content to write")
        ]
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve a .bak copy before editing")
        ] = False
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None

    class ProtectedSourceWritesRequest(m.ArbitraryTypesModel):
        """Validated options for transactionally writing multiple sources."""

        workspace: Annotated[
            Path, m.Field(description="Workspace root used for lint and pytest checks")
        ]
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve .bak copies before editing")
        ] = False
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None
        post_write: Annotated[
            Callable[[], None] | None,
            m.Field(description="Optional callback invoked after writes land"),
        ] = None
        skip_pytest: Annotated[
            bool, m.Field(description="Whether to bypass per-file pytest validation")
        ] = False

    class ProtectedFileEditRequest(m.ArbitraryTypesModel):
        """Validated options for a protected single-file edit pipeline."""

        workspace: Annotated[
            Path, m.Field(description="Workspace root used for lint and pytest checks")
        ]
        before_source: Annotated[
            str, m.Field(description="Original source text used for diff and restore")
        ]
        edit_fn: Annotated[
            Callable[[], None],
            m.Field(description="Callback that applies the file mutation"),
        ]
        restore_fn: Annotated[
            Callable[[], None] | None,
            m.Field(description="Optional callback that restores the original file"),
        ] = None
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve a .bak copy before editing")
        ] = False
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None

    class LintGateResult(m.ContractModel):
        """Validated result from one protected-edit lint gate."""

        tool_name: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical lint tool name")
        ]
        errors: Annotated[
            t.StrSequence, m.Field(description="Error lines reported by the lint tool")
        ] = m.Field(default_factory=tuple)

    class TransformStep(m.ContractModel):
        """Declarative step for enforcement pipeline."""

        detector: Annotated[str, m.Field(description="Detector rule_id to run")]
        transformer: Annotated[
            str, m.Field(description="Transformer class name to apply")
        ]
        gates: Annotated[
            str, m.Field(description="Comma-separated gate names for post-validation")
        ] = c.Infra.SAFE_EXECUTION_DEFAULT_GATES
