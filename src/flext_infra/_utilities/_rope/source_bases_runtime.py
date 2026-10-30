"""Qualified runtime-base resolution and linearization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import importlib.util
from collections.abc import Mapping, MutableMapping, Sequence
from functools import cache, partial
from pathlib import Path
from types import MappingProxyType

from flext_infra import c, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities._rope import (
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
        sources: Mapping[str, tuple[Path, str]] | None = None,
    ) -> p.Infra.RopePyName:
        """Resolve the first declared member along its authenticated native C3 order.

        Typed base references resolve the class itself. Planned sources retain
        their original mapping; native resolution failures propagate unchanged.

        Returns:
            The member binding belonging to the exact source or external owner.

        """
        return cls.source_member_resolver(
            project, sources=sources if sources is not None else {}
        )(qualified)

    @classmethod
    def source_member_resolver(
        cls,
        project: p.Infra.RopeProject,
        *,
        sources: Mapping[str, tuple[Path, str]],
    ) -> p.Infra.RopeSourceMemberResolver:
        """Bind reusable native member lookup to an immutable source mapping.

        Returns:
            The existing resolver's member operation for this source view.

        """
        return cls._RuntimeBaseResolver(
            project, MappingProxyType(dict(sources)), (), None
        )

    @classmethod
    def source_member_resolver_factory(
        cls,
        project: p.Infra.RopeProject,
        *,
        sources: Mapping[str, tuple[Path, str]],
    ) -> t.Infra.RopeSourceMemberResolverFactory:
        """Construct the existing resolver lazily once for this captured operation.

        Returns:
            The operation-local factory; construction failures escape unchanged.

        """
        return cache(
            partial(
                cls.source_member_resolver,
                project,
                sources=MappingProxyType(dict(sources)),
            )
        )

    @staticmethod
    def merge_class_lineages[TIdentity: str | tuple[str, str]](
        lineages: Sequence[Sequence[TIdentity]],
        *,
        message: str,
    ) -> tuple[TIdentity, ...]:
        """Merge declared ancestor sequences using their C3 ordering.

        Returns:
            The consistent ordered ancestors.

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
                failure = ValueError(message)
                heads = tuple(
                    dict.fromkeys(sequence[0] for sequence in sequences if sequence)
                )
                failure.add_note(
                    f"blocked_c3_heads={heads}; "
                    f"precedence_conflicts={
                        tuple(
                            (head, sequence[0])
                            for head in heads
                            for sequence in sequences
                            if sequence and head in sequence[1:]
                        )
                    }"
                )
                raise failure
            result.append(candidate)
            for sequence in sequences:
                if sequence and sequence[0] == candidate:
                    sequence.pop(0)
        return tuple(result)

    @classmethod
    def source_member_relocation(
        cls,
        project: p.Infra.RopeProject,
        receiver: tuple[p.Infra.RopePyName, p.Infra.RopePyName],
        canonical: tuple[p.Infra.RopePyName, p.Infra.RopePyName],
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

        def __call__(
            self, qualified: str | m.Infra.SourceClassReference, /
        ) -> p.Infra.RopePyName:
            """Resolve a member with this captured view's native ordering.

            Returns:
                The binding selected by the canonical member resolver.

            """
            return self.source_member_binding(qualified)

        def member_relocation_origin(
            self,
            receiver: tuple[p.Infra.RopePyName, p.Infra.RopePyName],
            canonical: tuple[p.Infra.RopePyName, p.Infra.RopePyName],
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
            self._prepare_ordering()
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
            sources: Mapping[str, tuple[Path, str]],
            roots: Sequence[str],
            extra_module_aliases: Mapping[str, str] | None,
        ) -> None:
            """Bind the resolution inputs and initialize the derived state.

            The supplied capture remains fixed and is retained by reference.
            Its exact paths index every module owner in capture order, preserving
            ambiguity without rescanning the complete capture for each lookup.

            Parameters:
                project: The open Rope project scoped to the analysis roots.
                sources: The qualified module name to captured path and source.
                roots: The configured root qualified names.
                extra_module_aliases: Facade alias maps read outside the sources.

            """
            self._project = project
            self._sources = sources
            names_by_path: dict[Path, list[str]] = {}
            for name, (path, _) in sources.items():
                names_by_path.setdefault(path, []).append(name)
            self._source_names_by_path: Mapping[Path, t.StrTuple] = {
                path: tuple(names) for path, names in names_by_path.items()
            }
            self._roots = roots
            self._extra_module_aliases = extra_module_aliases
            self._definitions: MutableMapping[str, m.Infra.SourceClassDefinition] = {}
            self._modules: MutableMapping[
                str,
                Mapping[str, m.Infra.SourceClassReference | None],
            ] = {}
            self._lazy_declarations: MutableMapping[
                str,
                Mapping[str, m.Infra.SourceClassReference | None],
            ] = {}
            self._providers: MutableMapping[str, t.Infra.RopePyModule] = {}
            self._namespaces: set[str] = set()
            self._module_aliases: MutableMapping[str, m.Infra.SourceClassReference] = {}
            self._external: MutableMapping[str, t.Infra.RopePyObject] = {}
            self._class_bindings: MutableMapping[str, p.Infra.RopePyName] = {}
            self._linearizations: MutableMapping[str, t.StrTuple] = {}
            self._active: set[str] = set()
            self._resolved_memo: MutableMapping[str, str] = {}
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
            declarations: Sequence[m.Infra.SourceClassReference],
        ) -> t.StrTuple:
            """Order declared owners from their authoritative source ancestry.

            Duplicate identities raise ValueError with declaration evidence;
            inconsistent C3 precedence propagates the lineage owner's ValueError.

            Returns:
                Declaration spellings in consistent source precedence order.

            Raises:
                ValueError: Owners have duplicate identities or inconsistent precedence.

            """
            self._prepare_ordering()
            identities = tuple(self._resolve(item) for item in declarations)
            if len(set(identities)) != len(identities):
                message = "Duplicate declared facade owner"
                failure = ValueError(message)
                failure.add_note(
                    f"declared_identities={
                        tuple(
                            (item.qualified_base, identity)
                            for item, identity in zip(
                                declarations, identities, strict=True
                            )
                        )
                    }"
                )
                raise failure
            lineages = tuple(self._linearize(identity) for identity in identities)
            try:
                lineage = (
                    FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                        lineages,
                        message=(
                            "Inconsistent declared facade owner precedence: "
                            "declarations="
                            f"{tuple(item.qualified_base for item in declarations)}"
                        ),
                    )
                )
            except ValueError as failure:
                orders: dict[tuple[str, str], set[str]] = {}
                for declaration, ancestors in zip(declarations, lineages, strict=True):
                    for index, left in enumerate(ancestors):
                        for right in ancestors[index + 1 :]:
                            orders.setdefault((left, right), set()).add(
                                declaration.qualified_base
                            )
                conflicts = tuple(
                    (
                        left,
                        right,
                        tuple(sorted(owners)),
                        tuple(sorted(orders[right, left])),
                    )
                    for (left, right), owners in sorted(orders.items())
                    if left < right and (right, left) in orders
                )
                failure.add_note(f"conflicting_declared_owner_orders={conflicts}")
                raise
            spellings = {
                identity: item.qualified_base
                for identity, item in zip(identities, declarations, strict=True)
            }
            return tuple(
                spellings[identity] for identity in lineage if identity in spellings
            )

        def class_reaches(
            self,
            declarations: Sequence[m.Infra.SourceClassReference],
            anchors: Sequence[m.Infra.SourceClassReference],
        ) -> tuple[frozenset[str], ...]:
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

        def class_defers_annotations(
            self, qualified: m.Infra.SourceClassReference
        ) -> bool:
            """Prove ordinary class construction through authenticated ancestry.

            Args:
                qualified: The source class reference to inspect.

            Returns:
                Whether the class defers annotations through its ancestry.

            Raises:
                TypeError: If a source provider has no module AST.

            """
            self._prepare_ordering()
            typing_module = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                self._project.get_module("typing")
            )
            protocol = self._resolve(
                m.Infra.SourceClassReference(target="typing", attributes=("Protocol",))
            )
            runtime_checkable = typing_module.get_attributes()[
                "runtime_checkable"
            ].get_object()
            for identity in self._linearize(self._resolve(qualified)):
                if identity in {self._object_id, protocol}:
                    continue
                if identity not in self._definitions:
                    return False
                module_name, _name, line = identity.rsplit(":", 2)
                tree = self._providers[module_name].get_ast()
                if not isinstance(tree, ast.Module):
                    message = f"Source provider has no module AST: {module_name}"
                    raise TypeError(message)
                declaration = next(
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef) and node.lineno == int(line)
                )
                scope = (
                    self
                    ._providers[module_name]
                    .get_scope()
                    .get_inner_scope_for_line(int(line))
                )
                if scope.parent is None:
                    return False
                if any(
                    (
                        binding := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                            scope.parent, decorator
                        )
                    )
                    is None
                    or binding.get_object() is not runtime_checkable
                    for decorator in declaration.decorator_list
                ):
                    return False
                if declaration.keywords:
                    return False
                if "__init_subclass__" in self._definitions[identity].members:
                    return False
            return True

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
            captured: tuple[Path, str],
            *,
            required_line: int | None = None,
            allow_conditional: bool = False,
            provider: t.Infra.RopePyModule | None = None,
        ) -> Mapping[str, m.Infra.SourceClassReference | None]:
            """Index lexical bindings without installing a cross-module overlay.

            A provider class is indexed at its native declaration line.
            Unreferenced module-level provider classes remain qualified
            declarations, not fabricated lineages. A captured class owns its
            nested declaration identities.
            Unchanged snapshot text uses that project's canonical provider so
            native class identity remains shared with consumer owner selection.
            Only derived text receives a distinct provider in its own source view.

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
            request = m.Infra.SourceBindingInventoryRequest(
                project=self._project,
                module=module,
                path=path,
                source=source,
                required_line=required_line,
                allow_conditional=allow_conditional,
            )
            provider = FlextInfraUtilitiesRopeSourceBasesInventory.source_provider(
                request, provider=provider
            )
            previous = self._providers.get(module)
            if previous is not None and (
                previous.get_resource() != provider.get_resource()
                or previous.source_code != provider.source_code
            ):
                message = f"Ambiguous source provider: {module}"
                raise ValueError(message)
            bindings = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
                request,
                self._definitions,
                # The elected provider above may be a string-built module the
                # restricted view cannot re-address; the inner election
                # re-derives its provider from the same authenticated request.
                provider=None,
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
            name = self._provider_name(module)
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

        @staticmethod
        def _provider_attribute_binding(
            module: t.Infra.RopeSemanticModule,
            name: str,
            target: str,
        ) -> p.Infra.RopePyName:
            """Read a native binding and annotate its original lookup failure.

            Returns:
                The unchanged binding declared by the native provider.

            """
            try:
                return module.get_attribute(name)
            except FlextInfraUtilitiesRopeRuntime.rope_unresolved_error_types() as exc:
                resource = module.get_resource()
                exc.add_note(
                    f"Provider base reference: {target}; source="
                    f"{resource.real_path if resource is not None else '<native>'}"
                )
                raise

        def _unresolved_declared_reference(
            self,
            provider: p.Infra.RopeSourceModule,
            attributes: t.StrTuple,
            target: str,
            *,
            route: tuple[bool, frozenset[str], int],
        ) -> str | None:
            """Route a provider binding the captured inventory does not declare.

            A package attribute may name a native submodule or a declaration
            in its authenticated initializer. The same project's candidate owns
            both routes; physical preimages never override it.

            Args:
                provider: The owned source module that publishes the name; its
                    module identity and resource drive every sub-resolution.
                attributes: Remaining dotted attribute path of the reference.
                target: Fully spelled provider reference being resolved.
                route: Owned flag, visiting set and depth budget tuple.

            Returns:
                The declared class identity, or None for a native external import.

            """
            owned, visiting, depth = route
            module_name = self._provider_name(provider)
            resource = provider.get_resource()
            bindings = self._provider_source_bindings(module_name, provider, resource)
            if (
                attributes[0] not in bindings
                and resource.is_folder()
                and self._project.find_module(target) is not None
            ):
                return self._external_reference(
                    target, attributes[1:], visiting | {target}, depth + 1
                )
            if (
                attributes[0]
                in self._provider_source_bindings(
                    module_name, self._providers[module_name].get_module(), resource
                )
                or owned
                or module_name in self._sources
            ):
                declared = self._candidate_declared_reference(
                    module_name, resource, attributes[0]
                )
                if declared is not None:
                    return self._external_reference(
                        declared.target,
                        (*declared.attributes, *attributes[1:]),
                        visiting | {declared.target},
                        depth + 1,
                    )
                if attributes[0] not in provider.get_attributes():
                    # The captured inventory elects the binding but the live
                    # provider view does not declare it: the walk falls back
                    # to the reexport and family-package routes upstream.
                    return None
                binding = self._provider_attribute_binding(
                    provider, attributes[0], target
                )
                return self._native_provider_reference(
                    provider, binding, attributes, visiting, depth
                )
            return None

        def _declared_source_reference(
            self,
            module: t.Infra.RopeSemanticModule,
            attributes: t.StrTuple,
            visiting: frozenset[str],
            depth: int,
        ) -> str | None:
            """Resolve completed source declarations before imported aliases.

            Rope records project resources with relative paths and external
            resources with absolute paths. Both may declare a final class alias;
            only missing external declarations defer to native import binding.

            Returns:
                The declared class identity, or None for a native external import.

            Raises:
                TypeError: If an owned resource has no native source module.
                ValueError: If owned or planned source lacks the declaration.
                ImportError: If the native import binding fails to resolve.

            """
            resource = module.get_resource()
            if resource is None:
                return None
            owned = not Path(resource.path).is_absolute()
            module_name = self._provider_name(module)
            target = f"{module_name}.{attributes[0]}"
            provider = module.get_module()
            if not FlextInfraUtilitiesRopeRuntime.source_module(provider):
                if owned:
                    message = f"Project-owned provider is not source: {target}"
                    raise TypeError(message)
                return None
            bindings = self._provider_source_bindings(module_name, provider, resource)
            # A lexical collector may shadow an initializer export with None;
            # the installer literal remains the declaration SSOT for that name.
            reference = bindings.get(attributes[0]) or self._lazy_declared_reference(
                module_name, resource, attributes[0]
            )
            if reference is None:
                return self._unresolved_declared_reference(
                    provider,
                    attributes,
                    target,
                    route=(owned, visiting, depth),
                )
            binding = self._providers[module_name].get_attributes().get(attributes[0])
            if isinstance(binding, p.Infra.RopeImportedName):
                return self._native_provider_reference(
                    self._providers[module_name],
                    binding,
                    attributes,
                    visiting,
                    depth,
                )
            try:
                return self._resolve(
                    m.Infra.SourceClassReference(
                        target=reference.target,
                        attributes=(*reference.attributes, *attributes[1:]),
                        qualified_base=reference.qualified_base,
                    ),
                    visiting | {target},
                    depth + 1,
                )
            except (ValueError, ImportError) as failure:
                binding = (
                    self._providers[module_name].get_attributes().get(attributes[0])
                )
                failure.add_note(
                    f"Declared provider binding: provider={module_name!r}; "
                    f"reference={reference!r}; native_type={type(binding).__qualname__}"
                )
                if isinstance(binding, p.Infra.RopeImportedName):
                    failure.add_note(
                        "Native imported name: "
                        f"module={binding.imported_module.module_name!r}; "
                        f"level={binding.imported_module.level}; "
                        f"name={binding.imported_name!r}"
                    )
                raise

        def _provider_source_bindings(
            self,
            module_name: str,
            provider: p.Infra.RopeSourceModule,
            resource: p.Infra.RopeResource,
        ) -> Mapping[str, m.Infra.SourceClassReference | None]:
            """Inventory a provider in its captured epoch using the native origin.

            Returns:
                The existing or newly authenticated declaration bindings.

            """
            source_path = Path(resource.real_path)
            if resource.is_folder():
                source_path /= c.Infra.INIT_PY
            captured = self._sources.get(
                module_name, (source_path, provider.source_code)
            )
            bindings = self._modules.get(module_name)
            if bindings is None:
                bindings = self._inventory(
                    module_name,
                    captured,
                    allow_conditional=Path(resource.path).is_absolute()
                    and module_name not in self._sources,
                    provider=(
                        provider
                        if captured == (source_path, provider.source_code)
                        else None
                    ),
                )
                self._modules[module_name] = bindings
            return bindings

        def _lazy_declared_reference(
            self,
            module_name: str,
            resource: p.Infra.RopeResource,
            name: str,
        ) -> m.Infra.SourceClassReference | None:
            """Read the core installer's declared route when inventory shadows it.

            The literal ``install_lazy_exports`` mapping is the declaration
            SSOT for initializers; a lexical collector that shadows an exported
            name with ``None`` must not erase the publisher route.

            Returns:
                The declared reference, or None when nothing is declared.

            """
            if module_name in self._lazy_declarations:
                return self._lazy_declarations[module_name].get(name)
            captured = self._sources.get(module_name)
            if captured is not None:
                source_path = captured[0]
            else:
                source_path = Path(resource.real_path)
                if resource.is_folder():
                    source_path /= c.Infra.INIT_PY
            request = m.Infra.SourceBindingInventoryRequest(
                project=self._project,
                module=module_name,
                path=source_path,
                source=self._project.source_text(source_path),
                required_line=None,
                allow_conditional=False,
            )
            inventory = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
                request, self._definitions, provider=None
            )
            self._lazy_declarations[module_name] = inventory
            return inventory.get(name)

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
            name = attributes[0]
            target = f"{self._provider_name(module)}.{name}"
            if target in visiting:
                chain = " <- ".join(sorted(visiting))
                message = f"Cyclic provider reexport: {target} (visiting: {chain})"
                failure = ValueError(message)
                resource = module.get_resource()
                failure.add_note(
                    f"Provider origin: name={module.get_name()!r}; "
                    "resource="
                    f"{resource.real_path if resource is not None else None!r}; "
                    f"captured={self._captured_provider_modules(module)!r}; "
                    f"attributes={attributes!r}"
                )
                if resource is not None:
                    failure.add_note(
                        f"Provider captured descendants={
                            tuple(
                                (name, str(path))
                                for name, (path, _) in self._sources.items()
                                if path.is_relative_to(Path(resource.real_path))
                            )
                        }"
                    )
                raise failure
            if (
                not self._captured_provider_modules(module)
                and name in module.get_attributes()
            ):
                binding = self._provider_attribute_binding(module, name, target)
                if self._function_object_identity(binding.get_object()) is not None:
                    return self._provider_value_reference(
                        binding, attributes[1:], visiting, depth
                    )
            declared = self._declared_source_reference(
                module, attributes, visiting, depth
            )
            if declared is not None:
                return declared
            if name not in module.get_attributes():
                reexported = self._missing_provider_reference(
                    module, attributes, visiting, depth
                )
                if reexported is not None:
                    return reexported
                outer = module.get_resource()
                if (
                    outer is not None
                    and outer.is_folder()
                    and self._project.find_module(target) is not None
                ):
                    # A family package publishes submodules, not attributes:
                    # the cached package view can trail a fresh sibling file,
                    # so the native module election is the truth — continue
                    # the walk inside the elected child module. A plain
                    # module (file resource) keeps the declared failure.
                    return self._external_reference(
                        target, attributes[1:], visiting | {target}, depth + 1
                    )
                message = (
                    f"Provider {module.get_name()} does not declare {name}: {target}"
                )
                raise ValueError(message)
            binding = self._provider_attribute_binding(module, name, target)
            return self._native_provider_reference(
                module, binding, attributes, visiting, depth
            )

        def _native_provider_reference(
            self,
            module: t.Infra.RopeSemanticModule,
            binding: p.Infra.RopePyName,
            attributes: t.StrTuple,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve one external binding through its native Rope import owner.

            Returns:
                The native class identity reached by the provider binding.

            Raises:
                ImportError: If the imported provider cannot be resolved.
                ValueError: If the binding does not identify a class.

            """
            name, *remaining = attributes
            target = f"{self._provider_name(module)}.{name}"
            if isinstance(binding, p.Infra.RopeImportedName):
                override = None
                try:
                    override = self._source_import_override(module, binding, attributes)
                    if override is not None:
                        return self._resolve(override, visiting | {target}, depth + 1)
                except (ValueError, ImportError) as exc:
                    resource = module.get_resource()
                    exc.add_note(
                        f"Provider source publication: module={module.get_name()!r}; "
                        f"attributes={attributes!r}; resource="
                        f"{resource.real_path if resource is not None else None!r}; "
                        f"selected_source_binding={override!r}; "
                        f"native_imported_name={binding.imported_name!r}"
                    )
                    raise
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
            try:
                return self._provider_value_reference(
                    binding, tuple(remaining), visiting, depth
                )
            except (ValueError, ImportError) as exc:
                resource = module.get_resource()
                captured = tuple(
                    (name, str(self._sources[name][0]))
                    for name in self._captured_provider_modules(module)
                )
                exc.add_note(
                    f"Provider member reference: module={module.get_name()!r}; "
                    f"attributes={attributes!r}; resource="
                    f"{resource.real_path if resource is not None else None!r}; "
                    f"captured_sources={captured!r}"
                )
                raise

        def _missing_provider_reference(
            self,
            module: t.Infra.RopeSemanticModule,
            attributes: t.StrTuple,
            visiting: frozenset[str],
            depth: int,
        ) -> str | None:
            """Resolve a lazy or star reexport before native attribute lookup.

            Returns:
                The declared class identity, or None for a native attribute.

            """
            name, *remaining = attributes
            target = f"{self._provider_name(module)}.{name}"
            provider = self._provider_lazy_bindings(module).get(name)
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
                    reexporter, attributes, visiting | {target}, depth + 1
                )
            return None

        def _provider_name(
            self,
            module: t.Infra.RopeSemanticModule,
        ) -> str:
            """Return a provider's authenticated complete import identity.

            Captured sources own their names. Other project resources use the
            declared namespace discovery; external providers keep Rope's name.

            Returns:
                The provider identity used by declarations and relative aliases.

            Raises:
                ValueError: Captured names are ambiguous or an owned source has
                    no declared module identity.

            """
            owners = self._captured_provider_modules(module)
            resource = module.get_resource()
            if len(owners) > 1:
                origin = (
                    resource.real_path if resource is not None else module.get_name()
                )
                message = f"Ambiguous captured source owner: {origin}"
                raise ValueError(message)
            if owners:
                return owners[0]
            return FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                module,
                source_project=self._project,
            )

        def _captured_provider_modules(
            self,
            module: t.Infra.RopeSemanticModule,
        ) -> t.StrTuple:
            """Read captured module owners from the fixed exact-path index.

            Ordered competing names remain present for the caller's ambiguity
            check. Native package folders retain their initializer identity.

            Returns:
                Captured owners of the source, including a package initializer.

            """
            resource = module.get_resource()
            if resource is None:
                return ()
            path = Path(resource.real_path)
            if resource.is_folder():
                path /= c.Infra.INIT_PY
            return self._source_names_by_path.get(path, ())

        def _source_import_override(
            self,
            module: t.Infra.RopeSemanticModule,
            binding: p.Infra.RopeImportedName,
            attributes: t.StrTuple,
        ) -> m.Infra.SourceClassReference | None:
            """Resolve completed source bindings before forwarding native imports.

            Captured providers retain their planned bytes; uncaptured providers
            retain their elected native source. Both completed inventories own
            assignments that replace earlier imports. Unchanged imports retain
            their native imported-name provenance. An authenticated final local
            declaration is elected before evaluating a replaced import. A required
            native lookup propagates its original failure.

            Returns:
                The completed source override, or no override of the native import.

            Raises:
                ValueError: If the source binding has no declared provider.

            """
            declaring = module.get_module()
            if not FlextInfraUtilitiesRopeRuntime.source_module(declaring):
                return None
            resource = declaring.get_resource()
            if resource is None:
                message = f"source-backed provider has no resource: {module.get_name()}"
                raise ValueError(message)
            module_name = self._provider_name(declaring)
            name, *remaining = attributes
            bindings = self._provider_source_bindings(module_name, declaring, resource)
            reference = bindings.get(name)
            if reference is None:
                if name not in bindings and module_name not in self._sources:
                    return None
                message = f"Unresolved provider base: {module_name}.{name}"
                raise ValueError(message)
            if (
                reference.target in self._definitions
                or reference.attributes != (binding.imported_name,)
                or reference.target
                != self._provider_name(self._provider_module(binding.imported_module))
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
        ) -> Mapping[str, m.Infra.SourceClassReference]:
            """Read a provider's declared lazy aliases from its native source module.

            An uncaptured candidate view can shadow the physical initializer
            with empty bytes; the physical raw disk is the lazy SSOT fallback
            when the candidate text declares no installer at all.

            Returns:
                Declared provider modules keyed by their lazy aliases.

            """
            declaring = module.get_module()
            if not FlextInfraUtilitiesRopeRuntime.source_module(declaring):
                # An abstract package election has no source module of its
                # own; its initializer on the raw disk is the lazy SSOT.
                outer = module.get_resource()
                if outer is None:
                    return {}
                folder = (
                    Path(outer.real_path)
                    if outer.is_folder()
                    else Path(outer.real_path).parent
                )
                init_path = folder / c.Infra.INIT_PY
                if not init_path.is_file():
                    return {}
                return FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                    self._provider_name(module),
                    init_path,
                    init_path.read_text(encoding=c.DEFAULT_ENCODING, errors="replace"),
                    project=self._project,
                    pymodule=None,
                )
            resource = declaring.get_resource()
            if resource is None:
                return {}
            source = declaring.source_code
            used_disk = False
            if "install_lazy_exports" not in source and resource.exists():
                # A cached candidate view can trail the latest projection:
                # when the candidate declares no installer at all, the raw
                # disk initializer is the lazy SSOT and its text parses
                # standalone (no candidate snapshot to diff). Preferring the
                # disk unconditionally re-widens the walk into foreign
                # runtime lineages and re-triggers candidate-epoch splices.
                physical = Path(resource.real_path)
                if physical.is_file():
                    disk = physical.read_text(
                        encoding=c.DEFAULT_ENCODING, errors="replace"
                    )
                    if "install_lazy_exports" in disk:
                        source = disk
                        used_disk = True
            return FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                self._provider_name(module),
                Path(resource.real_path),
                source,
                project=self._project,
                pymodule=None if used_disk else declaring,
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
                when no star re-export of the provider binds it. A required star
                target that Rope cannot resolve propagates its original failure.

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
            module_name = self._provider_name(module)
            package = (
                module_name
                if file_name == c.Infra.INIT_PY or not file_name.endswith(".py")
                else module_name.rpartition(".")[0]
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
            remaining: Sequence[str],
            target: str,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve one provider imported-name binding to an identity.

            Returns:
                The resolved declaration identity.

            """
            imported = self._provider_module(binding.imported_module)
            imported_name = self._provider_name(imported)
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
            remaining: Sequence[str],
            target: str,
            visiting: frozenset[str],
            depth: int,
        ) -> str:
            """Resolve one provider imported-module binding to an identity.

            Returns:
                The resolved declaration identity.

            """
            imported = self._provider_module(binding)
            imported_name = self._provider_name(imported)
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

        def _candidate_declared_reference(
            self,
            module_name: str,
            resource: p.Infra.RopeResource,
            name: str,
        ) -> m.Infra.SourceClassReference | None:
            """Read one export from the same native candidate and source resource.

            Returns:
                The declared reference, or absence in the authenticated candidate.

            """
            source_path = Path(resource.real_path)
            if resource.is_folder():
                source_path /= c.Infra.INIT_PY
            if not self._project.source_query(source_path, "isfile"):
                return None
            source = self._project.source_text(source_path)
            provider = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                self._project,
                self._project.get_file(
                    source_path.relative_to(
                        Path(self._project.root.real_path)
                    ).as_posix()
                )
                if source_path.is_relative_to(Path(self._project.root.real_path))
                else FlextInfraUtilitiesRopeRuntime.file_resource_at(
                    self._project, source_path
                ),
            )
            declared = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                module_name,
                source_path,
                source,
                project=self._project,
                pymodule=provider,
            )
            return declared.get(name)

        def _external_reference(
            self,
            target: str,
            attributes: t.StrTuple,
            visiting: frozenset[str] = frozenset(),
            depth: int = 0,
        ) -> str:
            """Resolve one external qualified target through Rope.

            The injected project retains its original native-module election.
            Resolution and attribute errors propagate unchanged.

            Returns:
                The resolved declaration identity.

            Raises:
                ValueError: The native provider rejects the requested class binding.
                ImportError: The native import owner cannot resolve the provider.

            """
            module = self._project.get_module(target)
            resource = module.get_resource()
            if resource is not None and not isinstance(
                module,
                self._native_module_type,
            ):
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self._project,
                    resource,
                )
            try:
                return self._provider_reference(
                    FlextInfraUtilitiesRopeRuntime.require_semantic_module(module),
                    attributes,
                    visiting,
                    depth,
                )
            except (ValueError, ImportError) as failure:
                origin = module.get_resource()
                failure.add_note(
                    f"Native module election: requested={target!r}; "
                    f"found={resource.real_path if resource is not None else None!r}; "
                    f"selected={module.get_name()!r}; "
                    "selected_resource="
                    f"{origin.real_path if origin is not None else None!r}"
                )
                raise

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
                ImportError: A required provider cannot be imported by its native owner.
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
            try:
                target, attributes = self._unresolved_target(
                    target,
                    list(attributes),
                    key,
                    visiting,
                    depth,
                )
                for attribute in attributes:
                    target = self._member(target, attribute, 0, visiting)
            except (ValueError, ImportError) as exc:
                exc.add_note(
                    f"Source class reference: target={reference.target!r}; "
                    f"attributes={reference.attributes!r}; "
                    f"qualified_base={reference.qualified_base!r}; "
                    f"selected_target={target!r}; remaining={attributes!r}"
                )
                raise
            self._resolved_memo[key] = target
            return target

        def _alias_rewritten_target(
            self,
            reference: m.Infra.SourceClassReference,
        ) -> tuple[str, t.StrTuple]:
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
        ) -> tuple[str, list[str]]:
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
            parts: Sequence[str],
            attributes: list[str],
            key: str,
            visiting: frozenset[str],
            depth: int,
        ) -> tuple[str, list[str]]:
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
                ImportError: If the native import binding fails to resolve.

            """
            index = next(
                index
                for index in range(len(parts), 0, -1)
                if ".".join(parts[:index]) in self._namespaces
            )
            module = ".".join(parts[:index])
            remaining = [*parts[index:], *attributes]
            module, name, remaining, external = self._descend_planned_namespace(
                module, remaining, parts, visiting, depth
            )
            if external is not None:
                return external, []
            bindings = self._modules.get(module)
            binding = (
                bindings.get(name) if bindings is not None else None
            ) or self._planned_lazy_binding(module, name)
            if binding is None:
                # The last path segment may be a submodule rather than a
                # lazy binding: dissolve-move waves publish classes into
                # sibling modules elected by file stem, so the module's own
                # declaration carries the base.
                submodule = f"{module}.{name}"
                if submodule in self._modules:
                    return self._resolve(
                        m.Infra.SourceClassReference(
                            target=submodule,
                            attributes=tuple(remaining),
                            qualified_base=f"{submodule}.{remaining[0]}"
                            if remaining
                            else submodule,
                        ),
                        visiting | {key},
                        depth + 1,
                    )
                message = (
                    f"Planned namespace has no module binding: {module}.{name}"
                    if bindings is None
                    else f"Unresolved planned base: {module}.{name}"
                )
                raise ValueError(message)
            try:
                return self._resolve(
                    m.Infra.SourceClassReference(
                        target=binding.target,
                        attributes=(*binding.attributes, *remaining),
                        qualified_base=binding.qualified_base,
                    ),
                    visiting | {key},
                    depth + 1,
                ), []
            except (ValueError, ImportError) as failure:
                failure.add_note(
                    f"Planned namespace binding: module={module!r}; name={name!r}; "
                    f"target={binding.target!r}; attributes={binding.attributes!r}; "
                    f"remaining={remaining!r}; visiting={tuple(sorted(visiting))!r}"
                )
                raise

        def _descend_planned_namespace(
            self,
            module: str,
            remaining: list[str],
            parts: Sequence[str],
            visiting: frozenset[str],
            depth: int,
        ) -> tuple[str, str, list[str], str | None]:
            """Walk planned namespace segments down to the binding owner.

            Captured module identities and the injected native module election
            determine the next owner within the bound source view.

            Returns:
                The owner module, its binding name, the remaining attribute
                path and an already-resolved external identity when the
                descent leaves the captured epoch.

            Raises:
                ValueError: If a module is used as a class base.
                ImportError: If the native import binding fails to resolve.

            """
            while True:
                if not remaining:
                    message = f"Module used as a class base: {module}"
                    raise ValueError(message)
                name = remaining.pop(0)
                if module not in self._modules and module in self._sources:
                    self._modules[module] = self._inventory(
                        module, self._sources[module]
                    )
                submodule = f"{module}.{name}"
                if name in self._modules.get(module, {}):
                    return module, name, remaining, None
                if submodule not in self._namespaces:
                    if submodule in self._sources or submodule in getattr(
                        self, "_raw_captures", {}
                    ):
                        module = submodule
                        continue
                    if self._project.find_module(submodule) is not None:
                        try:
                            external = self._external_reference(
                                submodule, tuple(remaining), visiting, depth + 1
                            )
                        except (ValueError, ImportError) as failure:
                            resource = self._project.find_module(".".join(parts))
                            origin = (
                                resource.real_path if resource is not None else None
                            )
                            failure.add_note(
                                f"Uncaptured namespace descent: module={module!r}; "
                                f"selected={submodule!r}; remaining={remaining!r}; "
                                f"full_target={'.'.join(parts)!r}; native_origin="
                                f"{origin!r}"
                            )
                            raise
                        return module, name, remaining, external
                    return module, name, remaining, None
                module = submodule

        def _planned_lazy_binding(
            self,
            module: str,
            name: str,
        ) -> m.Infra.SourceClassReference | None:
            """Resolve one planned base through the initializer's lazy SSOT.

            The literal ``install_lazy_exports`` mapping is read from the
            injected project's authenticated candidate. Captured paths elect
            their declared owners before native import lookup; captured text
            never replaces the candidate's source bytes.

            Returns:
                The declared reference, or None when nothing is declared.

            """
            captured = self._sources.get(module)
            if captured is not None:
                source_path = captured[0]
            else:
                resource = self._project.find_module(module)
                if resource is None:
                    return None
                source_path = Path(resource.real_path)
                if resource.is_folder():
                    source_path /= c.Infra.INIT_PY
                if not self._project.source_query(source_path, "isfile"):
                    return None
            request = m.Infra.SourceBindingInventoryRequest(
                project=self._project,
                module=module,
                path=source_path,
                source=self._project.source_text(source_path),
                required_line=None,
                allow_conditional=False,
            )
            bindings = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
                request, self._definitions, provider=None
            )
            return bindings.get(name)

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
        sources: Mapping[str, tuple[Path, str]],
        declarations: Sequence[m.Infra.SourceClassReference],
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
        sources: Mapping[str, tuple[Path, str]],
        groups: Sequence[Sequence[m.Infra.SourceClassReference]],
    ) -> tuple[t.StrTuple, ...]:
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
        sources: Mapping[str, tuple[Path, str]],
        declarations: Sequence[m.Infra.SourceClassReference],
        anchors: Sequence[m.Infra.SourceClassReference],
    ) -> tuple[frozenset[str], ...]:
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
        sources: Mapping[str, tuple[Path, str]],
        roots: Sequence[str],
        extra_module_aliases: Mapping[str, str] | None = None,
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
