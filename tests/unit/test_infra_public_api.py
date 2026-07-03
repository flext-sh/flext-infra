"""Public API contract tests for flext_infra facades."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

import flext_infra as infra_pkg
from tests.base import s
from tests.constants import c
from tests.models import m


class TestsFlextInfraPublicApi:
    """Exercise the root public facades as real importable contracts."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def test_root_public_facades_reload_cleanly(
        self,
        infra_public_root: ModuleType,
    ) -> None:
        root = infra_public_root

        assert root.__title__ == "flext-infra"
        assert root.__version__
        assert root.infra.__class__ is root.FlextInfra
        assert callable(root.main)

    @pytest.mark.parametrize(
        ("alias_name", "class_name"),
        c.Tests.INFRA_PUBLIC_ROOT_ALIAS_EXPECTATIONS,
    )
    def test_root_public_facades_export_expected_aliases(
        self,
        infra_public_root: ModuleType,
        alias_name: str,
        class_name: str,
    ) -> None:
        assert getattr(infra_public_root, alias_name).__name__ == class_name

    @pytest.mark.parametrize("alias_name", c.Tests.INFRA_PUBLIC_NAMESPACE_ALIAS_NAMES)
    def test_public_facades_expose_infra_namespace(
        self,
        infra_public_root: ModuleType,
        alias_name: str,
    ) -> None:
        assert hasattr(getattr(infra_public_root, alias_name), "Infra")

    @pytest.mark.parametrize(
        "method_name",
        c.Tests.INFRA_PUBLIC_UTILITY_NAMESPACE_METHODS,
    )
    def test_public_utilities_expose_expected_infra_methods(
        self,
        infra_public_root: ModuleType,
        method_name: str,
    ) -> None:
        assert hasattr(infra_public_root.u.Infra, method_name)

    @pytest.mark.parametrize(
        ("module_name", "alias_name", "class_name"),
        c.Tests.INFRA_PUBLIC_WRAPPER_ALIAS_EXPECTATIONS,
    )
    def test_public_wrapper_modules_export_expected_aliases(
        self,
        module_name: str,
        alias_name: str,
        class_name: str,
    ) -> None:
        module = importlib.reload(importlib.import_module(module_name))
        alias = getattr(module, alias_name)

        assert alias.__name__ == class_name

    def test_public_version_module_matches_package_version(self) -> None:
        version_module = importlib.reload(
            importlib.import_module("flext_infra.__version__")
        )
        assert version_module.__version__ == infra_pkg.__version__

    def test_public_runtime_metadata_matches_public_constants(
        self,
        infra_public_root: ModuleType,
    ) -> None:
        root = infra_public_root
        constants = root.u.read_project_constants(
            root.__title__,
            root=self._project_root(),
        )

        assert root.__version__ == constants.PACKAGE_VERSION
        assert root.__license__ == constants.PACKAGE_LICENSE
        assert root.__url__ == constants.PACKAGE_URL
        assert root.__author__ == constants.PACKAGE_AUTHORS[0]

    def test_test_service_settings_expose_tests_namespace(self) -> None:
        assert isinstance(s.fetch_settings().Tests, m.SettingsValue)
