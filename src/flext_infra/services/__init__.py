# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Services package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.services.consolidator as _flext_infra_services_consolidator

    consolidator = _flext_infra_services_consolidator
    import flext_infra.services.deduplicator as _flext_infra_services_deduplicator
    from flext_infra.services.consolidator import FlextInfraCodegenConsolidator

    deduplicator = _flext_infra_services_deduplicator
    import flext_infra.services.pipeline as _flext_infra_services_pipeline
    from flext_infra.services.deduplicator import FlextInfraCodegenDeduplicator

    pipeline = _flext_infra_services_pipeline
    import flext_infra.services.toml_engine as _flext_infra_services_toml_engine
    from flext_infra.services.pipeline import FlextInfraCodegenPipeline

    toml_engine = _flext_infra_services_toml_engine
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.services.toml_engine import FlextInfraToml
_LAZY_IMPORTS = {
    "FlextInfraCodegenConsolidator": "flext_infra.services.consolidator",
    "FlextInfraCodegenDeduplicator": "flext_infra.services.deduplicator",
    "FlextInfraCodegenPipeline": "flext_infra.services.pipeline",
    "FlextInfraToml": "flext_infra.services.toml_engine",
    "consolidator": "flext_infra.services.consolidator",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "deduplicator": "flext_infra.services.deduplicator",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "pipeline": "flext_infra.services.pipeline",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "toml_engine": "flext_infra.services.toml_engine",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenDeduplicator",
    "FlextInfraCodegenPipeline",
    "FlextInfraToml",
    "consolidator",
    "d",
    "deduplicator",
    "e",
    "h",
    "pipeline",
    "r",
    "s",
    "toml_engine",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
