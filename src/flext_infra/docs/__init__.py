# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.docs._auditor.checks import FlextInfraDocsAuditorChecks
    from flext_infra.docs._auditor.report import FlextInfraDocsAuditorReport
    from flext_infra.docs._generator.bundle import FlextInfraDocsGeneratorBundle
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
        "FlextInfraDocAuditorMixin": ".auditor_mixin",
        "FlextInfraDocBuilder": ".builder",
        "FlextInfraDocCollector": ".collector",
        "FlextInfraDocFixer": ".fixer",
        "FlextInfraDocFormatter": ".formatter",
        "FlextInfraDocGenerator": ".generator",
        "FlextInfraDocServer": ".server",
        "FlextInfraDocServiceBase": ".base",
        "FlextInfraDocValidator": ".validator",
        "FlextInfraDocsAuditorChecks": "._auditor.checks",
        "FlextInfraDocsAuditorReport": "._auditor.report",
        "FlextInfraDocsGeneratorBundle": "._generator.bundle",
    }),
    public_exports=__all__,
)
