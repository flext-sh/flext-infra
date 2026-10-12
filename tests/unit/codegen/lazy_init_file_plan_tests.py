"""Read-only publication plans for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u


class TestsFlextInfraCodegenLazyInitFilePlans:
    """Prove lazy-init describes effects without owning publication."""

    @staticmethod
    def test_authored_initializer_keeps_executable_declarations_after_generation(
        tmp_path: Path,
    ) -> None:
        """Retain a real JSON loader, model and value through the public generator."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        resource_package = package / "resource_owner"
        resource_package.mkdir()
        initializer = resource_package / c.Infra.INIT_PY
        initializer.write_text(
            '"""Load authored package data."""\n'
            "from importlib.resources import files\n"
            "from flext_core import m\n\n"
            "class Payload(m.ContractModel):\n"
            "    value: int\n\n"
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

        analysis = tm.ok(service.plan_files())
        retained = next(
            plan
            for plan in analysis.publications
            if plan.context.init_path == initializer
        )
        tm.that(retained.action, eq=c.Infra.LazyInitAction.RETAIN)
        tm.that(retained.ownership, eq="authored")
        tm.that(retained.disposition, eq="retained")
        tm.that(set(retained.exports), eq={"Payload", "VALUE", "load"})
        tm.that(initializer in {file.path for file in analysis.files}, eq=False)
        report = m.Infra.CodegenPhaseAnalysis.model_validate_json(
            (root / c.Infra.CODEGEN_LAZY_PLAN_REPORT_RELATIVE_PATH).read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
        )
        tm.that(
            any(
                plan.context.init_path == initializer
                and plan.ownership == "authored"
                and plan.disposition == "retained"
                for plan in report.publications
            ),
            eq=True,
        )
        workspace = u.Tests.standalone_workspace(root, root.name)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        tm.ok(infra.codegen_conform(request, workspace))

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
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)
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
            FlextInfraCodegenConform(
                repository_root=root,
                initial_workspace=workspace,
                request=request,
            ).plan(request),
        )

        tm.that(tuple(file.path for file in plan.files), eq=(destination,))
        tm.that(plan.uv_environments, eq=())
        file = plan.files[0]
        source = tm.not_none(file.desired_content).decode(c.DEFAULT_ENCODING)
        tm.that(source, has="PayloadOwner")
        tm.that(source, has="class Sample(ExistingOwner, PayloadOwner)")
        tm.that(source, has="retained = 'unchanged'")
        tm.that(
            {state.path for state in file.source_states},
            eq=set(before),
        )
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @staticmethod
    def _seed_conform_scope_repositories(
        tmp_path: Path,
        scope: c.Infra.CodegenConformScope,
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
            # Conform's fresh-import stage runs in the checkout's own runtime,
            # which a real checkout gets from make setup.
            u.Tests.provision_checkout(repository)
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
    def test_lazy_publication_owns_exact_conform_repositories(
        tmp_path: Path,
        scope: c.Infra.CodegenConformScope,
    ) -> None:
        """Root and nested Git repositories retain their selected publication scope."""
        seed = TestsFlextInfraCodegenLazyInitFilePlans._seed_conform_scope_repositories
        root, member, packages = seed(tmp_path, scope)
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = u.Tests.conform_request(
            root,
            scope=scope,
            mode=c.Infra.CodegenConformMode.CHECK,
        ).model_copy(update={"what": c.Infra.CodegenConformSurface.LAZY_INIT})
        plan = tm.ok(
            FlextInfraCodegenConform(
                repository_root=root,
                request=request,
                initial_workspace=workspace,
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
        before = {
            package / c.Infra.INIT_PY: (package / c.Infra.INIT_PY).read_bytes()
            for package in packages
        }
        tm.that(
            {file.project for file in plan.files},
            eq=expected,
        )
        tm.that({path: path.read_bytes() for path in before}, eq=before)
        applied = request.model_copy(update={"mode": c.Infra.CodegenConformMode.APPLY})
        tm.ok(infra.codegen_conform(applied, workspace))
        for repository, package in zip((root, member), packages, strict=True):
            initializer = package / c.Infra.INIT_PY
            tm.that(
                initializer.read_bytes() != before[initializer],
                eq=repository.resolve() in expected,
            )
        tm.ok(infra.codegen_conform(request, workspace))

    @staticmethod
    def test_scope_outside_workspace_is_a_causal_plan_failure(
        tmp_path: Path,
    ) -> None:
        """A selected repository outside the workspace fails instead of widening."""
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

        tm.that(result.failure, eq=True)
        tm.that(result.error, contains="lazy-init repository scope is missing")
        tm.that(init_path.read_bytes(), eq=before)

    @staticmethod
    def test_plan_files_binds_init_and_sidecar_effects_without_writing(
        tmp_path: Path,
    ) -> None:
        """Return exact target/source states while preserving every target byte."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextTestsModels",
            alias="m",
        )
        init_path = package_root / c.Infra.INIT_PY
        unit_path = package_root / "__unit__.py"
        unit_path.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = {path: path.read_bytes() for path in (init_path, unit_path)}
        service = u.Tests.create_lazy_init_service(repository_root)

        result = service.plan_files()

        tm.that(result.success, eq=True)
        analysis = result.value
        tm.that(analysis.phase, eq="lazy-init")
        plans = {plan.path: plan for plan in analysis.files}
        init_plan = plans[init_path.resolve()]
        tm.that(init_plan.project, eq=repository_root.resolve())
        tm.that(
            tm.ok(u.Infra.codegen_file_before_state(init_plan)).content,
            eq=before[init_path],
        )
        tm.that(init_plan.desired_mode, eq=0o644)
        tm.that(u.Tests.codegen_file_text(init_plan), contains="FlextTestsModels")
        tm.that(u.Infra.codegen_file_requires_effect(init_plan), eq=True)
        source_paths = {state.path for state in init_plan.source_states}
        tm.that(module_path.resolve() in source_paths, eq=True)
        tm.that(
            any(path.name == "lazy_init_root.py.j2" for path in source_paths),
            eq=True,
        )
        input_paths = {state.path for state in analysis.inputs}
        tm.that(source_paths.issubset(input_paths), eq=True)
        tm.that(init_path.resolve() in input_paths, eq=True)
        unit_plan = plans[unit_path.resolve()]
        tm.that(
            tm.ok(u.Infra.codegen_file_before_state(unit_plan)).content,
            eq=before[unit_path],
        )
        tm.that(unit_plan.desired_content, eq=None)
        tm.that(unit_plan.desired_mode, eq=None)
        tm.that(u.Infra.codegen_file_requires_effect(unit_plan), eq=True)
        tm.that({path: path.read_bytes() for path in (init_path, unit_path)}, eq=before)

    @staticmethod
    def test_plan_files_includes_all_retired_generated_sidecars(
        tmp_path: Path,
    ) -> None:
        """Describe the closed sidecar cleanup set, including one-pass constants."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        generated_header = f"{c.Infra.AUTOGEN_HEADER}\n"
        stub_path = package_root / c.Infra.INIT_PYI
        stub_path.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        root_sidecar = package_root / "_exports.py"
        root_sidecar.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        constants_dir = package_root / c.Infra.ROOT_EXPORTS_DIR
        constants_dir.mkdir()
        constants_init = constants_dir / c.Infra.INIT_PY
        constants_init.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        constants_sidecar = constants_dir / "_exports_lazy.py"
        constants_sidecar.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        obsolete_dir = package_root / "_root_exports"
        obsolete_dir.mkdir()
        obsolete_init = obsolete_dir / c.Infra.INIT_PY
        obsolete_init.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        obsolete_part = obsolete_dir / "part.py"
        obsolete_part.write_text(generated_header, encoding=c.DEFAULT_ENCODING)
        expected_deletes = {
            stub_path.resolve(),
            root_sidecar.resolve(),
            constants_init.resolve(),
            constants_sidecar.resolve(),
            obsolete_init.resolve(),
            obsolete_part.resolve(),
        }
        before = {path: path.read_bytes() for path in expected_deletes}

        result = u.Tests.create_lazy_init_service(repository_root).plan_files()

        tm.that(result.success, eq=True)
        deletes = {
            plan.path
            for plan in result.value.files
            if plan.desired_content is None
            and u.Infra.codegen_file_requires_effect(plan)
        }
        tm.that(expected_deletes.issubset(deletes), eq=True)
        tm.that({path: path.read_bytes() for path in expected_deletes}, eq=before)

    @staticmethod
    def test_execute_rejects_apply_and_preserves_planned_targets(
        tmp_path: Path,
    ) -> None:
        """The standalone command is a check surface, never a second writer."""
        _, init_path, service = u.Tests.lazy_init_scenario(tmp_path)
        before = init_path.read_bytes()
        service.apply_changes = True

        result = service.execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error, contains="owned by codegen conform")
        tm.that(init_path.read_bytes(), eq=before)

    @staticmethod
    def test_unknown_target_is_a_causal_plan_failure(tmp_path: Path) -> None:
        """A missing target fails instead of widening to the workspace."""
        _, init_path, service = u.Tests.lazy_init_scenario(tmp_path)
        before = init_path.read_bytes()
        service.target_module = "flext_missing"

        result = service.plan_files()

        tm.that(result.failure, eq=True)
        tm.that(result.error, contains="lazy-init target module not found")
        tm.that(init_path.read_bytes(), eq=before)
