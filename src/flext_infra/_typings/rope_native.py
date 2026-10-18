"""Native Rope SDK aliases independent of structural protocol declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from rope.base.builtins import BuiltinModule
from rope.base.pycore import PyCore
from rope.base.pyobjectsdef import PyModule, PyPackage
from rope.base.resources import Resource
from rope.refactor.similarfinder import ExpressionMatch, StatementMatch


class FlextInfraTypesRopeNative:
    """SDK identities consumed by native adapters and structural declarations."""

    type RopeNativeCore = PyCore
    type RopeNativeSourceModule = PyModule
    type RopeNativeParsedModule = PyModule | PyPackage
    type RopeNativeSemanticModule = BuiltinModule | RopeNativeParsedModule
    type RopeNativeResource = Resource
    type RopeNativeMatch = ExpressionMatch | StatementMatch


__all__: list[str] = ["FlextInfraTypesRopeNative"]
