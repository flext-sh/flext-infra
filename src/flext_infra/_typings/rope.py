"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only _utilities/rope.py touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence

from flext_core import FlextTypes
from flext_infra import FlextInfraProtocolsRope


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = FlextInfraProtocolsRope.RopeProjectLike
    "Typed Rope project alias backed by the public structural protocol."
    type RopeResource = FlextInfraProtocolsRope.RopeResourceLike
    "Typed Rope file resource alias backed by the public structural protocol."
    type RopeApiResource = FlextInfraProtocolsRope.RopeApiResourceLike
    "Typed Rope generic resource alias backed by the public structural protocol."
    type RopeChange = FlextInfraProtocolsRope.RopeChangeLike
    "Typed Rope child-change alias backed by the public structural protocol."
    type RopeLocation = FlextInfraProtocolsRope.RopeLocationLike
    "Typed Rope occurrence alias backed by the public structural protocol."
    type RopeChanges = FlextInfraProtocolsRope.RopeChangesLike
    "Typed Rope change-set alias backed by the public structural protocol."
    type RopeMutableChanges = FlextInfraProtocolsRope.RopeMutableChangesLike
    "Typed mutable Rope change-set alias backed by the public structural protocol."
    type RopePyCore = FlextInfraProtocolsRope.RopePyCoreLike
    "Typed Rope PyCore alias backed by the public structural protocol."
    type RopePyModule = FlextInfraProtocolsRope.RopePyModuleLike
    "Typed Rope PyModule alias backed by the public structural protocol."
    type RopePyName = FlextInfraProtocolsRope.RopePyNameLike
    "Typed Rope PyName alias backed by the public structural protocol."
    type RopePyObject = FlextInfraProtocolsRope.RopePyObjectLike
    "Typed Rope PyObject alias backed by the public structural protocol."
    type RopeNamedObject = FlextInfraProtocolsRope.RopeNamedObjectLike
    "Typed Rope named-object facade backed by the public structural protocol."
    type RopeAbstractClass = FlextInfraProtocolsRope.RopeAbstractClassLike
    "Typed Rope abstract class alias backed by the public structural protocol."
    type RopePyFunction = FlextInfraProtocolsRope.RopePyFunctionLike
    "Typed Rope function facade backed by the public structural protocol for get_kind()."
    type RopeImportInfo = FlextInfraProtocolsRope.RopeImportInfoLike
    "Typed Rope import info alias backed by the public structural protocol."
    type RopeFromImport = FlextInfraProtocolsRope.RopeFromImportLike
    "Typed Rope from-import alias backed by the public structural protocol."
    type RopeImportStatement = FlextInfraProtocolsRope.RopeImportStatementLike
    "Typed Rope import statement alias backed by the public structural protocol."
    type RopeModuleImports = FlextInfraProtocolsRope.RopeModuleImportsLike
    "Typed Rope ModuleImports alias backed by the public structural protocol."
    type RopeRename = FlextInfraProtocolsRope.RopeRenameLike
    "Typed Rope rename alias backed by the public structural protocol."
    type RopeImportOrganizer = FlextInfraProtocolsRope.RopeImportOrganizerLike
    "Typed Rope import organizer alias backed by the public structural protocol."
    type RopeImportUtilsModule = FlextInfraProtocolsRope.RopeImportUtilsModuleLike
    "Typed rope.refactor.importutils module facade backed by the public structural protocol."
    type RopeFindItModule = FlextInfraProtocolsRope.RopeFindItModuleLike
    "Typed rope.contrib.findit module facade backed by the public structural protocol."
    type RopeGetModuleImportsFn = FlextInfraProtocolsRope.RopeGetModuleImportsFn
    "Typed Rope get_module_imports callable backed by the public structural protocol."
    type RopeFindOccurrencesFn = FlextInfraProtocolsRope.RopeFindOccurrencesFn
    "Typed Rope find_occurrences callable backed by the public structural protocol."

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
            FlextInfraProtocolsRope.RopeProjectLike,
            FlextInfraProtocolsRope.RopeResourceLike,
        ],
        tuple[str, Sequence[str]],
    ]
    "Callback signature for rope-based transformers: (project, resource) -> (source, changes)."


__all__ = ["FlextInfraTypesRope"]
