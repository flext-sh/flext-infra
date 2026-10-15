"""Rope project, module and import factory boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeBase,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
)


class FlextInfraUtilitiesRopeRuntimeModules(FlextInfraUtilitiesRopeRuntimeBase):
    """Load Rope project/module/import objects behind protocols."""

    @classmethod
    def native_class(
        cls,
        native: p.Infra.NativeClassMetadata,
    ) -> t.Infra.RopePyObject:
        """Wrap an observed native class without requiring a module export.

        Returns:
            Rope's class object retaining the exact native identity.

        Raises:
            TypeError: If the input is not a class or Rope changes its identity.

        """
        if not isinstance(native, type):
            msg = "Rope native class input is not a class"
            raise TypeError(msg)
        wrapped = cls.runtime_callable("rope.base.builtins", "BuiltinClass")(
            native,
            {},
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(wrapped):
            msg = "Rope native class factory did not return a class"
            raise TypeError(msg)
        if (
            not isinstance(wrapped, p.Infra.RopeBuiltinClass)
            or wrapped.builtin is not native
        ):
            msg = "Rope native class factory did not preserve native identity"
            raise TypeError(msg)
        return wrapped

    @classmethod
    def native_class_primary_base(
        cls,
        native: p.Infra.NativeClassMetadata,
    ) -> t.Infra.RopePyObject:
        """Resolve the native type descriptor, not an inherited class member.

        Returns:
            Rope's wrapper retaining the observed primary base identity.

        Raises:
            TypeError: If the primary base is None rather than a class.

        """
        base = native.__base__
        if base is None:
            msg = "Rope native primary base is not a class"
            raise TypeError(msg)
        return cls.native_class(base)

    @classmethod
    def parse_rope_module(cls, source: str, *, filename: str) -> t.Infra.RopeAstNode:
        """Parse one source snapshot through Rope's canonical syntax boundary.

        Returns:
            The resulting ``t.Infra.RopeAstNode``.

        Raises:
            TypeError: If rope parser returned an invalid module node.

        """
        parsed = cls.runtime_callable("rope.base.ast", "parse")(
            source,
            filename=filename,
        )
        if not isinstance(parsed, p.Infra.RopeAstNode):
            msg = "rope parser returned an invalid module node"
            raise TypeError(msg)
        return parsed

    @classmethod
    def snapshot_project(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        *,
        captured: m.Infra.CodemodBindingSnapshot | None = None,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Infra.RopeProject:
        """Capture a complete identity graph with proposed sources authoritative.

        Unchanged dependencies are captured once before graph construction;
        subsequent imports and MRO resolution only read that closed inventory.
        Governed project-root entry modules (e.g. conftest.py) are real project
        resources outside every source folder; they join the closed inventory
        from disk so consumer rewrites still resolve inside the snapshot.

        Returns:
            The resulting ``p.Infra.RopeProject``.

        Raises:
            TypeError: If Rope project owner does not expose snapshot construction; or
                if Rope snapshot does not satisfy its project contract.
            ValueError: If Rope proposed source is outside its input inventory.

        """
        inventory = (
            {
                Path(resource.real_path).resolve(): resource.read()
                for resource in project.get_python_files()
            }
            if captured is None
            else {
                state.path.resolve(): state.content.decode("utf-8")
                for state in captured.states
                if state.content is not None
            }
        )
        root = Path(project.root.real_path).resolve()
        declared: dict[Path, str] = {}
        for plan in declared_files:
            path = plan.path.resolve()
            if not path.is_relative_to(root) or plan.desired_content is None:
                msg = f"Rope virtual destination is not a declared source: {path}"
                raise ValueError(msg)
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
                directory_state = u.Cli.atomic_plan_directory_chain(
                    plan.before.target,
                ).unwrap()
                if directory_state != plan.before:
                    msg = f"Rope virtual destination parent changed: {path}"
                    raise ValueError(msg)
            else:
                file_state = u.Cli.atomic_read_binary_file_state(
                    path,
                    required=False,
                ).unwrap()
                if file_state != plan.before or file_state.content is not None:
                    msg = f"Rope virtual destination changed or already exists: {path}"
                    raise ValueError(msg)
            proposed = plan.desired_content.decode("utf-8")
            if path in declared and declared[path] != proposed:
                msg = f"Rope virtual destination declarations disagree: {path}"
                raise ValueError(msg)
            declared[path] = proposed
            inventory[path] = proposed
        for path, source in sources.items():
            resolved = path.resolve()
            if resolved not in inventory:
                try:
                    relative = resolved.relative_to(root)
                except ValueError as error:
                    msg = f"Rope proposed source is outside its input inventory: {path}"
                    raise ValueError(msg) from error
                candidate_resource = project.get_resource(relative.as_posix())
                if not FlextInfraUtilitiesRopeRuntimeTypes.file_resource(
                    candidate_resource,
                ):
                    msg = f"Rope proposed source is outside its input inventory: {path}"
                    raise ValueError(msg)
                resource = candidate_resource
                if not Path(resource.real_path).is_file():
                    msg = f"Rope proposed source is outside its input inventory: {path}"
                    raise ValueError(msg)
                inventory[resolved] = resource.read()
            if resolved in declared and declared[resolved] != source:
                msg = f"Rope virtual destination source disagrees with its plan: {path}"
                raise ValueError(msg)
            inventory[resolved] = source
        owner = cls.runtime_type(
            "flext_infra._utilities._rope.project",
            "FlextInfraRopeProject",
        )
        factory = getattr(owner, "from_snapshot", None)
        if not callable(factory):
            msg = "Rope project owner does not expose snapshot construction"
            raise TypeError(msg)
        snapshot = factory(
            project.root.real_path,
            inventory,
            [folder.path for folder in project.get_source_folders()],
            ignored_resources=sorted(config.Infra.codegen.source_scan_ignored),
            python_path_folders=[
                folder.real_path for folder in project.get_python_path_folders()
                if folder.is_folder()
            ],
        )
        if not isinstance(snapshot, p.Infra.RopeProject):
            msg = "Rope snapshot does not satisfy its project contract"
            raise TypeError(msg)
        return snapshot

    @classmethod
    def imported_name_at(
        cls,
        pymodule: t.Infra.RopePyModule,
        offset: int,
    ) -> p.Infra.RopeImportedName | None:
        """Resolve a lexical binding; local shadows are not imported names.

        Returns:
            The resulting ``p.Infra.RopeImportedName | None``.

        """
        resolver = cls.runtime_callable("rope.base.evaluate", "eval_location")
        result = resolver(pymodule, offset)
        return result if isinstance(result, p.Infra.RopeImportedName) else None

    @classmethod
    def name_definition_resource_path(
        cls,
        pymodule: t.Infra.RopePyModule,
        offset: int,
        *,
        expected_binding: p.Infra.RopePyName | None = None,
    ) -> str | None:
        """Resolve the defining module's on-disk path of the name at ``offset``.

        Imported chains (``ImportedName``/``ImportedModule``) resolve through
        to their foreign definition; a builtin, dynamic, or unresolvable name
        resolves to ``None`` so callers can refuse unsafe rewrites.
        When supplied, ``expected_binding`` must match through Rope's existing
        name-identity comparator before the defining path is returned.

        Returns:
            The resulting ``str | None``.

        """
        resolver = cls.runtime_callable("rope.base.evaluate", "eval_location")
        result = resolver(pymodule, offset)
        if not isinstance(result, p.Infra.RopePyName):
            return None
        if expected_binding is not None and not cls.same_name(
            expected_binding,
            result,
        ):
            return None
        holder, _lineno = result.get_definition_location()
        if holder is None:
            return None
        resource = holder.get_resource()
        if resource is None:
            return None
        return resource.real_path

    @staticmethod
    def source_offset(source: str, node: p.Infra.RopeAstNode) -> int:
        """Resolve Rope AST byte coordinates to a Python source offset.

        Returns:
            The resulting ``int``.

        Raises:
            TypeError: If Rope AST node has no source position.
            ValueError: If Rope AST node line is outside its source.

        """
        line = getattr(node, "lineno", None)
        column = getattr(node, "col_offset", None)
        lines = source.splitlines(keepends=True)
        if not isinstance(line, int) or not isinstance(column, int):
            msg = "Rope AST node has no source position"
            raise TypeError(msg)
        if line < 1 or line > len(lines):
            msg = f"Rope AST node line is outside its source: {line}"
            raise ValueError(msg)
        encoded_prefix = lines[line - 1].encode("utf-8")[:column]
        prefix = encoded_prefix.decode("utf-8")
        return sum(map(len, lines[: line - 1])) + len(prefix)

    @staticmethod
    def scope_at(
        pymodule: p.Infra.RopePyModule,
        offset: int,
        *,
        declaration_line: int | None = None,
    ) -> p.Infra.RopeScope:
        """Return Rope's lexical scope for a source position.

        Returns:
            Rope's lexical scope for a source position.

        Raises:
            TypeError: If Rope module scope has no lexical offset lookup; or if Rope
                lexical lookup returned an invalid scope; or if Rope declaration has no
                defining scope.

        """
        scope = pymodule.get_scope()
        lookup = getattr(scope, "get_inner_scope_for_offset", None)
        if not callable(lookup):
            msg = "Rope module scope has no lexical offset lookup"
            raise TypeError(msg)
        result = lookup(offset)
        if not isinstance(result, p.Infra.RopeScope):
            msg = "Rope lexical lookup returned an invalid scope"
            raise TypeError(msg)
        if (
            result.get_start() == declaration_line
            and result.get_kind() != c.Infra.RopeScopeKind.MODULE
        ):
            parent = getattr(result, "parent", None)
            if not isinstance(parent, p.Infra.RopeScope):
                msg = "Rope declaration has no defining scope"
                raise TypeError(msg)
            return parent
        return result

    @classmethod
    def resolve_symbol(
        cls,
        scope: p.Infra.RopeScope,
        expression: p.Infra.RopeAstNode,
    ) -> p.Infra.RopePyName | None:
        """Resolve an identifier chain without evaluating Python expressions.

        Returns:
            The resulting ``p.Infra.RopePyName | None``.

        Raises:
            TypeError: If Rope identifier resolution returned an invalid name.

        """
        primary = expression
        attributes: list[str] = []
        while isinstance(primary, ast.Attribute):
            attributes.append(primary.attr)
            primary = primary.value
        if not isinstance(primary, ast.Name):
            return None
        result = cls.runtime_callable("rope.base.evaluate", "eval_node")(
            scope,
            primary,
        )
        if result is not None and not isinstance(result, p.Infra.RopePyName):
            msg = "Rope identifier resolution returned an invalid name"
            raise TypeError(msg)
        for attribute in reversed(attributes):
            result = cls._class_assignment_alias(result)
            if result is None:
                return None
            result = result.get_object().get_attributes().get(attribute)
        return cls._class_assignment_alias(result)

    @classmethod
    def _class_assignment_alias(
        cls,
        binding: p.Infra.RopePyName | None,
        *,
        visited: frozenset[t.Pair[str, int]] = frozenset(),
    ) -> p.Infra.RopePyName | None:
        """Resolve a class alias through its native pre-assignment name view."""
        if binding is None or not isinstance(binding, p.Infra.RopeAssignedName):
            return binding
        holder, line = binding.get_definition_location()
        if holder is None or line is None:
            return binding
        source = holder.source_code
        tree = holder.get_ast()
        if not isinstance(tree, ast.AST):
            msg = "native alias holder has no Python AST"
            raise TypeError(msg)
        if not binding.assignments:
            return binding
        rhs = binding.assignments[0].ast_node
        rhs_offset = cls.source_offset(source, rhs)
        scope = cls.scope_at(holder, rhs_offset)
        if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
            return binding
        candidates = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and node.value is not None
            and cls.source_offset(source, node.value) == rhs_offset
        ]
        if not candidates:
            # Native loop/context/pattern bindings are outside class alias policy.
            return binding
        if len(candidates) != 1:
            msg = f"native class alias RHS has no unique statement: {holder.get_name()}:{rhs_offset}"
            raise ValueError(msg)
        declaration = candidates[0]
        if declaration is None or not isinstance(
            declaration.value, ast.Name | ast.Attribute
        ):
            return binding
        offset = cls.source_offset(source, declaration)
        scope = cls.scope_at(holder, offset)
        if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
            return binding
        if len(binding.assignments) != 1:
            return None
        key = (holder.get_name(), offset)
        if key in visited:
            msg = f"cyclic class assignment identity: {key}"
            raise ValueError(msg)
        primary = declaration.value
        while isinstance(primary, ast.Attribute):
            primary = primary.value
        selected: dict[str, p.Infra.RopePyName] = {}
        prior = scope.get_defined_names().get(primary.id)
        if prior is not None:
            declarations = cls._scope_binding_nodes(tree, scope, primary.id)
            if len(declarations) != 1:
                return None
            node, unconditional = declarations[0]
            if not unconditional:
                return None
            annotation_only = any(
                isinstance(candidate, ast.AnnAssign)
                and candidate.value is None
                and candidate.target is node
                for candidate in ast.walk(tree)
            )
            if not annotation_only and cls.source_offset(source, node) < offset:
                if isinstance(prior, p.Infra.RopeAssignedName) and len(prior.assignments) != 1:
                    return None
                selected[primary.id] = prior
        lookup_parent = scope
        if prior is not None and primary.id not in selected:
            module_scope = holder.get_scope()
            if module_scope is None:
                msg = "class-local unbound lookup has no native module scope"
                raise TypeError(msg)
            lookup_parent = module_scope
        if prior is None:
            enclosing = scope.parent
            execution_offset = offset
            while enclosing is not None:
                if enclosing.get_kind() == c.Infra.RopeScopeKind.FUNCTION:
                    # FunctionScope owns lexical locals through its visitor;
                    # PyFunction structural attributes contain no local names.
                    if primary.id in enclosing.get_names():
                        declarations = cls._scope_binding_nodes(tree, enclosing, primary.id)
                        if len(declarations) != 1:
                            return None
                        node, unconditional = declarations[0]
                        if not unconditional or cls.source_offset(source, node) >= execution_offset:
                            return None
                        break
                    created = next(
                        (
                            node for node in ast.walk(tree)
                            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                            and node.lineno == enclosing.get_start()
                        ),
                        None,
                    )
                    if created is None:
                        return None
                    # An outer binding must be available when this inner
                    # function is created; later call timing is not inferred.
                    execution_offset = cls.source_offset(source, created)
                enclosing = enclosing.parent
        temporary = cls.runtime_callable("rope.base.pyscopes", "TemporaryScope")(
            scope.pycore, lookup_parent, selected,
        )
        if not isinstance(temporary, p.Infra.RopeScope):
            msg = "native TemporaryScope does not satisfy the Rope scope contract"
            raise TypeError(msg)
        result = cls.runtime_callable("rope.base.evaluate", "eval_node")(
            temporary, primary,
        )
        if result is not None and not isinstance(result, p.Infra.RopePyName):
            msg = "class RHS lookup returned an invalid native name"
            raise TypeError(msg)
        result = cls._class_assignment_alias(result, visited=visited | {key})
        attributes: list[str] = []
        value = declaration.value
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        for attribute in reversed(attributes):
            if result is None:
                return None
            result = result.get_object().get_attributes().get(attribute)
            result = cls._class_assignment_alias(result, visited=visited | {key})
        return result

    @staticmethod
    def _scope_binding_nodes(
        tree: ast.AST,
        scope: p.Infra.RopeScope,
        name: str,
    ) -> list[t.Pair[ast.AST, bool]]:
        """Elect structural lexical writes and their actual execution positions."""
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        frames = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
        selected: list[t.Pair[ast.AST, bool]] = []
        for node in ast.walk(tree):
            if name not in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(node):
                continue
            parent = parents.get(node)
            unconditional = True
            while parent is not None and not isinstance(parent, frames):
                if isinstance(
                    parent,
                    ast.If | ast.Try | ast.For | ast.AsyncFor | ast.While
                    | ast.With | ast.AsyncWith | ast.Match | ast.ExceptHandler,
                ):
                    unconditional = False
                parent = parents.get(parent)
            if parent is not None and not isinstance(parent, ast.Module) and (
                parent.lineno == scope.get_start()
            ):
                selected.append((node, unconditional and not isinstance(node, ast.arg)))
        return selected

    @classmethod
    def same_name(
        cls,
        expected: p.Infra.RopePyName,
        actual: p.Infra.RopePyName | None,
    ) -> bool:
        """Use Rope's imported-name identity contract for semantic comparisons.

        Returns:
            The resulting ``bool``.

        Raises:
            TypeError: If Rope name comparison returned a non-boolean result.

        """
        result = cls.runtime_callable("rope.refactor.occurrences", "same_pyname")(
            expected,
            actual,
        )
        if not isinstance(result, bool):
            msg = "Rope name comparison returned a non-boolean result"
            raise TypeError(msg)
        return result

    @staticmethod
    def imported_module_path(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopeImportedName,
    ) -> Path:
        """Resolve import provenance through Rope without evaluating its target.

        Generated initializers may still await publication. Their content is
        not required to identify which module an authored import names.

        Returns:
            The resulting ``Path``.

        Raises:
            ValueError: If unresolved imported module; or if import has no declared
                module location.

        """
        imported = binding.imported_module
        resource = imported.resource
        if resource is None:
            name = imported.module_name
            module = imported.importing_module.get_module()
            source = module.get_resource() if module is not None else None
            if name is None or source is None:
                message = (
                    f"import has no declared module location: {binding.imported_name}"
                )
                raise ValueError(message)
            resource = (
                project.find_module(name, source.parent)
                if imported.level == 0
                else project.find_relative_module(name, source.parent, imported.level)
            )
        if resource is None:
            message = f"unresolved imported module: {imported.module_name}"
            raise ValueError(message)
        return Path(resource.real_path).resolve()

    @classmethod
    def new_project(
        cls,
        root: str,
        *,
        ropefolder: str,
        save_objectdb: bool,
        filter_lists: t.Triple[t.SequenceOf[str], t.SequenceOf[str], t.SequenceOf[str]],
    ) -> t.Infra.RopeProject:
        """Create one Rope project.

        ``filter_lists`` carries the Rope filter sequences in order:
        ignored resources, source folders, extension modules.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        Raises:
            TypeError: If Rope project does not satisfy its project contract.

        """
        ignored_resources, source_folders, extension_modules = filter_lists
        project_factory = cls.runtime_callable(
            "flext_infra._utilities._rope.project",
            "FlextInfraRopeProject",
        )
        # FLEXT owns writes; disable Rope's leaking Git subprocess.
        fscommands_factory = cls.runtime_callable(
            "rope.base.fscommands",
            "FileSystemCommands",
        )
        project = project_factory(
            root,
            fscommands=fscommands_factory(),
            ropefolder=ropefolder,
            save_objectdb=save_objectdb,
            save_history=False,
            ignored_resources=list(ignored_resources),
            source_folders=list(source_folders),
            extension_modules=list(extension_modules),
        )
        if not isinstance(project, p.Infra.RopeProject):
            msg = "rope Project does not satisfy p.Infra.RopeProject"
            raise TypeError(msg)
        return project

    @classmethod
    def module_imports_for_pymodule(
        cls,
        rope_project: t.Infra.RopeProject,
        pymodule: t.Infra.RopePyModule,
    ) -> t.Infra.RopeModuleImports:
        loader = cls.runtime_callable(
            c.Infra.ROPE_IMPORTUTILS_MODULE,
            "get_module_imports",
        )
        result = loader(rope_project, pymodule)
        if not isinstance(result, p.Infra.RopeModuleImports):
            msg = "rope get_module_imports returned invalid module imports"
            raise TypeError(msg)
        return result

    @classmethod
    def import_binding(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        module_name: str,
        name: str,
    ) -> t.Pair[str, str]:
        """Plan an import and use the expression elected by Rope's import owner.

        Returns:
            The resulting ``t.Pair[str, str]``.

        Raises:
            TypeError: If Rope add_import returned an invalid source and binding pair;
                or if Rope add_import returned non-text source or binding.

        """
        result = cls.runtime_callable(c.Infra.ROPE_IMPORTUTILS_MODULE, "add_import")(
            project,
            module,
            module_name,
            name,
        )
        if not isinstance(result, tuple):
            msg = "Rope add_import returned an invalid source and binding pair"
            raise TypeError(msg)
        match result:
            case (source, binding):
                if not isinstance(source, str) or not isinstance(binding, str):
                    msg = "Rope add_import returned non-text source or binding"
                    raise TypeError(msg)
                return (source, binding)
            case _:
                msg = "Rope add_import returned an invalid source and binding pair"
                raise TypeError(msg)

    @classmethod
    def build_string_module(
        cls,
        rope_project: t.Infra.RopeProject,
        source: str,
        *,
        resource: t.Infra.RopeResource | None = None,
    ) -> t.Infra.RopePyModule:
        loader = cls.runtime_callable("rope.base.libutils", "get_string_module")
        pymodule = loader(rope_project, source, resource=resource, force_errors=True)
        if not isinstance(pymodule, p.Infra.RopePyModule):
            msg = "rope get_string_module returned non-PyModule"
            raise TypeError(msg)
        return pymodule

    @classmethod
    def import_organizer(
        cls,
        rope_project: t.Infra.RopeProject,
    ) -> p.Infra.RopeImportOrganizer:
        organizer_factory = cls.runtime_callable(
            c.Infra.ROPE_IMPORTUTILS_MODULE,
            "ImportOrganizer",
        )
        organizer = organizer_factory(rope_project)
        if not isinstance(organizer, p.Infra.RopeImportOrganizer):
            msg = "rope ImportOrganizer does not satisfy p.Infra.RopeImportOrganizer"
            raise TypeError(msg)
        return organizer

    @classmethod
    def runtime_find_occurrences(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        resources: t.SequenceOf[t.Infra.RopeResource] | None,
        in_hierarchy: bool,
    ) -> t.SequenceOf[t.Infra.RopeLocation]:
        finder = cls.runtime_callable("rope.contrib.findit", "find_occurrences")
        raw_locations = finder(
            rope_project,
            resource,
            offset,
            resources=resources,
            in_hierarchy=in_hierarchy,
        )
        if not isinstance(raw_locations, p.Infra.RopeRuntimeSequence):
            msg = "rope find_occurrences returned non-sequence locations"
            raise TypeError(msg)
        locations: t.MutableSequenceOf[t.Infra.RopeLocation] = []
        for location in raw_locations:
            if not isinstance(location, p.Infra.RopeLocation):
                msg = "rope find_occurrences returned an invalid location"
                raise TypeError(msg)
            locations.append(location)
        return tuple(locations)

    @classmethod
    def from_import(
        cls,
        module_name: str,
        level: int,
        names_and_aliases: t.SequenceOf[t.Pair[str, str | None]],
    ) -> t.Infra.RopeFromImport:
        from_import_factory = cls.runtime_callable(
            "rope.refactor.importutils.importinfo",
            "FromImport",
        )
        from_import = from_import_factory(module_name, level, list(names_and_aliases))
        if not isinstance(from_import, p.Infra.RopeFromImport):
            msg = "rope FromImport does not satisfy p.Infra.RopeFromImport"
            raise TypeError(msg)
        return from_import


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModules"]
