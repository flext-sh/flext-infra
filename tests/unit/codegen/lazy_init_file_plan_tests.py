"""Read-only publication plans for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from re import escape

import pytest

from flext_infra import config, infra
from flext_infra.codegen import (
    FlextInfraCodegenConformExecute,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraStagedPackage,
    codegen_transaction as transaction,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, tm, u


class TestsLazyInitScopedSourceElection:
    """Keep native catalog observation distinct from semantic source consumption."""

    @staticmethod
    @pytest.mark.parametrize("consumed", [False, True])
    def test_nested_target_authenticates_only_consumed_sibling_sources(
        tmp_path: Path, *, consumed: bool
    ) -> None:
        """Select one artifact without planning its unrelated production sibling."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_dir = package / "services"
        provider_dir.mkdir()
        (provider_dir / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        provider = provider_dir / "provider.py"
        provider.write_text(
            "class Provider: pass\n__all__ = ['Provider']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        fixtures = root / c.Infra.DIR_TESTS / "fixtures"
        fixtures.mkdir(parents=True)
        (fixtures.parent / c.Infra.INIT_PY).write_text(
            "__all__ = []\n", encoding=c.DEFAULT_ENCODING
        )
        target = fixtures / c.Infra.INIT_PY
        target.write_text("", encoding=c.DEFAULT_ENCODING)
        (fixtures / "reader.py").write_text(
            (
                f"from {package.name}.services.provider import Provider\n"
                "class Reader(Provider): pass\n"
                if consumed
                else "class Reader: pass\n"
            )
            + "__all__ = ['Reader']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        publications: list[tuple[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with u.Infra.facade_source_project(
            root, project_roots=(root,), source_publications=(publications, failures)
        ) as (project, _, _):
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(
                    repository_root=root,
                    module=f"{c.Infra.DIR_TESTS}.fixtures",
                ).plan_files(source_project=project, source_publications=publications)
            )
            tm.that(tuple(file.path for file in analysis.files), eq=(target,))
            tm.that(provider in {state.path for state in analysis.inputs}, eq=consumed)
            receipt = next(
                receipt for path, receipt in publications if path == fixtures
            )
            provider.write_text(
                "class Provider: VALUE = 'changed'\n__all__ = ['Provider']\n",
                encoding=c.DEFAULT_ENCODING,
            )
            if consumed:
                with pytest.raises(ValueError, match=escape(str(provider))):
                    project.verify_source_states(receipt)
            else:
                project.verify_source_states(receipt)
        tm.that(len(failures), eq=int(consumed))

    @staticmethod
    def _observe(
        observer: p.Infra.RopeResourceObserver, resource: p.Infra.RopeResource
    ) -> None:
        """Register the real native observer through its consumed typed contract."""
        observer.add_resource(resource)

    @staticmethod
    @pytest.mark.parametrize(
        "change", ["unrelated", "producer", "provider", "collision"]
    )
    def test_admission_retains_namespace_queries_not_unrelated_manifest_payloads(
        tmp_path: Path, change: str
    ) -> None:
        """Member metadata is a namespace query unless a checker consumes its bytes."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "scoped_receiver",
            pyproject="[project]\nname = 'scoped-receiver'\nversion = '1.0.0'\n",
        )
        member = root / "unrelated"
        u.Tests.src_package(
            member,
            "unrelated_provider",
            pyproject="[project]\nname = 'unrelated-provider'\nversion = '1.0.0'\n",
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "unrelated"]\n\tpath = unrelated\n',
            encoding=c.DEFAULT_ENCODING,
        )
        source = package / c.Infra.INIT_PY
        original = (
            "from unrelated_provider import VALUE\n"
            if change == "provider"
            else "VALUE = 1\n"
        )
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(root, {source: original + "\n"})
        )
        if change == "provider":
            tm.that(
                any(layout.project_root == member for layout in plan.layouts), eq=True
            )
        metadata = (root if change == "producer" else member) / c.PYPROJECT_FILENAME
        before = metadata.read_text(encoding=c.DEFAULT_ENCODING)
        metadata.write_text(
            before
            + (
                '[tool.hatch.build.targets.wheel]\npackages = ["src/scoped_receiver"]\n'
                if change == "collision"
                else (
                    "[tool.hatch.build.targets.wheel]\n"
                    'packages = ["src/changed_provider"]\n'
                )
                if change == "provider"
                else "description = 'unrelated metadata edit'\n"
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        result = FlextInfraStagedPackage.source_inputs_current(plan)
        if change == "unrelated":
            tm.fail(metadata in {state.path for state in plan.inputs})
            tm.ok(result)
        else:
            tm.fail(result)
            tm.that(
                result.error,
                has=(
                    "ambiguous candidate package"
                    if change == "collision"
                    else "provider namespace election changed"
                    if change == "provider"
                    else str(metadata)
                ),
            )
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    def test_original_target_error_is_not_replaced_by_unrelated_epoch_reads(
        tmp_path: Path,
    ) -> None:
        """A prior independent query cannot replace this target's original error."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        unrelated = root / c.Infra.DIR_TESTS / "unrelated.py"
        unrelated.parent.mkdir()
        unrelated.write_text("VALUE = 'original'\n", encoding=c.DEFAULT_ENCODING)
        publications: list[tuple[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with u.Infra.facade_source_project(
            root, project_roots=(root,), source_publications=(publications, failures)
        ) as (project, _, _):
            project.source_text(unrelated)
            unrelated.write_text("VALUE = 'changed'\n", encoding=c.DEFAULT_ENCODING)
            result = FlextInfraCodegenLazyInit(
                repository_root=root, module=f"{package.name}.absent"
            ).plan_files(source_project=project, source_publications=publications)
            tm.fail(result)
            tm.that(result.error, has="target module not found")
        tm.that(failures, eq=[])

    @staticmethod
    @pytest.mark.parametrize("location", ["tests", "module"])
    def test_observed_catalog_payload_is_not_a_semantic_dependency(
        tmp_path: Path, location: str
    ) -> None:
        """An observed but unread module can change without invalidating an artifact."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / c.Infra.DIR_TESTS if location == "tests" else package
        directory.mkdir(exist_ok=True)
        source = directory / "unrelated.py"
        source.write_text("VALUE = 'original'\n", encoding=c.DEFAULT_ENCODING)
        publications: list[tuple[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with u.Infra.facade_source_project(
            root, project_roots=(root,), source_publications=(publications, failures)
        ) as (project, _, _):
            with project.source_consumption() as consumption:
                resource = project.get_file(source.relative_to(root).as_posix())
                TestsLazyInitScopedSourceElection._observe(
                    project.get_pycore().observer, resource
                )
            receipt = consumption.receipt()
            publications.append((package, receipt))
            tm.fail(source in {state.path for state in receipt.inputs})
            tm.that(bool(receipt.source_directories), eq=True)
            source.write_text("VALUE = 'changed'\n", encoding=c.DEFAULT_ENCODING)
            project.verify_source_states(receipt)
        tm.that(failures, eq=[])

    @staticmethod
    def test_scoped_semantic_read_retains_original_caller_evidence(
        tmp_path: Path,
    ) -> None:
        """Real source reads remain authenticated even after observer registration."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "producer.py"
        source.write_text("VALUE = 'original'\n", encoding=c.DEFAULT_ENCODING)
        publications: list[tuple[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with u.Infra.facade_source_project(
            root, project_roots=(root,), source_publications=(publications, failures)
        ) as (project, _, _):
            with project.source_consumption() as consumption:
                resource = project.get_file(source.relative_to(root).as_posix())
                TestsLazyInitScopedSourceElection._observe(
                    project.get_pycore().observer, resource
                )
                tm.that(project.source_text(source), has="original")
            receipt = consumption.receipt()
            publications.append((package, receipt))
            tm.that(source in {state.path for state in receipt.inputs}, eq=True)
            source.write_text("VALUE = 'changed'\n", encoding=c.DEFAULT_ENCODING)
            with pytest.raises(ValueError, match=escape(str(source))):
                project.verify_source_states(receipt)
        tm.that(len(failures), eq=1)
        tm.that(str(failures[0].exception), has=str(source))
        tm.not_none(tm.not_none(failures[0].exception).__traceback__)


class TestsFlextInfraCodegenLazyInitFilePlans:
    """Prove lazy-init describes effects without owning publication."""

    @staticmethod
    @pytest.mark.parametrize("injected", [False, True])
    def test_unconsumed_authored_test_module_does_not_enter_publication_inputs(
        tmp_path: Path,
        *,
        injected: bool,
    ) -> None:
        """Capturing an unused module must not turn it into a shared read dependency."""
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
        phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots(phase.value, (root,))
        retained: list[m.Infra.CodegenPhaseAnalysis] = []

        def publish(scope_root: Path) -> p.Result[tuple[Path, ...]]:
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
                tm.fail(conftest in {state.path for state in analysis.inputs})
                tm.that(
                    any(
                        conftest == state.path
                        for file in analysis.files
                        for state in file.source_states
                    ),
                    eq=False,
                )
                conftest.write_text(
                    "# Unconsumed source edit\n__all__ = []\n",
                    encoding=c.DEFAULT_ENCODING,
                )
            retained.append(analysis)
            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            )

        tm.ok(owner.run_files_locked(roots, publish))
        production = next(
            file for file in retained[0].files if file.path == package / c.Infra.INIT_PY
        )
        tm.that(production.path.read_bytes(), eq=production.desired_content)

    @staticmethod
    def test_cached_native_absence_queries_keep_original_scoped_witness(
        tmp_path: Path,
    ) -> None:
        """A warmed negative predicate must retain its original proof in each scope."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        absent = package / "missing.py"
        unrelated = package / "unrelated.py"
        with ExitStack() as contexts:
            binding = contexts.enter_context(
                u.Infra.facade_source_project(root, project_roots=(root,)),
            )
            with binding[0].source_capture():
                tm.fail(binding[0].source_query(absent, "isfile"))
            with binding[0].source_consumption() as first:
                tm.fail(binding[0].source_query(absent, "isfile"))
            with binding[0].source_consumption() as second:
                tm.fail(binding[0].source_query(unrelated, "isfile"))
                tm.fail(binding[0].source_query(absent, "isfile"))
            tm.that(
                {
                    query
                    for inventory in first.receipt().source_directories
                    if inventory.root.path == package
                    for query in inventory.queries
                },
                eq={(absent.name, "isfile")},
            )
            tm.that(
                {
                    query
                    for inventory in second.receipt().source_directories
                    if inventory.root.path == package
                    for query in inventory.queries
                },
                eq={(absent.name, "isfile"), (unrelated.name, "isfile")},
            )
            with binding[0].source_consumption():
                binding[0].replay_source_consumption(first.receipt())
                binding[0].replay_source_consumption(second.receipt())
            tm.that(
                any(
                    inventory.root.path == package
                    and (absent.name, "isfile") in inventory.queries
                    for inventory in binding[0].consumed_source_directories()
                ),
                eq=True,
            )
            absent.write_text("VALUE = 'born'\n", encoding=c.DEFAULT_ENCODING)
            with pytest.raises(ValueError, match=escape(str(absent))):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize(
        "change", ["direct", "transitive", "negative", "absent", "metadata"]
    )
    def test_consumed_original_sources_reject_publication(
        tmp_path: Path, change: str
    ) -> None:
        """Refuse changed direct, transitive, negative, absent and metadata inputs."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="upstream-provider",
            package_name="upstream_provider",
        )
        provider = provider_package / "provider.py"
        provider.write_text(
            "class ProviderConstants: VALUE = 'original'\n"
            "c = ProviderConstants\n__all__ = ['ProviderConstants', 'c']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = package / "service.py"
        source.write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        if change == "transitive":
            (provider_package / c.Infra.INIT_PY).write_text(
                "from .provider import c\n__all__ = ['c']\n",
                encoding=c.DEFAULT_ENCODING,
            )
            (package / c.Infra.CONSTANTS_PY).write_text(
                "from upstream_provider import c as upstream_c\n"
                f"class {u.derive_class_stem(package.name.replace('_', '-'))}"
                "Constants(upstream_c): pass\n"
                f"c = {u.derive_class_stem(package.name.replace('_', '-'))}Constants\n"
                "__all__ = ['c']\n",
                encoding=c.DEFAULT_ENCODING,
            )
            tm.that(
                u.Tests.run_lazy_init_probe(
                    f"from {package.name}.constants import c\n"
                    "from upstream_provider import c as upstream_c\n"
                    "print(c.__mro__[1] is upstream_c)\n",
                    python_paths=(str(package.parent), str(provider_package.parent)),
                    cwd=root,
                ),
                eq=["True"],
            )
        negative = package / "hidden.py"
        negative.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        absent = package / f"{c.Infra.DUNDER_VERSION}{c.Infra.EXT_PYTHON}"
        target = package / c.Infra.INIT_PY
        before = target.read_bytes()
        phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots(phase.value, (root,))

        def publish(scope_root: Path) -> p.Result[tuple[Path, ...]]:
            inputs = tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path))
                for path in (
                    source,
                    negative,
                    target,
                    root / c.PYPROJECT_FILENAME,
                    provider,
                    provider_package / c.Infra.INIT_PY,
                    provider_root / c.PYPROJECT_FILENAME,
                )
            )
            with u.Infra.facade_source_project(
                tmp_path,
                source_options=m.Infra.StageSourceOptions(inputs=inputs),
                project_roots=(root, provider_root),
            ) as binding:
                analysis = tm.ok(
                    u.Tests.create_lazy_init_service(root).plan_files(
                        source_project=binding[0]
                    )
                )
            planned = next(file for file in analysis.files if file.path == target)
            changed = {
                "direct": source,
                "transitive": provider,
                "negative": negative,
                "absent": absent,
                "metadata": root / c.PYPROJECT_FILENAME,
            }[change]
            if change == "absent":
                tm.that(
                    any(
                        inventory.root.path == package
                        and (absent.name, "isfile") in inventory.queries
                        for inventory in planned.source_directories
                    ),
                    eq=True,
                )
                absent.write_text(
                    f"{c.Infra.DUNDER_VERSION} = 'changed'\n",
                    encoding=c.DEFAULT_ENCODING,
                )
            else:
                original = next(
                    state for state in planned.source_states if state.path == changed
                )
                changed.write_bytes(
                    tm.not_none(original.content) + b"\n# Changed original input\n"
                )
            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                m.Infra.CodegenPhaseAnalysis(
                    phase=phase,
                    files=(planned,),
                    inputs=planned.source_states,
                    source_directories=planned.source_directories,
                    source_query_topology=planned.source_query_topology,
                ),
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            )

        outcome = owner.run_files_locked(roots, publish)
        tm.ok(outcome.failure)
        tm.that(target.read_bytes(), eq=before)

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
        tm.fail(initializer in {file.path for file in analysis.files})
        tm.that(
            (root / c.Infra.CODEGEN_LAZY_PLAN_REPORT_RELATIVE_PATH).exists(),
            eq=False,
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        tm.ok(infra.codegen_conform(request))

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
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.FACADES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
            module=f"{package.name}.{destination.stem}",
        )

        plan = tm.ok(
            FlextInfraCodegenConformExecute(
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
        declared_inputs = {state.path for state in inputs.sources}
        tm.that(
            {
                state.path
                for state in file.source_states
                if state.path.is_relative_to(root) or state.path in declared_inputs
            },
            eq=set(before) | declared_inputs,
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(file.source_states))
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
            FlextInfraCodegenConformExecute(
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
        request = u.Tests.conform_request(
            root,
            scope=scope,
            mode=c.Infra.CodegenConformMode.APPLY,
        ).model_copy(update={"what": c.Infra.CodegenConformSurface.LAZY_INIT})
        before = {
            package / c.Infra.INIT_PY: (package / c.Infra.INIT_PY).read_bytes()
            for package in packages
        }
        published = tm.ok(infra.codegen_conform(request))
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
            infra.codegen_conform(
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
            )
        )

    @staticmethod
    def test_scope_outside_workspace_is_a_scoped_plan_issue(
        tmp_path: Path,
    ) -> None:
        """An invalid target is attributed without widening publication authority."""
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

        analysis = tm.ok(result)
        tm.that(analysis.files, eq=())
        tm.that(tuple(issue.file for issue in analysis.issues), eq=(str(foreign_root),))
        tm.that(
            analysis.issues[0].message,
            contains="lazy-init repository scope is missing",
        )
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
        tm.that(analysis.issues, eq=())
        tm.that(analysis.exception, eq=None)
        for index, name in enumerate(("FirstPublished", "SecondPublished")):
            plan = next(
                file
                for file in analysis.files
                if file.path == packages[index] / c.Infra.INIT_PY
            )
            tm.that(plan.project, eq=roots[index])
            tm.that(u.Tests.codegen_file_text(plan), contains=name)
            source_paths = {state.path for state in plan.source_states}
            tm.ok(packages[index] / "service.py" in source_paths)
            tm.fail(packages[1 - index] / "service.py" in source_paths)
        repeated = tm.ok(service.plan_files())
        tm.that(
            tuple((file.path, file.desired_content) for file in analysis.files),
            eq=tuple((file.path, file.desired_content) for file in repeated.files),
        )
        service.module = "shared_package"
        repeated = tm.ok(service.plan_files())
        tm.that(repeated.files, eq=())
        tm.that(repeated.publications, eq=())
        tm.that(
            all(
                "target module is ambiguous" in issue.message
                for issue in repeated.issues
            ),
            eq=True,
        )

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
        analysis = tm.ok(
            FlextInfraCodegenLazyInit(
                repository_root=tmp_path,
                project_scope_roots=tuple(reversed(roots)),
                module="shared_package",
            ).plan_files(),
        )
        tm.that(analysis.files, eq=())
        tm.that(analysis.publications, eq=())
        tm.that(
            {
                issue.file
                for issue in analysis.issues
                if "target module is ambiguous" in issue.message
            },
            eq={str(root) for root in roots},
        )
        tm.that(
            any("collision(s)" in issue.message for issue in analysis.issues),
            eq=True,
        )
        tm.that({target for target, _ in analysis.failed_targets}, eq=set(roots))

    @staticmethod
    def test_failed_target_source_change_fails_the_whole_epoch(
        tmp_path: Path,
    ) -> None:
        """Failed-target evidence stays separate; its source change fails loud."""
        failed_root, failed_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="a-failed",
            package_name="failed_package",
        )
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="z-healthy",
            package_name="healthy_package",
        )
        for provider in (failed_package / "first.py", failed_package / "second.py"):
            provider.write_text(
                "class Shared: pass\n__all__ = ['Shared']\n",
                encoding=c.DEFAULT_ENCODING,
            )
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with ExitStack() as contexts:
            binding = contexts.enter_context(
                u.Infra.facade_source_project(
                    tmp_path,
                    project_roots=(failed_root, root),
                ),
            )
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(
                    repository_root=tmp_path,
                    project_scope_roots=(root, failed_root),
                ).plan_files(source_project=binding[0]),
            )
            receipt = analysis.failed_targets[0][1]
            tm.that(receipt, is_=m.Infra.CodegenPhaseAnalysis)
            with binding[0].source_consumption():
                binding[0].replay_source_consumption(receipt)
            plan = next(
                file
                for file in analysis.files
                if file.path == package / c.Infra.INIT_PY
            )
            tm.ok(provider in {state.path for state in receipt.inputs})
            tm.fail(provider in {state.path for state in plan.source_states})
            provider.write_text(
                "class Shared: pass\n__all__ = ['Shared']\n# Changed failed target\n",
                encoding=c.DEFAULT_ENCODING,
            )
            with pytest.raises(ValueError, match=escape(str(provider))):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize("invalid", ["missing", "outside", "ambiguous"])
    def test_multi_root_issue_retains_independent_guarded_publication(
        tmp_path: Path,
        invalid: str,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Keep healthy effects and aggregate evidence despite invalid targets."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path / "workspace")
        u.Tests.initialize_git_repo(root.parent)
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=u.Tests.python_dependency_projects(root),
                session_runtime=session_runtime,
            )
        )
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        invalid_root = root.parent / invalid
        if invalid == "outside":
            invalid_root = tmp_path / invalid
            invalid_root.mkdir()
        elif invalid == "ambiguous":
            invalid_root, invalid_package = u.Tests.create_lazy_init_workspace(
                root.parent,
                project_name=invalid,
            )
            for module in ("first", "second"):
                (invalid_package / f"{module}.py").write_text(
                    "class Shared: pass\n__all__ = ['Shared']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root.parent),
        )
        roots = owner.capability_roots(
            c.Infra.CodegenStagedFilePhase.LAZY_INIT.value,
            (root,),
        )
        analyses: list[m.Infra.CodegenPhaseAnalysis] = []

        def publish(scope_root: Path) -> p.Result[tuple[Path, ...]]:
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(
                    repository_root=root.parent,
                    project_scope_roots=(invalid_root, root),
                ).plan_files()
            )
            analyses.append(analysis)
            tm.that(
                tuple(issue.file for issue in analysis.issues), eq=(str(invalid_root),)
            )
            tm.that({file.project for file in analysis.files}, eq={root})
            tm.that(
                (root.parent / c.Infra.CODEGEN_LAZY_PLAN_REPORT_RELATIVE_PATH).exists(),
                eq=False,
            )
            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            )

        outcome = owner.run_files_locked(roots, publish)
        tm.ok(outcome.failure)
        plan = next(
            file for file in analyses[0].files if file.path == package / c.Infra.INIT_PY
        )
        tm.that(plan.path.read_bytes(), eq=plan.desired_content, msg=outcome.error)

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
        for path in (init_path, unit_path):
            path.write_text(
                f"{c.Infra.AUTOGEN_HEADER}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        before = {path: path.read_bytes() for path in (init_path, unit_path)}
        service = u.Tests.create_lazy_init_service(repository_root)

        result = service.plan_files()

        tm.that(result.success, eq=True, msg=result.error)
        analysis = result.value
        tm.that(analysis.phase, eq="lazy-init")
        plans = {plan.path: plan for plan in analysis.files}
        init_plan = plans[init_path.resolve()]
        tm.that(init_plan.project, eq=repository_root.resolve())
        tm.that(
            tm.ok(u.Infra.codegen_file_before_state(init_plan)).content,
            eq=before[init_path],
        )
        tm.that(init_plan.desired_mode, eq=config.Infra.codegen.modes.file_default)
        tm.that(u.Tests.codegen_file_text(init_plan), contains="FlextTestsModels")
        tm.ok(u.Infra.codegen_file_requires_effect(init_plan))
        source_paths = {state.path for state in init_plan.source_states}
        tm.ok(module_path.resolve() in source_paths)
        tm.that(
            any(path.name == "lazy_init_root.py.j2" for path in source_paths),
            eq=True,
        )
        input_paths = {state.path for state in analysis.inputs}
        tm.ok(source_paths.issubset(input_paths))
        tm.ok(init_path.resolve() in input_paths)
        unit_plan = plans[unit_path.resolve()]
        tm.that(
            tm.ok(u.Infra.codegen_file_before_state(unit_plan)).content,
            eq=before[unit_path],
        )
        tm.that(unit_plan.desired_content, eq=None)
        tm.that(unit_plan.desired_mode, eq=None)
        tm.ok(u.Infra.codegen_file_requires_effect(unit_plan))
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
        (package_root / c.Infra.INIT_PY).write_text(
            generated_header, encoding=c.DEFAULT_ENCODING
        )
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

        tm.that(result.success, eq=True, msg=result.error)
        deletes = {
            plan.path
            for plan in result.value.files
            if plan.desired_content is None
            and u.Infra.codegen_file_requires_effect(plan)
        }
        tm.ok(expected_deletes.issubset(deletes))
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
