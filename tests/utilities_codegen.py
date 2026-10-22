"""Codegen and lazy-init fixture test utilities for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from multiprocessing import get_context
from pathlib import Path

from typing_extensions import TypeForm

from flext_infra import config, r, u
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenLazyInit,
)
from tests import (
    TestsFlextInfraUtilitiesGitMixin,
    TestsFlextInfraUtilitiesProjectFixtureMixin,
    TestsFlextInfraUtilitiesTomlMixin,
    TestsFlextInfraUtilitiesToolingFixtureMixin,
    c,
    m,
    p,
    t,
    tm,
)


class TestsFlextInfraUtilitiesCodegenMixin:
    """Codegen and lazy-init workspace fixture helpers."""

    @staticmethod
    def family_public_module(family: str) -> str:
        """Return the public facade module stem the core package gives a letter.

        Returns:
            The public facade module stem the core package gives a letter.

        """
        return u.Infra.facade_families()[family].module

    @staticmethod
    def ruff_policy_toml() -> str:
        """Render the fleet Ruff policy as a pyproject fragment.

        Reads the same typed SSOT production reads (P0): fixture
        workspaces carry the real rule selection, elected rule owners, native
        convention, preview, and import policy without exemption tables.

        Returns:
            The resulting ``str``.

        """
        ruff_cfg = config.Infra.tooling.tools.ruff
        delegated = FlextInfraGateRegistry.default().delegated_lint_rules(
            ruff_cfg.lint.rule_owners,
            check_gates=config.Infra.codegen.make.check_gates_default,
            repair_gates=(
                *config.Infra.codegen.make.check_gates_fixable,
                *config.Infra.codegen.make.fmt_gates,
            ),
        )
        options = u.Infra.native_tool_configuration(config.Infra.tooling, "ruff")
        options["target-version"] = (
            "py" + config.Infra.codegen.toolchain.python_version.replace(".", "")
        )
        lint = u.Cli.toml_mapping_ensure_table(options, "lint")
        u.Cli.toml_mapping_sync_string_list(
            lint,
            "ignore",
            sorted({
                *delegated,
                *ruff_cfg.lint.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "ignore", TypeForm(t.StrSequence)
                ),
            }),
        )
        return u.Cli.toml_dumps(
            u.Cli.toml_document_from_mapping({"tool": {"ruff": options}})
        )

    @staticmethod
    def conform_request(
        root: Path,
        *,
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
        scope: c.Infra.CodegenConformScope = c.Infra.CodegenConformScope.SELF,
        mode: c.Infra.CodegenConformMode = c.Infra.CodegenConformMode.CHECK,
    ) -> m.Infra.CodegenConformRequest:
        """Build one codegen conform request; every default is the model's own.

        Returns:
            The resulting ``m.Infra.CodegenConformRequest``.

        """
        return m.Infra.CodegenConformRequest(
            root=root,
            what=what,
            scope=scope,
            mode=mode,
        )

    @staticmethod
    def conform_plan(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        *,
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
    ) -> m.Infra.CodegenPlan:
        """Plan one fixture workspace through the public conform boundary.

        Returns:
            The resulting ``m.Infra.CodegenPlan``.

        """
        request = TestsFlextInfraUtilitiesCodegenMixin.conform_request(root, what=what)
        return (
            FlextInfraCodegenConform(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    request=request,
                    initial_workspace=workspace,
                ),
            )
            .plan(request)
            .unwrap()
        )

    @staticmethod
    def conform_makefile_text(root: Path, workspace: m.Infra.WorkspaceSpec) -> str:
        """Render the root Makefile conform plans for one fixture workspace.

        Returns:
            The resulting ``str``.

        """
        plan = TestsFlextInfraUtilitiesCodegenMixin.conform_plan(
            root,
            workspace,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        return TestsFlextInfraUtilitiesTomlMixin.codegen_file_text(makefile)

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
        for entry in config.Infra.codegen.templates.entries:
            destination = entry.destination.format(
                package_name="fixture_project",
                ns="fixture_project",
            )
            (root / destination).parent.mkdir(parents=True, exist_ok=True)
        for managed in config.Infra.codegen.managed_files:
            (root / managed.path).parent.mkdir(parents=True, exist_ok=True)
        # Scaffold entries create declaration family directories, and the
        # facade completeness law rejects owners without their public facade.
        package_dir = root / "src" / "fixture_project"
        for family in ("u", "p"):
            facade = (
                package_dir
                / f"{TestsFlextInfraUtilitiesCodegenMixin.family_public_module(family)}"
                ".py"
            )
            if (
                package_dir / u.Infra.facade_families()[family].directory
            ).is_dir() and (not facade.is_file()):
                facade.write_text(
                    f"class FixtureProject{family.capitalize()}Facade:\n    pass\n",
                    encoding="utf-8",
                )
        result = FlextInfraCodegenConform(repository_root=root).plan(
            TestsFlextInfraUtilitiesCodegenMixin.conform_request(root),
        )
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
    def create_lazy_init_workspace(
        tmp_path: Path,
        *,
        project_name: str = "flext-test-project",
        package_name: str = "flext_test_project",
    ) -> t.Pair[Path, Path]:
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
            assert process.exitcode == 0, (
                f"Native test callable exited {process.exitcode}: {target}"
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
        service = FlextInfraCodegenLazyInit(repository_root=repository_root)
        planned = service.plan_files().unwrap()
        changed = tuple(
            plan for plan in planned.files if u.Infra.codegen_file_requires_effect(plan)
        )
        if check_only:
            return len(changed)
        materialized = TestsFlextInfraUtilitiesCodegenMixin.materialize_lazy_init(
            service,
        )
        return 0 if materialized.success else 1

    @staticmethod
    def plan_lazy_init(repository_root: Path) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Return the lazy-init planning receipt WITHOUT unwrapping it.

        Refusing to plan is a first-class planning outcome — ambiguous export
        ownership stops the phase before a single file plan is built. A helper
        that unwraps turns that refusal into an exception and makes the
        pre-effect contract unobservable through the public surface.

        Returns:
            The lazy-init planning receipt WITHOUT unwrapping it.

        """
        return FlextInfraCodegenLazyInit(repository_root=repository_root).plan_files()

    @staticmethod
    def materialize_lazy_init(service: FlextInfraCodegenLazyInit) -> p.Result[bool]:
        """Publish one service plan through canonical guarded file primitives.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        planned = service.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        return TestsFlextInfraUtilitiesCodegenMixin.materialize_codegen_plans(
            r[tuple[m.Infra.CodegenFilePlan, ...]].ok(planned.value.files),
        )

    @staticmethod
    def materialize_codegen_plans(
        planned: p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]],
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
        for plan in changed:
            before = u.Infra.codegen_file_before_state(plan)
            if plan.desired_content is not None and (
                before.failure or before.value.parent_inode is None
            ):
                # Planning is read-only, so a destination planned into an absent
                # directory chain carries no parent identity. Like the
                # transaction owner at apply, the publisher materializes the
                # chain and reads the destination again before publishing.
                plan.path.parent.mkdir(parents=True, exist_ok=True)
                before = u.Cli.atomic_read_binary_file_state(plan.path)
            if before.failure:
                return r[bool].from_failure(before)
            if plan.desired_content is None:
                result = u.Cli.atomic_delete_binary_file_guarded(before.value)
            else:
                if plan.desired_mode is None:
                    return r[bool].fail(
                        f"lazy-init plan has no desired mode: {plan.path}",
                    )
                result = u.Cli.atomic_write_binary_file_guarded(
                    before.value,
                    plan.desired_content,
                    permission_mode=plan.desired_mode,
                )
            if result.failure:
                return r[bool].from_failure(result)
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
        if not (project / ".git").exists():
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
    def create_lazy_init_service(repository_root: Path) -> FlextInfraCodegenLazyInit:
        """Provide the typed test helper `create_lazy_init_service`.

        Returns:
            The resulting ``FlextInfraCodegenLazyInit``.

        """
        return FlextInfraCodegenLazyInit(repository_root=repository_root)

    @staticmethod
    def lazy_init_scenario(
        tmp_path: Path,
    ) -> t.Triple[Path, Path, FlextInfraCodegenLazyInit]:
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
    def extract_lazy_init_exports(source: str) -> t.Pair[bool, t.StrSequence]:
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
        service: FlextInfraCodegenConsolidator = FlextInfraCodegenConsolidator(
            repository_root=repository_root,
            dry_run=dry_run,
            project_name=project,
        )
        result: p.Result[str] = service.execute()
        return result


__all__: list[str] = ["TestsFlextInfraUtilitiesCodegenMixin"]
