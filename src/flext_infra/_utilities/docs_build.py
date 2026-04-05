"""Build helpers for docs services."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

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
            FlextInfraUtilitiesDocsBuild._run_mkdocs_api(config, site_dir)
        except (OSError, ValueError) as exc:
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
    def _run_mkdocs_api(config: Path, site_dir: Path) -> None:
        """Run MkDocs build via the Python API with lazy imports.

        Converts mkdocs-specific exceptions to ``OSError`` so callers only
        need to catch standard exception types.
        """
        from mkdocs.commands import build as _build_mod  # noqa: PLC0415
        from mkdocs.config import load_config as _raw_load  # noqa: PLC0415
        from mkdocs.exceptions import (  # noqa: PLC0415
            Abort,
            BuildError,
            ConfigurationError,
            MkDocsException,
            PluginError,
        )

        _typed_load: Callable[..., Mapping[str, bool]] = _raw_load
        _typed_build: Callable[..., None] = _build_mod.build
        try:
            site_dir.parent.mkdir(parents=True, exist_ok=True)
            config_obj: Mapping[str, bool] = _typed_load(
                config_file_path=str(config),
                site_dir=str(site_dir),
            )
            config_obj["strict"] = True
            _typed_build(config_obj, dirty=False)
        except (Abort, BuildError, ConfigurationError, MkDocsException, PluginError) as exc:
            msg = str(exc) or "mkdocs build failed"
            raise OSError(msg) from exc

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
