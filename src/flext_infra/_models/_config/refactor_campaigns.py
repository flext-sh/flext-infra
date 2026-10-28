"""Declared CSV-driven rename campaign models for the mod verb.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Annotated, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigRefactorCampaigns:
    """CSV-driven rename campaigns applied by the mod verb's rename phase."""

    class RenameCampaignSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One declared CSV-driven rename campaign applied by the mod verb."""

        rename_definitions: Annotated[
            bool,
            m.Field(description="Atomically rename owned declarations and references"),
        ] = False
        csv: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Config-directory-relative path to the old,new rename-list "
                    "CSV; the list ships with the declaring config"
                ),
            ),
        ]
        roots: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=(
                    "Repository-root-relative scan directories; empty selects "
                    "the whole repository root"
                ),
            ),
        ] = ()
        bindings: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(
                description=(
                    "CSV expression prefixes mapped "
                    "to current public Rope owner identities"
                ),
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, t.StrSequence]({}))
        text_globs: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Explicit root-relative non-Python "
                    "documentation and configuration text surfaces"
                ),
            ),
        ] = ()
        python_documentation: Annotated[
            bool,
            m.Field(
                description=(
                    "Rename comments and actual Python docstrings "
                    "without changing executable strings"
                ),
            ),
        ] = False
        exclude_globs: Annotated[
            t.StrSequence,
            m.Field(
                description="Generated projections excluded from campaign targets",
            ),
        ] = ()

        @staticmethod
        def _is_escaping_path(value: str) -> bool:
            """Whether one configured path escapes its declared relative owner.

            Returns:
                The resulting ``bool``.

            """
            path = Path(value)
            return bool(
                path.is_absolute()
                or PureWindowsPath(value).root
                or not path.parts
                or ".." in path.parts
                or "\\" in value
                or PureWindowsPath(value).drive,
            )

        @m.model_validator(mode="after")
        def _validate_source_paths(self) -> Self:
            """Keep campaign drivers and scan roots inside their declared owners.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If CSV campaign path must be relative and non-escaping.

            """
            for value in (self.csv, *self.roots):
                if self._is_escaping_path(value):
                    msg = (
                        f"CSV campaign path must be relative and non-escaping: {value}"
                    )
                    raise ValueError(msg)
            return self

    class RefactorCsvCampaignsSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Declared CSV-driven rename campaigns for the mod verb's rename phase."""

        campaigns: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigRefactorCampaigns.RenameCampaignSpec],
            m.Field(default=(), description="Ordered rename campaigns"),
        ] = ()
        semantic_plan: Annotated[
            Path | None,
            m.Field(description="Explicit workspace-relative semantic rename artifact"),
        ] = None
        semantic_decisions: Annotated[
            Path | None,
            m.Field(
                description="Workspace-relative SemanticRenameSelections JSON input"
            ),
        ] = None

        @m.model_validator(mode="after")
        def validate_semantic_decisions(self) -> Self:
            """Require an explicit artifact destination for declared decisions.

            Returns:
                The validated campaign specification, unchanged.

            Raises:
                ValueError: If semantic_decisions is set without semantic_plan.

            """
            if self.semantic_decisions is not None and self.semantic_plan is None:
                msg = "semantic_decisions requires semantic_plan"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsConfigRefactorCampaigns"]
