"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only _utilities/rope.py touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence

from flext_core import t
from flext_infra import p


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = p.Infra.RopeProjectLike
    "Typed Rope project alias backed by the public structural protocol."
    type RopeResource = p.Infra.RopeResourceLike
    "Typed Rope file resource alias backed by the public structural protocol."
    type RopeApiResource = p.Infra.RopeApiResourceLike
    "Typed Rope generic resource alias backed by the public structural protocol."
    type RopeChange = p.Infra.RopeChangeLike
    "Typed Rope child-change alias backed by the public structural protocol."
    type RopeLocation = p.Infra.RopeLocationLike
    "Typed Rope occurrence alias backed by the public structural protocol."
    type RopeChanges = p.Infra.RopeChangesLike
    "Typed Rope change-set alias backed by the public structural protocol."
    type RopeMutableChanges = p.Infra.RopeMutableChangesLike
    "Typed mutable Rope change-set alias backed by the public structural protocol."
    type RopePyCore = p.Infra.RopePyCoreLike
    "Typed Rope PyCore alias backed by the public structural protocol."
    type RopePyModule = p.Infra.RopePyModuleLike
    "Typed Rope PyModule alias backed by the public structural protocol."
    type RopePyName = p.Infra.RopePyNameLike
    "Typed Rope PyName alias backed by the public structural protocol."
    type RopePyObject = p.Infra.RopePyObjectLike
    "Typed Rope PyObject alias backed by the public structural protocol."
    type RopeNamedObject = p.Infra.RopeNamedObjectLike
    "Typed Rope named-object facade backed by the public structural protocol."
    type RopeAbstractClass = p.Infra.RopeAbstractClassLike
    "Typed Rope abstract class alias backed by the public structural protocol."
    type RopePyFunction = p.Infra.RopePyFunctionLike
    "Typed Rope function facade backed by the public structural protocol for get_kind()."
    type RopeImportInfo = p.Infra.RopeImportInfoLike
    "Typed Rope import info alias backed by the public structural protocol."
    type RopeFromImport = p.Infra.RopeFromImportLike
    "Typed Rope from-import alias backed by the public structural protocol."
    type RopeImportStatement = p.Infra.RopeImportStatementLike
    "Typed Rope import statement alias backed by the public structural protocol."
    type RopeModuleImports = p.Infra.RopeModuleImportsLike
    "Typed Rope ModuleImports alias backed by the public structural protocol."
    type RopeRename = p.Infra.RopeRenameLike
    "Typed Rope rename alias backed by the public structural protocol."
    type RopeImportOrganizer = p.Infra.RopeImportOrganizerLike
    "Typed Rope import organizer alias backed by the public structural protocol."
    type RopeImportUtilsModule = p.Infra.RopeImportUtilsModuleLike
    "Typed rope.refactor.importutils module facade backed by the public structural protocol."
    type RopeFindItModule = p.Infra.RopeFindItModuleLike
    "Typed rope.contrib.findit module facade backed by the public structural protocol."
    type RopeGetModuleImportsFn = Callable[
        [RopeProject, RopePyModule], RopeModuleImports
    ]
    "Typed Rope get_module_imports callable."
    type RopeFindOccurrencesFn = Callable[
        [RopeProject, RopeApiResource, int],
        t.SequenceOf[RopeLocation],
    ]
    "Typed Rope find_occurrences callable."

    type ImportMap = t.StrMapping
    "Mapping of local name → fully qualified import path."
    type MutableImportMap = t.MutableStrMapping
    "Mutable mapping of local name → fully qualified import path."
    type MethodKindMap = t.StrMapping
    "Mapping of method name → kind (staticmethod/classmethod/method)."
    type MutableMethodKindMap = t.MutableStrMapping
    "Mutable mapping of method name → kind."
    type ChangedPaths = t.StrSequence
    "Read-only sequence of changed file paths from rope operations."
    type MutableChangedPaths = MutableSequence[str]
    "Mutable sequence of changed file paths."
    type ClassNames = t.StrSequence
    "Read-only sequence of class names."
    type MutableClassNames = MutableSequence[str]
    "Mutable sequence of class names."
    type RopeTransformFn = Callable[
        [
            p.Infra.RopeProjectLike,
            p.Infra.RopeResourceLike,
        ],
        t.Pair[str, t.StrSequence],
    ]
    "Callback signature for rope-based transformers: (project, resource) -> (source, changes)."


__all__ = ["FlextInfraTypesRope"]
