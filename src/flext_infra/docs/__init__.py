# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.docs._auditor_mixin as _flext_infra_docs__auditor_mixin

    _auditor_mixin = _flext_infra_docs__auditor_mixin
    import flext_infra.docs.auditor as _flext_infra_docs_auditor
    from flext_infra.docs._auditor_mixin import FlextInfraDocAuditorMixin

    auditor = _flext_infra_docs_auditor
    import flext_infra.docs.builder as _flext_infra_docs_builder
    from flext_infra.docs.auditor import FlextInfraDocAuditor, main

    builder = _flext_infra_docs_builder
    import flext_infra.docs.cli as _flext_infra_docs_cli
    from flext_infra.docs.builder import FlextInfraDocBuilder

    cli = _flext_infra_docs_cli
    import flext_infra.docs.fixer as _flext_infra_docs_fixer
    from flext_infra.docs.cli import FlextInfraCliDocs, FlextInfraDocsCli

    fixer = _flext_infra_docs_fixer
    import flext_infra.docs.generator as _flext_infra_docs_generator
    from flext_infra.docs.fixer import FlextInfraDocFixer

    generator = _flext_infra_docs_generator
    import flext_infra.docs.validator as _flext_infra_docs_validator
    from flext_infra.docs.generator import FlextInfraDocGenerator

    validator = _flext_infra_docs_validator
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.docs.validator import FlextInfraDocValidator
_LAZY_IMPORTS = {
    "FlextInfraCliDocs": "flext_infra.docs.cli",
    "FlextInfraDocAuditor": "flext_infra.docs.auditor",
    "FlextInfraDocAuditorMixin": "flext_infra.docs._auditor_mixin",
    "FlextInfraDocBuilder": "flext_infra.docs.builder",
    "FlextInfraDocFixer": "flext_infra.docs.fixer",
    "FlextInfraDocGenerator": "flext_infra.docs.generator",
    "FlextInfraDocValidator": "flext_infra.docs.validator",
    "FlextInfraDocsCli": "flext_infra.docs.cli",
    "_auditor_mixin": "flext_infra.docs._auditor_mixin",
    "auditor": "flext_infra.docs.auditor",
    "builder": "flext_infra.docs.builder",
    "cli": "flext_infra.docs.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer": "flext_infra.docs.fixer",
    "generator": "flext_infra.docs.generator",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "main": "flext_infra.docs.auditor",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "validator": "flext_infra.docs.validator",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliDocs",
    "FlextInfraDocAuditor",
    "FlextInfraDocAuditorMixin",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
    "FlextInfraDocsCli",
    "_auditor_mixin",
    "auditor",
    "builder",
    "cli",
    "d",
    "e",
    "fixer",
    "generator",
    "h",
    "main",
    "r",
    "s",
    "validator",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
