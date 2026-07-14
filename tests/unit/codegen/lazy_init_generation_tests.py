"""Public contract tests for canonical lazy-init artifact rendering."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from flext_tests import tm

from flext_infra import c, m, t
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


# mro-i6nq.10: Tests assert the single manifest-backed thin-init contract.
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
                "__version__": ("demo_pkg.__version__", "__version__")
            }),
            child_packages=("demo_pkg.services",),
        )

        content = FlextInfraCodegenGeneration.render_unit_manifest(plan)

        compile(content, "__unit__.py", "exec")
        tm.that(content, contains="LAZY_MODULES")
        tm.that(content, contains="LAZY_ALIAS_GROUPS")
        tm.that(content, contains='".services"')
        tm.that(content, contains='".api": (')
        tm.that(content, contains='        "Demo",')
        tm.that(content, contains="PUBLIC_EXPORTS: tuple[str, ...] =")
        tm.that(content, lacks="TYPE_CHECKING")
        tm.that(content, contains='    "__version__",')
        tm.that(content, lacks="install_lazy_exports")

    def test_root_initializer_consumes_only_manifest_data(self) -> None:
        """Public root initializer imports manifest data and installs lazy access."""
        plan = self._plan(
            "demo_pkg", ("Demo",), MappingProxyType({"Demo": ("demo_pkg.api", "Demo")})
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from demo_pkg.__unit__ import (")
        tm.that(content, contains="PUBLIC_EXPORTS as _PUBLIC_EXPORTS,")
        tm.that(content, contains="__all__: tuple[str, ...]")
        tm.that(content, contains="public_exports=_PUBLIC_EXPORTS")
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="LAZY_MODULES: dict")

    def test_non_root_package_uses_manifest_and_thin_initializer(self) -> None:
        """Subpackages publish all symbols through a cycle-safe manifest."""
        plan = self._plan(
            "demo_pkg.services",
            ("Demo", "Nested"),
            MappingProxyType({
                "Demo": ("demo_pkg.services.demo", "Demo"),
                "Nested": ("demo_pkg.services.nested.item", "Nested"),
            }),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)
        unit_content = FlextInfraCodegenGeneration.render_unit_manifest(plan)

        compile(init_content, "__init__.py", "exec")
        compile(unit_content, "__unit__.py", "exec")
        tm.that(init_content, contains="from demo_pkg.services.__unit__ import (")
        tm.that(init_content, contains="install_lazy_exports(")
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(runtime_content, lacks="from demo_pkg.services.demo import Demo")
        tm.that(unit_content, contains='".demo": (')
        tm.that(unit_content, contains='        "Demo",')
        tm.that(unit_content, contains='".nested.item": (')
        tm.that(unit_content, contains='        "Nested",')

    def test_non_public_surface_uses_manifest_and_thin_initializer(self) -> None:
        """Tests, examples, and scripts use the same cycle-safe contract."""
        plan = self._plan(
            "tests",
            ("TestsDemo",),
            MappingProxyType({"TestsDemo": ("tests.demo", "TestsDemo")}),
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)
        unit_content = FlextInfraCodegenGeneration.render_unit_manifest(plan)

        compile(init_content, "__init__.py", "exec")
        compile(unit_content, "__unit__.py", "exec")
        tm.that(init_content, contains="from tests.__unit__ import (")
        tm.that(init_content, contains="install_lazy_exports(")
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(runtime_content, lacks="from tests.demo import TestsDemo")
        tm.that(unit_content, contains='".demo": (')
        tm.that(unit_content, contains='        "TestsDemo",')

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
