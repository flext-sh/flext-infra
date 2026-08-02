"""Cohesive environment-setup + per-project execution mixin for the dependency detector runtime."""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, p, t

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraDependencyDetectorRuntimeSteps:
    """Mixin holding environment setup and per-project detection steps."""

    _detector: p.Infra.DetectorRuntime
    _pip_check_factory: Callable[..., m.Infra.PipCheckReport]

    def _validate_environment(
        self, params: m.Infra.DetectCommand, root: Path, venv_bin: Path
    ) -> p.Result[t.SequenceOf[Path]]:
        """Discover projects and verify the configured deptry binary."""
        detector = self._detector
        projects_result = detector.deps.discover_project_paths(
            root, projects_filter=params.project_names
        )
        if projects_result.failure:
            return r[t.SequenceOf[Path]].fail(
                projects_result.error or "project discovery failed"
            )
        projects: t.SequenceOf[Path] = projects_result.value
        if not projects:
            detector.log.error("deps_no_projects_found")
            return r[t.SequenceOf[Path]].fail("no projects found")
        deptry_path = venv_bin / c.Infra.DEPTRY
        if not deptry_path.exists():
            detector.log.error("deps_deptry_missing", path=str(deptry_path))
            return r[t.SequenceOf[Path]].fail(
                f"Deptry executable not found at {deptry_path}"
            )
        return r[t.SequenceOf[Path]].ok(projects)

    def _run_project_detection(
        self,
        project_path: Path,
        *,
        deps_service: p.Infra.DepsService,
        venv_bin: Path,
        params: m.Infra.DetectCommand,
        projects_report: MutableMapping[str, MutableMapping[str, t.Infra.InfraValue]],
    ) -> p.Result[bool]:
        """Run deptry detection for one project."""
        detector = self._detector
        project_name = project_path.name
        if not params.quiet:
            detector.log.info("deps_deptry_running", project=project_name)
        deptry_result = deps_service.run_deptry(project_path, venv_bin)
        if deptry_result.failure:
            return r[bool].fail(deptry_result.error or "deptry run failed")
        issues, _ = deptry_result.value
        project_payload = deps_service.build_project_report(project_name, issues)
        projects_report[project_name] = dict(project_payload.model_dump())
        return r[bool].ok(True)

    def _run_pip_check(
        self,
        deps_service: p.Infra.DepsService,
        root: Path,
        venv_bin: Path,
        params: m.Infra.DetectCommand,
        report_model: p.Infra.WorkspaceReport,
    ) -> p.Result[bool]:
        """Execute the workspace ``pip check`` and stamp the report; ``r.ok(pip_ok)``."""
        if params.no_pip_check:
            return r[bool].ok(True)
        if not isinstance(deps_service, p.Infra.PipCheckDepsService):
            return r[bool].fail("pip-check dependency detection service unavailable")
        detector = self._detector
        if not params.quiet:
            detector.log.info("deps_pip_check_running")
        pip_result = deps_service.run_pip_check(root, venv_bin)
        if pip_result.failure:
            return r[bool].fail(pip_result.error or "pip check failed")
        pip_lines, pip_exit = pip_result.value
        pip_ok = pip_exit == 0
        report_model.pip_check = self._pip_check_factory(ok=pip_ok, lines=pip_lines)
        return r[bool].ok(pip_ok)


__all__: list[str] = ["FlextInfraDependencyDetectorRuntimeSteps"]
