# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.docs.auditor_budgets_tests as _tests_unit_docs_auditor_budgets_tests

    auditor_budgets_tests = _tests_unit_docs_auditor_budgets_tests
    import tests.unit.docs.auditor_cli_tests as _tests_unit_docs_auditor_cli_tests
    from tests.unit.docs.auditor_budgets_tests import TestLoadAuditBudgets

    auditor_cli_tests = _tests_unit_docs_auditor_cli_tests
    import tests.unit.docs.auditor_links_tests as _tests_unit_docs_auditor_links_tests
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli,
        TestAuditorScopeFailure,
    )

    auditor_links_tests = _tests_unit_docs_auditor_links_tests
    import tests.unit.docs.auditor_scope_tests as _tests_unit_docs_auditor_scope_tests
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorToMarkdown,
    )

    auditor_scope_tests = _tests_unit_docs_auditor_scope_tests
    import tests.unit.docs.auditor_tests as _tests_unit_docs_auditor_tests
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms,
        TestAuditorScope,
    )

    auditor_tests = _tests_unit_docs_auditor_tests
    import tests.unit.docs.builder_scope_tests as _tests_unit_docs_builder_scope_tests
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )

    builder_scope_tests = _tests_unit_docs_builder_scope_tests
    import tests.unit.docs.builder_tests as _tests_unit_docs_builder_tests
    from tests.unit.docs.builder_scope_tests import TestBuilderScope

    builder_tests = _tests_unit_docs_builder_tests
    import tests.unit.docs.fixer_internals_tests as _tests_unit_docs_fixer_internals_tests
    from tests.unit.docs.builder_tests import TestBuilderCore, builder

    fixer_internals_tests = _tests_unit_docs_fixer_internals_tests
    import tests.unit.docs.fixer_tests as _tests_unit_docs_fixer_tests
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )

    fixer_tests = _tests_unit_docs_fixer_tests
    import tests.unit.docs.generator_internals_tests as _tests_unit_docs_generator_internals_tests
    from tests.unit.docs.fixer_tests import TestFixerCore

    generator_internals_tests = _tests_unit_docs_generator_internals_tests
    import tests.unit.docs.generator_tests as _tests_unit_docs_generator_tests
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers,
        TestGeneratorScope,
        gen,
    )

    generator_tests = _tests_unit_docs_generator_tests
    import tests.unit.docs.init_tests as _tests_unit_docs_init_tests
    from tests.unit.docs.generator_tests import TestGeneratorCore

    init_tests = _tests_unit_docs_init_tests
    import tests.unit.docs.main_commands_tests as _tests_unit_docs_main_commands_tests
    from tests.unit.docs.init_tests import TestFlextInfraDocs

    main_commands_tests = _tests_unit_docs_main_commands_tests
    import tests.unit.docs.main_entry_tests as _tests_unit_docs_main_entry_tests
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild,
        TestRunGenerate,
        TestRunValidate,
    )

    main_entry_tests = _tests_unit_docs_main_entry_tests
    import tests.unit.docs.main_tests as _tests_unit_docs_main_tests
    from tests.unit.docs.main_entry_tests import TestMainRouting, TestMainWithFlags

    main_tests = _tests_unit_docs_main_tests
    import tests.unit.docs.shared_iter_tests as _tests_unit_docs_shared_iter_tests
    from tests.unit.docs.main_tests import TestRunAudit, TestRunFix

    shared_iter_tests = _tests_unit_docs_shared_iter_tests
    import tests.unit.docs.shared_tests as _tests_unit_docs_shared_tests
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles,
        TestSelectedProjectNames,
    )

    shared_tests = _tests_unit_docs_shared_tests
    import tests.unit.docs.shared_write_tests as _tests_unit_docs_shared_write_tests
    from tests.unit.docs.shared_tests import TestBuildScopes, TestFlextInfraDocScope

    shared_write_tests = _tests_unit_docs_shared_write_tests
    import tests.unit.docs.validator_internals_tests as _tests_unit_docs_validator_internals_tests
    from tests.unit.docs.shared_write_tests import TestWriteJson, TestWriteMarkdown

    validator_internals_tests = _tests_unit_docs_validator_internals_tests
    import tests.unit.docs.validator_tests as _tests_unit_docs_validator_tests
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )

    validator_tests = _tests_unit_docs_validator_tests
    from tests.unit.docs.validator_tests import TestValidateCore, TestValidateReport

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
_LAZY_IMPORTS = {
    "TestAdrHelpers": ("tests.unit.docs.validator_internals_tests", "TestAdrHelpers"),
    "TestAuditorBrokenLinks": (
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorBrokenLinks",
    ),
    "TestAuditorCore": ("tests.unit.docs.auditor_tests", "TestAuditorCore"),
    "TestAuditorForbiddenTerms": (
        "tests.unit.docs.auditor_scope_tests",
        "TestAuditorForbiddenTerms",
    ),
    "TestAuditorMainCli": ("tests.unit.docs.auditor_cli_tests", "TestAuditorMainCli"),
    "TestAuditorNormalize": ("tests.unit.docs.auditor_tests", "TestAuditorNormalize"),
    "TestAuditorScope": ("tests.unit.docs.auditor_scope_tests", "TestAuditorScope"),
    "TestAuditorScopeFailure": (
        "tests.unit.docs.auditor_cli_tests",
        "TestAuditorScopeFailure",
    ),
    "TestAuditorToMarkdown": (
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorToMarkdown",
    ),
    "TestBuildScopes": ("tests.unit.docs.shared_tests", "TestBuildScopes"),
    "TestBuilderCore": ("tests.unit.docs.builder_tests", "TestBuilderCore"),
    "TestBuilderScope": ("tests.unit.docs.builder_scope_tests", "TestBuilderScope"),
    "TestFixerCore": ("tests.unit.docs.fixer_tests", "TestFixerCore"),
    "TestFixerProcessFile": (
        "tests.unit.docs.fixer_internals_tests",
        "TestFixerProcessFile",
    ),
    "TestFixerScope": ("tests.unit.docs.fixer_internals_tests", "TestFixerScope"),
    "TestFixerToc": ("tests.unit.docs.fixer_internals_tests", "TestFixerToc"),
    "TestFlextInfraDocScope": (
        "tests.unit.docs.shared_tests",
        "TestFlextInfraDocScope",
    ),
    "TestFlextInfraDocs": ("tests.unit.docs.init_tests", "TestFlextInfraDocs"),
    "TestGeneratorCore": ("tests.unit.docs.generator_tests", "TestGeneratorCore"),
    "TestGeneratorHelpers": (
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorHelpers",
    ),
    "TestGeneratorScope": (
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorScope",
    ),
    "TestIterMarkdownFiles": (
        "tests.unit.docs.shared_iter_tests",
        "TestIterMarkdownFiles",
    ),
    "TestLoadAuditBudgets": (
        "tests.unit.docs.auditor_budgets_tests",
        "TestLoadAuditBudgets",
    ),
    "TestMainRouting": ("tests.unit.docs.main_entry_tests", "TestMainRouting"),
    "TestMainWithFlags": ("tests.unit.docs.main_entry_tests", "TestMainWithFlags"),
    "TestMaybeWriteTodo": (
        "tests.unit.docs.validator_internals_tests",
        "TestMaybeWriteTodo",
    ),
    "TestRunAudit": ("tests.unit.docs.main_tests", "TestRunAudit"),
    "TestRunBuild": ("tests.unit.docs.main_commands_tests", "TestRunBuild"),
    "TestRunFix": ("tests.unit.docs.main_tests", "TestRunFix"),
    "TestRunGenerate": ("tests.unit.docs.main_commands_tests", "TestRunGenerate"),
    "TestRunValidate": ("tests.unit.docs.main_commands_tests", "TestRunValidate"),
    "TestSelectedProjectNames": (
        "tests.unit.docs.shared_iter_tests",
        "TestSelectedProjectNames",
    ),
    "TestValidateCore": ("tests.unit.docs.validator_tests", "TestValidateCore"),
    "TestValidateReport": ("tests.unit.docs.validator_tests", "TestValidateReport"),
    "TestValidateScope": (
        "tests.unit.docs.validator_internals_tests",
        "TestValidateScope",
    ),
    "TestWriteJson": ("tests.unit.docs.shared_write_tests", "TestWriteJson"),
    "TestWriteMarkdown": ("tests.unit.docs.shared_write_tests", "TestWriteMarkdown"),
    "auditor": ("tests.unit.docs.auditor_tests", "auditor"),
    "auditor_budgets_tests": "tests.unit.docs.auditor_budgets_tests",
    "auditor_cli_tests": "tests.unit.docs.auditor_cli_tests",
    "auditor_links_tests": "tests.unit.docs.auditor_links_tests",
    "auditor_scope_tests": "tests.unit.docs.auditor_scope_tests",
    "auditor_tests": "tests.unit.docs.auditor_tests",
    "builder": ("tests.unit.docs.builder_tests", "builder"),
    "builder_scope_tests": "tests.unit.docs.builder_scope_tests",
    "builder_tests": "tests.unit.docs.builder_tests",
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer": ("tests.unit.docs.fixer_internals_tests", "fixer"),
    "fixer_internals_tests": "tests.unit.docs.fixer_internals_tests",
    "fixer_tests": "tests.unit.docs.fixer_tests",
    "gen": ("tests.unit.docs.generator_internals_tests", "gen"),
    "generator_internals_tests": "tests.unit.docs.generator_internals_tests",
    "generator_tests": "tests.unit.docs.generator_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.docs.init_tests",
    "is_external": ("tests.unit.docs.auditor_tests", "is_external"),
    "m": ("flext_core.models", "FlextModels"),
    "main_commands_tests": "tests.unit.docs.main_commands_tests",
    "main_entry_tests": "tests.unit.docs.main_entry_tests",
    "main_tests": "tests.unit.docs.main_tests",
    "normalize_link": ("tests.unit.docs.auditor_tests", "normalize_link"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "shared_iter_tests": "tests.unit.docs.shared_iter_tests",
    "shared_tests": "tests.unit.docs.shared_tests",
    "shared_write_tests": "tests.unit.docs.shared_write_tests",
    "should_skip_target": ("tests.unit.docs.auditor_tests", "should_skip_target"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "validator": ("tests.unit.docs.validator_internals_tests", "validator"),
    "validator_internals_tests": "tests.unit.docs.validator_internals_tests",
    "validator_tests": "tests.unit.docs.validator_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
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
    "c",
    "d",
    "e",
    "fixer",
    "fixer_internals_tests",
    "fixer_tests",
    "gen",
    "generator_internals_tests",
    "generator_tests",
    "h",
    "init_tests",
    "is_external",
    "m",
    "main_commands_tests",
    "main_entry_tests",
    "main_tests",
    "normalize_link",
    "p",
    "r",
    "s",
    "shared_iter_tests",
    "shared_tests",
    "shared_write_tests",
    "should_skip_target",
    "t",
    "u",
    "validator",
    "validator_internals_tests",
    "validator_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
