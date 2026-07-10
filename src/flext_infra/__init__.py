# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)
from flext_infra.__version__ import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)

if TYPE_CHECKING:
    from flext_cli import d as d, e as e, h as h, r as r, x as x
    from flext_infra import basemk
    from flext_infra._fixtures.enforcement import (
        FlextInfraEnforcementPytestPlugin as FlextInfraEnforcementPytestPlugin,
    )
    from flext_infra.api import FlextInfra as FlextInfra, infra as infra
    from flext_infra.base import FlextInfraServiceBase as FlextInfraServiceBase, s as s
    from flext_infra.base_selection import (
        FlextInfraProjectSelectionServiceBase as FlextInfraProjectSelectionServiceBase,
    )
    from flext_infra.cli import FlextInfraCli as FlextInfraCli, main as main
    from flext_infra.constants import FlextInfraConstants as FlextInfraConstants, c as c
    from flext_infra.models import FlextInfraModels as FlextInfraModels, m as m
    from flext_infra.protocols import (
        FlextInfraProtocols as FlextInfraProtocols,
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
        p as p,
    )
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t as t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u as u
_LAZY_IMPORTS = merge_lazy_imports(
    ("._enforcement",),
    build_lazy_import_map(
        {
            "._settings": ("FlextInfraSettings", "settings"),
            "._enforcement.collection_base": (
                "FlextInfraEnforcementCollectionBase",
                "FlextInfraEnforcementEvaluation",
            ),
            "._enforcement.collection_sources": (
                "FlextInfraEnforcementSourceCollectors",
            ),
            "._enforcement.collection_tests": ("FlextInfraEnforcementTestsCollector",),
            "._enforcement.engine": ("FlextInfraEnforcementEngine",),
            "._enforcement.metadata": ("FlextInfraEnforcementMetadata",),
            "._enforcement.selection": ("FlextInfraEnforcementSelection",),
            "._fixtures.enforcement": ("FlextInfraEnforcementPytestPlugin",),
            ".api": (
                "FlextInfra",
                "infra",
            ),
            ".base": (
                "FlextInfraServiceBase",
                "s",
            ),
            ".base_selection": ("FlextInfraProjectSelectionServiceBase",),
            ".cli": (
                "FlextInfraCli",
                "main",
            ),
            ".constants": (
                "FlextInfraConstants",
                "c",
            ),
            ".models": (
                "FlextInfraModels",
                "m",
            ),
            ".protocols": (
                "FlextInfraProtocols",
                "FlextInfraProtocolsBase",
                "p",
            ),
            ".typings": (
                "FlextInfraTypes",
                "t",
            ),
            ".utilities": (
                "FlextInfraUtilities",
                "u",
            ),
            "flext_cli": (
                "d",
                "e",
                "h",
                "r",
                "x",
            ),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name=__name__,
)


__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementPytestPlugin",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "basemk",
    "c",
    "d",
    "e",
    "h",
    "infra",
    "m",
    "main",
    "p",
    "r",
    "s",
    "settings",
    "t",
    "u",
    "x",
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=__all__,
)
