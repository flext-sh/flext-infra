"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only _utilities/rope.py touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

from rope.base.project import Project as _RopeProject
from rope.base.resources import File as _RopeFile


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = _RopeProject
    "Opaque handle to rope Project — orchestrators use this, never import rope directly."
    type RopeResource = _RopeFile
    "Opaque handle to rope File resource — orchestrators use this, never import rope directly."

    type ClassLineMap = Mapping[str, int]
    "Mapping of class name → definition line number."
    type MutableClassLineMap = MutableMapping[str, int]
    "Mutable mapping of class name → definition line number."
    type ImportMap = Mapping[str, str]
    "Mapping of local name → fully qualified import path."
    type MutableImportMap = MutableMapping[str, str]
    "Mutable mapping of local name → fully qualified import path."
    type MethodKindMap = Mapping[str, str]
    "Mapping of method name → kind (staticmethod/classmethod/method)."
    type MutableMethodKindMap = MutableMapping[str, str]
    "Mutable mapping of method name → kind."
    type ChangedPaths = Sequence[str]
    "Read-only sequence of changed file paths from rope operations."
    type MutableChangedPaths = MutableSequence[str]
    "Mutable sequence of changed file paths."
    type ClassNames = Sequence[str]
    "Read-only sequence of class names."
    type MutableClassNames = MutableSequence[str]
    "Mutable sequence of class names."


__all__ = ["FlextInfraTypesRope"]
