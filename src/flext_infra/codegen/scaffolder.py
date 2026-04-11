"""Module scaffolder for base module generation.

Generates missing base modules (constants, typings, protocols, models, utilities)
in both src/ and tests/ directories for workspace projects.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraNamespaceValidator,
    FlextInfraServiceBase,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraCodegenScaffolder(FlextInfraServiceBase[str]):
    """Generates missing base modules in src/ and tests/ directories."""

    @override
    def execute(self) -> r[str]:
        """Execute scaffolding directly from the validated CLI model."""
        dry_run = self.dry_run or not self.apply_changes
        results = self.run(dry_run=dry_run)
        total_created = sum(len(result.files_created) for result in results)
        total_skipped = sum(len(result.files_skipped) for result in results)
        lines: MutableSequence[str] = []
        if dry_run:
            lines.append("Dry-run mode: no files will be created")
        lines.extend(
            f"  {result.project}: created {len(result.files_created)} files"
            for result in results
            if result.files_created
        )
        lines.append(
            (
                f"Scaffold: {total_created} created, {total_skipped} skipped"
                f" across {len(results)} projects"
            ),
        )
        return r[str].ok("\n".join(lines))

    def run(
        self,
        *,
        dry_run: bool = False,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.ScaffoldResult]:
        """Scaffold missing base modules for all projects in workspace.

        Args:
            dry_run: If True, only report changes without writing.
            projects: Pre-discovered projects to skip redundant discovery.

        Returns:
            List of ScaffoldResult models, one per project.

        """
        projects_result = u.Infra.discover_codegen_projects(
            self.workspace_root,
            projects=projects,
        )
        if not projects_result.is_success:
            return []
        return [
            self.scaffold_project(project.path, dry_run=dry_run)
            for project in projects_result.unwrap()
        ]

    def scaffold_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.ScaffoldResult:
        """Scaffold missing base modules for a single project.

        Args:
            project_path: Path to the project root directory.

        Returns:
            ScaffoldResult with lists of created and skipped files.

        """
        prefix = FlextInfraNamespaceValidator.derive_prefix(project_path)
        if not prefix:
            return m.Infra.ScaffoldResult(
                project=project_path.name,
                files_created=[],
                files_skipped=[],
            )
        files_created: MutableSequence[str] = []
        files_skipped: MutableSequence[str] = []
        package_info = u.Infra.discover_src_package_dir(project_path)
        if package_info is not None:
            _package_name, pkg_dir = package_info
            self._scaffold_dir(
                target_dir=pkg_dir,
                prefix=prefix,
                modules=c.Infra.SRC_MODULES,
                test_prefix="",
                inherit_project_facade=False,
                dry_run=dry_run,
                files_created=files_created,
                files_skipped=files_skipped,
            )
        tests_dir = project_path / c.Infra.Directories.TESTS
        if tests_dir.is_dir():
            self._scaffold_dir(
                target_dir=tests_dir,
                prefix=prefix,
                modules=c.Infra.TESTS_MODULES,
                test_prefix="Tests",
                inherit_project_facade=False,
                dry_run=dry_run,
                files_created=files_created,
                files_skipped=files_skipped,
            )
        examples_dir = project_path / c.Infra.Directories.EXAMPLES
        if examples_dir.is_dir():
            self._scaffold_dir(
                target_dir=examples_dir,
                prefix=prefix,
                modules=c.Infra.SRC_MODULES,
                test_prefix="Examples",
                inherit_project_facade=True,
                dry_run=dry_run,
                files_created=files_created,
                files_skipped=files_skipped,
            )
        scripts_dir = project_path / c.Infra.Directories.SCRIPTS
        if scripts_dir.is_dir():
            self._scaffold_dir(
                target_dir=scripts_dir,
                prefix=prefix,
                modules=c.Infra.SRC_MODULES,
                test_prefix="Scripts",
                inherit_project_facade=True,
                dry_run=dry_run,
                files_created=files_created,
                files_skipped=files_skipped,
            )
        return m.Infra.ScaffoldResult(
            project=project_path.name,
            files_created=files_created,
            files_skipped=files_skipped,
        )

    def _scaffold_dir(
        self,
        *,
        target_dir: Path,
        prefix: str,
        modules: t.Infra.VariadicTuple[t.Infra.Quad[str, str, str, str]],
        test_prefix: str,
        inherit_project_facade: bool,
        dry_run: bool,
        files_created: MutableSequence[str],
        files_skipped: MutableSequence[str],
    ) -> None:
        """Generate missing modules in a directory."""
        for filename, suffix, base_class, doc_suffix in modules:
            filepath = target_dir / filename
            if filepath.exists():
                files_skipped.append(str(filepath))
                continue
            class_name = f"{test_prefix}{prefix}{suffix}"
            resolved_base = (
                f"{prefix}{suffix}" if inherit_project_facade else base_class
            )
            docstring = f"{doc_suffix} for {prefix.lower()}."
            content = u.Infra.generate_module_skeleton(
                class_name=class_name,
                base_class=resolved_base,
                docstring=docstring,
            )
            if dry_run:
                files_created.append(str(filepath))
                continue
            u.write_file(filepath, content, encoding=c.Infra.Encoding.DEFAULT)
            u.Infra.run_ruff_fix(filepath)
            files_created.append(str(filepath))


__all__ = ["FlextInfraCodegenScaffolder"]
