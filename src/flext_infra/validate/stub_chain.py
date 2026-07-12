"""Typed dependency validation service.

Validates typing dependency hints and unresolved imports for workspace projects.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util as importlib_util
from pathlib import Path
from typing import Annotated, override

from flext_core import r

from flext_infra import c, m, p, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase

type _StubChainInitValue = (
    t.GuardInput | p.Settings | p.Context | t.SettingsClass | None
)
type _StubChainRuntimeState = dict[str, _StubChainInitValue]


class FlextInfraStubSupplyChain(FlextInfraProjectSelectionServiceBase[bool]):
    """Validate typed dependency supply chain for workspace projects.

    Coordinates mypy install hints, pyrefly missing imports, and installed
    typing-package validation.
    """

    all_projects: Annotated[
        bool,
        m.Field(alias="all", description="Validate all projects"),
    ] = False
    _runner: p.Cli.CommandRunner | None = m.PrivateAttr(default_factory=lambda: None)

    def __init__(
        self,
        *,
        workspace_root: Path | None = None,
        apply_changes: bool = False,
        check_only: bool = False,
        dry_run: bool = False,
        fail_fast: bool = False,
        output_format: str = "text",
        project_filter: str | None = None,
        target_module: str | None = None,
        target_namespace: str | None = None,
        report_path: Path | None = None,
        output_dir: Path | None = None,
        selected_projects: t.StrSequence | None = None,
        all_projects: bool = False,
        runner: p.Cli.CommandRunner | None = None,
        settings_type: t.SettingsClass | None = None,
        runtime_settings: p.Settings | None = None,
        settings_overrides: t.JsonMapping | None = None,
        initial_context: p.Context | None = None,
    ) -> None:
        """Initialize with an internal command runner dependency."""
        model_data: _StubChainRuntimeState = {
            "workspace_root": workspace_root or Path.cwd(),
            "apply_changes": apply_changes,
            "check_only": check_only,
            "dry_run": dry_run,
            "fail_fast": fail_fast,
            "output_format": output_format,
            "project_filter": project_filter,
            "target_module": target_module,
            "target_namespace": target_namespace,
            "report_path": report_path,
            "output_dir": output_dir,
            "selected_projects": selected_projects,
            "all_projects": all_projects,
        }
        self.__pydantic_validator__.validate_python(model_data, self_instance=self)
        self._runner = runner
        runtime_state: _StubChainRuntimeState = {}
        if settings_type is not None:
            runtime_state["settings_type"] = settings_type
        if runtime_settings is not None:
            runtime_state["runtime_settings"] = runtime_settings
        if settings_overrides is not None:
            runtime_state["settings_overrides"] = settings_overrides
        if initial_context is not None:
            runtime_state["initial_context"] = initial_context
        self._apply_runtime_bootstrap_state(runtime_state)

    @property
    def runner(self) -> p.Cli.CommandRunner | None:
        """Optional command runner dependency for tests and command execution."""
        return self._runner

    @override
    @property
    def project_dirs(self) -> t.SequenceOf[Path] | None:
        """Resolved project directories for targeted validation."""
        names = self.project_names
        if self.all_projects or names is None:
            return None
        return [self.workspace_root / name for name in names]

    def _discover_typed_projects(self, workspace_root: Path) -> t.SequenceOf[Path]:
        """Discover projects that should participate in typed dependency checks."""
        _ = self
        return [
            project_root
            for project_root in u.Infra.discover_project_roots(workspace_root)
            if (project_root / c.Infra.DEFAULT_SRC_DIR).is_dir()
        ]

    def _is_internal(self, module_name: str, project_name: str) -> bool:
        """Check if a module is an internal project module."""
        _ = self
        root_mod = module_name.split(".", 1)[0]
        project_root = project_name.replace("-", "_")
        if root_mod.startswith(c.Infra.INTERNAL_PREFIXES):
            return True
        return root_mod == project_root

    def _module_resolved(self, module_name: str) -> bool:
        """Check if an external module is installed in the active typed environment."""
        _ = self
        root_module = module_name.split(".", maxsplit=1)[0]
        try:
            return importlib_util.find_spec(root_module) is not None
        except c.EXC_OS_TYPE_VALUE:
            return False

    def analyze(
        self,
        project_dir: Path,
        workspace_root: Path,
    ) -> p.Result[m.Infra.StubAnalysisReport]:
        """Analyze a project for missing typed dependencies.

        Runs mypy for hints and pyrefly for missing imports, then
        classifies each as internal, resolved, or unresolved.

        Args:
            project_dir: Path to the project directory.
            workspace_root: Root of the workspace.

        Returns:
            r with analysis report dict.

        """
        try:
            return self._analyze_project(project_dir, workspace_root)
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[m.Infra.StubAnalysisReport].fail(
                f"typed dependency analysis failed for {project_dir.name}: {exc}",
            )

    def build_report(
        self,
        workspace_root: Path,
        project_dirs: t.SequenceOf[Path] | None = None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate typed dependency supply chain across projects.

        Args:
            workspace_root: Root directory of the workspace.
            project_dirs: Optional specific projects; discovers all if None.

        Returns:
            r with ValidationReport indicating overall status.

        """
        try:
            return self._build_typed_dependency_report(workspace_root, project_dirs)
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[m.Infra.ValidationReport].fail_op(
                "typed dependency validation", exc
            )

    def _classify_missing_imports(
        self,
        missing_imports: t.StrSequence,
        project_name: str,
    ) -> tuple[t.StrSequence, t.StrSequence]:
        """Split missing imports into internal and unresolved external groups."""
        internal = tuple(
            module_name
            for module_name in missing_imports
            if self._is_internal(module_name, project_name)
        )
        external = tuple(
            module_name
            for module_name in missing_imports
            if not self._is_internal(module_name, project_name)
        )
        unresolved = tuple(
            module_name
            for module_name in external
            if not self._module_resolved(module_name)
        )
        return internal, unresolved

    def _analyze_project(
        self,
        project_dir: Path,
        workspace_root: Path,
    ) -> p.Result[m.Infra.StubAnalysisReport]:
        """Analyze one project after path resolution."""
        _ = workspace_root
        proj = project_dir.resolve()
        mypy_hints = self._run_mypy_hints(proj)
        missing_imports = self._run_pyrefly_missing(proj)
        internal, unresolved = self._classify_missing_imports(
            missing_imports,
            proj.name,
        )
        return r[m.Infra.StubAnalysisReport].ok(
            m.Infra.StubAnalysisReport(
                project=proj.name,
                mypy_hints=mypy_hints,
                internal_missing=internal,
                unresolved_missing=unresolved,
                total_missing=len(missing_imports),
            ),
        )

    def _project_violations(
        self,
        project_dir: Path,
        workspace_root: Path,
    ) -> t.StrSequence:
        """Return typed-dependency violations for one project."""
        result = self.analyze(project_dir, workspace_root)
        if result.failure:
            return (f"{project_dir.name}: {result.error}",)
        data = result.value
        violations: t.MutableSequenceOf[str] = []
        if data.mypy_hints:
            violations.append(
                f"{project_dir.name}: {len(data.mypy_hints)} missing typing packages",
            )
        if data.internal_missing:
            violations.append(
                f"{project_dir.name}: {len(data.internal_missing)} internal missing imports",
            )
        if data.unresolved_missing:
            violations.append(
                f"{project_dir.name}: {len(data.unresolved_missing)} unresolved imports",
            )
        return tuple(violations)

    def _typed_dependency_violations(
        self,
        projects: t.SequenceOf[Path],
        workspace_root: Path,
    ) -> t.StrSequence:
        """Collect typed-dependency violations for all selected projects."""
        violations: t.MutableSequenceOf[str] = []
        for project_dir in projects:
            violations.extend(self._project_violations(project_dir, workspace_root))
        return tuple(violations)

    def _build_typed_dependency_report(
        self,
        workspace_root: Path,
        project_dirs: t.SequenceOf[Path] | None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Build the workspace typed-dependency validation report."""
        root = workspace_root.resolve()
        projects = project_dirs or self._discover_typed_projects(root)
        violations = self._typed_dependency_violations(projects, root)
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=not violations,
                violations=violations,
                summary=(
                    f"typed dependency chain: {len(projects)} projects, {len(violations)} issues"
                ),
            ),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the typed-dependency validation CLI flow."""
        report_result = self.build_report(
            self.workspace_root,
            project_dirs=self.project_dirs,
        )
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "typed dependency validation failed",
            )
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)

    def _run_mypy_hints(self, project_dir: Path) -> t.StrSequence:
        """Run mypy and extract install-package hints."""
        runner = self.runner or u.Cli()
        result = runner.run(
            [
                c.Infra.POETRY,
                c.Infra.VERB_RUN,
                c.Infra.MYPY,
                c.Infra.DEFAULT_SRC_DIR,
                "--config-file",
                c.Infra.PYPROJECT_FILENAME,
                "--no-error-summary",
            ],
            cwd=project_dir,
        )
        output = ""
        if result.success:
            cmd_output: m.Cli.CommandOutput = result.value
            output = cmd_output.stdout
        return sorted({
            m.group(1).strip()
            for m in c.Infra.MYPY_HINT_RE.finditer(output)
            if m.group(1).strip()
        })

    def _run_pyrefly_missing(self, project_dir: Path) -> t.StrSequence:
        """Run pyrefly check and extract missing imports."""
        runner = self.runner or u.Cli()
        result = runner.run(
            [
                c.Infra.POETRY,
                c.Infra.VERB_RUN,
                c.Infra.PYREFLY,
                c.Infra.CHECK,
                c.Infra.DEFAULT_SRC_DIR,
                "--config",
                c.Infra.PYPROJECT_FILENAME,
            ],
            cwd=project_dir,
        )
        output = ""
        if result.success:
            cmd_output: m.Cli.CommandOutput = result.value
            output = cmd_output.stdout
        seen: t.Infra.StrSet = set()
        ordered: t.MutableSequenceOf[str] = []
        for match in c.Infra.MISSING_IMPORT_RE.finditer(output):
            name = match.group(1).strip()
            if name and name not in seen:
                seen.add(name)
                ordered.append(name)
        return ordered


__all__: list[str] = ["FlextInfraStubSupplyChain"]
