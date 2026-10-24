"""Codegen, check, and dependency CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import flext_infra
from flext_infra import c, codegen, deps, m, p, r, settings, t, u
from flext_infra._pytest_clock import FlextInfraPytestClock


def execute_codegen_generate(
    request: p.Infra.CodegenGenerateRequest,
) -> p.Result[t.Cli.ResultValue]:
    """Erase the typed generation receipt for the declarative CLI route.

    Returns:
        The generation failure verbatim, or an erased success marker whose
        static route message is the CLI output.

    """
    if settings.Infra.profile:
        storage = u.Infra.refactor_report_evidence_root(request.root).unwrap()
        output = (
            storage / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        ).with_suffix(".pstats")
        output.parent.mkdir(parents=True, exist_ok=True)

        def failed(result: p.Result[p.Infra.CodegenResult]) -> bool:
            return result.failure

        generated = FlextInfraPytestClock.profile_operation(
            lambda: flext_infra.infra.codegen_generate(request),
            output,
            is_failure=failed,
        )
    else:
        generated = flext_infra.infra.codegen_generate(request)
    if generated.failure:
        return r[t.Cli.ResultValue].from_failure(generated)
    return r[t.Cli.ResultValue].ok(value=True)


def execute_codegen_conform(
    request: p.Infra.CodegenConformRequest,
) -> p.Result[t.Cli.ResultValue]:
    """Erase the typed conformance receipt for the declarative CLI route.

    Returns:
        The conformance failure verbatim, or an erased success marker whose
        static route message is the CLI output.

    """
    conformed = flext_infra.infra.codegen_conform(request)
    if conformed.failure:
        return r[t.Cli.ResultValue].from_failure(conformed)
    return r[t.Cli.ResultValue].ok(value=True)


class FlextInfraCodegenRoutes:
    """Own check, codegen, and dependency command routes."""

    @staticmethod
    def check_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the check group's native model and handler bindings.

        Returns:
            The ordered check command routes.

        """
        return (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run workspace quality gates",
                model_cls=m.Infra.RunCommand,
                handler=flext_infra.infra.check,
            ),
            m.Cli.ResultCommandRoute(
                name="integrity",
                help_text="Run the same checker over runtime and project integrity",
                model_cls=m.Infra.RunCommand,
                handler=flext_infra.infra.check_integrity,
            ),
            m.Cli.ResultCommandRoute(
                name="fix-pyrefly-settings",
                help_text="Repair [tool.pyrefly] blocks",
                model_cls=m.Infra.FixPyreflyConfigCommand,
                handler=deps.FlextInfraConfigFixer.execute_payload,
            ),
        )

    @staticmethod
    def codegen_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the codegen group's native model and handler bindings.

        Returns:
            The ordered codegen command routes.

        """
        return (
            m.Cli.ResultCommandRoute(
                name="candidate-bootstrap",
                help_text="Atomically conform all declared candidate Makefiles",
                model_cls=m.Infra.CandidateBootstrapCommand,
                handler=flext_infra.infra.bootstrap_candidate,
                success_message="candidate bootstrap complete",
            ),
            m.Cli.ResultCommandRoute(
                name="generate",
                help_text="Generate managed projections without declaration repair",
                model_cls=m.Infra.CodegenGenerateRequest,
                handler=execute_codegen_generate,
                success_message="managed projection generation complete",
            ),
            m.Cli.ResultCommandRoute(
                name="conform",
                help_text="Conform generated project and workspace files",
                model_cls=m.Infra.CodegenConformRequest,
                handler=execute_codegen_conform,
                success_message="project conformance complete",
            ),
            m.Cli.ResultCommandRoute(
                name="footprint",
                help_text=(
                    "Inspect recorded generation effects "
                    "without planning or publication"
                ),
                model_cls=m.Infra.CodegenFootprintRequest,
                handler=flext_infra.infra.codegen_footprint,
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
                        "init",
                        (
                            "Initialize an explicitly declared new target or "
                            "recover its canonical Makefile"
                        ),
                        codegen.FlextInfraCodegenMakeBootstrap,
                        codegen.FlextInfraCodegenMakeBootstrap.execute,
                        "declared target bootstrap complete",
                    ),
                    (
                        "lazy-init",
                        (
                            "Regenerate PEP 562 lazy-import __init__.py files as "
                            "part of the continuous gen check/apply cycle"
                        ),
                        codegen.FlextInfraCodegenLazyInit,
                        codegen.FlextInfraCodegenLazyInit.execute,
                        "lazy-init complete",
                    ),
                    (
                        "census",
                        "Count namespace violations across workspace projects",
                        m.Infra.CodegenCommand,
                        flext_infra.infra.codegen_census,
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
                        flext_infra.infra.codegen_auto_fix,
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
                        flext_infra.infra.constants_quality_gate,
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
                        "mise-artifacts",
                        "Validate the generated Mise bundle read-only",
                        codegen.FlextInfraCodegenMiseArtifacts,
                        codegen.FlextInfraCodegenMiseArtifacts.execute,
                        "Mise artifact validation complete",
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
                        (
                            "Reinstall one explicitly selected locked tool and prove "
                            "reality"
                        ),
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
                )
            ),
        )

    @staticmethod
    def deps_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the dependency group's native model and handler bindings.

        Returns:
            The ordered dependency command routes.

        """
        return (
            m.Cli.ResultCommandRoute(
                name="upgrade-lock",
                help_text=(
                    "Upgrade and verify the elected native UV lock without installing"
                ),
                model_cls=m.Infra.WorkspaceRequest,
                handler=deps.FlextInfraLockIntegrityVerifier.upgrade_lock,
                success_message="native UV lock upgraded and verified",
            ),
            m.Cli.ResultCommandRoute(
                name="detect",
                help_text="Detect runtime vs dev dependencies",
                model_cls=m.Infra.DetectCommand,
                handler=deps.FlextInfraRuntimeDevDependencyDetector.execute,
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
                        deps.FlextInfraExtraPathsManager,
                    ),
                    (
                        "modernize",
                        "Modernize workspace pyproject files",
                        deps.FlextInfraPyprojectModernizer,
                    ),
                    (
                        "verify-locks",
                        (
                            "Verify committed generated TOML locks parse and repeat no "
                            "section"
                        ),
                        deps.FlextInfraLockIntegrityVerifier,
                    ),
                )
            ),
        )


__all__: list[str] = ["FlextInfraCodegenRoutes"]
