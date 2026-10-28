"""Generation preserves authored runtime outside declared family composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack, nullcontext
from pathlib import Path

import pytest

from flext_infra import codegen, config, workspace
from tests import c, m, p, tm, u


class TestsFlextInfraFacadeAuthoredRuntime:
    """Exercise preservation through generation and a fresh public consumer."""

    @staticmethod
    def test_declared_plans_overlay_the_live_tree_without_effects(
        tmp_path: Path,
    ) -> None:
        """Planned retirements and rewrites are visible only inside the view."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        binary = package / "opaque.bin"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        binary.write_bytes(b"\x00\xff")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        opaque = tm.ok(u.Cli.atomic_read_binary_file_state(binary))
        plans = (
            m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=original,
                desired_content=None,
                desired_mode=None,
            ),
            m.Infra.CodegenFilePlan(
                project=root,
                path=binary,
                before=opaque,
                desired_content=b"\xff\x00",
                desired_mode=opaque.mode,
            ),
        )
        with u.Infra.facade_source_project(root, declared_files=plans) as binding:
            project = binding[0]
            tm.fail(project.source_query(source, "isfile"))
            tm.fail(source in project.source_children(package))
            tm.that(project.source_bytes(binary), eq=b"\xff\x00")
            with pytest.raises(FileNotFoundError):
                project.source_bytes(source)
        tm.that(binary.read_bytes(), eq=opaque.content)
        tm.that(source.read_bytes(), eq=original.content)


