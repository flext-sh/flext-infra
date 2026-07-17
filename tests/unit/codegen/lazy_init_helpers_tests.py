"""Behavior tests for public lazy-init generation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flext_tests import tm

from tests import c, u


class TestsFlextInfraLazyInitHelpers:
    """Validate lazy-init through the public service surface only."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path]:
        workspace: tuple[Path, Path] = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        return workspace

    @staticmethod
    def _generated_init(package_root: Path) -> str:
        return package_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

    @staticmethod
    def _generated_exports(package_root: Path) -> str:
        # mro-wkii.17 (Codex): the generated initializer owns the inline ABI.
        return TestsFlextInfraLazyInitHelpers._generated_init(package_root)

    def test_discover_package_from_standard_roots(self) -> None:
        """Resolve package names consistently for every supported source shape."""
        tm.that(
            u.Infra.package_name(Path("/workspace/src/test_pkg/__init__.py")),
            eq="test_pkg",
        )
        tm.that(
            u.Infra.package_name(Path("/workspace/tests/unit/__init__.py")),
            eq="tests.unit",
        )
        tm.that(
            u.Infra.package_name(Path("/workspace/examples/tests/__init__.py")),
            eq="examples.tests",
        )

    def test_root_generation_uses_real_classes_and_aliases(
        self, tmp_path: Path
    ) -> None:
        """Publish real root declarations through the inline lazy contract."""
        workspace_root, package_root = self._workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        init_content = self._generated_init(package_root)
        exports_content = self._generated_exports(package_root)

        # mro-i6nq.10: Assert runtime installation through observable exports.
        tm.that(init_content, has="build_lazy_import_map as _build_lazy_import_map")
        tm.that(init_content, has="install_lazy_exports as _install_lazy_exports")
        tm.that(init_content, has="_LAZY_IMPORTS")
        tm.that(exports_content, has='"FlextDemoModels"')
        tm.that(exports_content, has='"m"')

    def test_generated_root_resolves_only_its_declared_runtime_abi(
        self, tmp_path: Path
    ) -> None:
        """Resolve a generated lazy export without publishing runtime helpers."""
        workspace_root, package_root = self._workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        pythonpath = os.pathsep.join(
            part
            for part in (
                str(workspace_root / c.Infra.DEFAULT_SRC_DIR),
                os.environ.get("PYTHONPATH", ""),
            )
            if part
        )
        probe = u.Cli.run_raw(
            [
                sys.executable,
                "-c",
                (
                    "import flext_demo as package\n"
                    "assert package.m is package.FlextDemoModels\n"
                    "assert tuple(package.__all__) == "
                    "('FlextDemoModels', 'm')\n"
                    "assert not hasattr(package, 'build_lazy_import_map')\n"
                    "assert not hasattr(package, 'install_lazy_exports')\n"
                    "print(package.m.__name__, package.__all__)\n"
                ),
            ],
            cwd=workspace_root,
            env={**os.environ, "PYTHONPATH": pythonpath},
        )

        tm.ok(probe)
        tm.that(probe.value.exit_code, eq=0)
        tm.that(probe.value.stdout, has="FlextDemoModels")

    def test_private_modules_do_not_export_from_root(self, tmp_path: Path) -> None:
        """Keep private sibling modules outside the public package contract."""
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "_internal.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoInternal:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        tm.that(self._generated_init(package_root), lacks="FlextDemoInternal")

    def test_root_regeneration_preserves_declared_abi_only(
        self, tmp_path: Path
    ) -> None:
        """Keep module-local public helpers outside the package-root ABI."""
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: tuple[str, ...] = ("FlextDemoConstants", "FlextDemoLazy", "c")\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "class FlextDemoConstants:\n"
            '    """Canonical constants facade."""\n\n'
            "class FlextDemoConstantsEnforcement:\n"
            '    """Module-local composition class."""\n\n'
            "c = FlextDemoConstants\n\n"
            '__all__ = ("FlextDemoConstants", '
            '"FlextDemoConstantsEnforcement", "c")\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath("lazy.py").write_text(
            "class FlextDemoLazy:\n"
            '    """Canonical lazy facade."""\n\n'
            "class FlextDemoLazyAttribute:\n"
            '    """Module-local implementation type."""\n\n'
            "def lazy_attribute() -> None:\n"
            '    """Module-local helper."""\n\n'
            '__all__ = ("FlextDemoLazy", "FlextDemoLazyAttribute", '
            '"lazy_attribute")\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated = self._generated_init(package_root)
        has_all, exports = u.Tests.extract_lazy_init_exports(generated)

        tm.that(has_all, eq=True)
        tm.that(exports, eq=("FlextDemoConstants", "FlextDemoLazy", "c"))
        tm.that(generated, lacks="FlextDemoConstantsEnforcement")
        tm.that(generated, lacks="FlextDemoLazyAttribute")
        tm.that(generated, lacks="lazy_attribute")

    def test_root_regeneration_fails_for_contract_without_owner(
        self, tmp_path: Path
    ) -> None:
        """Reject silent removal when an existing public name loses its owner."""
        workspace_root, package_root = self._workspace(tmp_path)
        declared_contract = (
            '__all__: tuple[str, ...] = ("FlextDemoModels", "FlextDemoMissing", "m")\n'
        )
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            declared_contract, encoding=c.Cli.ENCODING_DEFAULT
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextDemoModels", alias="m"
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=1)
        tm.that(self._generated_init(package_root), eq=declared_contract)

    def test_private_child_packages_do_not_widen_root_api(self, tmp_path: Path) -> None:
        """Keep private child declarations outside the public root contract."""
        workspace_root, package_root = self._workspace(tmp_path)
        child_dir = package_root / "_enforcement"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (child_dir / "engine.py").write_text(
            "class FlextDemoEnforcementEngine:\n"
            '    """Internal engine."""\n\n'
            '__all__ = ["FlextDemoEnforcementEngine"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        exports_content = self._generated_exports(package_root)
        public_exports = exports_content.split(
            "__all__: tuple[str, ...] =", maxsplit=1
        )[1]

        # mro-i6nq.10: private child classes never become root ABI.
        tm.that(exports_content, lacks="FlextDemoEnforcementEngine")
        tm.that(public_exports, lacks="FlextDemoEnforcementEngine")
        tm.that(public_exports, lacks='"_enforcement"')

    def test_public_api_owns_private_fixture_reexports(self, tmp_path: Path) -> None:
        """Publish a fixture-backed class only through the public API facade."""
        workspace_root, package_root = self._workspace(tmp_path)
        fixtures_dir = package_root / "_fixtures"
        fixtures_dir.mkdir()
        fixtures_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        fixtures_dir.joinpath("__version__.py").write_text(
            '__version__ = "0.1.0"\n', encoding=c.Cli.ENCODING_DEFAULT
        )
        fixtures_dir.joinpath("enforcement.py").write_text(
            "class FlextDemoReportLoader:\n"
            '    """Load a report through the public facade."""\n\n'
            '__all__ = ["FlextDemoReportLoader"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath("api.py").write_text(
            "from ._fixtures.enforcement import FlextDemoReportLoader\n\n"
            '__all__ = ["FlextDemoReportLoader"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated = self._generated_init(package_root)
        fixture_init = self._generated_init(fixtures_dir)

        # mro-wkii.17.26 (Codex): only the public facade may own the root ABI.
        # mro-wkii.17.26.2 (codex): private implementations never own root ABI.
        tm.that(generated, has='".api": (')
        tm.that(generated, has='"FlextDemoReportLoader",')
        tm.that(generated, lacks="flext_demo._fixtures.enforcement")
        tm.that(fixture_init, contains="__all__: tuple[str, ...] = ()")
        tm.that(fixture_init, lacks="FlextDemoReportLoader")
        tm.that(fixture_init, lacks="__version__")

    def test_nested_runtime_singleton_does_not_widen_root_api(
        self, tmp_path: Path
    ) -> None:
        """Keep a nested settings singleton owned by its child package."""
        workspace_root, package_root = self._workspace(tmp_path)
        services_dir = package_root / "services"
        services_dir.mkdir()
        services_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        services_dir.joinpath("_settings.py").write_text(
            'settings = "nested"\n\n__all__ = ["settings"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated = self._generated_init(package_root)

        # mro-wkii.17.26 (Codex): singleton conventions apply only at root.
        tm.that(generated, lacks='"settings"')
        tm.that(generated, lacks="flext_demo.services._settings")

    def test_private_direct_imports_never_widen_the_root_contract(
        self, tmp_path: Path
    ) -> None:
        """Keep implementation-only symbols out of generated root imports."""
        workspace_root, package_root = self._workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextDemoModels", alias="m"
        )
        utilities_dir = package_root / "_utilities"
        utilities_dir.mkdir()
        utilities_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        conversion_path = utilities_dir / "conversion.py"
        conversion_path.write_text(
            "class FlextDemoConversion:\n"
            '    """Private conversion implementation."""\n\n'
            '__all__ = ["FlextDemoConversion"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated_content = self._generated_init(package_root)
        tm.that(generated_content, lacks="_DIRECT_IMPORTS")
        tm.that(generated_content, lacks='"FlextDemoConversion"')

        extra_path = utilities_dir / "extra.py"
        extra_path.write_text(
            "class FlextDemoExtra:\n"
            '    """New internal name outside the frozen contract."""\n\n'
            '__all__ = ["FlextDemoExtra"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        tm.that(self._generated_init(package_root), lacks="FlextDemoExtra")

    def test_private_subdirectory_facade_never_becomes_root_public(
        self, tmp_path: Path
    ) -> None:
        """Keep private family facades and their parts out of the root API."""
        workspace_root, package_root = self._workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextDemoModels", alias="m"
        )
        models_dir = package_root / "_models"
        parts_dir = models_dir / "_base_parts"
        parts_dir.mkdir(parents=True)
        for package_dir in (models_dir, parts_dir):
            package_dir.joinpath(c.Infra.INIT_PY).write_text(
                "", encoding=c.Cli.ENCODING_DEFAULT
            )
        parts_dir.joinpath("flextdemomodelsbase_part_01.py").write_text(
            "class FlextDemoModelsBase:\n"
            '    """Private implementation part."""\n\n'
            '__all__ = ["FlextDemoModelsBase"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        models_dir.joinpath("base.py").write_text(
            "from ._base_parts.flextdemomodelsbase_part_01 import "
            "FlextDemoModelsBase as FlextDemoModelsBasePart01\n\n"
            "class FlextDemoModelsBase(FlextDemoModelsBasePart01):\n"
            '    """Public facade."""\n\n'
            '__all__ = ["FlextDemoModelsBase"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated = self._generated_init(package_root)

        tm.that(generated, lacks="FlextDemoModelsBase")
        tm.that(generated, lacks='"._models.base"')
        tm.that(generated, lacks="._models._base_parts.flextdemomodelsbase_part_01")

    def test_private_package_policy_rejects_numeric_module_names(
        self, tmp_path: Path
    ) -> None:
        """Generate valid private siblings without rendering numeric imports."""
        workspace_root, package_root = self._workspace(tmp_path)
        models_dir = package_root / "_models"
        models_dir.mkdir()
        models_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        models_dir.joinpath("_shared.py").write_text(
            "class FlextDemoShared:\n"
            '    """Private package export."""\n\n'
            '__all__ = ["FlextDemoShared"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        models_dir.joinpath("01_bad.py").write_text(
            "class FlextDemoBad:\n"
            '    """Invalid numeric module export."""\n\n'
            '__all__ = ["FlextDemoBad"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        generated = self._generated_init(models_dir)

        # mro-wkii.17.26 (Codex): policy is authoritative at every depth.
        tm.that(
            generated, has="from ._shared import FlextDemoShared as FlextDemoShared"
        )
        tm.that(generated, lacks="01_bad")
        tm.that(generated, lacks="FlextDemoBad")

    def test_explicit_all_exports_keep_public_aliases_only(
        self, tmp_path: Path
    ) -> None:
        """Respect an explicit module export contract without leaking siblings."""
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "api.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemo:\n"
            "    pass\n\n"
            "demo = FlextDemo()\n"
            "hidden = FlextDemo()\n\n"
            '__all__: list[str] = ["FlextDemo", "demo"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        exports_content = self._generated_exports(package_root)

        tm.that(exports_content, has='"FlextDemo"')
        tm.that(exports_content, has='"demo"')
        tm.that(exports_content, lacks="hidden")

    def test_child_exports_stay_owned_by_their_subpackage(self, tmp_path: Path) -> None:
        """Keep deep child declarations out of the thin root facade."""
        workspace_root, package_root = self._workspace(tmp_path)
        child_dir = package_root / "services"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (child_dir / "service.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoService:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoService"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child_dir / "colors.py").write_text(
            "from __future__ import annotations\n\n"
            'BLUE = "blue"\n\n'
            '__all__: list[str] = ["BLUE"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child_dir / "cli.py").write_text(
            "from __future__ import annotations\n\n"
            "def main() -> str:\n"
            '    return "ok"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Tests.write_lazy_init_namespace_module(
            child_dir / "models.py",
            class_name="FlextDemoServicesModels",
            alias="m",
            docstring="Models.",
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        exports_content = self._generated_exports(package_root)

        tm.that(exports_content, lacks="FlextDemoService")
        tm.that(exports_content, lacks='"BLUE"')
        tm.that(exports_content, lacks='"main"')
        tm.that(exports_content, lacks='"m": ("flext_demo.services.models", "m")')

    def test_tests_root_remains_outside_production_codegen(
        self, tmp_path: Path
    ) -> None:
        """Generate static test package initializers without a lazy root."""
        workspace_root, _package_root = self._workspace(tmp_path)
        tests_root = workspace_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        tests_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoConstants:\n"
            "    pass\n\n"
            "c = TestsFlextDemoConstants\n\n"
            '__all__: list[str] = ["TestsFlextDemoConstants", "c"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        child_dir = tests_root / "unit"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (child_dir / "test_child.py").write_text(
            "from __future__ import annotations\n\n"
            "class Child:\n"
            "    pass\n\n"
            '__all__: list[str] = ["Child"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(
            u.Tests.run_lazy_init(workspace_root, target_module=c.Infra.DIR_TESTS), eq=0
        )
        init_content = tests_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(init_content, contains='".constants": (')
        tm.that(init_content, contains='"TestsFlextDemoConstants",')
        tm.that(init_content, contains='"c",')
        tm.that(init_content, contains="_install_lazy_exports(")
        tm.that(tests_root.joinpath("__unit__.py").exists(), eq=False)
        child_init_content = child_dir.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        # mro-wkii.17.26 (codex): collected test classes remain module-local;
        # importing one test package must not pull every sibling test module.
        tm.that(child_init_content, lacks="Child")
        tm.that(child_init_content, contains="__all__: tuple[str, ...] = ()")
        compile(init_content, "tests/__init__.py", "exec")
        tm.that(
            u.Tests.run_lazy_init(
                workspace_root, check_only=True, target_module=c.Infra.DIR_TESTS
            ),
            eq=0,
        )

    def test_root_aliases_follow_transitive_parent_exports_from_source(
        self, tmp_path: Path
    ) -> None:
        """Order inherited aliases by the canonical facade dependency chain."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-meltano", package_name="flext_meltano"
        )
        core_root = tmp_path / "flext-core" / c.Infra.DEFAULT_SRC_DIR / "flext_core"
        core_root.mkdir(parents=True)
        core_root.parent.parent.joinpath(c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        core_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        u.Tests.write_lazy_init_namespace_module(
            core_root / "result.py",
            class_name="FlextCoreResult",
            alias="r",
            docstring="Result.",
        )
        core_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextCoreConstants:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextCoreConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        cli_root = tmp_path / "flext-cli" / c.Infra.DEFAULT_SRC_DIR / "flext_cli"
        cli_root.mkdir(parents=True)
        cli_root.parent.parent.joinpath(c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-cli"\nversion = "0.1.0"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: list[str] = ["c", "r"]\n', encoding=c.Cli.ENCODING_DEFAULT
        )
        cli_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import FlextCoreConstants\n\n"
            "class FlextCliConstants(FlextCoreConstants):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextCliConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextMeltanoConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextMeltanoConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        init_content = self._generated_init(package_root)
        exports_content = self._generated_exports(package_root)

        # mro-wkii.17 (Codex): aliases live in the inline root contract.
        tm.that(init_content, has="_LAZY_MODULES: dict[str, tuple[str, ...]]")
        tm.that(init_content, has="__all__: tuple[str, ...]")
        tm.that(init_content, has="install_lazy_exports(")
        tm.that(init_content, lacks="__unit__")
        tm.that(init_content, lacks="_root_typing_parts")
        ruff_ordered_aliases = ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x")
        for alias_name in ruff_ordered_aliases:
            tm.that(exports_content, has=f'    "{alias_name}",')
        public_exports = exports_content.split(
            "__all__: tuple[str, ...] =", maxsplit=1
        )[1]
        # mro-wkii.17 (Codex): __all__ follows RUF022; dependency order remains
        # exclusively in the static facade imports.
        alias_positions = tuple(
            public_exports.index(f'"{alias}"') for alias in ruff_ordered_aliases
        )
        tm.that(alias_positions, eq=tuple(sorted(alias_positions)))
        tm.that(
            init_content.splitlines(),
            lacks="from flext_cli import d, e, h, m, p, r, s, t, u, x",
        )
        tm.that(exports_content, has='"flext_cli": (')
        tm.that(exports_content, has='".constants": (')

    def test_nested_tests_namespace_exports_local_symbols_only(
        self, tmp_path: Path
    ) -> None:
        """Generate static nested test initializers with local exports only."""
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.RESULT_PY).write_text(
            "from __future__ import annotations\n\nclass FlextDemoResult:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_root = workspace_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        tests_unit_root = tests_root / "unit"
        tests_unit_root.mkdir(parents=True)
        tests_unit_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        tests_unit_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitConstants:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_unit_root.joinpath(c.Infra.MODELS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitModels:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(
            u.Tests.run_lazy_init(workspace_root, target_module=c.Infra.DIR_TESTS), eq=0
        )
        init_content = tests_unit_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(
            init_content,
            contains=(
                "from .constants import TestsFlextDemoUnitConstants "
                "as TestsFlextDemoUnitConstants"
            ),
        )
        tm.that(
            init_content,
            contains=(
                "from .models import TestsFlextDemoUnitModels "
                "as TestsFlextDemoUnitModels"
            ),
        )
        tm.that(init_content, lacks="install_lazy_exports")
        tm.that(tests_unit_root.joinpath("__unit__.py").exists(), eq=False)

    def test_root_excludes_symbols_from_deep_descendant_packages(
        self, tmp_path: Path
    ) -> None:
        """Keep deeply nested declarations owned by their subpackage facade."""
        workspace_root, package_root = self._workspace(tmp_path)
        deep_dir = package_root / "services" / "http"
        deep_dir.mkdir(parents=True)
        (package_root / "services" / c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        deep_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        deep_dir.joinpath("transport.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoHttpTransport:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoHttpTransport"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        exports_content = self._generated_exports(package_root)

        tm.that(exports_content, lacks="FlextDemoHttpTransport")

    def test_undeclared_duplicate_symbols_fail_before_write(
        self, tmp_path: Path
    ) -> None:
        """Reject ambiguous root ownership without changing the initializer."""
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "api.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n\n"
            '__all__: list[str] = ["Shared"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (package_root / "service.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n\n"
            '__all__: list[str] = ["Shared"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()

        # mro-wkii.17.26.2 (codex): the source owners must be reconciled; the
        # generator never picks a public ABI winner on the operator's behalf.
        tm.that(u.Tests.run_lazy_init(workspace_root), eq=1)
        tm.that(init_path.read_bytes(), eq=original_init)
