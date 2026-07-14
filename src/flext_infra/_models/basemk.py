"""Domain models for the basemk subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsBasemk:
    """Models for base.mk template rendering."""

    class BaseMkConfig(mm.ProjectNameFieldMixin, m.ArbitraryTypesModel):
        """Configuration model used to render base.mk templates."""

        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Target Python version")
        ]
        package_manager: Annotated[str, m.Field(description="Dependency manager")] = (
            c.Infra.POETRY
        )
        source_dir: Annotated[str, m.Field(description="Source directory path")] = (
            c.Infra.DEFAULT_SRC_DIR
        )
        tests_dir: Annotated[str, m.Field(description="Tests directory path")] = (
            c.Infra.DIR_TESTS
        )
        lint_gates: Annotated[
            t.StrSequence, m.Field(description="Enabled quality gates")
        ] = m.Field(default_factory=tuple)
        test_command: Annotated[str, m.Field(description="Default test command")] = (
            c.Infra.PYTEST
        )


__all__: list[str] = ["FlextInfraModelsBasemk"]
