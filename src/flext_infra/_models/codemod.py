"""Data-only contracts for the canonical AST-grep circuit."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_core import m
from flext_infra import t


class FlextInfraModelsCodemod:
    """Typed reports emitted by ``make mod``."""

    class ModGateSnapshot(m.ArbitraryTypesModel):
        """Exact Ruff and Pyrefly measurement with raw diagnostics."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        ruff_errors: Annotated[
            t.NonNegativeInt, m.Field(description="Ruff error count")
        ]
        pyrefly_errors: Annotated[
            t.NonNegativeInt, m.Field(description="Pyrefly error count")
        ]
        ruff_output: Annotated[
            str, m.Field(description="Complete Ruff machine output")
        ] = ""
        pyrefly_output: Annotated[
            str, m.Field(description="Complete Pyrefly machine output")
        ] = ""

    class ModScanReport(m.ArbitraryTypesModel):
        """Verified actionable AST-grep rewrite report."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        nodes: Annotated[t.NonNegativeInt, m.Field(description="Actionable node count")]
        files: Annotated[
            frozenset[Path], m.Field(description="Files containing actionable nodes")
        ]
        findings: Annotated[
            t.StrSequence,
            m.Field(description="Complete rule, file, line, and column diagnostics"),
        ]


__all__: list[str] = ["FlextInfraModelsCodemod"]
