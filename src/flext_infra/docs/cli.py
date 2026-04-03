"""CLI mixin for documentation commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r
from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    c,
    m,
    t,
    u,
)

if TYPE_CHECKING:
    import typer

_R = u.Infra.route  # shorthand


class FlextInfraCliDocs:
    """Docs CLI group — composed into FlextInfraCli via MRO."""

    def register_docs(self, app: typer.Typer) -> None:
        """Register documentation commands on the given Typer app."""
        auditor = FlextInfraDocAuditor()
        fixer = FlextInfraDocFixer()
        builder = FlextInfraDocBuilder()
        generator = FlextInfraDocGenerator()
        validator = FlextInfraDocValidator()
        u.Infra.register_routes(
            app,
            [
                _R(
                    "audit",
                    "Audit documentation for broken links and forbidden terms",
                    m.Infra.DocsAuditInput,
                    auditor.execute_command,
                    fail_msg="Audit failed",
                    success_msg="Audit completed successfully",
                ),
                _R(
                    "fix",
                    "Fix documentation issues",
                    m.Infra.DocsFixInput,
                    fixer.execute_command,
                    fail_msg="Fix failed",
                    success_msg="Fix completed successfully",
                ),
                _R(
                    "build",
                    "Build MkDocs sites",
                    m.Infra.DocsBuildInput,
                    builder.execute_command,
                    fail_msg="Build failed",
                    success_msg="Build completed successfully",
                ),
                _R(
                    "generate",
                    "Generate project docs",
                    m.Infra.DocsGenerateInput,
                    generator.execute_command,
                    fail_msg="Generate failed",
                    success_msg="Generate completed successfully",
                ),
                _R(
                    "validate",
                    "Validate documentation",
                    m.Infra.DocsValidateInput,
                    validator.execute_command,
                    fail_msg="Validate failed",
                    success_msg="Validate completed successfully",
                ),
            ],
        )


class FlextInfraDocsCli:
    """Declarative CLI router for documentation services.

    Retained for backward compatibility with tests that call _handle_* directly.
    New code should use FlextInfraCliDocs.register_docs() instead.
    """

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="docs",
            help_text="Documentation management services",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="docs", args=args)

    def _register_commands(self) -> None:
        u.Infra.register_routes(
            self._app,
            [
                _R(
                    "audit",
                    "Audit documentation for broken links and forbidden terms",
                    m.Infra.DocsAuditInput,
                    self._handle_audit,
                    fail_msg="Audit failed",
                    success_msg="Audit completed successfully",
                ),
                _R(
                    "fix",
                    "Fix documentation issues",
                    m.Infra.DocsFixInput,
                    self._handle_fix,
                    fail_msg="Fix failed",
                    success_msg="Fix completed successfully",
                ),
                _R(
                    "build",
                    "Build MkDocs sites",
                    m.Infra.DocsBuildInput,
                    self._handle_build,
                    fail_msg="Build failed",
                    success_msg="Build completed successfully",
                ),
                _R(
                    "generate",
                    "Generate project docs",
                    m.Infra.DocsGenerateInput,
                    self._handle_generate,
                    fail_msg="Generate failed",
                    success_msg="Generate completed successfully",
                ),
                _R(
                    "validate",
                    "Validate documentation",
                    m.Infra.DocsValidateInput,
                    self._handle_validate,
                    fail_msg="Validate failed",
                    success_msg="Validate completed successfully",
                ),
            ],
        )

    @staticmethod
    def _handle_audit(params: m.Infra.DocsAuditInput) -> r[bool]:
        return u.Infra.then_count(
            FlextInfraDocAuditor().audit(
                workspace_root=u.Infra.resolve_workspace(params),
                project=params.project,
                projects=params.projects,
                output_dir=params.output_dir,
                params=m.Infra.AuditScopeParams(
                    check="all" if params.check else "",
                    strict=params.strict,
                ),
            ),
            predicate=lambda report: not report.passed,
            fail_msg="Audit found failures",
        )

    @staticmethod
    def _handle_fix(params: m.Infra.DocsFixInput) -> r[bool]:
        return (
            FlextInfraDocFixer()
            .fix(
                workspace_root=u.Infra.resolve_workspace(params),
                project=params.project,
                projects=params.projects,
                output_dir=params.output_dir,
                apply=params.apply,
            )
            .map(lambda _: True)
        )

    @staticmethod
    def _handle_build(params: m.Infra.DocsBuildInput) -> r[bool]:
        return u.Infra.then_count(
            FlextInfraDocBuilder().build(
                workspace_root=u.Infra.resolve_workspace(params),
                project=params.project,
                projects=params.projects,
                output_dir=params.output_dir,
            ),
            predicate=lambda report: report.result == c.Infra.Status.FAIL,
            fail_msg="Build had failures",
        )

    @staticmethod
    def _handle_generate(params: m.Infra.DocsGenerateInput) -> r[bool]:
        return (
            FlextInfraDocGenerator()
            .generate(
                workspace_root=u.Infra.resolve_workspace(params),
                project=params.project,
                projects=params.projects,
                output_dir=params.output_dir,
                apply=params.apply,
            )
            .map(lambda _: True)
        )

    @staticmethod
    def _handle_validate(params: m.Infra.DocsValidateInput) -> r[bool]:
        return u.Infra.then_count(
            FlextInfraDocValidator().validate(
                workspace_root=u.Infra.resolve_workspace(params),
                project=params.project,
                projects=params.projects,
                output_dir=params.output_dir,
                check="all" if params.check else "",
                apply=params.apply,
            ),
            predicate=lambda report: report.result == c.Infra.Status.FAIL,
            fail_msg="Validate found failures",
        )
