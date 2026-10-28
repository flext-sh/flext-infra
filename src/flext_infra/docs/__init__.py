# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.docs package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.docs._auditor import (
        FlextInfraDocsAuditorChecks,
        FlextInfraDocsAuditorReport,
    )
    from flext_infra.docs._generator import FlextInfraDocsGeneratorBundle
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.auditor_mixin import FlextInfraDocAuditorMixin
    from flext_infra.docs.base import FlextInfraDocServiceBase
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.collector import FlextInfraDocCollector
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.formatter import FlextInfraDocFormatter
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.server import FlextInfraDocServer
    from flext_infra.docs.validator import FlextInfraDocValidator


__all__: tuple[str, ...] = (
    "FlextInfraDocAuditor",
    "FlextInfraDocAuditorMixin",
    "FlextInfraDocBuilder",
    "FlextInfraDocCollector",
    "FlextInfraDocFixer",
    "FlextInfraDocFormatter",
    "FlextInfraDocGenerator",
    "FlextInfraDocServer",
    "FlextInfraDocServiceBase",
    "FlextInfraDocValidator",
    "FlextInfraDocsAuditorChecks",
    "FlextInfraDocsAuditorReport",
    "FlextInfraDocsGeneratorBundle",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraDocAuditor": ".auditor",
        "FlextInfraDocsAuditorChecks": "._auditor_checks",
        "FlextInfraDocAuditorMixin": ".auditor_mixin",
        "FlextInfraDocsAuditorReport": "._auditor_report",
        "FlextInfraDocBuilder": ".builder",
        "FlextInfraDocCollector": ".collector",
        "FlextInfraDocFixer": ".fixer",
        "FlextInfraDocFormatter": ".formatter",
        "FlextInfraDocGenerator": ".generator",
        "FlextInfraDocsGeneratorBundle": "._generator_bundle",
        "FlextInfraDocServer": ".server",
        "FlextInfraDocServiceBase": ".base",
        "FlextInfraDocValidator": ".validator",
    }),
    public_exports=__all__,
)
