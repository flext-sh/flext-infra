# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.validate package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.validate._pytest_diag_xml import FlextInfraPytestDiagXmlMixin
    from flext_infra.validate._skill_rule_runner import FlextInfraSkillRuleRunnerMixin
    from flext_infra.validate.cprofile_report import FlextInfraCProfileReport
    from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.loc_delta import FlextInfraLocDeltaValidator
    from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.producer import FlextInfraValidateProducer
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
    from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
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
    "FlextInfraPytestDiagXmlMixin",
    "FlextInfraPytestRunner",
    "FlextInfraRuntimeCensusValidator",
    "FlextInfraSkillRuleRunnerMixin",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraTestmonDbInspector",
    "FlextInfraTextPatternScanner",
    "FlextInfraValidateFreshImport",
    "FlextInfraValidateLazyMapFreshness",
    "FlextInfraValidateProducer",
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
        "FlextInfraPytestDiagXmlMixin": "._pytest_diag_xml",
        "FlextInfraPytestRunner": ".pytest_runner",
        "FlextInfraRuntimeCensusValidator": ".runtime_census",
        "FlextInfraSkillRuleRunnerMixin": "._skill_rule_runner",
        "FlextInfraSkillValidator": ".skill_validator",
        "FlextInfraStubSupplyChain": ".stub_chain",
        "FlextInfraTestmonDbInspector": ".testmon_db",
        "FlextInfraTextPatternScanner": ".scanner",
        "FlextInfraValidateFreshImport": ".fresh_import",
        "FlextInfraValidateLazyMapFreshness": ".lazy_map_freshness",
        "FlextInfraValidateProducer": ".producer",
        "FlextInfraValidateTestImportDag": ".test_import_dag",
    }),
    public_exports=__all__,
)
