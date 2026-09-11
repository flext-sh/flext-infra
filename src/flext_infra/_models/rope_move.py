"""Typed requests for Rope-backed class moves."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_core import m
from flext_infra import t

from .mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsRopeMove:
    """Data-only contracts for semantic class relocation."""

    class ClassMoveRequest(mm.PositiveLineMixin, m.ArbitraryTypesModel):
        """One exact, prevalidated Rope class-move request."""

        rope_project: Annotated[
            t.Infra.RopeProject,
            m.Field(description="Active Rope project that owns both files"),
        ]
        source_file: Annotated[
            Path, m.Field(description="Existing module that declares the class")
        ]
        target_file: Annotated[
            Path, m.Field(description="Canonical destination module for the class")
        ]
        class_name: Annotated[
            t.NonEmptyStr, m.Field(description="Top-level class selected by Rope")
        ]
        apply: Annotated[
            bool, m.Field(description="Whether to execute the validated move")
        ]


__all__: list[str] = ["FlextInfraModelsRopeMove"]
