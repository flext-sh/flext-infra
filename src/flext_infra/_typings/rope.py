"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only _utilities/rope.py touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence

from rope.base.change import ChangeSet
from rope.base.project import Project
from rope.base.pyobjects import PyModule
from rope.base.resources import File
from rope.contrib.findit import Location

from flext_core import FlextTypes
from flext_infra import FlextInfraProtocolsRope


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = Project
    "Opaque handle to rope Project — orchestrators use this, never import rope directly."
    type RopeResource = File
    "Opaque handle to rope File resource — orchestrators use this, never import rope directly."
    type RopeLocation = Location
    "Opaque handle to one rope occurrence result."
    type RopeChanges = ChangeSet
    "Opaque handle to one rope change set."
    type RopePyCore = FlextInfraProtocolsRope.RopePyCoreLike
    "Typed Rope PyCore facade backed by the public structural protocol."
    type RopePyModule = PyModule
    "Concrete Rope PyModule handle."
    type RopeModuleImports = FlextInfraProtocolsRope.RopeModuleImportsLike
    "Typed Rope ModuleImports facade backed by the public structural protocol."

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
    type RopeTransformFn = Callable[
        [
            Project,
            File,
        ],
        tuple[str, Sequence[str]],
    ]
    "Callback signature for rope-based transformers: (project, resource) -> (source, changes)."


__all__ = ["FlextInfraTypesRope"]
