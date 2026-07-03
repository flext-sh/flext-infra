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
    from flext_core import d as d, e as e, h as h, r as r, x as x
    from flext_infra.api import FlextInfra as FlextInfra, infra as infra
    from flext_infra.base import FlextInfraServiceBase as FlextInfraServiceBase, s as s
    from flext_infra.base_selection import (
        FlextInfraProjectSelectionServiceBase as FlextInfraProjectSelectionServiceBase,
    )
    from flext_infra.cli import FlextInfraCli as FlextInfraCli, main as main
    from flext_infra.constants import FlextInfraConstants as FlextInfraConstants, c as c
    from flext_infra.fixers.base import FlextInfraFixerAdapter as FlextInfraFixerAdapter
    from flext_infra.fixers.gate_fixer import (
        FlextInfraGateFixerAdapter as FlextInfraGateFixerAdapter,
    )
    from flext_infra.fixers.orchestrator import (
        FlextInfraEnforcementFixerOrchestrator as FlextInfraEnforcementFixerOrchestrator,
    )
    from flext_infra.fixers.result import (
        FlextInfraFixersResult as FlextInfraFixersResult,
    )
    from flext_infra.fixers.transformer_fixer import (
        FlextInfraTransformerFixerAdapter as FlextInfraTransformerFixerAdapter,
    )
    from flext_infra.models import FlextInfraModels as FlextInfraModels, m as m
    from flext_infra.protocols import (
        FlextInfraProtocols as FlextInfraProtocols,
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
        p as p,
    )
    from flext_infra.settings import FlextInfraSettings as FlextInfraSettings
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t as t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u as u

_LAZY_IMPORTS = FLEXT_INFRA_LAZY_IMPORTS
_METADATA_EXPORTS = (
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
)
_PUBLIC_EXPORTS = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementFixerOrchestrator",
    "FlextInfraFixerAdapter",
    "FlextInfraFixersResult",
    "FlextInfraGateFixerAdapter",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTransformerFixerAdapter",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    *_METADATA_EXPORTS,
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
_PUBLISHED_NAMES = frozenset({*_LAZY_IMPORTS, *_METADATA_EXPORTS})
_ROOT_EXPORTS_DRIFT_ERROR = "flext_infra root exports drift from FLEXT_INFRA_LAZY_IMPORTS"
if not frozenset(_PUBLIC_EXPORTS) <= _PUBLISHED_NAMES:
    raise RuntimeError(_ROOT_EXPORTS_DRIFT_ERROR)

install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
