"""Base loader for the typed Rope runtime boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import TypeIs, get_protocol_members

from flext_infra import c, p


class FlextInfraUtilitiesRopeRuntimeBase:
    """Resolve Rope runtime attributes without importing Rope in leaf modules."""

    @classmethod
    def runtime_type(cls, module_name: str, attribute: str) -> type[p.AttributeProbe]:
        candidate: type[p.AttributeProbe] | p.AttributeProbe = getattr(
            import_module(module_name),
            attribute,
        )
        if not isinstance(candidate, type):
            msg = f"rope attribute is not a type: {module_name}.{attribute}"
            raise TypeError(msg)
        return candidate

    @classmethod
    def runtime_callable(
        cls,
        module_name: str,
        attribute: str,
    ) -> Callable[..., p.AttributeProbe]:
        candidate: Callable[..., p.AttributeProbe] | p.AttributeProbe = getattr(
            import_module(module_name),
            attribute,
        )
        if not callable(candidate):
            msg = f"rope attribute is not callable: {module_name}.{attribute}"
            raise TypeError(msg)
        return candidate

    @classmethod
    def _exception_type(cls, module_name: str, attribute: str) -> type[BaseException]:
        candidate = cls.runtime_type(module_name, attribute)
        if not issubclass(candidate, BaseException):
            msg = f"rope attribute is not an exception type: {module_name}.{attribute}"
            raise TypeError(msg)
        return candidate

    @classmethod
    def semantic_module(
        cls, value: p.AttributeProbe
    ) -> TypeIs[p.Infra.RopeSemanticModule]:
        """Admit module attributes only on the SDK's native module lineage.

        Returns:
            Whether the native module exposes its complete semantic interface.

        """
        return isinstance(
            value, cls.runtime_type(c.Infra.ROPE_PYOBJECTS_MODULE, "AbstractModule")
        ) and isinstance(value, p.Infra.RopeSemanticModule)

    @classmethod
    def require_semantic_module(
        cls, value: p.AttributeProbe
    ) -> p.Infra.RopeSemanticModule:
        """Admit a fetched native builtin, package, or source semantic module.

        Returns:
            The original module exposing the native semantic capability.

        Raises:
            TypeError: The provider is not a native semantic module.

        """
        if not cls.semantic_module(value):
            missing = sorted(
                member
                for member in get_protocol_members(p.Infra.RopeSemanticModule)
                if not hasattr(value, member)
            )
            message = (
                "Rope provider has no native semantic module: "
                f"{type(value).__module__}.{type(value).__qualname__}; "
                f"missing members={missing}"
            )
            raise TypeError(message)
        return value


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeBase"]
