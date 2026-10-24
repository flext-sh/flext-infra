# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen. Conform package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen._conform._execute_generation import (
        FlextInfraCodegenConformExecuteGenerationMixin,
    )
    from flext_infra.codegen._conform._existing_plan_governed import (
        FlextInfraCodegenConformExistingPlanGovernedMixin,
    )
    from flext_infra.codegen._conform._existing_plan_recovery import (
        FlextInfraCodegenConformExistingPlanRecoveryMixin,
    )
    from flext_infra.codegen._conform._plan_topology import (
        FlextInfraCodegenConformPlanTopologyMixin,
    )
    from flext_infra.codegen._conform.artifact_render import (
        FlextInfraCodegenConformArtifactRender,
    )
    from flext_infra.codegen._conform.beads_routes import (
        FlextInfraCodegenConformBeadsRoutes,
    )
    from flext_infra.codegen._conform.bootstrap import FlextInfraCodegenConformBootstrap
    from flext_infra.codegen._conform.context_render import (
        FlextInfraCodegenConformContextRender,
    )
    from flext_infra.codegen._conform.docs_ownership import (
        FlextInfraCodegenConformDocsOwnership,
    )
    from flext_infra.codegen._conform.execute import FlextInfraCodegenConformExecute
    from flext_infra.codegen._conform.execute_directed import (
        FlextInfraCodegenConformExecuteDirected,
    )
    from flext_infra.codegen._conform.execute_scaffold import (
        FlextInfraCodegenConformExecuteScaffold,
    )
    from flext_infra.codegen._conform.existing_plan import (
        FlextInfraCodegenConformExistingPlan,
    )
    from flext_infra.codegen._conform.file_plans import (
        FlextInfraCodegenConformFilePlans,
    )
    from flext_infra.codegen._conform.gitignore import FlextInfraCodegenConformGitignore
    from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan
    from flext_infra.codegen._conform.pyproject_policy import (
        FlextInfraCodegenConformPyprojectPolicy,
    )
    from flext_infra.codegen._conform.scaffold_plan import (
        FlextInfraCodegenConformScaffoldPlan,
    )


__all__: tuple[str, ...] = (
    "FlextInfraCodegenConformArtifactRender",
    "FlextInfraCodegenConformBeadsRoutes",
    "FlextInfraCodegenConformBootstrap",
    "FlextInfraCodegenConformContextRender",
    "FlextInfraCodegenConformDocsOwnership",
    "FlextInfraCodegenConformExecute",
    "FlextInfraCodegenConformExecuteDirected",
    "FlextInfraCodegenConformExecuteGenerationMixin",
    "FlextInfraCodegenConformExecuteScaffold",
    "FlextInfraCodegenConformExistingPlan",
    "FlextInfraCodegenConformExistingPlanGovernedMixin",
    "FlextInfraCodegenConformExistingPlanRecoveryMixin",
    "FlextInfraCodegenConformFilePlans",
    "FlextInfraCodegenConformGitignore",
    "FlextInfraCodegenConformPlan",
    "FlextInfraCodegenConformPlanTopologyMixin",
    "FlextInfraCodegenConformPyprojectPolicy",
    "FlextInfraCodegenConformScaffoldPlan",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenConformArtifactRender": ".artifact_render",
        "FlextInfraCodegenConformBeadsRoutes": ".beads_routes",
        "FlextInfraCodegenConformBootstrap": ".bootstrap",
        "FlextInfraCodegenConformContextRender": ".context_render",
        "FlextInfraCodegenConformDocsOwnership": ".docs_ownership",
        "FlextInfraCodegenConformExecute": ".execute",
        "FlextInfraCodegenConformExecuteDirected": ".execute_directed",
        "FlextInfraCodegenConformExecuteGenerationMixin": "._execute_generation",
        "FlextInfraCodegenConformExecuteScaffold": ".execute_scaffold",
        "FlextInfraCodegenConformExistingPlan": ".existing_plan",
        "FlextInfraCodegenConformExistingPlanGovernedMixin": "._existing_plan_governed",
        "FlextInfraCodegenConformExistingPlanRecoveryMixin": "._existing_plan_recovery",
        "FlextInfraCodegenConformFilePlans": ".file_plans",
        "FlextInfraCodegenConformGitignore": ".gitignore",
        "FlextInfraCodegenConformPlan": ".plan",
        "FlextInfraCodegenConformPlanTopologyMixin": "._plan_topology",
        "FlextInfraCodegenConformPyprojectPolicy": ".pyproject_policy",
        "FlextInfraCodegenConformScaffoldPlan": ".scaffold_plan",
    }),
    public_exports=__all__,
)
