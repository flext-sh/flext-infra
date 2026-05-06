"""Public API contract tests for flext_infra facades."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import flext_infra as infra_pkg
from tests import t


class TestsFlextInfraPublicApi:
    """Exercise the root public facades as real importable contracts."""

    _ROOT_EXPORTS: t.StrSequence = (
        "FlextInfra",
        "c",
        "infra",
        "m",
        "main",
        "p",
        "s",
        "t",
        "u",
    )
    _WRAPPER_MODULES: t.StrSequence = (
        "flext_infra.__version__",
        "flext_infra.constants",
        "flext_infra.models",
        "flext_infra.protocols",
        "flext_infra.typings",
        "flext_infra.utilities",
    )

    def _reload_public_root(self) -> ModuleType:
        for export_name in self._ROOT_EXPORTS:
            _ = infra_pkg.__dict__.pop(export_name, None)
        for module_name in self._WRAPPER_MODULES:
            _ = sys.modules.pop(module_name, None)
        return importlib.reload(infra_pkg)

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def test_root_public_facades_reload_cleanly(self) -> None:
        root = self._reload_public_root()

        assert root.__title__ == "flext-infra"
        assert root.__version__
        assert root.c.__name__ == "FlextInfraConstants"
        assert root.m.__name__ == "FlextInfraModels"
        assert root.p.__name__ == "FlextInfraProtocols"
        assert root.t.__name__ == "FlextInfraTypes"
        assert root.u.__name__ == "FlextInfraUtilities"
        assert root.s.__name__ == "FlextInfraServiceBase"
        assert root.infra.__class__ is root.FlextInfra
        assert callable(root.main)

    def test_public_facades_expose_infra_namespace(self) -> None:
        root = self._reload_public_root()

        assert hasattr(root.c, "Infra")
        assert hasattr(root.m, "Infra")
        assert hasattr(root.p, "Infra")
        assert hasattr(root.t, "Infra")
        assert hasattr(root.u, "Infra")
        assert hasattr(root.u.Infra, "current_workspace_version")
        assert hasattr(root.u.Infra, "parse_semver")

    def test_public_wrapper_modules_export_expected_aliases(self) -> None:
        wrapper_expectations = (
            ("flext_infra.constants", "c", "FlextInfraConstants"),
            ("flext_infra.models", "m", "FlextInfraModels"),
            ("flext_infra.protocols", "p", "FlextInfraProtocols"),
            ("flext_infra.typings", "t", "FlextInfraTypes"),
            ("flext_infra.utilities", "u", "FlextInfraUtilities"),
        )

        for module_name, alias_name, class_name in wrapper_expectations:
            module = importlib.reload(importlib.import_module(module_name))
            alias = getattr(module, alias_name)

            assert alias.__name__ == class_name

        version_module = importlib.reload(
            importlib.import_module("flext_infra.__version__")
        )
        assert version_module.__version__ == infra_pkg.__version__

    def test_public_runtime_metadata_matches_public_constants(self) -> None:
        root = self._reload_public_root()
        constants = root.u.read_project_constants(
            root.__title__,
            root=self._project_root(),
        )

        assert root.__version__ == constants.PACKAGE_VERSION
        assert root.__license__ == constants.PACKAGE_LICENSE
        assert root.__url__ == constants.PACKAGE_URL
        assert root.__author__ == constants.PACKAGE_AUTHORS[0]
