"""Public-facade discovery for semantic private-import rewrites.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
    Set as AbstractSet,
)
from importlib.util import resolve_name
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities._rope.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesPrivateImportFacades:
    """Derive public paths from live facade classes and reexports, never a registry."""

    @staticmethod
    def source_modules(
        sources: Mapping[Path, str],
    ) -> MutableMapping[str, tuple[str, bool]]:
        """Index the supplied repository sources as the only cutover surface.

        Per-repository resolution law: only this repository's own tree is
        indexed. Referenced packages absent from the supplied sources resolve
        nowhere — installed environments are never consulted, where divergent
        member libraries would leak into the cutover plan.

        Returns:
            The resulting ``MutableMapping[str, tuple[str, bool]]``.

        Raises:
            ValueError: If ambiguous source module identity.

        """
        modules: MutableMapping[str, tuple[str, bool]] = {}
        for path, source in sorted(sources.items()):
            indices = [
                index
                for index, part in enumerate(path.parts)
                if part == c.Infra.DEFAULT_SRC_DIR
            ]
            if not indices:
                continue
            parts = path.parts[indices[-1] + 1 :]
            module = ".".join(
                parts[:-1]
                if path.name == c.Infra.INIT_PY
                else (*parts[:-1], path.stem),
            )
            if not module:
                continue
            if module in modules:
                msg = f"ambiguous source module identity: {module}"
                raise ValueError(msg)
            modules[module] = (source, path.name == c.Infra.INIT_PY)
        return modules

    @staticmethod
    def reachable_sources(
        sources: Mapping[str, tuple[str, bool]],
        statements: Sequence[str],
    ) -> Mapping[str, tuple[str, bool]]:
        """Keep the importers that can expose a requested private module.

        An installed distribution can contain unrelated modules with invalid
        imports. Their declarations have no bearing on a cutover whose target
        is reachable through a different public facade.

        Returns:
            The resulting ``Mapping[str, tuple[str, bool]]``.

        """
        reverse: MutableMapping[str, set[str]] = {}
        for module, (source, is_package) in sources.items():
            package = module if is_package else module.rpartition(".")[0]
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(
                FlextInfraUtilitiesRopeAnalysis.parsed_module(source, filename=module)
            ):
                for imported in (
                    FlextInfraUtilitiesPrivateImportFacades._statement_imported_modules(
                        node,
                        package,
                        sources,
                    )
                ):
                    FlextInfraUtilitiesPrivateImportFacades._register_importer(
                        reverse,
                        sources,
                        imported,
                        module,
                    )
        reachable = FlextInfraUtilitiesPrivateImportFacades._transitive_reachable(
            reverse,
            {
                node.module
                for statement in statements
                for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(
                    FlextInfraUtilitiesRopeAnalysis.parsed_module(statement)
                )
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom)
                and not node.level
                and node.module
            },
        )
        return {
            module: source for module, source in sources.items() if module in reachable
        }

    @staticmethod
    def _statement_imported_modules(
        node: t.Infra.RopeAstNode,
        package: str,
        sources: Mapping[str, tuple[str, bool]],
    ) -> tuple[str, ...]:
        """Return the absolute modules one import statement connects to.

        Returns:
            The resulting ``tuple[str, ...]``.

        """
        imported_modules: set[str] = set()
        if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom):
            if node.level > len(package.split(".")):
                # This import has no absolute module identity. It cannot
                # connect the module to any requested private owner.
                return ()
            imported = (
                resolve_name("." * node.level + (node.module or ""), package)
                if node.level
                else node.module or ""
            )
            imported_modules.add(imported)
            imported_modules.update(
                f"{imported}.{alias.name}"
                for alias in node.names
                if f"{imported}.{alias.name}" in sources
            )
        return tuple(imported_modules)

    @staticmethod
    def _register_importer(
        reverse: MutableMapping[str, set[str]],
        sources: Mapping[str, tuple[str, bool]],
        imported: str,
        module: str,
    ) -> None:
        """Record one importer edge and every package ancestor it exposes.

        Importing a package's child can expose a name exported by the parent
        package: keep that importer reachable when the requested private import
        names the package itself.
        """
        reverse.setdefault(imported, set()).add(module)
        parent = imported.rpartition(".")[0]
        while parent:
            if parent in sources and sources[parent][1]:
                reverse.setdefault(parent, set()).add(module)
            parent = parent.rpartition(".")[0]

    @staticmethod
    def _transitive_reachable(
        reverse: Mapping[str, set[str]],
        seeds: Iterable[str],
    ) -> set[str]:
        """Walk the reverse-import graph from one seed set.

        Returns:
            The resulting ``set[str]``.

        """
        reachable = set(seeds)
        pending = list(seeds)
        while pending:
            for importer in reverse.get(pending.pop(), set()):
                if importer not in reachable:
                    reachable.add(importer)
                    pending.append(importer)
        return reachable

    @staticmethod
    def declared_exports(
        sources: Mapping[str, tuple[str, bool]],
        *,
        project: p.Infra.RopeProject,
    ) -> tuple[MutableMapping[str, set[str]], MutableMapping[str, set[str]]]:
        """Index declared public exports and module/class binding identities.

        Returns:
            The resulting ``tuple[MutableMapping[str, set[str]], MutableMapping[str,
                set[str]]]``.

        Raises:
            ValueError: A declared module has no native source resource.

        """
        bindings: MutableMapping[str, set[str]] = {}
        exports: MutableMapping[str, set[str]] = {}
        for module, (source, is_package) in sorted(sources.items()):
            package = module if is_package else module.rpartition(".")[0]
            tree = FlextInfraUtilitiesRopeAnalysis.parsed_module(
                source, filename=module
            )
            native = project.get_module(module)
            resource = native.get_resource()
            if resource is None:
                message = f"declared export module has no source: {module}"
                raise ValueError(message)
            if resource.is_folder():
                resource = project.get_resource(f"{resource.path}/{c.Infra.INIT_PY}")
            source_module = FlextInfraUtilitiesRopeRuntime.require_source_module(
                project.get_pymodule(resource)
            )
            public_names = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                source_module,
            )
            lazy_exports, lazy_name = (
                FlextInfraUtilitiesRopeAnalysis.lazy_public_exports_source(source)
            )
            collector = FlextInfraUtilitiesPrivateImportFacades._ExportBindingCollector(
                bindings,
                package=package,
                module=module,
                lazy=(lazy_exports, lazy_name),
            )
            collector.collect(tree.body)
            if not any(part.startswith("_") for part in module.split(".")):
                exports.setdefault(module.split(".")[0], set()).update(
                    f"{module}.{name}"
                    for name in public_names
                    if not name.startswith("_") and f"{module}.{name}" in bindings
                )
        return bindings, exports

    class _ExportBindingCollector:
        """Index one module's import and declaration bindings for exports."""

        def __init__(
            self,
            bindings: MutableMapping[str, set[str]],
            *,
            package: str,
            module: str,
            lazy: tuple[Sequence[str], str],
            scope: str | None = None,
        ) -> None:
            self.bindings = bindings
            self.package = package
            self.module = module
            self.lazy_exports, self.lazy_name = lazy
            self.scope = scope or module

        def collect(self, statements: Sequence[t.Infra.AstStatement]) -> None:
            """Index every binding one statement suite declares."""
            for node in statements:
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom):
                    self._bind_import(node)
                elif isinstance(node, c.Infra.AST_DEFINITION_TYPES):
                    self._bind_definition(node)
                elif isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES):
                    self._bind_assignment(node)
                elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.If):
                    self._collect_branches(node)

        def _bind_import(self, node: t.Infra.AstImportFrom) -> None:
            """Bind every non-star import alias to its resolved source module."""
            imported_module = (
                resolve_name("." * node.level + (node.module or ""), self.package)
                if node.level
                else node.module or ""
            )
            for imported in node.names:
                if imported.name != "*":
                    self.bindings.setdefault(
                        f"{self.scope}.{imported.asname or imported.name}",
                        set(),
                    ).add(f"{imported_module}.{imported.name}")

        def _bind_definition(
            self,
            node: t.Infra.AstClassDefinition | t.Infra.AstFunctionDefinition,
        ) -> None:
            """Bind one runtime declaration over any earlier imported name.

            A runtime declaration replaces an earlier imported name in the
            same module. Keeping both fabricated an ambiguity for the
            canonical ``from upstream import u; u = Facade`` shape.
            """
            identity = f"{self.scope}.{node.name}"
            self.bindings[identity] = {identity}
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                FlextInfraUtilitiesPrivateImportFacades._ExportBindingCollector(
                    self.bindings,
                    package=self.package,
                    module=self.module,
                    lazy=(self.lazy_exports, self.lazy_name),
                    scope=identity,
                ).collect(node.body)

        def _bind_assignment(self, node: t.Infra.AstAssignment) -> None:
            """Bind one module or class assignment to its last declaration.

            Assignments are runtime rebinding, not an additional
            possible source: the last declaration is the single Python
            authority for the public name.
            """
            if node.value is None:
                return
            targets = (
                node.targets
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Assign)
                else [node.target]
            )
            for target in targets:
                if isinstance(target, FlextInfraUtilitiesRopeAnalysis.Tree.Name):
                    identity = f"{self.scope}.{target.id}"
                    value = node.value
                    parts: list[str] = []
                    while isinstance(
                        value, FlextInfraUtilitiesRopeAnalysis.Tree.Attribute
                    ):
                        parts.insert(0, value.attr)
                        value = value.value
                    destination = identity
                    if isinstance(value, FlextInfraUtilitiesRopeAnalysis.Tree.Name):
                        local = f"{self.scope}.{value.id}"
                        root = (
                            local
                            if local in self.bindings
                            else f"{self.module}.{value.id}"
                        )
                        destination = ".".join((root, *parts))
                    self.bindings[identity] = {destination}

        def _collect_branches(self, node: t.Infra.AstIfStatement) -> None:
            """Enter conditional branches outside type-only lazy facades."""
            type_only = (
                isinstance(node.test, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and node.test.id == "TYPE_CHECKING"
            )
            if not type_only or self.lazy_exports or self.lazy_name:
                self.collect(node.body)
            self.collect(node.orelse)

    @classmethod
    def declared_public_reference(
        cls,
        qualified: str,
        bindings: Mapping[str, set[str]],
        exports: Mapping[str, set[str]],
    ) -> tuple[str, str] | None:
        """Resolve re-export chains by identity, preferring an explicit root ABI.

        Returns:
            The resulting ``tuple[str, str] | None``.

        Raises:
            ValueError: If ambiguous private symbol identity for; or if ambiguous
                declared public exports for; or if cyclic public export identity; or if
                ambiguous public export identity for.

        """
        expected = cls._export_identities(bindings, qualified, frozenset())
        if len(expected) != 1:
            msg = (
                f"ambiguous private symbol identity for {qualified}: {sorted(expected)}"
            )
            raise ValueError(msg)
        reverse = cls._reverse_bindings(bindings)
        reachable = cls._transitive_reachable(reverse, expected)
        candidates = exports.get(qualified.split(".", maxsplit=1)[0], set()) & reachable
        roots = {candidate for candidate in candidates if candidate.count(".") == 1}
        canonical = roots or candidates
        cls._verify_export_identities(bindings, canonical, expected)
        if len(canonical) > 1:
            msg = (
                f"ambiguous declared public exports for {qualified}: "
                f"{sorted(canonical)}"
            )
            raise ValueError(msg)
        if not canonical:
            return None
        module, _, name = canonical.pop().rpartition(".")
        return module, name

    @classmethod
    def _export_identities(
        cls,
        bindings: Mapping[str, set[str]],
        name: str,
        visiting: frozenset[str],
    ) -> set[str]:
        """Resolve one binding name to its transitive declared identities.

        Returns:
            The resulting ``set[str]``.

        Raises:
            ValueError: If cyclic public export identity.

        """
        if name in visiting:
            msg = f"cyclic public export identity: {name}"
            raise ValueError(msg)
        targets = bindings.get(name, {name})
        resolved: set[str] = set()
        for target in targets:
            if target == name:
                resolved.add(name)
            else:
                resolved.update(
                    cls._export_identities(bindings, target, visiting | {name}),
                )
        return resolved

    @staticmethod
    def _reverse_bindings(
        bindings: Mapping[str, set[str]],
    ) -> MutableMapping[str, set[str]]:
        """Invert the binding map from targets back to their binding names.

        Returns:
            The resulting ``MutableMapping[str, set[str]]``.

        """
        reverse: MutableMapping[str, set[str]] = {}
        for binding, targets in bindings.items():
            for target in targets:
                reverse.setdefault(target, set()).add(binding)
        return reverse

    @classmethod
    def _verify_export_identities(
        cls,
        bindings: Mapping[str, set[str]],
        canonical: Iterable[str],
        expected: Iterable[str],
    ) -> None:
        """Require every canonical export to resolve to the same identity.

        Raises:
            ValueError: If ambiguous public export identity for.

        """
        for export in canonical:
            targets = cls._export_identities(bindings, export, frozenset())
            if targets != set(expected):
                msg = (
                    f"ambiguous public export identity for {export}: {sorted(targets)}"
                )
                raise ValueError(msg)

    @staticmethod
    def private_owner(module: str) -> str | None:
        """Return the distribution root owning ``module``.

        The owner is the module's top-level package (the first segment),
        unless that segment is itself private. Nested private segments
        (``pkg.servers._oid.x``) belong to the same distribution root — the
        importer is a same-project sibling and must rewire relatively, never
        hunt a facade cross-owner.

        Returns:
            The distribution root owning ``module``.

        """
        parts = module.split(".")
        root = parts[0] if parts else ""
        if not root or (len(root) > 1 and root.startswith("_") and root[1].isalpha()):
            return None
        return root

    @staticmethod
    def discover(
        sources: Mapping[str, tuple[str, bool]],
    ) -> Mapping[str, tuple[tuple[t.Infra.AstModule, str, str, str], ...]]:
        """Discover facade aliases and roots from live source assignments.

        Returns:
            The resulting ``Mapping[str, tuple[tuple[t.Infra.AstModule, str,
                str, str], ...]]``.

        """
        discovered: MutableMapping[
            str, list[tuple[t.Infra.AstModule, str, str, str]]
        ] = {}
        for module, (source, is_package) in sorted(sources.items()):
            if is_package:
                continue
            package, _, name = module.rpartition(".")
            if not package:
                continue
            tree = FlextInfraUtilitiesRopeAnalysis.parsed_module(
                source, filename=module
            )
            class_names = {
                node.name
                for node in tree.body
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef)
            }
            for alias, root_name in sorted(
                FlextInfraUtilitiesPrivateImportFacades._facade_owners(
                    tree,
                    class_names,
                ),
            ):
                discovered.setdefault(package, []).append((
                    tree,
                    alias,
                    root_name,
                    f"{name}.py",
                ))
        return {
            package: tuple(owners) for package, owners in sorted(discovered.items())
        }

    @staticmethod
    def assigned_target_value(
        node: t.Infra.AstStatement,
    ) -> tuple[t.Infra.AstExpression | None, t.Infra.AstExpression | None]:
        """Return one single-target assignment's target and value, if any.

        Returns:
            The resulting ``(target, value)`` pair.

        """
        if (
            isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Assign)
            and len(node.targets) == 1
        ):
            return node.targets[0], node.value
        if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign):
            return node.target, node.value
        return None, None

    @staticmethod
    def facade_class_name(value: t.Infra.AstExpression | None) -> str | None:
        """Return the facade class one declaration value names, if any.

        The canonical facade singleton form is
        ``alias: Facade = Facade.fetch_global()``.

        Returns:
            The resulting ``str | None``.

        """
        if isinstance(value, FlextInfraUtilitiesRopeAnalysis.Tree.Name):
            return value.id
        if (
            isinstance(value, FlextInfraUtilitiesRopeAnalysis.Tree.Call)
            and isinstance(value.func, FlextInfraUtilitiesRopeAnalysis.Tree.Attribute)
            and isinstance(value.func.value, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
        ):
            return value.func.value.id
        return None

    @classmethod
    def _facade_owners(
        cls,
        tree: t.Infra.AstModule,
        class_names: AbstractSet[str],
    ) -> set[tuple[str, str]]:
        """Collect the single-letter facade aliases one module declares.

        Returns:
            The resulting ``set[tuple[str, str]]``.

        """
        owners: set[tuple[str, str]] = set()
        for node in tree.body:
            target, value = cls.assigned_target_value(node)
            facade_class = cls.facade_class_name(value)
            if (
                isinstance(target, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and len(target.id) == 1
                and target.id.islower()
                and facade_class is not None
                and facade_class in class_names
            ):
                owners.add((target.id, facade_class))
        return owners

    @classmethod
    def public_reference(
        cls,
        *,
        owners: Sequence[tuple[t.Infra.AstModule, str, str, str]],
        package: str,
        qualified: str,
        bindings: Mapping[str, set[str]],
        class_bases: Mapping[str, tuple[str, ...]],
    ) -> str | None:
        """Resolve one imported binding to exactly one public facade path.

        Returns:
            The resulting ``str | None``.

        Raises:
            ValueError: If ambiguous public facade references for; or if cyclic public
                facade inheritance; or if ambiguous public facade base identity;
                or if ambiguous or cyclic public export identity.

        """
        identities = cls._export_identities(bindings, qualified, frozenset())
        if len(identities) != 1:
            msg = (
                f"ambiguous private symbol identity for {qualified}: "
                f"{sorted(identities)}"
            )
            raise ValueError(msg)
        identity = identities.pop()
        references: set[str] = set()
        for tree, facade_alias, root_name, facade_file in owners:
            root_class = next(
                (
                    node
                    for node in tree.body
                    if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef)
                    and node.name == root_name
                ),
                None,
            )
            if root_class is None:
                continue
            cls._collect_facade_references(
                references,
                (bindings, class_bases, identity),
                root_class,
                facade_alias,
                f"{package}.{Path(facade_file).stem}.{root_name}",
            )
        if not references:
            return None
        deepest = max(reference.count(".") for reference in references)
        canonical = {
            reference for reference in references if reference.count(".") == deepest
        }
        if len(canonical) > 1:
            msg = (
                f"ambiguous public facade references for {qualified}: "
                f"{sorted(canonical)}"
            )
            raise ValueError(msg)
        return canonical.pop()

    @classmethod
    def _inherits_facade(
        cls,
        bindings: Mapping[str, set[str]],
        class_bases: Mapping[str, tuple[str, ...]],
        qualified: str,
        identity: str,
        visiting: frozenset[str],
    ) -> bool:
        """Resolve whether one identity inherits the private class.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If cyclic public facade inheritance; or if ambiguous
                public facade base identity.

        """
        if identity == qualified:
            return True
        if identity in visiting:
            msg = f"cyclic public facade inheritance: {identity}"
            raise ValueError(msg)
        prefix = identity
        while prefix:
            targets = bindings.get(prefix)
            if targets is not None:
                if len(targets) != 1:
                    msg = f"ambiguous public facade base identity: {identity}"
                    raise ValueError(msg)
                target = next(iter(targets)) + identity[len(prefix) :]
                if target != identity:
                    return cls._inherits_facade(
                        bindings,
                        class_bases,
                        qualified,
                        target,
                        visiting | {identity},
                    )
                break
            prefix = prefix.rpartition(".")[0]
        return any(
            cls._inherits_facade(
                bindings,
                class_bases,
                qualified,
                base,
                visiting | {identity},
            )
            for base in class_bases.get(identity, ())
        )

    @classmethod
    def _collect_facade_references(
        cls,
        references: set[str],
        resolvers: tuple[
            Mapping[str, set[str]],
            Mapping[str, tuple[str, ...]],
            str,
        ],
        node: t.Infra.AstClassDefinition,
        public_path: str,
        identity: str,
    ) -> None:
        """Add nested classes and class reexports exposing the private class.

        ``resolvers`` carries ``(bindings, class_bases, qualified)``.
        """
        bindings, class_bases, qualified = resolvers
        if cls._inherits_facade(
            bindings,
            class_bases,
            qualified,
            identity,
            frozenset(),
        ) or any(
            cls._inherits_facade(bindings, class_bases, qualified, base, frozenset())
            for base in class_bases.get(identity, ())
        ):
            references.add(public_path)
        for child in node.body:
            if isinstance(child, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                cls._collect_facade_references(
                    references,
                    resolvers,
                    child,
                    f"{public_path}.{child.name}",
                    f"{identity}.{child.name}",
                )
                continue
            if isinstance(child, c.Infra.AST_ASSIGNMENT_TYPES):
                cls._collect_reexport_references(
                    references, resolvers, child, public_path, identity
                )

    @classmethod
    def _collect_reexport_references(
        cls,
        references: set[str],
        resolvers: tuple[
            Mapping[str, set[str]],
            Mapping[str, tuple[str, ...]],
            str,
        ],
        child: t.Infra.AstAssignment,
        public_path: str,
        identity: str,
    ) -> None:
        """Add public class-body reexports whose target inherits the facade.

        ``resolvers`` carries ``(bindings, class_bases, qualified)``.
        """
        bindings, class_bases, qualified = resolvers
        targets = (
            child.targets
            if isinstance(child, FlextInfraUtilitiesRopeAnalysis.Tree.Assign)
            else [child.target]
        )
        for target in targets:
            if (
                isinstance(target, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and not target.id.startswith("_")
                and cls._inherits_facade(
                    bindings,
                    class_bases,
                    qualified,
                    f"{identity}.{target.id}",
                    frozenset(),
                )
            ):
                references.add(f"{public_path}.{target.id}")

    @staticmethod
    def facade_alias_binding(
        *,
        owners: Sequence[tuple[t.Infra.AstModule, str, str, str]],
        alias: str | None,
    ) -> str | None:
        """Return the alias when the owning package publishes it as a facade.

        A private symbol imported under a name the owner already publishes is a
        facade binding, not a class reference: the consumer writes ``m.X``
        against the facade, so the cutover swaps the import statement and every
        usage stays exactly as written.

        Returns:
            The alias when the owning package publishes it as a facade.

        """
        if alias is None:
            return None
        return next(
            (
                facade_alias
                for _tree, facade_alias, _root_name, _facade_file in owners
                if facade_alias == alias
            ),
            None,
        )

    @staticmethod
    def public_root_name(
        *,
        owners: Sequence[tuple[t.Infra.AstModule, str, str, str]],
        facade_alias: str,
    ) -> str | None:
        """Return the public long name assigned to a canonical facade alias.

        Returns:
            The public long name assigned to a canonical facade alias.

        Raises:
            ValueError: If ambiguous public facade root for alias.

        """
        roots = {
            root_name
            for _tree, alias, root_name, _facade_file in owners
            if alias == facade_alias
        }
        if len(roots) > 1:
            msg = f"ambiguous public facade root for alias {facade_alias}"
            raise ValueError(msg)
        return next(iter(roots), None)

    @classmethod
    def require_unshadowed_alias(
        cls,
        tree: t.Infra.AstModule,
        package: str,
        alias: str,
        file_path: Path,
        removals: Mapping[str, AbstractSet[str]],
    ) -> None:
        """Reject any binding that would shadow the inserted public facade.

        Raises:
            ValueError: If public facade alias.

        """
        allowed_imports = {
            id(node)
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree)
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom)
            and any(
                (
                    node.module == package
                    and imported.name == alias
                    and imported.asname is None
                )
                or (
                    node.module is not None
                    and node.module in removals
                    and imported.name in removals[node.module]
                    and (imported.asname or imported.name) == alias
                )
                for imported in node.names
            )
        }
        rewritten_bindings = {
            imported.asname or imported.name
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree)
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom)
            and node.module is not None
            and node.module in removals
            for imported in node.names
            if imported.name in removals[node.module]
        }
        for node in cls._lexical_binding_nodes(tree, rewritten_bindings):
            if (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Global)
                and alias in node.names
            ):
                break
            if isinstance(node, c.Infra.AST_IMPORT_TYPES):
                if id(node) in allowed_imports:
                    continue
                if any(
                    (imported.asname or imported.name.split(".")[0]) == alias
                    for imported in node.names
                ):
                    break
            elif (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Store)
                and node.id == alias
            ) or (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Argument)
                and node.arg == alias
            ):
                break
            elif isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.FunctionDef
                | FlextInfraUtilitiesRopeAnalysis.Tree.AsyncFunctionDef
                | FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef
                | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar
                | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple
                | FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec,
            ):
                if node.name == alias:
                    break
        else:
            return
        msg = f"public facade alias {alias} is shadowed in {file_path}"
        raise ValueError(msg)

    @classmethod
    def _lexical_binding_nodes(
        cls,
        tree: t.Infra.AstModule,
        rewritten_bindings: AbstractSet[str],
    ) -> Iterable[t.Infra.RopeAstNode]:
        """Exclude class attributes, but retain lexical bindings in methods.

        Yields:
            Nodes whose bindings can capture a public module facade.

        """
        pending: list[tuple[t.Infra.RopeAstNode, bool]] = [(tree, False)]
        deferred_annotations = any(
            isinstance(statement, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom)
            and statement.module == "__future__"
            and any(imported.name == "annotations" for imported in statement.names)
            for statement in tree.body
        )
        while pending:
            node, class_scope = pending.pop()
            # Class dictionaries are not enclosing lexical scopes of methods.
            child_scope = class_scope
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                child_scope = not cls._class_body_references(
                    node,
                    rewritten_bindings,
                    deferred_annotations=deferred_annotations,
                )
            elif isinstance(node, c.Infra.AST_CALLABLE_TYPES):
                child_scope = False
            pending.extend(
                (child, child_scope)
                for child in FlextInfraUtilitiesRopeAnalysis.Tree.child_nodes(node)
            )
            if not class_scope or isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Global
                | FlextInfraUtilitiesRopeAnalysis.Tree.TypeParameter,
            ):
                yield node

    @classmethod
    def _class_body_references(
        cls,
        declaration: t.Infra.AstClassDefinition,
        bindings: AbstractSet[str],
        *,
        deferred_annotations: bool,
    ) -> bool:
        """Keep class bindings when cutover references execute in that dictionary.

        Returns:
            Whether a rewritten binding is evaluated in the class body.

        """
        pending: list[t.Infra.RopeAstNode] = list(declaration.body)
        while pending:
            node = pending.pop()
            if (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and node.id in bindings
            ):
                return True
            pending.extend(
                cls._class_evaluation_children(
                    node,
                    deferred_annotations=deferred_annotations,
                )
            )
        return False

    @staticmethod
    def _class_evaluation_children(
        node: t.Infra.RopeAstNode,
        *,
        deferred_annotations: bool,
    ) -> Iterable[t.Infra.RopeAstNode]:
        """Select expressions that retain the enclosing class namespace.

        Yields:
            Definition expressions, excluding bodies and postponed annotations.

        """
        if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
            yield from node.decorator_list
            yield from node.bases
            yield from (keyword.value for keyword in node.keywords)
            yield from node.type_params
        elif isinstance(node, c.Infra.AST_CALLABLE_TYPES):
            yield from node.args.defaults
            yield from (item for item in node.args.kw_defaults if item is not None)
            if isinstance(node, c.Infra.AST_FUNCTION_TYPES):
                yield from node.decorator_list
                # PEP 695/696 bounds and defaults keep their annotation scope.
                yield from node.type_params
                if not deferred_annotations:
                    yield from node.args.posonlyargs
                    yield from node.args.args
                    yield from node.args.kwonlyargs
                    for expression in (node.args.vararg, node.args.kwarg, node.returns):
                        if expression is not None:
                            yield expression
        elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign):
            yield node.target
            if node.value is not None:
                yield node.value
            if node.simple and not deferred_annotations:
                yield node.annotation
        else:
            yield from FlextInfraUtilitiesRopeAnalysis.Tree.child_nodes(node)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportFacades"]
