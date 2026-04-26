"""Rope-specific type aliases for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Callable,
)

from rope.base.project import Project
from rope.base.pynames import PyName
from rope.base.pynamesdef import AssignedName
from rope.base.pyobjects import PyObject
from rope.base.pyobjectsdef import PyModule
from rope.base.resources import File
from rope.contrib.findit import Location
from rope.refactor.importutils.importinfo import (
    FromImport,
    ImportStatement,
)
from rope.refactor.importutils.module_imports import ModuleImports

from flext_core import t


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeProject = Project
    type RopeResource = File
    type RopeLocation = Location
    type RopePyModule = PyModule
    type RopePyName = PyName
    type RopeAssignedName = AssignedName
    type RopePyObject = PyObject
    type RopeFromImport = FromImport
    type RopeImportStatement = ImportStatement
    type RopeModuleImports = ModuleImports

    type RopeTransformFn = Callable[
        [RopeProject, RopeResource],
        t.Pair[str, t.StrSequence],
    ]


__all__: list[str] = ["FlextInfraTypesRope"]
