"""Public contract tests for canonical lazy-init artifact rendering."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from flext_tests import tm

from flext_infra import c, m, t
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


# mro-wkii.17 (Codex): tests assert the inline lazy-root/static-child contract.
class TestsFlextInfraCodegenGeneration:
    """Validate observable generated Python artifacts without legacy internals."""

    @staticmethod
    def _plan(
        workspace_root: Path,
        current_pkg: str,
        exports: t.StrSequence,
        lazy_map: t.LazyAliasMap,
        *,
        eager_dunders: t.LazyAliasMap | None = None,
        child_packages: t.StrSequence = (),
    ) -> m.Infra.LazyInitPlan:
        """Build one validated render plan for a synthetic package path."""
        package_dir = workspace_root / current_pkg.replace(".", "/")
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
            type_checking_map=MappingProxyType(dict(lazy_map)),
            eager_dunders=MappingProxyType(dict(eager_dunders or {})),
            child_packages_for_lazy=child_packages,
            excluded_lazy_names=("internal_only",),
        )

    def test_public_root_initializer_is_the_lazy_ssot(self, tmp_path: Path) -> None:
        """Public roots render one inline lazy map with a literal ABI."""
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("Demo", "r", "__version__"),
            MappingProxyType({
                "Demo": ("demo_pkg.api", "Demo"),
                "r": ("flext_core", "r"),
            }),
            eager_dunders=MappingProxyType({
                "__version__": ("demo_pkg.__version__", "__version__")
            }),
            child_packages=("demo_pkg.services",),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="_LAZY_MODULES")
        tm.that(content, contains="_LAZY_ALIAS_GROUPS")
        # mro-wkii.17.26 (codex): child metadata never invents a root ABI binding.
        tm.that(content, lacks='".services"')
        tm.that(content, contains='".api": ("Demo",)')
        public_exports = content.split("__all__: tuple[str, ...] =", maxsplit=1)[
            1
        ].split("_install_lazy_exports", maxsplit=1)[0]
        tm.that(public_exports, contains='"Demo"')
        tm.that(public_exports, contains='"__version__"')
        tm.that(public_exports, contains='"r"')
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="install_lazy_exports as _install_lazy_exports")
        tm.that(content, contains="_install_lazy_exports(")
        tm.that(content, lacks="_DIRECT_IMPORTS")
        tm.that(content, lacks="__unit__")

    def test_internal_package_uses_explicit_sibling_reexports(
        self, tmp_path: Path
    ) -> None:
        """Internal packages publish direct sibling symbols statically."""
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("Demo",),
            MappingProxyType({"Demo": ("demo_pkg.api", "Demo")}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .api import Demo")
        tm.that(content, contains='".api": ("Demo",)')
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

    def test_root_initializer_renders_the_filtered_public_plan(
        self, tmp_path: Path
    ) -> None:
        """Render only the public map supplied by the planner."""
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("Demo",),
            MappingProxyType({"Demo": ("demo_pkg.api", "Demo")}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)
        public_exports = content.split("__all__: tuple[str, ...] =", maxsplit=1)[
            1
        ].split("_install_lazy_exports", maxsplit=1)[0]

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .api import Demo")
        tm.that(content, lacks="_DIRECT_IMPORTS")
        tm.that(content, lacks='"DemoConversion"')
        tm.that(public_exports, contains='"Demo"')

    def test_root_renderer_preserves_runtime_and_typing_plan_parity(
        self, tmp_path: Path
    ) -> None:
        """Render every planner-owned public name in both ABI projections."""
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("build_lazy_import_map",),
            MappingProxyType({
                "build_lazy_import_map": ("demo_pkg.api", "build_lazy_import_map")
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)
        public_exports = content.split("__all__: tuple[str, ...] =", maxsplit=1)[
            1
        ].split("_install_lazy_exports", maxsplit=1)[0]
        type_checking_block = content.split("if TYPE_CHECKING:", maxsplit=1)[1].split(
            "_LAZY_MODULES", maxsplit=1
        )[0]

        compile(content, "__init__.py", "exec")
        tm.that(content, contains='".api": ("build_lazy_import_map",)')
        tm.that(public_exports, contains='"build_lazy_import_map"')
        tm.that(type_checking_block, contains="from .api import build_lazy_import_map")

    def test_root_type_checking_uses_compact_relative_local_imports(
        self, tmp_path: Path
    ) -> None:
        """Emit local declarations relatively without identity aliases."""
        plan = self._plan(
            tmp_path,
            "flext_cli",
            ("FlextCliSettings", "settings"),
            MappingProxyType({
                "FlextCliSettings": ("flext_cli._settings", "FlextCliSettings"),
                "settings": ("flext_cli._settings", "settings"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from ._settings import FlextCliSettings, settings")
        tm.that(content, lacks="from flext_cli._settings import")
        tm.that(content, lacks="FlextCliSettings as FlextCliSettings")
        tm.that(content, lacks="settings as settings")
        type_checking_block = content.split("if TYPE_CHECKING:", maxsplit=1)[1].split(
            "_LAZY_MODULES", maxsplit=1
        )[0]
        tm.that(type_checking_block, contains="FlextCliSettings")
        tm.that(type_checking_block, contains="settings")

    def test_non_root_package_uses_static_initializer(self, tmp_path: Path) -> None:
        """Subpackages publish direct siblings through explicit imports."""
        plan = self._plan(
            tmp_path,
            "demo_pkg.services",
            ("Demo", "Nested", "nested"),
            MappingProxyType({
                "Demo": ("demo_pkg.services.demo", "Demo"),
                "Nested": ("demo_pkg.services.nested.item", "Nested"),
                "nested": ("demo_pkg.services.nested", ""),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .demo import Demo")
        tm.that(content, lacks="Demo as Demo")
        tm.that(content, contains='__all__: tuple[str, ...] = ("Demo",)')
        tm.that(content, lacks="Nested")
        tm.that(content, lacks="import nested")
        tm.that(content, lacks="install_lazy_exports")

    def test_static_renderer_honors_explicit_plan_exports(self, tmp_path: Path) -> None:
        """Render the typed plan without re-deriving package-name policy."""
        plan = self._plan(
            tmp_path,
            "demo_pkg._fixtures",
            ("DemoFixture",),
            MappingProxyType({
                "DemoFixture": ("demo_pkg._fixtures.settings", "DemoFixture")
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains="from .settings import DemoFixture")
        tm.that(init_content, contains='__all__: tuple[str, ...] = ("DemoFixture",)')
        tm.that(init_content, lacks="install_lazy_exports")

    def test_non_public_surface_uses_static_initializer(self, tmp_path: Path) -> None:
        """Tests, examples, and scripts use explicit static exports."""
        plan = self._plan(
            tmp_path,
            "tests",
            ("TestsDemo", "r"),
            MappingProxyType({
                "TestsDemo": ("tests.demo", "TestsDemo"),
                "r": ("flext_tests", "r"),
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains="from .demo import TestsDemo")
        tm.that(init_content, contains="from flext_tests import r\n\nfrom .demo")
        tm.that(init_content, lacks="TestsDemo as TestsDemo")
        tm.that(init_content, contains='    "TestsDemo",')
        tm.that(init_content, contains='    "r",')
        tm.that(init_content, lacks="install_lazy_exports")

    def test_root_type_checking_alias_uses_named_local_facade(
        self, tmp_path: Path
    ) -> None:
        """Static analyzers receive the local facade class behind short aliases."""
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("FlextDemoProtocols", "p"),
            MappingProxyType({
                "FlextDemoProtocols": ("demo_pkg.protocols", "FlextDemoProtocols"),
                "p": ("demo_pkg.protocols", "p"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="FlextDemoProtocols as p")
        tm.that(content, lacks="p as p")

    def test_private_internal_package_is_not_empty(self, tmp_path: Path) -> None:
        """Private packages use the same explicit static contract."""
        plan = self._plan(
            tmp_path,
            "demo_pkg._models",
            ("FlextDemoModels",),
            MappingProxyType({
                "FlextDemoModels": ("demo_pkg._models.models", "FlextDemoModels")
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .models import FlextDemoModels")
        tm.that(content, lacks="FlextDemoModels as FlextDemoModels")
        tm.that(content, contains='__all__: tuple[str, ...] = ("FlextDemoModels",)')
        tm.that(content, lacks="install_lazy_exports")

    def test_type_checking_renderer_keeps_explicit_aliases(self) -> None:
        """Static imports preserve facade aliases explicitly."""
        lines = FlextInfraCodegenGeneration.generate_type_checking({
            "module": [("c", "FlextConstants"), ("m", "FlextModels")]
        })

        tm.that(
            "\n".join(lines),
            contains="from module import FlextConstants as c, FlextModels as m",
        )


__all__: list[str] = ["TestsFlextInfraCodegenGeneration"]
