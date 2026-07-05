"""Rope runtime type predicates and exception factories."""

from __future__ import annotations

from typing import TypeGuard

from flext_infra._utilities.rope_runtime_base import FlextInfraUtilitiesRopeRuntimeBase
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraUtilitiesRopeRuntimeTypes(FlextInfraUtilitiesRopeRuntimeBase):
    """Expose typed predicates for Rope runtime objects."""

    @classmethod
    def patched_ast_walker(cls) -> type[p.AttributeProbe]:
        return cls.runtime_type("rope.refactor.patchedast", "_PatchingASTWalker")

    @classmethod
    def is_resource(cls, value: p.AttributeProbe) -> TypeGuard[t.Infra.RopeResource]:
        return isinstance(value, cls.runtime_type("rope.base.resources", "File"))

    @classmethod
    def is_pymodule(cls, value: p.AttributeProbe) -> TypeGuard[t.Infra.RopePyModule]:
        return isinstance(value, cls.runtime_type("rope.base.pyobjectsdef", "PyModule"))

    @classmethod
    def is_from_import(
        cls, value: p.AttributeProbe
    ) -> TypeGuard[t.Infra.RopeFromImport]:
        return isinstance(
            value,
            cls.runtime_type("rope.refactor.importutils.importinfo", "FromImport"),
        )

    @classmethod
    def is_normal_import(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopeNormalImport]:
        return isinstance(
            value,
            cls.runtime_type("rope.refactor.importutils.importinfo", "NormalImport"),
        )

    @classmethod
    def is_assigned_name(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopeAssignedName]:
        return isinstance(
            value, cls.runtime_type("rope.base.pynamesdef", "AssignedName")
        )

    @classmethod
    def is_pyclass(cls, value: p.AttributeProbe) -> TypeGuard[t.Infra.RopePyObject]:
        return isinstance(value, cls.runtime_type("rope.base.pyobjects", "PyClass"))

    module_syntax_error_type = classmethod(
        lambda cls: cls._exception_type("rope.base.exceptions", "ModuleSyntaxError"),
    )
    refactoring_error_type = classmethod(
        lambda cls: cls._exception_type("rope.base.exceptions", "RefactoringError"),
    )
    resource_not_found_error_type = classmethod(
        lambda cls: cls._exception_type(
            "rope.base.exceptions", "ResourceNotFoundError"
        ),
    )
    module_not_found_error_type = classmethod(
        lambda cls: cls._exception_type("rope.base.exceptions", "ModuleNotFoundError"),
    )
    rope_error_type = classmethod(
        lambda cls: cls._exception_type("rope.base.exceptions", "RopeError"),
    )
    abstract_class_type = classmethod(
        lambda cls: cls.runtime_type("rope.base.pyobjects", "AbstractClass"),
    )
    py_function_type = classmethod(
        lambda cls: cls.runtime_type("rope.base.pyobjectsdef", "PyFunction"),
    )


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeTypes"]
