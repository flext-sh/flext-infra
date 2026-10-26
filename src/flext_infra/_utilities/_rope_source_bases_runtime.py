"""Qualified runtime-base resolution and linearization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesInventory,
)


class FlextInfraUtilitiesRopeSourceBasesRuntime:
    """Qualified runtime-base resolution and linearization."""

    @classmethod
    def source_member_binding(
        cls,
        project: p.Infra.RopeProject,
        qualified: str | m.Infra.SourceClassReference,
        *,
        sources: t.MappingKV[str, t.Pair[Path, str]] | None = None,
    ) -> p.Infra.RopePyName:
        """Resolve the first declared member along its authenticated native C3 order.

        Typed base references resolve the class itself. Planned sources retain
        their original mapping; native resolution failures propagate unchanged.

        Returns:
            The member binding belonging to the exact source or external owner.

        """
        return cls._RuntimeBaseResolver(
            project, sources if sources is not None else {}, (), None
        ).source_member_binding(qualified)

    @staticmethod
    def merge_class_lineages[TIdentity: str | t.Pair[str, str]](
        lineages: t.SequenceOf[t.SequenceOf[TIdentity]],
        *,
        message: str,
    ) -> t.VariadicTuple[TIdentity]:
        """Merge declared ancestor sequences using their C3 ordering.

        Returns:
            The consistent ordered ancestors.

        Raises:
            ValueError: If no consistent ordering exists.

        """
        sequences = [list(lineage) for lineage in lineages]
        result: list[TIdentity] = []
        while any(sequences):
            candidate = next(
                (
                    sequence[0]
                    for sequence in sequences
                    if sequence
                    and all(sequence[0] not in other[1:] for other in sequences)
                ),
                None,
            )
            if candidate is None:
                raise ValueError(message)
            result.append(candidate)
            for sequence in sequences:
                if sequence and sequence[0] == candidate:
                    sequence.pop(0)
        return tuple(result)

    @classmethod
    def source_member_relocation(
        cls,
        project: p.Infra.RopeProject,
        receiver: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
        canonical: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
        member: str,
    ) -> bool:
        """Prove canonical source ancestry and absence of a retired member.

        Unknown bases and inconsistent C3 orders propagate their native failure.

        Returns:
            Whether every source ancestor leaves the member undeclared.

        """
        return cls._RuntimeBaseResolver(project, {}, (), None).member_relocation_origin(
            receiver, canonical, member
        )

    class _RuntimeBaseResolver:
        """Resolve owned classes in C3 order and external classes through Rope.

        Only configured roots mark model evaluation boundaries. No first-party
        module is imported or resolved from disk when its planned source exists.
        Provider reexports follow Rope's declared import provenance. Their source
        declarations, not Rope's possibly incomplete superclass inference, supply
        the ordered bases. Missing references and invalid inheritance fail
        loudly.
        """

        def member_relocation_origin(
            self,
            receiver: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
            canonical: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
            member: str,
        ) -> bool:
            """Prove both source lineages and refuse every existing old member.

            Returns:
                Whether both origins and the retired member absence are known.

            """
            self._object_id = self._external_reference("builtins", ("object",))
            lineage = self._linearize(self._external_identity(receiver[0].get_object()))
            if self._external_identity(canonical[0].get_object()) not in lineage:
                return False
            # Identical model objects need no reconstruction of their source MRO.
            if receiver[1].get_object() is not canonical[1].get_object() and (
                self._external_identity(canonical[1].get_object())
                not in self._linearize(
                    self._external_identity(receiver[1].get_object())
                )
            ):
                return False
            for ancestor in lineage:
                if ancestor in self._definitions:
                    if member in self._definitions[ancestor].members:
                        return False
                elif ancestor in self._external:
                    if member in self._external[ancestor].get_attributes():
                        return False
                else:
                    return False
            return True

        def source_member_binding(
            self, qualified: str | m.Infra.SourceClassReference
        ) -> p.Infra.RopePyName:
            """Read a member from the first native declaration in the source MRO.

            Returns:
                The native member binding owned by the first declaring ancestor.

            Raises:
                ValueError: If an owner scope or declared member cannot be proven.

            """
            if isinstance(qualified, m.Infra.SourceClassReference):
                return self._source_class_binding(qualified)
            receiver, _, member = qualified.rpartition(".")
            identity = self._resolve(self._root_reference(receiver))
            for ancestor in self._linearize(identity):
                binding = self._declared_member_binding(ancestor, member)
                if binding is not None:
                    return binding
            msg = f"model utility has no declared binding: {qualified}"
            raise ValueError(msg)

        def _declared_member_binding(
            self, ancestor: str, member: str
        ) -> p.Infra.RopePyName | None:
            """Read one declared binding from its authenticated native owner.

            Returns:
                The member declared by this owner, or no declaration.

            Raises:
                ValueError: If the native class scope has another source identity.

            """
            if ancestor in self._external:
                return self._external[ancestor].get_attributes().get(member)
            module_name, _class_name, line = ancestor.rsplit(":", 2)
            declaration_line = int(line)
            declared = self._providers[module_name]
            scope = declared.get_scope().get_inner_scope_for_line(declaration_line)
            if scope.get_start() != declaration_line:
                msg = f"native class scope does not identify source owner: {ancestor}"
                raise ValueError(msg)
            return scope.get_defined_names().get(member)

        def _source_class_binding(
            self, qualified: m.Infra.SourceClassReference
        ) -> p.Infra.RopePyName:
            """Resolve the native class declaration before reading its members.

            Returns:
                The proven binding of the declared source class.

            Raises:
                ValueError: If the native resource or scope has another identity.

            """
            self._prepare_ordering()
            identity = self._resolve(qualified)
            self._linearize(identity)
            if identity in self._external:
                return self._class_bindings[identity]
            module_name, class_name, line = identity.rsplit(":", 2)
            declared = self._providers[module_name]
            scope = declared.get_scope().get_inner_scope_for_line(int(line))
            parent = scope.parent
            if (
                scope.get_start() != int(line)
                or scope.pyobject.get_name() != class_name.rsplit(".", 1)[-1]
                or parent is None
            ):
                msg = f"native class scope does not identify source owner: {identity}"
                raise ValueError(msg)
            binding = parent.get_defined_names().get(scope.pyobject.get_name())
            if binding is None or binding.get_object() is not scope.pyobject:
                msg = f"Ambiguous source class binding: {identity}"
                raise ValueError(msg)
            return binding

        def __init__(
            self,
            project: p.Infra.RopeProject,
            sources: t.MappingKV[str, t.Pair[Path, str]],
            roots: t.StrSequence,
            extra_module_aliases: t.MappingKV[str, str] | None,
        ) -> None:
            """Bind the resolution inputs and initialize the derived state.

            Parameters:
                project: The open Rope project scoped to the analysis roots.
                sources: The qualified module name to captured path and source.
                roots: The configured root qualified names.
                extra_module_aliases: Facade alias maps read outside the sources.

            """
            self._project = project
            self._sources = sources
            self._roots = roots
            self._extra_module_aliases = extra_module_aliases
            self._definitions: t.MutableMappingKV[
                str, m.Infra.SourceClassDefinition
            ] = {}
            self._modules: t.MutableMappingKV[
                str,
                t.MappingKV[str, m.Infra.SourceClassReference | None],
            ] = {}
            self._providers: t.MutableMappingKV[str, t.Infra.RopePyModule] = {}
            self._namespaces: set[str] = set()
            self._module_aliases: t.MutableMappingKV[
                str, m.Infra.SourceClassReference
            ] = {}
            self._external: t.MutableMappingKV[str, t.Infra.RopePyObject] = {}
            self._class_bindings: t.MutableMappingKV[str, p.Infra.RopePyName] = {}
            self._linearizations: t.MutableMappingKV[str, t.StrTuple] = {}
            self._active: set[str] = set()
            self._resolved_memo: t.MutableMappingKV[str, str] = {}
            self._ordering_ready = False
            self._native_module_type = FlextInfraUtilitiesRopeRuntime.runtime_type(
                "rope.base.builtins",
                "BuiltinModule",
            )
            self._object_id = ""

        def run(self) -> t.StrTuple:
            """Index every captured module and derive the ordered base set.

            Returns:
                Sorted configured roots and derived Ruff-qualified base
                expressions.

            """
            self._index_modules()
            self._build_module_alias_map()
            self._object_id = self._external_reference("builtins", ("object",))
            return self._derived_roots()

        def class_order(
            self,
            declarations: t.SequenceOf[m.Infra.SourceClassReference],
        ) -> t.StrTuple:
            """Order declared owners from their authoritative source ancestry.

            Returns:
                Declaration spellings in consistent source precedence order.

            Raises:
                ValueError: If declared identities duplicate or C3 conflicts.

            """
            self._prepare_ordering()
            identities = tuple(self._resolve(item) for item in declarations)
            if len(set(identities)) != len(identities):
                message = "Duplicate declared facade owner"
                raise ValueError(message)
            lineage = FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                (*(self._linearize(identity) for identity in identities),),
                message=(
                    "Inconsistent declared facade owner precedence: declarations="
                    f"{tuple(item.qualified_base for item in declarations)}"
                ),
            )
            spellings = {
                identity: item.qualified_base
                for identity, item in zip(identities, declarations, strict=True)
            }
            return tuple(
                spellings[identity] for identity in lineage if identity in spellings
            )

        def class_reaches(
            self,
            declarations: t.SequenceOf[m.Infra.SourceClassReference],
            anchors: t.SequenceOf[m.Infra.SourceClassReference],
        ) -> t.VariadicTuple[frozenset[str]]:
            """Report which anchors each declaration's source C3 ancestry holds.

            Returns:
                Per declaration, the anchor spellings its linearization holds.

            """
            self._prepare_ordering()
            anchored = {self._resolve(item): item.qualified_base for item in anchors}
            return tuple(
                frozenset(
                    anchored[identity]
                    for identity in self._linearize(self._resolve(item))
                    if identity in anchored
                )
                for item in declarations
            )

        def _prepare_ordering(self) -> None:
            """Build the namespace and alias maps once per resolver.

            The captured sources are immutable for the resolver's lifetime,
            so every memoized resolution and linearization serves the
            following questions.
            """
            if self._ordering_ready:
                return
            self._namespaces = {
                ".".join(parts[:index])
                for module in self._sources
                for parts in (module.split("."),)
                for index in range(1, len(parts) + 1)
            }
            self._build_module_alias_map()
            self._object_id = self._external_reference("builtins", ("object",))
            self._ordering_ready = True

        def _index_modules(self) -> None:
            """Index captured modules without changing interpreter resource policy."""
            self._modules = {
                module: self._inventory(module, captured)
                for module, captured in self._sources.items()
            }
            self._namespaces = {
                ".".join(parts[:index])
                for module in self._modules
                for parts in (module.split("."),)
                for index in range(1, len(parts) + 1)
            }

        def _build_module_alias_map(self) -> None:
            """Merge the captured and extra lazy-export alias maps.

            A lazy re-export alias is a module-local binding, never a global
            rename. When its name collides with a real analyzed module (or
            namespace), the real module wins: an absolute import elsewhere in
            the tree refers to the real module — a facade re-exporting a
            subpackage named like the project package must not shadow it
            (cosmos-docgen tests/unit re-exports a `dcdoc` subpackage; class
            bases declared as `from dcdoc import DcdocServiceBase` mean the
            project one).

            Consumed provider files are not a complete package inventory.
            Membership comes from the injected project's complete native source
            snapshot, including declared additions and retirements; captured
            initializer bytes still own the lazy bindings.

            Raises:
                ValueError: Native package membership differs from its source snapshot.

            """
            for alias_module, captured in self._sources.items():
                alias_path, alias_source = captured
                if alias_path.name != c.Infra.INIT_PY:
                    continue
                root = Path(self._project.root.real_path)
                relative_parent = alias_path.parent.relative_to(root).as_posix()
                if self._project.root.has_child(relative_parent):
                    expected = {
                        path
                        for path in self._project.source_children(alias_path.parent)
                        if path.suffix == c.Infra.EXT_PYTHON
                        and self._project.source_query(path, "isfile")
                    }
                    folder = self._project.get_folder(relative_parent)
                    actual = {
                        Path(child.real_path)
                        for child in folder.get_children()
                        if not child.is_folder()
                        and Path(child.real_path).suffix == c.Infra.EXT_PYTHON
                    }
                    if actual != expected:
                        message = (
                            "native lazy alias membership differs: "
                            f"{alias_path.parent}; "
                            f"project={root}; alias={alias_module}; "
                            "expected="
                            f"{tuple(sorted(path.name for path in expected))}; "
                            f"observed={tuple(sorted(path.name for path in actual))}"
                        )
                        raise ValueError(message)
                relative = alias_path.relative_to(root).as_posix()
                if self._project.root.has_child(relative):
                    resource = self._project.get_resource(relative)
                    FlextInfraUtilitiesRopeRuntime.require_file_resource(
                        resource, alias_path
                    ).read()
                for alias, binding in (
                    FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                        alias_module,
                        alias_path,
                        alias_source,
                        project=self._project,
                    )
                ).items():
                    qualified_alias = f"{alias_module}.{alias}"
                    if (
                        qualified_alias in self._modules
                        or qualified_alias in self._namespaces
                    ):
                        continue
                    self._module_aliases.setdefault(qualified_alias, binding)
            for alias, absolute in (self._extra_module_aliases or {}).items():
                if alias in self._modules or alias in self._namespaces:
                    continue
                self._module_aliases.setdefault(
                    alias,
                    m.Infra.SourceClassReference(
                        target=absolute,
                        attributes=(alias.rpartition(".")[2],),
                        qualified_base=alias,
                    ),
                )

        def _derived_roots(self) -> t.StrTuple:
            """Linearize every owned definition and collect the derived bases.

            Required provider parents participate in C3, but only captured
            project expressions belong to the project's generated Ruff
            configuration.

            Returns:
                The sorted union of configured roots and derived bases.

            """
            root_ids = frozenset(
                self._resolve(self._root_reference(root)) for root in self._roots
            )
            derived = set(self._roots)
            for definition in tuple(self._definitions.values()):
                self._linearize(definition.identity)
                for reference in definition.bases:
                    lineage = self._linearize(self._resolve(reference))
                    if root_ids.intersection(lineage):
                        derived.add(reference.qualified_base)
            return tuple(sorted(derived))

        def _inventory(
            self,
            module: str,
            captured: t.Pair[Path, str],
            *,
            required_line: int | None = None,
            allow_conditional: bool = False,
            provider: t.Infra.RopePyModule | None = None,
        ) -> t.MappingKV[str, m.Infra.SourceClassReference | None]:
            """Index lexical bindings without installing a cross-module overlay.

            A provider class is indexed at its native declaration line.
            Unreferenced module-level provider classes remain qualified
            declarations, not fabricated lineages. A captured class owns its
            nested declaration identities.

            Parameters:
                module: The qualified module name under inventory.
                captured: The module's path and captured source text.
                required_line: When set, index only bindings visible at the line.
                allow_conditional: Whether conditional bindings may degrade.
                provider: Existing Rope module owning the same captured source.

            Returns:
                The module's explicit lexical bindings, including value
                shadowing.

            Raises:
                ValueError: If the source provider is ambiguous.

            """
            path, source = captured
            if provider is None:
                relative = path.relative_to(
                    Path(self._project.root.real_path)
                ).as_posix()
                resource = self._project.get_resource(relative)
                # Derived facade text retains its original file input epoch.
                FlextInfraUtilitiesRopeRuntime.require_file_resource(
                    resource, path
                ).read()
                provider = FlextInfraUtilitiesRopeRuntime.build_string_module(
                    self._project, source, resource=resource
                )
            previous = self._providers.get(module)
            if previous is not None and (
                previous.get_resource() != provider.get_resource()
                or previous.source_code != provider.source_code
            ):
                message = f"Ambiguous source provider: {module}"
                raise ValueError(message)
            request = m.Infra.SourceBindingInventoryRequest(
                project=self._project,
                module=module,
                path=path,
                source=source,
                required_line=required_line,
                allow_conditional=allow_conditional,
            )
            bindings = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
                request,
                self._definitions,
                provider=provider,
            )
            self._providers[module] = provider
            return bindings

        def _external_identity(self, value: t.Infra.RopePyObject) -> str:
            """Return the declaration identity of one external Rope object.

            Raises:
                TypeError: If Rope resolves a required base to a non-class.

            """
            function_identity = self._function_object_identity(value)
            if function_identity is not None:
                return function_identity
            if not FlextInfraUtilitiesRopeRuntime.abstract_class(value):
                message = "Rope did not resolve a required base to a class"
                raise TypeError(message)
            if FlextInfraUtilitiesRopeRuntime.py_class(value):
                return self._pyclass_identity(value)
            return self._deduplicated_external_identity(value)

        @staticmethod
        def _function_object_identity(
            value: t.Infra.RopePyObject,
        ) -> str | None:
            """Return the constructed class identity of a TypedDict/NamedTuple.

            TypedDict and NamedTuple build their classes through function calls,
            so Rope resolves the declared base to a PyFunction; the base identity
            is still the class that call constructs at runtime.

            Returns:
                The constructed class identity, or None for other objects.

            """
            if not FlextInfraUtilitiesRopeRuntime.py_function(value):
                return None
            if value.get_name() not in {"TypedDict", "NamedTuple"}:
                return None
            module = value.get_module()
            module_name = module.get_name()
            name = value.get_name()
            return f"{module_name}.{name}" if module_name else name

        def _pyclass_identity(self, value: p.Infra.RopeSourceClass) -> str:
            """Return the declaration identity of one external Rope class.

            Returns:
                The resolved declaration identity.

            Raises:
                ValueError: If the class has no source declaration.

            """
            module = value.get_module()
            scope = value.get_scope()
            resource = module.get_resource()
            if (
                not FlextInfraUtilitiesRopeRuntime.source_module(module)
                or resource is None
            ):
                message = (
                    f"External class has no source declaration: {value.get_name()}"
                )
                raise ValueError(message)
            owners = tuple(
                name
                for name, (path, _source) in self._sources.items()
                if str(path) == resource.real_path
            )
            if len(owners) > 1:
                message = f"Ambiguous captured source owner: {resource.real_path}"
                raise ValueError(message)
            name = owners[0] if owners else module.get_name()
            previous = self._providers.get(name)
            if previous is not None and (
                previous.get_resource() != resource
                or (
                    name not in self._sources
                    and previous.source_code != module.source_code
                )
            ):
                message = f"Ambiguous source provider: {name}"
                raise ValueError(message)
            if name in self._sources:
                captured = self._sources[name]
                if str(captured[0]) != resource.real_path:
                    message = f"Source class resource does not identify owner: {name}"
                    raise ValueError(message)
                if name not in self._modules:
                    self._modules[name] = self._inventory(
                        name,
                        captured,
                        provider=module if module.source_code == captured[1] else None,
                    )
            line = scope.get_start()
            if name in self._modules:
                return self._declared_pyclass_identity(value, module, name, line)
            return self._inventory_pyclass_identity(name, module, line)

        def _declared_pyclass_identity(
            self,
            value: p.Infra.RopeNamedObject,
            module: t.Infra.RopePyModule,
            name: str,
            line: int,
        ) -> str:
            """Resolve one external class declared in a captured module.

            Rope may read an installed copy of the module; the planned source
            owns the module, so the declaration's dotted path resolves through
            the planned bindings, never through the installed copy's lines.

            Returns:
                The resolved declaration identity.

            Raises:
                TypeError: If the captured module has no module AST.
                ValueError: If no class declaration encloses the line.

            """
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                message = f"External class has no module AST: {name}"
                raise TypeError(message)
            path = ".".join(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
                and node.lineno <= line <= (node.end_lineno or node.lineno)
            )
            if not path or path.rsplit(".", 1)[-1] != value.get_name():
                message = f"Missing external class declaration: {name}:{line}"
                raise ValueError(message)
            return self._resolve(
                m.Infra.SourceClassReference(
                    target=name,
                    attributes=tuple(path.split(".")),
                    qualified_base=f"{name}.{path}",
                ),
            )

        def _inventory_pyclass_identity(
            self,
            name: str,
            module: t.Infra.RopePyModule,
            line: int,
        ) -> str:
            """Index the completed provider namespace and find its declaration.

            Returns:
                The resolved declaration identity.

            Raises:
                ValueError: If no class declaration encloses the line.

            """
            identity = self._declared_identity_at_line(name, line)
            if identity is None:
                resource = module.get_resource()
                if resource is None:
                    message = f"Module has no declared resource: {name}"
                    raise ValueError(message)
                # Module execution can publish class members after the body's
                # declaration line; its final bindings own the exported class.
                self._inventory(
                    name,
                    (Path(resource.real_path), module.source_code),
                    allow_conditional=True,
                    provider=module,
                )
                identity = self._declared_identity_at_line(name, line)
            if identity is None:
                message = f"Missing external class declaration: {name}:{line}"
                raise ValueError(message)
            return identity

        def _declared_identity_at_line(self, name: str, line: int) -> str | None:
            """Return the definition identity declared at one line, or None.

            Returns:
                The definition identity declared at the line, or None.

            """
            prefix = f"{name}:"
            suffix = f":{line}"
            return next(
                (
                    identity
                    for identity in self._definitions
                    if identity.startswith(prefix) and identity.endswith(suffix)
                ),
                None,
            )

        def _deduplicated_external_identity(self, value: t.Infra.RopePyObject) -> str:
            """Return a stable shared identity for one external runtime object."""
            for identity, known in self._external.items():
                if known == value or (
                    isinstance(known, p.Infra.RopeBuiltinClass)
                    and isinstance(value, p.Infra.RopeBuiltinClass)
                    and known.builtin is value.builtin
                ):
                    return identity
            identity = f"external:{len(self._external)}"
            self._external[identity] = value
            return identity

        def _provider_module(
            self,
            imported: p.Infra.RopeImportedModule,
        ) -> t.Infra.RopeSemanticModule:
            """Return the Rope module object one import points at.

            Returns:
                The resolved Rope module object.

            Raises:
                ValueError: The import has no declared module location.

            """
            if imported.resource is not None:
                return FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self._project,
                    imported.resource,
                )
            if imported.module_name is None:
                message = "Import has no declared module location"
                raise ValueError(message)
            source = imported.importing_module.get_module().get_resource()
            folder = source.parent if source is not None else None
            if imported.level:
                if folder is None:
                    message = "Import has no declared module location"
                    raise ValueError(message)
                module = self._project.get_relative_module(
                    imported.module_name,
                    folder,
                    imported.level,
                )
            else:
                module = self._project.get_module(imported.module_name, folder)
            return FlextInfraUtilitiesRopeRuntime.require_semantic_module(module)

        def _provider_reference(
            self,
            module: t.Infra.RopeSemanticModule,
            attributes: t.StrTuple,
            visiting: frozenset[str] = frozenset(),
            depth: int = 0,
        ) -> str:
            """Follow one provider module's reexport chain to a class identity.

            Completed owned-source bindings take precedence over stale imports.
            Providers retain their native Rope import provenance.

            Returns:
                The resolved declaration identity.

            Raises:
                ValueError: If the walk exceeds the depth budget, uses a module
                    as a class base, or cycles through provider reexports.

            """
            if depth > c.Infra.ROPE_WALK_DEPTH_BUDGET:
                message = (
                    f"Unresolved external base: {module.get_name()} at depth {depth}"
                )
                raise ValueError(message)
            if not attributes:
                message = f"Module used as a class base: {module.get_name()}"
                raise ValueError(message)
            name, *remaining = attributes
            target = f"{module.get_name()}.{name}"
            if target in visiting:
                chain = " <- ".join(sorted(visiting))
                message = f"Cyclic provider reexport: {target} (visiting: {chain})"
                raise ValueError(message)
            if name not in module.get_attributes():
                aliases = self._provider_lazy_bindings(module)
                provider = aliases.get(name)
                if provider is not None:
                    return self._resolve(
                        m.Infra.SourceClassReference(
                            target=provider.target,
                            attributes=(*provider.attributes, *remaining),
                            qualified_base=target,
                        ),
                        visiting | {target},
                        depth + 1,
                    )
                reexporter = self._star_reexporter(module, name)
                if reexporter is not None:
                    return self._provider_reference(
                        reexporter,
                        attributes,
                        visiting | {target},
                        depth + 1,
                    )
            try:
                binding = module.get_attribute(name)
            except (
                FlextInfraUtilitiesRopeRuntime.rope_attribute_not_found_error_types()
            ) as exc:
                resource = module.get_resource()
                exc.add_note(
                    f"Provider base reference: {target}; source="
                    f"{resource.real_path if resource is not None else '<native>'}"
                )
                raise
            if isinstance(binding, p.Infra.RopeImportedName):
                override = self._captured_import_override(module, binding, attributes)
                if override is not None:
                    return self._resolve(override, visiting | {target}, depth + 1)
                return self._provider_imported_name_reference(
                    binding,
                    remaining,
                    target,
                    visiting,
                    depth,
                )
            if isinstance(binding, p.Infra.RopeImportedModule):
                return self._provider_imported_module_reference(
                    binding,
                    remaining,
                    target,
                    visiting,
                    depth,
                )
            return self._provider_value_reference(
                binding, tuple(remaining), visiting, depth
            )

        def _captured_import_override(
            self,
            module: t.Infra.RopeSemanticModule,
            binding: p.Infra.RopeImportedName,
            attributes: t.StrTuple,
        ) -> m.Infra.SourceClassReference | None:
            """Prefer captured owned-source bindings over stale native imports.

            Returns:
                The owned source override; external providers keep native imports.

            Raises:
                ValueError: If the source binding has no declared provider.

            """
            module_name = module.get_name()
            if module_name not in self._sources:
                return None
            declaring = module.get_module()
            if not FlextInfraUtilitiesRopeRuntime.source_module(declaring):
                return None
            resource = declaring.get_resource()
            if resource is None:
                return None
            name, *remaining = attributes
            captured = self._sources[module_name]
            bindings = self._inventory(
                module_name,
                captured,
                allow_conditional=False,
                provider=declaring if declaring.source_code == captured[1] else None,
            )
            reference = bindings.get(name)
            if reference is None:
                message = f"Unresolved provider base: {module_name}.{name}"
                raise ValueError(message)
            if (
                reference.target in self._definitions
                or reference.target
                != self._provider_module(binding.imported_module).get_name()
                or reference.attributes != (binding.imported_name,)
            ):
                return m.Infra.SourceClassReference(
                    target=reference.target,
                    attributes=(*reference.attributes, *remaining),
                    qualified_base=f"{module_name}.{name}",
                )
            return None

        def _provider_value_reference(
            self,
            binding: p.Infra.RopePyName,
            remaining: t.StrTuple,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve native value ancestry and its remaining class members.

            Returns:
                The declaration identity reached by the original member sequence.

            """
            value = binding.get_object()
            if remaining and FlextInfraUtilitiesRopeRuntime.instance_object(value):
                # Attribute access on a facade instance (``meltano.Tap``)
                # reaches the class attribute through the instance's type.
                value = value.get_type()
            identity = self._external_identity(value)
            if identity in self._external and binding.get_object() is value:
                self._class_bindings[identity] = binding
            for attribute in remaining:
                identity = self._member(identity, attribute, depth + 1, visiting)
            return identity

        def _provider_lazy_bindings(
            self,
            module: t.Infra.RopeSemanticModule,
        ) -> t.MappingKV[str, m.Infra.SourceClassReference]:
            """Read a provider's declared lazy aliases from its native source module.

            Returns:
                Declared provider modules keyed by their lazy aliases.

            """
            declaring = module.get_module()
            if not FlextInfraUtilitiesRopeRuntime.source_module(declaring):
                return {}
            resource = declaring.get_resource()
            if resource is None:
                return {}
            return FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                module.get_name(),
                Path(resource.real_path),
                declaring.source_code,
                project=self._project,
                pymodule=declaring,
            )

        def _star_reexporter(
            self,
            module: t.Infra.RopeSemanticModule,
            name: str,
        ) -> t.Infra.RopeSemanticModule | None:
            """Return the module a provider star re-export binds ``name`` from.

            ``from .reader import *`` binds every public name of ``.reader`` in
            the provider (PyYAML's ``yaml.loader`` declares
            ``class SafeLoader(Reader, ...)`` that way). Rope drops such an
            import when its ``ignore_bad_imports`` preference cannot evaluate
            the module, so the walk reads the provider's own ``ImportFrom``
            nodes and resolves each star target itself.

            Returns:
                The first star-imported module that binds ``name``, or ``None``
                when no star re-export of the provider binds it.

            Raises:
                TypeError: A source provider has no native parsed module.

            """
            # A native module (no source resource) has no star re-export.
            resource = module.get_resource()
            if resource is None or name.startswith("_"):
                return None
            if not FlextInfraUtilitiesRopeRuntime.pymodule(module):
                message = "Rope source provider has no parsed module"
                raise TypeError(message)
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                return None
            file_name = Path(resource.real_path).name
            package = (
                module.get_name()
                if file_name == c.Infra.INIT_PY or not file_name.endswith(".py")
                else module.get_name().rpartition(".")[0]
            )
            for node in tree.body:
                if not (
                    isinstance(node, ast.ImportFrom)
                    and [alias.name for alias in node.names] == ["*"]
                ):
                    continue
                target = importlib.util.resolve_name(
                    "." * node.level + (node.module or ""),
                    package,
                )
                provider = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                    self._project.get_module(target)
                )
                if name in provider.get_attributes():
                    return provider
            return None

        def _provider_imported_name_reference(
            self,
            binding: p.Infra.RopeImportedName,
            remaining: t.StrSequence,
            target: str,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve one provider imported-name binding to an identity.

            Returns:
                The resolved declaration identity.

            """
            imported = self._provider_module(binding.imported_module)
            imported_name = imported.get_name()
            if (
                target == f"{imported_name}.{binding.imported_name}"
                and self._project.find_module(target) is not None
            ):
                # ``from . import child`` binds a real submodule, not a
                # reexport of the package attribute currently being resolved.
                return self._external_reference(
                    target, tuple(remaining), visiting | {target}, depth + 1
                )
            if imported_name in self._namespaces:
                return self._resolve(
                    m.Infra.SourceClassReference(
                        target=imported_name,
                        attributes=(binding.imported_name, *remaining),
                        qualified_base=target,
                    ),
                    visiting | {target},
                    depth + 1,
                )
            return self._provider_reference(
                imported,
                (binding.imported_name, *remaining),
                visiting | {target},
                depth + 1,
            )

        def _provider_imported_module_reference(
            self,
            binding: p.Infra.RopeImportedModule,
            remaining: t.StrSequence,
            target: str,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve one provider imported-module binding to an identity.

            Returns:
                The resolved declaration identity.

            """
            imported = self._provider_module(binding)
            imported_name = imported.get_name()
            if imported_name in self._namespaces:
                return self._resolve(
                    m.Infra.SourceClassReference(
                        target=imported_name,
                        attributes=tuple(remaining),
                        qualified_base=target,
                    ),
                    visiting | {target},
                    depth + 1,
                )
            return self._provider_reference(
                imported,
                tuple(remaining),
                visiting | {target},
                depth + 1,
            )

        def _external_reference(
            self,
            target: str,
            attributes: t.StrTuple,
            visiting: frozenset[str] = frozenset(),
            depth: int = 0,
        ) -> str:
            """Resolve one external qualified target through Rope.

            The injected project retains its original native-module election.
            A compiled extension has no source for Rope to parse; its import
            spec, resolved on demand, admits it as Rope's native module.
            Resolution and attribute errors propagate unchanged.

            Returns:
                The resolved declaration identity.

            """
            resource = self._project.find_module(target)
            spec = None if resource is not None else importlib.util.find_spec(target)
            module = (
                FlextInfraUtilitiesRopeRuntime.runtime_callable(
                    "rope.base.builtins", "BuiltinModule"
                )(target, FlextInfraUtilitiesRopeRuntime.project_core(self._project))
                if spec is not None
                and isinstance(spec.loader, importlib.machinery.ExtensionFileLoader)
                else self._project.get_module(target)
            )
            if resource is not None and not isinstance(
                module,
                self._native_module_type,
            ):
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self._project,
                    resource,
                )
            return self._provider_reference(
                FlextInfraUtilitiesRopeRuntime.require_semantic_module(module),
                attributes,
                visiting,
                depth,
            )

        def _resolve(
            self,
            reference: m.Infra.SourceClassReference,
            visiting: frozenset[str] = frozenset(),
            depth: int = 0,
        ) -> str:
            """Resolve one source class reference to a declaration identity.

            The dotted path is a binding path: every step reads the current
            module binding, submodule, or class member, so a rebinding after
            the declaration (``reflected.Contract = replacement``) replaces
            the declared lineage instead of being shadowed by it.

            Returns:
                The resolved declaration identity.

            Raises:
                ValueError: If the walk exceeds the depth budget, cycles
                    through class aliases, or resolves a module as a base.

            """
            if depth > c.Infra.ROPE_WALK_DEPTH_BUDGET:
                message = (
                    f"Unresolved external base: {reference.target} at depth {depth}"
                )
                raise ValueError(message)
            target, attributes = self._alias_rewritten_target(reference)
            key = ".".join((target, *attributes))
            if key in visiting:
                message = f"Cyclic class alias: {key}"
                raise ValueError(message)
            memo = self._resolved_memo.get(key)
            if memo is not None:
                return memo
            target, attributes = self._unresolved_target(
                target,
                list(attributes),
                key,
                visiting,
                depth,
            )
            for attribute in attributes:
                target = self._member(target, attribute, 0, visiting)
            self._resolved_memo[key] = target
            return target

        def _alias_rewritten_target(
            self,
            reference: m.Infra.SourceClassReference,
        ) -> t.Pair[str, t.StrTuple]:
            """Rewrite facade-qualified targets through the lazy alias map.

            The alias map routes a published name to its provider module, so
            the name itself stays the first attribute looked up there.

            Returns:
                The rewritten target and its remaining attribute path.

            """
            target = reference.target
            attributes = reference.attributes
            if target in self._module_aliases:
                binding = self._module_aliases[target]
                return (
                    binding.target,
                    (*binding.attributes, *attributes),
                )
            if attributes:
                qualified_head = f"{target}.{attributes[0]}"
                if qualified_head in self._module_aliases:
                    binding = self._module_aliases[qualified_head]
                    return binding.target, (*binding.attributes, *attributes[1:])
            return target, attributes

        def _unresolved_target(
            self,
            target: str,
            attributes: list[str],
            key: str,
            visiting: frozenset[str],
            depth: int,
        ) -> t.Pair[str, list[str]]:
            """Resolve a target that is not a direct definition key.

            Returns:
                The resolved target and its remaining attribute path.

            """
            if target in self._definitions or target in self._external:
                return target, attributes
            parts = target.split(".")
            if parts[0] in self._namespaces:
                return self._resolve_namespace_prefix(
                    parts,
                    attributes,
                    key,
                    visiting,
                    depth,
                )
            resolved = self._external_reference(
                target,
                tuple(attributes),
                visiting,
                depth + 1,
            )
            return resolved, []

        def _resolve_namespace_prefix(
            self,
            parts: t.StrSequence,
            attributes: list[str],
            key: str,
            visiting: frozenset[str],
            depth: int,
        ) -> t.Pair[str, list[str]]:
            """Resolve a namespace-qualified target through its planned module.

            A name the planned module does not bind continues into the captured
            submodule of that name, as ``from package import submodule`` does;
            an explicit package binding (class or value) keeps precedence over
            the file name. Captured package prefixes do not imply a complete
            child inventory: an uncaptured child retains the injected project's
            exact native module election, without importing its runtime package.

            Returns:
                The resolved target and its remaining attribute path.

            Raises:
                ValueError: If a module is used as a class base, the namespace
                    has no module binding, or the name is unresolved.

            """
            index = next(
                index
                for index in range(len(parts), 0, -1)
                if ".".join(parts[:index]) in self._namespaces
            )
            module = ".".join(parts[:index])
            remaining = [*parts[index:], *attributes]
            while True:
                if not remaining:
                    message = f"Module used as a class base: {module}"
                    raise ValueError(message)
                name = remaining.pop(0)
                if module not in self._modules and module in self._sources:
                    self._modules[module] = self._inventory(
                        module, self._sources[module]
                    )
                bound = module in self._modules and name in self._modules[module]
                submodule = f"{module}.{name}"
                if bound:
                    break
                if submodule not in self._namespaces:
                    if self._project.find_module(submodule) is not None:
                        return self._external_reference(
                            submodule, tuple(remaining), visiting, depth + 1
                        ), []
                    break
                module = submodule
            if module not in self._modules:
                message = f"Planned namespace has no module binding: {module}.{name}"
                raise ValueError(message)
            binding = self._modules[module].get(name)
            if binding is None:
                message = f"Unresolved planned base: {module}.{name}"
                raise ValueError(message)
            return self._resolve(
                m.Infra.SourceClassReference(
                    target=binding.target,
                    attributes=(*binding.attributes, *remaining),
                    qualified_base=binding.qualified_base,
                ),
                visiting | {key},
                depth + 1,
            ), []

        def _bases(self, identity: str) -> t.StrTuple:
            """Return one identity's declared or native base identities.

            Returns:
                The base declaration identities in declaration order.

            """
            if identity == self._object_id:
                return ()
            if identity not in self._definitions and identity not in self._external:
                # Synthetic terminal identities (runtime-constructed bases such
                # as TypedDict) carry no ancestry of their own; they linearize
                # as direct object children.
                return (self._object_id,)
            if identity in self._definitions:
                declared = self._definitions[identity].bases
                return (
                    tuple(self._resolve(base) for base in declared)
                    if declared
                    else (self._object_id,)
                )
            return self._external_bases(identity)

        def _external_bases(self, identity: str) -> t.StrTuple:
            """Return the native base identities of one external builtin class.

            Returns:
                The external base declaration identities.

            Raises:
                TypeError: If the external value is not a Rope builtin class.

            """
            value = self._external[identity]
            if not isinstance(value, p.Infra.RopeBuiltinClass):
                message = (
                    "External class has no declared source or native identity: "
                    f"{identity}"
                )
                raise TypeError(message)
            builtin_class = FlextInfraUtilitiesRopeRuntime.runtime_callable(
                "rope.base.builtins",
                "BuiltinClass",
            )
            return tuple(
                self._external_identity(
                    self._builtin_base_identity(builtin_class(base, {})),
                )
                for base in value.builtin.__bases__
            )

        @staticmethod
        def _builtin_base_identity(
            value: p.AttributeProbe,
        ) -> t.Infra.RopePyObject:
            """Narrow one constructed Rope builtin base to its object shape.

            Returns:
                The narrowed Rope object value.

            Raises:
                TypeError: If the constructed base is not a Rope class object.

            """
            if not FlextInfraUtilitiesRopeRuntime.abstract_class(value):
                message = "Rope builtin base did not resolve to a class object"
                raise TypeError(message)
            return value

        def _linearize(self, identity: str) -> t.StrTuple:
            """Return the C3 linearization of one identity's ancestry.

            Returns:
                The ordered linearization of the identity.

            Raises:
                ValueError: If the inheritance graph cycles, duplicates a base,
                    or is inconsistent.

            """
            if identity in self._linearizations:
                return self._linearizations[identity]
            if identity in self._active:
                message = f"Cyclic class inheritance: {identity}"
                raise ValueError(message)
            self._active.add(identity)
            parents = self._bases(identity)
            if len(set(parents)) != len(parents):
                message = f"Duplicate class base: {identity}"
                raise ValueError(message)
            linearization = self._c3_merge(identity, parents)
            self._active.remove(identity)
            self._linearizations[identity] = linearization
            return self._linearizations[identity]

        def _c3_merge(self, identity: str, parents: t.StrTuple) -> t.StrTuple:
            """Merge the parent linearizations into one C3 ordering.

            Returns:
                The merged linearization headed by the identity.

            """
            return (
                identity,
                *FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                    (
                        *(self._linearize(parent) for parent in parents),
                        parents,
                    ),
                    message=f"Inconsistent class MRO: {identity}",
                ),
            )

        def _member(
            self,
            identity: str,
            name: str,
            depth: int = 0,
            visiting: frozenset[str] = frozenset(),
        ) -> str:
            """Resolve one inherited class member through the ancestry.

            Returns:
                The member's resolved declaration identity.

            Raises:
                ValueError: If no ancestor declares the member as a class.

            """
            if name == "__base__" and identity in self._external:
                value = self._external[identity]
                if isinstance(value, p.Infra.RopeBuiltinClass):
                    return self._external_identity(
                        FlextInfraUtilitiesRopeRuntime.native_class_primary_base(
                            value.builtin,
                        ),
                    )
            for ancestor in self._linearize(identity):
                if ancestor in self._definitions:
                    members = self._definitions[ancestor].members
                    if name not in members:
                        continue
                    reference = members[name]
                    if reference is None:
                        message = (
                            f"Non-class member shadows required base: {ancestor}.{name}"
                        )
                        raise ValueError(message)
                    return self._resolve(reference, visiting, depth + 1)
                value = self._external[ancestor]
                external_members = value.get_attributes()
                if name in external_members:
                    binding = external_members[name]
                    resolved = self._external_identity(binding.get_object())
                    if resolved in self._external:
                        self._class_bindings[resolved] = binding
                    return resolved
            message = f"Missing inherited class member: {identity}.{name}"
            raise ValueError(message)

        def _root_reference(self, root: str) -> m.Infra.SourceClassReference:
            """Split one configured root into its reference parts.

            Returns:
                The root's source class reference.

            """
            parts = root.split(".")
            index = next(
                (
                    index
                    for index in range(len(parts) - 1, 0, -1)
                    if ".".join(parts[:index]) in self._modules
                    or self._project.find_module(".".join(parts[:index])) is not None
                ),
                1,
            )
            return m.Infra.SourceClassReference(
                target=".".join(parts[:index]),
                attributes=tuple(parts[index:]),
                qualified_base=root,
            )

    @classmethod
    def source_class_order(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> t.StrTuple:
        """Order declared owners by their strict source-backed C3.

        A generated facade's previous base order is an output, never an input
        authority. Resolution failures in the declared owners fail loudly.

        Returns:
            The declaration spellings in consistent precedence order.

        """
        return cls.source_class_orders(project, sources, (declarations,))[0]

    @classmethod
    def source_class_orders(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        groups: t.SequenceOf[t.SequenceOf[m.Infra.SourceClassReference]],
    ) -> t.VariadicTuple[t.StrTuple]:
        """Order several declaration groups through one source resolver.

        Every group shares the resolver's memoized resolutions and
        linearizations, so a pass asking many questions over the same
        captured sources resolves each ancestor once.

        Returns:
            Each group's declaration spellings in consistent precedence order.

        """
        resolver = cls._RuntimeBaseResolver(project, sources, (), None)
        return tuple(resolver.class_order(group) for group in groups)

    @classmethod
    def source_class_reaches(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        anchors: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> t.VariadicTuple[frozenset[str]]:
        """Answer which anchors every declaration inherits, in one resolver.

        Each ancestor is resolved and linearized once from the captured
        sources, so a pass asking about many classes shares one ancestry.

        Returns:
            Per declaration, the anchor spellings its source C3 order holds.

        """
        return cls._RuntimeBaseResolver(project, sources, (), None).class_reaches(
            declarations, anchors
        )

    @classmethod
    def runtime_bases(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        roots: t.StrSequence,
        extra_module_aliases: t.MappingKV[str, str] | None = None,
    ) -> t.StrTuple:
        """Resolve owned classes in C3 order and external classes through Rope.

        Only configured roots mark model evaluation boundaries. No first-party
        module is imported or resolved from disk when its planned source exists.
        Provider reexports follow Rope's declared import provenance. Their source
        declarations, not Rope's possibly incomplete superclass inference, supply
        the ordered bases. Missing references and invalid inheritance fail loudly.

        Returns:
            Sorted configured roots and derived Ruff-qualified base expressions.

        """
        return cls._RuntimeBaseResolver(
            project,
            sources,
            roots,
            extra_module_aliases,
        ).run()


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesRuntime"]
