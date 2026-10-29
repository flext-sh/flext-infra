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

    @staticmethod
    def source_declaration_region(
        module: p.Infra.RopeSourceModule,
        node: p.Infra.RopeAstNode,
    ) -> tuple[int, int]:
        """Read an opaque native node's exact region through its SDK index.

        Returns:
            The original inclusive/exclusive character offsets.

        Raises:
            ValueError: The native declaration has no valid source region.

        """
        start, end = module.get_source_binding_index().lines[node]
        if (
            start is None
            or end is None
            or not 0 <= start < end <= len(module.source_code)
        ):
            message = "Native declaration has no valid source region"
            raise ValueError(message)
        return start, end

    @classmethod
    def semantic_capture_region(
        cls,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        name: str,
    ) -> tuple[int, int]:
        """Resolve a native scalar capture through the SDK's public region API.

        Returns:
            The capture's exact half-open source region.

        Raises:
            ValueError: The capture is missing or outside the supplied source.

        """
        start, end = match.get_capture_region(name)
        if not 0 <= start < end <= len(module.source_code):
            message = f"Native capture is outside its source module: {name}"
            raise ValueError(message)
        return start, end

    @classmethod
    def require_class_object(
        cls, value: p.AttributeProbe, label: str
    ) -> p.Infra.RopeClassObject:
        """Admit the actual SDK class and its consumed superclass capability.

        Returns:
            The original native class by reference.

        Raises:
            TypeError: The producer does not supply a native class contract.

        """
        if not isinstance(
            value, cls.runtime_type(c.Infra.ROPE_PYOBJECTS_MODULE, "AbstractClass")
        ) or not isinstance(value, p.Infra.RopeClassObject):
            msg = (
                f"expected a native Rope class: {label} (found {type(value).__name__})"
            )
            raise TypeError(msg)
        return value

    @classmethod
    def require_source_object(
        cls, value: p.AttributeProbe, label: str
    ) -> p.Infra.RopeSourceObject:
        """Admit source and scope capabilities only on native Python definitions.

        Returns:
            The original native definition by reference.

        Raises:
            TypeError: The producer does not supply a native source definition.

        """
        if not isinstance(
            value,
            tuple(
                cls.runtime_type("rope.base.pyobjectsdef", kind)
                for kind in ("PyClass", "PyFunction", "PyModule", "PyPackage")
            ),
        ) or not isinstance(value, p.Infra.RopeSourceObject):
            msg = f"expected a native Rope source definition: {label}"
            raise TypeError(msg)
        return value

    @classmethod
    def require_named_object(
        cls, value: p.AttributeProbe, label: str
    ) -> p.Infra.RopeNamedObject:
        """Admit name queries only on actual native class, function or module owners.

        Returns:
            The original named native object by reference.

        Raises:
            TypeError: The producer does not supply a native named object.

        """
        if not isinstance(
            value,
            tuple(
                cls.runtime_type(c.Infra.ROPE_PYOBJECTS_MODULE, kind)
                for kind in ("AbstractClass", "AbstractFunction", "AbstractModule")
            ),
        ) or not isinstance(value, p.Infra.RopeNamedObject):
            msg = f"expected a named native Rope object: {label}"
            raise TypeError(msg)
        return value

    @classmethod
    def rope_error_types(cls) -> tuple[type[BaseException], ...]:
        """Return the generic Rope exception boundary.

        Returns:
            The generic Rope exception boundary.

        """
        return (cls._exception_type("rope.base.exceptions", "RopeError"),)

    @classmethod
    def rope_syntax_errors(cls) -> tuple[type[BaseException], ...]:
        """Return exceptions that signal unparseable Python source.

        Returns:
            Exceptions that signal unparseable Python source.

        """
        return (
            SyntaxError,
            cls._exception_type("rope.base.exceptions", "ModuleSyntaxError"),
        )

    @classmethod
    def rope_runtime_errors(cls) -> tuple[type[BaseException], ...]:
        """Return recoverable exceptions raised by Rope operations.

        Returns:
            Recoverable exceptions raised by Rope operations.

        """
        return (
            cls._exception_type("rope.base.exceptions", "RefactoringError"),
            cls._exception_type("rope.base.exceptions", "ResourceNotFoundError"),
            # Module probing (longest-prefix module/class split) treats a
            # missing module as "keep splitting", never as a hard failure.
            cls._exception_type("rope.base.exceptions", "ModuleNotFoundError"),
            AttributeError,
        )

    @classmethod
    def rope_hierarchy_errors(cls) -> tuple[type[BaseException], ...]:
        """Return Rope exceptions for hierarchies that fail to linearize.

        A candidate overlay may hold base chains whose MRO is not computable
        in that view (lazy cross-package letters); optimization owners treat
        these as "proof unavailable" and retain the prior state.

        Returns:
            The hierarchy-failure exception types.

        """
        return (
            cls._exception_type("rope.base.exceptions", "InconsistentHierarchyError"),
        )

    @classmethod
    def rope_unresolved_error_types(cls) -> tuple[type[BaseException], ...]:
        """Return Rope exceptions for statically unresolved modules or attributes.

        Returns:
            Rope exceptions raised when a native lookup resolves nothing.

        """
        return tuple(
            cls._exception_type("rope.base.exceptions", name)
            for name in (
                "ModuleNotFoundError",
                "BadIdentifierError",
                "AttributeNotFoundError",
            )
        )

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
