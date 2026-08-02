"""Pure Pydantic settings declarations for flext-infra."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_core import m


class FlextInfraSettingsModels:
    """Private namespace for validated settings payloads."""

    class Infra(m.BaseSettings):
        """Validated process-start settings owned by flext-infra."""

        # mro-wkii.4.15: validate every external alias before singleton export.
        model_config = m.SettingsConfigDict(
            env_prefix="",
            env_ignore_empty=True,
            case_sensitive=True,
            populate_by_name=True,
            frozen=True,
            extra="forbid",
        )

        standalone: Annotated[
            bool,
            m.Field(
                default=False,
                validation_alias="FLEXT_STANDALONE",
                description="Force standalone mode and skip workspace auto-detection.",
            ),
        ]
        workspace_root: Annotated[
            Path | None,
            m.Field(
                default=None,
                validation_alias="FLEXT_WORKSPACE_ROOT",
                description="Explicit workspace root for dependency orchestration.",
            ),
        ]
        use_https: Annotated[
            bool,
            m.Field(
                default=False,
                validation_alias="FLEXT_USE_HTTPS",
                description="Prefer HTTPS repository URLs during dependency sync.",
            ),
        ]
        github_actions: Annotated[
            bool,
            m.Field(
                default=False,
                validation_alias="GITHUB_ACTIONS",
                description="Whether the process runs in GitHub Actions.",
            ),
        ]
        github_head_ref: Annotated[
            str | None,
            m.Field(
                default=None,
                validation_alias="GITHUB_HEAD_REF",
                description="GitHub Actions head ref for dependency sync.",
            ),
        ]
        github_ref_name: Annotated[
            str | None,
            m.Field(
                default=None,
                validation_alias="GITHUB_REF_NAME",
                description="GitHub Actions ref name for dependency sync.",
            ),
        ]


__all__: list[str] = ["FlextInfraSettingsModels"]
