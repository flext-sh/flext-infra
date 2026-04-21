"""Shared MRO bases for thin dependency services."""

from __future__ import annotations

from abc import ABC

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    FlextInfraServiceBase,
)


class FlextInfraDepsServiceBase(FlextInfraServiceBase[bool], ABC):
    """Shared deps base extending the canonical infra service foundation."""


class FlextInfraDepsProjectServiceBase(
    FlextInfraProjectSelectionServiceBase[bool],
    ABC,
):
    """Dependency-service specialization of the shared project selection base."""


__all__: list[str] = [
    "FlextInfraDepsProjectServiceBase",
    "FlextInfraDepsServiceBase",
]
