"""Pipeline pass helpers for the codegen fixer service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, u
from flext_infra.codegen._fixer_lint import FlextInfraCodegenFixerLintMixin
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer

_log = u.fetch_logger(__name__)


class FlextInfraCodegenFixerPassesMixin(FlextInfraCodegenFixerLintMixin):
    """Private pipeline passes for codegen fixer composition."""

    @staticmethod
    def _run_mro_migration(ctx: p.Infra.FixContext, project_path: Path) -> None:
        """Run the MRO migrator and accumulate fixed/skipped violations."""
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_path).run(
            target="all", apply=True, gates=(c.Infra.LINT,)
        )
        _log.info(
            "mro_migration_complete",
            project=project_path.name,
            migrations=len(report.migrations),
        )
        ctx.files_modified |= {
            *(migration.file for migration in report.migrations),
            *(rewrite.file for rewrite in report.rewrites),
        }
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=migration.module,
                rule="MRO",
                line=1,
                message=(
                    f"migrated {', '.join(migration.moved_symbols) or 'symbols'}"
                    " into facade MRO"
                ),
                fixable=True,
            )
            for migration in report.migrations
        )
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=rewrite.file,
                rule="MRO-REWRITE",
                line=1,
                message=f"rewrote {rewrite.replacements} consumer references",
                fixable=True,
            )
            for rewrite in report.rewrites
        )
        ctx.violations_skipped.extend(
            m.Infra.CensusViolation(
                module=project_path.name,
                rule="MRO",
                line=0,
                message=error,
                fixable=False,
            )
            for error in report.errors
        )

    @staticmethod
    def _run_namespace_enforcement(ctx: p.Infra.FixContext, project_path: Path) -> None:
        """Run namespace enforcement and record any unresolved violations."""
        enforcement = FlextInfraNamespaceEnforcer(workspace_root=project_path).enforce(
            apply=True, gates=(c.Infra.LINT,)
        )
        violating_projects = tuple(
            project_report
            for project_report in enforcement.projects
            if project_report.has_violations
        )
        if not violating_projects:
            return
        _log.warning(
            "namespace_enforcement_failed",
            project=project_path.name,
            error="violations remain after namespace enforcement",
        )
        ctx.violations_skipped.extend(
            m.Infra.CensusViolation(
                module=project_report.project,
                rule="NAMESPACE",
                line=0,
                message="violations remain after namespace enforcement",
                fixable=False,
            )
            for project_report in violating_projects
        )

    @staticmethod
    def _run_lazy_init_regeneration(
        ctx: p.Infra.FixContext, project_path: Path
    ) -> None:
        """Regenerate lazy ``__init__.py`` files and record skip on errors."""
        lazy_generator = FlextInfraCodegenLazyInit(workspace_root=project_path)
        lazy_errors = lazy_generator.generate_inits(check_only=False)
        ctx.files_modified |= set(lazy_generator.modified_files)
        if lazy_errors > 0:
            ctx.skip(
                module=project_path.name,
                rule="LAZY-INIT",
                line=0,
                message=f"lazy propagation finished with {lazy_errors} errors",
            )


__all__: list[str] = ["FlextInfraCodegenFixerPassesMixin"]
