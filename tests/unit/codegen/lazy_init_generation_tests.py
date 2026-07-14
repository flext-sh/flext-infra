"""Public contract tests for canonical lazy-init artifact rendering."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from flext_tests import tm

from flext_infra import c, m, t
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


# mro-pulj (Codex): tests assert the lazy-root/empty-child contract.
class TestsFlextInfraCodegenGeneration:
    """Validate observable generated Python artifacts without legacy internals."""

    @staticmethod
    def _plan(
        current_pkg: str,
        exports: t.StrSequence,
        lazy_map: t.LazyAliasMap,
        *,
        eager_dunders: t.LazyAliasMap | None = None,
        child_packages: t.StrSequence = (),
    ) -> m.Infra.LazyInitPlan:
        """Build one validated render plan for a synthetic package path."""
        package_dir = Path.cwd() / current_pkg.replace(".", "/")
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
                "__version__": ("demo_pkg.__version__", "__version__")
            }),
            child_packages=("demo_pkg.services",),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="_LAZY_MODULES")
        tm.that(content, contains="_LAZY_ALIAS_GROUPS")
        tm.that(content, contains='".api": ("Demo",)')
        direct_imports = content.split(
            "_DIRECT_IMPORTS: tuple[str, ...] =", maxsplit=1
        )[1].split("__all__:", maxsplit=1)[0]
        tm.that(direct_imports, contains='"__version__"')
        tm.that(
            content, contains='__all__: tuple[str, ...] = ("Demo", "__version__", "r")'
        )
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

    def test_root_initializer_contains_static_and_lazy_contracts(self) -> None:
        """Public root initializer keeps typing and runtime targets aligned."""
        plan = self._plan(
            "demo_pkg", ("Demo",), MappingProxyType({"Demo": ("demo_pkg.api", "Demo")})
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .api import Demo")
        tm.that(content, contains='".api": ("Demo",)')
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

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
        tm.that(content, lacks="from ._utilities.conversion import DemoConversion")
        tm.that(content, lacks="DemoConversion")
        tm.that(content, contains="_DIRECT_IMPORTS: tuple[str, ...]")

    def test_root_type_checking_uses_compact_relative_local_imports(self) -> None:
        """Emit local declarations relatively without identity aliases."""
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
        tm.that(content, contains="from ._settings import FlextCliSettings, settings")
        tm.that(content, lacks="from flext_cli._settings import")
        tm.that(content, lacks="FlextCliSettings as FlextCliSettings")
        tm.that(content, lacks="settings as settings")
        tm.that(content, contains="_ = (FlextCliSettings, settings)")

    def test_non_root_package_uses_empty_initializer(self) -> None:
        """Subpackages never publish implementation classes or import siblings."""
        plan = self._plan(
            "demo_pkg.services",
            ("Demo", "Nested"),
            MappingProxyType({
                "Demo": ("demo_pkg.services.demo", "Demo"),
                "Nested": ("demo_pkg.services.nested.item", "Nested"),
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, lacks="from .demo import Demo")
        tm.that(init_content, contains="__all__: tuple[str, ...] = ()")
        tm.that(init_content, lacks="Demo")
        tm.that(init_content, lacks="Nested")
        tm.that(init_content, lacks="install_lazy_exports")

    def test_private_fixture_package_initializer_is_side_effect_free(self) -> None:
        """Keep pytest plugin siblings unloaded until pytest registers them."""
        plan = self._plan(
            "demo_pkg._fixtures",
            ("DemoFixture",),
            MappingProxyType({
                "DemoFixture": ("demo_pkg._fixtures.settings", "DemoFixture")
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, lacks="from .settings import")
        tm.that(init_content, contains="__all__: tuple[str, ...] = ()")
        tm.that(init_content, lacks="install_lazy_exports")

    def test_non_public_surface_uses_empty_initializer(self) -> None:
        """Tests, examples, and scripts remain side-effect-free namespaces."""
        plan = self._plan(
            "tests",
            ("TestsDemo",),
            MappingProxyType({"TestsDemo": ("tests.demo", "TestsDemo")}),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, lacks="from .demo import TestsDemo")
        tm.that(init_content, lacks="TestsDemo")
        tm.that(init_content, contains="__all__: tuple[str, ...] = ()")
        tm.that(init_content, lacks="install_lazy_exports")

    def test_root_type_checking_alias_uses_named_local_facade(self) -> None:
        """Static analyzers receive the local facade class behind short aliases."""
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
        tm.that(content, contains="FlextDemoProtocols as p")
        tm.that(content, lacks="p")

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
