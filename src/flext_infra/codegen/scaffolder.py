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

from flext_infra import c, config, m, p, r, u
from flext_infra.codegen import FlextInfraCodegenExecution


class FlextInfraCodegenScaffolder(FlextInfraCodegenExecution[str]):
    """Generates missing base modules in src/ and tests/ directories."""

    @staticmethod
    def plan_stems(
        root: Path,
        project: p.Infra.ProjectSpec,
        policy: p.Infra.ScaffoldSpec,
        planned: Sequence[p.Infra.CodegenFilePlan],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        """Plan missing family stems and auxiliary facades over authored sources.

        Returns:
            Only absent seeds, preserving existing modules and planned templates.

        """
        occupied = {plan.path for plan in planned}
        namespaces = (
            (
                root / c.Infra.DEFAULT_SRC_DIR / project.package_name,
                "",
                policy.source_stems,
            ),
            *(
                (root / tier, u.derive_class_stem(tier), policy.auxiliary_stems)
                for tier in config.Infra.source_scan.roots
                if tier != c.Infra.DEFAULT_SRC_DIR and (root / tier).is_dir()
            ),
        )
        seeds: list[p.Infra.CodegenFilePlan] = []
        for directory, prefix, stems in namespaces:
            renderings: dict[Path, str] = {}
            if prefix:
                name = f"{prefix}{project.class_stem}Service"
                renderings[directory / "base.py"] = u.Infra.generate_module_skeleton(
                    context=m.Infra.ModuleSkeletonRenderContext(
                        class_name=name,
                        base_class=f"{project.class_stem}Service",
                        base_module=project.package_name,
                        docstring=name,
                    )
                ).unwrap()
            for family in u.Infra.facade_families().values():
                if prefix:
                    name = f"{prefix}{project.class_stem}{family.suffix}"
                    renderings[directory / f"{family.module}.py"] = (
                        u.Infra.generate_test_module_skeleton(
                            context=m.Infra.TestModuleSkeletonRenderContext(
                                class_name=name,
                                base_class=f"FlextTests{family.suffix}",
                                project_module=project.package_name,
                                alias=family.letter,
                                namespace="Tests",
                                project_namespace=project.namespace,
                                docstring=name,
                            )
                        )
                    )
                for stem in stems:
                    path = directory / f"_{family.module}" / f"{stem}.py"
                    name = (
                        f"{prefix}{project.class_stem}{family.suffix}"
                        f"{u.derive_class_stem(stem)}"
                    )
                    renderings[path] = u.Infra.generate_module_skeleton(
                        context=m.Infra.ModuleSkeletonRenderContext(
                            class_name=name,
                            base_class=None,
                            base_module=None,
                            docstring=name,
                        )
                    ).unwrap()
            for path, source in renderings.items():
                if path in occupied or path.is_file():
                    continue
                before = u.Cli.atomic_read_binary_file_state(
                    path, required=False
                ).unwrap()
                seeds.append(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before,
                        desired_content=source.encode(c.DEFAULT_ENCODING),
                        desired_mode=config.Infra.codegen.modes.file_default,
                    )
                )
        return tuple(seeds)

    @override
    def execute(self) -> p.Result[str]:
        """Execute scaffolding directly from the validated CLI model.

        Returns:
            The resulting ``p.Result[str]``.

        """
        dry_run = self.dry_run or not self.apply_changes
        planned = self.run(dry_run=dry_run)
        if planned.failure:
            return r[str].from_failure(planned)
        results = planned.value
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
            f"Scaffold: {total_created} created, {total_skipped} skipped"
            f" across {len(results)} projects",
        )
        return r[str].ok("\n".join(lines))

    def run(
        self,
        *,
        dry_run: bool = False,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> p.Result[Sequence[p.Infra.ScaffoldResult]]:
        """Scaffold missing base modules for all projects in workspace.

        Args:
            dry_run: If True, only report changes without writing.
            projects: Pre-discovered projects to skip redundant discovery.

        Returns:
            List of ScaffoldResult models, one per project.

        """
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            discovered = u.Infra.projects(self.repository_root)
            if discovered.failure:
                return r[Sequence[p.Infra.ScaffoldResult]].from_failure(discovered)
            selected_projects = tuple(discovered.value)
        return r.traverse(
            selected_projects,
            lambda project: self._scaffold_project(project, dry_run=dry_run),
        )

    def _scaffold_project(
        self,
        project: p.Infra.ProjectInfo,
        *,
        dry_run: bool = False,
    ) -> p.Result[p.Infra.ScaffoldResult]:
        """Scaffold missing base modules for a single project.

        Args:
            project: Project descriptor or project root path.
            dry_run: If True, only report changes without writing.

        Returns:
            ScaffoldResult with lists of created and skipped files.

        """
        project_path = project.path
        files_created: MutableSequence[str] = []
        files_skipped: MutableSequence[str] = []
        project_layout = (
            u.Infra.layout(project_path)
            if (project_path / c.Infra.DEFAULT_SRC_DIR).is_dir()
            else None
        )
        if project_layout is not None and project_layout.class_stem:
            for request in self._scaffold_dir_requests(
                project_path, project_layout, dry_run=dry_run
            ):
                planned = self._scaffold_dir(request)
                if planned.failure:
                    return r[p.Infra.ScaffoldResult].from_failure(planned)
                created, skipped = planned.value
                files_created.extend(created)
                files_skipped.extend(skipped)
        return r[p.Infra.ScaffoldResult].ok(
            m.Infra.ScaffoldResult(
                project=project_path.name,
                files_created=files_created,
                files_skipped=files_skipped,
            )
        )

    @staticmethod
    def _scaffold_dir_requests(
        project_path: Path,
        project_layout: p.Infra.RopeProjectLayout,
        *,
        dry_run: bool,
    ) -> tuple[p.Infra.ScaffoldDirRequest, ...]:
        """Declare the scaffold request of every present project namespace.

        Returns:
            The ordered requests for the package, tests, examples and scripts
            directories that exist in the project.

        """
        package = project_layout.package_name
        namespaces = (
            (
                project_layout.init_path.is_file(),
                project_layout.package_dir,
                c.Infra.SRC_MODULES,
                "",
                c.Infra.PKG_CORE_UNDERSCORE,
                False,
            ),
            (
                (project_path / c.Infra.DIR_TESTS).is_dir(),
                project_path / c.Infra.DIR_TESTS,
                c.Infra.TESTS_MODULES,
                "Tests",
                c.Infra.PKG_TESTS_UNDERSCORE,
                True,
            ),
            (
                (project_path / c.Infra.DIR_EXAMPLES).is_dir(),
                project_path / c.Infra.DIR_EXAMPLES,
                c.Infra.SRC_MODULES,
                "Examples",
                package,
                False,
            ),
            (
                (project_path / c.Infra.DIR_SCRIPTS).is_dir(),
                project_path / c.Infra.DIR_SCRIPTS,
                c.Infra.SRC_MODULES,
                "Scripts",
                package,
                False,
            ),
        )
        return tuple(
            m.Infra.ScaffoldDirRequest(
                target_dir=target_dir,
                prefix=project_layout.class_stem,
                modules=modules,
                test_prefix=test_prefix,
                base_module=base_module,
                project_module=package,
                test_module=test_module,
                dry_run=dry_run,
                files_created=[],
                files_skipped=[],
            )
            for present, target_dir, modules, test_prefix, base_module, test_module in (
                namespaces
            )
            if present
        )

    @staticmethod
    def _scaffold_dir(
        request: p.Infra.ScaffoldDirRequest,
    ) -> p.Result[tuple[MutableSequence[str], MutableSequence[str]]]:
        """Generate missing modules in a directory and return file lists.

        Returns:
            The resulting ``tuple[MutableSequence[str],
                MutableSequence[str]]``.

        """
        files_created: MutableSequence[str] = []
        files_skipped: MutableSequence[str] = []
        for filename, suffix, base_class, doc_suffix in request.modules:
            filepath = request.target_dir / filename
            if filepath.exists():
                files_skipped.append(str(filepath))
                continue
            class_name = f"{request.test_prefix}{request.prefix}{suffix}"
            docstring = f"{doc_suffix} for {request.prefix.lower()}."
            if request.test_module:
                alias = u.Infra.facade_family_declared_by(filename).letter
                content = u.Infra.generate_test_module_skeleton(
                    context=m.Infra.TestModuleSkeletonRenderContext(
                        class_name=class_name,
                        base_class=base_class,
                        project_module=request.project_module,
                        alias=alias,
                        namespace=f"{request.test_prefix}{request.prefix}",
                        project_namespace=request.prefix.removeprefix(
                            c.Infra.PKG_PREFIX_UNDERSCORE.rstrip("_").capitalize(),
                        ),
                        docstring=docstring,
                    ),
                )
            else:
                rendered = u.Infra.generate_module_skeleton(
                    context=m.Infra.ModuleSkeletonRenderContext(
                        class_name=class_name,
                        base_class=base_class,
                        base_module=request.base_module,
                        docstring=docstring,
                    )
                )
                if rendered.failure:
                    return r[
                        tuple[MutableSequence[str], MutableSequence[str]]
                    ].from_failure(rendered)
                content = rendered.value
            if request.dry_run:
                files_created.append(str(filepath))
                continue
            before = u.Cli.atomic_read_binary_file_state(filepath, required=False)
            if before.failure:
                return r[
                    tuple[MutableSequence[str], MutableSequence[str]]
                ].from_failure(before)
            planned = m.Infra.CodegenFilePlan(
                project=request.target_dir,
                path=filepath,
                before=before.value,
                desired_content=content.encode(c.DEFAULT_ENCODING),
                desired_mode=config.Infra.codegen.modes.file_default,
                owner="codegen",
            )
            u.Infra.contained_write_targets(planned.project, (planned.path,))
            lock = u.Infra.mutation_lock_path(planned.project)
            if lock.failure:
                return r[
                    tuple[MutableSequence[str], MutableSequence[str]]
                ].from_failure(lock)
            written = u.Cli.publish_file_changes((planned,), lock_path=lock.value)
            if written.failure:
                return r[
                    tuple[MutableSequence[str], MutableSequence[str]]
                ].from_failure(written)
            if not written.value:
                files_skipped.append(str(filepath))
                continue
            files_created.append(str(filepath))
        return r[tuple[MutableSequence[str], MutableSequence[str]]].ok((
            files_created,
            files_skipped,
        ))


__all__: list[str] = ["FlextInfraCodegenScaffolder"]
