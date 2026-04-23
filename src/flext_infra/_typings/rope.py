"""Rope-specific type aliases for flext-infra.

Orchestrators use t.Infra.RopeProject and t.Infra.RopeResource in signatures.
Only the centralized Rope boundary touches concrete rope APIs internally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Callable,
)

from flext_core import t
from rope.base.change import ChangeContents, ChangeSet
from rope.base.project import Project
from rope.base.pycore import PyCore
from rope.base.pynames import PyName
from rope.base.pynamesdef import AssignedName
from rope.base.pyobjects import AbstractClass, PyObject
from rope.base.pyobjectsdef import PyFunction, PyModule
from rope.base.resources import File, Resource
from rope.contrib.findit import Location
from rope.refactor.importutils import ImportOrganizer
from rope.refactor.importutils.importinfo import (
    FromImport,
    ImportInfo,
    ImportStatement,
)
from rope.refactor.importutils.module_imports import ModuleImports
from rope.refactor.rename import Rename


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = Project
    "Typed Rope project alias backed by the centralized concrete Rope project."
    type RopeResource = File
    "Typed Rope file resource alias backed by Rope's concrete File."
    type RopeApiResource = Resource
    "Typed Rope generic resource alias backed by Rope's concrete Resource."
    type RopeChange = ChangeContents
    "Typed Rope child-change alias backed by Rope's concrete ChangeContents."
    type RopeLocation = Location
    "Typed Rope occurrence alias backed by Rope's concrete Location."
    type RopeChanges = ChangeSet
    "Typed Rope change-set alias backed by Rope's concrete ChangeSet."
    type RopeMutableChanges = ChangeSet
    "Typed mutable Rope change-set alias backed by Rope's concrete ChangeSet."
    type RopePyCore = PyCore
    "Typed Rope PyCore alias backed by Rope's concrete PyCore."
    type RopePyModule = PyModule
    "Typed Rope PyModule alias backed by Rope's concrete PyModule."
    type RopePyName = PyName
    "Typed Rope PyName alias backed by Rope's concrete PyName."
    type RopeAssignedName = AssignedName
    "Typed Rope assigned-name alias for names with assignment metadata."
    type RopePyObject = PyObject
    "Typed Rope PyObject alias backed by Rope's concrete PyObject."
    type RopeAbstractClass = AbstractClass
    "Typed Rope abstract class alias backed by Rope's concrete AbstractClass."
    type RopePyFunction = PyFunction
    "Typed Rope function alias backed by Rope's concrete PyFunction."
    type RopeImportInfo = ImportInfo
    "Typed Rope import info alias backed by Rope's concrete ImportInfo."
    type RopeFromImport = FromImport
    "Typed Rope from-import alias backed by Rope's concrete FromImport."
    type RopeImportStatement = ImportStatement
    "Typed Rope import statement alias backed by Rope's concrete ImportStatement."
    type RopeModuleImports = ModuleImports
    "Typed Rope ModuleImports alias backed by Rope's concrete ModuleImports."
    type RopeRename = Rename
    "Typed Rope rename alias backed by Rope's concrete Rename."
    type RopeImportOrganizer = ImportOrganizer
    "Typed Rope import organizer alias backed by Rope's concrete ImportOrganizer."
    type RopeGetModuleImportsFn = Callable[
        [RopeProject, RopePyModule], RopeModuleImports
    ]
    "Typed Rope get_module_imports callable."
    type RopeFindOccurrencesFn = Callable[
        [RopeProject, RopeApiResource, int],
        t.SequenceOf[RopeLocation],
    ]
    "Typed Rope find_occurrences callable."

    type RopeTransformFn = Callable[
        [
            RopeProject,
            RopeResource,
        ],
        t.Pair[str, t.StrSequence],
    ]
    "Callback signature for rope-based transformers: (project, resource) -> (source, changes)."


__all__: list[str] = ["FlextInfraTypesRope"]
