"""Rope lexical queries and module/import construction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntimeTypes
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
)
from flext_infra._utilities.rope_runtime_module_queries import (
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
)


class FlextInfraUtilitiesRopeRuntimeModules(
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
):
    """Resolve lexical identities and construct Rope module/import objects."""

    @staticmethod
    def definition_location(
        binding: t.Infra.RopePyName,
    ) -> t.Pair[t.Infra.RopeParsedModule | None, int | None]:
        """Read native definition metadata, including annotation-only bindings.

        Returns:
            The original supplier and first assignment's logical declaration line.

        Raises:
            TypeError: The native annotation is not an expression node.

        """
        module, line = binding.get_definition_location()
        if (
            line is not None
            or not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module)
            or not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
            or not binding.assignments
        ):
            return module, line
        assignment = binding.assignments[0]
        annotation = assignment.type_hint
        if assignment.ast_node is not None or annotation is None:
            return module, line
        if not isinstance(annotation, ast.expr):
            message = "native Rope assignment annotation is not an expression"
            raise TypeError(message)
        return module, module.logical_lines.logical_line_in(annotation.lineno)[0]

    @classmethod
    def annotation_alias_definition(
        cls,
        binding: p.Infra.RopePyName,
    ) -> tuple[ast.TypeAlias, p.Infra.RopeScope] | None:
        """Locate one native alias identity without evaluating its deferred value.

        Returns:
            The unique declaration and lexical scope, or None without native proof.

        Raises:
            TypeError: If the native module does not expose a Python syntax tree.

        """
        imported: set[int] = set()
        while isinstance(binding, p.Infra.RopeImportedName):
            if id(binding) in imported:
                return None
            imported.add(id(binding))
            supplier = (
                binding.imported_module
                .get_object()
                .get_attributes()
                .get(binding.imported_name)
            )
            if supplier is None:
                return None
            binding = supplier
        if (
            not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
            or binding.assignments
        ):
            return None
        module, _line = cls.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            return None
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            message = "native alias module has no Python syntax tree"
            raise TypeError(message)
        declarations: list[tuple[ast.TypeAlias, p.Infra.RopeScope]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.TypeAlias):
                continue
            lexical = cls.scope_at(module, cls.source_offset(module.source_code, node))
            # TypeAlias bindings intentionally have no inferred assignment or
            # line in Rope. Only the source token's exact identity proves them.
            if cls.resolve_symbol(lexical, node.name) is binding:
                declarations.append((node, lexical))
        return declarations[0] if len(declarations) == 1 else None

    @classmethod
    def annotation_origin(
        cls,
        project: p.Infra.RopeProject,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        *,
        visiting: frozenset[tuple[str, int]] = frozenset(),
    ) -> p.Infra.RopePyName | None:
        """Resolve outer native types and aliases without evaluating element types.

        Returns:
            The native outer type identity, or None when no safe origin is proven.

        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return cls.annotation_origin(
                project,
                ast.parse(node.value, mode="eval").body,
                scope,
                visiting=visiting,
            )
        primary = node.value if isinstance(node, ast.Subscript) else node
        binding = cls.resolve_symbol(scope, primary)
        if (
            binding is not None
            and isinstance(node, ast.Subscript)
            and cls.same_name(binding, cls.qualified_name(project, "typing.Annotated"))
        ):
            if not isinstance(node.slice, ast.Tuple) or not node.slice.elts:
                return None
            return cls.annotation_origin(
                project, node.slice.elts[0], scope, visiting=visiting
            )
        alias = None if binding is None else cls.annotation_alias_definition(binding)
        if alias is None:
            return binding
        declaration, lexical = alias
        module = lexical.pyobject.get_module()
        if (module.get_name(), declaration.lineno) in visiting:
            return None
        identity = (module.get_name(), declaration.lineno)
        return cls.annotation_origin(
            project, declaration.value, lexical, visiting=visiting | {identity}
        )

    @classmethod
    def expression_name(
        cls, scope: p.Infra.RopeScope, expression: str
    ) -> p.Infra.RopePyName | None:
        """Resolve a source expression through Rope's lexical evaluator.

        Returns:
            The resolved identity, or None when Rope cannot establish one.

        """
        lexical = cls.lexical_scope(scope, expression.partition(".")[0])
        if lexical is None:
            return None
        result = cls.runtime_callable("rope.base.evaluate", "eval_str")(
            lexical, expression
        )
        return result if isinstance(result, p.Infra.RopePyName) else None

    @staticmethod
    def lexical_scope(scope: p.Infra.RopeScope, name: str) -> p.Infra.RopeScope | None:
        """Resolve lexical names without treating inherited members as locals.

        Returns:
            The native declaring scope, including global interpreter builtins.

        Raises:
            TypeError: When a native parent violates the scope contract.

        """
        first = True
        current: p.Infra.RopeScope | None = scope
        while current is not None:
            if first or current.get_kind() != c.Infra.RopeScopeKind.CLASS:
                names = (
                    current.get_defined_names()
                    if current.get_kind() == c.Infra.RopeScopeKind.CLASS
                    else current.get_names()
                )
                if name in names:
                    return current
            parent = getattr(current, "parent", None)
            if parent is not None and not isinstance(parent, p.Infra.RopeScope):
                message = "Rope lexical parent does not satisfy its scope contract"
                raise TypeError(message)
            current = parent
            first = False
        return None

    @staticmethod
    def qualified_name(
        project: p.Infra.RopeProject,
        expression: str,
        *,
        module_name: str | None = None,
    ) -> p.Infra.RopePyName:
        """Resolve the same qualified identity grammar as Rope wildcards.

        Returns:
            The declaration reached through the native module object graph.

        Raises:
            ValueError: When the identity does not name an attribute.
            TypeError: The fetched provider violates its native semantic contract.

        """
        attributes = expression.split(".")
        module = attributes.pop(0) if module_name is None else module_name
        if not attributes:
            message = f"Rope identity requires an attribute: {expression}"
            raise ValueError(message)
        try:
            value = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module(module),
            )
        except TypeError as error:
            error.add_note(f"Rope identity {expression!r} in module {module!r}")
            raise
        identity = value.get_attribute(attributes[0])
        for attribute in attributes[1:]:
            identity = identity.get_object().get_attribute(attribute)
        return identity

    @classmethod
    def name_definition_resource_path(
        cls,
        pymodule: t.Infra.RopeParsedModule,
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
        pymodule: p.Infra.RopeParsedModule,
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
        """Resolve a class alias through its native pre-assignment name view.

        Returns:
            The proven native alias, or None for an ambiguous lexical binding.

        Raises:
            TypeError: If the native alias holder does not expose its Python AST.
            ValueError: If the class assignment identity is cyclic.

        """
        if not isinstance(binding, p.Infra.RopeAssignedName):
            return binding
        holder, line = binding.get_definition_location()
        if holder is not None and line is not None:
            tree = holder.get_ast()
            if not isinstance(tree, ast.AST):
                msg = "native alias holder has no Python AST"
                raise TypeError(msg)
            statement = cls._class_alias_statement(holder, binding, tree)
            if statement is not None:
                holder, declaration, scope, offset, primary = statement
                if len(binding.assignments) != 1:
                    return None
                key = (holder.get_name(), offset)
                if key in visited:
                    msg = f"cyclic class assignment identity: {key}"
                    raise ValueError(msg)
                if not isinstance(primary, ast.Name):
                    return binding
                lookup = cls._class_alias_namespace(
                    holder, tree, scope, primary, offset
                )
                if lookup is None:
                    return None
                lookup_parent, selected = lookup
                temporary = cls.runtime_callable(
                    "rope.base.pyscopes", "TemporaryScope"
                )(scope.pycore, lookup_parent, selected)
                if not isinstance(temporary, p.Infra.RopeScope):
                    msg = (
                        "native TemporaryScope does not satisfy the Rope scope contract"
                    )
                    raise TypeError(msg)
                return cls._class_alias_value(
                    temporary,
                    declaration,
                    primary,
                    binding=binding,
                    visited=visited | {key},
                )
        return binding

    @classmethod
    def _class_alias_statement(
        cls,
        holder: p.Infra.RopeParsedModule,
        binding: p.Infra.RopeAssignedName,
        tree: ast.AST,
    ) -> (
        tuple[
            p.Infra.RopeSourceModule,
            ast.Assign | ast.AnnAssign,
            p.Infra.RopeScope,
            int,
            ast.expr,
        ]
        | None
    ):
        if not binding.assignments or (rhs := binding.assignments[0].ast_node) is None:
            return None
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder):
            message = "native class assignment has no source module"
            raise TypeError(message)
        source = holder.source_code
        rhs_offset = cls.source_offset(source, rhs)
        scope = cls.scope_at(holder, rhs_offset)
        if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
            return None
        candidates = [
            node
            for node in ast.walk(tree)
            if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
            and node.value is not None
            and cls.source_offset(source, node.value) == rhs_offset
        ]
        if not candidates:
            # Native loop/context/pattern bindings are outside class alias policy.
            return None
        if len(candidates) != 1:
            msg = (
                "native class alias RHS has no unique statement: "
                f"{holder.get_name()}:{rhs_offset}"
            )
            raise ValueError(msg)
        declaration = candidates[0]
        if not isinstance(declaration.value, c.Infra.AST_NAME_REFERENCE_TYPES):
            return None
        offset = cls.source_offset(source, declaration)
        scope = cls.scope_at(holder, offset)
        if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
            return None
        primary = declaration.value
        while isinstance(primary, ast.Attribute):
            primary = primary.value
        return holder, declaration, scope, offset, primary

    @classmethod
    def _class_alias_namespace(
        cls,
        holder: p.Infra.RopeSourceModule,
        tree: ast.AST,
        scope: p.Infra.RopeScope,
        primary: ast.Name,
        offset: int,
    ) -> t.Pair[p.Infra.RopeScope, t.DictKV[str, p.Infra.RopePyName]] | None:
        source = holder.source_code
        selected: t.DictKV[str, p.Infra.RopePyName] = {}
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
                if (
                    isinstance(prior, p.Infra.RopeAssignedName)
                    and len(prior.assignments) != 1
                ):
                    return None
                selected[primary.id] = prior
        lookup_parent = scope
        if prior is not None and primary.id not in selected:
            module_scope = holder.get_scope()
            lookup_parent = module_scope
        if prior is None and not cls._enclosing_alias_available(
            holder, tree, scope, primary, offset
        ):
            return None
        return lookup_parent, selected

    @classmethod
    def _enclosing_alias_available(
        cls,
        holder: p.Infra.RopeSourceModule,
        tree: ast.AST,
        scope: p.Infra.RopeScope,
        primary: ast.Name,
        execution_offset: int,
    ) -> bool:
        enclosing = scope.parent
        while enclosing is not None:
            if enclosing.get_kind() == c.Infra.RopeScopeKind.FUNCTION:
                # FunctionScope owns lexical locals through its visitor;
                # PyFunction structural attributes contain no local names.
                if primary.id in enclosing.get_names():
                    declarations = cls._scope_binding_nodes(tree, enclosing, primary.id)
                    if len(declarations) != 1:
                        return False
                    node, unconditional = declarations[0]
                    return unconditional and (
                        cls.source_offset(holder.source_code, node) < execution_offset
                    )
                created = next(
                    (
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, c.Infra.AST_FUNCTION_TYPES)
                        and node.lineno == enclosing.get_start()
                    ),
                    None,
                )
                if created is None:
                    return False
                # An outer binding must be available when this inner
                # function is created; later call timing is not inferred.
                execution_offset = cls.source_offset(holder.source_code, created)
            enclosing = enclosing.parent
        return True

    @classmethod
    def _class_alias_value(
        cls,
        temporary: p.Infra.RopeScope,
        declaration: ast.Assign | ast.AnnAssign,
        primary: ast.Name,
        *,
        binding: p.Infra.RopePyName,
        visited: frozenset[t.Pair[str, int]],
    ) -> p.Infra.RopePyName | None:
        result = cls.runtime_callable("rope.base.evaluate", "eval_node")(
            temporary,
            primary,
        )
        if result is not None and not isinstance(result, p.Infra.RopePyName):
            msg = "class RHS lookup returned an invalid native name"
            raise TypeError(msg)
        result = cls._class_assignment_alias(result, visited=visited)
        attributes: list[str] = []
        value = declaration.value
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        for attribute in reversed(attributes):
            if result is None:
                return None
            result = result.get_object().get_attributes().get(attribute)
            result = cls._class_assignment_alias(result, visited=visited)
        if (
            result is not None
            and not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(
                result.get_object()
            )
        ):
            # Values retain their declaration, including shared enum members.
            return binding
        return result

    @staticmethod
    def _scope_binding_nodes(
        tree: ast.AST,
        scope: p.Infra.RopeScope,
        name: str,
    ) -> list[t.Pair[ast.AST, bool]]:
        """Elect structural lexical writes and their actual execution positions.

        Returns:
            Matching lexical writes with their unconditional execution status.

        """
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        frames = (
            ast.Module,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Lambda,
        )
        selected: list[t.Pair[ast.AST, bool]] = []
        for node in ast.walk(tree):
            if name not in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                node
            ):
                continue
            parent = parents.get(node)
            unconditional = True
            while parent is not None and not isinstance(parent, frames):
                if isinstance(
                    parent,
                    ast.If
                    | ast.Try
                    | ast.For
                    | ast.AsyncFor
                    | ast.While
                    | ast.With
                    | ast.AsyncWith
                    | ast.Match
                    | ast.ExceptHandler,
                ):
                    unconditional = False
                parent = parents.get(parent)
            if (
                parent is not None
                and not isinstance(parent, ast.Module)
                and (parent.lineno == scope.get_start())
            ):
                selected.append((node, unconditional and not isinstance(node, ast.arg)))
        return selected

    @classmethod
    def same_name(
        cls,
        expected: p.Infra.RopePyName,
        actual: p.Infra.RopePyName | None,
    ) -> bool:
        """Compare native builtin identity or Rope's imported-name identity.

        Returns:
            The resulting ``bool``.

        Raises:
            TypeError: If Rope name comparison returned a non-boolean result.

        """
        if actual is None:
            return False
        expected_object = expected.get_object()
        builtin_types = (
            cls.runtime_type("rope.base.builtins", "BuiltinClass"),
            cls.runtime_type("rope.base.builtins", "BuiltinFunction"),
        )
        if (
            isinstance(expected_object, builtin_types)
            and isinstance(expected_object, p.Infra.RopeBuiltinClass)
            and expected_object.builtin
            and isinstance(actual_object := actual.get_object(), builtin_types)
            and isinstance(actual_object, p.Infra.RopeBuiltinClass)
        ):
            return expected_object.builtin is actual_object.builtin
        unknown = cls.runtime_callable("rope.base.pyobjects", "get_unknown")()
        if expected_object is unknown and expected.get_definition_location() == (
            None,
            None,
        ):
            return False
        result = cls.runtime_callable("rope.refactor.occurrences", "same_pyname")(
            expected,
            actual,
        )
        if not isinstance(result, bool):
            msg = "Rope name comparison returned a non-boolean result"
            raise TypeError(msg)
        # Infer the actual object only for a positive identity: inferring every
        # unrelated binding first made each reference scan re-run Rope inference.
        return result and not (
            actual.get_object() is unknown
            and actual.get_definition_location() == (None, None)
        )

    @staticmethod
    def imported_module_path(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopeImportedName,
        *,
        resolved: t.MutableMappingKV[p.Infra.RopeImportedModule, Path] | None = None,
    ) -> Path:
        """Resolve import provenance through Rope without evaluating its target.

        Generated initializers may still await publication. Their content is
        not required to identify which module an authored import names.
        A caller may retain resolutions for the same native import objects
        within its source observation.

        Returns:
            The resulting ``Path``.

        A ``ValueError`` propagates from ``imported_module_resource`` when the
        imported module is unresolved or the import has no declared module
        location.

        """
        if resolved is not None and binding.imported_module in resolved:
            return resolved[binding.imported_module]
        path = Path(
            FlextInfraUtilitiesRopeRuntimeModules.imported_module_resource(
                project, binding
            ).real_path
        ).resolve()
        if resolved is not None:
            resolved[binding.imported_module] = path
        return path

    @staticmethod
    def imported_module_resource(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopeImportedName,
    ) -> p.Infra.RopeResource:
        """Resolve a declared import through its native Rope resource identity.

        Returns:
            The exact file or package resource declared by the import.

        Raises:
            ValueError: If the declared import has no resolvable source resource.

        """
        imported = binding.imported_module
        resource = imported.resource
        if resource is None:
            name = imported.module_name
            module = imported.importing_module.get_module()
            source = module.get_resource()
            if source is None or (name is None and imported.level == 0):
                message = (
                    f"import has no declared module location: {binding.imported_name}"
                )
                raise ValueError(message)
            if imported.level == 0 and name is not None:
                resource = project.find_module(name, source.parent)
            else:
                resource = project.find_relative_module(
                    name if name is not None else "", source.parent, imported.level
                )
        if resource is None:
            message = f"unresolved imported module: {imported.module_name}"
            raise ValueError(message)
        return resource

    @classmethod
    def new_project(
        cls,
        root: str,
        *,
        ropefolder: str,
        save_objectdb: bool,
        filter_lists: t.Pair[t.SequenceOf[str], t.SequenceOf[str]],
    ) -> t.Infra.RopeProject:
        """Create one Rope project.

        ``filter_lists`` carries the Rope filter sequences in order:
        ignored resources, source folders. The project itself declares the
        interpreter's sourceless stdlib modules.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        Raises:
            TypeError: If Rope project does not satisfy its project contract.

        """
        ignored_resources, source_folders = filter_lists
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
        )
        if not isinstance(project, p.Infra.RopeProject):
            msg = "rope Project does not satisfy p.Infra.RopeProject"
            raise TypeError(msg)
        return project

    @classmethod
    def module_imports_for_pymodule(
        cls,
        rope_project: t.Infra.RopeProject,
        pymodule: t.Infra.RopeParsedModule,
    ) -> t.Infra.RopeModuleImports:
        source_module = pymodule.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(source_module):
            message = "Rope import operations require a source module"
            raise TypeError(message)
        loader = cls.runtime_callable(
            c.Infra.ROPE_IMPORTUTILS_MODULE,
            "get_module_imports",
        )
        result = loader(rope_project, source_module)
        if not isinstance(result, p.Infra.RopeModuleImports):
            msg = "rope get_module_imports returned invalid module imports"
            raise TypeError(msg)
        return result

    @classmethod
    def imported_binding_precedes(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        name: str,
        offset: int,
    ) -> bool:
        """Prove a binding is imported unconditionally before an occurrence.

        Returns:
            Whether Rope's module import inventory proves runtime availability.

        """
        line = module.lines.get_line_number(offset)
        imports = cls.module_imports_for_pymodule(project, module)
        return any(
            statement.start_line < line
            and any(
                (
                    alias
                    or (
                        imported
                        if isinstance(statement.import_info, p.Infra.RopeFromImport)
                        else imported.partition(".")[0]
                    )
                )
                == name
                for imported, alias in statement.import_info.names_and_aliases
            )
            for statement in imports.imports
        )

    @classmethod
    def import_binding(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        module_name: str,
        name: str | None,
    ) -> t.Pair[str, str]:
        """Plan an import and use the expression elected by Rope's import owner.

        ``name=None`` elects the module binding rather than a member binding.

        Returns:
            The resulting ``t.Pair[str, str]``.

        Raises:
            TypeError: If Rope add_import returned an invalid source and binding pair;
                or if Rope add_import returned non-text source or binding.

        """
        source_module = module.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(source_module):
            message = "Rope import insertion requires a source module"
            raise TypeError(message)
        result = cls.runtime_callable(c.Infra.ROPE_IMPORTUTILS_MODULE, "add_import")(
            project,
            source_module,
            module_name,
            name,
        )
        if not isinstance(result, p.Infra.RopeRuntimeSequence):
            msg = "Rope add_import returned an invalid source and binding pair"
            raise TypeError(msg)
        pair: p.Infra.RopeRuntimeSequence = result
        size = len(pair)
        source_binding_pair_size = 2
        if not isinstance(result, tuple) or size != source_binding_pair_size:
            msg = "Rope add_import returned an invalid source and binding pair"
            raise TypeError(msg)
        source, binding = pair[0], pair[1]
        if not isinstance(source, str) or not isinstance(binding, str):
            msg = "Rope add_import returned non-text source or binding"
            raise TypeError(msg)
        return (source, binding)

    @classmethod
    def build_string_module(
        cls,
        rope_project: t.Infra.RopeProject | None,
        source: str,
        *,
        resource: t.Infra.RopeResource | None = None,
    ) -> t.Infra.RopeSourceModule:
        loader = cls.runtime_callable("rope.base.libutils", "get_string_module")
        project = (
            rope_project
            if rope_project is not None
            else cls.runtime_callable("rope.base.project", "get_no_project")()
        )
        pymodule = loader(project, source, resource=resource, force_errors=True)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(pymodule):
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


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModules"]
