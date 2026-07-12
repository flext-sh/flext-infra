"""Runtime settings for flext-infra — namespaced under ``settings.Infra``.

Layer-0 style: universal fields via MRO; all project fields in the ``Infra``
namespace group with simple scalar types (env-settable).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from importlib.metadata import version
from typing import TYPE_CHECKING, Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from flext_cli import FlextCliSettings


class FlextInfraSettings(FlextCliSettings):
    """Environment-backed infra settings; fields under ``settings.Infra.*``."""

    model_config = SettingsConfigDict(
        env_prefix="FLEXT_INFRA_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    class _Infra(BaseSettings):
        """Namespaced infra workspace + dependency settings."""

        # mro-wkii.4.15: Nested settings resolve external aliases once.
        model_config = SettingsConfigDict(extra="ignore")

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

    if TYPE_CHECKING:
        Infra: _Infra
    else:
        Infra: _Infra = Field(
            default_factory=_Infra, description="Namespaced infra settings."
        )


settings: FlextInfraSettings = FlextInfraSettings.fetch_global()
"""Pre-instantiated project settings singleton — ``from flext_infra import settings``."""

__all__: list[str] = ["FlextInfraSettings", "settings"]
