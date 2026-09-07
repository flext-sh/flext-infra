"""Generation helpers for docs services."""

from __future__ import annotations

# Why: restored lost composition — FlextInfraUtilitiesDocsGuidesMixin was
# never wired into any composed Docs* facade, leaving consumers unresolved.
from flext_infra._utilities._docs_guides import FlextInfraUtilitiesDocsGuidesMixin

from .._utilities._docs_generate_root import FlextInfraUtilitiesDocsGenerateRootMixin


class FlextInfraUtilitiesDocsGenerate(
    FlextInfraUtilitiesDocsGenerateRootMixin, FlextInfraUtilitiesDocsGuidesMixin
):
    """Reusable generation helpers exposed through ``u.Infra``."""


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerate"]
