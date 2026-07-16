"""Validate command CLI routes for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m, p
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles
from flext_infra.validate.inventory import FlextInfraInventoryService
from flext_infra.validate.lazy_map_freshness import FlextInfraValidateLazyMapFreshness
from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
from flext_infra.validate.metadata_discipline import (
    FlextInfraValidateMetadataDiscipline,
)
from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator
from flext_infra.validate.scanner import FlextInfraTextPatternScanner
from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator
from flext_infra.validate.skill_validator import FlextInfraSkillValidator
from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist

VALIDATE_COMMAND_ROUTES: tuple[p.Cli.ResultCommandRoute, ...] = tuple(
    m.Cli.ResultCommandRoute(
        name=route_name, help_text=help_text, model_cls=model_cls, handler=handler
    )
    for route_name, help_text, model_cls, handler in (
        (
            "basemk-validate",
            "Validate base.mk sync",
            FlextInfraBaseMkValidator,
            lambda params, mc=FlextInfraBaseMkValidator: mc.execute_command(params),
        ),
        (
            "inventory",
            "Generate scripts inventory",
            FlextInfraInventoryService,
            lambda params, mc=FlextInfraInventoryService: mc.execute_command(params),
        ),
        (
            "runtime-census",
            "Post-import Beartype enforcement census for flext_* modules",
            FlextInfraRuntimeCensusValidator,
            lambda params, mc=FlextInfraRuntimeCensusValidator: mc.execute_command(
                params
            ),
        ),
        (
            "pytest-diag",
            "Extract pytest diagnostics",
            FlextInfraPytestDiagExtractor,
            lambda params, mc=FlextInfraPytestDiagExtractor: mc.execute_command(params),
        ),
        (
            "scan",
            "Scan text files for patterns",
            FlextInfraTextPatternScanner,
            lambda params, mc=FlextInfraTextPatternScanner: mc.execute_command(params),
        ),
        (
            "skill-validate",
            "Validate a skill",
            FlextInfraSkillValidator,
            lambda params, mc=FlextInfraSkillValidator: mc.execute_command(params),
        ),
        (
            "silent-failure",
            "Validate silent failure sentinel returns",
            FlextInfraSilentFailureValidator,
            lambda params, mc=FlextInfraSilentFailureValidator: mc.execute_command(
                params
            ),
        ),
        (
            "stub-validate",
            "Validate stub supply chain",
            FlextInfraStubSupplyChain,
            lambda params, mc=FlextInfraStubSupplyChain: mc.execute_command(params),
        ),
        (
            "fresh-import",
            "Guard 7: fresh-process import smoke test",
            FlextInfraValidateFreshImport,
            lambda params, mc=FlextInfraValidateFreshImport: mc.execute_command(params),
        ),
        (
            "import-cycles",
            "Guard 1: ROPE-backed import cycle detector",
            FlextInfraValidateImportCycles,
            lambda params, mc=FlextInfraValidateImportCycles: mc.execute_command(
                params
            ),
        ),
        (
            "lazy-map-freshness",
            "Guard 2/3: lazy-map freshness validator",
            FlextInfraValidateLazyMapFreshness,
            lambda params, mc=FlextInfraValidateLazyMapFreshness: mc.execute_command(
                params
            ),
        ),
        (
            "namespace",
            "Guard: static namespace rules (NS-000..003) via rope",
            FlextInfraNamespaceValidator,
            lambda params, mc=FlextInfraNamespaceValidator: mc.execute_command(params),
        ),
        (
            "tier-whitelist",
            "Guard 5: tier-whitelist/abstraction-boundary enforcer",
            FlextInfraValidateTierWhitelist,
            lambda params, mc=FlextInfraValidateTierWhitelist: mc.execute_command(
                params
            ),
        ),
        (
            "metadata-discipline",
            "Guard 8: centralized metadata parser discipline",
            FlextInfraValidateMetadataDiscipline,
            lambda params, mc=FlextInfraValidateMetadataDiscipline: mc.execute_command(
                params
            ),
        ),
        (
            "manual-cmd",
            "Manual-command blocker (§5): pre-commit config drift gate",
            FlextInfraManualCommandValidator,
            lambda params, mc=FlextInfraManualCommandValidator: mc.execute_command(
                params
            ),
        ),
    )
)

__all__: list[str] = ["VALIDATE_COMMAND_ROUTES"]
