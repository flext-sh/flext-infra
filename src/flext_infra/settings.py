"""Runtime settings for flext-infra environment-driven behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_core import FlextSettings, m, u

from flext_infra import c


@FlextSettings.auto_register("infra")
class FlextInfraSettings(FlextSettings):
    """Environment-backed settings for infra workspace and dependency flows."""

    model_config: ClassVar[m.SettingsConfigDict] = m.SettingsConfigDict(
        env_prefix="FLEXT_INFRA_",
        extra="ignore",
    )

    standalone: Annotated[
        bool,
        u.Field(
            default=c.Infra.ENV_DEFAULT_STANDALONE,
            validation_alias=c.Infra.ENV_VAR_STANDALONE,
            description="Force standalone mode and skip workspace auto-detection.",
        ),
    ]
    workspace_root: Annotated[
        Path | None,
        u.Field(
            default=None,
            validation_alias=c.Infra.ENV_VAR_WORKSPACE_ROOT,
            description="Explicit workspace root used for dependency orchestration.",
        ),
    ] = None
    use_https: Annotated[
        bool,
        u.Field(
            default=c.Infra.ENV_DEFAULT_USE_HTTPS,
            validation_alias=c.Infra.ENV_VAR_USE_HTTPS,
            description="Prefer HTTPS repository URLs during dependency sync.",
        ),
    ]
    github_actions: Annotated[
        bool,
        u.Field(
            default=c.Infra.ENV_DEFAULT_GITHUB_ACTIONS,
            validation_alias=c.Infra.ENV_VAR_GITHUB_ACTIONS,
            description="Whether the current runtime is a GitHub Actions environment.",
        ),
    ]
    github_head_ref: Annotated[
        str | None,
        u.Field(
            default=None,
            validation_alias=c.Infra.ENV_VAR_GITHUB_HEAD_REF,
            description="GitHub Actions head ref override for dependency sync.",
        ),
    ] = None
    github_ref_name: Annotated[
        str | None,
        u.Field(
            default=None,
            validation_alias=c.Infra.ENV_VAR_GITHUB_REF_NAME,
            description="GitHub Actions ref-name override for dependency sync.",
        ),
    ] = None

    @u.field_validator("standalone", mode="before")
    @classmethod
    def _coerce_standalone(cls, value: bool | str | None) -> bool | str:
        if value is None:
            return c.Infra.ENV_DEFAULT_STANDALONE
        if isinstance(value, str) and not value.strip():
            return c.Infra.ENV_DEFAULT_STANDALONE
        return value

    @u.field_validator("workspace_root", mode="before")
    @classmethod
    def _coerce_workspace_root(cls, value: str | Path | None) -> Path | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return Path(text).expanduser().resolve()


__all__: list[str] = ["FlextInfraSettings"]
