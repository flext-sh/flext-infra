"""Typed common execution inputs for codegen services."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_core import s

from flext_infra import m, t


class FlextInfraCodegenExecutionBase[TResult: t.Cli.ResultValue](s[TResult]):
    """Own explicit repository execution state shared by codegen services."""

    repository_root: Annotated[
        Path,
        m.Field(default=Path(), description="Repository selected for codegen execution"),
    ] = Path()
    dry_run: Annotated[
        bool, m.Field(default=False, description="Whether the service may mutate files")
    ] = False
    check_only: Annotated[
        bool, m.Field(default=False, description="Whether the service validates only")
    ] = False
    apply_changes: Annotated[
        bool, m.Field(default=True, description="Whether the requested operation applies changes")
    ] = True
    project_filter: Annotated[
        str, m.Field(default="", description="Optional project selection filter")
    ] = ""

    @property
    def effective_dry_run(self) -> bool:
        """Return the one execution mode that forbids mutation."""
        return self.dry_run or self.check_only or not self.apply_changes


__all__: list[str] = ["FlextInfraCodegenExecutionBase"]
