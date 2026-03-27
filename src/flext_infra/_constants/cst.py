"""CST analysis constants — accessed via c.Infra.*."""

from __future__ import annotations

from typing import ClassVar, Final


class FlextInfraConstantsCst:
    """Constants for libcst-based code analysis and extraction."""

    class Cst:
        """CST analysis constants — accessed via c.Infra.Cst.*."""

        # -- Annotation markers that signal object kind -----------------------

        FINAL: Final[str] = "Final"
        CLASSVAR: Final[str] = "ClassVar"
        TYPE_ALIAS: Final[str] = "TypeAlias"

        CONSTANT_ANNOTATIONS: ClassVar[frozenset[str]] = frozenset({
            "Final",
            "ClassVar",
        })
        """Annotation names that mark a constant assignment."""

        TYPE_ANNOTATIONS: ClassVar[frozenset[str]] = frozenset({
            "TypeAlias",
        })
        """Annotation names that mark a type alias assignment."""

        # -- Base class names that determine object kind ----------------------

        PROTOCOL_BASES: ClassVar[frozenset[str]] = frozenset({
            "Protocol",
        })
        """Base class names that identify a Protocol definition."""

        MODEL_BASES: ClassVar[frozenset[str]] = frozenset({
            "BaseModel",
            "TypedDict",
            "FrozenStrictModel",
            "ArbitraryTypesModel",
            "StrictModel",
        })
        """Base class names that identify a Pydantic/TypedDict model."""

        # -- Constant name detection ------------------------------------------

        CONSTANT_NAME_CHARS: ClassVar[frozenset[str]] = frozenset(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        )
        """Characters allowed in UPPER_CASE constant names."""

        # -- Files to skip during extraction ----------------------------------

        SKIP_FILES: ClassVar[frozenset[str]] = frozenset({
            "__init__.py",
            "__main__.py",
            "__version__.py",
            "conftest.py",
            "py.typed",
        })
        """Files that should be skipped during object extraction."""

        SKIP_DIRS: ClassVar[frozenset[str]] = frozenset({
            "__pycache__",
            ".mypy_cache",
            ".git",
            ".venv",
            "node_modules",
            ".reports",
        })
        """Directories that should be skipped during workspace traversal."""

        # -- Decorator markers ------------------------------------------------

        STATIC_DECORATORS: ClassVar[frozenset[str]] = frozenset({
            "staticmethod",
        })
        CLASS_DECORATORS: ClassVar[frozenset[str]] = frozenset({
            "classmethod",
        })
        PROPERTY_DECORATORS: ClassVar[frozenset[str]] = frozenset({
            "property",
        })
        RUNTIME_CHECKABLE_DECORATOR: Final[str] = "runtime_checkable"

        # -- Method kind constants --------------------------------------------

        METHOD_STATIC: Final[str] = "static"
        METHOD_CLASS: Final[str] = "class"
        METHOD_INSTANCE: Final[str] = "instance"
        METHOD_PROPERTY: Final[str] = "property"

        # -- Facade detection -------------------------------------------------

        FACADE_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
            "Constants",
            "Types",
            "Protocols",
            "Models",
            "Utilities",
        })
        """Class name suffixes that identify MRO facade/namespace classes."""

        FACADE_PREFIX: Final[str] = "Flext"
        """Standard prefix for facade class names."""


__all__ = ["FlextInfraConstantsCst"]
