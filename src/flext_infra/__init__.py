# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports
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
from flext_infra._constants._exports import FLEXT_INFRA_LAZY_IMPORTS

if TYPE_CHECKING:
    from flext_core._root_typing_parts.facades import (
        d as d,
        e as e,
        h as h,
        r as r,
        x as x,
    )
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
    from flext_infra.protocols import FlextInfraProtocols as FlextInfraProtocols, p as p
    from flext_infra.settings import FlextInfraSettings as FlextInfraSettings
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t as t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u as u


_LAZY_IMPORTS = FLEXT_INFRA_LAZY_IMPORTS


_EAGER_EXPORTS = (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)


_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementPytestPlugin",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "basemk",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
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
    "t",
    "u",
    "x",
)

__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementPytestPlugin",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
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
    "t",
    "u",
    "x",
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
