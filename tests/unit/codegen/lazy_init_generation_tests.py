"""Tests for lazy_init code generation: aliases, type checking, file output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as mod
from flext_infra import FlextInfraCodegenGeneration
from tests import c, t, u


class TestResolveAliases:
    """Test declarative alias inheritance from public package exports."""

    @staticmethod
    def _write_parent_package(tmp_path: Path) -> None:
        project_dir = tmp_path / "flext-tests"
        project_dir.mkdir(parents=True)
        _ = (project_dir / "pyproject.toml").write_text(
            "[project]\nname = 'flext-tests'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        package_dir = project_dir / "src" / "flext_tests"
        utilities_dir = package_dir / "_utilities"
        package_dir.mkdir(parents=True)
        utilities_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (package_dir / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestsConstants:\n    pass\n\n"
            "c = FlextTestsConstants\n"
            '__all__ = ["FlextTestsConstants", "c"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (package_dir / "docker.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestsDocker:\n    pass\n\n"
            "tk = FlextTestsDocker\n"
            '__all__ = ["FlextTestsDocker", "tk"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (utilities_dir / "__init__.py").write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (utilities_dir / "matchers.py").write_text(
            'from __future__ import annotations\n\ntm = "matcher"\n__all__ = ["tm"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )

    @staticmethod
    def _write_surface_package(tmp_path: Path, surface: str) -> Path:
        project_dir = tmp_path / "child"
        project_dir.mkdir(parents=True)
        _ = (project_dir / "pyproject.toml").write_text(
            "[project]\nname = 'child'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        surface_dir = project_dir / surface
        surface_dir.mkdir(parents=True)
        (surface_dir / "__init__.py").write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (surface_dir / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_tests.constants import FlextTestsConstants\n\n"
            "class TestsFlextDemoConstants(FlextTestsConstants):\n    pass\n\n"
            "c = TestsFlextDemoConstants\n"
            '__all__ = ["TestsFlextDemoConstants", "c"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        return surface_dir

    @pytest.mark.parametrize(
        ("surface", "expected"),
        [
            (
                "tests",
                {
                    "c": ("flext_tests.constants", "c"),
                    "tk": ("flext_tests.docker", "tk"),
                    "tm": ("flext_tests._utilities.matchers", "tm"),
                },
            ),
            ("examples", {"c": ("flext_tests.constants", "c")}),
            ("scripts", {"c": ("flext_tests.constants", "c")}),
        ],
    )
    def test_inherits_only_declared_parent_aliases_by_surface(
        self,
        tmp_path: Path,
        surface: str,
        expected: Mapping[str, tuple[str, str]],
    ) -> None:
        """Root wrappers inherit only the aliases declared for their surface."""
        self._write_parent_package(tmp_path)
        pkg_dir = self._write_surface_package(tmp_path, surface)
        lazy_map: MutableMapping[str, tuple[str, str]] = {}
        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=pkg_dir,
        )
        tm.that(lazy_map, eq=expected)

    def test_parent_alias_filter_blocks_noncanonical_lowercase_exports(
        self,
        tmp_path: Path,
    ) -> None:
        """Lowercase helpers outside the declared allowlist must not leak."""
        self._write_parent_package(tmp_path)
        package_dir = tmp_path / "flext-tests" / "src" / "flext_tests"
        (package_dir / "lazy.py").write_text(
            'build_lazy_import_map = "nope"\n__all__ = ["build_lazy_import_map"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        pkg_dir = self._write_surface_package(tmp_path, "examples")
        lazy_map: MutableMapping[str, tuple[str, str]] = {}
        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=pkg_dir,
        )
        tm.that(lazy_map, lacks="build_lazy_import_map")

    @pytest.mark.parametrize("surface", ["tests", "examples", "scripts"])
    def test_surface_root_inherits_aliases_from_project_source_package(
        self,
        tmp_path: Path,
        surface: str,
    ) -> None:
        """Surface roots inherit source aliases without replacing local aliases."""
        project_dir = tmp_path / "flext-demo"
        src_dir = project_dir / c.Infra.Paths.DEFAULT_SRC_DIR / "flext_demo"
        surface_dir = project_dir / surface
        src_dir.mkdir(parents=True)
        surface_dir.mkdir(parents=True)
        (project_dir / c.Infra.Files.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'flext-demo'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (src_dir / c.Infra.Files.INIT_PY).write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (surface_dir / c.Infra.Files.INIT_PY).write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        for module_name, alias, class_name in (
            ("constants.py", "c", "FlextDemoConstants"),
            ("models.py", "m", "FlextDemoModels"),
            ("protocols.py", "p", "FlextDemoProtocols"),
            ("typings.py", "t", "FlextDemoTypes"),
            ("utilities.py", "u", "FlextDemoUtilities"),
        ):
            (src_dir / module_name).write_text(
                "from __future__ import annotations\n\n"
                f"class {class_name}:\n"
                "    pass\n\n"
                f"{alias} = {class_name}\n"
                f'__all__ = ["{class_name}", "{alias}"]\n',
                encoding=c.Infra.Encoding.DEFAULT,
            )
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "m": (f"{surface}.models", "m"),
        }

        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=surface_dir,
        )

        tm.that(lazy_map["m"], eq=(f"{surface}.models", "m"))
        tm.that(lazy_map["c"], eq=("flext_demo.constants", "c"))
        tm.that(lazy_map["p"], eq=("flext_demo.protocols", "p"))
        tm.that(lazy_map["t"], eq=("flext_demo.typings", "t"))
        tm.that(lazy_map["u"], eq=("flext_demo.utilities", "u"))

    @pytest.mark.parametrize("surface", ["tests", "examples", "scripts"])
    def test_does_not_synthesize_alias_from_local_suffix_match(
        self,
        tmp_path: Path,
        surface: str,
    ) -> None:
        """Local Result-like classes must not manufacture runtime aliases."""
        pkg_dir = self._write_surface_package(tmp_path, surface)
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "TestsFlextCoreConstantsResult": (
                f"{surface}._constants.result",
                "TestsFlextCoreConstantsResult",
            ),
        }
        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=pkg_dir,
        )
        tm.that(lazy_map, excludes="r")

    def test_subpackage_does_not_add_runtime_aliases(self, tmp_path: Path) -> None:
        """Nested packages do not inherit parent aliases."""
        pkg_dir = tmp_path / "src" / "pkg" / "tools"
        pkg_dir.mkdir(parents=True)
        _ = (tmp_path / "src" / "pkg" / "__init__.py").write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        _ = (pkg_dir / "__init__.py").write_text(
            "",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
            "FlextModels": ("pkg.models", "FlextModels"),
            "FlextTypes": ("pkg.typings", "FlextTypes"),
        }
        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=pkg_dir,
        )
        tm.that(lazy_map, lacks="c")
        tm.that(lazy_map, lacks="tk")
        tm.that(lazy_map, lacks="tm")

    def test_root_package_keeps_local_alias_and_inherits_from_ancestor_chain(
        self,
        tmp_path: Path,
    ) -> None:
        """Root package keeps local aliases while inheriting runtime ones transitively."""
        core_project_dir = tmp_path / "flext-core"
        core_project_dir.mkdir(parents=True)
        _ = (core_project_dir / "pyproject.toml").write_text(
            "[project]\nname = 'flext-core'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        core_dir = core_project_dir / "src" / "flext_core"
        core_dir.mkdir(parents=True)
        (core_dir / "__init__.py").write_text("", encoding=c.Infra.Encoding.DEFAULT)
        (core_dir / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextConstants:\n    pass\n\n"
            "c = FlextConstants\n"
            '__all__ = ["FlextConstants", "c"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        (core_dir / "result.py").write_text(
            "from __future__ import annotations\n\n"
            'r = "runtime-result"\n'
            '__all__ = ["r"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        parent_project_dir = tmp_path / "flext-cli"
        parent_project_dir.mkdir(parents=True)
        _ = (parent_project_dir / "pyproject.toml").write_text(
            "[project]\nname = 'flext-cli'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        parent_dir = parent_project_dir / "src" / "flext_cli"
        parent_dir.mkdir(parents=True)
        (parent_dir / "__init__.py").write_text("", encoding=c.Infra.Encoding.DEFAULT)
        (parent_dir / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core.constants import FlextConstants\n\n"
            "class FlextCliConstants(FlextConstants):\n    pass\n\n"
            "c = FlextCliConstants\n"
            '__all__ = ["FlextCliConstants", "c"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        project_dir = tmp_path / "flext-infra"
        project_dir.mkdir(parents=True)
        _ = (project_dir / "pyproject.toml").write_text(
            "[project]\nname = 'flext-infra'\nversion = '0.0.0'\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        pkg_dir = project_dir / "src" / "flext_infra"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding=c.Infra.Encoding.DEFAULT)
        (pkg_dir / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli.constants import FlextCliConstants\n\n"
            "class FlextInfraConstants(FlextCliConstants):\n    pass\n\n"
            "c = FlextInfraConstants\n"
            '__all__ = ["FlextInfraConstants", "c"]\n',
            encoding=c.Infra.Encoding.DEFAULT,
        )
        lazy_map = (
            mod.FlextInfraUtilitiesCodegenLazyScanning.build_sibling_export_index(
                pkg_dir,
                "flext_infra",
            )
        )
        mod.FlextInfraUtilitiesCodegenLazyAliases(
            workspace_root=tmp_path,
        ).resolve_aliases(
            lazy_map,
            pkg_dir=pkg_dir,
        )
        tm.that(lazy_map["c"], eq=("flext_infra.constants", "c"))
        tm.that(lazy_map["r"], eq=("flext_core.result", "r"))


class TestGenerateTypeChecking:
    """Test generate_type_checking function."""

    def test_with_empty_groups(self) -> None:
        """Test with no imports returns header + FlextTypes only."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="if _t.TYPE_CHECKING:")
        tm.that(any("FlextTypes" in line for line in lines), eq=True)

    def test_with_empty_groups_no_flext_types(self) -> None:
        """Test with no imports and no FlextTypes returns empty list."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
        )
        tm.that(lines, eq=[])

    def test_with_single_module(self) -> None:
        """Test with single module."""
        groups = {"module": [("Test", "Test")]}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(" ".join(lines), contains="from module import")

    def test_with_aliased_imports(self) -> None:
        """Test with aliased imports."""
        groups = {"module": [("c", "FlextConstants"), ("m", "FlextModels")]}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        joined = " ".join(lines)
        tm.that(
            joined, contains="from module import FlextConstants as c, FlextModels as m"
        )

    def test_with_long_import_line(self) -> None:
        """Test wraps long import lines."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["module"] = [
            ("VeryLongClassName1", "VeryLongClassName1"),
            ("VeryLongClassName2", "VeryLongClassName2"),
            ("VeryLongClassName3", "VeryLongClassName3"),
        ]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(any("module" in line for line in lines), eq=True)

    def test_with_multiple_modules_spacing(self) -> None:
        """Test blank lines between different top-level package groups."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="")


class TestGenerateFile:
    """Test public lazy-init file generation behavior."""

    def test_with_flext_core_package(self) -> None:
        """Test uses correct lazy import for flext_core."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "flext_core",
        )
        tm.that(
            content,
            contains="from flext_core.lazy import build_lazy_import_map, install_lazy_exports",
        )

    def test_with_other_package(self) -> None:
        """Test uses correct lazy import for non-core packages."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "other_pkg",
        )
        tm.that(
            content,
            contains="from flext_core.lazy import build_lazy_import_map, install_lazy_exports",
        )

    def test_with_inline_constants(self) -> None:
        """Test includes inline constants."""
        exports = ["__version__", "Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants = {"__version__": "1.0.0"}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains='__version__ = "1.0.0"')

    def test_with_eager_runtime_imports(self) -> None:
        """Test version-like exports are imported eagerly at runtime."""
        exports = ["FlextVersion", "__version__"]
        filtered: t.Infra.LazyImportMap = {}
        inline_constants: t.StrMapping = {}
        eager_imports: t.Infra.LazyImportMap = {
            "FlextVersion": ("test_pkg.__version__", "FlextVersion"),
            "__version__": ("test_pkg.__version__", "__version__"),
        }
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            eager_imports=eager_imports,
        )
        tm.that(
            content,
            contains="from test_pkg.__version__ import FlextVersion, __version__",
        )
        tm.that(content, contains="_LAZY_IMPORTS = build_lazy_import_map(")
        tm.that(content, lacks="merge_lazy_imports(")
        tm.that(content, contains="build_lazy_import_map(")
        tm.that(content, contains='        "FlextVersion",')
        tm.that(content, contains='        "__version__",')

    def test_skips_wildcard_runtime_modules_in_type_checking(self) -> None:
        """Test wildcard runtime imports are not duplicated in TYPE_CHECKING."""
        exports = ["VERSION", "__version__", "Test"]
        filtered: t.Infra.LazyImportMap = {
            "VERSION": ("test_pkg.__version__", "VERSION"),
            "__version__": ("test_pkg.__version__", "__version__"),
            "Test": ("test_pkg.models", "Test"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            wildcard_runtime_modules=("test_pkg.__version__",),
        )
        tm.that(content, contains="from test_pkg.__version__ import *")
        tm.that(content, lacks="from test_pkg.__version__ import VERSION")
        tm.that(content, lacks="from test_pkg.__version__ import __version__")

    def test_ignores_docstring_source(self) -> None:
        """Generated __init__.py files should not preserve package docstrings."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, lacks='"""Test module."""')

    def test_has_autogen_header(self) -> None:
        """Test generated file starts with autogen header."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="AUTO-GENERATED")

    def test_has_lazy_imports_with_exports(self) -> None:
        """Test generated file registers exports in _LAZY_IMPORTS."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="install_lazy_exports")
        tm.that(content, contains='"Alpha"')
        tm.that(content, contains='"Beta"')

    def test_typevars_stay_lazy_exports(self) -> None:
        """TypeVar-like exports stay lazy while remaining visible to static analysis."""
        exports = ["FlextTypes", "T", "U"]
        filtered = {
            "FlextTypes": ("test_pkg.typings", "FlextTypes"),
            "T": ("test_pkg.typings", "T"),
            "U": ("test_pkg.typings", "U"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="if _t.TYPE_CHECKING:")
        tm.that(
            content,
            contains="from test_pkg.typings import FlextTypes, T, U",
        )
        tm.that(content, contains='        ".typings": (')
        tm.that(content, contains='            "T",')
        tm.that(content, contains='            "U",')

    def test_root_namespace_emits_static_analysis_hints(self) -> None:
        """Root namespace __init__.py keeps TYPE_CHECKING and __all__."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="if _t.TYPE_CHECKING:")
        tm.that(content, contains="import typing as _t")
        tm.that(content, contains="__all__ = [")
        tm.that(
            content, contains="install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)"
        )

    def test_root_namespace_writes___all___after_lazy_loader(self) -> None:
        """Root namespace places ``__all__`` after ``install_lazy_exports``."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(
            content.rfind("__all__ = [")
            > content.rfind("install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)"),
            eq=True,
        )

    def test_root_namespace_type_checking_uses_source_modules(self) -> None:
        """Root namespace TYPE_CHECKING must target real source modules."""
        exports = ["Alpha", "Beta"]
        filtered = {
            "Alpha": ("test_pkg._constants.base", "Alpha"),
            "Beta": ("test_pkg._models.base", "Beta"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_tc=("test_pkg._constants", "test_pkg._models"),
        )
        tm.that(content, contains="from test_pkg._constants.base import Alpha")
        tm.that(content, contains="from test_pkg._models.base import Beta")
        tm.that(content, lacks="from test_pkg._constants import Alpha")
        tm.that(content, lacks="from test_pkg._models import Beta")

    def test_subpackage_generated_init_includes_package_docstring(self) -> None:
        """Generated subpackage __init__.py files include the package docstring."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha"],
            {"Alpha": ("test_pkg.tools.alpha", "Alpha")},
            {},
            "test_pkg.tools",
        )
        tm.that(content, contains='"""Tools package."""')

    def test_subpackage_keeps_module_entries_in_lazy_imports(self) -> None:
        """Subpackage module entries remain importable through _LAZY_IMPORTS."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["test_base"],
            {"test_base": ("tests.unit._models.test_base", "")},
            {},
            "tests.unit._models",
        )
        tm.that(content, contains='".test_base": ("test_base",)')
        tm.that(content, contains="publish_all=False")
        tm.that(content, lacks="__all__ = [")

    def test_root_namespace_type_checking_skips_module_reexport_names(self) -> None:
        """Root namespace TYPE_CHECKING must omit module/package compatibility names."""
        exports = ["_constants", "api", "constants"]
        filtered = {
            "_constants": ("test_pkg", "_constants"),
            "api": ("test_pkg.api", ""),
            "constants": ("test_pkg.constants", ""),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, lacks="import test_pkg.api as api")
        tm.that(content, lacks="import test_pkg.constants as constants")
        tm.that(content, lacks="from test_pkg import _constants")
        tm.that(content, lacks="from test_pkg import api")
        tm.that(content, lacks="from test_pkg import constants")

    def test_root_namespace_omits_module_and_directory_exports(self) -> None:
        """Root namespace omits compatibility module/directory names entirely."""
        exports = ["Alpha", "_constants", "api", "constants", "tools"]
        filtered = {
            "Alpha": ("test_pkg._utilities.alpha", "Alpha"),
            "_constants": ("test_pkg._constants", ""),
            "api": ("test_pkg.api", ""),
            "constants": ("test_pkg.constants", ""),
            "tools": ("test_pkg.tools", ""),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_lazy=("test_pkg._constants", "test_pkg.tools"),
            child_packages_for_tc=("test_pkg._constants", "test_pkg.tools"),
        )
        tm.that(content, contains='"._utilities.alpha": ("Alpha",)')
        tm.that(content, lacks='"_constants": "test_pkg._constants"')
        tm.that(content, lacks='"api": "test_pkg.api"')
        tm.that(content, lacks='"constants": "test_pkg.constants"')
        tm.that(content, lacks='"tools": "test_pkg.tools"')
        tm.that(content, contains='    "Alpha",')
        tm.that(content, lacks='    "_constants",')
        tm.that(content, lacks='    "api",')
        tm.that(content, lacks='    "constants",')
        tm.that(content, lacks='    "tools",')

    def test_root_namespace_uses_relative_child_package_paths(self) -> None:
        """Root merge list uses relative child package paths for local children."""
        exports = ["Alpha"]
        filtered = {"Alpha": ("test_pkg.models", "Alpha")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_lazy=("test_pkg._constants", "test_pkg.services"),
        )
        tm.that(content, contains='"._constants"')
        tm.that(content, contains='".services"')
        tm.that(content, contains="exclude_names=(")
        tm.that(content, contains="module_name=__name__")
        tm.that(content, lacks='"test_pkg._constants"')
        tm.that(content, lacks='"test_pkg.services"')
        tm.that(content, lacks="_LAZY_IMPORTS.pop(")

    def test_subpackage_omits_static_analysis_hints(self) -> None:
        """Non-root package __init__.py keeps only _LAZY_IMPORTS + lazy loader."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg.transformers",
        )
        tm.that(content, lacks="if _t.TYPE_CHECKING:")
        tm.that(content, lacks="import typing as _t")
        tm.that(content, lacks="__all__ = [")
        tm.that(
            content,
            contains=(
                "install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, "
                "publish_all=False)"
            ),
        )


class TestRunRuffFix:
    """Test public ruff post-processing utility behavior."""

    def test_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handles nonexistent files gracefully."""
        nonexistent = tmp_path / "nonexistent.py"
        u.Infra.run_ruff_fix(nonexistent)

    def test_runs_ruff_check_and_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated files are lint-fixed and formatted."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        u.Infra.run_ruff_fix(generated)
        tm.that(generated.read_text(encoding="utf-8"), eq="__all__ = []\n")

    def test_raises_when_ruff_postprocess_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generator fails when ruff post-processing fails."""
        generated = tmp_path / "__init__.py"
        generated.write_text("def broken(:\n", encoding="utf-8")
        with pytest.raises(ValueError, match="ruff"):
            u.Infra.run_ruff_fix(generated)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
