"""Domain models for quality gate execution."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_core import FlextModels
from pydantic import ConfigDict, Field


class FlextInfraGatesModels:
    """Quality gate execution domain models."""

    class GateContext(FlextModels.FrozenStrictModel):
        """Quality gate execution context and configuration."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="forbid",
            arbitrary_types_allowed=True,
        )
        workspace_root: Annotated[Path, Field(description="Workspace root directory")]
        reports_dir: Annotated[Path, Field(description="Reports output directory")]
        fail_fast: Annotated[
            bool,
            Field(default=False, description="Stop on first gate failure"),
        ] = False
        apply_fixes: Annotated[
            bool,
            Field(default=False, description="Apply supported fixes before checking"),
        ] = False
        check_only: Annotated[
            bool,
            Field(
                default=False,
                description="Never write files even when fix mode is requested",
            ),
        ] = False
        ruff_args: Annotated[
            Sequence[str],
            Field(default_factory=tuple, description="Extra arguments for Ruff"),
        ] = ()
        pyright_args: Annotated[
            Sequence[str],
            Field(default_factory=tuple, description="Extra arguments for Pyright"),
        ] = ()


__all__ = ["FlextInfraGatesModels"]
