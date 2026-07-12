"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_cli import FlextCliConfig
from flext_infra._models.config import FlextInfraConfigModels


class FlextInfraConfig(FlextCliConfig):
    """Declarative flext-infra config loaded and validated once."""

    # NOTE (multi-agent, mro-wkii.9 + mro-wkii.17 / agent: codex): direct
    # config.Infra is the only codegen information surface; no accessor method.
    CONFIG_DIR: ClassVar[str] = str(Path(__file__).resolve().parent / "config")
    Infra: FlextInfraConfigModels.Infra


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
