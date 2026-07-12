"""Public contract tests for canonical lazy-init artifact rendering."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from flext_tests import tm

from flext_infra import c, m, t
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


# mro-i6nq.10: Tests assert only the new manifest/root-thin/eager public contract.
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
        package_dir = Path("/tmp") / current_pkg.replace(".", "/")
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

    def test_root_manifest_is_the_lazy_ssot(self) -> None:
        """Public roots render one importable manifest with a literal ABI."""
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
            child_packages=("demo_pkg.services",),
        )

        content = FlextInfraCodegenGeneration.render_unit_manifest(plan)

        tm.that(content is not None, eq=True)
        assert content is not None
        compile(content, "__unit__.py", "exec")
        tm.that(content, contains="LAZY_MODULES")
        tm.that(content, contains="LAZY_ALIAS_GROUPS")
        tm.that(content, contains='".services"')
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains='    "__version__",')
        tm.that(content, lacks="install_lazy_exports")

    def test_root_initializer_consumes_only_manifest_data(self) -> None:
        """Public root initializer imports manifest data and installs lazy access."""
        plan = self._plan(
            "demo_pkg",
            ("Demo",),
            MappingProxyType({"Demo": ("demo_pkg.api", "Demo")}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from demo_pkg.__unit__ import __all__ as __all__")
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="LAZY_MODULES: dict")
        tm.that(content, lacks="PUBLIC_EXPORTS")

    def test_non_root_initializer_is_eager_and_sibling_only(self) -> None:
        """Subpackages import sibling symbols eagerly and publish a literal ABI."""
        plan = self._plan(
            "demo_pkg.services",
            ("Demo", "Nested"),
            MappingProxyType({
                "Demo": ("demo_pkg.services.demo", "Demo"),
                "Nested": ("demo_pkg.services.nested.item", "Nested"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from demo_pkg.services.demo import Demo")
        tm.that(content, contains='    "Demo",')
        tm.that(content, lacks="Nested")
        tm.that(content, lacks="flext_core.lazy")
        tm.that(content, lacks="TYPE_CHECKING")
        tm.that(content, lacks="__unit__")

    def test_non_public_surface_root_uses_eager_contract(self) -> None:
        """Tests/examples/scripts roots never receive public lazy machinery."""
        plan = self._plan(
            "tests",
            ("TestsDemo",),
            MappingProxyType({"TestsDemo": ("tests.demo", "TestsDemo")}),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)
        unit_content = FlextInfraCodegenGeneration.render_unit_manifest(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains="from tests.demo import TestsDemo")
        tm.that(init_content, lacks="install_lazy_exports")
        tm.that(unit_content is None, eq=True)

    def test_type_checking_renderer_keeps_explicit_aliases(self) -> None:
        """Static imports preserve facade aliases explicitly."""
        lines = FlextInfraCodegenGeneration.generate_type_checking({
            "module": [("c", "FlextConstants"), ("m", "FlextModels")],
        })

        tm.that(
            "\n".join(lines),
            contains="from module import FlextConstants as c, FlextModels as m",
        )


__all__: list[str] = ["TestsFlextInfraCodegenGeneration"]
