"""Build helpers for docs services."""

from __future__ import annotations

from collections.abc import (
    Callable,
    MutableMapping,
)
from pathlib import Path

import mkdocs.commands.build
import mkdocs.config
import mkdocs.exceptions
from flext_cli import u

from flext_infra import FlextInfraUtilitiesDocs, c, m, p


class FlextInfraUtilitiesDocsBuild:
    """Reusable build helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_run_mkdocs(
        scope: m.Infra.DocScope,
        *,
        runner: p.Cli.CommandRunner,
    ) -> m.Infra.DocsPhaseReport:
        """Run MkDocs directly through the MkDocs Python API for one scope."""
        settings = scope.path / "mkdocs.yml"
        if not settings.exists():
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result="SKIP",
                reason="mkdocs.yml not found",
                site_dir="",
                passed=True,
            )
        site_dir = (
            scope.path / c.Infra.DEFAULT_DOCS_OUTPUT_DIR / c.Infra.DIR_SITE
        ).resolve()
        if not isinstance(runner, type):
            completed = runner.run_raw(
                [
                    "mkdocs",
                    c.Infra.DIR_BUILD,
                    "--strict",
                    "-f",
                    str(settings),
                    "-d",
                    str(site_dir),
                ],
                cwd=scope.path,
            )
            if completed.failure:
                return m.Infra.DocsPhaseReport(
                    phase="build",
                    scope=scope.name,
                    result=c.Infra.ResultStatus.FAIL,
                    reason=completed.error or "mkdocs build failed",
                    site_dir=site_dir.as_posix(),
                    passed=False,
                )
            output = completed.value
            if output.exit_code == 0:
                return m.Infra.DocsPhaseReport(
                    phase="build",
                    scope=scope.name,
                    result=c.Infra.ResultStatus.OK,
                    reason="build succeeded",
                    site_dir=site_dir.as_posix(),
                    passed=True,
                )
            reason_lines = (output.stderr or output.stdout).strip().splitlines()
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason=reason_lines[-1]
                if reason_lines
                else f"mkdocs exited {output.exit_code}",
                site_dir=site_dir.as_posix(),
                passed=False,
            )
        try:
            FlextInfraUtilitiesDocsBuild._run_mkdocs_api(settings, site_dir)
        except (OSError, ValueError) as exc:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason=str(exc) or "mkdocs build failed",
                site_dir=site_dir.as_posix(),
                passed=False,
            )
        return m.Infra.DocsPhaseReport(
            phase="build",
            scope=scope.name,
            result=c.Infra.ResultStatus.OK,
            reason="build succeeded",
            site_dir=site_dir.as_posix(),
            passed=True,
        )

    @staticmethod
    def _run_mkdocs_api(settings: Path, site_dir: Path) -> None:
        """Run MkDocs build via the Python API with lazy imports.

        Converts mkdocs-specific exceptions to ``OSError`` so callers only
        need to catch standard exception types.
        """
        load: Callable[..., MutableMapping[str, bool]] = getattr(
            mkdocs.config, "load_config"
        )
        build: Callable[..., None] = mkdocs.commands.build.build
        try:
            site_dir.parent.mkdir(parents=True, exist_ok=True)
            config_obj: MutableMapping[str, bool] = load(
                config_file_path=str(settings),
                site_dir=str(site_dir),
            )
            config_obj["strict"] = True
            build(config_obj, dirty=False)
        except (
            mkdocs.exceptions.Abort,
            mkdocs.exceptions.BuildError,
            mkdocs.exceptions.ConfigurationError,
            mkdocs.exceptions.MkDocsException,
            mkdocs.exceptions.PluginError,
        ) as exc:
            msg = str(exc) or "mkdocs build failed"
            raise OSError(msg) from exc

    @staticmethod
    def docs_write_build_reports(
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Persist the standard build summary and markdown report."""
        _ = u.Cli.json_write(
            scope.report_dir / "build-summary.json",
            {c.Infra.RK_SUMMARY: report.model_dump()},
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


__all__: list[str] = ["FlextInfraUtilitiesDocsBuild"]
