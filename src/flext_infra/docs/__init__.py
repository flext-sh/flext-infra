# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.docs._auditor_helpers as _flext_infra_docs__auditor_helpers

    _auditor_helpers = _flext_infra_docs__auditor_helpers
    import flext_infra.docs._constants as _flext_infra_docs__constants
    from flext_infra.docs._auditor_helpers import (
        find_architecture_config,
        parse_audit_gate,
        resolve_checks,
        write_audit_reports,
    )

    _constants = _flext_infra_docs__constants
    import flext_infra.docs._models as _flext_infra_docs__models
    from flext_infra.docs._constants import FlextInfraDocsConstants

    _models = _flext_infra_docs__models
    import flext_infra.docs.auditor as _flext_infra_docs_auditor
    from flext_infra.docs._models import FlextInfraDocsModels

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
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.docs.validator import FlextInfraDocValidator
_LAZY_IMPORTS = {
    "FlextInfraCliDocs": "flext_infra.docs.cli",
    "FlextInfraDocAuditor": "flext_infra.docs.auditor",
    "FlextInfraDocBuilder": "flext_infra.docs.builder",
    "FlextInfraDocFixer": "flext_infra.docs.fixer",
    "FlextInfraDocGenerator": "flext_infra.docs.generator",
    "FlextInfraDocValidator": "flext_infra.docs.validator",
    "FlextInfraDocsCli": "flext_infra.docs.cli",
    "FlextInfraDocsConstants": "flext_infra.docs._constants",
    "FlextInfraDocsModels": "flext_infra.docs._models",
    "_auditor_helpers": "flext_infra.docs._auditor_helpers",
    "_constants": "flext_infra.docs._constants",
    "_models": "flext_infra.docs._models",
    "auditor": "flext_infra.docs.auditor",
    "builder": "flext_infra.docs.builder",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.docs.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "find_architecture_config": "flext_infra.docs._auditor_helpers",
    "fixer": "flext_infra.docs.fixer",
    "generator": "flext_infra.docs.generator",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main": "flext_infra.docs.auditor",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "parse_audit_gate": "flext_infra.docs._auditor_helpers",
    "r": ("flext_core.result", "FlextResult"),
    "resolve_checks": "flext_infra.docs._auditor_helpers",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "validator": "flext_infra.docs.validator",
    "write_audit_reports": "flext_infra.docs._auditor_helpers",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliDocs",
    "FlextInfraDocAuditor",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
    "FlextInfraDocsCli",
    "FlextInfraDocsConstants",
    "FlextInfraDocsModels",
    "_auditor_helpers",
    "_constants",
    "_models",
    "auditor",
    "builder",
    "c",
    "cli",
    "d",
    "e",
    "find_architecture_config",
    "fixer",
    "generator",
    "h",
    "m",
    "main",
    "p",
    "parse_audit_gate",
    "r",
    "resolve_checks",
    "s",
    "t",
    "u",
    "validator",
    "write_audit_reports",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
