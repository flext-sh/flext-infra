"""Public contract tests for canonical lazy-init artifact rendering.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.util import resolve_name
from pathlib import Path
from types import MappingProxyType

import flext_core
import pytest

from flext_infra import config, u
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
from flext_infra.deps.phases.tool_tables import FlextInfraToolTablesPhase
from flext_infra.gates import FlextInfraRuffLintGate
from tests import c, m, t, tm, u


class TestsFlextInfraCodegenGeneration:
    """Validate observable generated Python artifacts without legacy internals."""

    @classmethod
    def _bootstrap_content(
        cls, tmp_path: Path, current_pkg: str, provider: str, export: str
    ) -> str:
        """Render a real loader dependency and prove its cold bootstrap identity.

        Returns:
            The initializer rendered against materialized loader source.

        """
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-bootstrap",
            package_name=c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE,
        )
        source_root = package.parent
        package_dir = source_root.joinpath(*current_pkg.split("."))
        package_dir.mkdir(parents=True)
        source_root.joinpath(*provider.split(".")).with_suffix(".py").write_text(
            f"class {export}: pass\n", encoding=c.DEFAULT_ENCODING
        )
        source_root.joinpath(*c.Infra.LAZY_BOOTSTRAP_MODULE.split(".")).with_suffix(
            ".py"
        ).write_text(f"from {provider} import {export}\n", encoding=c.DEFAULT_ENCODING)
        plan = cls._plan(
            current_pkg,
            (export,),
            {export: (provider, export)},
            package_dir=package_dir,
        )
        source = FlextInfraCodegenGeneration.render_init(plan)
        compile(source, str(plan.context.init_path), "exec")
        tm.that(source, lacks=f"from {c.Infra.LAZY_BOOTSTRAP_MODULE} import")
        tm.that(source, lacks="install_lazy_exports")
        tm.that(u.Infra.public_export_names_source(source), eq=(export,))
        plan.context.init_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {c.Infra.LAZY_BOOTSTRAP_MODULE} as loader\n"
                f"import {current_pkg} as dependency\n"
                f"from {provider} import {export}\n"
                f"print(loader.{export} is dependency.{export} is {export})\n",
                python_paths=(str(source_root),),
                cwd=repository,
            ),
            eq=["True"],
        )
        tm.that(FlextInfraCodegenGeneration.render_init(plan), eq=source)
        return source

    @staticmethod
    def test_class_owned_test_root_installs_lazy_exports(tmp_path: Path) -> None:
        """The public renderer exposes declared test exports lazily."""
        repository, _ = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-rendered",
            package_name="flext_rendered",
        )
        testing = repository / c.Infra.DIR_TESTS
        testing.mkdir()
        testing.joinpath("constants.py").write_text(
            "class TestsFlextRenderedConstants:\n"
            "    __all__ = ('TestsFlextRenderedConstants',)\n"
            "c = TestsFlextRenderedConstants\n",
            encoding=c.DEFAULT_ENCODING,
        )
        plan = m.Infra.LazyInitPlan(
            context=m.Infra.LazyInitPackageContext(
                pkg_dir=testing,
                init_path=testing / c.Infra.INIT_PY,
                current_pkg=c.Infra.DIR_TESTS,
                surface=c.Infra.DIR_TESTS,
                importable=True,
            ),
            action=c.Infra.LazyInitAction.WRITE,
            exports=("TestsFlextRenderedConstants", "c"),
            lazy_map={
                "TestsFlextRenderedConstants": (
                    "tests.constants",
                    "TestsFlextRenderedConstants",
                ),
                "c": ("tests.constants", "c"),
            },
            eager_dunders={},
        )
        source = FlextInfraCodegenGeneration.render_init(plan)
        testing.joinpath(c.Infra.INIT_PY).write_text(
            source, encoding=c.DEFAULT_ENCODING
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nimport tests as package\n"
                "print('tests.constants' not in sys.modules)\n"
                "from tests.constants import TestsFlextRenderedConstants\n"
                "print(package.c is TestsFlextRenderedConstants)\n"
                f"print(package.__all__ == {plan.exports!r})\n",
                python_paths=(str(repository),),
                cwd=repository,
            ),
            eq=["True", "True", "True"],
        )
        tm.that(FlextInfraCodegenGeneration.render_init(plan), eq=source)
        checked = FlextInfraRuffLintGate(repository).check_files(
            (plan.context.init_path,),
            repository,
            m.Infra.GateContext(
                repository_root=repository,
                reports_dir=repository,
                selected_files=(plan.context.init_path,),
            ),
        )
        tm.that(
            plan.context.init_path.read_text(encoding=c.DEFAULT_ENCODING), eq=source
        )
        tm.that(
            checked.result.passed,
            eq=True,
            msg=f"{plan.context.init_path}\n{source}\n{checked.raw_output}",
        )

    @staticmethod
    def _owner_sections(
        plan: m.Infra.LazyInitPlan,
        imports: t.MappingKV[str, t.StrPair],
    ) -> str:
        """Render the TYPE_CHECKING block the single first-party owner implies.

        Third-party imports, one blank line, then first-party imports, each
        alphabetical; the partition comes from the owner, never a literal.

        Returns:
            The expected ``if TYPE_CHECKING:`` block.

        """
        pyproject = next(
            candidate / c.PYPROJECT_FILENAME
            for candidate in (plan.context.pkg_dir, *plan.context.pkg_dir.parents)
            if (candidate / c.PYPROJECT_FILENAME).is_file()
        ).resolve()
        first_party = frozenset(
            FlextInfraToolTablesPhase.first_party_namespaces(path=pyproject.parent),
        )

        def block(*, owned: bool) -> str:
            return "".join(
                f"    from {module} import {attr} as {alias}\n"
                for alias, (module, attr) in sorted(imports.items())
                if (module in first_party) is owned
            )

        sections = [text for text in (block(owned=False), block(owned=True)) if text]
        return "if TYPE_CHECKING:\n" + "\n".join(sections)

    @staticmethod
    def _plan(
        current_pkg: str,
        exports: t.StrSequence,
        lazy_map: t.LazyAliasMap,
        *,
        eager_dunders: t.LazyAliasMap | None = None,
        package_dir: Path | None = None,
    ) -> m.Infra.LazyInitPlan:
        """Build one validated render plan for a synthetic package path.

        Returns:
            The resulting ``m.Infra.LazyInitPlan``.

        """
        package_dir = package_dir or Path.cwd() / current_pkg.replace(".", "/")
        return m.Infra.LazyInitPlan(
            context=m.Infra.LazyInitPackageContext(
                pkg_dir=package_dir,
                init_path=package_dir / c.Infra.INIT_PY,
                current_pkg=current_pkg,
                surface=current_pkg.split(".", maxsplit=1)[0],
                importable=True,
            ),
            action=c.Infra.LazyInitAction.WRITE,
            exports=exports,
            lazy_map=MappingProxyType(dict(lazy_map)),
            eager_dunders=MappingProxyType(dict(eager_dunders or {})),
            child_packages_for_lazy=(),
        )

    def test_root_initializer_is_the_lazy_ssot(self) -> None:
        """Public roots render one importable initializer with a literal ABI."""
        plan = self._plan(
            "demo_pkg",
            ("Demo", "r", "__version__"),
            MappingProxyType({
                "Demo": ("demo_pkg.api", "Demo"),
                "r": ("flext_core", "r"),
            }),
            eager_dunders=MappingProxyType({
                "__version__": ("demo_pkg.__version__", "__version__"),
            }),
        ).model_copy(update={"child_packages_for_lazy": ("demo_pkg.services",)})

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, lacks="_LAZY_MODULES")
        tm.that(content, lacks="_LAZY_ALIAS_GROUPS")
        # The installer publishes its normalized metadata; the projection
        # provides only the elected flat targets.
        tm.that(content, lacks="_LAZY_IMPORTS =")
        tm.that(content, contains="MappingProxyType(")
        tm.that(content, lacks="build_lazy_import_map(")
        tm.that(content, contains='"Demo": ".api"')
        tm.that(content, contains="from demo_pkg.__version__ import __version__\n")
        tm.that(
            content,
            contains='__all__: tuple[str, ...] = ("Demo", "__version__", "r")',
        )
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="    from demo_pkg.api import Demo")
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

    def test_export_width_is_a_real_formatter_fixed_point(self, tmp_path: Path) -> None:
        """The rendered tuple annotation owns the compact-line width budget."""
        names = ("FlextInfraCleanService", "FlextInfraPythonVersionEnforcer")
        plan = self._plan(
            "demo_pkg",
            names,
            {name: ("demo_pkg.owner", name) for name in names},
        )
        rendered = FlextInfraCodegenGeneration.render_init(plan)
        target = tmp_path / "__init__.py"
        target.write_text(rendered, encoding="utf-8")
        formatted = u.Cli.run([
            "ruff",
            "format",
            "--config",
            str(Path.cwd() / "pyproject.toml"),
            str(target),
        ])
        tm.that(formatted.success, truth=True, msg=formatted.error)
        tm.that(target.read_text(encoding="utf-8") == rendered, truth=True)

    @pytest.mark.parametrize("with_eager_version", [False, True])
    def test_singleton_lazy_map_survives_format_and_regeneration(
        self,
        tmp_path: Path,
        *,
        with_eager_version: bool,
    ) -> None:
        """A generated singleton map stays valid across formatter and lint gates."""
        export = "FlextCliProtocolsBase"
        package_name = u.Infra.project_package_name(Path.cwd())
        owner = f"{package_name}._protocols._base.flextcliprotocolsbase_part_05"
        eager = (
            {"__version__": (f"{package_name}.__version__", "__version__")}
            if with_eager_version
            else {}
        )
        plan = self._plan(
            package_name,
            (export, *eager),
            {export: (owner, export)},
            eager_dunders=eager,
        )
        rendered = FlextInfraCodegenGeneration.render_init(plan)
        target = tmp_path / "__init__.py"
        target.write_text(rendered, encoding="utf-8")
        project_config = str(Path.cwd() / "pyproject.toml")

        formatted = u.Cli.run([
            "ruff",
            "format",
            "--config",
            project_config,
            str(target),
        ])
        tm.that(formatted.success, truth=True, msg=formatted.error)
        tm.that(target.read_text(encoding="utf-8"), eq=rendered)

        checked = u.Cli.run([
            "ruff",
            "check",
            "--select",
            "I,COM812",
            "--config",
            project_config,
            str(target),
        ])
        tm.that(checked.success, truth=True, msg=checked.error)
        tm.that(FlextInfraCodegenGeneration.render_init(plan), eq=rendered)

    def test_sibling_private_exports_import_their_absolute_owner(self) -> None:
        """The static import names the absolute owner; the lazy key stays compact."""
        plan = self._plan(
            "demo_pkg.servers._rfc",
            ("BaseConstants",),
            {"BaseConstants": ("demo_pkg.servers._base.constants", "BaseConstants")},
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(
            content,
            has="from demo_pkg.servers._base.constants import BaseConstants",
        )
        tm.that(content, has='"BaseConstants": ".._base.constants"')
        tm.that(content, lacks="from .._base.constants import")

    @staticmethod
    def test_generated_runtime_surfaces_import_without_bootstrap_cycles() -> None:
        """Test generated runtime surfaces import without bootstrap cycles."""
        tm.that(flext_core.__all__, has="c")
        tm.that(dir(flext_core), has="c")
        tm.that(flext_core.c.__name__, eq="FlextConstants")
        tm.that(u.Infra.init_rope_project, none=False)

    @pytest.mark.parametrize(
        ("owner", "rendered_owner"),
        [
            ("demo_pkg.servers._base.constants", ".._base.constants"),
            ("demo_pkg._shared.constants", "..._shared.constants"),
            ("demo_pkg.servers", ".."),
            ("demo_pkg", "..."),
            ("demo_pkg.servers._rfc", "."),
            ("demo_pkg.servers._rfc.constants", ".constants"),
            (".._base.constants", ".._base.constants"),
            ("upstream_pkg.constants", "upstream_pkg.constants"),
        ],
    )
    def test_generated_imports_preserve_owner_resolution(
        self,
        owner: str,
        rendered_owner: str,
    ) -> None:
        """The static import names the compact lazy key's absolute owner."""
        package = "demo_pkg.servers._rfc"
        plan = self._plan(
            package,
            ("Demo",),
            MappingProxyType({"Demo": (owner, "Demo")}),
        )
        absolute_owner = resolve_name(owner, package)

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains=f"from {absolute_owner} import Demo")
        tm.that(content, contains=f'"Demo": "{rendered_owner}"')
        tm.that(resolve_name(rendered_owner, package), eq=absolute_owner)

    def test_root_initializer_contains_static_and_lazy_contracts(self) -> None:
        """Public root initializer keeps typing and runtime targets aligned."""
        plan = self._plan(
            "demo_pkg",
            ("Demo",),
            MappingProxyType({"Demo": ("demo_pkg.api", "Demo")}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="    from demo_pkg.api import Demo")
        runtime_prefix = content.split("if TYPE_CHECKING:", maxsplit=1)[0]
        tm.that(runtime_prefix, lacks="from demo_pkg.api import Demo")
        tm.that(content, contains='"Demo": ".api"')
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

    def test_nested_package_initializer_is_static(self, tmp_path: Path) -> None:
        """A loader dependency statically publishes its declared class identity."""
        content = self._bootstrap_content(
            tmp_path,
            "flext_core._lazy_parts",
            "flext_core._lazy_parts.flextlazy_part_02",
            "FlextLazy",
        )
        tm.that(content, lacks="from flext_core.lazy import")
        tm.that(content, contains='__all__: tuple[str, ...] = ("FlextLazy",)')

    def test_root_initializer_rejects_private_entries_outside_all(self) -> None:
        """Render no package attribute that is absent from the public contract."""
        plan = self._plan(
            "demo_pkg",
            ("Demo",),
            MappingProxyType({
                "Demo": ("demo_pkg.api", "Demo"),
                "DemoConversion": ("demo_pkg._utilities.conversion", "DemoConversion"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(
            content,
            lacks="from demo_pkg._utilities.conversion import DemoConversion",
        )
        tm.that(content, lacks="DemoConversion")
        tm.that(content, contains='__all__: tuple[str, ...] = ("Demo",)')

    def test_root_type_checking_imports_local_declarations_absolutely(self) -> None:
        """Emit local declarations as absolute public re-exports."""
        plan = self._plan(
            "flext_cli",
            ("FlextCliSettings", "settings"),
            MappingProxyType({
                "FlextCliSettings": ("flext_cli._settings", "FlextCliSettings"),
                "settings": ("flext_cli._settings", "settings"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(
            content,
            contains="from flext_cli._settings import FlextCliSettings, settings",
        )
        tm.that(content, lacks="from ._settings import")
        tm.that(content, lacks="    _ = (")

    @pytest.mark.parametrize("current_pkg", ["demo_pkg", "demo_pkg.services"])
    def test_public_nested_package_preserves_lazy_exports(
        self, current_pkg: str, tmp_path: Path
    ) -> None:
        """Rendered package exports resolve lazily to their declared objects."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-rendered",
            package_name="demo_pkg",
        )
        package_dir = package.joinpath(*current_pkg.split(".")[1:])
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "nested").mkdir()
        (package_dir / "demo.py").write_text(
            "class Demo: pass\n", encoding=c.DEFAULT_ENCODING
        )
        (package_dir / "nested" / "item.py").write_text(
            "class Nested: pass\n", encoding=c.DEFAULT_ENCODING
        )
        plan = self._plan(
            current_pkg,
            ("Demo", "Nested"),
            MappingProxyType({
                "Demo": (f"{current_pkg}.demo", "Demo"),
                "Nested": (f"{current_pkg}.nested.item", "Nested"),
            }),
            package_dir=package_dir,
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        plan.context.init_path.write_text(init_content, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import sys\nimport {current_pkg} as package\n"
                f"print('{current_pkg}.demo' not in sys.modules and "
                f"'{current_pkg}.nested.item' not in sys.modules)\n"
                f"from {current_pkg}.demo import Demo\n"
                f"from {current_pkg}.nested.item import Nested\n"
                "print(package.Demo is Demo and package.Nested is Nested)\n"
                f"print(package.__all__ == {plan.exports!r})\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["True", "True", "True"],
        )

    def test_private_fixture_package_initializer_is_side_effect_free(self) -> None:
        """Keep pytest plugin siblings unloaded until pytest registers them."""
        plan = self._plan(
            "demo_pkg._fixtures",
            ("DemoFixture",),
            MappingProxyType({
                "DemoFixture": ("demo_pkg._fixtures.settings", "DemoFixture"),
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(
            init_content,
            contains="from demo_pkg._fixtures.settings import DemoFixture",
        )
        tm.that(init_content, contains='__all__: tuple[str, ...] = ("DemoFixture",)')
        tm.that(init_content, contains="install_lazy_exports")

    def test_lazy_bootstrap_package_initializer_is_side_effect_free(
        self, tmp_path: Path
    ) -> None:
        """Keep the lazy runtime importable while its implementation initializes."""
        self._bootstrap_content(
            tmp_path,
            "flext_core._lazy_parts",
            "flext_core._lazy_parts.flextlazy_part_02",
            "FlextLazy",
        )

    def test_lazy_typings_bootstrap_initializer_is_side_effect_free(
        self, tmp_path: Path
    ) -> None:
        """Keep the lazy runtime's typing dependency free of import callbacks."""
        self._bootstrap_content(
            tmp_path,
            "flext_core._typings",
            "flext_core._typings.lazy",
            "FlextTypesLazy",
        )

    def test_tests_root_renders_only_its_facade_contract(self, tmp_path: Path) -> None:
        """Render test facades without importing collected test classes."""
        repository, _ = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-rendered", package_name="flext_rendered"
        )
        testing = repository / "tests"
        testing.mkdir()
        plan = self._plan(
            "tests",
            (
                "TestsDemoConstants",
                "TestsDemoModels",
                "TestsDemoProtocols",
                "TestsDemoServiceBase",
                "TestsDemoSettings",
                "TestsDemoTypes",
                "TestsDemoUtilities",
                "c",
                "m",
                "p",
                "s",
                "t",
                "tm",
                "u",
            ),
            MappingProxyType({
                "TestsDemoCase": ("tests.unit.test_demo", "TestsDemoCase"),
                "TestsDemoConstants": ("tests.constants", "TestsDemoConstants"),
                "TestsDemoModels": ("tests.models", "TestsDemoModels"),
                "TestsDemoProtocols": ("tests.protocols", "TestsDemoProtocols"),
                "TestsDemoServiceBase": ("tests.base", "TestsDemoServiceBase"),
                "TestsDemoSettings": ("tests.settings", "TestsDemoSettings"),
                "TestsDemoTypes": ("tests.typings", "TestsDemoTypes"),
                "TestsDemoUtilities": ("tests.utilities", "TestsDemoUtilities"),
                "c": ("tests.constants", "c"),
                "m": ("tests.models", "m"),
                "p": ("tests.protocols", "p"),
                "s": ("tests.base", "s"),
                "t": ("tests.typings", "t"),
                "tm": ("flext_tests", "tm"),
                "u": ("tests.utilities", "u"),
            }),
            package_dir=testing,
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)
        for module in {owner for owner, _ in plan.lazy_map.values()}:
            if module.startswith("tests.") and ".unit." not in module:
                (testing / f"{module.rpartition('.')[2]}.py").write_text(
                    "\n".join(
                        f"{name} = {name!r}"
                        for owner, name in plan.lazy_map.values()
                        if owner == module
                    ),
                    encoding=c.DEFAULT_ENCODING,
                )
        plan.context.init_path.write_text(init_content, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nfrom importlib import import_module\n"
                "import tests as package\nfrom flext_tests import tm\n"
                f"bindings = {dict(plan.lazy_map)!r}\n"
                f"exports = {plan.exports!r}\n"
                "print(package.__all__ == exports)\n"
                "print(all(getattr(package, name) is "
                "getattr(import_module(bindings[name][0]), bindings[name][1]) "
                "for name in exports))\n"
                "print(package.tm is tm and 'TestsDemoCase' not in dir(package) "
                "and 'tests.unit.test_demo' not in sys.modules)\n",
                python_paths=(str(repository),),
                cwd=repository,
            ),
            eq=["True", "True", "True"],
        )

    def test_root_type_checking_imports_the_declared_letter(self) -> None:
        """Static imports name the letter the facade module declares."""
        plan = self._plan(
            "demo_pkg",
            ("FlextDemoProtocols", "p"),
            MappingProxyType({
                "FlextDemoProtocols": ("demo_pkg.protocols", "FlextDemoProtocols"),
                "p": ("demo_pkg.protocols", "p"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(
            content,
            contains="from demo_pkg.protocols import FlextDemoProtocols, p",
        )
        tm.that(content, lacks="FlextDemoProtocols as p")

    def test_root_service_letter_is_the_declared_service_letter(self) -> None:
        """The service letter is imported as the base module declares it."""
        plan = self._plan(
            "demo_pkg",
            ("FlextDemoServiceBase", "s"),
            MappingProxyType({
                "FlextDemoServiceBase": ("demo_pkg.base", "FlextDemoServiceBase"),
                "s": ("demo_pkg.base", "s"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from demo_pkg.base import FlextDemoServiceBase, s")
        tm.that(content, lacks="FlextDemoServiceBase as s")

    @staticmethod
    def test_type_checking_renderer_keeps_declared_letters() -> None:
        """Static imports keep each letter under the name its module declares."""
        lines = FlextInfraCodegenGeneration.generate_type_checking({
            "module": [("c", "c"), ("m", "m")],
        })

        tm.that(
            "\n".join(lines),
            contains=(
                "if TYPE_CHECKING:\n"
                "    from flext_core import FlextTypes\n"
                "    from module import c, m"
            ),
        )

    def test_root_type_checking_sections_follow_known_first_party_policy(self) -> None:
        """The TYPE_CHECKING block mirrors the first-party owner's sections.

        The generated block follows the project's ruff isort sections as the
        single first-party owner derives them: third-party imports, then the
        blank line ruff requires (I001), then first-party imports.
        """
        imports = {"cli_c": ("flext_cli", "c"), "core_d": ("flext_core", "d")}
        plan = self._plan("demo_pkg", tuple(imports), MappingProxyType(imports))

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains=self._owner_sections(plan, imports))

    def test_root_type_checking_keeps_the_project_package_first_party(self) -> None:
        """Roots outside the source tree import the project package first-party.

        ``examples``/``scripts`` initializers import the distribution package
        absolutely; the single first-party owner decides each import's
        section, so the rendered block is the owner's partition: third-party
        imports, one blank line, then first-party imports.
        """
        imports = {
            "cli_c": ("flext_cli", "c"),
            "core_d": ("flext_core", "d"),
            "project_p": ("flext_infra", "p"),
        }
        plan = self._plan("demo_root", tuple(imports), MappingProxyType(imports))

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains=self._owner_sections(plan, imports))

    @staticmethod
    def test_project_package_name_reads_manifest_not_directory_name(
        tmp_path: Path,
    ) -> None:
        """Worktree checkouts keep the project's own package first-party.

        A project root directory named after a git branch (``0.12.0-dev``)
        must not leak into isort sectioning: the first-party package is the
        project's live ``src`` package (the single first-party owner), never
        proxied from the directory name, so a wrapper root renders the project
        import in the first-party section below the third-party block.
        """
        project_root = tmp_path / "0.12.0-dev"
        wrapper_root = project_root / "examples"
        wrapper_root.mkdir(parents=True)
        project_package = project_root / "src" / "demo_worktree_pkg"
        project_package.mkdir(parents=True)
        (project_package / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        (project_root / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "demo-worktree-pkg"\nversion = "1.0.0"\n'
            f'license = "{u.Tests.project_spec("demo-worktree-pkg").license}"\n'
            'authors = [{ name = "Fixture Author" }]\n',
            encoding="utf-8",
        )
        # A FLEXT project is a Git repository; workspace detection reads it.
        u.Tests.initialize_git_repo(project_root)
        plan = m.Infra.LazyInitPlan(
            context=m.Infra.LazyInitPackageContext(
                pkg_dir=wrapper_root,
                init_path=wrapper_root / c.Infra.INIT_PY,
                current_pkg="examples",
                surface="examples",
                importable=True,
            ),
            action=c.Infra.LazyInitAction.WRITE,
            exports=("cli_c", "project_p"),
            lazy_map=MappingProxyType({
                "cli_c": ("flext_cli", "c"),
                "project_p": ("demo_worktree_pkg", "p"),
            }),
            eager_dunders=MappingProxyType({}),
            child_packages_for_lazy=(),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(
            init_content,
            contains=(
                "if TYPE_CHECKING:\n"
                "    from flext_cli import c as cli_c\n"
                "\n"
                "    from demo_worktree_pkg import p as project_p\n"
            ),
        )

    @pytest.mark.parametrize("declared_empty", [False, True])
    def test_first_party_is_the_live_package_set_whatever_the_declared_table(
        self,
        tmp_path: Path,
        *,
        declared_empty: bool,
    ) -> None:
        """A declared first-party table never varies the derived sections.

        The single first-party owner derives the live ``src`` packages; an
        explicit empty list and an absent table render the same sections.
        """
        additional = tmp_path / "src" / "fixture_extra_namespace"
        additional.mkdir(parents=True)
        (additional / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        wrapper = tmp_path / "examples"
        wrapper.mkdir()
        table = (
            "[tool.ruff.lint.isort]\nknown-first-party = []\n" if declared_empty else ""
        )
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            f'[project]\nname = "configured-workspace"\nversion = "1.0.0"\n'
            f'license = "{u.Tests.project_spec("configured-workspace").license}"\n'
            f'authors = [{{ name = "Fixture Author" }}]\n{table}',
            encoding="utf-8",
        )
        # A FLEXT project is a Git repository; workspace detection reads it.
        u.Tests.initialize_git_repo(tmp_path)
        plan = self._plan(
            "examples",
            ("extra", "external"),
            MappingProxyType({
                "extra": ("fixture_extra_namespace", "value"),
                "external": ("zz_external_fixture", "value"),
            }),
        )
        plan = plan.model_copy(
            update={
                "context": plan.context.model_copy(
                    update={"pkg_dir": wrapper, "init_path": wrapper / c.Infra.INIT_PY},
                ),
            },
        )
        rendered = FlextInfraCodegenGeneration.render_init(plan)
        expected = (
            "    from zz_external_fixture import value as external\n\n"
            "    from fixture_extra_namespace import value as extra\n"
        )
        tm.that(rendered, has=expected)

    @pytest.mark.parametrize("planned_helpers", [False, True])
    def test_runtime_imports_are_one_isort_section_with_the_lazy_helpers(
        self, *, planned_helpers: bool
    ) -> None:
        """The helpers import sorts inside the first-party block it belongs to.

        In the bootstrap root the helpers live in a sibling module of the
        ``__version__`` import; both are first-party, so Ruff isort keeps them
        in one block ordered by module. A separate helpers block was rewritten
        by ``make fix`` after every ``make gen``.
        """
        root = c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE
        helper_targets = (
            {
                name: (c.Infra.LAZY_BOOTSTRAP_MODULE, name)
                for name in c.Infra.LAZY_BOOTSTRAP_HELPERS
            }
            if planned_helpers
            else {}
        )
        plan = self._plan(
            root,
            ("FlextLazy", "__version__", *helper_targets),
            MappingProxyType({
                "FlextLazy": (c.Infra.LAZY_BOOTSTRAP_MODULE, "FlextLazy"),
                **helper_targets,
            }),
            eager_dunders=MappingProxyType({
                "__version__": (f"{root}.__version__", "__version__"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        helpers = ", ".join(c.Infra.LAZY_BOOTSTRAP_HELPERS)
        tm.that(
            content,
            contains=(
                f"from {root}.__version__ import __version__\n"
                f"from {c.Infra.LAZY_BOOTSTRAP_MODULE} import {helpers}\n"
            ),
        )
        tm.that(content, lacks=f"from {root} import")
        published = u.Infra.public_export_names_source(content)
        for helper in c.Infra.LAZY_BOOTSTRAP_HELPERS:
            tm.that(published, has=helper)
            tm.that(content, lacks=f'"{helper}":')

    def test_expanded_single_entry_mapping_keeps_its_trailing_comma(self) -> None:
        """An exploded one-entry mapping carries the comma COM812 requires.

        Derive the long target from the configured width rather than freezing
        today's compact-versus-expanded boundary.
        """
        width = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        module = "demo_pkg." + "owner" * (
            (width - len("    from demo_pkg. import (")) // len("owner")
        )
        plan = self._plan(
            "demo_pkg",
            ("FlextDemoGeneratedFacade",),
            MappingProxyType({
                "FlextDemoGeneratedFacade": (
                    module,
                    "PublishedFacade",
                ),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        tm.that(
            content,
            contains='            "PublishedFacade",\n        ),\n    }),',
        )
