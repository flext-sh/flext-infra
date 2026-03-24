# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Docs package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.docs.auditor_budgets_tests import TestLoadAuditBudgets
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli,
        TestAuditorScopeFailure,
    )
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorToMarkdown,
    )
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms,
        TestAuditorScope,
    )
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from tests.unit.docs.builder_scope_tests import TestBuilderScope
    from tests.unit.docs.builder_tests import TestBuilderCore, builder
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )
    from tests.unit.docs.fixer_tests import TestFixerCore
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers,
        TestGeneratorScope,
        gen,
    )
    from tests.unit.docs.generator_tests import TestGeneratorCore
    from tests.unit.docs.init_tests import TestFlextInfraDocs
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild,
        TestRunGenerate,
        TestRunValidate,
    )
    from tests.unit.docs.main_entry_tests import TestMainRouting, TestMainWithFlags
    from tests.unit.docs.main_tests import TestRunAudit, TestRunFix
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles,
        TestSelectedProjectNames,
    )
    from tests.unit.docs.shared_tests import TestBuildScopes, TestFlextInfraDocScope
    from tests.unit.docs.shared_write_tests import TestWriteJson, TestWriteMarkdown
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )
    from tests.unit.docs.validator_tests import TestValidateCore, TestValidateReport

_LAZY_IMPORTS: Mapping[str, tuple[str, str]] = {
    "TestAdrHelpers": ("tests.unit.docs.validator_internals_tests", "TestAdrHelpers"),
    "TestAuditorBrokenLinks": ("tests.unit.docs.auditor_links_tests", "TestAuditorBrokenLinks"),
    "TestAuditorCore": ("tests.unit.docs.auditor_tests", "TestAuditorCore"),
    "TestAuditorForbiddenTerms": ("tests.unit.docs.auditor_scope_tests", "TestAuditorForbiddenTerms"),
    "TestAuditorMainCli": ("tests.unit.docs.auditor_cli_tests", "TestAuditorMainCli"),
    "TestAuditorNormalize": ("tests.unit.docs.auditor_tests", "TestAuditorNormalize"),
    "TestAuditorScope": ("tests.unit.docs.auditor_scope_tests", "TestAuditorScope"),
    "TestAuditorScopeFailure": ("tests.unit.docs.auditor_cli_tests", "TestAuditorScopeFailure"),
    "TestAuditorToMarkdown": ("tests.unit.docs.auditor_links_tests", "TestAuditorToMarkdown"),
    "TestBuildScopes": ("tests.unit.docs.shared_tests", "TestBuildScopes"),
    "TestBuilderCore": ("tests.unit.docs.builder_tests", "TestBuilderCore"),
    "TestBuilderScope": ("tests.unit.docs.builder_scope_tests", "TestBuilderScope"),
    "TestFixerCore": ("tests.unit.docs.fixer_tests", "TestFixerCore"),
    "TestFixerMaybeFixLink": ("tests.unit.docs.fixer_internals_tests", "TestFixerMaybeFixLink"),
    "TestFixerProcessFile": ("tests.unit.docs.fixer_internals_tests", "TestFixerProcessFile"),
    "TestFixerScope": ("tests.unit.docs.fixer_internals_tests", "TestFixerScope"),
    "TestFixerToc": ("tests.unit.docs.fixer_internals_tests", "TestFixerToc"),
    "TestFlextInfraDocScope": ("tests.unit.docs.shared_tests", "TestFlextInfraDocScope"),
    "TestFlextInfraDocs": ("tests.unit.docs.init_tests", "TestFlextInfraDocs"),
    "TestGeneratorCore": ("tests.unit.docs.generator_tests", "TestGeneratorCore"),
    "TestGeneratorHelpers": ("tests.unit.docs.generator_internals_tests", "TestGeneratorHelpers"),
    "TestGeneratorScope": ("tests.unit.docs.generator_internals_tests", "TestGeneratorScope"),
    "TestIterMarkdownFiles": ("tests.unit.docs.shared_iter_tests", "TestIterMarkdownFiles"),
    "TestLoadAuditBudgets": ("tests.unit.docs.auditor_budgets_tests", "TestLoadAuditBudgets"),
    "TestMainRouting": ("tests.unit.docs.main_entry_tests", "TestMainRouting"),
    "TestMainWithFlags": ("tests.unit.docs.main_entry_tests", "TestMainWithFlags"),
    "TestMaybeWriteTodo": ("tests.unit.docs.validator_internals_tests", "TestMaybeWriteTodo"),
    "TestRunAudit": ("tests.unit.docs.main_tests", "TestRunAudit"),
    "TestRunBuild": ("tests.unit.docs.main_commands_tests", "TestRunBuild"),
    "TestRunFix": ("tests.unit.docs.main_tests", "TestRunFix"),
    "TestRunGenerate": ("tests.unit.docs.main_commands_tests", "TestRunGenerate"),
    "TestRunValidate": ("tests.unit.docs.main_commands_tests", "TestRunValidate"),
    "TestSelectedProjectNames": ("tests.unit.docs.shared_iter_tests", "TestSelectedProjectNames"),
    "TestValidateCore": ("tests.unit.docs.validator_tests", "TestValidateCore"),
    "TestValidateReport": ("tests.unit.docs.validator_tests", "TestValidateReport"),
    "TestValidateScope": ("tests.unit.docs.validator_internals_tests", "TestValidateScope"),
    "TestWriteJson": ("tests.unit.docs.shared_write_tests", "TestWriteJson"),
    "TestWriteMarkdown": ("tests.unit.docs.shared_write_tests", "TestWriteMarkdown"),
    "auditor": ("tests.unit.docs.auditor_tests", "auditor"),
    "builder": ("tests.unit.docs.builder_tests", "builder"),
    "fixer": ("tests.unit.docs.fixer_internals_tests", "fixer"),
    "gen": ("tests.unit.docs.generator_internals_tests", "gen"),
    "is_external": ("tests.unit.docs.auditor_tests", "is_external"),
    "normalize_link": ("tests.unit.docs.auditor_tests", "normalize_link"),
    "should_skip_target": ("tests.unit.docs.auditor_tests", "should_skip_target"),
    "validator": ("tests.unit.docs.validator_internals_tests", "validator"),
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


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
