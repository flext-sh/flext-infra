"""Runtime behavior tests for generated lazy package artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Literal

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u


class TestsFlextInfraLazyInitRuntime:
    """Exercise generated roots through Python's real import machinery."""

    @staticmethod
    @pytest.mark.parametrize(
        ("declarations", "mapping_argument"),
        [
            (
                "",
                'MappingProxyType({"Exported": (".provider", "Declared")})',
            ),
            (
                (
                    "_LAZY_IMPORTS = MappingProxyType("
                    '{"Exported": (".provider", "Declared")})\n'
                ),
                "_LAZY_IMPORTS",
            ),
            (
                (
                    '_PROVIDERS = {"Exported": (".provider", "Declared")}\n'
                    "_LAZY_IMPORTS = MappingProxyType(_PROVIDERS)\n"
                ),
                "lazy_imports=_LAZY_IMPORTS",
            ),
        ],
    )
    def test_native_alias_inventory_matches_the_runtime_initializer(
        tmp_path: Path, declarations: str, mapping_argument: str
    ) -> None:
        """Named and inline maps preserve their actual exported attribute."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = (
            "from types import MappingProxyType\n"
            "from flext_core import install_lazy_exports\n"
            + declarations
            + '__all__ = ("Exported",)\n'
            + "__getattr__ = install_lazy_exports(\n"
            + f"    __name__, globals(), {mapping_argument}, public_exports=__all__\n"
            + ")[0]\n"
        )
        initializer = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(initializer, source))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "provider.py",
                'class Declared:\n    marker = True\n__all__ = ("Declared",)\n',
            )
        )
        with infra.rope_workspace(repository) as workspace:
            module = u.Infra.resolve_pymodule(
                workspace.rope_project,
                workspace.rope_project.get_file(
                    initializer.relative_to(repository).as_posix()
                ),
            )
            bindings = u.Infra.lazy_export_bindings(
                package.name,
                initializer,
                source,
                project=workspace.rope_project,
                pymodule=module,
            )
            tm.that(bindings["Exported"].target, eq=f"{package.name}.provider")
            tm.that(bindings["Exported"].attributes, eq=("Declared",))
            tm.that(
                u.Infra.lazy_module_aliases(
                    package.name,
                    initializer,
                    source,
                    project=workspace.rope_project,
                ),
                eq={"Exported": bindings["Exported"].target},
            )
            graph, modules = u.Infra.snapshot_import_graph(workspace.rope_project)
            tm.that(package.name in graph, eq=True)
            tm.that(modules[initializer.resolve()], eq=package.name)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "import sys\n"
                        f"from {package.name} import Exported\n"
                        "assert Exported is "
                        f"sys.modules['{package.name}.provider'].Declared\n"
                        "assert Exported.marker is True\n"
                    ),
                ),
                cwd=repository,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    }
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("class Root:\n    __all__ = ('Root',)\n", ("Root",)),
            ("class Root:\n    __all__: tuple[str, ...] = ()\n", ()),
            (
                "__all__ = ('Module',)\nclass Root:\n    __all__ = ('Root',)\n",
                ("Module",),
            ),
            ("class Root:\n    class Nested:\n        __all__ = ('Nested',)\n", ()),
            ("class First:\n    __all__ = ('First',)\nclass Second: pass\n", ()),
        ],
    )
    def test_export_metadata_has_one_declaration_owner(
        source: str, expected: tuple[str, ...]
    ) -> None:
        """Only explicit module metadata or a single root's metadata publishes."""
        tm.that(u.Infra.public_export_names_source(source), eq=expected)
        tm.that(
            u.Infra.module_export_names_source(
                source,
                export_options=m.Infra.ExportOptions(require_explicit_all=True),
            ),
            eq=expected,
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("imported_alias", "published_alias"),
        [(False, False), (True, False), (True, True)],
    )
    def test_public_generation_publishes_test_exports_without_namespace_classes(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        imported_alias: bool,
        published_alias: bool,
    ) -> None:
        """Generated initializers propagate precise aliases at module scope."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-owned-tests",
            package_name="flext_owned_tests",
        )
        u.Tests.write_lazy_init_namespace_module(
            package / "constants.py", class_name="ParentConstants", alias="c"
        )
        package.joinpath("api.py").write_text(
            "class PublishedApi: pass\n__all__ = ('PublishedApi',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        testing = repository / c.Infra.DIR_TESTS
        testing.mkdir()
        declaration = testing / "constants.py"
        declaration.write_text(
            ("from flext_owned_tests.constants import c\n" if imported_alias else "")
            + "class TestsFlextOwnedTestsConstants:\n"
            + (
                "    __all__ = ('TestsFlextOwnedTestsConstants', 'c')\n"
                if published_alias
                else "    __all__ = ('TestsFlextOwnedTestsConstants',)\n"
            )
            + "    value = 'local'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        nested = testing / "unit"
        nested.mkdir()
        nested.joinpath("provider.py").write_text(
            "from tests import c\n"
            "class TestsFlextOwnedTestsProvider(c):\n"
            "    __all__ = ('TestsFlextOwnedTestsProvider',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        original = declaration.read_bytes()
        request = m.Infra.CodegenGenerateRequest(
            root=repository,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        tm.ok(
            u.Tests.create_python_environment(
                repository,
                dependency_projects=u.Tests.python_dependency_projects(repository),
                session_runtime=session_runtime,
            ),
        )

        tm.ok(infra.codegen_generate(request))

        generated = {path: path.read_bytes() for path in testing.rglob(c.Infra.INIT_PY)}
        tm.that(len(generated), eq=2)
        for content in generated.values():
            source = content.decode(c.DEFAULT_ENCODING)
            module = ast.parse(source)
            roots = [node for node in module.body if isinstance(node, ast.ClassDef)]
            tm.that(roots, empty=True)
            for node in module.body:
                if isinstance(node, ast.If):
                    tm.that(isinstance(node.test, ast.Name), eq=True)
                    tm.that(ast.unparse(node.test), eq="TYPE_CHECKING")
                    tm.that(bool(node.orelse), eq=False)
                    tm.that(
                        all(
                            isinstance(item, (ast.Import, ast.ImportFrom))
                            for item in node.body
                        ),
                        eq=True,
                    )
                else:
                    tm.that(
                        isinstance(
                            node,
                            (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign),
                        ),
                        eq=True,
                    )
            tm.that(
                any(
                    isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "__getattr__"
                        for target in node.targets
                    )
                    for node in module.body
                ),
                eq=True,
            )
            tm.that(bool(u.Infra.public_export_names_source(source)), eq=True)
        initializer = testing / c.Infra.INIT_PY
        source = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        expected_target = "c" if published_alias else "TestsFlextOwnedTestsConstants"
        tm.that(
            any(
                item.level == 0
                and item.module == "tests.constants"
                and any(
                    alias.name == expected_target and alias.asname == "c"
                    for alias in item.names
                )
                for node in ast.parse(source).body
                if isinstance(node, ast.If)
                for item in node.body
                if isinstance(item, ast.ImportFrom)
            ),
            eq=True,
        )
        base = (
            "flext_owned_tests.constants.ParentConstants"
            if published_alias
            else "tests.constants.TestsFlextOwnedTestsConstants"
        )
        tm.that(
            "tests.c"
            in u.Infra.runtime_evaluated_base_classes(
                repository, {initializer: source}, (base,)
            ),
            eq=True,
        )
        if published_alias:
            planned_source = source.replace(
                '"c": ".constants"',
                '"c": (".constants", "TestsFlextOwnedTestsConstants")',
            )
            tm.that(planned_source == source, eq=False)
            tm.that(
                "tests.c"
                in u.Infra.runtime_evaluated_base_classes(
                    repository,
                    {initializer: planned_source},
                    ("tests.constants.TestsFlextOwnedTestsConstants",),
                ),
                eq=True,
            )
        tm.that(declaration.read_bytes(), eq=original)
        tm.ok(infra.codegen_generate(request))
        tm.that({path: path.read_bytes() for path in generated}, eq=generated)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nimport tests as generated\n"
                "print('flext_owned_tests' not in sys.modules)\n"
                "print('tests.constants' not in sys.modules)\n"
                "from tests.constants import TestsFlextOwnedTestsConstants\n"
                + (
                    "from flext_owned_tests.constants import c as expected\n"
                    if published_alias
                    else "expected = TestsFlextOwnedTestsConstants\n"
                )
                + "print(generated.c is expected)\n"
                "print(generated.TestsFlextOwnedTestsConstants "
                "is TestsFlextOwnedTestsConstants)\n"
                "print(all(name in dir(generated) for name in generated.__all__) "
                "and 'TestsFlextOwnedTestsPackage' not in generated.__all__)\n"
                "print('flext_owned_tests.api' not in sys.modules)\n",
                python_paths=(
                    str(repository),
                    str(repository / c.Infra.DEFAULT_SRC_DIR),
                ),
                cwd=repository,
            ),
            eq=["True"] * 6,
        )

    @staticmethod
    @pytest.mark.parametrize("exports", [False, True])
    def test_isolated_package_decisions_keep_only_consumed_original_reads(
        tmp_path: Path,
        *,
        exports: bool,
    ) -> None:
        """Cold artifact graphs retain negative modules with no cross-surface leak."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "class Published: pass\n__all__ = ['Published']\n",
            ),
        )
        tests = repository / c.Infra.DIR_TESTS
        tests.mkdir()
        conftest = tests / "conftest.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                conftest,
                "class TestProvider: pass\n__all__ = ['TestProvider']\n"
                if exports
                else "__all__ = []\n",
            ),
        )
        analysis = tm.ok(u.Tests.create_lazy_init_service(repository).plan_files())
        production = next(
            plan for plan in analysis.publications if plan.context.pkg_dir == package
        )
        testing = next(
            plan for plan in analysis.publications if plan.context.pkg_dir == tests
        )
        tm.that(source in {state.path for state in production.source_states}, eq=True)
        tm.that(
            conftest in {state.path for state in production.source_states}, eq=False
        )
        tm.that(conftest in {state.path for state in testing.source_states}, eq=True)

    @staticmethod
    def test_parent_consumes_original_receipt_of_removed_child(tmp_path: Path) -> None:
        """A cached negative child decision remains an authenticated parent input."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "service.py",
                "class Published: pass\n__all__ = ['Published']\n",
            ),
        )
        child = package / "retired"
        child.mkdir()
        initializer = child / c.Infra.INIT_PY
        tm.ok(
            u.Cli.atomic_write_text_file(initializer, c.Infra.AUTOGEN_HEADER + "\n"),
        )
        analysis = tm.ok(u.Tests.create_lazy_init_service(repository).plan_files())
        child_plan = next(
            plan for plan in analysis.publications if plan.context.pkg_dir == child
        )
        parent_plan = next(
            plan for plan in analysis.publications if plan.context.pkg_dir == package
        )
        tm.that(child_plan.action, eq=c.Infra.LazyInitAction.REMOVE)
        tm.that("retired" in parent_plan.lazy_map, eq=False)
        child_original = next(
            state for state in child_plan.source_states if state.path == initializer
        )
        tm.that(
            next(
                state
                for state in parent_plan.source_states
                if state.path == initializer
            ),
            eq=child_original,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "ownership",
        [
            "single",
            "scoped",
            "rebound",
            "module",
            "module-only",
            "entities",
            "standalone",
            "parenthesized",
        ],
    )
    def test_declared_model_publication_preserves_symbol_ownership(
        tmp_path: Path,
        ownership: str,
    ) -> None:
        """The generated public facade retains the final publisher's real models."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_families()["m"]
        owners = package / family.directory
        owner = owners / "owner.py"
        source = (
            "from flext_core import m as parent\n"
            "class PublishedOwner:\n"
            "    class Payload(parent.ContractModel):\n"
            "        value: int = parent.Field(description='Payload value.')\n"
            "__all__ = ['PublishedOwner']\n"
        )
        sources = {owner: source}
        if ownership == "scoped":
            sources[owners / "parts" / "owner.py"] = source
            sources[owner] = (
                "from .parts.owner import PublishedOwner as ParentOwner\n"
                "class PublishedOwner(ParentOwner): pass\n"
                "__all__ = ['PublishedOwner']\n"
            )
        if ownership == "rebound":
            sources[owner] = source.replace("value: int", "value: str") + source
        facade = package / f"{family.module}.py"
        sources[facade] = (
            "from flext_core import m as parent\n"
            "class Facade(parent): pass\n"
            "m = Facade\n__all__ = ['Facade', 'm']\n"
        )
        if ownership == "parenthesized":
            sources[facade] = sources[facade].replace(
                "from flext_core import m as parent\n",
                "from flext_core import (\n    m as parent,\n)\n",
            )
        if ownership == "standalone":
            sources[owners / "standalone.py"] = (
                "from flext_core import m as parent\n"
                "class Standalone(parent.ContractModel):\n"
                "    value: int = parent.Field(description='Standalone value.')\n"
                "__all__ = ['Standalone']\n"
            )
            sources[package / "service.py"] = (
                f"from {package.name}.{family.directory} import Standalone\n"
                "__all__ = ['Standalone']\n"
            )
        if ownership == "entities":
            sources[owner] = source.replace(
                "__all__ = ['PublishedOwner']\n",
                "    class First: value = 'first'\n"
                "    class Second: value = 'second'\n"
                "__all__ = ['PublishedOwner']\n",
            )
        if ownership in {"module", "module-only"}:
            sources[package / "ancestor.py"] = (
                "class Ancestor: pass\n__all__ = ['Ancestor']\n"
            )
            base = "backing.Ancestor" if ownership == "module" else "backing"
            sources[facade] = (
                f"import {package.name}.ancestor as backing\n"
                f"class Facade({base}): pass\n"
                "m = Facade\n__all__ = ['Facade', 'm']\n"
            )
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        u.Tests.git_run(
            repository,
            "add",
            "--",
            *(str(path.relative_to(repository)) for path in sources),
        )
        if ownership == "module-only":
            with pytest.raises(ValueError, match="Module used as a class base"):
                u.Infra.render_utility_facade(package, family="m")
            return
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import m\n"
                "payload = m.Payload.model_validate_json('{\"value\":7}')\n"
                "print(isinstance(payload.value, int))\n"
                "print(m.Payload.model_validate_json("
                "payload.model_dump_json()) == payload)\n"
                + (
                    "print((m.First.value, m.Second.value) == ('first', 'second'))\n"
                    if ownership == "entities"
                    else ""
                )
                + (
                    f"from {package.name} import Standalone\n"
                    "record = Standalone.model_validate_json('{\"value\":7}')\n"
                    "print(record.value == 7)\n"
                    if ownership == "standalone"
                    else ""
                ),
                python_paths=(str(package.parent),),
            ),
            eq=["True"] * (3 if ownership in {"entities", "standalone"} else 2),
        )
        tm.that(u.Infra.render_utility_facade(package, family="m"), eq=rendered)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)

    @staticmethod
    def test_upstream_attribute_base_stays_inherited(tmp_path: Path) -> None:
        """A namespace base reached through an installed upstream class is kept.

        The facade snapshot captures only the project's own sources, so the
        upstream package is absent from it; the base is inherited, never an
        unresolved own base.
        """
        _, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_families()["m"]
        sources = {
            package / family.directory / "owner.py": (
                "class PublishedOwner: pass\n__all__ = ['PublishedOwner']\n"
            ),
            package / f"{family.module}.py": (
                "from flext_tests import FlextTestsModels\n"
                "class Facade(FlextTestsModels):\n"
                "    class Tests(FlextTestsModels.Tests): pass\n"
                "m = Facade\n__all__ = ['Facade', 'm']\n"
            ),
        }
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        tm.that(rendered, has="FlextTestsModels.Tests")

    @staticmethod
    @pytest.mark.parametrize("family", ["c", "m"])
    def test_competing_declared_publishers_keep_their_exact_diagnostic(
        tmp_path: Path,
        family: Literal["c", "m"],
    ) -> None:
        """Equal spellings cannot erase distinct declared implementations."""
        _, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declaration = u.Infra.facade_families()[family]
        sources = {
            package / declaration.directory / f"{module}.py": (
                "class PublishedOwner: pass\n__all__ = ['PublishedOwner']\n"
            )
            for module in ("first", "second")
        }
        sources[package / f"{declaration.module}.py"] = (
            f"class Facade: pass\n{family} = Facade\n__all__ = ['Facade', '{family}']\n"
        )
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with pytest.raises(
            ValueError, match="Competing declared facade owner names"
        ) as failure:
            u.Infra.render_utility_facade(package, family=family)
        for module in ("first", "second"):
            tm.that(
                str(failure.value),
                has=f"{package.name}.{declaration.directory}.{module}:PublishedOwner",
            )

    @staticmethod
    def test_published_lazy_bases_replan_in_the_same_process(tmp_path: Path) -> None:
        """Published PEP 562 owners retain model ancestry through replanning."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-planned-bases",
            package_name="flext_planned_bases",
        )
        family = package / "_models"
        family.mkdir()
        family.joinpath("base.py").write_text(
            "class FlextPlannedBase: pass\n__all__ = ('FlextPlannedBase',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declaration = family / "errors.py"
        declaration_source = (
            "from flext_core import m\n"
            "class FlextPlannedErrors:\n"
            "    class Payload(m.ContractModel):\n"
            '        message: str = m.Field(description="Error message.")\n'
        )
        declaration.write_text(declaration_source, encoding=c.DEFAULT_ENCODING)
        package.joinpath("models.py").write_text(
            "from flext_core import m as parent\n"
            "from ._models import FlextPlannedErrors\n"
            "class FlextPlannedModels(FlextPlannedErrors):\n"
            "    class Response(FlextPlannedErrors.Payload):\n"
            '        code: int = parent.Field(description="Response code.")\n'
            "m = FlextPlannedModels\n"
            "__all__ = ('FlextPlannedModels', 'm')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        roots = u.Tests.runtime_evaluated_roots()
        with pytest.raises(ValueError, match="Unresolved planned base"):
            u.Infra.runtime_evaluated_base_classes(repository, {}, roots)
        with pytest.raises(
            AssertionError, match="cannot import name 'FlextPlannedErrors'"
        ):
            u.Tests.run_lazy_init_probe(
                "from flext_planned_bases import m\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            )
        declaration.write_text(
            declaration_source + "__all__ = ('FlextPlannedErrors',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        first = u.Infra.runtime_evaluated_base_classes(repository, {}, roots)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from flext_planned_bases import m\n"
                "response = m.Response.model_validate("
                "{'message': 'ready', 'code': 7})\n"
                "print(response.model_dump() == {'message': 'ready', 'code': 7})\n"
                "print(m.Response.model_validate_json(response.model_dump_json())"
                " == response)\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )
        published = {
            path: path.read_bytes() for path in package.rglob(c.Infra.EXT_PYTHON_GLOB)
        }
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Infra.runtime_evaluated_base_classes(repository, {}, roots), eq=first)
        tm.that({path: path.read_bytes() for path in published}, eq=published)

    @staticmethod
    def test_planned_lazy_init_resolves_bases_behind_a_stale_initializer(
        tmp_path: Path,
    ) -> None:
        """Base derivation over the planned projection converges in one pass.

        The family module declares its owner in ``__all__`` after its package
        initializer was generated, so the on-disk projection no longer
        publishes the owner the facade imports in package form. Conform
        derives tooling from the initializer bytes the same generation
        publishes, so the stale projection cannot block its own regeneration.
        """
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-stale-bases",
            package_name="flext_stale_bases",
        )
        family = package / "_models"
        family.mkdir()
        family.joinpath("base.py").write_text(
            "class FlextStaleBase: pass\n__all__ = ('FlextStaleBase',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declaration = family / "errors.py"
        declaration_source = (
            "from flext_core import m\n"
            "class FlextStaleErrors:\n"
            "    class Payload(m.ContractModel):\n"
            '        message: str = m.Field(description="Error message.")\n'
        )
        declaration.write_text(declaration_source, encoding=c.DEFAULT_ENCODING)
        package.joinpath("models.py").write_text(
            "from flext_core import m as parent\n"
            "from ._models import FlextStaleErrors\n"
            "class FlextStaleModels(FlextStaleErrors):\n"
            "    class Response(FlextStaleErrors.Payload):\n"
            '        code: int = parent.Field(description="Response code.")\n'
            "m = FlextStaleModels\n"
            "__all__ = ('FlextStaleModels', 'm')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        declaration.write_text(
            declaration_source + "__all__ = ('FlextStaleErrors',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        roots = u.Tests.runtime_evaluated_roots()
        with pytest.raises(ValueError, match="Unresolved planned base"):
            u.Infra.runtime_evaluated_base_classes(repository, {}, roots)
        analysis = tm.ok(u.Tests.plan_lazy_init(repository))
        planned = {
            plan.path.resolve(): plan.desired_content.decode(c.DEFAULT_ENCODING)
            for plan in analysis.files
            if plan.path.suffix == c.Infra.EXT_PYTHON
            and plan.desired_content is not None
        }
        exports = u.Infra.public_export_names_source(
            planned[(family / c.Infra.INIT_PY).resolve()],
        )
        tm.that("FlextStaleErrors" in exports, eq=True)
        derived = u.Infra.runtime_evaluated_base_classes(repository, planned, roots)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Infra.runtime_evaluated_base_classes(repository, {}, roots),
            eq=derived,
        )

    @staticmethod
    def test_explicit_hook_exports_follow_their_source_declaration(
        tmp_path: Path,
    ) -> None:
        """A declared hook name has no filename-specific publication bypass."""
        repository, _ = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-fixtures",
            package_name="flext_fixtures",
        )
        package = repository / "tests" / "unit"
        package.mkdir(parents=True, exist_ok=True)
        (package.parent / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (package / "support.py").write_text(
            "class PublishedSupport:\n    pass\n__all__ = ['PublishedSupport']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        conftest = package / "conftest.py"
        private_source = "pytest_plugins = []\n__all__ = ['pytest_plugins']\n"
        conftest.write_text(private_source, encoding=c.DEFAULT_ENCODING)

        tm.that(u.Tests.run_lazy_init(repository), eq=0)

        tm.that(
            u.Tests.run_lazy_init_probe(
                "from tests.unit import PublishedSupport, pytest_plugins\n"
                "print(isinstance(PublishedSupport(), PublishedSupport))\n"
                "print(pytest_plugins == [])\n",
                python_paths=(str(repository),),
                cwd=repository,
            ),
            eq=["True", "True"],
        )
        tm.that(conftest.read_text(encoding=c.DEFAULT_ENCODING), eq=private_source)

    @staticmethod
    def _generate_package(tmp_path: Path) -> t.Pair[Path, Path]:
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-lazy-demo",
            package_name="flext_lazy_demo",
        )
        package_root.joinpath("api.py").write_text(
            "from pathlib import Path\n"
            "COUNTER = Path(__file__).with_name('imports.txt')\n"
            "COUNTER.write_text("
            "COUNTER.read_text() + 'x' if COUNTER.exists() else 'x')\n"
            "class FlextDemo:\n    pass\n"
            "primary = FlextDemo\n"
            "__all__ = ('FlextDemo', 'primary')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        return repository_root, package_root

    def test_generated_root_preserves_lazy_runtime_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated root preserves lazy runtime contract."""
        repository_root, package_root = self._generate_package(tmp_path)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\n"
                "import flext_lazy_demo as package\n"
                "print('flext_lazy_demo.api' not in sys.modules)\n"
                "print(package.__all__ == ('FlextDemo', 'primary'))\n"
                "print(dir(package) == list(package.__all__))\n"
                "first = package.FlextDemo\n"
                "print(first is package.FlextDemo is package.primary)\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * 4,
        )
        tm.that(package_root.joinpath("imports.txt").read_text(), eq="x")

    @staticmethod
    def test_generated_version_metadata_survives_public_export_traversal(
        tmp_path: Path,
    ) -> None:
        """Resolving the version class cannot shadow the declared version scalar."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = tm.ok(u.Infra.read_project_metadata_result(repository))
        version_name = c.Infra.DUNDER_VERSION
        version = metadata.project.version
        package.joinpath(f"{version_name}.py").write_text(
            "class FlextVersion:\n"
            f"    {version_name}: str = {version!r}\n"
            f"{version_name} = FlextVersion.{version_name}\n"
            f"__title__ = {metadata.project.name!r}\n"
            f"__all__ = ('FlextVersion', {version_name!r}, '__title__')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {package.name} as generated\n"
                "print(isinstance(generated.FlextVersion, type))\n"
                f"print({version_name!r} in generated.__all__)\n"
                "print(all(getattr(generated, name) is not None\n"
                "          for name in generated.__all__\n"
                f"          if name != {version_name!r}))\n"
                f"value = getattr(generated, {version_name!r})\n"
                f"print(isinstance(value, str) and value == {version!r})\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"] * 4,
        )

    @staticmethod
    def test_generated_root_never_invents_undeclared_api_alias(
        tmp_path: Path,
    ) -> None:
        """Test generated root never invents undeclared api alias."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-bare",
            package_name="flext_bare",
        )
        package_root.joinpath("api.py").write_text(
            "class FlextBare:\n    pass\n__all__ = ('FlextBare',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_bare as package\n"
                "print(package.__all__ == ('FlextBare',))\n"
                "print(all(hasattr(package, name) for name in package.__all__))\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )

    @staticmethod
    def test_generated_model_alias_preserves_mro_and_pydantic_roundtrip(
        tmp_path: Path,
    ) -> None:
        """Resolve deferred annotations through the generated public model alias."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-runtime-model",
            package_name="flext_runtime_model",
        )
        package_root.joinpath("models.py").write_text(
            "from __future__ import annotations\n"
            "from flext_core import FlextModels\n"
            "class FlextRuntimeModels(FlextModels):\n"
            "    class Payload(FlextModels.ContractModel):\n"
            '        count: int = FlextModels.Field(description="Payload count.")\n'
            "m = FlextRuntimeModels\n"
            "__all__ = ('FlextRuntimeModels', 'm')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        probe = (
            "import sys\n"
            "from flext_core import FlextModels, e\n"
            "import flext_runtime_model as package\n"
            "print('flext_runtime_model.models' not in sys.modules)\n"
            "models = package.m\n"
            "print(models is package.FlextRuntimeModels is package.m)\n"
            "print(issubclass(models, FlextModels))\n"
            "payload = models.Payload.model_validate({'count': 7})\n"
            "print(payload.count == 7)\n"
            "print(models.Payload.model_validate_json(payload.model_dump_json())"
            " == payload)\n"
            "try:\n"
            "    models.Payload.model_validate({'count': 'invalid'})\n"
            "except e.PydanticValidationError as error:\n"
            "    print('count' in str(error))\n"
            "print(dir(package) == list(package.__all__))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * 7,
        )

    @staticmethod
    @pytest.mark.parametrize("same_named_export", [False, True])
    def test_child_package_preserves_export_ownership(
        tmp_path: Path,
        *,
        same_named_export: bool,
    ) -> None:
        """Child packages resolve as modules; competing public owners fail loud."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-child-runtime",
            package_name="flext_child_runtime",
        )
        child = package_root / "child"
        child.mkdir()
        (child / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (child / "api.py").write_text(
            "class PublishedChild:\n    pass\n"
            + (
                "child = PublishedChild\n__all__ = ('PublishedChild', 'child')\n"
                if same_named_export
                else "__all__ = ('PublishedChild',)\n"
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        if same_named_export:
            with pytest.raises(RuntimeError, match="ownership is ambiguous"):
                u.Tests.run_lazy_init(repository)
            return
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        probe = (
            "import flext_child_runtime as package\n"
            "import flext_child_runtime.child as child\n"
            "print(package.child is child)\n"
            "print('PublishedChild' not in package.__all__)\n"
            "print(isinstance(child.PublishedChild(), child.PublishedChild))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True", "True"],
        )

    @staticmethod
    def test_empty_package_preserves_its_unmanaged_initializer(tmp_path: Path) -> None:
        """No published declarations means no generated root contract is invented."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-empty-runtime",
            package_name="flext_empty_runtime",
        )
        package_root.joinpath("api.py").write_text(
            "__all__ = ()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        initializer = package_root / c.Infra.INIT_PY
        initializer.write_text(
            '"""Authored package without published declarations."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        original = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        probe = (
            "import flext_empty_runtime as package\n"
            "print(not hasattr(package, '__all__'))\n"
            "try:\n"
            "    package.undeclared\n"
            "except AttributeError as error:\n"
            "    print('undeclared' in str(error))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )

    @staticmethod
    def test_generated_root_preserves_import_failures(tmp_path: Path) -> None:
        """Test generated root preserves import failures."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-failure",
            package_name="flext_failure",
        )
        package_root.joinpath("api.py").write_text(
            "raise ModuleNotFoundError('missing runtime dependency')\n"
            "class FlextDemo:\n    pass\n"
            "__all__ = ('FlextDemo',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_failure as package\n"
                "try:\n"
                "    package.FlextDemo\n"
                "except ModuleNotFoundError as error:\n"
                "    print(str(error) == 'missing runtime dependency')\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"],
        )

    @staticmethod
    @pytest.mark.parametrize("cyclic", [False, True])
    def test_public_generation_repairs_existing_and_absent_initializers(
        tmp_path: Path, cyclic: bool
    ) -> None:
        """Generation converges without executing or repairing authored consumers."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-source-only",
            package_name="flext_source_only",
        )
        u.Tests.write_lazy_init_namespace_module(
            package / "models.py",
            class_name="PublishedModels",
            alias="m",
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        initializer = package / c.Infra.INIT_PY
        original = initializer.read_bytes()
        authored = package / "api.py"
        authored.write_text(
            (
                "from flext_source_only.child.api import PublishedChild\n"
                if cyclic
                else "raise ModuleNotFoundError('unavailable runtime dependency')\n"
            )
            + "class PublishedApi:\n    value: int = 'invalid annotation value'\n"
            "__all__ = ('PublishedApi',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        child = package / "child"
        child.mkdir()
        child.joinpath("api.py").write_text(
            "from flext_source_only.api import PublishedApi\n"
            "class PublishedChild:\n    pass\n"
            "__all__ = ('PublishedChild',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = {path: path.read_bytes() for path in package.rglob("*.py")}
        request = m.Infra.CodegenGenerateRequest(
            root=repository,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
        )

        tm.ok(infra.codegen_generate(request))

        tm.that(initializer.read_bytes() == original, eq=False)
        child_initializer = child / c.Infra.INIT_PY
        tm.that(child_initializer.is_file(), eq=True)
        for path, content in before.items():
            if path != initializer:
                tm.that(path.read_bytes(), eq=content)
        generated = {path: path.read_bytes() for path in package.rglob(c.Infra.INIT_PY)}
        tm.ok(infra.codegen_generate(request))
        tm.that(
            {path: path.read_bytes() for path in generated},
            eq=generated,
        )
        error_name = "ImportError" if cyclic else "ModuleNotFoundError"
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_source_only as package\n"
                "print('PublishedApi' in package.__all__)\n"
                "print('child' in package.__all__)\n"
                "try:\n"
                "    package.PublishedApi\n"
                "except ImportError as error:\n"
                f"    print(type(error).__name__ == '{error_name}')\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True", "True"],
        )

    @staticmethod
    def test_conflicted_generated_initializer_is_rebuilt_from_declarations(
        tmp_path: Path,
    ) -> None:
        """Generated bytes are outputs, including while a merge is unresolved."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-rebuilt",
            package_name="flext_rebuilt",
        )
        declaration = package / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            declaration,
            class_name="FlextRebuiltModels",
            alias="m",
            docstring="Models.",
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        initializer = package / c.Infra.INIT_PY
        canonical = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        conflicted = canonical + (
            "\n<<<<<<< HEAD\n__all__ = ['stale']\n"
            "=======\n__all__ = ['obsolete']\n>>>>>>> incoming\n"
        )
        initializer.write_text(conflicted, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(repository) as rope:
            layout = tm.not_none(rope.layout(repository))
            tm.that(layout.runtime_aliases, eq=("m",))
        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=conflicted)

        tm.that(u.Tests.run_lazy_init(repository), eq=0)

        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=canonical)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_rebuilt as generated\n"
                "from flext_rebuilt.models import FlextRebuiltModels\n"
                "print(generated.m is FlextRebuiltModels)\n"
                "print(all(hasattr(generated, name) for name in generated.__all__))\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )
        declaration.write_text(
            "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(repository) as rope, pytest.raises(SyntaxError):
            rope.layout(repository)

    @staticmethod
    def test_internal_facade_requires_its_local_declaration(
        tmp_path: Path,
    ) -> None:
        """An undeclared letter propagates the declaring root's binding.

        Operator ruling (tier-alias propagation): a module declaring the
        letter wins. A facet that declares no letter inherits the root's
        declared letter, and the generator never rewrites the facet to
        substitute a local class for it.
        """
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-local",
            package_name="flext_local",
        )
        package.joinpath("constants.py").write_text(
            "class Parent:\n    class Domain:\n        pass\n"
            "c = Parent\n__all__ = ('Parent', 'c')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        examples = repository / "examples"
        examples.mkdir()
        examples.joinpath("__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        facet = examples / "constants.py"
        facet_source = (
            "from flext_local.constants import Parent\n"
            "class Local(Parent):\n    pass\n__all__ = ('Local',)\n"
        )
        facet.write_text(facet_source, encoding=c.DEFAULT_ENCODING)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        # The facet declares no letter, so the generator leaves it untouched:
        # no runtime-alias repair may invent a local binding for one.
        tm.that(facet.read_text(encoding=c.DEFAULT_ENCODING), eq=facet_source)
        exports = u.Infra.public_export_names_source(
            examples.joinpath("__init__.py").read_text(encoding=c.DEFAULT_ENCODING),
        )
        tm.that("c" in exports, eq=True)
        probe = (
            "import examples as generated\n"
            "import examples.constants as local\n"
            "import flext_local.constants as parent\n"
            "print('c' in generated.__all__)\n"
            "print(generated.c is parent.c)\n"
            "print(generated.c is parent.Parent)\n"
            "print(generated.c is local.Local)\n"
            "print(all(hasattr(generated, name) for name in generated.__all__))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(
                    str(repository),
                    str(repository / c.Infra.DEFAULT_SRC_DIR),
                    *sys.path,
                ),
                cwd=repository,
            ),
            eq=["True", "True", "True", "False", "True"],
        )
