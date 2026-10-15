"""Origin resolution for automated accessor renames — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra import u
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class FlextInfraAccessorOriginResolver:
    """Prove each rename occurrence is defined inside the rule's origin package.

    The rename catalog's ``origin`` names the owning distribution package
    (for example ``flext_core``). A rewrite may only touch occurrences whose
    defining module lives under that package: a homonym defined by the scanned
    repository, another library, or a builtin stays untouched and is reported
    as a skipped warning instead.
    """

    def __init__(self, rope_project: t.Infra.RopeProject) -> None:
        """Initialize with the shared Rope project of the migration run."""
        self._rope_project = rope_project
        self._pymodules: dict[str, t.Infra.RopePyModule] = {}

    @staticmethod
    def within_origin(definition_path: str, *, origin: str) -> bool:
        """Return whether ``definition_path`` lives inside the origin package.

        Returns:
            The resulting ``bool``.

        """
        return f"/{origin}/" in definition_path

    def occurrence_origin(
        self,
        py_file: Path,
        offset: int,
    ) -> str | None:
        """Resolve the defining module path of the name at ``offset``.

        Returns:
            The resulting ``str | None`` — ``None`` marks an unresolvable,
            builtin, or out-of-project definition.

        """
        resource = u.Infra.resolve_resource_from_path(self._rope_project, py_file)
        if resource is None:
            return None
        cache_key = str(py_file)
        if cache_key not in self._pymodules:
            self._pymodules[cache_key] = u.Infra.resolve_pymodule(
                self._rope_project,
                resource,
            )
        return u.Infra.name_definition_resource_path(
            self._pymodules[cache_key],
            offset,
        )

    def receiver_attributes(
        self,
        py_file: Path,
        source: str,
        receiver: ast.expr,
    ) -> t.MappingKV[str, p.Infra.RopePyName]:
        """Resolve actual receiver members without evaluating consumer code.

        Returns:
            The receiver's semantically resolved member definitions.

        Raises:
            ValueError: If the receiver has no established semantic identity.
        """
        attributes = self._receiver_object(py_file, source, receiver).get_attributes()
        if not attributes:
            msg = f"Unknown accessor receiver members: {py_file}:{receiver.lineno}"
            raise ValueError(msg)
        return attributes

    def _receiver_object(
        self, py_file: Path, source: str, receiver: ast.expr
    ) -> p.Infra.RopePyObject:
        """Resolve the exact receiver object through its lexical Rope binding.

        Returns:
            The actual receiver object, without executing consumer code.

        Raises:
            ValueError: If its resource or binding is unavailable.
        """
        resource = u.Infra.resolve_resource_from_path(self._rope_project, py_file)
        if resource is None:
            msg = f"Accessor source has no Rope resource: {py_file}"
            raise ValueError(msg)
        pymodule = u.Infra.resolve_pymodule(self._rope_project, resource)
        offset = u.Infra.source_offset(source, receiver)
        scope = u.Infra.scope_at(pymodule, offset)
        binding = u.Infra.resolve_symbol(scope, receiver)
        if binding is None:
            msg = f"Unresolved accessor receiver: {py_file}:{receiver.lineno}"
            raise ValueError(msg)
        return binding.get_object()

    def receiver_inherits(
        self,
        py_file: Path,
        source: str,
        receiver: ast.expr,
        declaring_class: str,
    ) -> bool:
        """Prove receiver lineage by native class and declaration object identity.

        Returns:
            Whether the configured declaration occurs in the actual lineage.

        Raises:
            ValueError: If receiver class identity or acyclic lineage is unproven.
        """
        target = self._receiver_object(py_file, source, receiver)
        if FlextInfraUtilitiesRopeRuntime.instance_object(target):
            target = target.get_type()
        if not FlextInfraUtilitiesRopeRuntime.abstract_class(target):
            msg = f"Unknown accessor receiver class: {py_file}:{receiver.lineno}"
            raise ValueError(msg)
        pending = [(target, frozenset[int]())]
        while pending:
            candidate, ancestors = pending.pop()
            if id(candidate) in ancestors:
                msg = f"Cyclic accessor receiver lineage: {py_file}:{receiver.lineno}"
                raise ValueError(msg)
            if self._matches_declaration(candidate, declaring_class):
                return True
            pending.extend(
                (base, ancestors | {id(candidate)})
                for base in candidate.get_superclasses()
            )
        return False

    @staticmethod
    def _matches_declaration(
        candidate: p.Infra.RopePyObject, declaring_class: str
    ) -> bool:
        """Compare a native class against its exact qualified declaration binding.

        Returns:
            Whether resolving that declaration produces the same native object.
        """
        module = candidate.get_module()
        if module is None:
            return False
        prefix = f"{module.get_name()}."
        if not declaring_class.startswith(prefix):
            return False
        names = declaring_class.removeprefix(prefix).split(".")
        binding = module.get_attributes().get(names[0])
        if binding is None:
            return False
        declared = binding.get_object()
        for name in names[1:]:
            binding = declared.get_attributes().get(name)
            if binding is None:
                return False
            declared = binding.get_object()
        return declared is candidate

    @staticmethod
    def declaring_class(binding: p.Infra.RopePyName) -> str | None:
        """Find the exact lexical class owning a Rope member definition.

        Returns:
            Its qualified declaration path, or None for a non-class binding.

        Raises:
            TypeError: If the defining module has no native Python module AST.
        """
        module, line = binding.get_definition_location()
        if module is None or line is None:
            return None
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            msg = "Accessor definition module has no Python module AST"
            raise TypeError(msg)
        classes: t.MutableSequenceOf[ast.ClassDef] = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and node.lineno <= line <= (node.end_lineno or node.lineno)
        ]
        if not classes:
            return None
        ordered = sorted(classes, key=lambda node: node.lineno)
        return ".".join((module.get_name(), *(node.name for node in ordered)))

    def require_normalizer_binding(
        self,
        py_file: Path,
        source: str,
        tree: ast.Module,
        node: ast.Attribute,
        *,
        rule: m.Infra.AccessorMigrationRule,
    ) -> None:
        """Reject aliases that would capture the introduced public facade.

        Raises:
            ValueError: If the selected facade is conflicting or locally shadowed.
        """
        prefix = rule.replacement_name.split(".", maxsplit=1)[0]
        resource = u.Infra.resolve_resource_from_path(self._rope_project, py_file)
        if resource is None:
            msg = f"Accessor source has no Rope resource: {py_file}"
            raise ValueError(msg)
        pymodule = u.Infra.resolve_pymodule(self._rope_project, resource)
        scope = u.Infra.scope_at(pymodule, u.Infra.source_offset(source, node))
        existing = u.Infra.resolve_symbol(
            scope,
            ast.Name(id=prefix, ctx=ast.Load()),
        )
        if existing is None:
            return
        runtime_import = any(
            isinstance(statement, ast.ImportFrom)
            and statement.level == 0
            and statement.module == rule.origin
            and any(
                alias.name == prefix and alias.asname is None
                for alias in statement.names
            )
            for statement in tree.body
        )
        module_binding = pymodule.get_attributes().get(prefix)
        if (
            not runtime_import
            or module_binding is None
            or not u.Infra.same_name(module_binding, existing)
        ):
            msg = f"Captured accessor normalizer facade: {py_file}:{node.lineno}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraAccessorOriginResolver"]
