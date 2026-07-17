"""Rope Project configuration constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import TYPE_CHECKING, Final

from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from flext_cli import p


class FlextInfraConstantsRope:
    """Rope Project configuration constants — accessed via c.Infra.*."""

    @unique
    class RopeScopeKind(StrEnum):
        """Semantic scope kinds returned by rope's ``PyScope.get_kind()``.

        Rope emits ``"Module"``/``"Function"``/``"Class"`` for those scopes and
        ``None`` for comprehension (temporary) scopes; ``UNKNOWN`` is the
        canonical fallback for that ``None`` so the contract stays typed.
        """

        MODULE = "Module"
        "Module (global) scope."
        FUNCTION = "Function"
        "Function or method scope."
        CLASS = "Class"
        "Class scope."
        UNKNOWN = "Unknown"
        "Fallback for rope comprehension/temporary scopes (get_kind() is None)."

    @unique
    class StatementCategory(StrEnum):
        """Lexical category of one logical statement from the rope structure boundary.

        Derived from the leading token of a rope ``LogicalLineFinder`` region;
        the classification is lexical (rope-owned source slice), never ``ast``.
        """

        IMPORT = "import"
        "Plain ``import x`` statement."
        FROM_IMPORT = "from_import"
        "``from m import x`` statement."
        TYPE_ALIAS = "type_alias"
        "PEP 695 ``type X = ...`` alias declaration."
        ANN_ASSIGN = "ann_assign"
        "Annotated assignment ``x: T = v`` or ``x: T``."
        ASSIGN = "assign"
        "Plain assignment ``x = v``."
        IF_GUARD = "if_guard"
        "``if ...:`` block header (e.g. ``if TYPE_CHECKING:``)."
        CLASS_DEF = "class_def"
        "``class X...:`` header."
        FUNC_DEF = "func_def"
        "``def``/``async def`` header."
        CALL = "call"
        "Expression statement whose head is a call."
        OTHER = "other"
        "Any statement not matched by a more specific category."

    SYNTAX_ERRORS: Final[tuple[type[BaseException], ...]] = (
        SyntaxError,
        FlextInfraUtilitiesRopeRuntime.module_syntax_error_type(),
    )
    "Exception types that signal unparseable Python source during Rope operations."

    RUNTIME_ERRORS: Final[tuple[type[BaseException], ...]] = (
        FlextInfraUtilitiesRopeRuntime.refactoring_error_type(),
        FlextInfraUtilitiesRopeRuntime.resource_not_found_error_type(),
        AttributeError,
    )
    "Exception types that signal recoverable Rope runtime failures."

    ROPE_ERROR_TYPES: Final[tuple[type[BaseException], ...]] = (
        FlextInfraUtilitiesRopeRuntime.rope_error_type(),
    )
    "Generic Rope exception types surfaced by semantic inventory operations."

    MODULE_NOT_FOUND_ERROR_TYPES: Final[tuple[type[BaseException], ...]] = (
        FlextInfraUtilitiesRopeRuntime.module_not_found_error_type(),
    )
    "Rope exception types raised when an importable module cannot be resolved."

    ABSTRACT_CLASS_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.abstract_class_type(),
    )
    "Rope pyobject classes treated as abstract class shapes."

    PY_FUNCTION_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.py_function_type(),
    )
    "Rope pyobject classes treated as function shapes."

    DEFINED_NAME_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.runtime_type("rope.base.pynames", "DefinedName"),
    )
    "Rope pyname classes treated as defined-name shapes."

    IMPORTED_NAME_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.runtime_type(
            "rope.base.pynames", "ImportedName"
        ),
    )
    "Rope pyname classes treated as imported-name shapes."

    ASSIGNED_NAME_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.runtime_type(
            "rope.base.pynamesdef", "AssignedName"
        ),
    )
    "Rope pyname classes treated as assigned-name shapes."

    PARAMETER_NAME_TYPES: Final[tuple[type[p.AttributeProbe], ...]] = (
        FlextInfraUtilitiesRopeRuntime.runtime_type(
            "rope.base.pynamesdef", "ParameterName"
        ),
    )
    "Rope pyname classes treated as parameter-name shapes."

    ROPE_IGNORED_RESOURCES: Final[tuple[str, ...]] = (
        ".venv",
        "venv",
        "node_modules",
        "*.pyc",
        "dist/",
        "build/",
        ".tox/",
        ".cache/",
        "__pycache__",
        ".mypy_cache",
        ".pyrefly_cache",
        ".pytest_cache",
        ".git",
    )
    "Resources rope should ignore when scanning the project tree."

    PROPERTY_DECORATORS: Final[frozenset[str]] = frozenset({
        "property",
        "cached_property",
        "computed_field",
    })
    "Decorator names that mark Python descriptors / Pydantic computed fields."


__all__: list[str] = ["FlextInfraConstantsRope"]
