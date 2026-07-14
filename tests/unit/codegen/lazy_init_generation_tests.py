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
        tm.that(content, contains='".services"')
        tm.that(content, contains='".api": (')
        tm.that(content, contains='        "Demo",')
        tm.that(content, contains="__all__: tuple[str, ...] =")
        tm.that(content, contains='    "__version__",')
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, lacks="__unit__")

    def test_internal_package_uses_explicit_sibling_reexports(
        self, tmp_path: Path
    ) -> None:
        """Internal packages publish direct sibling symbols statically."""
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
        tm.that(content, contains="from .demo import Demo as Demo")
        tm.that(content, contains='    "Demo",')
        tm.that(content, lacks="Nested")
        tm.that(content, lacks="import nested")
        tm.that(content, lacks="install_lazy_exports")

    def test_non_public_root_uses_explicit_static_reexports(
        self, tmp_path: Path
    ) -> None:
        """Tests, examples, and scripts use the static internal contract."""
        plan = self._plan(
            tmp_path,
            "tests",
            ("TestsDemo",),
            MappingProxyType({"TestsDemo": ("tests.demo", "TestsDemo")}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains="from .demo import TestsDemo as TestsDemo")
        tm.that(content, contains='    "TestsDemo",')
        tm.that(content, lacks="install_lazy_exports")

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
        tm.that(
            content, contains="from .models import FlextDemoModels as FlextDemoModels"
        )
        tm.that(content, contains='    "FlextDemoModels",')
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
