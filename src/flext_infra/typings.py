# AUTO-GENERATED FILE — Regenerate with: make gen
"""Type aliases for flext-infra.

Re-exports and extends flext-cli typings for infrastructure services.
Infra-specific type aliases live inside ``FlextInfraTypes`` so they are
accessed via ``t.Infra.Payload``, ``t.JsonMapping``, etc.

Non-recursive aliases use ``type X = ...`` (PEP 695 Python 3.13+ syntax).
See AGENTS.md §3 AXIOMATIC rule.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliTypes

from flext_infra._typings import (
    FlextInfraTypesAdapters,
    FlextInfraTypesBase,
    FlextInfraTypesCollections,
    FlextInfraTypesPytest,
    FlextInfraTypesRope,
    FlextInfraTypesRopeNative,
)


class FlextInfraTypes(FlextCliTypes):
    """Type namespace for flext-infra; extends FlextTypes via FLEXT.

    Infra-specific types are nested under the ``Infra`` inner class to
    keep the namespace explicit (``t.Infra.Payload``, ``t.JsonMapping``).
    Parent types (``t.Scalar``, ``Mapping[str, str]``, etc.) are inherited
    transparently from ``FlextTypes`` via FLEXT.
    """

    Container = FlextInfraTypesCollections.Container

    type PyrightScalarValue = str | bool | int
    """Scalar value accepted by a Pyright setting."""

    class Infra(
        FlextInfraTypesAdapters,
        FlextInfraTypesBase,
        FlextInfraTypesCollections,
        FlextInfraTypesPytest,
        FlextInfraTypesRope,
        FlextInfraTypesRopeNative,
    ):
        """Infrastructure-domain type aliases.

        These aliases compose CLI JSON contracts and infrastructure-specific
        collection generics for common tooling payloads.
        """


t = FlextInfraTypes
__all__: list[str] = ["FlextInfraTypes", "t"]
