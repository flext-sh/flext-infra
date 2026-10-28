# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Import Law. Policy package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._import_law._policy.namespace import (
        FlextInfraUtilitiesImportLawPolicyNamespace,
    )
    from flext_infra._utilities._import_law._policy.publication import (
        FlextInfraUtilitiesImportLawPolicyPublication,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawPolicyNamespace",
    "FlextInfraUtilitiesImportLawPolicyPublication",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesImportLawPolicyNamespace": ".namespace",
        "FlextInfraUtilitiesImportLawPolicyPublication": ".publication",
    }),
    public_exports=__all__,
)
