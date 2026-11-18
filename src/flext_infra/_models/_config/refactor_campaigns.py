"""Declared CSV-driven rename campaign models for the mod verb.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config import FlextInfraModelsConfigContract


class FlextInfraModelsConfigRefactorCampaigns:
    """CSV-driven rename campaigns applied by the mod verb's rename phase."""

    class RenameCampaignSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One declared CSV-driven rename campaign applied by the mod verb."""

        id: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^csv:[a-z0-9]+(?:-[a-z0-9]+)*$",
                description="Stable public selector for this CSV campaign",
            ),
        ]
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
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Repository-root-relative scan directories; empty selects "
                    "the whole repository root"
                ),
            ),
        ] = ()
        bindings: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(
                description=(
                    "CSV expression prefixes mapped "
                    "to current public Rope owner identities"
                ),
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, Sequence[str]]({}))
        text_globs: Annotated[
            Sequence[str],
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
            Sequence[str],
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

    class ModOwnerSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One explicitly selected semantic or callback owner for ``mod``."""

        id: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^(?:semantic|callback):[a-z0-9]+(?:-[a-z0-9]+)*$",
                description="Stable public selector for a non-catalog mod owner",
            ),
        ]
        kind: Literal["semantic", "callback"]
        phase: str | None = None
        callback: str | None = None

        @m.model_validator(mode="after")
        def validate_owner(self) -> Self:
            """Keep owner selectors closed and unambiguous.

            Returns:
                The validated declaration.

            Raises:
                ValueError: If the selector does not match its declared owner.

            """
            callbacks = {
                "import-normalization",
                "facade-components",
                "namespace-relocations",
                "duplicate-apply",
                "accessor-rename",
            }
            if self.kind == "semantic":
                phases = {
                    "semantic:cutover": None,
                    "semantic:external-model-owner": "external-model-owner",
                    "semantic:test-namespace-import": "test-namespace-import",
                    "semantic:test-assert-to-matcher": "test-assert-to-matcher",
                    "semantic:compat-alias": "compat-alias",
                    "semantic:contract-normalization": "contract-normalization",
                }
                if (
                    self.id not in phases
                    or self.phase != phases[self.id]
                    or self.callback is not None
                ):
                    msg = (
                        "semantic owner must declare its supported phase without "
                        "callback"
                    )
                    raise ValueError(msg)
            elif (
                self.callback not in callbacks
                or self.id != f"callback:{self.callback}"
                or self.phase is not None
            ):
                msg = "callback owner ID must name one declared callback"
                raise ValueError(msg)
            return self

    class RefactorCsvCampaignsSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Declared CSV-driven rename campaigns for the mod verb's rename phase."""

        rewire_directory: Annotated[
            Path,
            m.Field(
                description="Repository-relative immutable native rewire artifacts"
            ),
        ]
        campaigns: Annotated[
            tuple[
                (FlextInfraModelsConfigRefactorCampaigns.RenameCampaignSpec),
                ...,
            ],
            m.Field(default=(), description="Ordered rename campaigns"),
        ] = ()
        owners: Annotated[
            tuple[
                FlextInfraModelsConfigRefactorCampaigns.ModOwnerSpec,
                ...,
            ],
            m.Field(
                default=(), description="Explicit semantic and callback mod owners"
            ),
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
        def validate_campaign_ids(self) -> Self:
            """Require every declared campaign selector to be unique.

            Returns:
                The validated campaign specification, unchanged.

            Raises:
                ValueError: If two campaigns claim the same public selector.

            """
            ids = tuple(campaign.id for campaign in self.campaigns) + tuple(
                owner.id for owner in self.owners
            )
            if len(ids) != len(set(ids)):
                msg = "duplicate refactor mod owner selector"
                raise ValueError(msg)
            return self

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
