"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only _utilities/rope.py touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence

from rope.base.project import Project as _RopeProject
from rope.base.resources import File as _RopeFile

from flext_core import FlextTypes


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = _RopeProject
    "Opaque handle to rope Project — orchestrators use this, never import rope directly."
    type RopeResource = _RopeFile
    "Opaque handle to rope File resource — orchestrators use this, never import rope directly."

    type ImportMap = FlextTypes.StrMapping
    "Mapping of local name → fully qualified import path."
    type MutableImportMap = FlextTypes.MutableStrMapping
    "Mutable mapping of local name → fully qualified import path."
    type MethodKindMap = FlextTypes.StrMapping
    "Mapping of method name → kind (staticmethod/classmethod/method)."
    type MutableMethodKindMap = FlextTypes.MutableStrMapping
    "Mutable mapping of method name → kind."
    type ChangedPaths = FlextTypes.StrSequence
    "Read-only sequence of changed file paths from rope operations."
    type MutableChangedPaths = MutableSequence[str]
    "Mutable sequence of changed file paths."
    type ClassNames = FlextTypes.StrSequence
    "Read-only sequence of class names."
    type MutableClassNames = MutableSequence[str]
    "Mutable sequence of class names."


__all__ = ["FlextInfraTypesRope"]
