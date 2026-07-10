"""FlextInfraConfig — frozen config singleton for flext-infra (ADR-005 §7).

Model-less: business rules live in ``config/*.yaml`` under the ``Infra:`` key and
are exposed through the open ``config.Infra`` namespace (``extra="allow"``), with
no per-domain model. Access is ``config.Infra.<domain>[<key>...]``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from flext_cli import FlextCliConfig


class _InfraNamespace(BaseModel):
    """Open, frozen namespace exposing every ``config/*.yaml`` domain model-less."""

    model_config = ConfigDict(extra="allow", frozen=True)


class FlextInfraConfig(FlextCliConfig):
    """Infra config auto-loaded model-less from ``config/*.yaml``."""

    Infra: _InfraNamespace = _InfraNamespace()


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
