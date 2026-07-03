"""Rope Project configuration constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final

from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyFunction


class FlextInfraConstantsRope:
    """Rope Project configuration constants — accessed via c.Infra.*."""

    SYNTAX_ERRORS: Final[tuple[type[BaseException], ...]] = (
        SyntaxError,
        ModuleSyntaxError,
    )
    "Exception types that signal unparseable Python source during Rope operations."

    RUNTIME_ERRORS: Final[tuple[type[BaseException], ...]] = (
        RefactoringError,
        ResourceNotFoundError,
        AttributeError,
    )
    "Exception types that signal recoverable Rope runtime failures."

    ABSTRACT_CLASS_TYPES: Final[tuple[type[AbstractClass], ...]] = (AbstractClass,)
    "Rope pyobject classes treated as abstract class shapes."

    PY_FUNCTION_TYPES: Final[tuple[type[PyFunction], ...]] = (PyFunction,)
    "Rope pyobject classes treated as function shapes."

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
