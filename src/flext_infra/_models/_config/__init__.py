# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models. Config package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models._config.base import FlextInfraConfigModels
    from flext_infra._models._config.external_cache import (
        FlextInfraExternalCacheDirectorySpec,
    )
    from flext_infra._models._config.make_docs import FlextInfraConfigModelsMakeDocs
    from flext_infra._models._config.root import FlextInfraConfigModelsRoot


__all__: tuple[str, ...] = (
    "FlextInfraConfigModels",
    "FlextInfraConfigModelsMakeDocs",
    "FlextInfraConfigModelsRoot",
    "FlextInfraExternalCacheDirectorySpec",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraConfigModels": ".base",
        "FlextInfraConfigModelsMakeDocs": ".make_docs",
        "FlextInfraConfigModelsRoot": ".root",
        "FlextInfraExternalCacheDirectorySpec": ".external_cache",
    }),
    public_exports=__all__,
)
