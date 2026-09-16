"""Config models facade: the config families joined via MRO."""

from __future__ import annotations

from ._config.base import FlextInfraConfigModelsBase


class FlextInfraConfigModels(FlextInfraConfigModelsBase):
    """Field-only models for config loading and codegen plans."""


__all__: list[str] = ["FlextInfraConfigModels"]
