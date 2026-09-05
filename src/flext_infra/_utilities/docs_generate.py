"""Generation helpers for docs services."""

from __future__ import annotations

from flext_infra._utilities._docs_generate_root import (
    FlextInfraUtilitiesDocsGenerateRootMixin,
)


class FlextInfraUtilitiesDocsGenerate(FlextInfraUtilitiesDocsGenerateRootMixin):
    """Reusable generation helpers exposed through ``u.Infra``."""


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerate"]
