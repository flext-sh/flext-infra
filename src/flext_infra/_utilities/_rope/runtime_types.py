"""Rope runtime type predicates and exception factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeGuard, TypeIs

from flext_infra import c, p, t
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeBase


class FlextInfraUtilitiesRopeRuntimeScopes(FlextInfraUtilitiesRopeRuntimeBase):
    """Expose lexical-scope predicates for native Rope values."""

    @classmethod
    def native_scope(cls, value: p.AttributeProbe) -> TypeGuard[p.Infra.RopeScope]:
        """Admit lexical scopes through their native SDK ancestry.

        Returns:
            Whether the object belongs to Rope's declared Scope hierarchy.

        """
        return isinstance(value, cls.runtime_type("rope.base.pyscopes", "Scope"))


class FlextInfraUtilitiesRopeRuntimeTypes(FlextInfraUtilitiesRopeRuntimeScopes):
    """Expose typed predicates for Rope runtime objects."""

    @classmethod
    def file_resource(cls, value: p.AttributeProbe) -> TypeGuard[t.Infra.RopeFile]:
        return isinstance(value, cls.runtime_type("rope.base.resources", "File"))

    @classmethod
    def require_file_resource(
        cls,
        value: p.AttributeProbe,
        label: str | Path,
    ) -> t.Infra.RopeFile:
        """Narrow one Rope resource to the file shape or refuse the input.

        Single owner for the ``get_resource`` result consumers read content
        from: every caller that treats a project resource as a module file
        narrows through here instead of restating the predicate and refusal.

        Returns:
            The resulting ``t.Infra.RopeFile``.

        Raises:
            TypeError: If the resource is not a Rope file (folder or absent).

        """
        if not cls.file_resource(value):
            msg = f"expected a Rope file resource: {label}"
            raise TypeError(msg)
        return value

    @classmethod
    def folder_resource(cls, value: p.AttributeProbe) -> TypeGuard[t.Infra.RopeRoot]:
        """Return whether ``value`` is a Rope folder resource.

        Returns:
            Whether the resource is a native Rope folder (child lookup root).

        """
        return isinstance(
            value,
            cls.runtime_type("rope.base.resources", "Folder"),
        )

    @classmethod
    def pymodule(cls, value: p.AttributeProbe) -> TypeIs[t.Infra.RopeParsedModule]:
        """Accept every rope module-like object: modules and packages.

        ``find_module`` resolves an installed third-party package to its
        folder resource and ``get_pymodule`` returns a ``PyPackage`` for it,
        which is rope's ``_PyModule`` sibling of ``PyModule`` — never a
        ``PyModule`` instance. External base resolution
        (``pydantic.BaseModel`` and friends) must read attributes through
        packages exactly like through modules, so both shapes satisfy the
        contract.

        Returns:
            The resulting ``TypeIs[t.Infra.RopeParsedModule]``.

        """
        return isinstance(
            value,
            (
                cls.runtime_type("rope.base.pyobjectsdef", "PyModule"),
                cls.runtime_type("rope.base.pyobjectsdef", "PyPackage"),
            ),
        )

    @classmethod
    def source_module(cls, value: p.AttributeProbe) -> TypeIs[p.Infra.RopeSourceModule]:
        """Recognize the SDK's source-bearing module, including string modules.

        Returns:
            Whether the value is a native source module rather than a package.

        """
        return isinstance(value, cls.runtime_type("rope.base.pyobjectsdef", "PyModule"))

    @classmethod
    def require_source_module(cls, value: p.AttributeProbe) -> p.Infra.RopeSourceModule:
        """Admit the native source-bearing module at the shared runtime boundary.

        Returns:
            The original native source module.

        Raises:
            TypeError: If the native object is not a source-bearing module.

        """
        if not cls.source_module(value):
            message = "expected a native Rope source module"
            raise TypeError(message)
        return value

    @classmethod
    def require_declared_source_module(
        cls, project: p.Infra.RopeProject, module: str
    ) -> p.Infra.RopeSourceModule:
        """Admit the source module that declares one dotted module or package.

        Rope answers a package name with its ``PyPackage`` folder object, which
        carries no source; the declaration of a package is its ``__init__.py``,
        so a folder resolves to that file before admission.

        Returns:
            The native source module declaring ``module``.

        Raises:
            ValueError: If the resolved module has no source resource.
            TypeError: If rope's untyped resource is not a rope resource.

        """
        resource = project.get_module(module).get_resource()
        if resource is None:
            message = f"declared module has no source: {module}"
            raise ValueError(message)
        if not isinstance(resource, p.Infra.RopeResource):  # untyped rope boundary
            message = f"declared module source is not a rope resource: {module}"
            raise TypeError(message)
        if resource.is_folder():
            path = Path(resource.real_path) / c.Infra.INIT_PY
            resource = cls.require_file_resource(
                cls.runtime_callable("rope.base.libutils", "path_to_resource")(
                    project, str(path), type="file"
                ),
                path,
            )
        return cls.require_source_module(project.get_pymodule(resource))

    @classmethod
    def require_parsed_module(cls, value: p.AttributeProbe) -> p.Infra.RopeParsedModule:
        """Admit native parsed modules through the existing runtime predicate.

        Returns:
            The original module exposing the parsed-module contract.

        Raises:
            TypeError: The native result is not a parsed module.

        """
        if not cls.pymodule(value):
            msg = "rope resource returned a non-parsed module"
            raise TypeError(msg)
        return value

    @classmethod
    def from_import_info(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopeFromImport]:
        return isinstance(
            value,
            cls.runtime_type("rope.refactor.importutils.importinfo", "FromImport"),
        )

    @classmethod
    def normal_import_info(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopeNormalImport]:
        return isinstance(
            value,
            cls.runtime_type("rope.refactor.importutils.importinfo", "NormalImport"),
        )

    @classmethod
    def assigned_name(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopeAssignedName]:
        return isinstance(
            value,
            cls.runtime_type("rope.base.pynamesdef", "AssignedName"),
        )

    @classmethod
    def abstract_class(
        cls, value: p.AttributeProbe
    ) -> TypeGuard[p.Infra.RopeClassObject]:
        """Return whether ``value`` is a Rope abstract class object.

        Returns:
            Whether ``value`` is a Rope abstract class object.

        """
        return isinstance(
            value,
            cls.runtime_type(c.Infra.ROPE_PYOBJECTS_MODULE, "AbstractClass"),
        )

    @classmethod
    def unresolved_witness(
        cls, value: p.AttributeProbe
    ) -> TypeGuard[p.Infra.RopeUnresolvedBase]:
        """Return whether ``value`` is an unresolved base witness.

        Rope dc15 keeps an ``UnresolvedBase`` in its MRO position by policy
        (TypedDict synthetic bases, staged renames): the witness occupies
        its slot, contributes no ancestors and never matches a first-party
        declaration. Classification consumers skip witnesses instead of
        rejecting the class that carries them.

        Returns:
            Whether ``value`` is an unresolved base witness.

        """
        return isinstance(
            value,
            cls.runtime_type(c.Infra.ROPE_PYOBJECTS_MODULE, "UnresolvedBase"),
        )

    @classmethod
    def instance_object(
        cls,
        value: p.AttributeProbe,
    ) -> TypeGuard[t.Infra.RopePyObject]:
        """Return whether ``value`` is a Rope inferred instance of a class.

        Rope infers a typed value (``facade: Facade = Facade()``) as an exact
        ``PyObject`` whose type is the declared class; classes, functions and
        modules are ``PyObject`` subclasses and never match.

        Returns:
            Whether ``value`` is a Rope inferred class instance.

        """
        return type(value) is cls.runtime_type(
            c.Infra.ROPE_PYOBJECTS_MODULE,
            "PyObject",
        )

    @classmethod
    def py_class(cls, value: p.AttributeProbe) -> TypeGuard[p.Infra.RopeSourceClass]:
        """Return whether ``value`` is a Rope class declared in Python source.

        Builtin classes (``Exception``, ``object``) are abstract classes too,
        but they have no source scope.

        Returns:
            Whether ``value`` is a Rope source-declared class object.

        """
        return isinstance(
            value,
            cls.runtime_type("rope.base.pyobjectsdef", "PyClass"),
        )

    @classmethod
    def py_function(
        cls, value: p.AttributeProbe
    ) -> TypeGuard[p.Infra.RopeSourceFunction]:
        """Identify a native source function retaining its callable role.

        Returns:
            Whether ``value`` is the SDK's source-defined function object.

        """
        return isinstance(
            value,
            cls.runtime_type("rope.base.pyobjectsdef", "PyFunction"),
        )

    @classmethod
    def defined_name(cls, value: p.AttributeProbe) -> bool:
        """Return whether ``value`` is a Rope defined name.

        Returns:
            Whether ``value`` is a Rope defined name.

        """
        return isinstance(value, cls.runtime_type("rope.base.pynames", "DefinedName"))

    @classmethod
    def imported_name(
        cls, value: p.Infra.RopePyName | None
    ) -> TypeIs[p.Infra.RopeImportedName]:
        """Return whether ``value`` is a Rope imported name.

        Returns:
            Whether ``value`` is a Rope imported name.

        """
        return isinstance(value, cls.runtime_type("rope.base.pynames", "ImportedName"))

    @classmethod
    def imported_module(
        cls, value: p.Infra.RopePyName | None
    ) -> TypeIs[p.Infra.RopeImportedModule]:
        """Prove native module-import provenance without evaluating the module.

        Returns:
            Whether the binding exposes the native module import contract.

        """
        return isinstance(
            value, cls.runtime_type("rope.base.pynames", "ImportedModule")
        )

    @classmethod
    def parameter_name(cls, value: p.AttributeProbe) -> bool:
        """Return whether ``value`` is a Rope parameter name.

        Returns:
            Whether ``value`` is a Rope parameter name.

        """
        return isinstance(
            value,
            cls.runtime_type("rope.base.pynamesdef", "ParameterName"),
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeTypes"]
