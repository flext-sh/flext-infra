"""Root configuration namespaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsDepsToolConfig
from flext_infra._models._config import (
    FlextInfraModelsConfigArtifact,
    FlextInfraModelsConfigContract,
    FlextInfraModelsConfigRelease,
    FlextInfraModelsConfigStatic,
)


class FlextInfraModelsConfigRoot:
    """Own the root configuration namespaces."""

    class Infra(FlextInfraModelsConfigContract.ConfigContract):
        """Complete flext-infra configuration namespace."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project distribution name")]
        initial_project_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Version seeded into a newly scaffolded project"),
        ]
        codegen: Annotated[
            FlextInfraModelsConfigArtifact.CodegenConfigSpec,
            m.Field(description="Unified project and workspace codegen contract"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument,
            m.Field(description="Validated lint, typecheck, and scaffold policy"),
        ]
        source_scan: Annotated[
            FlextInfraModelsConfigStatic.SourceScanSpec,
            m.Field(description="Production-only source discovery contract"),
        ]
        rope: FlextInfraModelsConfigStatic.RopePreferencesSpec = m.Field(
            description="Native source-engine preference policy"
        )
        mutation_lock: Annotated[
            FlextInfraModelsConfigStatic.MutationLockSpec,
            m.Field(description="Bounded wait for a mutation scope lock"),
        ]
        gate_admission: Annotated[
            FlextInfraModelsConfigStatic.GateAdmissionSpec,
            m.Field(description="Host-wide FIFO admission for heavy gates"),
        ]
        release: Annotated[
            FlextInfraModelsConfigRelease.ReleasePolicySpec,
            m.Field(description="Release protocol policy"),
        ]
        refactor_csv_campaigns: Annotated[
            FlextInfraModelsConfigArtifact.RefactorCsvCampaignsSpec,
            m.Field(
                description="Declared CSV-driven rename campaigns for the mod verb",
            ),
        ]

    class Root(FlextInfraModelsConfigContract.ConfigContract, frozen=False):
        """Root payload deep-merged from flext-infra config files.

        Not frozen: the ``Infra`` namespace is a read-write attribute, exactly
        as its structural protocol declares it.
        """

        Infra: Annotated[
            FlextInfraModelsConfigRoot.Infra,
            m.Field(description="Validated flext-infra namespace"),
        ]


__all__: list[str] = ["FlextInfraModelsConfigRoot"]
