"""Build helpers for docs services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import mkdocs.commands.build
import mkdocs.commands.serve
import mkdocs.config
from flext_cli import u

from flext_infra import c, m, p
from flext_infra._utilities import FlextInfraUtilitiesDocs

if TYPE_CHECKING:
    from types import ModuleType

    from flext_infra import t


class FlextInfraUtilitiesDocsBuild:
    """Reusable build helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_mkdocs_config_files(scope: m.Infra.DocScope) -> t.VariadicTuple[Path]:
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
    def docs_run_mkdocs(scope: m.Infra.DocScope) -> m.Infra.DocsPhaseReport:
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
        primary_report: m.Infra.DocsPhaseReport | None = None
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
        scope: m.Infra.DocScope,
        *,
        settings: Path,
        site_suffix: str,
    ) -> m.Infra.DocsPhaseReport:
        """Build one MkDocs config file into a site directory.

        MkDocs owns strict warning accounting; its first failure escapes.

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        site_dir = (
            scope.path
            / c.Infra.DEFAULT_DOCS_OUTPUT_DIR
            / f"{c.Infra.DIR_SITE}{site_suffix}"
        ).resolve()
        FlextInfraUtilitiesDocsBuild._run_mkdocs_api(settings, site_dir)
        return m.Infra.DocsPhaseReport(
            phase="build",
            scope=scope.name,
            result=c.Infra.ResultStatus.OK,
            reason=f"build succeeded ({settings.name})",
            site_dir=site_dir.as_posix(),
            passed=True,
        )

    @staticmethod
    def _run_mkdocs_api(settings: Path, site_dir: Path) -> None:
        """Validate and build through the typed public MkDocs SDK."""
        site_dir.parent.mkdir(parents=True, exist_ok=True)
        config_obj = FlextInfraUtilitiesDocsBuild._config_sdk(
            mkdocs.config,
        ).load_config(
            config_file=str(settings),
            site_dir=str(site_dir),
            strict=True,
        )
        mkdocs.commands.build.build(config_obj, dirty=False)

    @staticmethod
    def docs_serve_mkdocs(
        scope: m.Infra.DocScope,
        *,
        dev_addr: str,
        livereload: bool,
        strict: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Serve one scope through the MkDocs Python serve API (blocking).

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
        FlextInfraUtilitiesDocsBuild._serve_sdk(mkdocs.commands.serve).serve(
            config_file=str(settings),
            livereload=livereload,
            dev_addr=dev_addr,
            strict=strict,
        )
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
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Persist the standard build summary and markdown report."""
        _ = u.Cli.json_write(
            scope.report_dir / "build-summary.json",
            {c.Infra.RK_SUMMARY: report.model_dump()},
        ).unwrap()
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
        ).unwrap()

    @staticmethod
    def _config_sdk(module: ModuleType) -> p.Infra.MkDocsConfigModule:
        """Validate the native SDK configuration dependency before effects.

        Returns:
            The native module through its required configuration port.

        Raises:
            TypeError: If the dependency lacks its declared operation.
        """
        if isinstance(module, p.Infra.MkDocsConfigModule):
            return module
        message = "MkDocs configuration module does not satisfy its public contract"
        raise TypeError(message)

    @staticmethod
    def _serve_sdk(module: ModuleType) -> p.Infra.MkDocsServeModule:
        """Validate the native SDK serve dependency before effects.

        Returns:
            The native module through its required serve port.

        Raises:
            TypeError: If the dependency lacks its declared operation.
        """
        if isinstance(module, p.Infra.MkDocsServeModule):
            return module
        message = "MkDocs serve module does not satisfy its public contract"
        raise TypeError(message)


__all__: list[str] = ["FlextInfraUtilitiesDocsBuild"]
