"""Origin resolution for automated accessor renames — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, u

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraAccessorOriginResolver:
    """Bind accessor declarations, introducing contracts and consumers through Rope."""

    def __init__(
        self,
        rope_project: t.Infra.RopeProject,
        *,
        namespace: str | None = None,
        module: str | None = None,
    ) -> None:
        """Initialize with the shared Rope project of the migration run.

        Args:
            rope_project: The shared Rope project of the migration run.
            namespace: Optional namespace to resolve.
            module: Optional module to resolve.

        Raises:
            ValueError: If the specified module is unknown.
        """
        self._rope_project = rope_project
        self._root = Path(rope_project.root.real_path)
        self._pymodules: dict[str, t.Infra.RopePyModule] = {}
        self._bindings: dict[str, dict[str, list[p.Infra.RopePyName]]] = {}
        self._owners: dict[int, p.Infra.RopePyObject] = {}
        self._names: dict[int, str] = {}
        self._introduced: dict[str, tuple[m.Infra.Object, ...]] = {}
        self._lineages: dict[int, tuple[p.Infra.RopePyObject, ...]] = {}
        self._namespace_owners: tuple[p.Infra.RopePyObject, ...] | None = None
        self._target_module = module
        self._policy = m.MethodShapeParams.model_validate(
            c.ENFORCEMENT_PREDICATE_SPECS["no_accessor_methods"]["params"]
        )
        projects = u.Infra.resolve_projects(self._root, ()).unwrap()
        if namespace is not None:
            alias = namespace.split(".", 1)[0]
            paths: list[Path] = []
            for project in projects:
                layout = u.Infra.layout(project.path, project=project)
                if layout is not None:
                    path = u.Infra.facade_module_path(layout.package_dir, alias)
                    if path is not None:
                        paths.append(path)
            self._namespace_owners = self.namespace_classes(paths, namespace)
        if module is not None and self._rope_project.find_module(module) is None:
            msg = f"unknown accessor module selector: {module}"
            raise ValueError(msg)

    def within_origin(self, definition_path: str, *, origin: str) -> bool:
        """Compare the canonical module identity, not a directory substring.

        Returns:
            The resulting ``bool``.

        """
        path = Path(definition_path)
        project_root = u.Infra.nearest_project_root(self._root, path)
        if project_root is None:
            return False
        module = u.Infra.module_name_for_file(path, project_root=project_root)
        return module.split(".", 1)[0] == origin

    @property
    def rope_project(self) -> p.Infra.RopeProject:
        """The one project whose original bindings this resolver authenticates."""
        return self._rope_project

    def module(self, py_file: Path) -> p.Infra.RopePyModule:
        """Return the original module snapshot or fail on an unknown source.

        Returns:
            The authenticated original Rope module.

        Raises:
            ValueError: If the source is absent from the project inventory.
        """
        key = str(py_file)
        if key not in self._pymodules:
            resource = u.Infra.resolve_resource_from_path(self._rope_project, py_file)
            if resource is None:
                msg = f"accessor source is outside the Rope inventory: {py_file}"
                raise ValueError(msg)
            self._pymodules[key] = u.Infra.resolve_pymodule(
                self._rope_project, resource
            )
        return self._pymodules[key]

    def class_lineage(
        self, owner: p.Infra.RopePyObject
    ) -> tuple[p.Infra.RopePyObject, ...]:
        """Use the existing C3 owner and reject incomplete superclass inference.

        Returns:
            The class followed by its resolved C3 ancestors.

        Raises:
            ValueError: If ancestry is cyclic, inconsistent or unresolved.
            TypeError: If the defining module has no syntax tree.
        """
        key = id(owner)
        if key in self._lineages:
            if not self._lineages[key]:
                msg = f"cyclic accessor ancestry: {owner.get_name()}"
                raise ValueError(msg)
            return self._lineages[key]
        self._lineages[key] = ()
        bases = tuple(owner.get_superclasses())
        scope = owner.get_scope() if u.Infra.py_class(owner) else None
        if scope is not None:
            module = owner.get_module()
            if module is None:
                msg = f"accessor class has no defining module: {owner.get_name()}"
                raise ValueError(msg)
            tree = module.get_ast()
            if not isinstance(tree, ast.AST):
                msg = "Rope class source has no syntax tree"
                raise TypeError(msg)
            declaration = next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                    and node.lineno == scope.get_start()
                ),
                None,
            )
            if declaration is None or len(bases) != len(declaration.bases):
                msg = f"unresolved accessor class ancestry: {owner.get_name()}"
                raise ValueError(msg)
        if any(not u.Infra.abstract_class(base) for base in bases):
            msg = f"unresolved accessor superclass: {owner.get_name()}"
            raise ValueError(msg)
        ancestors = tuple(self.class_lineage(base) for base in bases)
        objects = {str(id(item)): item for chain in ancestors for item in chain}
        ordered = u.Infra.merge_class_lineages(
            (
                *(tuple(str(id(item)) for item in chain) for chain in ancestors),
                tuple(str(id(base)) for base in bases),
            ),
            message=f"inconsistent accessor MRO: {owner.get_name()}",
        )
        lineage = (owner, *(objects[identity] for identity in ordered))
        self._lineages[key] = lineage
        return lineage

    def _index(self, py_file: Path) -> None:
        """Inventory direct functions and methods from semantic scopes once.

        Raises:
            ValueError: If a source, declaration or project owner is unresolved.
        """
        key = str(py_file)
        if key in self._bindings:
            return
        module = self.module(py_file)
        scope = module.get_scope()
        if scope is None:
            msg = f"accessor module has no declaration scope: {py_file}"
            raise ValueError(msg)
        project_root = u.Infra.nearest_project_root(self._root, py_file)
        if project_root is None:
            msg = f"accessor source has no project owner: {py_file}"
            raise ValueError(msg)
        metadata = u.Infra.read_project_metadata_result(project_root).unwrap()
        module_name = u.Infra.module_name_for_file(py_file, project_root=project_root)
        bindings: dict[str, list[p.Infra.RopePyName]] = {}
        introduced: list[m.Infra.Object] = []
        pending: list[tuple[p.Infra.RopeScope, tuple[str, ...]]] = [(scope, ())]
        while pending:
            current, chain = pending.pop()
            owner = current.pyobject if current.get_kind() == "Class" else None
            children = tuple(current.get_scopes())
            candidates = {
                child.pyobject.get_name()
                for child in children
                if child.get_kind() == "Function"
                and not child.pyobject.get_name().startswith("_")
                and (
                    child.pyobject.get_name() in c.ENFORCEMENT_ACCESSOR_RENAMES
                    or child.pyobject.get_name().startswith(
                        tuple(self._policy.forbidden_prefixes)
                    )
                )
            }
            inherited = (
                {
                    name
                    for base in self.class_lineage(owner)[1:]
                    for name in base.get_attributes()
                }
                if owner is not None and candidates
                else set()
            )
            for child in children:
                name = child.pyobject.get_name()
                if child.get_kind() == "Class":
                    pending.append((child, (*chain, name)))
                elif child.get_kind() == "Function":
                    pending.append((child, (*chain, name)))
                    binding = current.get_names().get(name)
                    if binding is None:
                        msg = f"accessor declaration has no binding: {py_file}:{name}"
                        raise ValueError(msg)
                    holder, line = binding.get_definition_location()
                    resource = holder.get_resource() if holder is not None else None
                    if (
                        resource is None
                        or resource.real_path != str(py_file)
                        or line != child.get_start()
                    ):
                        continue
                    bindings.setdefault(name, []).append(binding)
                    self._names[id(binding)] = name
                    if owner is not None:
                        self._owners[id(binding)] = owner
                        if (
                            name in candidates
                            and name not in inherited
                            and u.Infra.py_function(binding.get_object())
                        ):
                            introduced.append(
                                m.Infra.Object(
                                    file_path=str(py_file),
                                    line=child.get_start(),
                                    project=metadata.project.name,
                                    name=name,
                                    kind="method",
                                    module_name=module_name,
                                    scope_path=".".join((*chain, name)),
                                    class_path=".".join(chain),
                                )
                            )
        self._bindings[key] = bindings
        self._introduced[key] = tuple(introduced)

    def introduced_methods(self, py_file: Path) -> tuple[m.Infra.Object, ...]:
        """Return actual class introducers, including names outside the rename catalog.

        Returns:
            Existing canonical object records for selected direct introductions.
        """
        self._index(py_file)
        return tuple(
            item
            for item in self._introduced[str(py_file)]
            if self._declaration_selected(py_file, item)
        )

    def _declaration_selected(self, path: Path, item: m.Infra.Object) -> bool:
        """Select declaring identities while retaining all their consumers.

        Returns:
            Whether the declaration belongs to the selected module/facade scope.
        """
        if self._target_module is not None and not (
            item.module_name == self._target_module
            or item.module_name.startswith(self._target_module + ".")
        ):
            return False
        if self._namespace_owners is None:
            return True
        return any(
            binding.get_definition_location()[1] == item.line
            and self._owners.get(id(binding)) in self._namespace_owners
            for binding in self._bindings[str(path)].get(item.name, ())
        )

    def _binding_selected(self, binding: p.Infra.RopePyName) -> bool:
        """Check whether a binding retains a selected introducing contract.

        Returns:
            Whether this binding is eligible under the ownership selectors.
        """
        holder, _line = binding.get_definition_location()
        resource = holder.get_resource() if holder is not None else None
        if resource is None:
            return False
        origin = self._contract_origin(binding)
        if origin is None:
            return False
        if self._target_module is not None:
            root = u.Infra.nearest_project_root(self._root, Path(origin))
            module = (
                u.Infra.module_name_for_file(Path(origin), project_root=root)
                if root is not None
                else ""
            )
            if module != self._target_module and not module.startswith(
                self._target_module + "."
            ):
                return False
        if self._namespace_owners is None:
            return True
        owner = self._owners.get(id(binding))
        return owner is not None and any(
            base in self._namespace_owners
            and self._names[id(binding)] in base.get_attributes()
            for base in self.class_lineage(owner)
        )

    def _contract_origin(self, binding: p.Infra.RopePyName) -> str | None:
        """Resolve the sole introducing contract without changing inherited ownership.

        Returns:
            The introducing source path, or None for an ambiguous/native contract.
        """
        owner = self._owners.get(id(binding))
        if owner is None:
            holder, _line = binding.get_definition_location()
            resource = holder.get_resource() if holder is not None else None
            return resource.real_path if resource is not None else None
        name = self._names[id(binding)]
        lineage = self.class_lineage(owner)
        origins: set[str] = set()
        for base in lineage:
            scope = base.get_scope() if u.Infra.py_class(base) else None
            attributes = (
                scope.get_defined_names()
                if scope is not None
                else base.get_attributes()
            )
            declaration = attributes.get(name)
            if declaration is None or any(
                name in parent.get_attributes()
                for parent in self.class_lineage(base)[1:]
            ):
                continue
            holder, _line = declaration.get_definition_location()
            resource = holder.get_resource() if holder is not None else None
            if resource is None:
                return None
            origins.add(resource.real_path)
        return next(iter(origins)) if len(origins) == 1 else None

    def occurrence_origin(
        self,
        py_file: Path,
        offset: int,
        *,
        name: str,
    ) -> str | None:
        """Prove the selected introducing contract of the consumer at ``offset``.

        Returns:
            The resulting ``str | None`` — ``None`` marks an unresolvable,
            builtin, or out-of-project definition.

        """
        module = self.module(py_file)
        definition = u.Infra.name_definition_resource_path(module, offset)
        if definition is None:
            return None
        defining_file = Path(definition)
        if not defining_file.is_relative_to(self._root):
            return definition
        self._index(defining_file)
        for binding in self._bindings[str(defining_file)].get(name, ()):
            if u.Infra.name_definition_resource_path(
                module, offset, expected_binding=binding
            ) is not None and self._binding_selected(binding):
                return self._contract_origin(binding)
        return None

    def namespace_classes(
        self, py_files: t.SequenceOf[Path], selector: str
    ) -> tuple[p.Infra.RopePyObject, ...]:
        """Resolve a published facade alias and optional domain through real bindings.

        Returns:
            Selected namespace classes and their actual introducing ancestors.

        Raises:
            ValueError: If a selected facade/domain or its source is unknown.
        """
        alias, *domains = selector.split(".")
        if not alias or any(not part for part in domains):
            msg = f"unknown accessor facade namespace: {selector}"
            raise ValueError(msg)
        selected: list[p.Infra.RopePyObject] = []
        for path in py_files:
            resource = u.Infra.resolve_resource_from_path(self._rope_project, path)
            if resource is None:
                msg = f"accessor selector source is outside inventory: {path}"
                raise ValueError(msg)
            declared = u.Infra.published_facade_owner(self._rope_project, resource)
            if declared is None or declared[0] != alias:
                continue
            owner = self.module(path).get_attribute(declared[1]).get_object()
            for domain in domains:
                binding = owner.get_attributes().get(domain)
                if binding is None:
                    owner = None
                    break
                if not u.Infra.abstract_class(binding.get_object()):
                    msg = f"accessor namespace is not a class: {selector} in {path}"
                    raise ValueError(msg)
                owner = binding.get_object()
            if owner is not None:
                selected.extend(self.class_lineage(owner))
        if not selected:
            msg = f"accessor namespace selected no published facade: {selector}"
            raise ValueError(msg)
        return tuple(selected)


__all__: list[str] = ["FlextInfraAccessorOriginResolver"]
