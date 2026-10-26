"""Read-only publication plans for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenLazyInit
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenLazyInitFilePlans:
    """Prove lazy-init describes effects without owning publication."""

    @staticmethod
    @pytest.mark.parametrize("injected", [False, True])
    def test_planned_initializer_publishes_without_touching_authored_tests(
        tmp_path: Path,
        *,
        injected: bool,
    ) -> None:
        """Publishing planned initializers never rewrites an authored test module."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tests = root / c.Infra.DIR_TESTS
        tests.mkdir()
        (tests / c.Infra.INIT_PY).write_text(
            "__all__ = []\n", encoding=c.DEFAULT_ENCODING
        )
        conftest = tests / "conftest.py"
        conftest.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        authored = conftest.read_bytes()
        with ExitStack() as contexts:
            binding = (
                contexts.enter_context(
                    u.Infra.facade_source_project(root, project_roots=(root,)),
                )[0]
                if injected
                else None
            )
            analysis = tm.ok(
                u.Tests.create_lazy_init_service(root).plan_files(
                    source_project=binding,
                )
            )
        tm.that(
            (root / c.Infra.CODEGEN_LAZY_PLAN_REPORT_RELATIVE_PATH).exists(),
            eq=False,
        )
        tm.fail(conftest in {file.path for file in analysis})
        tm.ok(u.Infra.publish_codegen_plans(root, analysis))
        production = next(
            file for file in analysis if file.path == package / c.Infra.INIT_PY
        )
        tm.that(
            production.path.read_bytes(),
            eq=tm.ok(u.Infra.normalized_codegen_changes((production,)))[
                0
            ].desired_content,
        )
        tm.that(conftest.read_bytes(), eq=authored)

    @staticmethod
    def test_concurrent_target_edit_refuses_publication(tmp_path: Path) -> None:
        """A destination edited after planning is never overwritten."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / c.Infra.INIT_PY
        analysis = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.ok(any(file.path == target for file in analysis))
        foreign = target.read_bytes() + b"\n# Concurrent edit\n"
        target.write_bytes(foreign)
        tm.fail(u.Infra.publish_codegen_plans(root, analysis))
        tm.that(target.read_bytes(), eq=foreign)

    @staticmethod
    def test_authored_initializer_keeps_executable_declarations_after_generation(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Retain a real JSON loader, model and value through the public generator."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=u.Tests.python_dependency_projects(root),
                session_runtime=session_runtime,
            )
        )
        u.Tests.write_lazy_init_namespace_module(
            package / "models.py",
            class_name=u.derive_class_stem(root.name) + "Models",
            alias="m",
        )
        resource_package = package / "resource_owner"
        resource_package.mkdir()
        initializer = resource_package / c.Infra.INIT_PY
        initializer.write_text(
            '"""Load authored package data."""\n'
            "from importlib.resources import files\n"
            "from flext_core import m\n\n"
            f"class {u.derive_class_stem(root.name)}Payload(m.ContractModel):\n"
            "    value: int = m.Field(description='Loaded resource value')\n\n"
            f"Payload = {u.derive_class_stem(root.name)}Payload\n\n"
            "def load() -> Payload:\n"
            "    return Payload.model_validate_json(\n"
            "        files(__package__).joinpath('payload.json').read_text()\n"
            "    )\n\n"
            "VALUE = load().value\n"
            "__all__ = ['Payload', 'VALUE', 'load']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        value = 37
        (resource_package / "payload.json").write_text(
            f'{{"value": {value}}}\n',
            encoding=c.DEFAULT_ENCODING,
        )
        before = initializer.read_bytes()
        service = u.Tests.create_lazy_init_service(root)

        planned = tm.ok(service.plan_files())
        tm.fail(initializer in {file.path for file in planned})
        tm.that(
            (root / c.Infra.CODEGEN_LAZY_PLAN_REPORT_RELATIVE_PATH).exists(),
            eq=False,
        )
        workspace = u.Tests.standalone_workspace(root, root.name)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        tm.ok(TestsFlextInfraConformSupport.conform_in_workspace(request, workspace))

        tm.that(initializer.read_bytes(), eq=before)
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"import sys; sys.path.insert(0, {str(package.parent)!r}); "
                        f"from {package.name}.resource_owner import VALUE, load; "
                        "print(VALUE, load().value)"
                    ),
                ),
                cwd=root,
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))
        tm.that(consumer.stdout.strip(), eq=f"{value} {value}")

    @pytest.mark.parametrize("family", ["m", "p", "u"])
    def test_facade_plan_selects_declared_family_and_only_requested_module(
        self,
        tmp_path: Path,
        family: str,
    ) -> None:
        """Exact facade selection reuses discovery without rewriting other surfaces."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        workspace = u.Tests.standalone_workspace(root, root.name)
        destination = package / "selected.py"
        self._write_facade_selection_fixture(package, family)
        before = {
            path: path.read_bytes() for path in package.rglob(c.Infra.EXT_PYTHON_GLOB)
        }
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.FACADES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
            module=f"{package.name}.{destination.stem}",
        )

        plan = tm.ok(
            FlextInfraCodegenConform.Generate(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    initial_workspace=workspace,
                    request=request,
                ),
            ).plan(request),
        )

        tm.that(tuple(file.path for file in plan.files), eq=(destination,))
        tm.that(plan.uv_environments, eq=())
        file = plan.files[0]
        source = tm.not_none(file.desired_content).decode(c.DEFAULT_ENCODING)
        tm.that(source, has="PayloadOwner")
        tm.that(source, has="class Sample(ExistingOwner, PayloadOwner)")
        tm.that(source, has="retained = 'unchanged'")
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @staticmethod
    @pytest.fixture
    def seed_conform_scope_repositories(
        tmp_path: Path,
        scope: c.Infra.CodegenConformScope,
        session_runtime: p.Tests.SessionRuntime,
    ) -> tuple[Path, Path, list[Path]]:
        """Seed the root/member pair with runtime, git and lazy-init fixtures.

        Returns:
            The resulting ``tuple[Path, Path, list[Path]]`` of the workspace
            root, the member repository and the seeded package paths.

        """
        root = tmp_path / "flext-scope-root"
        member = root / "apps" / "flext-scope-member"
        packages: list[Path] = []
        for repository in (root, member):
            _, package = u.Tests.create_lazy_init_workspace(
                repository.parent,
                project_name=repository.name,
                package_name=repository.name.replace("-", "_"),
            )
            packages.append(package)
            u.Tests.initialize_git_repo(
                repository,
                origin_url=u.Tests.repository_ref(repository.name).url,
            )
            u.Tests.standalone_workspace(repository, repository.name)
            # Conform formats pyproject through the Taplo release the committed
            # Mise lock pins; generation never resolves a moving selector.
            u.Tests.copy_tracked_mise_seeds(repository)
            u.Tests.write_lazy_init_namespace_module(
                package / "models.py",
                class_name=u.derive_class_stem(repository.name) + "Models",
                alias="m",
            )
            u.Tests.commit_git_changes(repository, "Seed scope fixture")
        if scope is c.Infra.CodegenConformScope.DECLARED:
            # A members-only run meets a root that already carries its runtime
            # Mise declaration, launchers and pin: each member's launchers are
            # validated as projections of that runtime root.
            u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution=member.name,
            relative_path=member.relative_to(root).as_posix(),
        )
        # Attached members share the containing workspace's physical runtime.
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=u.Tests.python_dependency_projects(root),
                session_runtime=session_runtime,
            )
        )
        for repository in (root, member):
            u.Tests.provision_checkout(repository)
        return root, member, packages

    @staticmethod
    def _write_facade_selection_fixture(package: Path, family: str) -> None:
        """Declare a nonstandard destination and a local executable consumer."""
        directory = u.Infra.facade_families()[family].directory
        owners = package / directory
        owners.mkdir()
        payload = (
            "    @staticmethod\n    def Payload() -> None:\n        pass\n"
            if family == "u"
            else "    class Payload:\n        pass\n"
        )
        sources = {
            owners / "payload.py": (
                "class PayloadOwner:\n" + payload + "__all__ = ['PayloadOwner']\n"
            ),
            owners / "existing.py": (
                "class ExistingOwner:\n    pass\n__all__ = ['ExistingOwner']\n"
            ),
            package / "selected.py": (
                f"from {package.name}.{directory}.existing import ExistingOwner\n\n"
                "class Facade:\n"
                "    class Sample(ExistingOwner):\n"
                "        retained = 'unchanged'\n\n"
                f"{family} = Facade\n__all__ = ['Facade', '{family}']\n"
            ),
            package / "consumer.py": (
                f"from {package.name} import {family}\n{family}.Sample.Payload()\n"
            ),
            package / c.Infra.INIT_PY: f"from .selected import {family}\n",
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("scope", tuple(c.Infra.CodegenConformScope))
    def test_lazy_planning_owns_exact_conform_repositories(
        scope: c.Infra.CodegenConformScope,
        seed_conform_scope_repositories: tuple[Path, Path, list[Path]],
    ) -> None:
        """Read-only planning elects exactly the selected physical repositories."""
        root, member, packages = seed_conform_scope_repositories
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = u.Tests.conform_request(
            root,
            scope=scope,
            mode=c.Infra.CodegenConformMode.CHECK,
        ).model_copy(update={"what": c.Infra.CodegenConformSurface.LAZY_INIT})
        before = {
            package / c.Infra.INIT_PY: (package / c.Infra.INIT_PY).read_bytes()
            for package in packages
        }
        plan = tm.ok(
            FlextInfraCodegenConform.Generate(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    request=request,
                    initial_workspace=workspace,
                ),
            ).plan(request),
        )
        selected = tuple(
            (root / repository.path).resolve() for repository in plan.repositories
        )
        expected = (
            {root.resolve()}
            if scope is c.Infra.CodegenConformScope.SELF
            else {member.resolve()}
            if scope is c.Infra.CodegenConformScope.DECLARED
            else {root.resolve(), member.resolve()}
        )
        tm.that(set(selected), eq=expected)
        tm.that(
            {file.project for file in plan.files},
            eq=expected,
        )
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("scope", tuple(c.Infra.CodegenConformScope))
    def test_lazy_publication_owns_exact_conform_repositories(
        scope: c.Infra.CodegenConformScope,
        seed_conform_scope_repositories: tuple[Path, Path, list[Path]],
    ) -> None:
        """Publication and its public observation retain exact repository scope."""
        root, member, packages = seed_conform_scope_repositories
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = u.Tests.conform_request(
            root,
            scope=scope,
            mode=c.Infra.CodegenConformMode.APPLY,
        ).model_copy(update={"what": c.Infra.CodegenConformSurface.LAZY_INIT})
        before = {
            package / c.Infra.INIT_PY: (package / c.Infra.INIT_PY).read_bytes()
            for package in packages
        }
        published = tm.ok(
            TestsFlextInfraConformSupport.conform_in_workspace(request, workspace)
        )
        expected = {
            (root / repository.path).resolve()
            for repository in tm.not_none(published.plan).repositories
        }
        tm.that(
            expected,
            eq=(
                {root.resolve()}
                if scope is c.Infra.CodegenConformScope.SELF
                else {member.resolve()}
                if scope is c.Infra.CodegenConformScope.DECLARED
                else {root.resolve(), member.resolve()}
            ),
        )
        for repository, package in zip((root, member), packages, strict=True):
            initializer = package / c.Infra.INIT_PY
            tm.that(
                initializer.read_bytes() != before[initializer],
                eq=repository.resolve() in expected,
            )
        tm.ok(
            TestsFlextInfraConformSupport.conform_in_workspace(
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
                workspace,
            )
        )

    @staticmethod
    def test_scope_outside_workspace_fails_planning(
        tmp_path: Path,
    ) -> None:
        """An invalid scope fails loud without widening publication authority."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path / "workspace",
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        foreign_root = tmp_path / "foreign"
        foreign_root.mkdir()
        init_path = package_root / c.Infra.INIT_PY
        before = init_path.read_bytes()

        result = FlextInfraCodegenLazyInit(
            repository_root=repository_root,
            project_scope_roots=(foreign_root,),
        ).plan_files()

        tm.fail(result, has="lazy-init repository scope is missing")
        tm.that(str(result.error), has=str(foreign_root))
        tm.that(init_path.read_bytes(), eq=before)

    @staticmethod
    @pytest.mark.parametrize("injected", [False, True])
    def test_multi_root_epoch_elects_same_named_packages_by_physical_owner(
        tmp_path: Path,
        *,
        injected: bool,
    ) -> None:
        """A shared read epoch never elects a sibling's same-named module."""
        roots: list[Path] = []
        packages: list[Path] = []
        for name in ("FirstPublished", "SecondPublished"):
            root, package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=name.lower(),
                package_name="shared_package",
            )
            (package / "service.py").write_text(
                f"class {name}: pass\n__all__ = [{name!r}]\n",
                encoding=c.DEFAULT_ENCODING,
            )
            roots.append(root)
            packages.append(package)
        service = FlextInfraCodegenLazyInit(
            repository_root=tmp_path,
            project_scope_roots=tuple(reversed(roots)),
        )
        with ExitStack() as contexts:
            source: p.Infra.RopeProject | None = None
            if injected:
                source = contexts.enter_context(
                    u.Infra.facade_source_project(tmp_path, project_roots=tuple(roots)),
                )[0]
            analysis = tm.ok(service.plan_files(source_project=source))
        for index, name in enumerate(("FirstPublished", "SecondPublished")):
            plan = next(
                file
                for file in analysis
                if file.path == packages[index] / c.Infra.INIT_PY
            )
            tm.that(plan.project, eq=roots[index])
            tm.that(u.Tests.codegen_file_text(plan), contains=name)
            other = ("FirstPublished", "SecondPublished")[1 - index]
            tm.that(u.Tests.codegen_file_text(plan), lacks=other)
        repeated = tm.ok(service.plan_files())
        tm.that(
            tuple((file.path, file.desired_content) for file in analysis),
            eq=tuple((file.path, file.desired_content) for file in repeated),
        )
        service.module = "shared_package"
        tm.fail(service.plan_files(), has="target module is ambiguous")

    @staticmethod
    @pytest.mark.parametrize("failed_first", [False, True])
    def test_target_ambiguity_survives_candidate_planning_failure(
        tmp_path: Path,
        *,
        failed_first: bool,
    ) -> None:
        """Authorization counts physical candidates, not successful analyses."""
        roots: list[Path] = []
        for index, name in enumerate(("a-candidate", "z-candidate")):
            root, package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=name,
                package_name="shared_package",
            )
            roots.append(root)
            for module in (
                ("first", "second") if (index == 0) == failed_first else ("first",)
            ):
                (package / f"{module}.py").write_text(
                    "class Shared: pass\n__all__ = ['Shared']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
        tm.fail(
            FlextInfraCodegenLazyInit(
                repository_root=tmp_path,
                project_scope_roots=tuple(reversed(roots)),
                module="shared_package",
            ).plan_files(),
            has="target module is ambiguous",
        )

    @staticmethod
    def test_execute_rejects_apply_and_preserves_planned_targets(
        tmp_path: Path,
    ) -> None:
        """The standalone command is a check surface, never a second writer."""
        _, init_path, service = u.Tests.lazy_init_scenario(tmp_path)
        before = init_path.read_bytes()
        service.apply_changes = True

        result = service.execute()

        tm.ok(result.failure)
        tm.that(result.error, contains="owned by codegen conform")
        tm.that(init_path.read_bytes(), eq=before)

    @staticmethod
    def test_unknown_target_is_a_causal_plan_failure(tmp_path: Path) -> None:
        """A missing target fails instead of widening to the workspace."""
        _, init_path, service = u.Tests.lazy_init_scenario(tmp_path)
        before = init_path.read_bytes()
        service.module = "flext_missing"

        result = service.plan_files()

        tm.ok(result.failure)
        tm.that(result.error, contains="lazy-init target module not found")
        tm.that(init_path.read_bytes(), eq=before)
