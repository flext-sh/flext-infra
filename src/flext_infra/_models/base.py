"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m
from flext_infra import t


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class ProcessExit(m.ContractModel):
        """Structured process outcome propagated through a Result failure."""

        exit_code: Annotated[
            int, m.Field(ge=0, le=255, description="Process-compatible exit code")
        ]
        raw_exit_code: Annotated[
            int, m.Field(description="Raw subprocess return code before signal mapping")
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
            tuple[FlextInfraModelsBase.WorkspaceFingerprintEntry, ...],
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

        workspace: Annotated[Path, m.Field(description="Transactional write root")]
        updated_source: Annotated[
            str, m.Field(description="Replacement source content to write")
        ]
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve a .bak copy before editing")
        ] = False

    class ProtectedSourceWritesRequest(m.ArbitraryTypesModel):
        """Validated options for transactionally writing multiple sources."""

        workspace: Annotated[Path, m.Field(description="Transactional write root")]
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve .bak copies before editing")
        ] = False
        post_write: Annotated[
            Callable[[], None] | None,
            m.Field(description="Optional callback invoked after writes land"),
        ] = None

    class ProtectedFileEditRequest(m.ArbitraryTypesModel):
        """Validated options for a protected single-file edit pipeline."""

        workspace: Annotated[Path, m.Field(description="Transactional write root")]
        edit_fn: Annotated[
            Callable[[], None],
            m.Field(description="Callback that applies the file mutation"),
        ]
        restore_fn: Annotated[
            Callable[[], None],
            m.Field(description="Callback that restores the original file"),
        ]
        keep_backup: Annotated[
            bool, m.Field(description="Whether to preserve a .bak copy before editing")
        ] = False

    class TransformStep(m.ContractModel):
        """Declarative step for enforcement pipeline."""

        detector: Annotated[str, m.Field(description="Detector rule_id to run")]
        transformer: Annotated[
            str, m.Field(description="Transformer class name to apply")
        ]
        gates: Annotated[
            str, m.Field(description="Comma-separated gate names for post-validation")
        ] = ""
