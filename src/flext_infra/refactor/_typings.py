"""Type aliases for refactor-domain policy wiring."""

from __future__ import annotations

from collections.abc import Mapping

from flext_infra import m


class FlextInfraRectorTypes:
    type PolicyContext = Mapping[str, m.Infra.Refactor.ClassNestingPolicy]
    type ClassFamilyMap = Mapping[str, str]


__all__ = ["FlextInfraRectorTypes"]
