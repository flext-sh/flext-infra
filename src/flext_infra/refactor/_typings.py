"""Type aliases for refactor-domain policy wiring."""

from __future__ import annotations

from collections.abc import Mapping

from flext_infra import m, t


class FlextInfraRectorTypes:
    type PolicyContext = Mapping[str, m.Infra.ClassNestingPolicy]
    type ClassFamilyMap = t.StrMapping


__all__ = ["FlextInfraRectorTypes"]
