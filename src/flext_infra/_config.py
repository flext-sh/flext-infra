"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_cli import FlextCliConfig

if TYPE_CHECKING:
    from flext_infra._models.config import (
        FlextInfraConfigModels,  # mro-itcd.1: runtime type required by Pydantic for Infra annotation.
    )


class FlextInfraConfig(FlextCliConfig):
    """Auto-loaded, validated flext-infra config; access via ``config.Infra.*``."""

    # Canonical [project-root]/config resolution (cosmos-main pattern): overrides
    # the package-anchored CONFIG_DIR inherited from FlextCliConfig so the infra
    # YAML SSOT loads, composing config.Infra beside the inherited config.Cli.
    CONFIG_DIR: ClassVar[str] = str(Path(__file__).resolve().parents[2] / "config")
    Infra: FlextInfraConfigModels.Infra


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
