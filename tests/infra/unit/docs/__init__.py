# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .auditor import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from .auditor_budgets import TestLoadAuditBudgets
    from .auditor_cli import TestAuditorMainCli, TestAuditorScopeFailure
    from .auditor_links import TestAuditorBrokenLinks, TestAuditorToMarkdown
    from .auditor_scope import TestAuditorForbiddenTerms, TestAuditorScope
    from .builder import TestBuilderCore, builder
    from .builder_scope import TestBuilderScope
    from .fixer import TestFixerCore
    from .fixer_internals import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )
    from .generator import TestGeneratorCore
    from .generator_internals import TestGeneratorHelpers, TestGeneratorScope, gen
    from .init import TestFlextInfraDocs
    from .main import TestRunAudit, TestRunFix
    from .main_commands import TestRunBuild, TestRunGenerate, TestRunValidate
    from .main_entry import TestMainRouting, TestMainWithFlags
    from .shared import TestBuildScopes, TestFlextInfraDocScope
    from .shared_iter import TestIterMarkdownFiles, TestSelectedProjectNames
    from .shared_write import TestWriteJson, TestWriteMarkdown
    from .validator import TestValidateCore, TestValidateReport
    from .validator_internals import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestAdrHelpers": ("tests.infra.unit.docs.validator_internals", "TestAdrHelpers"),
    "TestAuditorBrokenLinks": (
        "tests.infra.unit.docs.auditor_links",
        "TestAuditorBrokenLinks",
    ),
    "TestAuditorCore": ("tests.infra.unit.docs.auditor", "TestAuditorCore"),
    "TestAuditorForbiddenTerms": (
        "tests.infra.unit.docs.auditor_scope",
        "TestAuditorForbiddenTerms",
    ),
    "TestAuditorMainCli": ("tests.infra.unit.docs.auditor_cli", "TestAuditorMainCli"),
    "TestAuditorNormalize": ("tests.infra.unit.docs.auditor", "TestAuditorNormalize"),
    "TestAuditorScope": ("tests.infra.unit.docs.auditor_scope", "TestAuditorScope"),
    "TestAuditorScopeFailure": (
        "tests.infra.unit.docs.auditor_cli",
        "TestAuditorScopeFailure",
    ),
    "TestAuditorToMarkdown": (
        "tests.infra.unit.docs.auditor_links",
        "TestAuditorToMarkdown",
    ),
    "TestBuildScopes": ("tests.infra.unit.docs.shared", "TestBuildScopes"),
    "TestBuilderCore": ("tests.infra.unit.docs.builder", "TestBuilderCore"),
    "TestBuilderScope": ("tests.infra.unit.docs.builder_scope", "TestBuilderScope"),
    "TestFixerCore": ("tests.infra.unit.docs.fixer", "TestFixerCore"),
    "TestFixerMaybeFixLink": (
        "tests.infra.unit.docs.fixer_internals",
        "TestFixerMaybeFixLink",
    ),
    "TestFixerProcessFile": (
        "tests.infra.unit.docs.fixer_internals",
        "TestFixerProcessFile",
    ),
    "TestFixerScope": ("tests.infra.unit.docs.fixer_internals", "TestFixerScope"),
    "TestFixerToc": ("tests.infra.unit.docs.fixer_internals", "TestFixerToc"),
    "TestFlextInfraDocScope": (
        "tests.infra.unit.docs.shared",
        "TestFlextInfraDocScope",
    ),
    "TestFlextInfraDocs": ("tests.infra.unit.docs.init", "TestFlextInfraDocs"),
    "TestGeneratorCore": ("tests.infra.unit.docs.generator", "TestGeneratorCore"),
    "TestGeneratorHelpers": (
        "tests.infra.unit.docs.generator_internals",
        "TestGeneratorHelpers",
    ),
    "TestGeneratorScope": (
        "tests.infra.unit.docs.generator_internals",
        "TestGeneratorScope",
    ),
    "TestIterMarkdownFiles": (
        "tests.infra.unit.docs.shared_iter",
        "TestIterMarkdownFiles",
    ),
    "TestLoadAuditBudgets": (
        "tests.infra.unit.docs.auditor_budgets",
        "TestLoadAuditBudgets",
    ),
    "TestMainRouting": ("tests.infra.unit.docs.main_entry", "TestMainRouting"),
    "TestMainWithFlags": ("tests.infra.unit.docs.main_entry", "TestMainWithFlags"),
    "TestMaybeWriteTodo": (
        "tests.infra.unit.docs.validator_internals",
        "TestMaybeWriteTodo",
    ),
    "TestRunAudit": ("tests.infra.unit.docs.main", "TestRunAudit"),
    "TestRunBuild": ("tests.infra.unit.docs.main_commands", "TestRunBuild"),
    "TestRunFix": ("tests.infra.unit.docs.main", "TestRunFix"),
    "TestRunGenerate": ("tests.infra.unit.docs.main_commands", "TestRunGenerate"),
    "TestRunValidate": ("tests.infra.unit.docs.main_commands", "TestRunValidate"),
    "TestSelectedProjectNames": (
        "tests.infra.unit.docs.shared_iter",
        "TestSelectedProjectNames",
    ),
    "TestValidateCore": ("tests.infra.unit.docs.validator", "TestValidateCore"),
    "TestValidateReport": ("tests.infra.unit.docs.validator", "TestValidateReport"),
    "TestValidateScope": (
        "tests.infra.unit.docs.validator_internals",
        "TestValidateScope",
    ),
    "TestWriteJson": ("tests.infra.unit.docs.shared_write", "TestWriteJson"),
    "TestWriteMarkdown": ("tests.infra.unit.docs.shared_write", "TestWriteMarkdown"),
    "auditor": ("tests.infra.unit.docs.auditor", "auditor"),
    "builder": ("tests.infra.unit.docs.builder", "builder"),
    "fixer": ("tests.infra.unit.docs.fixer_internals", "fixer"),
    "gen": ("tests.infra.unit.docs.generator_internals", "gen"),
    "is_external": ("tests.infra.unit.docs.auditor", "is_external"),
    "normalize_link": ("tests.infra.unit.docs.auditor", "normalize_link"),
    "should_skip_target": ("tests.infra.unit.docs.auditor", "should_skip_target"),
    "validator": ("tests.infra.unit.docs.validator_internals", "validator"),
}

__all__ = [
    "TestAdrHelpers",
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorMainCli",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorScopeFailure",
    "TestAuditorToMarkdown",
    "TestBuildScopes",
    "TestBuilderCore",
    "TestBuilderScope",
    "TestFixerCore",
    "TestFixerMaybeFixLink",
    "TestFixerProcessFile",
    "TestFixerScope",
    "TestFixerToc",
    "TestFlextInfraDocScope",
    "TestFlextInfraDocs",
    "TestGeneratorCore",
    "TestGeneratorHelpers",
    "TestGeneratorScope",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestMainRouting",
    "TestMainWithFlags",
    "TestMaybeWriteTodo",
    "TestRunAudit",
    "TestRunBuild",
    "TestRunFix",
    "TestRunGenerate",
    "TestRunValidate",
    "TestSelectedProjectNames",
    "TestValidateCore",
    "TestValidateReport",
    "TestValidateScope",
    "TestWriteJson",
    "TestWriteMarkdown",
    "auditor",
    "builder",
    "fixer",
    "gen",
    "is_external",
    "normalize_link",
    "should_skip_target",
    "validator",
]


_LAZY_CACHE: dict[str, object] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
