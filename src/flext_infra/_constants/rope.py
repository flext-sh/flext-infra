"""Rope Project configuration constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsRope:
    """Rope Project configuration constants — accessed via c.Infra.*."""

    ROPE_WALK_DEPTH_BUDGET: ClassVar[int] = 128
    "Bound for the external-base walk's provider/reexport hops; the workspace"
    " facade chain (examples -> flext -> flext_infra -> flext_core pydantic) is"
    " a finite multi-layer walk, cycles terminate through the preserved"
    " visiting stack, and self-referential definition references short-circuit"
    " through the direct identity map."

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

    # NOTE: runtime engine types and exception-boundary
    # tuples live in u.Infra (FlextInfraUtilitiesRopeRuntimeTypes), not in the
    # constants layer, to keep c.Infra declarative and cycle-free.

    ROPE_IMPORTUTILS_MODULE: ClassVar[str] = "rope.refactor.importutils"
    "Public Rope import planning and organization module."

    ROPE_PYOBJECTS_MODULE: ClassVar[str] = "rope.base.pyobjects"
    "Rope module owning the native semantic object classes."

    PYDANTIC_MODEL_IDENTITY: ClassVar[str] = "pydantic.BaseModel"
    "Qualified identity every relocated payload model must inherit."

    PYDANTIC_SETTINGS_IDENTITY: ClassVar[str] = "pydantic_settings.BaseSettings"
    "Qualified identity that excludes a settings model from payload relocation."

    TYPING_GUARD_MODULE: ClassVar[str] = "typing"
    "Module that owns the static-analysis import guard."

    TYPING_GUARD_NAME: ClassVar[str] = "TYPE_CHECKING"
    "Name of the static-analysis import guard."

    TYPING_GUARD_IDENTITY: ClassVar[str] = f"{TYPING_GUARD_MODULE}.{TYPING_GUARD_NAME}"
    "Qualified identity of the only guard that keeps a guarded import importable."

    DECLARATION_RELOCATION_IDENTITIES: ClassVar[t.VariadicTuple[str]] = (
        PYDANTIC_MODEL_IDENTITY,
        PYDANTIC_SETTINGS_IDENTITY,
        TYPING_GUARD_IDENTITY,
    )
    "Identities declaration relocation resolves; its planning epoch captures them."

    # NOTE: ROPE_IGNORED_RESOURCES was removed: the rope project election
    # derives ignored resources from the codegen artifact SSOT
    # (source_scan_ignored) through the typed RopeProjectElection owner.

    PROPERTY_DECORATORS: ClassVar[frozenset[str]] = frozenset({
        "property",
        "cached_property",
        "computed_field",
    })
    "Decorator names that mark Python descriptors / Pydantic computed fields."

    PYDANTIC_PAYLOAD_DECORATORS: ClassVar[t.VariadicTuple[str]] = (
        "pydantic.field_validator",
        "pydantic.model_validator",
        "pydantic.field_serializer",
        "pydantic.model_serializer",
        "pydantic.computed_field",
    )
    "Native Pydantic declaration decorators, resolved by Rope identity."

    PAYLOAD_DESCRIPTOR_DECORATORS: ClassVar[t.VariadicTuple[str]] = (
        "builtins.classmethod",
        "builtins.staticmethod",
        "builtins.property",
    )
    "Native descriptors permitted around a Pydantic declaration decorator."


__all__: list[str] = ["FlextInfraConstantsRope"]
