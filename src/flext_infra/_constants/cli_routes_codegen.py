"""Codegen, check, basemk, and deps CLI routes for flext-infra."""

from __future__ import annotations

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from flext_infra.codegen.pyproject_keys import FlextInfraCodegenPyprojectKeys
from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
from flext_infra.constants import c
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.fixers.orchestrator import FlextInfraEnforcementFixerOrchestrator
from flext_infra.models import m

# NOTE (multi-agent, mro-wkii.17.9): deps no longer exposes path-sync;
# codegen consumes the pure u.Infra pyproject renderer internally.
CODEGEN_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
    c.Infra.CLI_GROUP_BASEMK: (
        m.Cli.ResultCommandRoute(
            name="generate",
            help_text="Generate base.mk content from the canonical template",
            model_cls=FlextInfraBaseMkGenerator,
            handler=lambda params: params.execute(),
            success_message="base.mk generation complete",
        ),
    ),
    c.Infra.CLI_GROUP_CHECK: (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Run workspace quality gates",
            model_cls=m.Infra.RunCommand,
            handler=FlextInfraWorkspaceChecker.execute_command,
        ),
        m.Cli.ResultCommandRoute(
            name="fix-pyrefly-settings",
            help_text="Repair [tool.pyrefly] blocks",
            model_cls=m.Infra.FixPyreflyConfigCommand,
            handler=FlextInfraConfigFixer.execute_command,
        ),
        m.Cli.ResultCommandRoute(
            name="fix-enforcement",
            help_text="Auto-fix enforcement-catalog violations",
            model_cls=m.Infra.FixEnforcementCommand,
            handler=FlextInfraEnforcementFixerOrchestrator.execute_command,
        ),
    ),
    c.Infra.CLI_GROUP_CODEGEN: tuple(
        m.Cli.ResultCommandRoute(
            name=route_name,
            help_text=help_text,
            model_cls=model_cls,
            handler=lambda params, mc=model_cls: mc.execute_command(params),
            success_message=success_message,
        )
        for route_name, help_text, model_cls, success_message in (
            # NOTE (multi-agent, mro-wkii.14 / agent: codegen): ``new`` is the
            # project-creation entry point; keep it first so it surfaces at the
            # top of ``codegen --help``. Template/manifest fixes share this lane.
            (
                "new",
                "Create a new FLEXT project from the canonical templates",
                FlextInfraCodegenProjectNew,
                "project created",
            ),
            (
                "init",
                "Generate/refresh PEP 562 lazy-import __init__.py files",
                FlextInfraCodegenLazyInit,
                "init complete",
            ),
            (
                "census",
                "Count namespace violations across workspace projects",
                FlextInfraCodegenCensus,
                None,
            ),
            (
                "scaffold",
                "Generate missing base modules in src/ and tests/",
                FlextInfraCodegenScaffolder,
                None,
            ),
            (
                "auto-fix",
                "Auto-fix namespace violations (move Finals/TypeVars)",
                FlextInfraCodegenFixer,
                None,
            ),
            (
                "py-typed",
                "Create/remove PEP 561 py.typed markers",
                FlextInfraCodegenPyTyped,
                "py-typed markers updated",
            ),
            (
                "pipeline",
                "Run full codegen pipeline",
                FlextInfraCodegenPipeline,
                None,
            ),
            (
                "constants-quality-gate",
                "Run constants migration quality gate",
                FlextInfraCodegenQualityGate,
                "constants quality gate passed",
            ),
            (
                "consolidate",
                "Consolidate inline constants into c.Infra.* references",
                FlextInfraCodegenConsolidator,
                None,
            ),
            (
                "pyproject-keys",
                "Generate [tool.flext.*] tables in pyproject.toml",
                FlextInfraCodegenPyprojectKeys,
                "pyproject-keys generation complete",
            ),
            (
                "version-file",
                "Generate __version__.py from project-metadata SSOT",
                FlextInfraCodegenVersionFile,
                "version-file generation complete",
            ),
        )
    ),
    c.Infra.CLI_GROUP_DEPS: (
        *(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
            )
            for route_name, help_text, model_cls in (
                (
                    "detect",
                    "Detect runtime vs dev dependencies",
                    FlextInfraRuntimeDevDependencyDetector,
                ),
                (
                    "extra-paths",
                    "Synchronize pyright/mypy extraPaths",
                    FlextInfraExtraPathsManager,
                ),
                (
                    "internal-sync",
                    "Synchronize internal FLEXT dependencies",
                    FlextInfraInternalDependencySyncService,
                ),
                (
                    "modernize",
                    "Modernize workspace pyproject files",
                    FlextInfraPyprojectModernizer,
                ),
            )
        ),
    ),
}

__all__: list[str] = []
