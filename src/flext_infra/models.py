"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from flext_core import FlextModels
from flext_infra._utilities._models import FlextInfraUtilitiesModels
from flext_infra.basemk._models import FlextInfraBasemkModels
from flext_infra.check._models import FlextInfraCheckModels
from flext_infra.codegen._models import FlextInfraCodegenModels
from flext_infra.deps._models import FlextInfraDepsModels
from flext_infra.docs._models import FlextInfraDocsModels
from flext_infra.github._models import FlextInfraGithubModels
from flext_infra.refactor._models import FlextInfraRefactorModels
from flext_infra.release._models import FlextInfraReleaseModels
from flext_infra.validate._models import FlextInfraCoreModels
from flext_infra.workspace._models import FlextInfraWorkspaceModels


class FlextInfraModels(FlextModels):
    class Infra(
        FlextInfraUtilitiesModels,
        FlextInfraBasemkModels,
        FlextInfraCheckModels,
        FlextInfraCodegenModels,
        FlextInfraDepsModels,
        FlextInfraDocsModels,
        FlextInfraGithubModels,
        FlextInfraRefactorModels,
        FlextInfraReleaseModels,
        FlextInfraCoreModels,
        FlextInfraWorkspaceModels,
    ):
        class ReleaseOrchestratorConfig(BaseModel):
            """Configuration for release workflow execution."""

            workspace_root: Annotated[
                Path,
                Field(description="Workspace root path for release execution"),
            ]
            version: Annotated[
                str,
                Field(description="Release version for execution", min_length=1),
            ]
            tag: Annotated[
                str,
                Field(description="Release tag name", min_length=1),
            ]
            phases: Annotated[
                list[str],
                Field(description="Ordered list of phases to execute"),
            ]
            project_names: Annotated[
                list[str] | None,
                Field(default=None, description="Optional project list scope"),
            ]
            dry_run: Annotated[
                bool,
                Field(default=False, description="Skip mutating operations when true"),
            ]
            push: Annotated[
                bool,
                Field(default=False, description="Push branch and tag when true"),
            ]
            dev_suffix: Annotated[
                bool,
                Field(default=False, description="Use -dev suffix during versioning"),
            ]
            create_branches: Annotated[
                bool,
                Field(
                    default=True,
                    description="Create release branches before phases",
                ),
            ]
            next_dev: Annotated[
                bool,
                Field(
                    default=False,
                    description="Bump to next dev version after release",
                ),
            ]
            next_bump: Annotated[
                str,
                Field(default="minor", description="Semver bump type for next dev"),
            ]

        class ReleasePhaseDispatchConfig(BaseModel):
            """Configuration for single release phase dispatch."""

            phase: Annotated[
                str,
                Field(description="Phase name to dispatch", min_length=1),
            ]
            workspace_root: Annotated[
                Path,
                Field(description="Workspace root path for phase execution"),
            ]
            version: Annotated[
                str,
                Field(description="Release version for the phase", min_length=1),
            ]
            tag: Annotated[
                str,
                Field(description="Release tag for the phase", min_length=1),
            ]
            project_names: Annotated[
                list[str],
                Field(default_factory=list, description="Scoped project names"),
            ]
            dry_run: Annotated[
                bool,
                Field(default=False, description="Dry-run mode for the phase"),
            ]
            push: Annotated[
                bool,
                Field(default=False, description="Push flag for publish phase"),
            ]
            dev_suffix: Annotated[
                bool,
                Field(default=False, description="Dev suffix flag for version phase"),
            ]


m = FlextInfraModels

__all__ = ["FlextInfraModels", "m"]
