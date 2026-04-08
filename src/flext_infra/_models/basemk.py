"""Domain models for the basemk subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_cli import m
from flext_infra import FlextInfraConstantsBase, t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraBasemkModels:
    """Models for base.mk template rendering."""

    class BaseMkConfig(
        FlextInfraModelsMixins.ProjectNameFieldMixin,
        m.ArbitraryTypesModel,
    ):
        """Configuration model used to render base.mk templates."""

        python_version: Annotated[
            t.NonEmptyStr,
            Field(description="Target Python version"),
        ]
        core_stack: Annotated[
            t.NonEmptyStr,
            Field(description="Core stack classification"),
        ]
        package_manager: Annotated[
            str,
            Field(
                default=FlextInfraConstantsBase.POETRY,
                description="Dependency manager",
            ),
        ]
        source_dir: Annotated[
            str,
            Field(
                default=FlextInfraConstantsBase.Paths.DEFAULT_SRC_DIR,
                description="Source directory path",
            ),
        ]
        tests_dir: Annotated[
            str,
            Field(
                default=FlextInfraConstantsBase.Directories.TESTS,
                description="Tests directory path",
            ),
        ]
        lint_gates: Annotated[
            t.StrSequence,
            Field(
                description="Enabled quality gates",
            ),
        ] = Field(default_factory=list)
        test_command: Annotated[
            str,
            Field(
                default=FlextInfraConstantsBase.PYTEST,
                description="Default test command",
            ),
        ]


__all__ = ["FlextInfraBasemkModels"]
