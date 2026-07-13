"""Behavior tests for public lazy-init generation."""

from __future__ import annotations

from pathlib import Path

from tests import c
from tests import u
from flext_tests import tm


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
        # mro-i6nq.10: The root ABI is owned by the generated unit manifest.
        return package_root.joinpath(c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

    def test_discover_package_from_standard_roots(self) -> None:
        assert (
            u.Infra.package_name(Path("/workspace/src/test_pkg/__init__.py"))
            == "test_pkg"
        )
        assert (
            u.Infra.package_name(Path("/workspace/tests/unit/__init__.py"))
            == "tests.unit"
        )
        assert (
            u.Infra.package_name(Path("/workspace/examples/tests/__init__.py"))
            == "examples.tests"
        )

    def test_root_generation_uses_real_classes_and_aliases(
        self, tmp_path: Path
    ) -> None:
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
        tm.that(init_content, has="from flext_core.lazy import (")
        tm.that(init_content, has="build_lazy_import_map,")
        tm.that(init_content, has="install_lazy_exports,")
        tm.that(init_content, has="_LAZY_IMPORTS")
        tm.that(exports_content, has='"FlextDemoModels"')
        tm.that(exports_content, has='"m"')

    def test_private_modules_do_not_export_from_root(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "_internal.py").write_text(
            "from __future__ import annotations\n\nclass FlextDemoInternal:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        tm.that(self._generated_init(package_root), lacks="FlextDemoInternal")

    def test_private_child_packages_do_not_widen_root_api(self, tmp_path: Path) -> None:
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
            "PUBLIC_EXPORTS: tuple[str, ...] =", maxsplit=1
        )[1]

        # mro-i6nq.10: private child classes never become root ABI.
        tm.that(public_exports, lacks="FlextDemoEnforcementEngine")
        tm.that(public_exports, lacks='"_enforcement"')

    def test_explicit_all_exports_keep_public_aliases_only(
        self, tmp_path: Path
    ) -> None:
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

    def test_child_exports_bubble_public_symbols_only(self, tmp_path: Path) -> None:
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
            'from __future__ import annotations\n\nBLUE = "blue"\n\n__all__: list[str] = ["BLUE"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child_dir / "cli.py").write_text(
            'from __future__ import annotations\n\ndef main() -> str:\n    return "ok"\n',
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

        tm.that(exports_content, has="FlextDemoService")
        tm.that(exports_content, has='"BLUE"')
        tm.that(exports_content, lacks='"main"')
        tm.that(exports_content, lacks='"m": ("flext_demo.services.models", "m")')

    def test_tests_root_uses_private_lazy_manifest(self, tmp_path: Path) -> None:
        """A tests root keeps imports lazy and local to avoid collection cycles."""
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
        (child_dir / "child.py").write_text(
            "from __future__ import annotations\n\n"
            "class Child:\n"
            "    pass\n\n"
            '__all__: list[str] = ["Child"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        init_content = tests_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        unit_content = tests_root.joinpath(c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        # NOTE (multi-agent): mro-i6nq.10 prevents eager test-suite fan-out.
        tm.that(init_content, has="from tests.__unit__ import (")
        tm.that(init_content, has="install_lazy_exports(")
        tm.that(unit_content, has='".constants": (')
        tm.that(unit_content, has='".unit.child": ("Child",)')
        tm.that(unit_content, has='CHILD_MODULE_PATHS: tuple[str, ...] = (".unit",)')
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(runtime_content, lacks="from tests.constants import")
        compile(unit_content, "tests/__unit__.py", "exec")
        compile(init_content, "tests/__init__.py", "exec")
        check_service = u.Tests.create_lazy_init_service(workspace_root)
        tm.that(check_service.generate_inits(check_only=True), eq=0)
        assert not check_service.modified_files

    def test_root_aliases_follow_transitive_parent_exports_from_source(
        self, tmp_path: Path
    ) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-meltano", package_name="flext_meltano"
        )
        core_root = tmp_path / "flext-core" / c.Infra.DEFAULT_SRC_DIR / "flext_core"
        core_root.mkdir(parents=True)
        core_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
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
        cli_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
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

        # mro-i6nq.10: Assert the grouped manifest import structurally.
        tm.that(init_content, has="from flext_meltano.__unit__ import (")
        tm.that(init_content, has="PUBLIC_EXPORTS as _PUBLIC_EXPORTS,")
        tm.that(init_content, has="__all__: tuple[str, ...]")
        tm.that(init_content, has="public_exports=_PUBLIC_EXPORTS")
        for alias_name in ("d", "e", "h", "m", "p", "r", "s", "t", "u", "x"):
            tm.that(exports_content, has=f'    "{alias_name}",')
        public_exports = exports_content.split(
            "PUBLIC_EXPORTS: tuple[str, ...] =", maxsplit=1
        )[1]
        present_aliases = tuple(
            alias
            for alias in c.Infra.PUBLIC_ROOT_ALIAS_ORDER
            if f'"{alias}"' in public_exports
        )
        alias_positions = tuple(
            public_exports.index(f'"{alias}"') for alias in present_aliases
        )
        tm.that(alias_positions, eq=tuple(sorted(alias_positions)))
        assert (
            "from flext_cli import d, e, h, m, p, r, s, t, u, x"
            not in init_content.splitlines()
        )
        tm.that(exports_content, has='"flext_cli": (')
        tm.that(exports_content, has='".constants": (')

    def test_nested_tests_namespace_exports_local_symbols_only(
        self, tmp_path: Path
    ) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.RESULT_PY).write_text(
            "from __future__ import annotations\n\nclass FlextDemoResult:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_unit_root = workspace_root / c.Infra.DIR_TESTS / "unit"
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

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        init_content = tests_unit_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        unit_content = tests_unit_root.joinpath(c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        # mro-i6nq.10: Nested test packages use the universal lazy contract.
        tm.that(init_content, has="from tests.unit.__unit__ import (")
        tm.that(init_content, has="install_lazy_exports(")
        tm.that(init_content, has="__all__: tuple[str, ...]")
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(runtime_content, lacks="from tests.unit.constants import")
        tm.that(runtime_content, lacks="from tests.unit.models import")
        tm.that(unit_content, has="TestsFlextDemoUnitConstants")
        tm.that(unit_content, has="TestsFlextDemoUnitModels")

    def test_root_exports_symbols_from_deep_descendant_packages(
        self, tmp_path: Path
    ) -> None:
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

        tm.that(exports_content, has="FlextDemoHttpTransport")

    def test_duplicate_public_export_resolved_by_canonical_scorer(
        self, tmp_path: Path
    ) -> None:
        """Duplicate public exports are resolved deterministically (warn + generate)."""
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "alpha.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (package_root / "beta.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        init_content = self._generated_init(package_root)
        exports_content = self._generated_exports(package_root)
        assert init_content.startswith(c.Infra.AUTOGEN_HEADER)
        tm.that(exports_content, has="Shared")
