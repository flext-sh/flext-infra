"""Bootstrap-safe namespace constants."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final


class FlextInfraConstantsNamespace:
    """Namespace constants shared by bootstrap-sensitive utilities."""

    NAMESPACE_SETTINGS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
    })
    NAMESPACE_PROTECTED_FILES: Final[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
        "typings.py",
        "_typings.py",
        "__init__.py",
        "__main__.py",
        "__version__.py",
        "conftest.py",
        "py.typed",
    })
    NAMESPACE_CANONICAL_ALIAS_MODULE_STEMS: Final[frozenset[str]] = frozenset({
        "ldif",
        "cli",
        "main",
    })
    NAMESPACE_LAYER_ORDER: Final[tuple[str, ...]] = (
        "settings",
        "config",
        "c",
        "t",
        "p",
        "m",
        "u",
        "base",
        "services",
        "api",
        "cli",
    )
    NAMESPACE_OPERATION_FACADES: Final[tuple[str, ...]] = ("r", "e", "x", "h", "d", "s")
    NAMESPACE_LAYER_BY_FILE: Final[MappingProxyType[str, str]] = MappingProxyType({
        "settings.py": "settings",
        "_settings.py": "settings",
        "config.py": "config",
        "_config.py": "config",
        "constants.py": "c",
        "typings.py": "t",
        "protocols.py": "p",
        "models.py": "m",
        "utilities.py": "u",
        "base.py": "base",
        "api.py": "api",
        "cli.py": "cli",
    })
    NAMESPACE_LAYER_BY_FAMILY: Final[MappingProxyType[str, str]] = MappingProxyType({
        "_constants": "c",
        "_typings": "t",
        "_protocols": "p",
        "_models": "m",
        "_utilities": "u",
        "services": "services",
    })
    NAMESPACE_BANNED_ANNOTATIONS: Final[frozenset[str]] = frozenset({
        "Any",
        "Optional",
        "dict",
        "object",
    })
    NAMESPACE_PYDANTIC_V1_MEMBERS: Final[frozenset[str]] = frozenset({
        "dict",
        "json",
        "parse_obj",
        "parse_raw",
        "validator",
        "root_validator",
    })
    # The subset reached by bare name rather than through a model instance:
    # `@validator(...)` is imported from pydantic and called directly, while
    # `dict`, `json`, `parse_obj` and `parse_raw` are only Pydantic when they
    # appear as an attribute -- as bare names they are the builtins.
    NAMESPACE_PYDANTIC_V1_DECORATORS: Final[frozenset[str]] = frozenset({
        "validator",
        "root_validator",
    })
    NAMESPACE_SERVICE_LOCATOR_NAMES: Final[frozenset[str]] = frozenset({
        "container",
        "get_service",
        "locator",
        "resolve_service",
        "service_locator",
    })
    NAMESPACE_LOGICAL_STATEMENT_KINDS: Final[frozenset[str]] = frozenset({
        "AnnAssign",
        "Assert",
        "Assign",
        "AsyncFor",
        "AsyncFunctionDef",
        "AsyncWith",
        "AugAssign",
        "ClassDef",
        "Delete",
        "For",
        "FunctionDef",
        "If",
        "Match",
        "Raise",
        "Return",
        "Try",
        "TypeAlias",
        "While",
        "With",
        "Yield",
        "YieldFrom",
    })
    NAMESPACE_MAX_LOGICAL_LOC: Final[int] = 200


__all__: list[str] = ["FlextInfraConstantsNamespace"]
