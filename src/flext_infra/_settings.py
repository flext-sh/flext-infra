"""Runtime settings for flext-infra — namespaced under ``settings.Infra``.

Layer-0 style: universal fields via MRO; all project fields in the ``Infra``
namespace group with simple scalar types (env-settable).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import SettingsConfigDict

from flext_cli import FlextCliSettings


class FlextInfraSettings(FlextCliSettings):
    """Environment-backed infra settings; fields under ``settings.Infra.*``."""

    model_config = SettingsConfigDict(
        env_prefix="FLEXT_INFRA_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    class _Infra(BaseModel):
        """Namespaced infra workspace + dependency settings."""

        standalone: Annotated[
            bool,
            Field(
                default=False,
                validation_alias="FLEXT_STANDALONE",
                description="Force standalone mode and skip workspace auto-detection.",
            ),
        ]
        workspace_root: Annotated[
            str | None,
            Field(
                default=None,
                validation_alias="FLEXT_WORKSPACE_ROOT",
                description="Explicit workspace root used for dependency orchestration.",
            ),
        ]
        use_https: Annotated[
            bool,
            Field(
                default=False,
                validation_alias="FLEXT_USE_HTTPS",
                description="Prefer HTTPS repository URLs during dependency sync.",
            ),
        ]
        github_actions: Annotated[
            bool,
            Field(
                default=False,
                validation_alias="GITHUB_ACTIONS",
                description="Whether the current runtime is a GitHub Actions environment.",
            ),
        ]
        github_head_ref: Annotated[
            str | None,
            Field(
                default=None,
                validation_alias="GITHUB_HEAD_REF",
                description="GitHub Actions head ref override for dependency sync.",
            ),
        ]
        github_ref_name: Annotated[
            str | None,
            Field(
                default=None,
                validation_alias="GITHUB_REF_NAME",
                description="GitHub Actions ref-name override for dependency sync.",
            ),
        ]
        # NOTE(mro-wkii.13, agent codegen): default git branch/tag for flext-*
        # deps derives from the package version ("0.12.0.dev0" -> "0.12.0-dev",
        # the real remote branch); settings is the SSOT — NO constant, NO
        # hardcoded version string (operator directive). Env FLEXT_GIT_BRANCH
        # overrides when the remote ref differs.
        flext_git_branch: Annotated[
            str,
            Field(
                default_factory=lambda: re.sub(
                    r"\.dev\d+$", "-dev", version("flext-infra")
                ),
                validation_alias="FLEXT_GIT_BRANCH",
                description="Default git branch/tag for flext-* deps (PEP440 version normalized to branch).",
            ),
        ]
        # NOTE(mro-wkii.14, agent codegen): default VERSION for generated projects
        # derives from the flext-infra package metadata ("0.12.0.dev0" ->
        # "0.12.0-dev"); settings is the SSOT — NO constant, NO hardcoded version
        # (operator directive: version must come from settings, not constants).
        # Env FLEXT_VERSION overrides. Consumed by codegen ``project_new`` as the
        # default ``--version`` for every scaffold.
        flext_version: Annotated[
            str,
            Field(
                default_factory=lambda: re.sub(
                    r"\.dev\d+$", "-dev", version("flext-infra")
                ),
                validation_alias="FLEXT_VERSION",
                description="Default version stamped into generated project pyproject (from flext-infra metadata).",
            ),
        ]

        @field_validator("workspace_root", mode="before")
        @classmethod
        def _coerce_workspace_root(cls, value: str | None) -> str | None:
            """Coerce workspace root to a resolved absolute path string."""
            if value is None:
                return None
            # NOTE(mro-wkii.14, agent codegen): pyrefly unnecessary-type-conversion —
            # apos o guard None, value ja e str; str(value) removido (gate exigido
            # para commitar este arquivo verde; sem mudanca de comportamento).
            text = value.strip()
            if not text:
                return None
            return str(Path(text).expanduser().resolve())

    if TYPE_CHECKING:
        Infra: _Infra
    else:
        Infra: _Infra = Field(
            default_factory=_Infra, description="Namespaced infra settings."
        )


settings: FlextInfraSettings = FlextInfraSettings.fetch_global()
"""Pre-instantiated project settings singleton — ``from flext_infra import settings``."""

__all__: list[str] = ["FlextInfraSettings", "settings"]
