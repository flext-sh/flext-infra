"""Origin resolution for automated accessor renames — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, p, u
from flext_infra.refactor._accessor import FlextInfraRefactorAccessorWarnings

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraRefactorAccessorOrigin:
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
        self._pymodules: t.MutableMappingKV[str, t.Infra.RopePyModule] = {}
        self._bindings: dict[str, dict[str, list[p.Infra.RopePyName]]] = {}
        self._owners: dict[int, p.Infra.RopePyObject] = {}
        self._names: dict[int, str] = {}
        self._introduced: dict[str, tuple[m.Infra.Object, ...]] = {}
        self._lineages: dict[int, tuple[p.Infra.RopePyObject, ...]] = {}
        self._namespace_owners: tuple[p.Infra.RopePyObject, ...] | None = None
        self._target_module = module
        self._forbidden_prefixes = (
            config.Infra.tooling.accessor_policy.forbidden_prefixes
        )
        self._renamed_accessors = frozenset(
            rule.source_name
            for rule in FlextInfraRefactorAccessorWarnings.automated_rules()
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
        owner = u.Infra.require_class_object(owner, "accessor lineage")
        key = id(owner)
        if key in self._lineages:
            if not self._lineages[key]:
                msg = f"cyclic accessor ancestry: {owner.get_name()}"
                raise ValueError(msg)
            return self._lineages[key]
        self._lineages[key] = ()
        bases = tuple(owner.get_superclasses())
        if u.Infra.py_class(owner):
            scope = owner.get_scope()
            module = owner.get_module()
            if not u.Infra.source_module(module):
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
            if declaration is None:
                msg = f"unresolved accessor class ancestry: {owner.get_name()}"
                raise ValueError(msg)
            scope = u.Infra.scope_at(
                module,
                u.Infra.source_offset(module.source_code, declaration),
                declaration_line=declaration.lineno,
            )
            # Generic subscriptions name their introducing class, not __getitem__.
            bases = tuple(
                binding.get_object()
                for expression in declaration.bases
                if (
                    binding := u.Infra.resolve_symbol(
                        scope,
                        expression.value
                        if isinstance(expression, ast.Subscript)
                        else expression,
                    )
                )
                is not None
            )
            if len(bases) != len(declaration.bases):
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

    @staticmethod
    def _scope_binding(
        current: p.Infra.RopeScope,
        child: p.Infra.RopeScope,
        name: str,
        py_file: Path,
    ) -> p.Infra.RopePyName | None:
        """Resolve the function binding admitted from one semantic scope.

        Args:
            current: The enclosing semantic scope holding the binding.
            child: The child scope being inventoried.
            name: The declared child scope name.
            py_file: The inventoried source file path.

        Returns:
            The admitted function binding, or ``None`` for a non-function
            scope declared outside this source file.

        Raises:
            ValueError: If the accessor declaration has no binding.

        """
        if child.get_kind() != "Function":
            return None
        binding = current.get_names().get(name)
        if binding is None:
            msg = f"accessor declaration has no binding: {py_file}:{name}"
            raise ValueError(msg)
        definition = binding.get_definition_location()
        resource = definition[0].get_resource() if definition[0] is not None else None
        if (
            resource is None
            or resource.real_path != str(py_file)
            or definition[1] != child.get_start()
        ):
            return None
        return binding

    def _admitted_introducer(
        self,
        binding: p.Infra.RopePyName,
        name: str,
        owner: p.Infra.RopePyObject,
    ) -> bool:
        """Whether one method binding introduces a forbidden accessor identity.

        Args:
            binding: The admitted function binding being judged.
            name: The declared binding name.
            owner: The owning class object of the method binding.

        Returns:
            Whether the binding renames or prefixes a forbidden accessor
            introduced by this owner.

        """
        if name.startswith("_"):
            return False
        if name not in self._renamed_accessors and not name.startswith(
            tuple(self._forbidden_prefixes)
        ):
            return False
        if not u.Infra.py_function(binding.get_object()):
            return False
        return any(
            u.Infra.same_name(binding, declaration)
            for declaration in self._introducing_bindings(owner, name)
        )

    def _index(self, py_file: Path) -> None:
        """Inventory direct functions and methods from semantic scopes once.

        Raises:
            ValueError: If a source, declaration or project owner is unresolved.

        """
        if str(py_file) in self._bindings:
            return
        scope = self.module(py_file).get_scope()
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
            for child in current.get_scopes():
                name = child.pyobject.get_name()
                pending.append((child, (*chain, name)))
                binding = self._scope_binding(current, child, name, py_file)
                if binding is None:
                    continue
                bindings.setdefault(name, []).append(binding)
                self._names[id(binding)] = name
                if owner is None:
                    continue
                self._owners[id(binding)] = owner
                if self._admitted_introducer(binding, name, owner):
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
        self._bindings[str(py_file)] = bindings
        self._introduced[str(py_file)] = tuple(introduced)

    def collect_manual_warnings(
        self,
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
        *,
        rules: t.SequenceOf[m.Infra.AccessorMigrationRule],
    ) -> tuple[m.Infra.AccessorMigrationChange, ...]:
        """Authenticate the snapshot and report selected introducing accessors.

        Returns:
            Manual review findings from the resolver's captured prefix policy.

        Raises:
            ValueError: If the source/project differs from the original Rope snapshot.

        """
        if (
            rope_project is not self._rope_project
            or source != self.module(py_file).source_code
        ):
            msg = f"accessor discovery source differs from Rope snapshot: {py_file}"
            raise ValueError(msg)
        self._index(py_file)
        warnings: list[m.Infra.AccessorMigrationChange] = []
        for declaration in self._introduced[str(py_file)]:
            if not self._declaration_selected(py_file, declaration):
                continue
            name = declaration.name
            prefix = next(
                (
                    prefix
                    for prefix in self._forbidden_prefixes
                    if name.startswith(prefix)
                ),
                None,
            )
            if prefix is None or name.startswith("_"):
                continue
            rule = next((rule for rule in rules if rule.source_name == name), None)
            if rule is not None and self.within_origin(
                str(py_file), origin=rule.origin
            ):
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=declaration.line,
                    original_name=name,
                    replacement_name="",
                    automated=False,
                    reason=(
                        "Owned introducing method "
                        f"{declaration.module_name}.{declaration.scope_path} "
                        "violates ban-accessor-method-name; "
                        f"{self._forbidden_prefixes[prefix]}; "
                        "an explicit domain rename decision is required."
                    ),
                ),
            )
        return tuple(warnings)

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

    def _introducing_bindings(
        self, owner: p.Infra.RopePyObject, name: str
    ) -> tuple[p.Infra.RopePyName, ...]:
        """Return direct introducing declarations for both discovery and consumers.

        Returns:
            Bindings whose classes introduce the name rather than override it.

        """
        introduced: list[p.Infra.RopePyName] = []
        for base in self.class_lineage(owner):
            scope = base.get_scope() if u.Infra.py_class(base) else None
            attributes = (
                scope.get_defined_names()
                if scope is not None
                else base.get_attributes()
            )
            declaration = attributes.get(name)
            if declaration is not None and not any(
                name in parent.get_attributes()
                for parent in self.class_lineage(base)[1:]
            ):
                introduced.append(declaration)
        return tuple(introduced)

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
        origins: set[str] = set()
        for declaration in self._introducing_bindings(owner, self._names[id(binding)]):
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
        if u.Infra.parameter_name(binding):
            module, line = binding.get_definition_location()
            if not u.Infra.source_module(module) or line is None:
                msg = f"Unresolved accessor parameter declaration: {py_file}"
                raise ValueError(msg)
            scope = module.get_scope().get_inner_scope_for_line(line)
            declaration = scope.pyobject.get_ast()
            if isinstance(declaration, c.Infra.AST_FUNCTION_TYPES):
                for argument in (
                    *declaration.args.posonlyargs,
                    *declaration.args.args,
                    *declaration.args.kwonlyargs,
                ):
                    if (
                        argument.annotation is not None
                        and scope.get_names().get(argument.arg) is binding
                    ):
                        declared = u.Infra.annotation_origin(
                            self._rope_project, argument.annotation, scope
                        )
                        if declared is None:
                            msg = (
                                "Unresolved accessor receiver annotation: "
                                f"{py_file}:{argument.lineno}"
                            )
                            raise ValueError(msg)
                        return declared.get_object()
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
        if u.Infra.instance_object(target):
            target = target.get_type()
        if not u.Infra.abstract_class(target):
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
                (
                    u.Infra.require_class_object(base, "accessor receiver lineage"),
                    ancestors | {id(candidate)},
                )
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


__all__: list[str] = ["FlextInfraRefactorAccessorOrigin"]
