# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)
from flext_infra.__version__ import (
    __author__ as __author__,
    __author_email__ as __author_email__,
    __description__ as __description__,
    __license__ as __license__,
    __title__ as __title__,
    __url__ as __url__,
    __version__ as __version__,
    __version_info__ as __version_info__,
)

if TYPE_CHECKING:
    from flext_cli import d as d, e as e, h as h, r as r, x as x

    from flext_infra import basemk as basemk
    from flext_infra._config import config as config
    from flext_infra._settings import settings as settings
    from flext_infra.api import FlextInfra as FlextInfra, infra as infra
    from flext_infra.base import FlextInfraServiceBase as FlextInfraServiceBase, s as s
    from flext_infra.base_selection import (
        FlextInfraProjectSelectionServiceBase as FlextInfraProjectSelectionServiceBase,
    )
    from flext_infra.cli import (
        FlextInfraCli as FlextInfraCli,
        docs_main as docs_main,
        main as main,
    )
    from flext_infra.constants import FlextInfraConstants as FlextInfraConstants, c as c
    from flext_infra.models import FlextInfraModels as FlextInfraModels, m as m
    from flext_infra.protocols import (
        FlextInfraProtocols as FlextInfraProtocols,
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
        p as p,
    )
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t as t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u as u

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
