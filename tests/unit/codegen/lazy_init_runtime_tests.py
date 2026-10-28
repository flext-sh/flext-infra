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
from tests import c, m, p, tm, u


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
            (
                (
                    "_LAZY_IMPORTS = MappingProxyType(build_lazy_import_map(\n"
                    "    MappingProxyType({}),\n"
                    "    alias_groups=MappingProxyType({\n"
                    '        ".provider": (("Exported", "Declared"),),\n'
                    "    }), sort_keys=False))\n"
                ),
                "_LAZY_IMPORTS",
            ),
            (
                (
                    "_LAZY_IMPORTS = MappingProxyType(build_lazy_import_map(\n"
                    '    MappingProxyType({".provider": ("Exported",)}),\n'
                    "    alias_groups=MappingProxyType({\n"
                    '        ".provider": (("Exported", "Declared"),),\n'
                    "    })))\n"
                ),
                "_LAZY_IMPORTS",
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
            "from flext_core import build_lazy_import_map, install_lazy_exports\n"
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
            tm.ok(package.name in graph)
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
                cwd=package.parent,
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @staticmethod
    def test_native_builder_cycle_is_rejected_without_execution(tmp_path: Path) -> None:
        """SDK builder arguments retain the declaration-cycle proof."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = (
            "from types import MappingProxyType\n"
            "from flext_core import build_lazy_import_map, install_lazy_exports\n"
            "_GROUPS = MappingProxyType(build_lazy_import_map(_GROUPS))\n"
            '__all__ = ("Exported",)\n'
            "install_lazy_exports(\n"
            "    __name__, globals(), _GROUPS, public_exports=__all__)\n"
        )
        initializer = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(initializer, source))
        with (
            infra.rope_workspace(repository) as workspace,
            pytest.raises(ValueError, match="Cyclic lazy alias mapping declaration"),
        ):
            u.Infra.lazy_export_bindings(
                package.name, initializer, source, project=workspace.rope_project
            )

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
        tmp_path: Path, source: str, expected: tuple[str, ...]
    ) -> None:
        """Only explicit module metadata or a single root's metadata publishes."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-export-metadata",
            package_name="flext_export_metadata",
        )
        initializer = package / c.Infra.INIT_PY
        initializer.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(repository) as workspace:
            module = u.Infra.resolve_pymodule(
                workspace.rope_project,
                workspace.rope_project.get_file(
                    initializer.relative_to(repository).as_posix()
                ),
            )
            assert isinstance(module, p.Infra.RopeSourceModule)
            tm.that(u.Infra.public_export_names_source(module), eq=expected)
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
        *,
        imported_alias: bool,
        published_alias: bool,
    ) -> None:
        """Generated initializers propagate precise aliases at module scope."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-owned-tests",
            package_name="flext_owned_tests",
        )
        layout = u.Infra.layout(repository)
        if layout is None:
            pytest.fail("The fixture must declare its native project layout")
        u.Tests.write_lazy_init_namespace_module(
            package / "constants.py",
            class_name=f"{layout.class_stem}Constants",
            alias="c",
        )
        package.joinpath("api.py").write_text(
            f"class {layout.class_stem}Api: pass\n"
            f"__all__ = ('{layout.class_stem}Api',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        testing = repository / c.Infra.DIR_TESTS
        testing.mkdir()
        declaration = testing / "constants.py"
        declaration.write_text(
            ("from flext_owned_tests.constants import c\n" if imported_alias else "")
            + f"class Tests{layout.class_stem}Constants:\n"
            + (
                f"    __all__ = ('Tests{layout.class_stem}Constants', 'c')\n"
                if published_alias
                else f"    __all__ = ('Tests{layout.class_stem}Constants',)\n"
            )
            + "    value = 'local'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        nested = testing / "unit"
        nested.mkdir()
        nested.joinpath("provider.py").write_text(
            "from tests import c, r\n"
            f"class Tests{layout.class_stem}Provider(c):\n"
            f"    __all__ = ('Tests{layout.class_stem}Provider',)\n",
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
        tooling = tm.ok(
            u.Cli.run_raw(
                (
                    str(u.Infra.runtime_python(repository)),
                    "-I",
                    "-c",
                    (
                        "import importlib.util; "
                        "print(importlib.util.find_spec('flext_infra') is None)"
                    ),
                ),
                cwd=repository,
            )
        )
        tm.that(u.Cli.process_succeeded(tooling.outcome), eq=True, msg=tooling.stderr)
        tm.that(tooling.stdout.strip(), eq="True")

        tm.ok(infra.codegen_generate(request))

        generated = {path: path.read_bytes() for path in testing.rglob(c.Infra.INIT_PY)}
        tm.that(len(generated), eq=2)
        for content in generated.values():
            source = content.decode(c.DEFAULT_ENCODING)
            module = ast.parse(source)
            roots = [node for node in module.body if isinstance(node, ast.ClassDef)]
            tm.that(roots, empty=True)
            for node in module.body:
                if isinstance(node, ast.Expr):
                    tm.that(
                        (
                            node is module.body[0]
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        )
                        or (
                            isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "install_lazy_exports"
                        ),
                        eq=True,
                    )
                elif isinstance(node, ast.If):
                    tm.ok(isinstance(node.test, ast.Name))
                    tm.that(ast.unparse(node.test), eq="TYPE_CHECKING")
                    tm.fail(bool(node.orelse))
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
                sum(
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "install_lazy_exports"
                    for node in ast.walk(module)
                ),
                eq=1,
            )
        with infra.rope_workspace(repository) as workspace:
            for generated_path in generated:
                native = u.Infra.resolve_pymodule(
                    workspace.rope_project,
                    workspace.rope_project.get_file(
                        generated_path.relative_to(repository).as_posix()
                    ),
                )
                assert isinstance(native, p.Infra.RopeSourceModule)
                tm.ok(bool(u.Infra.public_export_names_source(native)))
        initializer = testing / c.Infra.INIT_PY
        source = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            any(
                item.level == 0
                and item.module
                == ("tests.constants" if published_alias else layout.package_name)
                and any(
                    alias.name == "c" and (alias.asname or alias.name) == "c"
                    for alias in item.names
                )
                for node in ast.parse(source).body
                if isinstance(node, ast.If)
                for item in node.body
                if isinstance(item, ast.ImportFrom)
            ),
            eq=True,
            msg=source,
        )
        tm.that(
            "tests.c"
            in u.Infra.runtime_evaluated_base_classes(
                repository,
                {initializer: source},
                (f"flext_owned_tests.constants.{layout.class_stem}Constants",),
            ),
            eq=True,
        )
        if published_alias:
            planned_source = source.replace(
                '"c": ".constants"',
                f'"c": (".constants", "Tests{layout.class_stem}Constants")',
            )
            tm.fail(planned_source == source)
            tm.that(
                "tests.c"
                in u.Infra.runtime_evaluated_base_classes(
                    repository,
                    {initializer: planned_source},
                    (f"tests.constants.Tests{layout.class_stem}Constants",),
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
                f"from tests.constants import Tests{layout.class_stem}Constants\n"
                "from flext_owned_tests.constants import c as expected\n"
                "print(generated.c is expected)\n"
                f"print(generated.Tests{layout.class_stem}Constants "
                f"is Tests{layout.class_stem}Constants)\n"
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
    def test_parent_drops_removed_child_from_its_lazy_map(tmp_path: Path) -> None:
        """A retired child initializer is deleted and leaves the parent exports."""
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
        plans = tm.ok(u.Tests.create_lazy_init_service(repository).plan_files())
        child_plan = next(plan for plan in plans if plan.path == initializer)
        parent_plan = next(
            plan for plan in plans if plan.path == package / c.Infra.INIT_PY
        )
        tm.that(child_plan.desired_content, eq=None)
        tm.that(
            tm.not_none(parent_plan.desired_content).decode(c.DEFAULT_ENCODING),
            lacks="retired",
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
        tmp_path: Path, family: Literal["c", "m"]
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
            "class FlextModelsPlanned(FlextPlannedErrors):\n"
            "    class Response(FlextPlannedErrors.Payload):\n"
            '        code: int = parent.Field(description="Response code.")\n'
            "m = FlextModelsPlanned\n"
            "__all__ = ('FlextModelsPlanned', 'm')\n",
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
            "class FlextModelsStale(FlextStaleErrors):\n"
            "    class Response(FlextStaleErrors.Payload):\n"
            '        code: int = parent.Field(description="Response code.")\n'
            "m = FlextModelsStale\n"
            "__all__ = ('FlextModelsStale', 'm')\n",
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
        planned = {
            plan.path.resolve(): plan.desired_content.decode(c.DEFAULT_ENCODING)
            for plan in tm.ok(u.Tests.create_lazy_init_service(repository).plan_files())
            if plan.path.suffix == c.Infra.EXT_PYTHON
            and plan.desired_content is not None
        }
        with (
            infra.rope_workspace(repository) as workspace,
            u.Infra.facade_source_project(
                repository,
                planned_sources=planned,
                source_project=workspace.rope_project,
            ) as (project, _captured),
        ):
            module = u.Infra.resolve_pymodule(
                project,
                project.get_file(
                    (family / c.Infra.INIT_PY).relative_to(repository).as_posix()
                ),
            )
            assert isinstance(module, p.Infra.RopeSourceModule)
            exports = u.Infra.public_export_names_source(module)
        tm.ok("FlextStaleErrors" in exports)
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
