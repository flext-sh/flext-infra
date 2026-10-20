"""Runtime execution for dependency detector CLI.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.deps import FlextInfraDependencyDetectorRuntimeSteps


class FlextInfraDependencyDetectorRuntime(FlextInfraDependencyDetectorRuntimeSteps):
    """Runtime executor for dependency detection pipeline."""

    def __init__(
        self,
        detector: p.Infra.DetectorRuntime,
        deps: p.Infra.DepsService,
    ) -> None:
        """Receive the reporting command and the dependency-analysis port."""
        self._detector = detector
        self._deps = deps

    def run(self, params: m.Infra.DetectCommand) -> p.Result[bool]:
        """Execute dependency detection and generate workspace report (orchestrator).

        Returns:
            The resulting ``p.Result[bool]``.

        """
        # The environment under inspection is the repository's own; an ambient
        # UV_PROJECT_ENVIRONMENT would silently redirect detection elsewhere.
        venv_bin = u.Infra.runtime_environment_dir(params.repository_root) / (
            "Scripts" if os.name == "nt" else "bin"
        )
        env_result = self._validate_environment(
            params, params.repository_root, venv_bin
        )
        if env_result.failure:
            return r[bool].from_failure(env_result)
        projects, limits_path = env_result.value
        report_model = m.Infra.WorkspaceDependencyReport(
            workspace=str(params.repository_root),
            projects={},
            pip_check=None,
            dependency_limits=None,
        )
        if params.typings or params.apply_typings:
            limits_setup = self._configure_typings_limits(limits_path, report_model)
            if limits_setup.failure:
                return r[bool].from_failure(limits_setup)
        for project_path in projects:
            project_result = self._run_project_detection(
                project_path,
                venv_bin=venv_bin,
                limits_path=limits_path,
                params=params,
                projects_report=report_model.projects,
            )
            if project_result.failure:
                return r[bool].from_failure(project_result)
        return self._finalize_run(params, report_model, venv_bin, limits_path)

    def _finalize_run(
        self,
        params: m.Infra.DetectCommand,
        report_model: m.Infra.WorkspaceDependencyReport,
        venv_bin: Path,
        limits_path: Path,
    ) -> p.Result[bool]:
        """Publish the typed report and return its actual dependency verdict.

        Returns:
            Success only when the configured dependency checks succeed.

        """
        if params.apply and params.apply_typings:
            generated = self._deps.generate_typing_packages(
                u.Infra.runtime_owner_root(params.repository_root).unwrap(),
                tuple(
                    module
                    for project in report_model.projects.values()
                    if project.typings is not None
                    for module in project.typings.untyped_modules
                ),
                m.Infra.TypingGenerationPolicy.model_validate(
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                        self._deps.load_dependency_limits(limits_path).get(
                            c.Infra.TYPING_LIBRARIES,
                        ),
                    ).get("generation"),
                ),
            )
            if generated.failure:
                return r[bool].from_failure(generated)
            report_model.generated_typings = generated.value
        pip_check_result = self._run_pip_check(
            params.repository_root,
            venv_bin,
            params,
            report_model,
        )
        if pip_check_result.failure:
            return r[bool].from_failure(pip_check_result)
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
                pip_check=c.Infra.RK_OK if pip_check_result.value else "FAIL",
            )
        if params.no_fail or (total_issues == 0 and pip_check_result.value):
            return r[bool].ok(value=True)
        return r[bool].fail("dependency issues detected")


__all__: list[str] = ["FlextInfraDependencyDetectorRuntime"]
