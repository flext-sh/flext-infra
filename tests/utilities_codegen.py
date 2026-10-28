"""Codegen and lazy-init fixture test utilities for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from multiprocessing import get_context
from pathlib import Path

from flext_infra import codegen, config, u, workspace
from tests import (
    TestsFlextInfraUtilitiesGitMixin,
    TestsFlextInfraUtilitiesProjectFixtureMixin,
    TestsFlextInfraUtilitiesToolingFixtureMixin,
    c,
    m,
    p,
    r,
    t,
    tm,
    utilities_conform,
)


class TestsFlextInfraUtilitiesCodegenMixin(
    utilities_conform.TestsFlextInfraUtilitiesConform,
):
    """Public conformance and scaffold fixture helpers."""

    @staticmethod
    def scaffold_plan(
        root: Path,
        *,
        members: t.StrSequence = (),
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
    ) -> m.Infra.CodegenPlan:
        """Plan the artifacts conform renders for a fresh repository scaffold.

        Without members the fixture repository is standalone; each member
        makes it a workspace composing that project, so generated surfaces
        are observed exactly as the public codegen owner renders them.
        ``what`` selects the conform surface, so a scenario about one surface
        never pays for planning every template.

        Returns:
            The resulting ``m.Infra.CodegenPlan``.

        """
        fixture = TestsFlextInfraUtilitiesProjectFixtureMixin
        # A governed repository carries its committed Mise lock; generation
        # formats through the release it pins and never resolves a selector.
        TestsFlextInfraUtilitiesToolingFixtureMixin.copy_tracked_mise_seeds(root)
        for name in members:
            manifest = root / name / c.PYPROJECT_FILENAME
            if not manifest.exists():
                manifest.parent.mkdir(parents=True, exist_ok=True)
                tm.ok(
                    u.Cli.toml_write_mapping(
                        manifest,
                        {
                            "project": {
                                "name": name,
                                "version": tm.ok(
                                    u.Infra.current_workspace_version(Path.cwd()),
                                ),
                                "dependencies": [],
                            },
                            "tool": {
                                "flext": {
                                    "docs": {
                                        "package_name": fixture.project_spec(
                                            name,
                                        ).package_name,
                                    },
                                },
                            },
                        },
                    ),
                )
        repository = fixture.repository_ref(
            "fixture-project",
            role=(
                c.Infra.MakeProfile.WORKSPACE
                if members
                else c.Infra.MakeProfile.STANDALONE
            ),
        )
        control = root / c.Infra.GIT_DIR
        if not control.exists() and not control.is_symlink():
            TestsFlextInfraUtilitiesGitMixin.git_bootstrap(
                root, ("init", "-b", fixture.provider_branch())
            )
            TestsFlextInfraUtilitiesGitMixin.git_bootstrap(
                root, ("remote", "add", c.Infra.GIT_ORIGIN, repository.url)
            )
        return TestsFlextInfraUtilitiesCodegenMixin.conform_plan(
            root,
            fixture.workspace_spec(
                repository,
                project=fixture.project_spec(repository.name),
                subprojects=tuple(
                    fixture.repository_ref(name, path=Path(name)) for name in members
                ),
            ),
            what=what,
            executor_root=Path.cwd(),
        )

    @staticmethod
    def scaffold_text(
        root: Path,
        destination: str,
        *,
        members: t.StrSequence = (),
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
    ) -> str:
        """Return one rendered scaffold artifact, failing when it is not planned.

        Returns:
            One rendered scaffold artifact, failing when it is not planned.

        """
        plan = TestsFlextInfraUtilitiesCodegenMixin.scaffold_plan(
            root,
            members=members,
            what=what,
        )
        tm.that(plan.issues, eq=(), msg=str(plan.issues))
        return tm.not_none(
            TestsFlextInfraUtilitiesCodegenMixin.planned_text(plan, destination),
        )

    @staticmethod
    def governed_project_plan(root: Path) -> m.Infra.CodegenPlan:
        """Plan every declared artifact of one governed fixture project read-only.

        Returns:
            The resulting ``m.Infra.CodegenPlan``.

        """
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        declared = tm.ok(
            workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                root, inputs=inputs
            ),
        )
        metadata = tm.ok(u.Infra.read_project_metadata_result(root))
        project = declared.project
        package_name = (
            metadata.package_name if project is None else project.package_name
        )
        class_stem = metadata.class_stem if project is None else project.class_stem
        namespace = (
            u.Infra.package_alias(package_name=package_name)
            if project is None
            else project.namespace_attribute
        )
        for entry in inputs.spec.templates.entries:
            if declared.repository.role not in entry.profiles:
                continue
            destination = entry.destination.format(
                package_name=package_name,
                ns=namespace,
                **u.Infra.runtime_module_names(
                    project_name=declared.repository.distribution,
                    codegen=inputs.spec,
                ),
            )
            (root / destination).parent.mkdir(parents=True, exist_ok=True)
        # Scaffold entries create declaration family directories, and the
        # facade completeness law rejects owners without their public facade.
        package_dir = root / c.Infra.DEFAULT_SRC_DIR / package_name
        for family in u.Infra.facade_families().values():
            facade = package_dir / f"{family.module}.py"
            if (package_dir / family.directory).is_dir() and not facade.is_file():
                facade.write_text(
                    f"class {class_stem}{family.suffix}:\n    pass\n",
                    encoding="utf-8",
                )
        request = TestsFlextInfraUtilitiesCodegenMixin.conform_request(root)
        result = codegen.FlextInfraCodegenConform.Generate(
            state=m.Infra.CodegenConformState(repository_root=root, request=request),
        ).plan(request)
        return m.Infra.CodegenPlan.model_validate(tm.ok(result))

    @staticmethod
    def planned_text(plan: m.Infra.CodegenPlan, destination: str) -> str | None:
        """Return the desired text of the plan entry ending with ``destination``.

        Returns:
            The desired text of the plan entry ending with ``destination``.

        """
        match = next(
            (item for item in plan.files if item.path.as_posix().endswith(destination)),
            None,
        )
        return (
            None
            if match is None or match.desired_content is None
            else tm.not_none(match.desired_content).decode(c.DEFAULT_ENCODING)
        )

    @staticmethod
    @contextmanager
    def authenticated_rope_workspace(
        repository_root: Path,
    ) -> Generator[p.Infra.RopeWorkspaceDsl]:
        """Borrow the public source view for one native planning session.

        Yields:
            A workspace bound to the overlaid source view.

        """
        with (
            u.Infra.facade_source_project(repository_root) as (project, _),
            workspace.FlextInfraRopeWorkspace.open_workspace(
                repository_root, source_project=project
            ) as rope_workspace,
        ):
            yield rope_workspace

    @staticmethod
    def create_lazy_init_workspace(
        tmp_path: Path,
        *,
        project_name: str = "flext-test-project",
        package_name: str = "flext_test_project",
    ) -> tuple[Path, Path]:
        """Create a real workspace with an empty, generation-eligible initializer.

        Returns:
            The resulting ``t.Pair[Path, Path]``.

        """
        repository_root = tmp_path / project_name
        project = TestsFlextInfraUtilitiesProjectFixtureMixin.project_spec(project_name)
        upstream = TestsFlextInfraUtilitiesProjectFixtureMixin.flext_source(
            project.upstream,
        )
        package_root = repository_root / c.Infra.DEFAULT_SRC_DIR / package_name
        package_root.mkdir(parents=True)
        (repository_root / "Makefile").write_text(
            "check:\n\t@true\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (repository_root / c.PYPROJECT_FILENAME).write_text(
            (
                f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n'
                f'dependencies = ["{upstream}"]\n'
                f'license = "{project.license}"\n'
                f'authors = [{{name = "{project.author_name}", '
                f'email = "{project.author_email}"}}]\n\n'
                "[tool.hatch.build.targets.wheel]\n"
                f'packages = ["{c.Infra.DEFAULT_SRC_DIR}/{package_name}"]\n\n'
                + TestsFlextInfraUtilitiesCodegenMixin.ruff_policy_toml()
            ),
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (package_root / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            repository_root,
            project_name,
        )
        # Semantic publication authenticates every changed path against its Git
        # checkout.  The shared workspace fixture therefore owns a real,
        # repository-local identity instead of letting individual tests depend
        # on whichever checkout happens to contain ``tmp_path``.
        TestsFlextInfraUtilitiesGitMixin.initialize_git_repo(
            repository_root,
            TestsFlextInfraUtilitiesProjectFixtureMixin.repository_ref(
                project_name
            ).url,
        )
        return (repository_root, package_root)

    @staticmethod
    def write_lazy_init_namespace_module(
        module_path: Path,
        *,
        class_name: str,
        alias: str,
        docstring: str = "Test namespace.",
        extra_class_names: t.StrSequence = (),
    ) -> None:
        """Write a namespace module fixture for lazy-export tests."""
        export_list = f'"{class_name}", "{alias}"'
        extra_classes = "".join(
            f'\nclass {extra_class_name}:\n    """Additional namespace '
            f'declaration."""\n'
            for extra_class_name in extra_class_names
        )
        notice = u.Infra.copyright_notice(module_path.parent, module=module_path)
        module_path.write_text(
            (
                f'"""{docstring}\n\n{notice}\n"""\n\n'
                "from __future__ import annotations\n\n"
                f"__all__: list[str] = [{export_list}]\n\n"
                f"class {class_name}:\n"
                '    """Public namespace declaration."""\n\n'
                f"{alias} = {class_name}\n"
                f"{extra_classes}"
            ),
            encoding=c.Infra.ENCODING_DEFAULT,
        )

    @staticmethod
    def write_lazy_init_version_module(package_root: Path) -> None:
        """Write a version module fixture for lazy-export tests."""
        (package_root / "__version__.py").write_text(
            ('__version__ = "0.1.0"\n__version_info__ = (0, 1, 0)\n'),
            encoding=c.Infra.ENCODING_DEFAULT,
        )

    @staticmethod
    def run_native_callable[**P](
        target: Callable[P, None], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        """Run a real callable under the native runner's aggregate process wall."""
        policy = config.Infra.tooling.tools.pytest
        process = get_context("spawn").Process(target=target, args=args, kwargs=kwargs)
        process.start()
        try:
            process.join()
            tm.that(
                process.exitcode,
                eq=0,
                msg=f"Native test callable exited {process.exitcode}: {target}",
            )
        finally:
            if process.is_alive():
                process.terminate()
                process.join(policy.termination_grace_seconds)
            if process.is_alive():
                process.kill()
                process.join(policy.termination_grace_seconds)
            process.close()

    @staticmethod
    def run_lazy_init_probe(
        probe: str,
        *,
        python_paths: t.StrSequence = (),
        cwd: Path | None = None,
        arguments: t.StrSequence = (),
        runtime_root: Path | None = None,
    ) -> t.StrSequence:
        """Run ``probe`` in a fresh interpreter importing generated packages.

        The probe observes generated initializers through Python's real import
        machinery, isolated from the test process's already imported modules.

        Returns:
            The probe's standard output lines.

        Raises:
            ValueError: If an installed project probe injects Python source paths.

        """
        if runtime_root is not None:
            if python_paths:
                msg = "An installed project probe cannot inject Python source paths"
                raise ValueError(msg)
            command = [str(u.Infra.runtime_python(runtime_root)), "-I", "-c", probe]
            options = m.Cli.ProcessOptions(remove_env_keys=("PYTHONPATH", "PYTHONHOME"))
        else:
            probe_env = dict(os.environ)
            probe_env["PYTHONPATH"] = os.pathsep.join(python_paths)
            command = [sys.executable, "-c", probe]
            options = m.Cli.ProcessOptions(env=probe_env)
        result = tm.ok(
            u.Cli.run(
                [*command, *arguments],
                options=options,
                cwd=cwd,
            ),
        )
        return result.stdout.splitlines()

    @staticmethod
    def run_lazy_init(repository_root: Path, *, check_only: bool = False) -> int:
        """Materialize immutable lazy-init plans only inside test workspaces.

        Returns:
            The resulting ``int``.

        """
        service = codegen.FlextInfraCodegenLazyInit(repository_root=repository_root)
        planned = service.plan_files().unwrap()
        changed = tuple(
            plan for plan in planned if u.Infra.codegen_file_requires_effect(plan)
        )
        if check_only:
            return len(changed)
        materialized = TestsFlextInfraUtilitiesCodegenMixin.materialize_lazy_init(
            service,
        )
        return 0 if materialized.success else 1

    @staticmethod
    def lazy_init_effects(
        planned: p.Result[tuple[m.Infra.CodegenFilePlan, ...]],
    ) -> t.StrSequence:
        """Return the destinations a successful lazy-init plan would change.

        Returns:
            The changed destination paths, sorted.

        """
        return tuple(
            str(plan.path)
            for plan in tm.ok(planned)
            if u.Infra.codegen_file_requires_effect(plan)
        )

    @staticmethod
    def demo_lazy_init_workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Create the ``flext-demo`` lazy-init workspace.

        Returns:
            The repository root and the ``flext_demo`` package directory.

        """
        return TestsFlextInfraUtilitiesCodegenMixin.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )

    @staticmethod
    def generated_init(package_root: Path) -> str:
        """Read one package's initializer.

        Returns:
            The initializer source.

        """
        return package_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING,
        )

    @staticmethod
    def materialize_lazy_init(
        service: codegen.FlextInfraCodegenLazyInit,
    ) -> p.Result[bool]:
        """Publish one service plan through canonical guarded file primitives.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return TestsFlextInfraUtilitiesCodegenMixin.materialize_codegen_plans(
            service.plan_files(),
        )

    @staticmethod
    def materialize_codegen_plans(
        planned: p.Result[tuple[m.Infra.CodegenFilePlan, ...]],
    ) -> p.Result[bool]:
        """Publish immutable codegen plans only inside test workspaces.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if planned.failure:
            return r[bool].from_failure(planned)
        changed = tuple(
            plan for plan in planned.value if u.Infra.codegen_file_requires_effect(plan)
        )
        if not changed:
            return r[bool].ok(value=True)
        lock = u.Infra.mutation_lock_path(changed[0].project)
        if lock.failure:
            return r[bool].from_failure(lock)
        published = u.Cli.publish_file_changes(changed, lock_path=lock.value)
        if published.failure:
            return r[bool].from_failure(published)
        for project in sorted({plan.project for plan in changed}):
            TestsFlextInfraUtilitiesCodegenMixin._stage_changed_codegen_plans(
                changed, project
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _stage_changed_codegen_plans(
        changed: tuple[m.Infra.CodegenFilePlan, ...],
        project: Path,
    ) -> None:
        if not (project / c.GIT_DIR_NAME).exists():
            return
        visible = frozenset(tm.not_none(u.Infra.git_source_scope_paths(project)))
        targets: list[str] = []
        for plan in changed:
            if plan.project != project:
                continue
            relative = plan.path.relative_to(project).as_posix()
            if plan.path not in visible and plan.desired_content is not None:
                continue
            if plan.path not in visible and plan.desired_content is None:
                tracked = tm.ok(
                    u.Infra.git_is_tracked(
                        m.Infra.GitRelativePathRequest(
                            repo_root=project, relative_path=relative
                        )
                    )
                )
                if not tracked.value:
                    continue
            targets.append(relative)
        if targets:
            TestsFlextInfraUtilitiesGitMixin.git_bootstrap(
                project, ("add", "--", *targets)
            )

    @staticmethod
    def create_lazy_init_service(
        repository_root: Path,
    ) -> codegen.FlextInfraCodegenLazyInit:
        """Provide the typed test helper `create_lazy_init_service`.

        Returns:
            The resulting ``FlextInfraCodegenLazyInit``.

        """
        return codegen.FlextInfraCodegenLazyInit(repository_root=repository_root)

    @staticmethod
    def lazy_init_scenario(
        tmp_path: Path,
    ) -> tuple[Path, Path, codegen.FlextInfraCodegenLazyInit]:
        """Create the workspace, write its namespace module, build the service.

        Returns:
            The resulting ``t.Triple[Path, Path, FlextInfraCodegenLazyInit]``.

        """
        repository_root, package_root = (
            TestsFlextInfraUtilitiesCodegenMixin.create_lazy_init_workspace(tmp_path)
        )
        TestsFlextInfraUtilitiesCodegenMixin.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        init_path = package_root / c.Infra.INIT_PY
        service = TestsFlextInfraUtilitiesCodegenMixin.create_lazy_init_service(
            repository_root,
        )
        return package_root, init_path, service

    @staticmethod
    def extract_lazy_init_exports(source: str) -> tuple[bool, t.StrSequence]:
        """Read the published lazy export contract through the public source reader.

        Returns:
            The resulting ``t.Pair[bool, t.StrSequence]``.

        """
        exports = u.Infra.module_assignment_strings_source(source, c.Infra.DUNDER_ALL)
        return (bool(exports), exports)

    @staticmethod
    def consolidate_codegen(
        *,
        repository_root: Path,
        project: str | None = None,
        dry_run: bool = True,
    ) -> p.Result[str]:
        """Provide the typed test helper `consolidate_codegen`.

        Returns:
            The resulting ``p.Result[str]``.

        """
        service = codegen.FlextInfraCodegenConsolidator(
            repository_root=repository_root,
            dry_run=dry_run,
            project_name=project,
        )
        result: p.Result[str] = service.execute()
        return result


__all__: list[str] = ["TestsFlextInfraUtilitiesCodegenMixin"]
