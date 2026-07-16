"""Runtime settings for flext-infra — namespaced under ``settings.Infra``.

Layer-0 style: universal fields via MRO; all project fields in the ``Infra``
namespace group with simple scalar types (env-settable).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from flext_core import FlextSettings
from flext_infra._models.settings import FlextInfraSettingsModels


class FlextInfraSettings(FlextSettings):
    """Environment-backed infra settings; fields under ``settings.Infra.*``."""

    model_config = SettingsConfigDict(
        env_prefix="FLEXT_INFRA_", env_nested_delimiter="__", extra="ignore"
    )

    Infra: FlextInfraSettingsModels.Infra = Field(
        default_factory=FlextInfraSettingsModels.Infra,
        description="Namespaced infra settings.",
    )


settings: FlextInfraSettings = FlextInfraSettings.fetch_global()
"""Pre-instantiated project settings singleton — ``from flext_infra import settings``."""

__all__: list[str] = ["FlextInfraSettings", "settings"]
