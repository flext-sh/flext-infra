"""Runtime execution for dependency detector CLI."""

from __future__ import annotations

from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    Sequence,
)
from pathlib import Path

from flext_cli import m

from flext_infra import FlextInfraModelsDeps, c, p, r, t, u


class FlextInfraDependencyDetectorRuntime:
    """Runtime executor for dependency detection pipeline."""

    def __init__(
        self,
        detector: p.Infra.DetectorRuntime,
        workspace_report_factory: Callable[..., p.Infra.WorkspaceReport],
        dependency_limits_factory: Callable[
            ..., FlextInfraModelsDeps.DependencyLimitsInfo
        ],
        pip_check_factory: Callable[..., FlextInfraModelsDeps.PipCheckReport],
    ) -> None:
        """Store runtime collaborators used by dependency detection orchestration."""
        self._detector = detector
        self._workspace_report_factory = workspace_report_factory
        self._dependency_limits_factory = dependency_limits_factory
        self._pip_check_factory = pip_check_factory

    def run(self, params: FlextInfraModelsDeps.DetectCommand) -> p.Result[bool]:
        """Execute dependency detection and generate workspace report."""
        detector = self._detector
        limits_default = Path(__file__).resolve().parent / "dependency_limits.toml"
        root = params.workspace_path
        venv_bin = root / c.Infra.VENV_BIN_REL
        projects_result = detector.deps.discover_project_paths(
            root,
            projects_filter=params.project_names,
        )
        if projects_result.failure:
            return r[bool].fail(projects_result.error or "project discovery failed")
        projects: Sequence[Path] = projects_result.value
        if not projects:
            detector.log.error("deps_no_projects_found")
            return r[bool].fail("no projects found")
        if not (venv_bin / c.Infra.DEPTRY).exists():
            detector.log.error(
                "deps_deptry_missing",
                path=str(venv_bin / c.Infra.DEPTRY),
            )
            return r[bool].fail("deptry executable not found")
        apply_typings = bool(params.apply_typings)
        do_typings = bool(params.typings) or apply_typings
        limits_path = params.limits_path or limits_default
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
        typing_deps = (
            deps_service
            if isinstance(deps_service, p.Infra.TypingsDepsService)
            else None
        )
        if do_typings:
            if typing_deps is None:
                return r[bool].fail("typing dependency detection service unavailable")
            limits_data = typing_deps.load_dependency_limits(limits_path)
            if limits_data:
                python_cfg: t.Infra.ContainerDict = (
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                        limits_data.get(c.Infra.PYTHON),
                    )
                    if isinstance(limits_data.get(c.Infra.PYTHON), Mapping)
                    else {}
                )
                python_version = (
                    str(python_cfg.get(c.VERSION))
                    if python_cfg.get(c.VERSION) is not None
                    else None
                )
                report_model.dependency_limits = self._dependency_limits_factory(
                    python_version=python_version,
                    limits_path=str(limits_path),
                )
        for project_path in projects:
            project_name = project_path.name
            if not params.quiet:
                detector.log.info("deps_deptry_running", project=project_name)
            deptry_result = deps_service.run_deptry(project_path, venv_bin)
            if deptry_result.failure:
                return r[bool].fail(deptry_result.error or "deptry run failed")
            issues, _ = deptry_result.value
            project_payload = deps_service.build_project_report(project_name, issues)
            projects_report[project_name] = dict(project_payload.model_dump())
            if (
                typing_deps is not None
                and (project_path / c.Infra.DEFAULT_SRC_DIR).is_dir()
            ):
                if not params.quiet:
                    detector.log.info(
                        "deps_typings_detect_running",
                        project=project_name,
                    )
                typings_result = typing_deps.get_required_typings(
                    project_path,
                    venv_bin,
                    limits_path=limits_path,
                )
                if typings_result.failure:
                    return r[bool].fail(
                        typings_result.error or "typing dependency detection failed",
                    )
                typings_report = typings_result.value
                projects_report[project_name][c.Infra.DIR_TYPINGS] = (
                    typings_report.model_dump()
                )
                to_add: t.StrSequence = typings_report.to_add
                if apply_typings and to_add and params.apply:
                    env = {"VIRTUAL_ENV": str(venv_bin.parent)}
                    poetry = venv_bin / c.Infra.POETRY
                    for package in to_add:
                        run = detector.runner.run_raw(
                            [
                                str(poetry),
                                "add",
                                "--group",
                                c.Infra.DIR_TYPINGS,
                                package,
                            ],
                            cwd=project_path,
                            timeout=c.Infra.TIMEOUT_MEDIUM,
                            env=env,
                        )
                        if run.failure:
                            detector.log.warning(
                                "deps_typings_add_failed",
                                project=project_name,
                                package=package,
                            )
                        else:
                            run_output: m.Cli.CommandOutput = run.value
                            if run_output.exit_code != 0:
                                detector.log.warning(
                                    "deps_typings_add_failed",
                                    project=project_name,
                                    package=package,
                                )
        pip_ok = True
        if not params.no_pip_check:
            if not isinstance(deps_service, p.Infra.PipCheckDepsService):
                return r[bool].fail(
                    "pip-check dependency detection service unavailable",
                )
            if not params.quiet:
                detector.log.info("deps_pip_check_running")
            pip_result = deps_service.run_pip_check(root, venv_bin)
            if pip_result.failure:
                return r[bool].fail(pip_result.error or "pip check failed")
            pip_lines, pip_exit = pip_result.value
            pip_ok = pip_exit == 0
            report_model.pip_check = self._pip_check_factory(ok=pip_ok, lines=pip_lines)
        if params.output_format == c.Cli.OutputFormats.JSON:
            return r[bool].ok(True)
        out_path: Path | None = None
        if params.output_path is not None:
            out_path = params.output_path
        elif params.apply:
            out_path = u.Cli.get_report_path(
                root,
                c.Infra.PROJECT,
                c.Infra.DEPENDENCIES,
                "detect-runtime-dev-latest.json",
            )
        if out_path is not None and not params.dry_run:
            report_payload: dict[str, t.JsonValue] = {
                key: u.Cli.normalize_json_value(value)
                for key, value in report_model.model_dump().items()
            }
            write_result = u.Cli.json_write(out_path, report_payload)
            if write_result.failure:
                return r[bool].fail(write_result.error or "failed to write report")
            if not params.quiet:
                detector.log.info("deps_report_written", path=str(out_path))
        total_issues = 0
        for payload in projects_report.values():
            deptry_payload = u.Cli.json_as_mapping(payload.get(c.Infra.DEPTRY))
            total_issues += u.Cli.json_pick_int(deptry_payload, "raw_count")
        if not params.quiet:
            detector.log.info(
                "deps_summary",
                projects=len(projects),
                deptry_issues=total_issues,
                pip_check=c.Infra.RK_OK if pip_ok else "FAIL",
            )
        if params.no_fail or (total_issues == 0 and pip_ok):
            return r[bool].ok(True)
        return r[bool].fail("dependency issues detected")


__all__: list[str] = ["FlextInfraDependencyDetectorRuntime"]
