"""Runtime execution for dependency detector CLI."""

from __future__ import annotations

import os
from collections.abc import Callable, MutableMapping, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, t, u


class FlextInfraDependencyDetectorRuntime:
    """Runtime executor for dependency detection pipeline."""

    def __init__(
        self,
        detector: p.Infra.DetectorRuntime,
        workspace_report_factory: Callable[..., p.Infra.WorkspaceReport],
        dependency_limits_factory: Callable[..., m.Infra.DependencyLimitsInfo],
        pip_check_factory: Callable[..., m.Infra.PipCheckReport],
    ) -> None:
        self._detector = detector
        self._workspace_report_factory = workspace_report_factory
        self._dependency_limits_factory = dependency_limits_factory
        self._pip_check_factory = pip_check_factory

    def run(self, argv: t.StrSequence | None = None) -> r[int]:
        """Execute dependency detection and generate workspace report."""
        detector = self._detector
        limits_default = Path(__file__).resolve().parent / "dependency_limits.toml"
        parser = detector.parser(limits_default)
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        root: Path = cli.workspace
        venv_bin = root / c.Infra.Paths.VENV_BIN_REL
        projects_result = detector.deps.discover_project_paths(
            root,
            projects_filter=detector.project_filter(cli),
        )
        if projects_result.is_failure:
            return r[int].fail(projects_result.error or "project discovery failed")
        projects: Sequence[Path] = projects_result.value
        if not projects:
            detector.log.error("deps_no_projects_found")
            return r[int].ok(2)
        if not (venv_bin / c.Infra.DEPTRY).exists():
            detector.log.error(
                "deps_deptry_missing",
                path=str(venv_bin / c.Infra.DEPTRY),
            )
            return r[int].ok(3)
        apply_typings = bool(args.apply_typings)
        do_typings = bool(args.typings) or apply_typings
        limits_path = Path(args.limits) if args.limits else limits_default
        projects_report: MutableMapping[
            str,
            MutableMapping[str, t.Infra.InfraValue],
        ] = {}
        report_model = self._workspace_report_factory(
            workspace=str(root),
            projects=projects_report,
            pip_check=None,
            dependency_limits=None,
        )
        deps_service = detector.deps
        typing_deps: p.Infra.TypingsDepsService | None = None
        if do_typings:
            if not isinstance(deps_service, p.Infra.TypingsDepsService):
                return r[int].fail("typing dependency detection service unavailable")
            typing_deps = deps_service  # narrowed by isinstance above
            if (
                typing_deps is None
            ):  # pragma: no cover — unreachable after isinstance guard
                return r[int].fail("typing dependency detection service unavailable")
            limits_data = typing_deps.load_dependency_limits(limits_path)
            if limits_data:
                python_cfg = limits_data.get(c.Infra.PYTHON)
                python_version = (
                    str(python_cfg.get(c.Infra.VERSION))
                    if u.is_mapping(python_cfg)
                    and python_cfg.get(c.Infra.VERSION) is not None
                    else None
                )
                report_model.dependency_limits = self._dependency_limits_factory(
                    python_version=python_version,
                    limits_path=str(limits_path),
                )
        for project_path in projects:
            project_name = project_path.name
            if not args.quiet:
                detector.log.info("deps_deptry_running", project=project_name)
            deptry_result = deps_service.run_deptry(project_path, venv_bin)
            if deptry_result.is_failure:
                return r[int].fail(deptry_result.error or "deptry run failed")
            issues, _ = deptry_result.value
            project_payload = deps_service.build_project_report(project_name, issues)
            dumped: MutableMapping[str, t.Infra.InfraValue] = dict(
                project_payload.model_dump(),
            )
            projects_report[project_name] = dumped
            if do_typings and (project_path / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir():
                if typing_deps is None:
                    return r[int].fail(
                        "typing dependency detection service unavailable",
                    )
                if not args.quiet:
                    detector.log.info(
                        "deps_typings_detect_running",
                        project=project_name,
                    )
                typings_result = typing_deps.get_required_typings(
                    project_path,
                    venv_bin,
                    limits_path=limits_path,
                )
                if typings_result.is_failure:
                    return r[int].fail(
                        typings_result.error or "typing dependency detection failed",
                    )
                typings_report = typings_result.value
                projects_report[project_name][c.Infra.Directories.TYPINGS] = (
                    typings_report.model_dump()
                )
                to_add: t.StrSequence = typings_report.to_add
                if apply_typings and to_add and cli.apply:
                    env = {
                        **os.environ,
                        "VIRTUAL_ENV": str(venv_bin.parent),
                        "PATH": f"{venv_bin}:{os.environ.get('PATH', '')}",
                    }
                    for package in to_add:
                        run = detector.runner.run_raw(
                            [
                                c.Infra.POETRY,
                                "add",
                                "--group",
                                c.Infra.Directories.TYPINGS,
                                package,
                            ],
                            cwd=project_path,
                            timeout=c.Infra.Timeouts.MEDIUM,
                            env=env,
                        )
                        if run.is_failure:
                            detector.log.warning(
                                "deps_typings_add_failed",
                                project=project_name,
                                package=package,
                            )
                        else:
                            run_output: m.Infra.CommandOutput = run.value
                            if run_output.exit_code != 0:
                                detector.log.warning(
                                    "deps_typings_add_failed",
                                    project=project_name,
                                    package=package,
                                )
        pip_ok = True
        if not args.no_pip_check:
            if not isinstance(deps_service, p.Infra.PipCheckDepsService):
                return r[int].fail("pip-check dependency detection service unavailable")
            if not args.quiet:
                detector.log.info("deps_pip_check_running")
            pip_result = deps_service.run_pip_check(root, venv_bin)
            if pip_result.is_failure:
                return r[int].fail(pip_result.error or "pip check failed")
            pip_lines, pip_exit = pip_result.value
            pip_ok = pip_exit == 0
            report_model.pip_check = self._pip_check_factory(ok=pip_ok, lines=pip_lines)
        report_payload = report_model.model_dump()
        if cli.output_format == "json":
            return r[int].ok(0)
        out_path: Path | None = None
        if args.output:
            out_path = Path(args.output)
        elif cli.apply:
            report_dir = detector.reporting.get_report_dir(
                root,
                c.Infra.PROJECT,
                c.Infra.DEPENDENCIES,
            )
            try:
                report_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return r[int].fail(f"failed to create report directory: {exc}")
            out_path = report_dir / "detect-runtime-dev-latest.json"
        if out_path is not None and not cli.dry_run:
            write_result = detector.json.write_json(out_path, report_payload)
            if write_result.is_failure:
                return r[int].fail(write_result.error or "failed to write report")
            if not args.quiet:
                detector.log.info("deps_report_written", path=str(out_path))
        total_issues = 0
        for payload in projects_report.values():
            deptry_obj = payload.get(c.Infra.DEPTRY)
            if u.is_mapping(deptry_obj):
                deptry_payload = u.Infra.validate(
                    t.Infra.INFRA_MAPPING_ADAPTER,
                    deptry_obj,
                    default={},
                )
                if not deptry_payload:
                    continue
                raw_count_obj: t.Infra.InfraValue = deptry_payload.get("raw_count", 0)
                if isinstance(raw_count_obj, int):
                    total_issues += raw_count_obj
        if not args.quiet:
            detector.log.info(
                "deps_summary",
                projects=len(projects),
                deptry_issues=total_issues,
                pip_check=c.Infra.ReportKeys.OK if pip_ok else "FAIL",
            )
        if args.no_fail:
            return r[int].ok(0)
        return r[int].ok(0 if total_issues == 0 and pip_ok else 1)


__all__ = ["FlextInfraDependencyDetectorRuntime"]
