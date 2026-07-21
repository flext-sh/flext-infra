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
    """Auto-loaded, validated flext-infra config; access via ``config.Infra.*``."""

    # NOTE (multi-agent, mro-wkii.9 + mro-wkii.17 / agent: codex): direct
    # config.Infra is the only codegen information surface; no accessor method.
    # NOTE (mro-sltx / backport from 0.20.0-dev): canonical [project-root]/config
    # resolution (parents[2]) overrides the package-anchored CONFIG_DIR inherited
    # from FlextCliConfig, so the infra YAML SSOT loads from the repo-root config/.
    CONFIG_DIR: ClassVar[str] = str(Path(__file__).resolve().parents[2] / "config")
    Infra: FlextInfraConfigModels.Infra


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
