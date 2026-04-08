"""Domain models for quality gate execution."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra import t


class FlextInfraModelsGates:
    """Quality gate execution domain models."""

    class GateContext(
        FlextModels.ContractModel,
    ):
        """Quality gate execution context and configuration."""

        fail_fast: Annotated[
            bool,
            Field(default=True, description="Stop on first failure"),
        ] = True
        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="forbid",
            arbitrary_types_allowed=True,
            populate_by_name=True,
        )
        workspace_root: Annotated[
            Path,
            Field(alias="workspace", description="Workspace root directory"),
        ]
        reports_dir: Annotated[Path, Field(description="Reports output directory")]
        apply_fixes: Annotated[
            bool,
            Field(description="Apply supported fixes before checking"),
        ] = False
        check_only: Annotated[
            bool,
            Field(
                description="Never write files even when fix mode is requested",
            ),
        ] = False
        ruff_args: Annotated[
            t.StrSequence,
            Field(description="Extra arguments for Ruff"),
        ] = ()
        pyright_args: Annotated[
            t.StrSequence,
            Field(description="Extra arguments for Pyright"),
        ] = ()


__all__ = ["FlextInfraModelsGates"]
