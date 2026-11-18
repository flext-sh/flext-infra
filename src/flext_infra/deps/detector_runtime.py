"""Runtime execution for dependency detector CLI.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.deps._detector import FlextInfraDepsDetectorRuntimeSteps


class FlextInfraDependencyDetectorRuntime(FlextInfraDepsDetectorRuntimeSteps):
    """Runtime executor for dependency detection pipeline."""

    def __init__(
        self,
        detector: p.Infra.DetectorRuntime,
        deps: p.Infra.DepsService,
    ) -> None:
        """Receive the reporting command and the dependency-analysis port."""
        self._detector = detector
        self._deps = deps

    def run(self, params: p.Infra.DetectCommand) -> p.Result[bool]:
        """Execute dependency detection and generate workspace report (orchestrator).

        Returns:
            The resulting ``p.Result[bool]``.

        """
        # The environment under inspection is the repository's own; an ambient
        # UV_PROJECT_ENVIRONMENT would silently redirect detection elsewhere.
        owner = u.Infra.runtime_owner_root(params.repository_root)
        if owner.failure:
            return r[bool].from_failure(owner)
        venv_bin = u.Infra.runtime_environment_dir(
            params.repository_root, runtime_root=owner.value
        ) / ("Scripts" if os.name == "nt" else "bin")
        env_result = self._validate_environment(
            params, params.repository_root, venv_bin
        )
        if env_result.failure:
            return r[bool].from_failure(env_result)
        projects_report: dict[str, p.Infra.ProjectDependencyReport] = {}
        for project_path in env_result.value:
            project_result = self._run_project_detection(
                project_path,
                venv_bin=venv_bin,
                params=params,
                projects_report=projects_report,
            )
            if project_result.failure:
                return r[bool].from_failure(project_result)
        return self._finalize_run(params, projects_report, venv_bin)

    def _finalize_run(
        self,
        params: p.Infra.DetectCommand,
        projects_report: Mapping[str, p.Infra.ProjectDependencyReport],
        venv_bin: Path,
    ) -> p.Result[bool]:
        """Publish the typed report and return its actual dependency verdict.

        Returns:
            Success only when the configured dependency checks succeed.

        """
        pip_check_result = self._run_pip_check(
            params.repository_root,
            venv_bin,
            params,
        )
        if pip_check_result.failure:
            return r[bool].from_failure(pip_check_result)
        pip_check = pip_check_result.value
        report_model = m.Infra.WorkspaceDependencyReport.model_validate({
            "workspace": str(params.repository_root),
            "projects": projects_report,
            "pip_check": pip_check,
        })
        if params.output_format != c.Cli.OutputFormats.JSON:
            out_path = params.output_path or u.Cli.resolve_report_path(
                params.repository_root,
                c.Infra.PROJECT,
                c.Infra.DEPENDENCIES,
                "detect-runtime-dev-latest.json",
            )
            written = u.Cli.atomic_write_text_file(
                out_path,
                report_model.model_dump_json(indent=2, exclude_none=True) + "\n",
            )
            if written.failure:
                return r[bool].from_failure(written)
            if not params.quiet:
                self._detector.log.info("deps_report_written", path=str(out_path))
        total_issues = sum(
            report.deptry.raw_count for report in report_model.projects.values()
        )
        if not params.quiet:
            self._detector.log.info(
                "deps_summary",
                projects=len(report_model.projects),
                deptry_issues=total_issues,
                pip_check=c.Infra.RK_OK if pip_check.ok else "FAIL",
            )
        if params.no_fail or (total_issues == 0 and pip_check.ok):
            return r[bool].ok(value=True)
        return r[bool].fail("dependency issues detected")


__all__: list[str] = ["FlextInfraDependencyDetectorRuntime"]
