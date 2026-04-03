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
    from tests.unit.docs import (
        auditor_budgets_tests,
        auditor_cli_tests,
        auditor_links_tests,
        auditor_scope_tests,
        auditor_tests,
        builder_scope_tests,
        builder_tests,
        fixer_internals_tests,
        fixer_tests,
        generator_internals_tests,
        generator_tests,
        init_tests,
        main_commands_tests,
        main_entry_tests,
        main_tests,
        shared_iter_tests,
        shared_tests,
        shared_write_tests,
        validator_internals_tests,
        validator_tests,
    )
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

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
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
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer": "tests.unit.docs.fixer_internals_tests",
    "fixer_internals_tests": "tests.unit.docs.fixer_internals_tests",
    "fixer_tests": "tests.unit.docs.fixer_tests",
    "gen": "tests.unit.docs.generator_internals_tests",
    "generator_internals_tests": "tests.unit.docs.generator_internals_tests",
    "generator_tests": "tests.unit.docs.generator_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.docs.init_tests",
    "is_external": "tests.unit.docs.auditor_tests",
    "m": ("flext_core.models", "FlextModels"),
    "main_commands_tests": "tests.unit.docs.main_commands_tests",
    "main_entry_tests": "tests.unit.docs.main_entry_tests",
    "main_tests": "tests.unit.docs.main_tests",
    "normalize_link": "tests.unit.docs.auditor_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "shared_iter_tests": "tests.unit.docs.shared_iter_tests",
    "shared_tests": "tests.unit.docs.shared_tests",
    "shared_write_tests": "tests.unit.docs.shared_write_tests",
    "should_skip_target": "tests.unit.docs.auditor_tests",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "validator": "tests.unit.docs.validator_internals_tests",
    "validator_internals_tests": "tests.unit.docs.validator_internals_tests",
    "validator_tests": "tests.unit.docs.validator_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
