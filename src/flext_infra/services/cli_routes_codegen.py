"""Codegen, check, and dependency CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u

from flext_infra import c, codegen, deps, infra, m, p, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraCodegenRoutes:
    """Own check, codegen, and dependency command routes."""

    @staticmethod
    def execute_upgrade_lock(request: p.Infra.WorkspaceRequest) -> p.Result[bool]:
        """Compose the lock upgrade with the shared native command runner.

        Returns:
            The lock upgrade result, or its first native failure.

        """
        return deps.FlextInfraLockIntegrityVerifier.upgrade_lock(request, u.Cli)

    @staticmethod
    def check_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
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
    ) -> t.VariadicTuple[p.Cli.ResultCommandRoute]:
        """Build the codegen group's native model and handler bindings.

        Returns:
            The ordered codegen command routes.

        """
        primary = infra.codegen_routes(provide=lambda: infra)
        if command is not None and any(route.name == command for route in primary):
            return primary
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
        return (
            *bootstrap,
            *primary,
            *remaining,
        )

    @staticmethod
    def deps_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the dependency group's native model and handler bindings.

        Returns:
            The ordered dependency command routes.

        """
        return FlextInfraUtilitiesBase.result_routes((
            (
                "upgrade-lock",
                "Upgrade the elected native UV and Mise locks without installing",
                m.Infra.WorkspaceRequest,
                FlextInfraCodegenRoutes.execute_upgrade_lock,
                "native UV and Mise locks upgraded and verified",
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
