"""Codegen, check, and dependency CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, codegen, deps, infra, m, p, u
from flext_infra._utilities import FlextInfraUtilitiesBase


class FlextInfraCodegenRoutes:
    """Own check, codegen, and dependency command routes."""

    @staticmethod
    def execute_repair_mise_platforms(
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[bool]:
        """Compose the Mise platform repair with the shared native command runner.

        Returns:
            The Mise platform repair result, or its first native failure.

        """
        return deps.FlextInfraLockIntegrityVerifier.repair_mise_platforms(
            request, u.Cli
        )

    @staticmethod
    def execute_cooldown_admission(
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[bool]:
        """Compose the cooldown admission with the shared native command runner.

        Returns:
            Success once every requirement is inside the window, or every refusal.

        """
        return deps.FlextInfraCooldownAdmission.admit(request, u.Cli)

    @staticmethod
    def execute_upg_bounds(
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[bool]:
        """Write the upg-owned bounds from each governed project's resolved lock.

        Returns:
            Success once every owned bound equals its locked version.

        """
        return deps.FlextInfraCooldownAdmission.record_bounds(request)

    @staticmethod
    def check_routes() -> tuple[p.Cli.ResultCommandRoute, ...]:
        """Build the check group's native model and handler bindings.

        Returns:
            The ordered check command routes.

        """
        return FlextInfraUtilitiesBase.result_routes((
            (
                c.Infra.VERB_RUN,
                "Run workspace quality gates",
                m.Infra.RunCommand,
                infra.check,
                None,
            ),
            (
                "integrity",
                "Run the same checker over runtime and project integrity",
                m.Infra.RunCommand,
                infra.check_integrity,
                None,
            ),
            (
                "fix-pyrefly-settings",
                "Repair [tool.pyrefly] blocks",
                m.Infra.FixPyreflyConfigCommand,
                deps.FlextInfraConfigFixer.execute_payload,
                None,
            ),
        ))

    @staticmethod
    def codegen_routes(
        *, command: str | None = None
    ) -> tuple[p.Cli.ResultCommandRoute, ...]:
        """Build the codegen group's native model and handler bindings.

        Returns:
            The ordered codegen command routes.

        """
        bootstrap = FlextInfraUtilitiesBase.result_routes((
            (
                "candidate-bootstrap",
                "Atomically conform all declared candidate Makefiles",
                m.Infra.CandidateBootstrapCommand,
                infra.bootstrap_candidate,
                "candidate bootstrap complete",
            ),
        ))
        remaining = FlextInfraUtilitiesBase.result_routes((
            (
                "init",
                (
                    "Initialize an explicitly declared new target or recover its "
                    "canonical Makefile"
                ),
                codegen.FlextInfraCodegenMakeBootstrap,
                codegen.FlextInfraCodegenMakeBootstrap.execute,
                "declared target bootstrap complete",
            ),
            (
                "lazy-init",
                (
                    "Regenerate PEP 562 lazy-import __init__.py files as part of the "
                    "continuous gen check/apply cycle"
                ),
                codegen.FlextInfraCodegenLazyInit,
                codegen.FlextInfraCodegenLazyInit.execute,
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
                codegen.FlextInfraCodegenScaffolder,
                codegen.FlextInfraCodegenScaffolder.execute,
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
                codegen.FlextInfraCodegenPyTyped,
                codegen.FlextInfraCodegenPyTyped.execute,
                "py-typed markers updated",
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
                codegen.FlextInfraCodegenConsolidator,
                codegen.FlextInfraCodegenConsolidator.execute,
                None,
            ),
            (
                "layout",
                "Check/apply the canonical project layout (SSOT-driven)",
                codegen.FlextInfraCodegenLayout,
                codegen.FlextInfraCodegenLayout.execute,
                "layout conformance complete",
            ),
            (
                "mise-proof",
                "Prove each declared tool is the self-contained locked release",
                codegen.FlextInfraCodegenMiseToolchainProof,
                codegen.FlextInfraCodegenMiseToolchainProof.execute,
                "Mise toolchain reality proof complete",
            ),
            (
                "mise-repair",
                "Reinstall one explicitly selected locked tool and prove reality",
                codegen.FlextInfraCodegenMiseToolchainRepair,
                codegen.FlextInfraCodegenMiseToolchainRepair.execute,
                "Selected tool installation and complete toolchain verified",
            ),
            (
                "version-file",
                "Generate __version__.py from project-metadata SSOT",
                codegen.FlextInfraCodegenVersionFile,
                codegen.FlextInfraCodegenVersionFile.execute,
                "version-file generation complete",
            ),
        ))
        secondary = (*bootstrap, *remaining)
        if command is not None and any(route.name == command for route in secondary):
            return secondary
        return (*bootstrap, *infra.codegen_routes(provide=lambda: infra), *remaining)

    @staticmethod
    def deps_routes() -> tuple[p.Cli.ResultCommandRoute, ...]:
        """Build the dependency group's native model and handler bindings.

        Returns:
            The ordered dependency command routes.

        """
        return FlextInfraUtilitiesBase.result_routes((
            (
                "repair-mise-platforms",
                "Lock the governed Mise tools missing a declared platform",
                m.Infra.WorkspaceRequest,
                FlextInfraCodegenRoutes.execute_repair_mise_platforms,
                "native Mise platform repair completed",
            ),
            (
                "cooldown-admission",
                "Lower upg-owned bounds into the uv cooldown; report every refusal",
                m.Infra.WorkspaceRequest,
                FlextInfraCodegenRoutes.execute_cooldown_admission,
                "every declared requirement is inside the cooldown",
            ),
            (
                "upg-bounds",
                "Write the upg-owned floors and pins from the resolved locks",
                m.Infra.WorkspaceRequest,
                FlextInfraCodegenRoutes.execute_upg_bounds,
                "upg-owned bounds match the resolved locks",
            ),
            (
                "detect",
                "Detect runtime vs dev dependencies",
                m.Infra.DetectCommand,
                deps.FlextInfraRuntimeDevDependencyDetector.execute,
                None,
            ),
            (
                "extra-paths",
                "Synchronize pyright/mypy extraPaths",
                deps.FlextInfraExtraPathsManager,
                deps.FlextInfraExtraPathsManager.execute,
                None,
            ),
            (
                "modernize",
                "Modernize workspace pyproject files",
                deps.FlextInfraPyprojectModernizer,
                deps.FlextInfraPyprojectModernizer.execute,
                None,
            ),
            (
                "verify-locks",
                "Verify committed generated TOML locks parse and repeat no section",
                deps.FlextInfraLockIntegrityVerifier,
                deps.FlextInfraLockIntegrityVerifier.execute,
                None,
            ),
        ))


__all__: list[str] = ["FlextInfraCodegenRoutes"]
