# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes


if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .auditor_budgets_tests import TestLoadAuditBudgets
    from .auditor_cli_tests import TestAuditorMainCli, TestAuditorScopeFailure
    from .auditor_links_tests import TestAuditorBrokenLinks, TestAuditorToMarkdown
    from .auditor_scope_tests import TestAuditorForbiddenTerms, TestAuditorScope
    from .auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from .builder_scope_tests import TestBuilderScope
    from .builder_tests import TestBuilderCore, builder
    from .fixer_internals_tests import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )
    from .fixer_tests import TestFixerCore
    from .generator_internals_tests import TestGeneratorHelpers, TestGeneratorScope, gen
    from .generator_tests import TestGeneratorCore
    from .init_tests import TestFlextInfraDocs
    from .main_commands_tests import TestRunBuild, TestRunGenerate, TestRunValidate
    from .main_entry_tests import TestMainRouting, TestMainWithFlags
    from .main_tests import TestRunAudit, TestRunFix
    from .shared_iter_tests import TestIterMarkdownFiles, TestSelectedProjectNames
    from .shared_tests import TestBuildScopes, TestFlextInfraDocScope
    from .shared_write_tests import TestWriteJson, TestWriteMarkdown
    from .validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )
    from .validator_tests import TestValidateCore, TestValidateReport

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestAdrHelpers": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestAdrHelpers",
    ),
    "TestAuditorBrokenLinks": (
        "tests.infra.unit.docs.auditor_links_tests",
        "TestAuditorBrokenLinks",
    ),
    "TestAuditorCore": ("tests.infra.unit.docs.auditor_tests", "TestAuditorCore"),
    "TestAuditorForbiddenTerms": (
        "tests.infra.unit.docs.auditor_scope_tests",
        "TestAuditorForbiddenTerms",
    ),
    "TestAuditorMainCli": (
        "tests.infra.unit.docs.auditor_cli_tests",
        "TestAuditorMainCli",
    ),
    "TestAuditorNormalize": (
        "tests.infra.unit.docs.auditor_tests",
        "TestAuditorNormalize",
    ),
    "TestAuditorScope": (
        "tests.infra.unit.docs.auditor_scope_tests",
        "TestAuditorScope",
    ),
    "TestAuditorScopeFailure": (
        "tests.infra.unit.docs.auditor_cli_tests",
        "TestAuditorScopeFailure",
    ),
    "TestAuditorToMarkdown": (
        "tests.infra.unit.docs.auditor_links_tests",
        "TestAuditorToMarkdown",
    ),
    "TestBuildScopes": ("tests.infra.unit.docs.shared_tests", "TestBuildScopes"),
    "TestBuilderCore": ("tests.infra.unit.docs.builder_tests", "TestBuilderCore"),
    "TestBuilderScope": (
        "tests.infra.unit.docs.builder_scope_tests",
        "TestBuilderScope",
    ),
    "TestFixerCore": ("tests.infra.unit.docs.fixer_tests", "TestFixerCore"),
    "TestFixerMaybeFixLink": (
        "tests.infra.unit.docs.fixer_internals_tests",
        "TestFixerMaybeFixLink",
    ),
    "TestFixerProcessFile": (
        "tests.infra.unit.docs.fixer_internals_tests",
        "TestFixerProcessFile",
    ),
    "TestFixerScope": ("tests.infra.unit.docs.fixer_internals_tests", "TestFixerScope"),
    "TestFixerToc": ("tests.infra.unit.docs.fixer_internals_tests", "TestFixerToc"),
    "TestFlextInfraDocScope": (
        "tests.infra.unit.docs.shared_tests",
        "TestFlextInfraDocScope",
    ),
    "TestFlextInfraDocs": ("tests.infra.unit.docs.init_tests", "TestFlextInfraDocs"),
    "TestGeneratorCore": ("tests.infra.unit.docs.generator_tests", "TestGeneratorCore"),
    "TestGeneratorHelpers": (
        "tests.infra.unit.docs.generator_internals_tests",
        "TestGeneratorHelpers",
    ),
    "TestGeneratorScope": (
        "tests.infra.unit.docs.generator_internals_tests",
        "TestGeneratorScope",
    ),
    "TestIterMarkdownFiles": (
        "tests.infra.unit.docs.shared_iter_tests",
        "TestIterMarkdownFiles",
    ),
    "TestLoadAuditBudgets": (
        "tests.infra.unit.docs.auditor_budgets_tests",
        "TestLoadAuditBudgets",
    ),
    "TestMainRouting": ("tests.infra.unit.docs.main_entry_tests", "TestMainRouting"),
    "TestMainWithFlags": (
        "tests.infra.unit.docs.main_entry_tests",
        "TestMainWithFlags",
    ),
    "TestMaybeWriteTodo": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestMaybeWriteTodo",
    ),
    "TestRunAudit": ("tests.infra.unit.docs.main_tests", "TestRunAudit"),
    "TestRunBuild": ("tests.infra.unit.docs.main_commands_tests", "TestRunBuild"),
    "TestRunFix": ("tests.infra.unit.docs.main_tests", "TestRunFix"),
    "TestRunGenerate": ("tests.infra.unit.docs.main_commands_tests", "TestRunGenerate"),
    "TestRunValidate": ("tests.infra.unit.docs.main_commands_tests", "TestRunValidate"),
    "TestSelectedProjectNames": (
        "tests.infra.unit.docs.shared_iter_tests",
        "TestSelectedProjectNames",
    ),
    "TestValidateCore": ("tests.infra.unit.docs.validator_tests", "TestValidateCore"),
    "TestValidateReport": (
        "tests.infra.unit.docs.validator_tests",
        "TestValidateReport",
    ),
    "TestValidateScope": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestValidateScope",
    ),
    "TestWriteJson": ("tests.infra.unit.docs.shared_write_tests", "TestWriteJson"),
    "TestWriteMarkdown": (
        "tests.infra.unit.docs.shared_write_tests",
        "TestWriteMarkdown",
    ),
    "auditor": ("tests.infra.unit.docs.auditor_tests", "auditor"),
    "builder": ("tests.infra.unit.docs.builder_tests", "builder"),
    "fixer": ("tests.infra.unit.docs.fixer_internals_tests", "fixer"),
    "gen": ("tests.infra.unit.docs.generator_internals_tests", "gen"),
    "is_external": ("tests.infra.unit.docs.auditor_tests", "is_external"),
    "normalize_link": ("tests.infra.unit.docs.auditor_tests", "normalize_link"),
    "should_skip_target": ("tests.infra.unit.docs.auditor_tests", "should_skip_target"),
    "validator": ("tests.infra.unit.docs.validator_internals_tests", "validator"),
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


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


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
