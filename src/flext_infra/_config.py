"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_cli import FlextCliConfig
from flext_infra._models.config import FlextInfraConfigModels


class _FlextInfraConfig(FlextCliConfig):
    """Declarative flext-infra config loaded and validated once."""

    # NOTE (multi-agent, mro-wkii.9 + mro-wkii.17 / agent: codex): direct
    # config.Infra is the only codegen information surface; no accessor method.
    # NOTE (mro-wkii.17.26, agent codex): flext-core resolves this canonical
    # relative root in both installed-package and editable-project layouts.
    CONFIG_DIR: ClassVar[str] = "config"
    Infra: FlextInfraConfigModels.Infra


config: _FlextInfraConfig = _FlextInfraConfig()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["config"]
