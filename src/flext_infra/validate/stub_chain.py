"""Stub supply chain service.

Manages typing stubs and typing dependencies for workspace projects,
including stub generation, types-package installation, and idempotency checks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, m, p, r, t, u


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
    def project_dirs(self) -> Sequence[Path] | None:
        """Return resolved project directories for targeted validation."""
        names = self.project_names
        if self.all_projects or names is None:
            return None
        return [self.workspace_root / name for name in names]

    def _discover_stub_projects(self, workspace_root: Path) -> Sequence[Path]:
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
            root = workspace_root.resolve()
            proj = project_dir.resolve()
            mypy_hints = self._run_mypy_hints(proj)
            missing_imports = self._run_pyrefly_missing(proj)
            internal = [m for m in missing_imports if self._is_internal(m, proj.name)]
            external = [
                m for m in missing_imports if not self._is_internal(m, proj.name)
            ]
            unresolved = [m for m in external if not self._stub_exists(m, root)]
            result = m.Infra.StubAnalysisReport(
                project=proj.name,
                mypy_hints=mypy_hints,
                internal_missing=internal,
                unresolved_missing=unresolved,
                total_missing=len(missing_imports),
            )
            return r[m.Infra.StubAnalysisReport].ok(result)
        except (OSError, TypeError, ValueError) as exc:
            return r[m.Infra.StubAnalysisReport].fail(
                f"stub analysis failed for {project_dir.name}: {exc}",
            )

    def build_report(
        self,
        workspace_root: Path,
        project_dirs: Sequence[Path] | None = None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate stub supply chain across projects.

        Args:
            workspace_root: Root directory of the workspace.
            project_dirs: Optional specific projects; discovers all if None.

        Returns:
            r with ValidationReport indicating overall status.

        """
        try:
            root = workspace_root.resolve()
            projects = project_dirs or self._discover_stub_projects(root)
            violations: MutableSequence[str] = []
            for proj in projects:
                result = self.analyze(proj, root)
                if result.failure:
                    violations.append(f"{proj.name}: {result.error}")
                    continue
                data = result.value
                internal = data.internal_missing
                unresolved = data.unresolved_missing
                if internal:
                    violations.append(
                        f"{proj.name}: {len(internal)} internal missing imports",
                    )
                if unresolved:
                    violations.append(
                        f"{proj.name}: {len(unresolved)} unresolved imports",
                    )
            passed = not violations
            summary = f"stub chain: {len(projects)} projects, {len(violations)} issues"
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=passed,
                    violations=violations,
                    summary=summary,
                ),
            )
        except (OSError, TypeError, ValueError) as exc:
            return r[m.Infra.ValidationReport].fail(
                f"stub validation failed: {exc}",
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
        ordered: MutableSequence[str] = []
        for match in c.Infra.MISSING_IMPORT_RE.finditer(output):
            name = match.group(1).strip()
            if name and name not in seen:
                seen.add(name)
                ordered.append(name)
        return ordered


__all__: list[str] = ["FlextInfraStubSupplyChain"]
