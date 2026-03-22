"""Domain models for quality gate execution."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import FlextModels


class FlextInfraGatesModels:
    """Quality gate execution domain models."""

    class GateContext(FlextModels.FrozenStrictModel):
        """Quality gate execution context and configuration."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="forbid", arbitrary_types_allowed=True
        )
        workspace_root: Annotated[Path, Field(description="Workspace root directory")]
        reports_dir: Annotated[Path, Field(description="Reports output directory")]
        fail_fast: Annotated[
            bool,
            Field(default=False, description="Stop on first gate failure"),
        ] = False


__all__ = ["FlextInfraGatesModels"]
