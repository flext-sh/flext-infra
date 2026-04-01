# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.docs.auditor_budgets_tests import *
    from tests.unit.docs.auditor_cli_tests import *
    from tests.unit.docs.auditor_links_tests import *
    from tests.unit.docs.auditor_scope_tests import *
    from tests.unit.docs.auditor_tests import *
    from tests.unit.docs.builder_scope_tests import *
    from tests.unit.docs.builder_tests import *
    from tests.unit.docs.fixer_internals_tests import *
    from tests.unit.docs.fixer_tests import *
    from tests.unit.docs.generator_internals_tests import *
    from tests.unit.docs.generator_tests import *
    from tests.unit.docs.init_tests import *
    from tests.unit.docs.main_commands_tests import *
    from tests.unit.docs.main_entry_tests import *
    from tests.unit.docs.main_tests import *
    from tests.unit.docs.shared_iter_tests import *
    from tests.unit.docs.shared_tests import *
    from tests.unit.docs.shared_write_tests import *
    from tests.unit.docs.validator_internals_tests import *
    from tests.unit.docs.validator_tests import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "TestAdrHelpers": "tests.unit.docs.validator_internals_tests",
    "TestAuditorBrokenLinks": "tests.unit.docs.auditor_links_tests",
    "TestAuditorCore": "tests.unit.docs.auditor_tests",
    "TestAuditorForbiddenTerms": "tests.unit.docs.auditor_scope_tests",
    "TestAuditorMainCli": "tests.unit.docs.auditor_cli_tests",
    "TestAuditorNormalize": "tests.unit.docs.auditor_tests",
    "TestAuditorScope": "tests.unit.docs.auditor_scope_tests",
    "TestAuditorScopeFailure": "tests.unit.docs.auditor_cli_tests",
    "TestAuditorToMarkdown": "tests.unit.docs.auditor_links_tests",
    "TestBuildScopes": "tests.unit.docs.shared_tests",
    "TestBuilderCore": "tests.unit.docs.builder_tests",
    "TestBuilderScope": "tests.unit.docs.builder_scope_tests",
    "TestFixerCore": "tests.unit.docs.fixer_tests",
    "TestFixerMaybeFixLink": "tests.unit.docs.fixer_internals_tests",
    "TestFixerProcessFile": "tests.unit.docs.fixer_internals_tests",
    "TestFixerScope": "tests.unit.docs.fixer_internals_tests",
    "TestFixerToc": "tests.unit.docs.fixer_internals_tests",
    "TestFlextInfraDocScope": "tests.unit.docs.shared_tests",
    "TestFlextInfraDocs": "tests.unit.docs.init_tests",
    "TestGeneratorCore": "tests.unit.docs.generator_tests",
    "TestGeneratorHelpers": "tests.unit.docs.generator_internals_tests",
    "TestGeneratorScope": "tests.unit.docs.generator_internals_tests",
    "TestIterMarkdownFiles": "tests.unit.docs.shared_iter_tests",
    "TestLoadAuditBudgets": "tests.unit.docs.auditor_budgets_tests",
    "TestMainRouting": "tests.unit.docs.main_entry_tests",
    "TestMainWithFlags": "tests.unit.docs.main_entry_tests",
    "TestMaybeWriteTodo": "tests.unit.docs.validator_internals_tests",
    "TestRunAudit": "tests.unit.docs.main_tests",
    "TestRunBuild": "tests.unit.docs.main_commands_tests",
    "TestRunFix": "tests.unit.docs.main_tests",
    "TestRunGenerate": "tests.unit.docs.main_commands_tests",
    "TestRunValidate": "tests.unit.docs.main_commands_tests",
    "TestSelectedProjectNames": "tests.unit.docs.shared_iter_tests",
    "TestValidateCore": "tests.unit.docs.validator_tests",
    "TestValidateReport": "tests.unit.docs.validator_tests",
    "TestValidateScope": "tests.unit.docs.validator_internals_tests",
    "TestWriteJson": "tests.unit.docs.shared_write_tests",
    "TestWriteMarkdown": "tests.unit.docs.shared_write_tests",
    "auditor": "tests.unit.docs.auditor_tests",
    "auditor_budgets_tests": "tests.unit.docs.auditor_budgets_tests",
    "auditor_cli_tests": "tests.unit.docs.auditor_cli_tests",
    "auditor_links_tests": "tests.unit.docs.auditor_links_tests",
    "auditor_scope_tests": "tests.unit.docs.auditor_scope_tests",
    "auditor_tests": "tests.unit.docs.auditor_tests",
    "builder": "tests.unit.docs.builder_tests",
    "builder_scope_tests": "tests.unit.docs.builder_scope_tests",
    "builder_tests": "tests.unit.docs.builder_tests",
    "fixer": "tests.unit.docs.fixer_internals_tests",
    "fixer_internals_tests": "tests.unit.docs.fixer_internals_tests",
    "fixer_tests": "tests.unit.docs.fixer_tests",
    "gen": "tests.unit.docs.generator_internals_tests",
    "generator_internals_tests": "tests.unit.docs.generator_internals_tests",
    "generator_tests": "tests.unit.docs.generator_tests",
    "init_tests": "tests.unit.docs.init_tests",
    "is_external": "tests.unit.docs.auditor_tests",
    "main_commands_tests": "tests.unit.docs.main_commands_tests",
    "main_entry_tests": "tests.unit.docs.main_entry_tests",
    "main_tests": "tests.unit.docs.main_tests",
    "normalize_link": "tests.unit.docs.auditor_tests",
    "shared_iter_tests": "tests.unit.docs.shared_iter_tests",
    "shared_tests": "tests.unit.docs.shared_tests",
    "shared_write_tests": "tests.unit.docs.shared_write_tests",
    "should_skip_target": "tests.unit.docs.auditor_tests",
    "validator": "tests.unit.docs.validator_internals_tests",
    "validator_internals_tests": "tests.unit.docs.validator_internals_tests",
    "validator_tests": "tests.unit.docs.validator_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
