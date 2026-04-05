"""Build helpers for docs services."""

from __future__ import annotations

from mkdocs.commands.build import build as mkdocs_build
from mkdocs.config import load_config
from mkdocs.exceptions import (
    Abort,
    BuildError,
    ConfigurationError,
    MkDocsException,
    PluginError,
)

from flext_cli import FlextCliUtilitiesJson
from flext_infra import c, m, p
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs


class FlextInfraUtilitiesDocsBuild:
    """Reusable build helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_run_mkdocs(
        scope: m.Infra.DocScope,
        *,
        runner: p.Infra.CommandRunner,
    ) -> m.Infra.DocsPhaseReport:
        """Run MkDocs directly through the MkDocs Python API for one scope."""
        config = scope.path / "mkdocs.yml"
        if not config.exists():
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result="SKIP",
                reason="mkdocs.yml not found",
                site_dir="",
                passed=True,
            )
        site_dir = (
            scope.path / c.Infra.DEFAULT_DOCS_OUTPUT_DIR / c.Infra.Directories.SITE
        ).resolve()
        if not isinstance(runner, type):
            completed = runner.run_raw(
                [
                    "mkdocs",
                    c.Infra.Directories.BUILD,
                    "--strict",
                    "-f",
                    str(config),
                    "-d",
                    str(site_dir),
                ],
                cwd=scope.path,
            )
            if completed.is_failure:
                return m.Infra.DocsPhaseReport(
                    phase="build",
                    scope=scope.name,
                    result=c.Infra.Status.FAIL,
                    reason=completed.error or "mkdocs build failed",
                    site_dir=site_dir.as_posix(),
                    passed=False,
                )
            output = completed.value
            if output.exit_code == 0:
                return m.Infra.DocsPhaseReport(
                    phase="build",
                    scope=scope.name,
                    result=c.Infra.Status.OK,
                    reason="build succeeded",
                    site_dir=site_dir.as_posix(),
                    passed=True,
                )
            reason_lines = (output.stderr or output.stdout).strip().splitlines()
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.Status.FAIL,
                reason=reason_lines[-1]
                if reason_lines
                else f"mkdocs exited {output.exit_code}",
                site_dir=site_dir.as_posix(),
                passed=False,
            )
        try:
            site_dir.parent.mkdir(parents=True, exist_ok=True)
            config_obj = load_config(
                config_file_path=str(config),
                site_dir=str(site_dir),
            )
            config_obj["strict"] = True
            mkdocs_build(config_obj, dirty=False)
        except (
            Abort,
            BuildError,
            ConfigurationError,
            MkDocsException,
            OSError,
            PluginError,
            ValueError,
        ) as exc:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.Status.FAIL,
                reason=str(exc) or "mkdocs build failed",
                site_dir=site_dir.as_posix(),
                passed=False,
            )
        return m.Infra.DocsPhaseReport(
            phase="build",
            scope=scope.name,
            result=c.Infra.Status.OK,
            reason="build succeeded",
            site_dir=site_dir.as_posix(),
            passed=True,
        )

    @staticmethod
    def docs_write_build_reports(
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Persist the standard build summary and markdown report."""
        _ = FlextCliUtilitiesJson.json_write(
            scope.report_dir / "build-summary.json",
            {c.Infra.ReportKeys.SUMMARY: report.model_dump()},
        )
        _ = FlextInfraUtilitiesDocs.write_markdown(
            scope.report_dir / "build-report.md",
            [
                "# Docs Build Report",
                "",
                f"Scope: {report.scope}",
                f"Result: {report.result}",
                f"Reason: {report.reason}",
                f"Site dir: {report.site_dir}",
            ],
        )


__all__ = ["FlextInfraUtilitiesDocsBuild"]
