"""Generation preserves authored runtime outside declared family composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

import pytest

from flext_infra import c, config
from flext_infra.codegen import FlextInfraCodegenGeneration
from tests import p, tm, u


class TestsFlextInfraFacadeAuthoredRuntime:
    """Exercise preservation through generation and a fresh public consumer."""

    @staticmethod
    @pytest.mark.parametrize("depth", [1, 2])
    def test_generated_imports_preserve_relative_alias_levels(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        depth: int,
    ) -> None:
        """Execute generated ancestor aliases and absolute external imports."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        children = ("child",) * depth
        child = package.joinpath(*children)
        child.mkdir(parents=True)
        namespace = ".".join((package.name, *children))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "sibling.py",
                "SENTINEL = 'native-sibling'\n",
            )
        )
        imports = FlextInfraCodegenGeneration.generate_type_checking(
            {
                f"{package.name}.sibling": (("sibling", ""),),
                "pathlib": (("Path", "Path"),),
            },
            include_flext_types=False,
            local_package_root=namespace,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                child / c.Infra.INIT_PY,
                "TYPE_CHECKING = True\n\n" + "\n".join(imports) + "\n",
            )
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pathlib\n"
            f"from {namespace} import Path, sibling\n"
            "assert Path is pathlib.Path\n"
            "assert sibling.SENTINEL == 'native-sibling'\n",
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
            root, declared_files=analysis.files
        ) as binding:
            project, consumed, sources = binding
            tm.that(any(path.is_relative_to(generated) for path in sources), eq=False)
            planned = {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                for file in analysis.files
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
            tm.that({state.path for state in consumed()[0]}, has=provider.resolve())
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
            project, _, sources = binding
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
    @pytest.mark.parametrize("consumer_fails", [False, True])
    def test_source_epoch_failure_preserves_consumer_exception(
        tmp_path: Path,
        *,
        consumer_fails: bool,
    ) -> None:
        """Changed inputs reject success but never replace a consumer's exception."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(path, ""))
        failure = RuntimeError("consumer failed before source verification")

        def consume_changed_source() -> None:
            """Exercise one complete public source epoch."""
            with u.Infra.facade_source_project(root) as (project, _, _):
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                )
                tm.ok(u.Cli.atomic_write_text_file(path, "# Changed source epoch\n"))
                if consumer_fails:
                    raise failure

        with pytest.raises(
            RuntimeError if consumer_fails else ValueError,
            match=r"consumer failed|atomic source changed",
        ) as caught:
            consume_changed_source()
        tm.that(caught.value is failure, eq=consumer_fails)

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
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in files
        )
        with u.Infra.facade_source_project(root, source_states=states) as binding:
            project, consumed, sources = binding
            project.get_pymodule(
                project.get_resource(
                    (installed / c.Infra.UTILITIES_PY).relative_to(root).as_posix()
                )
            )
            tm.that(
                {path.resolve() for path in sources},
                eq={(package / c.Infra.INIT_PY).resolve()},
            )
            tm.that(
                {state.path.resolve() for state in consumed()[0]},
                has=(installed / c.Infra.UTILITIES_PY).resolve(),
            )

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
        provider_namespace = (
            f"{provider_root.name}.{c.Infra.DEFAULT_SRC_DIR}.{provider.name}"
        )
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
                f"from {provider_namespace}.{family.directory} "
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
            if not declared:
                stack.enter_context(
                    pytest.raises(
                        u.Infra.rope_attribute_not_found_error_types(),
                        match="Attribute ProviderBase not found",
                    )
                )
            project, consumed, sources = stack.enter_context(
                u.Infra.facade_source_project(
                    root,
                    declared_files=provider_analysis.files,
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
                has=f"{provider_namespace}.{family.directory}.ProviderBase",
            )
            tm.that(
                {state.path for state in consumed()[0]},
                has=barrel.resolve(),
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(barrel, required=True)),
            eq=original_barrel,
        )
        if declared:
            tm.ok(u.Tests.materialize_lazy_init(provider_service))
            tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
            native_consumer(
                f"sys.path.insert(0, {str(installed_dependency_path)!r})\n"
                f"sys.path.insert(0, {str(package.parent)!r})\n"
                f"from {provider_namespace}.{family.directory} "
                "import ProviderBase\n"
                f"from {package.name} import Consumer\n"
                "assert ProviderBase.__module__ == "
                f"{f'{provider_namespace}.{family.directory}.base'!r}\n"
                "assert issubclass(Consumer, ProviderBase)\n",
                cwd=root,
            )
