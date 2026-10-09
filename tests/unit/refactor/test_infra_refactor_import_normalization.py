"""Behavior of the FLEXT import-law engine on real package trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import m
from flext_infra.refactor import FlextInfraImportNormalization
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalization:
    """Each import-law rule observed through ``normalize_source``."""

    @classmethod
    def test_facade_dependency_retains_its_external_provider(
        cls,
        tmp_path: Path,
    ) -> None:
        """The facade still loads a provider imported by one of its MRO parts."""
        project, package = cls._project(tmp_path)
        module = package / "provider_boundary.py"
        source = (
            "from flext_cli import u\n\n"
            "class Provider:\n"
            "    ADAPTER = u.type_adapter(str)\n"
        )
        module.write_text(source, encoding="utf-8")
        (package / "utilities.py").write_text(
            "from demo_pkg.provider_boundary import Provider\n\n"
            "class DemoUtilities(Provider):\n"
            "    pass\n\n"
            "u = DemoUtilities\n"
            "__all__ = ['u']\n",
            encoding="utf-8",
        )
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg import u\nassert u.ADAPTER.validate_python('x') == "
                        "'x'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @classmethod
    @pytest.mark.parametrize(
        "directory",
        tuple(family.directory for family in u.Infra.facade_families().values()),
    )
    def test_family_retains_external_model_and_utility_providers(
        cls,
        tmp_path: Path,
        directory: str,
    ) -> None:
        """The rewritten family still imports and validates with its real provider."""
        project, package = cls._project(tmp_path)
        family = package / directory
        family.mkdir(exist_ok=True)
        (family / "__init__.py").touch(exist_ok=True)
        module = family / "provider_boundary.py"
        source = (
            "from flext_cli import m, u\n\n"
            "ADAPTER: m.TypeAdapter[str] = u.type_adapter(str)\n"
        )
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source, encoding="utf-8"
        )
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from demo_pkg.{directory}.provider_boundary import ADAPTER; "
                        "assert ADAPTER.validate_python('native-value') == 'native-value'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    def _lazy_init(package_dir: Path, exports: t.StrMapping) -> None:
        """Write one generated-shape lazy ``__init__`` publishing ``exports``."""
        package_dir.mkdir(parents=True, exist_ok=True)
        entries = "".join(
            f"    {name!r}: {module!r},\n" for name, module in exports.items()
        )
        (package_dir / "__init__.py").write_text(
            "from flext_core import install_lazy_exports\n"
            "\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    {\n"
            f"{entries}"
            "    },\n"
            ")\n",
            encoding="utf-8",
        )

    @classmethod
    def _project(cls, tmp_path: Path) -> tuple[Path, Path]:
        """Materialize ``demo_pkg`` with a lazy root and lazy family inits.

        Returns:
            The project root and the package directory.

        """
        project = tmp_path / "project"
        package = u.Tests.src_package(
            project,
            "demo_pkg",
            pyproject="[project]\nname='demo'\n",
        )
        cls._lazy_init(
            package,
            {
                "c": ".constants",
                "t": ".typings",
                "m": ".models",
                "u": ".utilities",
                "r": "flext_core",
                "DemoApi": ".api",
            },
        )
        cls._lazy_init(package / "_utilities", {"DemoHelper": ".helper"})
        cls._lazy_init(package / "_models", {"DemoRecord": ".record"})
        cls._lazy_init(package / "services", {"DemoRunner": ".runner"})
        return project, package

    @staticmethod
    def _normalize(project: Path, file_path: Path, source: str) -> str:
        """Normalize one module and require a rewrite.

        Returns:
            The rewritten source.

        """
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=file_path,
            source=source,
        )
        tm.that(normalized is not None, eq=True)
        return normalized or ""

    @classmethod
    def test_forward_inline_import_is_hoisted(cls, tmp_path: Path) -> None:
        """A function-body import of a lower layer moves to the module block."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "import json\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    from demo_pkg._utilities import DemoHelper\n"
            "\n"
            "    return json.dumps(DemoHelper())\n",
        )

        tm.that(
            normalized, has="import json\nfrom demo_pkg._utilities import DemoHelper\n"
        )
        tm.that(normalized, lacks="    from demo_pkg._utilities import DemoHelper")

    @classmethod
    def test_reverse_runtime_import_keeps_its_place(cls, tmp_path: Path) -> None:
        """A lower layer reading a higher layer at runtime keeps the import inline."""
        project, package = cls._project(tmp_path)
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_utilities" / "bridge.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "\n"
                "def run() -> object:\n"
                "    from demo_pkg import DemoApi\n"
                "\n"
                "    return DemoApi()\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_reverse_typing_import_moves_under_type_checking(
        cls,
        tmp_path: Path,
    ) -> None:
        """A reverse import read only in annotations moves under TYPE_CHECKING."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "_models" / "report.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg.services import DemoRunner\n"
            "\n"
            "\n"
            "def describe(runner: DemoRunner) -> str:\n"
            "    return 'runner'\n",
        )

        tm.that(normalized, has="from typing import TYPE_CHECKING\n")
        tm.that(
            normalized,
            has="if TYPE_CHECKING:\n    from demo_pkg.services import DemoRunner\n",
        )

    @classmethod
    def test_foreign_root_alias_binds_through_own_root(cls, tmp_path: Path) -> None:
        """A root alias imported from another namespace binds through its own root."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "from flext_core import r\n"
            "from demo_pkg.typings import t\n"
            "\n"
            "\n"
            "def run(value: t.StrSequence) -> object:\n"
            "    return r.ok(value)\n",
        )

        tm.that(normalized, has="from demo_pkg import r\n")
        tm.that(normalized, has="from demo_pkg import t\n")
        tm.that(normalized, lacks="from flext_core import r")

    @classmethod
    def test_family_keeps_upstream_own_letter(cls, tmp_path: Path) -> None:
        """A family package keeps its own letter from the upstream namespace."""
        project, package = cls._project(tmp_path)
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_models" / "record.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "from flext_cli import m\n"
                "\n"
                "\n"
                "class DemoRecord(m.ContractModel):\n"
                "    name: str\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_leaf_object_routes_through_lazy_package(cls, tmp_path: Path) -> None:
        """A leaf-module object binds through the package that publishes it."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg._models.record import DemoRecord\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    return DemoRecord\n",
        )

        tm.that(normalized, has="from demo_pkg._models import DemoRecord\n")
        tm.that(normalized, lacks="demo_pkg._models.record")

    @classmethod
    def test_tier_long_letter_forms_collapse_to_tier_root(
        cls,
        tmp_path: Path,
    ) -> None:
        """The operator's flext-auth shape: tier letters and helpers bind lazily."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(
            tier,
            {"c": ".constants", "m": ".models", "u": ".utilities"},
        )
        cls._lazy_init(
            tier / "unit" / "api_cases",
            {"DemoApiTestDataHelper": ".support"},
        )
        normalized = cls._normalize(
            project,
            tier / "unit" / "test_api.py",
            "from __future__ import annotations\n"
            "\n"
            "from tests.constants import TestsDemoConstants as c\n"
            "from tests.unit.api_cases.support import DemoApiTestDataHelper\n"
            "from tests.utilities import TestsDemoUtilities as u\n"
            "from demo_pkg import DemoApi, m\n"
            "\n"
            "\n"
            "def test_api() -> None:\n"
            "    assert DemoApi(c, m, u, DemoApiTestDataHelper)\n",
        )

        tm.that(normalized, has="from tests import c\n")
        tm.that(normalized, has="from tests import u\n")
        tm.that(normalized, has="from tests import m\n")
        tm.that(normalized, has="from demo_pkg import DemoApi\n")
        tm.that(
            normalized,
            has="from tests.unit.api_cases import DemoApiTestDataHelper\n",
        )
        tm.that(normalized, lacks="TestsDemoConstants")
        tm.that(normalized, lacks="TestsDemoUtilities")

    @classmethod
    def test_settings_config_modules_keep_direct_imports(
        cls,
        tmp_path: Path,
    ) -> None:
        """Settings/config modules import each other directly, never via a root."""
        project, package = cls._project(tmp_path)
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_config.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "from flext_core import r\n"
                "from demo_pkg._settings import DemoSettings\n"
                "from demo_pkg._models.base import DemoModelsBase\n"
                "\n"
                "\n"
                "class DemoConfig(DemoModelsBase):\n"
                "    settings: DemoSettings\n"
                "    result: r[str]\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_internal_tier_alias_binds_through_tier_root(cls, tmp_path: Path) -> None:
        """An internal tier imports root aliases from its own root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"r": "flext_tests", "c": ".constants"})
        normalized = cls._normalize(
            project,
            tier / "unit" / "test_demo.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg import c\n"
            "from flext_tests import r\n"
            "\n"
            "\n"
            "def test_demo() -> None:\n"
            "    assert r.ok(c)\n",
        )

        tm.that(normalized, has="from tests import c\n")
        tm.that(normalized, has="from tests import r\n")

    @classmethod
    def test_relative_import_becomes_absolute(cls, tmp_path: Path) -> None:
        """A relative own-package import becomes its absolute form."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "_utilities" / "extra.py",
            "from __future__ import annotations\n"
            "\n"
            "from .helper import DemoHelper\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    return DemoHelper\n",
        )

        tm.that(normalized, has="from demo_pkg._utilities import DemoHelper\n")
        tm.that(normalized, lacks="from .helper")

    @classmethod
    def test_import_guard_becomes_plain_import(cls, tmp_path: Path) -> None:
        """A ``try/except ImportError`` guard becomes its plain imports."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "try:\n"
            "    import json\n"
            "except ImportError:\n"
            "    json = None\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    return json.dumps({})\n",
        )

        tm.that(normalized, lacks="except ImportError")
        tm.that(normalized, has="\nimport json\n")

    @classmethod
    def test_normalization_is_idempotent(cls, tmp_path: Path) -> None:
        """A second pass over the normalized module changes nothing."""
        project, package = cls._project(tmp_path)
        target = package / "services" / "worker.py"
        first = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from flext_core import r\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    from demo_pkg._models.record import DemoRecord\n"
            "\n"
            "    return r.ok(DemoRecord)\n",
        )

        second = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=target,
            source=first,
        )

        tm.that(second, eq=None)
