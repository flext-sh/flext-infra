"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import ClassVar

from flext_cli import FlextCliConfig
from flext_infra._models.config import FlextInfraConfigModels


class FlextInfraConfig(FlextCliConfig):
    """Auto-loaded, validated flext-infra config; access via ``config.Infra.*``."""

    # Canonical [project-root]/config resolution (cosmos-main pattern): overrides
    # the package-anchored CONFIG_DIR inherited from FlextCliConfig so the infra
    # YAML SSOT loads, composing config.Infra beside the inherited config.Cli.
    CONFIG_DIR: ClassVar[str] = str(Path(__file__).resolve().parents[2] / "config")

    @cached_property
    def Infra(self) -> FlextInfraConfigModels.Infra:
        """Validated ``Infra`` business-rule config namespace."""
        root = FlextInfraConfigModels.Root.model_validate(
            dict(self.model_extra or {}),
        )
        return root.Infra


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
