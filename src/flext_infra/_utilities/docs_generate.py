"""Generation helpers for docs services."""

from __future__ import annotations

# Why: restored lost composition — FlextInfraUtilitiesDocsGuidesMixin was
# never wired into any composed Docs* facade, leaving consumers unresolved.
from ._docs_generate_root import FlextInfraUtilitiesDocsGenerateRootMixin
from ._docs_guides import FlextInfraUtilitiesDocsGuidesMixin


class FlextInfraUtilitiesDocsGenerate(
    FlextInfraUtilitiesDocsGenerateRootMixin, FlextInfraUtilitiesDocsGuidesMixin
):
    """Reusable generation helpers exposed through ``u.Infra``."""


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerate"]
