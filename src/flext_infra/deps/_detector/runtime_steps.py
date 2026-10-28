"""Environment-setup + per-project execution mixin for the dependency detector.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.workspace import FlextInfraRuntimeDependencyCollector


class FlextInfraDepsDetectorRuntimeSteps:
    """Mixin holding environment setup and per-project detection steps."""

    _detector: p.Infra.DetectorRuntime
    _deps: p.Infra.DepsService

    def _validate_environment(
        self,
        params: m.Infra.DetectCommand,
        root: Path,
        venv_bin: Path,
    ) -> p.Result[Sequence[Path]]:
        """Discover projects and verify deptry.

        Returns:
            The discovered project paths.

        """
        detector = self._detector
        projects_result = self._deps.discover_project_paths(
            root,
            projects_filter=u.Infra.normalize_sequence_values(params.projects),
        )
        if projects_result.failure:
            return r[Sequence[Path]].from_failure(projects_result)
        projects: Sequence[Path] = projects_result.value
        if not projects:
            detector.log.error("deps_no_projects_found")
            return r[Sequence[Path]].fail("no projects found")
        deptry_path = venv_bin / c.Infra.DEPTRY
        if not deptry_path.exists():
            detector.log.error("deps_deptry_missing", path=str(deptry_path))
            return r[Sequence[Path]].fail(
                f"Deptry executable not found at {deptry_path}",
            )
        return r[Sequence[Path]].ok(projects)

    def _run_project_detection(
        self,
        project_path: Path,
        *,
        venv_bin: Path,
        params: m.Infra.DetectCommand,
        projects_report: MutableMapping[str, m.Infra.ProjectDependencyReport],
    ) -> p.Result[bool]:
        """Run deptry for one project.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        detector = self._detector
        deps_service = self._deps
        project_name = project_path.name
        if not params.quiet:
            detector.log.info("deps_deptry_running", project=project_name)
        if params.apply:
            with u.Cli.file_changes_lock(
                u.Infra.mutation_lock_path(project_path).unwrap()
            ):
                scan = u.Infra.capture_deptry_scan(
                    project_path,
                    venv_bin,
                    config_path=project_path / c.PYPROJECT_FILENAME,
                    json_output_path=u.Cli.ensure_dir(
                        project_path / c.Infra.REPORTS_DIR_NAME
                    ).unwrap()
                    / f"deptry-report-{u.generate_id()}.json",
                ).unwrap()
                if scan.report.root:
                    inputs = FlextInfraRuntimeDependencyCollector(
                        python=u.Infra.runtime_python(params.repository_root),
                        development_only=(),
                    )(project_path, scan).unwrap()
                    plan = u.Infra.runtime_dependency_plan(scan, inputs).unwrap()
                    u.Infra.publish_runtime_dependency_plan(plan).unwrap()
                u.Cli.atomic_delete_binary_file_guarded(scan.report_state).unwrap()
        deptry_result = deps_service.run_deptry(project_path, venv_bin)
        if deptry_result.failure:
            return r[bool].from_failure(deptry_result)
        issues, _ = deptry_result.value
        projects_report[project_name] = deps_service.build_project_report(
            project_name,
            issues,
        )
        return r[bool].ok(value=True)

    def _run_pip_check(
        self,
        root: Path,
        venv_bin: Path,
        params: m.Infra.DetectCommand,
        report_model: p.Infra.WorkspaceReport,
    ) -> p.Result[bool]:
        """Execute the workspace ``pip check`` and stamp the report; ``r.ok(pip_ok)``.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if params.no_pip_check:
            return r[bool].ok(value=True)
        detector = self._detector
        if not params.quiet:
            detector.log.info("deps_pip_check_running")
        pip_result = self._deps.run_pip_check(root, venv_bin)
        if pip_result.failure:
            return r[bool].from_failure(pip_result)
        pip_lines, pip_exit = pip_result.value
        pip_ok = pip_exit == 0
        report_model.pip_check = m.Infra.PipCheckReport(ok=pip_ok, lines=pip_lines)
        return r[bool].ok(pip_ok)


__all__: list[str] = ["FlextInfraDepsDetectorRuntimeSteps"]
