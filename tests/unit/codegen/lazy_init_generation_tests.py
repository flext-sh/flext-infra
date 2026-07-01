"""Tests for lazy_init code generation: aliases, type checking, file output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import (
    MutableMapping,
)
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as mod
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from tests.typings import t
from tests.utilities import u


class TestGenerateTypeChecking:
    """Test generate_type_checking function."""

    def test_with_empty_groups(self) -> None:
        """Test with no imports returns header + FlextTypes only."""
        groups: t.MappingKV[str, t.StrPairSequence] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="if TYPE_CHECKING:")
        tm.that(any("FlextTypes" in line for line in lines), eq=True)

    def test_with_empty_groups_no_flext_types(self) -> None:
        """Test with no imports and no FlextTypes returns empty list."""
        groups: t.MappingKV[str, t.StrPairSequence] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
        )
        tm.that(lines, empty=True)

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
        groups: MutableMapping[str, t.StrPairSequence] = defaultdict(list)
        groups["module"] = [
            ("VeryLongClassName1", "VeryLongClassName1"),
            ("VeryLongClassName2", "VeryLongClassName2"),
            ("VeryLongClassName3", "VeryLongClassName3"),
        ]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(any("module" in line for line in lines), eq=True)

    def test_with_multiple_modules(self) -> None:
        """Test multiple type-checking imports are emitted."""
        groups: MutableMapping[str, t.StrPairSequence] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        joined = "\n".join(lines)
        tm.that(joined, contains="from alpha_pkg.module import Test1")
        tm.that(joined, contains="from beta_pkg.module import Test2")

    def test_typing_stub_omits_all_when_disabled(self) -> None:
        """Non-public typing stubs keep static exports without ``__all__``."""
        export_name = "TestsFlextInfraIntegrationRefactorNestingIdempotency"
        content = FlextInfraCodegenGeneration.generate_typing_stub(
            (export_name,),
            {export_name: ("tests.sample", export_name)},
            {},
            include_all=False,
        )
        tm.that(content, contains=f"{export_name} as {export_name}")
        tm.that(content, lacks="__all__ = (")

    def test_typing_stub_rejects_long_public_all_entries(self) -> None:
        """Public typing stubs fail loud on invalid long ``__all__`` literals."""
        export_name = "TestsFlextInfraIntegrationRefactorNestingIdempotency"
        with pytest.raises(ValueError, match="public stub export exceeds"):
            FlextInfraCodegenGeneration.generate_typing_stub(
                (export_name,),
                {export_name: ("tests.sample", export_name)},
                {},
            )

    def test_flext_core_root_typing_stub_uses_public_facade_contract(self) -> None:
        content = FlextInfraCodegenGeneration.generate_flext_core_root_typing_stub()

        tm.that(content, contains="from flext_core._root_typing_parts.facades import (")
        tm.that(content, contains="FlextConstants as FlextConstants,")
        tm.that(content, contains="c as c,")
        tm.that(content, contains="FlextSettingsBase as FlextSettingsBase")
        tm.that(content, contains='    "FlextUtilities",')
        tm.that(content, contains='    "u",')
        tm.that(content, lacks="from flext_core._root_typing import")
        tm.that(content, lacks="FlextModelsPydantic as FlextModelsPydantic")
        tm.that(content, lacks='    "FlextModelsPydantic",')
        tm.that(content, lacks="build_lazy_import_map")


class TestLazyInitPlannerCollision:
    """Test lazy-init export collision classification."""

    def test_mro_part_siblings_are_intentional_reexports(self) -> None:
        """MRO implementation parts share one logical owner by design."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                (
                    "flext_cli._models._base_parts.flextclimodelsbase_part_01",
                    "FlextCliModelsBase",
                ),
                (
                    "flext_cli._models._base_parts.flextclimodelsbase_part_02",
                    "FlextCliModelsBase",
                ),
            ),
            eq=True,
        )

    def test_mro_part_facade_is_intentional_reexport(self) -> None:
        """A canonical facade module may re-export its private MRO part family."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                ("flext_cli._utilities.files", "FlextCliUtilitiesFiles"),
                (
                    "flext_cli._utilities._files_parts.flextcliutilitiesfiles_part_04",
                    "FlextCliUtilitiesFiles",
                ),
            ),
            eq=True,
        )

    def test_same_package_part_modules_are_intentional_reexports(self) -> None:
        """Generated split test modules share one logical exported owner."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                (
                    "tests.unit._cases.test_cli_service.testsflextcliservice_part_01",
                    "TestsFlextCliService",
                ),
                (
                    "tests.unit._cases.test_cli_service.testsflextcliservice_part_02",
                    "TestsFlextCliService",
                ),
            ),
            eq=True,
        )

    def test_private_parts_facade_is_intentional_reexport(self) -> None:
        """A facade may re-export implementation modules from a private parts family."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                ("flext_tests._fixtures.enforcement", "active_rules"),
                (
                    "flext_tests._fixtures._enforcement_parts.config",
                    "active_rules",
                ),
            ),
            eq=True,
        )

    def test_root_facade_private_package_parts_are_intentional_reexports(self) -> None:
        """A root facade may expose its private implementation package owner."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                ("flext_tests.validator", "FlextTestsValidator"),
                (
                    "flext_tests._validator._orchestration_parts.validator_part_02",
                    "FlextTestsValidator",
                ),
            ),
            eq=True,
        )

    def test_root_typing_parts_are_intentional_reexports(self) -> None:
        """Generated root typing parts aggregate canonical source owners."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                ("flext_core._constants.cqrs", "FlextConstantsCqrs"),
                ("flext_core._root_typing_parts.core", "FlextConstantsCqrs"),
            ),
            eq=True,
        )

    def test_unrelated_same_name_exports_are_not_intentional_reexports(self) -> None:
        """Unrelated modules exporting the same name still count as collisions."""
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_intentional_reexport(
                ("demo.alpha", "DemoService"),
                ("demo.beta", "DemoService"),
            ),
            eq=False,
        )


class TestGenerateFile:
    """Test public lazy-init file generation behavior."""

    def test_root_public_contract_exports_read_exports_module(
        self,
        tmp_path: Path,
    ) -> None:
        """Root planner reads the package-level frozen public ABI contract."""
        exports_file = tmp_path / "_exports.py"
        exports_file.write_text(
            'DEMO_PUBLIC_EXPORTS: tuple[str, ...] = ("DemoService", "c")\n',
            encoding="utf-8",
        )
        tm.that(
            FlextInfraCodegenLazyInitPlanner._root_public_contract_exports(tmp_path),
            eq=frozenset({"DemoService", "c"}),
        )

    def test_root_public_contract_exports_allow_child_service(self) -> None:
        """Explicit public root ABI keeps child-package service exports published."""
        lazy_map: t.LazyAliasMap = {
            "DemoService": ("demo_pkg.services.demo", "DemoService"),
        }
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_public_root_export(
                "DemoService",
                lazy_map,
                root_pkg="demo_pkg",
                root_namespace_files=(),
                explicit_public_exports=frozenset({"DemoService"}),
            ),
            eq=True,
        )
        tm.that(
            FlextInfraCodegenLazyInitPlanner._is_public_root_export(
                "DemoService",
                lazy_map,
                root_pkg="demo_pkg",
                root_namespace_files=(),
            ),
            eq=False,
        )

    def test_with_flext_core_package(self) -> None:
        """flext_core root uses its canonical root export map."""
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
        tm.that(content, contains="from flext_core._root_exports import (")
        tm.that(content, contains="ROOT_LAZY_MODULES")
        tm.that(content, contains="public_exports=ROOT_ALL")
        tm.that(content, lacks='        "Test",')

    def test_lazy_parts_bootstrap_uses_direct_imports(self) -> None:
        """The lazy runtime bootstrap package cannot import flext_core.lazy."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["FlextLazy", "LazyImportDict"],
            {
                "FlextLazy": (
                    "flext_core._lazy_parts.flextlazy_part_02",
                    "FlextLazy",
                ),
                "LazyImportDict": (
                    "flext_core._lazy_parts.flextlazy_part_01",
                    "LazyImportDict",
                ),
            },
            {},
            "flext_core._lazy_parts",
        )
        tm.that(
            content,
            contains=(
                "from flext_core._lazy_parts.flextlazy_part_01 import LazyImportDict"
            ),
        )
        tm.that(content, contains="from __future__ import annotations")
        tm.that(
            content,
            contains="from flext_core._lazy_parts.flextlazy_part_02 import FlextLazy",
        )
        tm.that(content, contains="__all__: list[str] = [")
        tm.that(content, lacks="from flext_core.lazy")
        tm.that(content, lacks="install_lazy_exports")

    def test_typings_bootstrap_uses_direct_imports(self) -> None:
        """The typing package is loaded by lazy bootstrap and cannot import it."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["FlextTypesLazy", "FlextTypingBase"],
            {
                "FlextTypesLazy": (
                    "flext_core._typings.lazy",
                    "FlextTypesLazy",
                ),
                "FlextTypingBase": (
                    "flext_core._typings.base",
                    "FlextTypingBase",
                ),
            },
            {},
            "flext_core._typings",
        )
        tm.that(content, contains="from flext_core._typings.lazy import FlextTypesLazy")
        tm.that(content, contains="from __future__ import annotations")
        tm.that(content, contains="__all__: list[str] = [")
        tm.that(content, lacks="FlextTypingBase")
        tm.that(content, lacks="from flext_core._typings.base")
        tm.that(content, lacks="from flext_core.lazy")
        tm.that(content, lacks="install_lazy_exports")

    def test_flext_core_packages_do_not_eager_merge_child_packages(self) -> None:
        """flext_core bootstraps from explicit lazy maps without child imports."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["FlextConstantsEnforcementEnums"],
            {
                "FlextConstantsEnforcementEnums": (
                    "flext_core._constants._enforcement_parts.flextconstantsenforcement_part_01",
                    "FlextConstantsEnforcementEnums",
                ),
            },
            {},
            "flext_core._constants",
            child_packages_for_lazy=("flext_core._constants._enforcement_parts",),
        )
        tm.that(content, contains="build_lazy_import_map(")
        tm.that(
            content, contains='"._enforcement_parts.flextconstantsenforcement_part_01"'
        )
        tm.that(content, lacks="merge_lazy_imports(")
        tm.that(content, lacks='("._enforcement_parts",)')

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

    def test_with_child_packages_uses_lazy_module_merge_imports(self) -> None:
        """Merged lazy imports must import helpers from flext_core.lazy."""
        exports = ["Test"]
        filtered = {"Test": ("other_pkg.module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "other_pkg",
            child_packages_for_lazy=("other_pkg.services",),
        )
        tm.that(
            content,
            contains="from flext_core.lazy import (",
        )
        tm.that(content, contains="merge_lazy_imports,")

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
        filtered: t.LazyAliasMap = {}
        inline_constants: t.StrMapping = {}
        eager_imports: t.LazyAliasMap = {
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
        tm.that(content, contains="__all__: tuple[str, ...] = (")
        tm.that(content, contains='    "FlextVersion",')
        tm.that(content, contains='    "__version__",')
        tm.that(content, contains="public_exports=__all__")

    def test_skips_wildcard_runtime_modules_in_type_checking(self) -> None:
        """Test wildcard runtime imports are not duplicated in TYPE_CHECKING."""
        exports = ["VERSION", "__version__", "Test"]
        filtered: t.LazyAliasMap = {
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
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(
            content,
            contains=(
                "from test_pkg.typings import FlextTypes as FlextTypes, T as T, U as U"
            ),
        )
        tm.that(content, contains='        ".typings": (')
        tm.that(content, contains='            "T",')
        tm.that(content, contains='            "U",')

    def test_root_namespace_emits_static_analysis_hints(self) -> None:
        """Root namespace keeps TYPE_CHECKING and explicit public exports."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="from typing import TYPE_CHECKING")
        tm.that(content, contains="install_lazy_exports(")
        tm.that(content, contains="__all__: tuple[str, ...] = (")
        tm.that(content, contains='    "Alpha",')
        tm.that(content, contains='    "Beta",')
        tm.that(content, contains="public_exports=__all__")

    def test_root_namespace_passes_public_exports_to_lazy_loader(self) -> None:
        """Root namespace exposes lazy-loader and static __all__ contracts."""
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
            content.rfind("public_exports=__all__") > content.rfind("_LAZY_IMPORTS"),
            eq=True,
        )
        tm.that(content, contains="__all__: tuple[str, ...] = (")

    def test_root_namespace_public_exports_exclude_private_implementation(self) -> None:
        """Root namespace keeps private implementation names out of public exports."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha", "Beta"],
            {
                "Alpha": ("test_pkg._internal.alpha", "Alpha"),
                "Beta": ("test_pkg.public.beta", "Beta"),
            },
            {},
            "test_pkg",
        )
        tm.that(content, contains='"._internal.alpha": ("Alpha",)')
        tm.that(content, lacks="from test_pkg._internal.alpha import Alpha")
        tm.that(content, contains='".public.beta": ("Beta",)')
        tm.that(content, contains="from test_pkg.public.beta import Beta")
        public_exports = content[content.index("__all__:") :]
        tm.that(public_exports, lacks='    "Alpha",')
        tm.that(public_exports, contains='    "Beta",')

    def test_root_namespace_type_checking_uses_source_modules(self) -> None:
        """Root namespace TYPE_CHECKING must target real source modules."""
        exports = ["Alpha", "Beta"]
        filtered = {
            "Alpha": ("test_pkg._constants.base", "Alpha"),
            "Beta": ("test_pkg.models.base", "Beta"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="from test_pkg._constants.base import Alpha")
        tm.that(content, contains="from test_pkg.models.base import Beta")
        tm.that(content, lacks="from test_pkg._constants import Alpha")
        tm.that(content, lacks="from test_pkg.models import Beta")

    def test_root_namespace_normalizes_private_local_module_targets(self) -> None:
        """Root namespace never emits unqualified private-package imports."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha", "Beta"],
            {
                "Alpha": ("_constants.base", "Alpha"),
                "Beta": ("models.base", "Beta"),
            },
            {},
            "test_pkg",
        )
        tm.that(content, contains="from test_pkg._constants.base import Alpha")
        tm.that(content, contains="from test_pkg.models.base import Beta")
        tm.that(content, contains='"._constants.base": ("Alpha",)')
        tm.that(content, contains='".models.base": ("Beta",)')
        tm.that(content, lacks="from _constants")
        tm.that(content, lacks="from models")
        tm.that(content, lacks='"_constants.base"')
        tm.that(content, lacks='"models.base"')

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
            {"test_base": ("tests.unit.models.test_base", "")},
            {},
            "tests.unit.models",
        )
        tm.that(content, contains='".test_base": ("test_base",)')
        tm.that(content, contains="publish_all=False")
        tm.that(content, lacks="__all__: list[str] = [")

    def test_subpackage_omits_static_analysis_hints(self) -> None:
        """Subpackage __init__.py keeps lazy runtime without static hints."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["ExamplesFlextModelsEx00"],
            {
                "ExamplesFlextModelsEx00": (
                    "examples.models.ex00",
                    "ExamplesFlextModelsEx00",
                ),
            },
            {},
            "examples.models",
        )
        tm.that(content, contains='".ex00": ("ExamplesFlextModelsEx00",)')
        tm.that(content, lacks="if TYPE_CHECKING:")
        tm.that(content, lacks="from typing import TYPE_CHECKING")
        tm.that(content, lacks="from examples.models.ex00 import")
        tm.that(content, lacks="from models")

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

    def test_root_namespace_preserves_alias_hierarchy_order(self) -> None:
        """Root namespace keeps alias ordering from the resolved export hierarchy."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["FlextDemoConstants", "FlextDemoModels", "c", "m", "p", "t", "u", "r"],
            {
                "FlextDemoConstants": ("test_pkg.constants", "FlextDemoConstants"),
                "FlextDemoModels": ("test_pkg.models", "FlextDemoModels"),
                "c": ("test_pkg.constants", "c"),
                "m": ("test_pkg.models", "m"),
                "p": ("flext_core", "p"),
                "t": ("test_pkg.typings", "t"),
                "u": ("test_pkg.utilities", "u"),
                "r": ("flext_core", "r"),
            },
            {},
            "test_pkg",
        )
        all_block_start = content.index("__all__:")
        all_block = content[all_block_start:]
        alias_positions = tuple(
            all_block.index(f'    "{alias}",')
            for alias in ("c", "m", "p", "r", "t", "u")
        )
        tm.that(alias_positions == tuple(sorted(alias_positions)), eq=True)

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
        )
        tm.that(content, contains='"._utilities.alpha": ("Alpha",)')
        tm.that(content, lacks='"_constants": "test_pkg._constants"')
        tm.that(content, lacks='"api": "test_pkg.api"')
        tm.that(content, lacks='"constants": "test_pkg.constants"')
        tm.that(content, lacks='"tools": "test_pkg.tools"')
        tm.that(content, contains="__all__: tuple[str, ...] = (")
        tm.that(content, contains="public_exports=__all__")
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

    def test_subpackage_keeps_lazy_exports_without_static_hints(self) -> None:
        """Non-root package __init__.py keeps lazy runtime without static hints."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg.transformers",
        )
        tm.that(content, lacks="if TYPE_CHECKING:")
        tm.that(content, lacks="from typing import TYPE_CHECKING")
        tm.that(content, lacks="from mod import Alpha as Alpha")
        tm.that(content, lacks="__all__: tuple[str, ...] = (")
        tm.that(
            content,
            contains="publish_all=False,",
        )

    def test_tests_root_is_not_public_abi(self) -> None:
        """Consumer test root keeps lazy exports without public ABI."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha", "t"],
            {"Alpha": ("tests.alpha", "Alpha"), "t": ("flext_tests", "t")},
            {},
            "tests",
        )
        tm.that(content, contains='".alpha": ("Alpha",)')
        tm.that(content, lacks="public_exports=(")
        tm.that(content, contains="if TYPE_CHECKING:")
        tm.that(content, contains="from flext_tests import t as t")
        tm.that(
            content,
            contains="publish_all=False,",
        )


class TestRunRuffFix:
    """Test public ruff post-processing utility behavior."""

    def test_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handles nonexistent files gracefully."""
        nonexistent = tmp_path / "nonexistent.py"
        _ = u.Infra.run_ruff_fix(nonexistent)

    def test_runs_ruff_check_and_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated files are lint-fixed and formatted."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        result = u.Infra.run_ruff_fix(generated)
        tm.that(result.success, eq=True)
        tm.that(generated.read_text(encoding="utf-8"), eq="__all__ = []\n")

    def test_preserves_stub_all_literal_strings(
        self,
        tmp_path: Path,
    ) -> None:
        """Typing stubs keep literal ``__all__`` names after post-processing."""
        generated = tmp_path / "__init__.pyi"
        export_name = "TestsFlextInfraRootExportContract"
        generated.write_text(
            f"from tests.sample import {export_name} as {export_name}\n"
            "__all__ = (\n"
            f'    "{export_name}",\n'
            ")\n",
            encoding="utf-8",
        )
        result = u.Infra.run_ruff_fix(generated)
        content = generated.read_text(encoding="utf-8")
        tm.that(result.success, eq=True)
        tm.that(content, contains=f'"{export_name}"')
        tm.that(content, lacks="    ...,")

    def test_raises_when_ruff_postprocess_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Ruff post-processing failure is surfaced via ``r.fail``."""
        generated = tmp_path / "__init__.py"
        generated.write_text("def broken(:\n", encoding="utf-8")
        result = u.Infra.run_ruff_fix(generated)
        tm.that(result.failure, eq=True)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
