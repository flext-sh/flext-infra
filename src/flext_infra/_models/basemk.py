"""Domain models for the basemk subpackage."""

from __future__ import annotations

from flext_cli import m
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsBasemk:
    """Models for base.mk template rendering."""

    class BaseMkConfig(mm.ProjectNameFieldMixin, m.ArbitraryTypesModel):
        """Project identity accepted by the legacy basemk facade."""


__all__: list[str] = ["FlextInfraModelsBasemk"]
