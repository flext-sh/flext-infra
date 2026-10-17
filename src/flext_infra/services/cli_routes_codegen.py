"""Codegen, check, and dependency CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, infra, m
from flext_infra.codegen import (
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenLayout,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMakeBootstrap,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenMiseToolchainProof,
    FlextInfraCodegenMiseToolchainRepair,
    FlextInfraCodegenProjectNew,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    FlextInfraCodegenVersionFile,
)
from flext_infra.deps import (
    FlextInfraConfigFixer,
    FlextInfraExtraPathsManager,
    FlextInfraLockIntegrityVerifier,
    FlextInfraPyprojectModernizer,
    FlextInfraRuntimeDevDependencyDetector,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraCodegenRoutes:
    """Own check, codegen, and dependency command routes."""

    codegen_routes: ClassVar[
        MutableMapping[str, t.VariadicTuple[m.Cli.ResultCommandRoute]]
    ] = {
        c.Infra.CLI_GROUP_CHECK: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run workspace quality gates",
                model_cls=m.Infra.RunCommand,
                handler=infra.check,
            ),
            m.Cli.ResultCommandRoute(
                name="fix-pyrefly-settings",
                help_text="Repair [tool.pyrefly] blocks",
                model_cls=m.Infra.FixPyreflyConfigCommand,
                handler=FlextInfraConfigFixer.execute_payload,
            ),
        ),
        c.Infra.CLI_GROUP_CODEGEN: (
            m.Cli.ResultCommandRoute(
                name="candidate-bootstrap",
                help_text="Atomically conform all declared candidate Makefiles",
                model_cls=m.Infra.CandidateBootstrapCommand,
                handler=infra.bootstrap_candidate,
                success_message="candidate bootstrap complete",
            ),
            m.Cli.ResultCommandRoute(
                name="generate",
                help_text="Generate managed projections without declaration repair",
                model_cls=m.Infra.CodegenGenerateRequest,
                handler=infra.codegen_generate,
                success_message="managed projection generation complete",
            ),
            m.Cli.ResultCommandRoute(
                name="conform",
                help_text="Conform generated project and workspace files",
                model_cls=m.Infra.CodegenConformRequest,
                handler=infra.codegen_conform,
                success_message="project conformance complete",
            ),
            m.Cli.ResultCommandRoute(
                name="footprint",
                help_text="Read the actual generation journal and plan without effects",
                model_cls=m.Infra.CodegenConformRequest,
                handler=infra.codegen_footprint,
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=handler,
                    success_message=success_message,
                )
                for route_name, help_text, model_cls, handler, success_message in (
                    (
                        "new",
                        "Create a new FLEXT project from the canonical templates",
                        FlextInfraCodegenProjectNew,
                        infra.codegen_new,
                        "project created",
                    ),
                    (
                        "init",
                        "Bootstrap the target's own declaration and canonical Makefile",
                        FlextInfraCodegenMakeBootstrap,
                        FlextInfraCodegenMakeBootstrap.execute,
                        "Makefile bootstrap complete",
                    ),
                    (
                        "lazy-init",
                        (
                            "Regenerate PEP 562 lazy-import __init__.py files as "
                            "part of the continuous gen check/apply cycle (unlike "
                            "`init`, which only bootstraps a fresh, unprovisioned "
                            "repository)"
                        ),
                        FlextInfraCodegenLazyInit,
                        FlextInfraCodegenLazyInit.execute,
                        "lazy-init complete",
                    ),
                    (
                        "census",
                        "Count namespace violations across workspace projects",
                        m.Infra.CodegenCommand,
                        infra.codegen_census,
                        None,
                    ),
                    (
                        "scaffold",
                        "Generate missing base modules in src/ and tests/",
                        FlextInfraCodegenScaffolder,
                        FlextInfraCodegenScaffolder.execute,
                        None,
                    ),
                    (
                        "auto-fix",
                        "Auto-fix namespace violations (move Finals/TypeVars)",
                        m.Infra.CodegenAutoFixCommand,
                        infra.codegen_auto_fix,
                        None,
                    ),
                    (
                        "py-typed",
                        "Create/remove PEP 561 py.typed markers",
                        FlextInfraCodegenPyTyped,
                        FlextInfraCodegenPyTyped.execute,
                        "py-typed markers updated",
                    ),
                    (
                        "pipeline",
                        "Run full codegen pipeline",
                        m.Infra.CodegenCommand,
                        infra.codegen_pipeline,
                        None,
                    ),
                    (
                        "constants-quality-gate",
                        "Run constants migration quality gate",
                        m.Infra.CodegenCommand,
                        infra.constants_quality_gate,
                        "constants quality gate passed",
                    ),
                    (
                        "consolidate",
                        "Consolidate inline constants into c.Infra.* references",
                        FlextInfraCodegenConsolidator,
                        FlextInfraCodegenConsolidator.execute,
                        None,
                    ),
                    (
                        "layout",
                        "Check/apply the canonical project layout (SSOT-driven)",
                        FlextInfraCodegenLayout,
                        FlextInfraCodegenLayout.execute,
                        "layout conformance complete",
                    ),
                    (
                        "mise-artifacts",
                        "Validate the generated Mise bundle read-only",
                        FlextInfraCodegenMiseArtifacts,
                        FlextInfraCodegenMiseArtifacts.execute,
                        "Mise artifact validation complete",
                    ),
                    (
                        "mise-proof",
                        "Prove each declared tool is the self-contained locked release",
                        FlextInfraCodegenMiseToolchainProof,
                        FlextInfraCodegenMiseToolchainProof.execute,
                        "Mise toolchain reality proof complete",
                    ),
                    (
                        "mise-repair",
                        (
                            "Reinstall one explicitly selected locked tool and prove "
                            "reality"
                        ),
                        FlextInfraCodegenMiseToolchainRepair,
                        FlextInfraCodegenMiseToolchainRepair.execute,
                        "Selected tool repaired and complete toolchain proven",
                    ),
                    (
                        "version-file",
                        "Generate __version__.py from project-metadata SSOT",
                        FlextInfraCodegenVersionFile,
                        FlextInfraCodegenVersionFile.execute,
                        "version-file generation complete",
                    ),
                )
            ),
        ),
        c.Infra.CLI_GROUP_DEPS: (
            m.Cli.ResultCommandRoute(
                name="detect",
                help_text="Detect runtime vs dev dependencies",
                model_cls=m.Infra.DetectCommand,
                handler=FlextInfraRuntimeDevDependencyDetector.execute,
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=model_cls.execute,
                )
                for route_name, help_text, model_cls in (
                    (
                        "extra-paths",
                        "Synchronize pyright/mypy extraPaths",
                        FlextInfraExtraPathsManager,
                    ),
                    (
                        "modernize",
                        "Modernize workspace pyproject files",
                        FlextInfraPyprojectModernizer,
                    ),
                    (
                        "verify-locks",
                        "Verify committed generated TOML locks parse and repeat no section",
                        FlextInfraLockIntegrityVerifier,
                    ),
                )
            ),
        ),
    }


__all__: list[str] = ["FlextInfraCodegenRoutes"]
