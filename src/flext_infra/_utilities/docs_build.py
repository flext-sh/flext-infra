"""Build helpers for docs services."""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from importlib import import_module
from pathlib import Path
from types import ModuleType

from flext_cli import u
from flext_infra import c, m, p
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs


class FlextInfraUtilitiesDocsBuild:
    """Reusable build helpers exposed through ``u.Infra``."""

    @staticmethod
    def _module_callable(module: ModuleType, name: str) -> Callable[..., object]:
        """Return a named callable from a lazily loaded module."""
        value: object = getattr(module, name)
        if callable(value):
            return value
        msg = f"{module.__name__}.{name} is not callable"
        raise OSError(msg)

    @staticmethod
    def _mkdocs_exception_types(module: ModuleType) -> tuple[type[BaseException], ...]:
        """Return MkDocs exception classes from a lazily loaded module."""
        names = (
            "Abort",
            "BuildError",
            "ConfigurationError",
            "MkDocsException",
            "PluginError",
        )
        errors: list[type[BaseException]] = []
        for name in names:
            value: object = getattr(module, name)
            if not isinstance(value, type) or not issubclass(value, BaseException):
                msg = f"{module.__name__}.{name} is not an exception type"
                raise OSError(msg)
            errors.append(value)
        return tuple(errors)

    @staticmethod
    def _load_mkdocs_config(
        load: Callable[..., object], settings: Path, site_dir: Path
    ) -> MutableMapping[str, object]:
        """Load and validate a MkDocs config mapping."""
        config_raw = load(config_file_path=str(settings), site_dir=str(site_dir))
        if not isinstance(config_raw, MutableMapping):
            msg = "mkdocs.config.load_config did not return a mutable mapping"
            raise OSError(msg)
        return config_raw

    @staticmethod
    def docs_run_mkdocs(
        scope: m.Infra.DocScope, *, runner: p.Cli.CommandRunner
    ) -> p.Infra.DocsPhaseReport:
        """Run MkDocs directly through the MkDocs Python API for one scope."""
        settings = scope.path / "mkdocs.yml"
        if not settings.exists():
            result = m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result="SKIP",
                reason="mkdocs.yml not found",
                site_dir="",
                passed=True,
            )
        else:
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
                    result = m.Infra.DocsPhaseReport(
                        phase="build",
                        scope=scope.name,
                        result=c.Infra.ResultStatus.FAIL,
                        reason=completed.error or "mkdocs build failed",
                        site_dir=site_dir.as_posix(),
                        passed=False,
                    )
                else:
                    output = completed.value
                    if output.exit_code == 0:
                        result = m.Infra.DocsPhaseReport(
                            phase="build",
                            scope=scope.name,
                            result=c.Infra.ResultStatus.OK,
                            reason="build succeeded",
                            site_dir=site_dir.as_posix(),
                            passed=True,
                        )
                    else:
                        reason_lines = (
                            (output.stderr or output.stdout).strip().splitlines()
                        )
                        result = m.Infra.DocsPhaseReport(
                            phase="build",
                            scope=scope.name,
                            result=c.Infra.ResultStatus.FAIL,
                            reason=reason_lines[-1]
                            if reason_lines
                            else f"mkdocs exited {output.exit_code}",
                            site_dir=site_dir.as_posix(),
                            passed=False,
                        )
            else:
                try:
                    FlextInfraUtilitiesDocsBuild._run_mkdocs_api(settings, site_dir)
                except c.EXC_OS_VALUE as exc:
                    result = m.Infra.DocsPhaseReport(
                        phase="build",
                        scope=scope.name,
                        result=c.Infra.ResultStatus.FAIL,
                        reason=str(exc) or "mkdocs build failed",
                        site_dir=site_dir.as_posix(),
                        passed=False,
                    )
                else:
                    result = m.Infra.DocsPhaseReport(
                        phase="build",
                        scope=scope.name,
                        result=c.Infra.ResultStatus.OK,
                        reason="build succeeded",
                        site_dir=site_dir.as_posix(),
                        passed=True,
                    )
        return result

    @staticmethod
    def _run_mkdocs_api(settings: Path, site_dir: Path) -> None:
        """Run MkDocs build via the Python API with lazy imports.

        Converts mkdocs-specific exceptions to ``OSError`` so callers only
        need to catch standard exception types.
        """
        mkdocs_build = import_module("mkdocs.commands.build")
        mkdocs_config = import_module("mkdocs.config")
        mkdocs_exceptions = import_module("mkdocs.exceptions")
        load = FlextInfraUtilitiesDocsBuild._module_callable(
            mkdocs_config, "load_config"
        )
        build = FlextInfraUtilitiesDocsBuild._module_callable(mkdocs_build, "build")
        mkdocs_error_types = FlextInfraUtilitiesDocsBuild._mkdocs_exception_types(
            mkdocs_exceptions
        )
        site_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            config_obj = FlextInfraUtilitiesDocsBuild._load_mkdocs_config(
                load, settings, site_dir
            )
            config_obj["strict"] = True
            _ = build(config_obj, dirty=False)
        except mkdocs_error_types as exc:
            msg = str(exc) or "mkdocs build failed"
            raise OSError(msg) from exc

    @staticmethod
    def docs_serve_mkdocs(
        scope: m.Infra.DocScope, *, dev_addr: str, livereload: bool, strict: bool
    ) -> p.Infra.DocsPhaseReport:
        """Serve one scope through the MkDocs Python serve API (blocking)."""
        settings = scope.path / "mkdocs.yml"
        if not settings.exists():
            return m.Infra.DocsPhaseReport(
                phase="serve",
                scope=scope.name,
                result="SKIP",
                reason="mkdocs.yml not found",
                site_dir="",
                passed=True,
            )
        try:
            serve_module = import_module("mkdocs.commands.serve")
            serve_fn = FlextInfraUtilitiesDocsBuild._module_callable(
                serve_module, "serve"
            )
            serve_fn(
                config_file=str(settings),
                livereload=livereload,
                dev_addr=dev_addr,
                strict=strict,
            )
        except c.EXC_OS_VALUE as exc:
            return m.Infra.DocsPhaseReport(
                phase="serve",
                scope=scope.name,
                result=c.Infra.ResultStatus.FAIL,
                reason=str(exc) or "mkdocs serve failed",
                site_dir="",
                passed=False,
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
        scope: m.Infra.DocScope, report: m.Infra.DocsPhaseReport
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
