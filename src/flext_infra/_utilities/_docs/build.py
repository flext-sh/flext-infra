"""Build helpers for docs services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsBase


class FlextInfraUtilitiesDocsBuild:
    """Reusable build helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_mkdocs_config_files(scope: p.Infra.DocScope) -> tuple[Path, ...]:
        """Return primary mkdocs.yml then optional product mkdocs.yaml.

        Returns:
            Primary mkdocs.yml then optional product mkdocs.yaml.

        """
        configs: list[Path] = []
        primary = scope.path / "mkdocs.yml"
        secondary = scope.path / "mkdocs.yaml"
        if primary.is_file():
            configs.append(primary)
        if secondary.is_file() and secondary.resolve() != primary.resolve():
            configs.append(secondary)
        return tuple(configs)

    @staticmethod
    def docs_run_mkdocs(scope: p.Infra.DocScope) -> p.Infra.DocsPhaseReport:
        """Run MkDocs for primary yml and optional product yaml configs.

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        configs = FlextInfraUtilitiesDocsBuild.docs_mkdocs_config_files(scope)
        if not configs:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason="mkdocs.yml not found",
                site_dir="",
                passed=False,
            )
        primary_report: p.Infra.DocsPhaseReport | None = None
        for settings in configs:
            suffix = "" if settings.suffix == ".yml" else "-product"
            report = FlextInfraUtilitiesDocsBuild._docs_run_one_mkdocs(
                scope,
                settings=settings,
                site_suffix=suffix,
            )
            if primary_report is None:
                primary_report = report
            if not report.passed:
                return report
        if primary_report is None:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason="mkdocs build produced no report",
                site_dir="",
                passed=False,
            )
        if len(configs) > 1:
            return primary_report.model_copy(
                update={
                    "reason": (
                        f"{primary_report.reason}; product mkdocs.yaml also built"
                    ),
                },
            )
        return primary_report

    @staticmethod
    def _docs_run_one_mkdocs(
        scope: p.Infra.DocScope,
        *,
        settings: Path,
        site_suffix: str,
    ) -> p.Infra.DocsPhaseReport:
        """Build one MkDocs config file into a site directory.

        ProperDocs owns strict warning accounting; its first failure escapes.

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        site_dir = (
            scope.path
            / c.Infra.DEFAULT_DOCS_OUTPUT_DIR
            / f"{c.Infra.DIR_SITE}{site_suffix}"
        ).resolve()
        FlextInfraUtilitiesDocsBuild._run_mkapi(settings, site_dir)
        return m.Infra.DocsPhaseReport(
            phase="build",
            scope=scope.name,
            result=c.Infra.ResultStatus.OK,
            reason=f"build succeeded ({settings.name})",
            site_dir=site_dir.as_posix(),
            passed=True,
            strict=True,
        )

    @staticmethod
    def _run_mkapi(settings: Path, site_dir: Path) -> None:
        """Run the docs engine's native strict build as a child process."""
        site_dir.parent.mkdir(parents=True, exist_ok=True)
        u.Cli.run_checked(
            (
                sys.executable,
                "-m",
                c.Infra.DOCS_ENGINE_MODULE,
                "build",
                "--strict",
                "--clean",
                "--config-file",
                str(settings.resolve()),
                "--site-dir",
                str(site_dir),
            ),
            cwd=settings.resolve().parent,
        ).unwrap()

    @staticmethod
    def docs_serve_mkdocs(
        scope: p.Infra.DocScope,
        *,
        dev_addr: str,
        livereload: bool,
        strict: bool,
    ) -> p.Infra.DocsPhaseReport:
        """Serve one scope through the docs engine's dev server (blocking).

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        settings = scope.path / "mkdocs.yml"
        if not settings.exists():
            return m.Infra.DocsPhaseReport(
                phase="serve",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason="mkdocs.yml not found",
                site_dir="",
                passed=False,
            )
        _ = u.Cli.run_live(
            (
                sys.executable,
                "-m",
                c.Infra.DOCS_ENGINE_MODULE,
                "serve",
                "--config-file",
                str(settings.resolve()),
                "--dev-addr",
                dev_addr,
                "--strict" if strict else "--no-strict",
                *(() if livereload else ("--no-livereload",)),
            ),
            cwd=settings.resolve().parent,
        ).unwrap()
        return m.Infra.DocsPhaseReport(
            phase="serve",
            scope=scope.name,
            result=c.Infra.ResultStatus.OK,
            reason="dev server stopped",
            site_dir="",
            passed=True,
        )

    @staticmethod
    def docs_write_build_reports(
        scope: p.Infra.DocScope,
        report: p.Infra.DocsPhaseReport,
    ) -> None:
        """Persist the standard build summary and markdown report."""
        _ = u.Cli.json_write(
            scope.report_dir / "build-summary.json",
            {c.Infra.RK_SUMMARY: report.model_dump(mode="json")},
        ).unwrap()
        _ = FlextInfraUtilitiesDocsBase.write_markdown(
            scope.report_dir / "build-report.md",
            [
                "# Docs Build Report",
                "",
                f"Scope: {report.scope}",
                f"Result: {report.result}",
                f"Reason: {report.reason}",
                f"Site dir: {report.site_dir}",
            ],
        ).unwrap()


__all__: list[str] = ["FlextInfraUtilitiesDocsBuild"]
