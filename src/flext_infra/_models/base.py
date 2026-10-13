"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import c, m, t


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class ProcessExit(m.ContractModel):
        """Structured process outcome propagated through a Result failure."""

        exit_code: Annotated[
            int,
            m.Field(description="Exact subprocess return code without remapping"),
        ]
        classification: Annotated[
            t.NonEmptyStr,
            m.Field(description="Failure, timeout, or terminating signal"),
        ]

    class WorkspaceFingerprintEntry(m.ContractModel):
        """Content and index fingerprint for one repository-relative path."""

        path: Annotated[t.NonEmptyStr, m.Field(description="Repository-relative path")]
        digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 of path, index state, mode, and content"),
        ]

    class WorkspaceFingerprint(m.ContractModel):
        """Immutable repository snapshot used to validate one gate run."""

        digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="Aggregate SHA-256 for HEAD, index, and worktree"),
        ]
        entries: Annotated[
            t.VariadicTuple[FlextInfraModelsBase.WorkspaceFingerprintEntry],
            m.Field(description="Ordered per-path fingerprints"),
        ]

    class SummaryStats(m.ContractModel):
        """Bundled stats for summary output."""

        verb: str = m.Field(description="Verb label for the summary block")
        total: int = m.Field(description="Total processed items")
        success: int = m.Field(description="Successful items")
        failed: int = m.Field(description="Failed items")
        skipped: int = m.Field(description="Skipped items")
        elapsed: float = m.Field(description="Elapsed time in seconds")

    class ProtectedSourceWriteRequest(m.ContractModel):
        """Validated options for a single protected source write."""

        # Source content must retain its exact bytes (notably the mandatory
        # trailing newline every FLEXT module requires). ContractModel sets
        # str_strip_whitespace=True, which would corrupt written files, so the
        # canonical contract config is inherited with stripping disabled.
        model_config: ClassVar[m.ConfigDict] = {
            **m.ContractModel.model_config,
            "str_strip_whitespace": False,
        }

        workspace: Annotated[
            Path,
            m.Field(description="Repository root used for lint and pytest checks"),
        ]
        updated_source: Annotated[
            str,
            m.Field(description="Replacement source content to write"),
        ]
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None

    class ProtectedSourceWritesRequest(m.ArbitraryTypesModel):
        """Validated options for transactionally writing multiple sources."""

        workspace: Annotated[
            Path,
            m.Field(description="Repository root used for lint and pytest checks"),
        ]
        expected_sources: Annotated[
            t.MappingKV[Path, str | None],
            m.Field(
                description=(
                    "Expected current source bytes keyed by updated path; None "
                    "requires the path to be absent"
                ),
            ),
        ]
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None
        post_write: Annotated[
            Callable[[], None] | None,
            m.Field(description="Optional callback invoked after writes land"),
        ] = None
        skip_pytest: Annotated[
            bool,
            m.Field(description="Whether to bypass per-file pytest validation"),
        ] = False

    class ProtectedFileEditRequest(m.ArbitraryTypesModel):
        """Validated options for a protected single-file edit pipeline."""

        workspace: Annotated[
            Path,
            m.Field(description="Repository root used for lint and pytest checks"),
        ]
        before_source: Annotated[
            str,
            m.Field(description="Original source text used for validation evidence"),
        ]
        edit_fn: Annotated[
            Callable[[], None],
            m.Field(description="Callback that applies the file mutation"),
        ]
        gates: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional lint gate selection for validation"),
        ] = None

    class LintGateResult(m.ContractModel):
        """Validated result from one protected-edit lint gate."""

        tool_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical lint tool name"),
        ]
        errors: Annotated[
            t.StrSequence,
            m.Field(description="Diagnostic lines reported by the lint tool"),
        ] = m.Field(default_factory=tuple)
        output: Annotated[
            m.Cli.CommandOutput | None,
            m.Field(
                description="Original native streams, duration and process outcome"
            ),
        ] = None
        execution_error: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Execution or report failure, independent of findings"),
        ] = None
        error_code: Annotated[
            str | None,
            m.Field(
                description="Original Result failure code when no process launched"
            ),
        ] = None
        error_data: Annotated[
            t.JsonMapping | None,
            m.Field(description="Original Result failure metadata"),
        ] = None
        error_traceback: Annotated[
            str | None,
            m.Field(description="Original Result exception traceback when available"),
        ] = None

        @m.model_validator(mode="after")
        def _require_execution_evidence(self) -> Self:
            if self.output is None and self.execution_error is None:
                msg = "lint gate requires a native output or an execution failure"
                raise ValueError(msg)
            if self.output is not None and self.execution_error is None:
                outcome = self.output.outcome
                if (
                    outcome.timed_out
                    or outcome.forwarded_signal is not None
                    or (
                        outcome.raw_return_code != c.Cli.EXIT_CODE_SUCCESS
                        and not self.errors
                    )
                ):
                    msg = "unsuccessful lint execution requires its failure receipt"
                    raise ValueError(msg)
            return self

    class TransformStep(m.ContractModel):
        """Declarative step for enforcement pipeline."""

        detector: Annotated[str, m.Field(description="Detector rule_id to run")]
        transformer: Annotated[
            str,
            m.Field(description="Transformer class name to apply"),
        ]
        gates: Annotated[
            str,
            m.Field(
                description=(
                    "Comma-separated gate names for post-validation; empty selects"
                    " the SSOT snapshot gates (make.check_gates_ci)."
                ),
            ),
        ] = ""


__all__ = ["FlextInfraModelsBase"]
