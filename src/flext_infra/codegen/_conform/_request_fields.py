"""Conform request state fields shared across conformance facets."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from ... import m


class FlextInfraCodegenConformRequestFields:
    """Shared request-scoped state for conformance facets."""

    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    repository_root: Annotated[
        Path,
        m.Field(default=Path(), exclude=True, description="Conform repository root"),
    ] = Path()
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated scaffold specification included in the atomic plan",
        ),
    ] = None


__all__: list[str] = ["FlextInfraCodegenConformRequestFields"]
