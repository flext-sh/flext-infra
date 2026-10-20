"""Runtime execution for dependency detector CLI.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u
from flext_infra.deps import FlextInfraDependencyDetectorRuntimeSteps

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping


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
        root = params.repository_root
        # The environment under inspection is the repository's own; an ambient
        # UV_PROJECT_ENVIRONMENT would silently redirect detection elsewhere.
        venv_bin = u.Infra.runtime_environment_dir(root) / (
            "Scripts" if os.name == "nt" else "bin"
        )
        env_result = self._validate_environment(params, root, venv_bin)
        if env_result.failure:
            return r[bool].from_failure(env_result)
        projects, limits_path = env_result.value
        do_typings = params.typings or params.apply_typings
        projects_report: MutableMapping[str, m.Infra.ProjectRuntimeReport] = {}
        report_model = m.Infra.WorkspaceDependencyReport(
            workspace=str(root),
            projects={},
            pip_check=None,
            dependency_limits=None,
        )
        if do_typings:
            limits_setup = self._configure_typings_limits(limits_path, report_model)
            if limits_setup.failure:
                return r[bool].from_failure(limits_setup)
        for project_path in projects:
            project_result = self._run_project_detection(
                project_path,
                venv_bin=venv_bin,
                limits_path=limits_path,
                params=params,
                projects_report=projects_report,
            )
            if project_result.failure:
                return r[bool].from_failure(project_result)
        report_model.projects = projects_report
        if params.apply and params.apply_typings:
            limits = self._deps.load_dependency_limits(limits_path)
            typing_limits = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                limits.get(c.Infra.TYPING_LIBRARIES, {}),
            )
            policy = m.Infra.TypingGenerationPolicy.model_validate(
                typing_limits.get("generation"),
            )
            generated = self._deps.generate_typing_packages(
                venv_bin.parent.parent,
                tuple(
                    module
                    for project in report_model.projects.values()
                    if project.typings is not None
                    for module in project.typings.untyped_modules
                ),
                policy,
            )
            if generated.failure:
                return r[bool].from_failure(generated)
            report_model.generated_typings = generated.value
        pip_check_result = self._run_pip_check(root, venv_bin, params, report_model)
        if pip_check_result.failure:
            return r[bool].from_failure(pip_check_result)
        pip_ok = pip_check_result.value
        return self._finalize_run(
            (params, root),
            report_model,
            projects_report,
            projects,
            pip_ok=pip_ok,
        )

    def _finalize_run(
        self,
        scope: t.Pair[m.Infra.DetectCommand, Path],
        report_model: p.Infra.WorkspaceReport,
        projects_report: Mapping[str, m.Infra.ProjectRuntimeReport],
        projects: t.SequenceOf[Path],
        *,
        pip_ok: bool,
    ) -> p.Result[bool]:
        """Persist and summarize the workspace report unless JSON-silent.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        params, root = scope
        if params.output_format == c.Cli.OutputFormats.JSON:
            return r[bool].ok(value=True)
        write_result = self._write_workspace_report(
            params,
            root,
            report_model,
        )
        if write_result.failure:
            return r[bool].from_failure(write_result)
        return self._summarize_run(
            projects,
            projects_report,
            pip_ok=pip_ok,
            params=params,
        )

    def _write_workspace_report(
        self,
        params: m.Infra.DetectCommand,
        root: Path,
        report_model: p.Infra.WorkspaceReport,
    ) -> p.Result[Path]:
        """Render and persist the canonical workspace dependency report JSON.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        out_path: Path = params.output_path or u.Cli.resolve_report_path(
            root,
            c.Infra.PROJECT,
            c.Infra.DEPENDENCIES,
            "detect-runtime-dev-latest.json",
        )
        write_result = u.Cli.atomic_write_text_file(
            out_path,
            report_model.model_dump_json(indent=2) + "\n",
        )
        if write_result.failure:
            return r[Path].from_failure(write_result)
        if not params.quiet:
            self._detector.log.info("deps_report_written", path=str(out_path))
        return r[Path].ok(out_path)

    def _summarize_run(
        self,
        projects: t.SequenceOf[Path],
        projects_report: Mapping[str, m.Infra.ProjectRuntimeReport],
        *,
        pip_ok: bool,
        params: m.Infra.DetectCommand,
    ) -> p.Result[bool]:
        """Aggregate deptry counts, log the summary, decide overall pass/fail.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        total_issues = sum(
            report.deptry.raw_count for report in projects_report.values()
        )
        if not params.quiet:
            self._detector.log.info(
                "deps_summary",
                projects=len(projects),
                deptry_issues=total_issues,
                pip_check=c.Infra.RK_OK if pip_ok else "FAIL",
            )
        if params.no_fail or (total_issues == 0 and pip_ok):
            return r[bool].ok(value=True)
        return r[bool].fail("dependency issues detected")


__all__: list[str] = ["FlextInfraDependencyDetectorRuntime"]
