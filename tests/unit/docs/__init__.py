# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.docs import (
        auditor_budgets_tests as auditor_budgets_tests,
        auditor_cli_tests as auditor_cli_tests,
        auditor_links_tests as auditor_links_tests,
        auditor_scope_tests as auditor_scope_tests,
        auditor_tests as auditor_tests,
        builder_scope_tests as builder_scope_tests,
        builder_tests as builder_tests,
        fixer_internals_tests as fixer_internals_tests,
        fixer_tests as fixer_tests,
        generator_internals_tests as generator_internals_tests,
        generator_tests as generator_tests,
        init_tests as init_tests,
        main_commands_tests as main_commands_tests,
        main_entry_tests as main_entry_tests,
        main_tests as main_tests,
        shared_iter_tests as shared_iter_tests,
        shared_tests as shared_tests,
        shared_write_tests as shared_write_tests,
        validator_internals_tests as validator_internals_tests,
        validator_tests as validator_tests,
    )
    from tests.unit.docs.auditor_budgets_tests import (
        TestLoadAuditBudgets as TestLoadAuditBudgets,
    )
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli as TestAuditorMainCli,
        TestAuditorScopeFailure as TestAuditorScopeFailure,
    )
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks as TestAuditorBrokenLinks,
        TestAuditorToMarkdown as TestAuditorToMarkdown,
    )
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms as TestAuditorForbiddenTerms,
        TestAuditorScope as TestAuditorScope,
    )
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore as TestAuditorCore,
        TestAuditorNormalize as TestAuditorNormalize,
        auditor as auditor,
        is_external as is_external,
        normalize_link as normalize_link,
        should_skip_target as should_skip_target,
    )
    from tests.unit.docs.builder_scope_tests import TestBuilderScope as TestBuilderScope
    from tests.unit.docs.builder_tests import (
        TestBuilderCore as TestBuilderCore,
        builder as builder,
    )
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerMaybeFixLink as TestFixerMaybeFixLink,
        TestFixerProcessFile as TestFixerProcessFile,
        TestFixerScope as TestFixerScope,
        TestFixerToc as TestFixerToc,
        fixer as fixer,
    )
    from tests.unit.docs.fixer_tests import TestFixerCore as TestFixerCore
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers as TestGeneratorHelpers,
        TestGeneratorScope as TestGeneratorScope,
        gen as gen,
    )
    from tests.unit.docs.generator_tests import TestGeneratorCore as TestGeneratorCore
    from tests.unit.docs.init_tests import TestFlextInfraDocs as TestFlextInfraDocs
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild as TestRunBuild,
        TestRunGenerate as TestRunGenerate,
        TestRunValidate as TestRunValidate,
    )
    from tests.unit.docs.main_entry_tests import (
        TestMainRouting as TestMainRouting,
        TestMainWithFlags as TestMainWithFlags,
    )
    from tests.unit.docs.main_tests import (
        TestRunAudit as TestRunAudit,
        TestRunFix as TestRunFix,
    )
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles as TestIterMarkdownFiles,
        TestSelectedProjectNames as TestSelectedProjectNames,
    )
    from tests.unit.docs.shared_tests import (
        TestBuildScopes as TestBuildScopes,
        TestFlextInfraDocScope as TestFlextInfraDocScope,
    )
    from tests.unit.docs.shared_write_tests import (
        TestWriteJson as TestWriteJson,
        TestWriteMarkdown as TestWriteMarkdown,
    )
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers as TestAdrHelpers,
        TestMaybeWriteTodo as TestMaybeWriteTodo,
        TestValidateScope as TestValidateScope,
        validator as validator,
    )
    from tests.unit.docs.validator_tests import (
        TestValidateCore as TestValidateCore,
        TestValidateReport as TestValidateReport,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestAdrHelpers": ["tests.unit.docs.validator_internals_tests", "TestAdrHelpers"],
    "TestAuditorBrokenLinks": [
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorBrokenLinks",
    ],
    "TestAuditorCore": ["tests.unit.docs.auditor_tests", "TestAuditorCore"],
    "TestAuditorForbiddenTerms": [
        "tests.unit.docs.auditor_scope_tests",
        "TestAuditorForbiddenTerms",
    ],
    "TestAuditorMainCli": ["tests.unit.docs.auditor_cli_tests", "TestAuditorMainCli"],
    "TestAuditorNormalize": ["tests.unit.docs.auditor_tests", "TestAuditorNormalize"],
    "TestAuditorScope": ["tests.unit.docs.auditor_scope_tests", "TestAuditorScope"],
    "TestAuditorScopeFailure": [
        "tests.unit.docs.auditor_cli_tests",
        "TestAuditorScopeFailure",
    ],
    "TestAuditorToMarkdown": [
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorToMarkdown",
    ],
    "TestBuildScopes": ["tests.unit.docs.shared_tests", "TestBuildScopes"],
    "TestBuilderCore": ["tests.unit.docs.builder_tests", "TestBuilderCore"],
    "TestBuilderScope": ["tests.unit.docs.builder_scope_tests", "TestBuilderScope"],
    "TestFixerCore": ["tests.unit.docs.fixer_tests", "TestFixerCore"],
    "TestFixerMaybeFixLink": [
        "tests.unit.docs.fixer_internals_tests",
        "TestFixerMaybeFixLink",
    ],
    "TestFixerProcessFile": [
        "tests.unit.docs.fixer_internals_tests",
        "TestFixerProcessFile",
    ],
    "TestFixerScope": ["tests.unit.docs.fixer_internals_tests", "TestFixerScope"],
    "TestFixerToc": ["tests.unit.docs.fixer_internals_tests", "TestFixerToc"],
    "TestFlextInfraDocScope": [
        "tests.unit.docs.shared_tests",
        "TestFlextInfraDocScope",
    ],
    "TestFlextInfraDocs": ["tests.unit.docs.init_tests", "TestFlextInfraDocs"],
    "TestGeneratorCore": ["tests.unit.docs.generator_tests", "TestGeneratorCore"],
    "TestGeneratorHelpers": [
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorHelpers",
    ],
    "TestGeneratorScope": [
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorScope",
    ],
    "TestIterMarkdownFiles": [
        "tests.unit.docs.shared_iter_tests",
        "TestIterMarkdownFiles",
    ],
    "TestLoadAuditBudgets": [
        "tests.unit.docs.auditor_budgets_tests",
        "TestLoadAuditBudgets",
    ],
    "TestMainRouting": ["tests.unit.docs.main_entry_tests", "TestMainRouting"],
    "TestMainWithFlags": ["tests.unit.docs.main_entry_tests", "TestMainWithFlags"],
    "TestMaybeWriteTodo": [
        "tests.unit.docs.validator_internals_tests",
        "TestMaybeWriteTodo",
    ],
    "TestRunAudit": ["tests.unit.docs.main_tests", "TestRunAudit"],
    "TestRunBuild": ["tests.unit.docs.main_commands_tests", "TestRunBuild"],
    "TestRunFix": ["tests.unit.docs.main_tests", "TestRunFix"],
    "TestRunGenerate": ["tests.unit.docs.main_commands_tests", "TestRunGenerate"],
    "TestRunValidate": ["tests.unit.docs.main_commands_tests", "TestRunValidate"],
    "TestSelectedProjectNames": [
        "tests.unit.docs.shared_iter_tests",
        "TestSelectedProjectNames",
    ],
    "TestValidateCore": ["tests.unit.docs.validator_tests", "TestValidateCore"],
    "TestValidateReport": ["tests.unit.docs.validator_tests", "TestValidateReport"],
    "TestValidateScope": [
        "tests.unit.docs.validator_internals_tests",
        "TestValidateScope",
    ],
    "TestWriteJson": ["tests.unit.docs.shared_write_tests", "TestWriteJson"],
    "TestWriteMarkdown": ["tests.unit.docs.shared_write_tests", "TestWriteMarkdown"],
    "auditor": ["tests.unit.docs.auditor_tests", "auditor"],
    "auditor_budgets_tests": ["tests.unit.docs.auditor_budgets_tests", ""],
    "auditor_cli_tests": ["tests.unit.docs.auditor_cli_tests", ""],
    "auditor_links_tests": ["tests.unit.docs.auditor_links_tests", ""],
    "auditor_scope_tests": ["tests.unit.docs.auditor_scope_tests", ""],
    "auditor_tests": ["tests.unit.docs.auditor_tests", ""],
    "builder": ["tests.unit.docs.builder_tests", "builder"],
    "builder_scope_tests": ["tests.unit.docs.builder_scope_tests", ""],
    "builder_tests": ["tests.unit.docs.builder_tests", ""],
    "fixer": ["tests.unit.docs.fixer_internals_tests", "fixer"],
    "fixer_internals_tests": ["tests.unit.docs.fixer_internals_tests", ""],
    "fixer_tests": ["tests.unit.docs.fixer_tests", ""],
    "gen": ["tests.unit.docs.generator_internals_tests", "gen"],
    "generator_internals_tests": ["tests.unit.docs.generator_internals_tests", ""],
    "generator_tests": ["tests.unit.docs.generator_tests", ""],
    "init_tests": ["tests.unit.docs.init_tests", ""],
    "is_external": ["tests.unit.docs.auditor_tests", "is_external"],
    "main_commands_tests": ["tests.unit.docs.main_commands_tests", ""],
    "main_entry_tests": ["tests.unit.docs.main_entry_tests", ""],
    "main_tests": ["tests.unit.docs.main_tests", ""],
    "normalize_link": ["tests.unit.docs.auditor_tests", "normalize_link"],
    "shared_iter_tests": ["tests.unit.docs.shared_iter_tests", ""],
    "shared_tests": ["tests.unit.docs.shared_tests", ""],
    "shared_write_tests": ["tests.unit.docs.shared_write_tests", ""],
    "should_skip_target": ["tests.unit.docs.auditor_tests", "should_skip_target"],
    "validator": ["tests.unit.docs.validator_internals_tests", "validator"],
    "validator_internals_tests": ["tests.unit.docs.validator_internals_tests", ""],
    "validator_tests": ["tests.unit.docs.validator_tests", ""],
}

_EXPORTS: Sequence[str] = [
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
    "auditor_budgets_tests",
    "auditor_cli_tests",
    "auditor_links_tests",
    "auditor_scope_tests",
    "auditor_tests",
    "builder",
    "builder_scope_tests",
    "builder_tests",
    "fixer",
    "fixer_internals_tests",
    "fixer_tests",
    "gen",
    "generator_internals_tests",
    "generator_tests",
    "init_tests",
    "is_external",
    "main_commands_tests",
    "main_entry_tests",
    "main_tests",
    "normalize_link",
    "shared_iter_tests",
    "shared_tests",
    "shared_write_tests",
    "should_skip_target",
    "validator",
    "validator_internals_tests",
    "validator_tests",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