class TestsFlextInfraGeneratedRuntime:
    """Execute generated candidates through their real public consumers."""

    @staticmethod
    @pytest.mark.parametrize("depth", [1, 2])
    @pytest.mark.parametrize(
        "segment", ["child", "descriptive_namespace_for_deep_native_owner_projection"]
    )
    def test_generated_imports_preserve_relative_alias_levels(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        depth: int,
        segment: str,
    ) -> None:
        """Execute elected own imports alongside ancestor and external imports.

        Premise: the public renderer expresses same-root targets relative to the
        rendered package and binds an own child whose import line cannot fit
        through a module alias; a namespace whose own import cannot fit at all
        is rejected before any initializer is written.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        children = (segment,) * depth
        child = package.joinpath(*children)
        child.mkdir(parents=True)
        namespace = ".".join((package.name, *children))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "sibling.py",
                "SENTINEL = 'native-sibling'\n",
            )
        )
        provider = child / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(provider, "LOCAL_SENTINEL = object()\n"))
        plan = m.Infra.LazyInitPlan(
            context=m.Infra.LazyInitPackageContext(
                pkg_dir=child,
                init_path=child / c.Infra.INIT_PY,
                current_pkg=namespace,
                surface=package.name,
                importable=True,
            ),
            action=c.Infra.LazyInitAction.WRITE,
            exports=("LOCAL_SENTINEL", "Path", "sibling"),
            lazy_map={
                "sibling": (f"{package.name}.sibling", ""),
                "Path": ("pathlib", "Path"),
                "LOCAL_SENTINEL": (f"{namespace}.{provider.stem}", "LOCAL_SENTINEL"),
            },
            eager_dunders={},
        )
        width: int = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            project = snapshot.engine
            model = u.Infra.lazy_init_run(
                project,
                u.Infra.index_rope_workspace(snapshot, root),
                root=root,
                scoped=True,
            ).model
            if len(f"    from {namespace} import (") > width:
                with pytest.raises(ValueError, match="exceeds Ruff line length"):
                    u.Infra.lazy_init_render(
                        plan, model=model, first_party=frozenset({package.name})
                    )
                tm.fail((child / c.Infra.INIT_PY).exists())
                return
            rendered = u.Infra.lazy_init_render(
                plan, model=model, first_party=frozenset({package.name})
            )
        tm.ok(u.Cli.atomic_write_text_file(child / c.Infra.INIT_PY, rendered))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pathlib\n"
            f"import {namespace}.{provider.stem} as provider\n"
            f"from {namespace} import LOCAL_SENTINEL, Path, sibling\n"
            "assert Path is pathlib.Path\n"
            "assert sibling.SENTINEL == 'native-sibling'\n"
            "assert LOCAL_SENTINEL is provider.LOCAL_SENTINEL\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("generated_name", config.Infra.codegen.generated_sources)
    def test_generated_barrel_does_not_elect_an_authored_facade(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        generated_name: str,
    ) -> None:
        """Ignored generated providers remain importable without owning facades."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        generated = package / generated_name
        generated.mkdir()
        provider = generated / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                "class GeneratedProvider:\n"
                "    marker = 'native-provider'\n"
                "__all__ = ['GeneratedProvider']\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".gitignore",
                f"/{generated.relative_to(root).as_posix()}/\n",
            )
        )
        service = u.Tests.create_lazy_init_service(root)
        analysis = tm.ok(service.plan_files())
        with u.Infra.facade_source_project(
            root,
            declared_files=analysis,
        ) as binding:
            project, sources = binding
            tm.fail(any(path.is_relative_to(generated) for path in sources))
            planned = {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                for file in analysis
                if file.path.suffix == c.Infra.EXT_PYTHON
                and file.desired_content is not None
            }
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    {**sources, **planned},
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
            tm.that(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                ),
                eq=None,
            )
            module = u.Infra.require_semantic_module(
                project.get_module(f"{package.name}.{generated.name}.{provider.stem}")
            )
            tm.not_none(module.get_attribute("GeneratedProvider").get_object())
        tm.ok(u.Tests.materialize_lazy_init(service))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"provider = importlib.import_module("
            f"{f'{package.name}.{generated.name}.{provider.stem}'!r})\n"
            "assert provider.GeneratedProvider.marker == 'native-provider'\n",
            cwd=root,
        )

    @staticmethod
    def test_shared_source_project_keeps_native_stdlib_election(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """The authenticated graph resolves the interpreter's virtual stdlib."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                "from collections.abc import Mapping\n"
                "class Consumer(Mapping):\n"
                '    """Native stdlib inheritance contract."""\n'
                "__all__ = ['Consumer']\n",
            )
        )
        with u.Infra.facade_source_project(root) as binding:
            project, sources = binding
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    sources,
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from collections.abc import Mapping\n"
            f"from {package.name} import Consumer\n"
            "assert issubclass(Consumer, Mapping)\n",
            cwd=root,
        )

    @staticmethod
    def test_declared_projection_preserves_authored_bindings(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Unrelated authored bindings keep working after the family is published."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "owner.py": (
                "class Owner:\n    marker = 'owner'\n__all__ = ['Owner']\n"
            ),
            package / family.directory / "support.py": (
                "class AuthoredSupport:\n"
                "    @staticmethod\n"
                "    def render(value):\n"
                "        return value.upper()\n"
                "__all__ = []\n"
            ),
            facade: (
                f"from {package.name}.{family.directory}.owner import Owner\n"
                f"from {package.name}.{family.directory}.support "
                "import AuthoredSupport\n"
                "def authored_value(value):\n"
                "    return AuthoredSupport.render(value)\n"
                "class Utilities(Owner):\n"
                "    @classmethod\n"
                "    def read(cls, value):\n"
                "        return authored_value(value) + ':' + cls.marker\n"
                "u = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            "assert u.read('value') == 'VALUE:owner'\n"
            "class Receiver(u):\n"
            "    marker = 'receiver'\n"
            "assert Receiver.read('value') == 'VALUE:receiver'\n",
            cwd=root,
        )

    @staticmethod
    def test_checkout_environment_is_never_a_planning_source(tmp_path: Path) -> None:
        """Dependency modules read from the checkout environment stay inputs only.

        Premise (70dc29f1b9 regression): the lazy-init plans carry every state
        their native reads consumed, including dependency modules installed in
        the checkout-local environment. Those states entered the planned-source
        map, so the facade planner treated the installed dependency as a
        project package and republished its facade inside the environment
        (cosmos-charts lost an importable flext_cli this way).
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        installed = (
            root
            / c.Infra.ENVIRONMENT_DIRECTORY
            / "lib"
            / "site-packages"
            / "flext_dependency"
        )
        files = {
            package / c.Infra.INIT_PY: "",
            installed / c.Infra.INIT_PY: "",
            installed / c.Infra.UTILITIES_PY: "class Dependency:\n    pass\n",
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with u.Infra.facade_source_project(root) as (project, sources):
            project.get_pymodule(
                project.get_resource(
                    (installed / c.Infra.UTILITIES_PY).relative_to(root).as_posix()
                )
            )
            tm.that(
                {path.resolve() for path in sources},
                eq={(package / c.Infra.INIT_PY).resolve()},
            )

    @staticmethod
    def test_failed_planning_retains_only_a_completed_source_cohort(
        tmp_path: Path,
    ) -> None:
        """A tooling failure retains the completed source cohort, unpublished.

        Premise: projected import cycles are a declarative catalog finding
        (``ban-cyclic-import``), not a planning failure, so the first planning
        failure here is the invalid tooling configuration.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_standalone_workspace_manifest(root, root.name)
        model = u.Infra.facade_families()["m"]
        utility = u.Infra.facade_families()["u"]
        facade = package / f"{model.module}.py"
        barrel = package / model.directory / c.Infra.INIT_PY
        utility_facade = package / f"{utility.module}.py"
        sources = {
            barrel: (
                f"{c.Infra.AUTOGEN_HEADER}\nfrom .base import ProviderBase\n"
                "from .departed import DepartedOwner\n"
                "__all__ = ['ProviderBase', 'DepartedOwner']\n"
            ),
            barrel.parent / "base.py": (
                "class ProviderBase:\n    marker = 'provider'\n"
                "__all__ = ['ProviderBase']\n"
            ),
            barrel.parent / "departed.py": (
                "class DepartedOwner:\n    departed = 'retained'\n__all__ = []\n"
            ),
            facade: (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                f"from {package.name}.{model.directory} "
                "import ProviderBase, DepartedOwner\n"
                "class ProviderModels(ProviderBase, DepartedOwner):\n    pass\n"
                "m = ProviderModels\n__all__ = ['ProviderModels', 'm']\n"
            ),
            package / utility.directory / c.Infra.INIT_PY: "",
            package / utility.directory / "owner.py": (
                f"from {package.name} import m\n"
                "class ConsumerOwner(m):\n    pass\n__all__ = ['ConsumerOwner']\n"
            ),
            utility_facade: (
                "class ConsumerUtilities:\n    pass\n"
                "u = ConsumerUtilities\n__all__ = ['ConsumerUtilities', 'u']\n"
            ),
        }
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        tooling = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        tm.ok(u.Cli.yaml_dump(tooling, {"Infra": {"tooling": {"settings": []}}}))
        incoming = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.that(len(incoming), gt=0)
        tm.fail(facade in {file.path for file in incoming})
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (
                package / c.Infra.INIT_PY,
                *sources,
                tooling,
                root / c.PYPROJECT_FILENAME,
            )
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        spec = tm.ok(
            workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                root, inputs=inputs
            )
        )
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            outcome = codegen.FlextInfraCodegenConform.Generate.plan_repository_task(
                m.Infra.CodegenRepositoryPlanTask(
                    root=root,
                    workspace=spec,
                    current_target=tm.ok(
                        workspace.FlextInfraWorkspaceDetector.conform_target(
                            root, spec, inputs=inputs
                        )
                    ),
                    repository=spec.repository,
                    surface=c.Infra.CodegenConformSurface.ALL,
                    selected_inputs=inputs,
                    provider_plans=incoming,
                ),
                snapshot,
            )
        tm.that(outcome.failed, eq=True)
        tm.that(outcome.error, has="settings")
        tm.that(isinstance(outcome.exception, m.ValidationError), eq=True)
        projected = {file.path: file for file in outcome.files}
        tm.that(set(projected), has=facade)
        tm.that(set(projected), has=barrel)
        tm.that(set(projected), has=utility_facade)
        tm.that(set(projected), has=package / c.Infra.INIT_PY)
        tm.that(
            projected[facade].before,
            eq=next(state for state in originals if state.path == facade),
        )
        tm.fail(b"DepartedOwner" in tm.not_none(projected[facade].desired_content))
        with u.Infra.facade_source_project(
            root,
            declared_files=outcome.files,
        ) as binding:
            tm.that(
                tm.not_none(
                    u.Infra.render_utility_facade(
                        package, project=binding[0], sources=binding[1]
                    )
                ).encode(c.DEFAULT_ENCODING),
                eq=projected[utility_facade].desired_content,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_unpublished_provider_facet_precedes_native_consumer(
        native_consumer: p.Tests.NativeConsumer,
        installed_dependency_path: Path,
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """Bind a complete supplier candidate without publishing its original files."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider = u.Tests.create_lazy_init_workspace(
            installed_dependency_path,
            project_name="provider_project",
            package_name="provider_package",
        )
        families = u.Infra.facade_families()
        model_facade = provider / f"{families['m'].module}.py"
        model_barrel = provider / families["m"].directory / c.Infra.INIT_PY
        consumer_facade = package / f"{families['u'].module}.py"
        sources = {
            provider / c.Infra.INIT_PY: (
                f"from .{families['m'].module} import m\n__all__ = ['m']\n"
            ),
            model_barrel: (
                f"{c.Infra.AUTOGEN_HEADER}\nfrom .base import ProviderBase\n"
                "from .departed import DepartedOwner\n"
                "__all__ = ['ProviderBase', 'DepartedOwner']\n"
            ),
            model_barrel.parent / "base.py": (
                "class ProviderBase:\n"
                "    marker = 'provider'\n"
                "__all__ = ['ProviderBase']\n"
            ),
            model_barrel.parent / "departed.py": (
                "class DepartedOwner:\n    departed = 'retained'\n__all__ = []\n"
            ),
            model_facade: (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                f"from {provider.name}.{families['m'].directory} "
                "import ProviderBase, DepartedOwner\n"
                "class ProviderModels(ProviderBase, DepartedOwner):\n    pass\n"
                "m = ProviderModels\n__all__ = ['ProviderModels', 'm']\n"
            ),
            package / c.Infra.INIT_PY: "",
            package / families["u"].directory / c.Infra.INIT_PY: "",
            package / families["u"].directory / "owner.py": (
                f"from {provider.name} import m\n"
                f"class ConsumerOwner({'m' if declared else 'm.DepartedOwner'}):\n"
                "    pass\n"
                "__all__ = ['ConsumerOwner']\n"
            ),
            consumer_facade: (
                "class ConsumerUtilities:\n    pass\n"
                "u = ConsumerUtilities\n__all__ = ['ConsumerUtilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        by_path = {state.path: state for state in originals}
        plans = {
            file.path: file
            for file in tm.ok(
                u.Tests.create_lazy_init_service(provider_root).plan_files()
            )
        }
        with (
            tm.scope(python_paths=(str(provider.parent),)),
            nullcontext()
            if declared
            else pytest.raises(
                ValueError,
                match=(
                    r"^Missing inherited class member: "
                    r".*:ProviderModels:\d+\.DepartedOwner$"
                ),
            ),
        ):
            with u.Infra.facade_source_project(
                provider_root,
                declared_files=tuple(plans.values()),
            ) as binding:
                plans[model_facade] = m.Infra.CodegenFilePlan(
                    project=provider_root,
                    path=model_facade,
                    before=by_path[model_facade],
                    desired_content=tm.not_none(
                        u.Infra.render_utility_facade(
                            provider,
                            family="m",
                            project=binding[0],
                            sources=binding[1],
                        )
                    ).encode(c.DEFAULT_ENCODING),
                    desired_mode=tm.not_none(by_path[model_facade].mode),
                )
            with u.Infra.facade_source_project(
                root,
                declared_files=tuple(plans.values()),
            ) as binding:
                consumer = tm.not_none(
                    u.Infra.render_utility_facade(
                        package, project=binding[0], sources=binding[1]
                    )
                )
                plans[consumer_facade] = m.Infra.CodegenFilePlan(
                    project=root,
                    path=consumer_facade,
                    before=by_path[consumer_facade],
                    desired_content=consumer.encode(c.DEFAULT_ENCODING),
                    desired_mode=tm.not_none(by_path[consumer_facade].mode),
                )
            with u.Infra.facade_source_project(
                root,
                declared_files=tuple(plans.values()),
            ) as binding:
                plans.update(
                    (file.path, file)
                    for file in tm.ok(
                        u.Tests.create_lazy_init_service(root).plan_files(
                            source_project=binding[0]
                        )
                    )
                )
            with u.Infra.facade_source_project(
                root,
                declared_files=tuple(plans.values()),
            ) as binding:
                tm.that(
                    u.Infra.render_utility_facade(
                        package, project=binding[0], sources=binding[1]
                    ),
                    eq=consumer,
                )
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        if not declared:
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
            return
        candidate = tmp_path / "candidate"
        for state in originals:
            destination = candidate / state.path.relative_to(
                provider.parent
                if state.path.is_relative_to(provider)
                else package.parent
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(
                u.Cli.atomic_write_text_file(
                    destination,
                    tm.not_none(state.content).decode(c.DEFAULT_ENCODING),
                )
            )
        for file in plans.values():
            destination = candidate / file.path.relative_to(
                provider.parent
                if file.path.is_relative_to(provider)
                else package.parent
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(
                u.Cli.atomic_write_text_file(
                    destination,
                    tm.not_none(file.desired_content).decode(c.DEFAULT_ENCODING),
                )
            )
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(candidate)!r})\n"
            f"from {package.name}.{families['u'].module} import u\n"
            f"from {provider.name} import m\n"
            f"from {provider.name}.{families['m'].directory}.departed "
            "import DepartedOwner\n"
            "tm.that(u.marker, eq=m.marker)\n"
            "tm.fail(hasattr(m, 'departed'))\n"
            "tm.that(DepartedOwner.departed, eq='retained')\n",
            cwd=root,
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_planned_provider_export_precedes_native_consumer(
        native_consumer: p.Tests.NativeConsumer,
        installed_dependency_path: Path,
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """A stale live barrel never replaces the provider's planned export."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider = u.Tests.create_lazy_init_workspace(
            installed_dependency_path,
            project_name="provider_project",
            package_name="provider_package",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        barrel = provider / family.directory / c.Infra.INIT_PY
        barrel.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(barrel, ""))
        public_name = "ProviderBase" if declared else "OtherProviderBase"
        tm.ok(
            u.Cli.atomic_write_text_file(
                barrel.parent / "base.py",
                u.Tests.runtime_root_import() + f"class {public_name}(RuntimeRoot):\n"
                '    """Explicitly published empty protocol owner."""\n'
                f"__all__ = [{public_name!r}]\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                "class Consumer(ProviderBase):\n"
                '    """Consumer of the generated provider barrel."""\n'
                "__all__ = ['Consumer']\n",
            ),
        )
        provider_service = u.Tests.create_lazy_init_service(provider_root)
        provider_analysis = tm.ok(provider_service.plan_files())
        original_barrel = tm.ok(
            u.Cli.atomic_read_binary_file_state(barrel, required=True)
        )
        with ExitStack() as stack:
            stack.enter_context(tm.scope(python_paths=(str(provider.parent),)))
            if not declared:
                stack.enter_context(
                    pytest.raises(
                        u.Infra.rope_unresolved_error_types(),
                        match="Attribute ProviderBase not found",
                    )
                )
            project, sources = stack.enter_context(
                u.Infra.facade_source_project(
                    root,
                    declared_files=provider_analysis,
                )
            )
            roots = u.Infra.runtime_evaluated_base_classes(
                root,
                sources,
                u.Tests.runtime_evaluated_roots(),
                source_project=project,
            )
            tm.that(
                roots,
                has=f"{provider.name}.{family.directory}.ProviderBase",
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(barrel, required=True)),
            eq=original_barrel,
        )
        if declared:
            with tm.scope(python_paths=(str(provider.parent),)):
                tm.ok(u.Tests.materialize_lazy_init(provider_service))
                tm.ok(
                    u.Tests.materialize_lazy_init(
                        u.Tests.create_lazy_init_service(root)
                    )
                )
            native_consumer(
                f"sys.path.insert(0, {str(provider.parent)!r})\n"
                f"sys.path.insert(0, {str(package.parent)!r})\n"
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                f"from {package.name} import Consumer\n"
                "assert ProviderBase.__module__ == "
                f"{f'{provider.name}.{family.directory}.base'!r}\n"
                "assert issubclass(Consumer, ProviderBase)\n",
                cwd=root,
            )
