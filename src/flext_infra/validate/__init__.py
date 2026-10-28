# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package.

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
    from flext_infra.validate._pytest.diag_xml import FlextInfraValidatePytestDiagXml
    from flext_infra.validate._pytest_runner.base import FlextInfraPytestRunnerBase
    from flext_infra.validate._pytest_runner.command import (
        FlextInfraPytestRunnerCommand,
    )
    from flext_infra.validate._pytest_runner.execution import (
        FlextInfraPytestRunnerExecution,
    )
    from flext_infra.validate._pytest_runner.reports import (
        FlextInfraPytestRunnerReports,
    )
    from flext_infra.validate._skill.rule_runner import (
        FlextInfraValidateSkillRuleRunner,
    )
    from flext_infra.validate.cprofile_report import FlextInfraCProfileReport
    from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.loc_delta import FlextInfraLocDeltaValidator
    from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest import FlextInfraValidatePytest
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.skill import FlextInfraValidateSkill
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.validate.test_import_dag import FlextInfraValidateTestImportDag
    from flext_infra.validate.testmon_db import FlextInfraTestmonDbInspector


__all__: tuple[str, ...] = (
    "FlextInfraCProfileReport",
    "FlextInfraInventoryService",
    "FlextInfraLocDeltaValidator",
    "FlextInfraManualCommandValidator",
    "FlextInfraNamespaceValidator",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPytestRunner",
    "FlextInfraPytestRunnerBase",
    "FlextInfraPytestRunnerCommand",
    "FlextInfraPytestRunnerExecution",
    "FlextInfraPytestRunnerReports",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraTestmonDbInspector",
    "FlextInfraTextPatternScanner",
    "FlextInfraValidateFreshImport",
    "FlextInfraValidateLazyMapFreshness",
    "FlextInfraValidatePytest",
    "FlextInfraValidatePytestDiagXml",
    "FlextInfraValidateSkill",
    "FlextInfraValidateSkillRuleRunner",
    "FlextInfraValidateTestImportDag",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCProfileReport": ".cprofile_report",
        "FlextInfraInventoryService": ".inventory",
        "FlextInfraLocDeltaValidator": ".loc_delta",
        "FlextInfraManualCommandValidator": ".manual_command",
        "FlextInfraNamespaceValidator": ".namespace_validator",
        "FlextInfraPytestDiagExtractor": ".pytest_diag",
        "FlextInfraPytestRunner": ".pytest_runner",
        "FlextInfraPytestRunnerBase": "._pytest_runner.base",
        "FlextInfraPytestRunnerCommand": "._pytest_runner.command",
        "FlextInfraPytestRunnerExecution": "._pytest_runner.execution",
        "FlextInfraPytestRunnerReports": "._pytest_runner.reports",
        "FlextInfraSkillValidator": ".skill_validator",
        "FlextInfraStubSupplyChain": ".stub_chain",
        "FlextInfraTestmonDbInspector": ".testmon_db",
        "FlextInfraTextPatternScanner": ".scanner",
        "FlextInfraValidateFreshImport": ".fresh_import",
        "FlextInfraValidateLazyMapFreshness": ".lazy_map_freshness",
        "FlextInfraValidatePytest": ".pytest",
        "FlextInfraValidatePytestDiagXml": "._pytest.diag_xml",
        "FlextInfraValidateSkill": ".skill",
        "FlextInfraValidateSkillRuleRunner": "._skill.rule_runner",
        "FlextInfraValidateTestImportDag": ".test_import_dag",
    }),
    public_exports=__all__,
)
