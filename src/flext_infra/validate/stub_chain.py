"""Stub supply chain service.

Manages typing stubs and typing dependencies for workspace projects,
including stub generation, types-package installation, and idempotency checks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraStubSupplyChain(FlextInfraProjectSelectionServiceBase[bool]):
    """Manages typing stub supply chain for workspace projects.

    Coordinates mypy stub hints, pyrefly missing imports, stubgen
    generation, and types-package installation.
    """

    all_projects: Annotated[
        bool, m.Field(alias="all", description="Validate all projects")
    ] = False
    runner: Annotated[
        p.Cli.CommandRunner | None,
        m.Field(exclude=True, description="Optional command runner"),
    ] = None

    @override
    @property
    def project_dirs(self) -> t.SequenceOf[Path] | None:
        """Return resolved project directories for targeted validation."""
        names = self.project_names
        if self.all_projects or names is None:
            return None
        return [self.workspace_root / name for name in names]

    def _discover_stub_projects(self, workspace_root: Path) -> t.SequenceOf[Path]:
        """Discover projects that should participate in stub checks."""
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

    def _stub_exists(self, module_name: str, workspace_root: Path) -> bool:
        """Check if a stub file exists for a module."""
        _ = self
        rel = module_name.replace(".", "/")
        for base in (
            workspace_root / c.Infra.DIR_TYPINGS,
            workspace_root / c.Infra.DIR_TYPINGS / "generated",
        ):
            candidates = [base / f"{rel}.pyi", base / rel / "__init__.pyi"]
            if any(c.exists() for c in candidates):
                return True
        return False

    def analyze(
        self,
        project_dir: Path,
        workspace_root: Path,
    ) -> p.Result[m.Infra.StubAnalysisReport]:
        """Analyze a project for missing stubs and type packages.

        Runs mypy for hints and pyrefly for missing imports, then
        classifies each as internal, resolved, or unresolved.

        Args:
            project_dir: Path to the project directory.
            workspace_root: Root of the workspace for stub lookup.

        Returns:
            r with analysis report dict.

        """
        try:
            return self._analyze_project(project_dir, workspace_root)
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[m.Infra.StubAnalysisReport].fail(
                f"stub analysis failed for {project_dir.name}: {exc}",
            )

    def build_report(
        self,
        workspace_root: Path,
        project_dirs: t.SequenceOf[Path] | None = None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate stub supply chain across projects.

        Args:
            workspace_root: Root directory of the workspace.
            project_dirs: Optional specific projects; discovers all if None.

        Returns:
            r with ValidationReport indicating overall status.

        """
        try:
            return self._build_stub_report(workspace_root, project_dirs)
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[m.Infra.ValidationReport].fail_op("stub validation", exc)

    def _classify_missing_imports(
        self,
        missing_imports: t.StrSequence,
        project_name: str,
        workspace_root: Path,
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
            if not self._stub_exists(module_name, workspace_root)
        )
        return internal, unresolved

    def _analyze_project(
        self,
        project_dir: Path,
        workspace_root: Path,
    ) -> p.Result[m.Infra.StubAnalysisReport]:
        """Analyze one project after path resolution."""
        root = workspace_root.resolve()
        proj = project_dir.resolve()
        mypy_hints = self._run_mypy_hints(proj)
        missing_imports = self._run_pyrefly_missing(proj)
        internal, unresolved = self._classify_missing_imports(
            missing_imports,
            proj.name,
            root,
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
        """Return stub-chain violations for one project."""
        result = self.analyze(project_dir, workspace_root)
        if result.failure:
            return (f"{project_dir.name}: {result.error}",)
        data = result.value
        violations: t.MutableSequenceOf[str] = []
        if data.internal_missing:
            violations.append(
                f"{project_dir.name}: {len(data.internal_missing)} internal missing imports",
            )
        if data.unresolved_missing:
            violations.append(
                f"{project_dir.name}: {len(data.unresolved_missing)} unresolved imports",
            )
        return tuple(violations)

    def _stub_violations(
        self,
        projects: t.SequenceOf[Path],
        workspace_root: Path,
    ) -> t.StrSequence:
        """Collect stub-chain violations for all selected projects."""
        violations: t.MutableSequenceOf[str] = []
        for project_dir in projects:
            violations.extend(self._project_violations(project_dir, workspace_root))
        return tuple(violations)

    def _build_stub_report(
        self,
        workspace_root: Path,
        project_dirs: t.SequenceOf[Path] | None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Build the workspace stub-chain validation report."""
        root = workspace_root.resolve()
        projects = project_dirs or self._discover_stub_projects(root)
        violations = self._stub_violations(projects, root)
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=not violations,
                violations=violations,
                summary=(
                    f"stub chain: {len(projects)} projects, {len(violations)} issues"
                ),
            ),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the stub-validation CLI flow."""
        report_result = self.build_report(
            self.workspace_root,
            project_dirs=self.project_dirs,
        )
        if report_result.failure:
            return r[bool].fail(report_result.error or "stub validation failed")
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
