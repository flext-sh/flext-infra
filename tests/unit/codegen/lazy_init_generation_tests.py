"""Public contract tests for canonical lazy-init artifact rendering.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from flext_tests import tm

from flext_infra import c, m, p, t
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


# mro-pulj (Codex): tests assert the lazy-root/empty-child contract.
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
        production: bool = True,
    ) -> p.Infra.LazyInitPlan:
        """Build one validated render plan for a synthetic package path."""
        package_dir = workspace_root.joinpath(
            *((c.Infra.DEFAULT_SRC_DIR,) if production else ()), *current_pkg.split(".")
        )
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
        tm.that(content, contains="from .demo import Demo as Demo")
        tm.that(content, contains='__all__: tuple[str, ...] = ("Demo",)')
        tm.that(content, lacks="Nested")
        tm.that(content, lacks="import nested")
        tm.that(content, lacks="install_lazy_exports")

    def test_static_renderer_uses_all_for_unformattable_identity_aliases(
        self, tmp_path: Path
    ) -> None:
        """Use literal __all__ when a redundant alias cannot fit one line."""
        # NOTE (multi-agent, mro-wkii.17.26.2 / agent: codex): __all__ owns
        # the reexport contract when spelling an identity alias exceeds Ruff.
        long_name = (
            "TestsFlextInfraGeneratedInitializerWithAnIntentionallyLongPublicClassName"
        )
        plan = self._plan(
            tmp_path,
            "demo_pkg._fixtures",
            (long_name,),
            MappingProxyType({long_name: ("demo_pkg._fixtures.settings", long_name)}),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        compile(content, "__init__.py", "exec")
        tm.that(content, contains=f"from .settings import (\n    {long_name},\n)")
        tm.that(content, lacks=f"{long_name} as {long_name}")
        tm.that(content, contains=f'    "{long_name}",')

    def test_static_renderer_rejects_unformattable_nonidentity_aliases(
        self, tmp_path: Path
    ) -> None:
        """Fail loud when a renamed reexport cannot satisfy line length."""
        imported_name = (
            "FlextInfraGeneratedInitializerWithAnIntentionallyLongOwnedClassName"
        )
        export_name = "FlextInfraGeneratedInitializerWithAnIntentionallyLongPublicAlias"
        plan = self._plan(
            tmp_path,
            "demo_pkg._fixtures",
            (export_name,),
            MappingProxyType({
                export_name: ("demo_pkg._fixtures.settings", imported_name)
            }),
        )

        with pytest.raises(
            ValueError,
            match="static reexport cannot satisfy generated line-length contract",
        ):
            FlextInfraCodegenGeneration.render_init(plan)

    def test_wrapper_surface_roots_use_lazy_initializers(self, tmp_path: Path) -> None:
        """Use one PEP 562 boundary at tests, examples, and scripts roots."""
        for surface, class_name in (
            ("tests", "TestsDemo"),
            ("examples", "ExamplesDemo"),
            ("scripts", "ScriptsDemo"),
        ):
            plan = self._plan(
                tmp_path,
                surface,
                (class_name, "r"),
                MappingProxyType({
                    class_name: (f"{surface}.demo", class_name),
                    "r": ("flext_core", "r"),
                }),
                production=False,
            )

            init_content = FlextInfraCodegenGeneration.render_init(plan)

            compile(init_content, f"{surface}/__init__.py", "exec")
            tm.that(init_content, contains='".demo":')
            tm.that(init_content, contains=f'"{class_name}",')
            tm.that(init_content, contains='"flext_core": ("r",)')
            tm.that(init_content, contains=f'    "{class_name}",')
            tm.that(init_content, contains='    "r",')
            tm.that(init_content, contains="_install_lazy_exports(")

    def test_tests_root_renders_only_its_facade_contract(self, tmp_path: Path) -> None:
        """Render test facades without importing collected test classes."""
        plan = self._plan(
            tmp_path,
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
            production=False,
        )

        init_content = FlextInfraCodegenGeneration.render_init(plan)

        compile(init_content, "__init__.py", "exec")
        tm.that(init_content, contains="from flext_tests import tm")
        tm.that(init_content, contains="TestsDemoConstants")
        tm.that(init_content, contains="TestsDemoUtilities")
        tm.that(init_content, contains="_install_lazy_exports(")
        tm.that(init_content, lacks="TestsDemoCase")
        tm.that(init_content, lacks=".unit.test_demo")

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
        tm.that(content, lacks="from .protocols import FlextDemoProtocols, p as p")

    def test_root_type_checking_separates_absolute_and_relative_imports(self) -> None:
        """Render Ruff-ordered absolute and local typing import sections."""
        # NOTE (multi-agent, mro-wkii.17.26.2 / agent: codex): reproduce the
        # fleet I001 failure at the public TYPE_CHECKING renderer boundary.
        lines = FlextInfraCodegenGeneration.generate_type_checking(
            {
                "flext_cli": (("FlextCliExternal", "FlextCliExternal"),),
                "flext_core": (("r", "r"),),
                "flext_infra.api": (
                    ("FlextInfraApi", "FlextInfraApi"),
                    ("infra", "infra"),
                ),
            },
            include_flext_types=False,
            local_package_root="flext_infra",
        )

        tm.that(
            "\n".join(lines),
            contains=(
                "    from flext_cli import FlextCliExternal\n"
                "    from flext_core import r\n\n"
                "    from .api import FlextInfraApi, infra"
            ),
        )

    def test_wrapper_root_type_checking_matches_ruff_order(
        self, tmp_path: Path
    ) -> None:
        """Render wrapper facade imports in deterministic Ruff order."""
        # NOTE (multi-agent, mro-0ftd.3.5 / agent: codex): preserve the exact
        # pruned tests-root plan that exposed I001 in the LDIF transaction.
        lazy_map = MappingProxyType({
            "integration": ("tests.integration", ""),
            "unit": ("tests.unit", ""),
            **{
                name: ("flext_tests", name)
                for name in ("d", "e", "h", "r", "td", "tf", "tk", "tm", "tv", "x")
            },
            "TestsFlextLdifServiceBase": ("tests.base", "TestsFlextLdifServiceBase"),
            "s": ("tests.base", "s"),
            "TestsFlextLdifConstants": ("tests.constants", "TestsFlextLdifConstants"),
            "c": ("tests.constants", "c"),
            "TestsFlextLdifModels": ("tests.models", "TestsFlextLdifModels"),
            "m": ("tests.models", "m"),
            "TestsFlextLdifProtocols": ("tests.protocols", "TestsFlextLdifProtocols"),
            "p": ("tests.protocols", "p"),
            "TestsFlextLdifSettings": ("tests.settings", "TestsFlextLdifSettings"),
            "TestsFlextLdifTypes": ("tests.typings", "TestsFlextLdifTypes"),
            "t": ("tests.typings", "t"),
            "TestsFlextLdifUtilities": ("tests.utilities", "TestsFlextLdifUtilities"),
            "u": ("tests.utilities", "u"),
        })
        plan = self._plan(
            tmp_path, "tests", tuple(lazy_map), lazy_map, production=False
        )

        content = FlextInfraCodegenGeneration.render_init(plan)
        type_checking_block = content.split("if TYPE_CHECKING:", maxsplit=1)[1].split(
            "_LAZY_MODULES", maxsplit=1
        )[0]

        tm.that(
            type_checking_block,
            contains=(
                "    from flext_tests import d, e, h, r, td, tf, tk, tm, tv, x\n\n"
                "    from . import integration, unit\n"
                "    from .base import TestsFlextLdifServiceBase, s\n"
                "    from .constants import TestsFlextLdifConstants, "
                "TestsFlextLdifConstants as c\n"
                "    from .models import TestsFlextLdifModels, "
                "TestsFlextLdifModels as m\n"
                "    from .protocols import TestsFlextLdifProtocols, "
                "TestsFlextLdifProtocols as p\n"
                "    from .settings import TestsFlextLdifSettings\n"
                "    from .typings import TestsFlextLdifTypes, "
                "TestsFlextLdifTypes as t\n"
                "    from .utilities import TestsFlextLdifUtilities, "
                "TestsFlextLdifUtilities as u"
            ),
        )

    def test_root_runtime_keeps_first_party_imports_in_one_section(
        self, tmp_path: Path
    ) -> None:
        """Keep distinct first-party modules in one Ruff import section."""
        # NOTE (multi-agent, mro-wkii.17.26.2 / agent: codex): distinct FLEXT
        # owners are one isort section; module boundaries are not sections.
        plan = self._plan(
            tmp_path,
            "demo_pkg",
            ("__cli_version__", "__core_version__"),
            MappingProxyType({}),
            eager_dunders=MappingProxyType({
                "__cli_version__": ("flext_cli.__version__", "__version__"),
                "__core_version__": ("flext_core.__version__", "__version__"),
            }),
        )

        content = FlextInfraCodegenGeneration.render_init(plan)

        tm.that(
            content,
            contains=(
                "from flext_cli.__version__ import __version__ as __cli_version__\n"
                "from flext_core.__version__ import __version__ as __core_version__"
            ),
        )

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
        tm.that(content, contains='__all__: tuple[str, ...] = ("FlextDemoModels",)')
        tm.that(content, lacks="install_lazy_exports")

    def test_root_service_alias_uses_typed_service_base(self) -> None:
        """Bind ``s`` to the concrete project service base for static analysis."""
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
        tm.that(content, contains="FlextDemoServiceBase as s")
        tm.that(content, lacks="from .base import FlextDemoServiceBase, s")

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
