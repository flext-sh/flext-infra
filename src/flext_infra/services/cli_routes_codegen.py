"""Codegen, check, and dependency CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, infra, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenLayout,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMakeBootstrap,
    FlextInfraCodegenMiseToolchainProof,
    FlextInfraCodegenMiseToolchainRepair,
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


class FlextInfraCodegenRoutes:
    """Own check, codegen, and dependency command routes."""

    @staticmethod
    def execute_codegen_generate(
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[t.Cli.ResultValue]:
        """Report the native publication receipt for the declarative CLI route.

        Returns:
            The generation failure verbatim, or the successful route marker
            after reporting the producer's actual scope and write count.

        """
        # Profiling is admitted once, around the whole command, by the CLI entry.
        generated = infra.codegen_generate(request)
        if generated.failure:
            return r[t.Cli.ResultValue].from_failure(generated)
        receipt = generated.value
        u.Cli.info(
            f"generation receipt: repositories={len(receipt.plan.repositories)} "
            f"planned_files={len(receipt.plan.files)} "
            f"written_files={len(receipt.written_files)} "
            f"errors={len(receipt.errors)}"
        )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def execute_codegen_conform(
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[t.Cli.ResultValue]:
        """Erase the typed conformance receipt for the declarative CLI route.

        Returns:
            The conformance failure verbatim, or an erased success marker whose
            static route message is the CLI output.

        """
        conformed = infra.codegen_conform(request)
        if conformed.failure:
            return r[t.Cli.ResultValue].from_failure(conformed)
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def execute_upgrade_lock(request: p.Infra.WorkspaceRequest) -> p.Result[bool]:
        """Compose the lock upgrade with the shared native command runner.

        Returns:
            The lock upgrade result, or its first native failure.

        """
        return FlextInfraLockIntegrityVerifier.upgrade_lock(request, u.Cli)

    @staticmethod
    def check_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the check group's native model and handler bindings.

        Returns:
            The ordered check command routes.

        """
        return u.Infra.result_routes((
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
                FlextInfraConfigFixer.execute_payload,
                None,
            ),
        ))

    @staticmethod
    def codegen_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the codegen group's native model and handler bindings.

        Returns:
            The ordered codegen command routes.

        """
        return u.Infra.result_routes((
            (
                "candidate-bootstrap",
                "Atomically conform all declared candidate Makefiles",
                m.Infra.CandidateBootstrapCommand,
                infra.bootstrap_candidate,
                "candidate bootstrap complete",
            ),
            (
                "generate",
                "Generate managed projections without declaration repair",
                m.Infra.CodegenGenerateRequest,
                FlextInfraCodegenRoutes.execute_codegen_generate,
                "managed projection generation complete",
            ),
            (
                "conform",
                "Conform generated project and workspace files",
                m.Infra.CodegenConformRequest,
                FlextInfraCodegenRoutes.execute_codegen_conform,
                "project conformance complete",
            ),
            (
                "init",
                (
                    "Initialize an explicitly declared new target or recover its "
                    "canonical Makefile"
                ),
                FlextInfraCodegenMakeBootstrap,
                FlextInfraCodegenMakeBootstrap.execute,
                "declared target bootstrap complete",
            ),
            (
                "lazy-init",
                (
                    "Regenerate PEP 562 lazy-import __init__.py files as part of the "
                    "continuous gen check/apply cycle"
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
                "mise-proof",
                "Prove each declared tool is the self-contained locked release",
                FlextInfraCodegenMiseToolchainProof,
                FlextInfraCodegenMiseToolchainProof.execute,
                "Mise toolchain reality proof complete",
            ),
            (
                "mise-repair",
                "Reinstall one explicitly selected locked tool and prove reality",
                FlextInfraCodegenMiseToolchainRepair,
                FlextInfraCodegenMiseToolchainRepair.execute,
                "Selected tool installation and complete toolchain verified",
            ),
            (
                "version-file",
                "Generate __version__.py from project-metadata SSOT",
                FlextInfraCodegenVersionFile,
                FlextInfraCodegenVersionFile.execute,
                "version-file generation complete",
            ),
        ))

    @staticmethod
    def deps_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the dependency group's native model and handler bindings.

        Returns:
            The ordered dependency command routes.

        """
        return u.Infra.result_routes((
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
                FlextInfraRuntimeDevDependencyDetector.execute,
                None,
            ),
            (
                "extra-paths",
                "Synchronize pyright/mypy extraPaths",
                FlextInfraExtraPathsManager,
                FlextInfraExtraPathsManager.execute,
                None,
            ),
            (
                "modernize",
                "Modernize workspace pyproject files",
                FlextInfraPyprojectModernizer,
                FlextInfraPyprojectModernizer.execute,
                None,
            ),
            (
                "verify-locks",
                "Verify committed generated TOML locks parse and repeat no section",
                FlextInfraLockIntegrityVerifier,
                FlextInfraLockIntegrityVerifier.execute,
                None,
            ),
        ))


__all__: list[str] = ["FlextInfraCodegenRoutes"]
