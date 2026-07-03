"""Canonical CLI route tables for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
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
from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer
from flext_infra.models import m
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)
from flext_infra.refactor.census import FlextInfraRefactorCensus
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.refactor.modernize_orchestrator import FlextInfraModernizeOrchestrator
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from flext_infra.refactor.wrapper_root_namespace import (
    FlextInfraWrapperRootNamespaceRefactor,
)
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.transformers.cli_modernizer import FlextInfraRefactorCliModernizer
from flext_infra.transformers.logging_modernizer import (
    FlextInfraRefactorLoggingModernizer,
)
from flext_infra.transformers.pattern_modernizer import (
    FlextInfraRefactorPatternModernizer,
)
from flext_infra.transformers.pydantic_modernizer import (
    FlextInfraRefactorPydanticModernizer,
)
from flext_infra.transformers.result_di_modernizer import (
    FlextInfraRefactorResultDiModernizer,
)
from flext_infra.transformers.tests_modernizer import FlextInfraRefactorTestsModernizer
from flext_infra.utilities import u
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles
from flext_infra.validate.inventory import FlextInfraInventoryService
from flext_infra.validate.lazy_map_freshness import FlextInfraValidateLazyMapFreshness
from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
from flext_infra.validate.metadata_discipline import (
    FlextInfraValidateMetadataDiscipline,
)
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator
from flext_infra.validate.scanner import FlextInfraTextPatternScanner
from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator
from flext_infra.validate.skill_validator import FlextInfraSkillValidator
from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.sync import FlextInfraSyncService

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
            handler=lambda params: FlextInfraWorkspaceChecker.execute_command(params),
        ),
        m.Cli.ResultCommandRoute(
            name="fix-pyrefly-settings",
            help_text="Repair [tool.pyrefly] blocks",
            model_cls=m.Infra.FixPyreflyConfigCommand,
            handler=lambda params: FlextInfraConfigFixer.execute_command(params),
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
        # path-sync uses ``u.Infra.execute_command`` instead of the model's
        # own classmethod (single-callable contract owned by utilities).
        m.Cli.ResultCommandRoute(
            name="path-sync",
            help_text="Rewrite internal FLEXT dependency paths",
            model_cls=m.Infra.PathSyncCommand,
            handler=lambda params: u.Infra.execute_command(params),
        ),
    ),
}

VALIDATE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
    c.Infra.CLI_GROUP_DOCS: tuple(
        m.Cli.ResultCommandRoute(
            name=route_name,
            help_text=help_text,
            model_cls=model_cls,
            handler=lambda params, mc=model_cls: mc.execute_command(params),
            success_message=success_message,
        )
        for route_name, help_text, model_cls, success_message in (
            (
                "audit",
                "Audit documentation for broken links and forbidden terms",
                FlextInfraDocAuditor,
                "Audit completed successfully",
            ),
            (
                "fix",
                "Fix documentation issues",
                FlextInfraDocFixer,
                "Fix completed successfully",
            ),
            (
                "build",
                "Build MkDocs sites",
                FlextInfraDocBuilder,
                "Build completed successfully",
            ),
            (
                "generate",
                "Generate project docs",
                FlextInfraDocGenerator,
                "Generate completed successfully",
            ),
            (
                "validate",
                "Validate documentation",
                FlextInfraDocValidator,
                "Validate completed successfully",
            ),
        )
    ),
    c.Infra.CLI_GROUP_GITHUB: (
        m.Cli.ResultCommandRoute(
            name="workflows",
            help_text="Sync GitHub workflow files across workspace",
            model_cls=m.Infra.GithubWorkflowSyncRequest,
            handler=u.Infra.sync_github_workflows,
        ),
        m.Cli.ResultCommandRoute(
            name=c.Infra.LINT_SECTION,
            help_text="Lint GitHub workflow files",
            model_cls=m.Infra.GithubWorkflowLintRequest,
            handler=u.Infra.lint_github_workflows,
        ),
        m.Cli.ResultCommandRoute(
            name=c.Infra.PR,
            help_text="Manage pull requests for a single project",
            model_cls=m.Infra.GithubPullRequestRequest,
            handler=u.Infra.run_github_pull_request,
        ),
        m.Cli.ResultCommandRoute(
            name="pr-workspace",
            help_text="Manage pull requests across workspace projects",
            model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
            handler=u.Infra.run_github_workspace_pull_requests,
        ),
    ),
    c.Infra.CLI_GROUP_MAINTENANCE: (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Enforce Python version constraints",
            model_cls=FlextInfraPythonVersionEnforcer,
            handler=lambda params: FlextInfraPythonVersionEnforcer.execute_command(
                params
            ),
            success_message="Maintenance completed",
        ),
    ),
    c.Infra.CLI_GROUP_VALIDATE: tuple(
        m.Cli.ResultCommandRoute(
            name=route_name,
            help_text=help_text,
            model_cls=model_cls,
            handler=lambda params, mc=model_cls: mc.execute_command(params),
        )
        for route_name, help_text, model_cls in (
            (
                "basemk-validate",
                "Validate base.mk sync",
                FlextInfraBaseMkValidator,
            ),
            (
                "inventory",
                "Generate scripts inventory",
                FlextInfraInventoryService,
            ),
            (
                "runtime-census",
                "Post-import Beartype enforcement census for flext_* modules",
                FlextInfraRuntimeCensusValidator,
            ),
            (
                "pytest-diag",
                "Extract pytest diagnostics",
                FlextInfraPytestDiagExtractor,
            ),
            (
                "scan",
                "Scan text files for patterns",
                FlextInfraTextPatternScanner,
            ),
            (
                "skill-validate",
                "Validate a skill",
                FlextInfraSkillValidator,
            ),
            (
                "silent-failure",
                "Validate silent failure sentinel returns",
                FlextInfraSilentFailureValidator,
            ),
            (
                "stub-validate",
                "Validate stub supply chain",
                FlextInfraStubSupplyChain,
            ),
            (
                "fresh-import",
                "Guard 7: fresh-process import smoke test",
                FlextInfraValidateFreshImport,
            ),
            (
                "import-cycles",
                "Guard 1: ROPE-backed import cycle detector",
                FlextInfraValidateImportCycles,
            ),
            (
                "lazy-map-freshness",
                "Guard 2/3: lazy-map freshness validator",
                FlextInfraValidateLazyMapFreshness,
            ),
            (
                "tier-whitelist",
                "Guard 5: tier-whitelist/abstraction-boundary enforcer",
                FlextInfraValidateTierWhitelist,
            ),
            (
                "metadata-discipline",
                "Guard 8: centralized metadata parser discipline",
                FlextInfraValidateMetadataDiscipline,
            ),
            (
                "manual-cmd",
                "Manual-command blocker (§5): pre-commit config drift gate",
                FlextInfraManualCommandValidator,
            ),
        )
    ),
}

WORKSPACE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
    c.Infra.CLI_GROUP_REFACTOR: (
        # ``migrate-mro`` and ``namespace-enforce`` register one input model
        # but dispatch to a different orchestrator's classmethod; the rest
        # follow the model_cls.execute_command default.
        m.Cli.ResultCommandRoute(
            name="migrate-mro",
            help_text="Migrate loose declarations into MRO facade classes",
            model_cls=m.Infra.RefactorMigrateMroInput,
            handler=lambda params: FlextInfraRefactorMigrateToClassMRO.execute_command(
                params
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="namespace-enforce",
            help_text=(
                "Scan workspace for namespace governance violations "
                "(--diff is NOT read-only: it applies rewrites, captures "
                "the diff, then restores originals)"
            ),
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(params),
        ),
        *(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
            )
            for route_name, help_text, model_cls in (
                (
                    "census",
                    "Run a Rope-only workspace census for Python objects",
                    FlextInfraRefactorCensus,
                ),
                (
                    "accessor-migrate",
                    "Preview or apply automated get_/set_/is_ migration",
                    FlextInfraAccessorMigrationOrchestrator,
                ),
            )
        ),
        m.Cli.ResultCommandRoute(
            name="wrapper-root-namespace",
            help_text=(
                "Normalize wrapper alias imports to wrapper root and "
                "flatten *.Core.Tests paths"
            ),
            model_cls=FlextInfraWrapperRootNamespaceRefactor,
            handler=lambda params: params.execute(),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-patterns",
            help_text="Fix print(), pdb, bare except and open() encoding in library code",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPatternModernizer,
                description="pattern modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-pydantic",
            help_text="Migrate Pydantic v1/legacy patterns to Pydantic v2",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPydanticModernizer,
                description="pydantic modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-logging",
            help_text="Migrate logging usage to u.fetch_logger",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorLoggingModernizer,
                description="logging modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-result-di",
            help_text=(
                "Migrate result-flow and dependency-injector patterns "
                "to FLEXT canonical forms"
            ),
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorResultDiModernizer,
                description="result/DI modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-cli",
            help_text=(
                "Remove banned CLI helper imports and route print() "
                "to cli.display_text()"
            ),
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorCliModernizer,
                description="cli modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-tests",
            help_text="Migrate unittest.TestCase tests to FLEXT test helpers",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorTestsModernizer,
                description="tests modernizer",
            ),
        ),
    ),
    c.Infra.CLI_GROUP_RELEASE: (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Run release orchestration CLI flow",
            model_cls=FlextInfraReleaseOrchestrator,
            handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                params
            ),
            success_message="Release completed successfully",
        ),
    ),
    c.Infra.CLI_GROUP_WORKSPACE: tuple(
        m.Cli.ResultCommandRoute(
            name=route_name,
            help_text=help_text,
            model_cls=model_cls,
            handler=lambda params, mc=model_cls: mc.execute_command(params),
        )
        for route_name, help_text, model_cls in (
            (
                "detect",
                "Detect workspace or standalone mode",
                FlextInfraWorkspaceDetector,
            ),
            (
                "sync",
                "Sync base.mk to project root",
                FlextInfraSyncService,
            ),
            (
                "orchestrate",
                "Run make verb across projects",
                FlextInfraOrchestratorService,
            ),
            (
                "migrate",
                "Migrate workspace projects to flext_infra tooling",
                FlextInfraProjectMigrator,
            ),
        )
    ),
}

__all__: list[str] = ["CODEGEN_ROUTES", "VALIDATE_ROUTES", "WORKSPACE_ROUTES"]
