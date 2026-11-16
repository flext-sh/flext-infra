"""Rope lexical queries and module/import construction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import (
    Generator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from contextlib import contextmanager
from contextvars import ContextVar
from keyword import iskeyword
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from flext_core import build_lazy_import_map
from rope.base import exceptions as rope_exceptions
from typing_extensions import TypeForm

from flext_infra import c, m, p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAst,
    FlextInfraUtilitiesRopeAstBindings,
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesRopeRuntimeAliasIndices(
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
):
    """Retain candidate-scoped indexes for deferred annotation aliases."""

    _lazy_bindings_memo: ClassVar[
        dict[tuple[str, str, str, str], dict[str, p.Infra.SourceClassReference]]
    ] = {}

    @classmethod
    def resolve_lazy_export_bindings(
        cls,
        module: str,
        path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> Mapping[str, p.Infra.SourceClassReference]:
        """Read native lazy routes without losing their exported attributes.

        ``install_lazy_exports`` accepts both a provider string and an explicit
        ``(provider, attribute)`` pair. An empty attribute elects the module
        itself. The same typed binding feeds source and upstream resolution;
        module-only consumers derive their projection from these bindings.
        The owning project supplies native import identities even when the
        initializer is parsed from proposed source rather than a live module.

        Returns:
            The absolute provider and exact attribute of every declared export.

        Raises:
            ValueError: The parsed module differs from its native Rope snapshot.

        """
        # Lazy package propagation belongs to initializers. Ordinary module
        # bindings are resolved by the lexical inventory, so their executable
        # bodies are not inputs to this package-alias reader.
        if path.name != c.Infra.INIT_PY or not module:
            return {}
        # Only an initializer that names the installer can declare a lazy
        # route; any other one (a third-party distribution) is never handed to
        # the semantic scope analysis below.
        installer = "install_lazy_exports"
        if installer not in source:
            return {}
        # The bindings are a pure function of the initializer text, so one
        # read per distinct text serves every facade render of the process.
        key = (str(project), module, str(path), source)
        if pymodule is None and key in cls._lazy_bindings_memo:
            return dict(cls._lazy_bindings_memo[key])
        parsed = cls._lazy_initializer(project, source, pymodule)
        if key in cls._lazy_bindings_memo:
            return dict(cls._lazy_bindings_memo[key])
        aliases: dict[str, p.Infra.SourceClassReference] = {}
        for node in ast.walk(parsed.get_ast()):
            if not isinstance(node, ast.Call):
                continue
            scope = parsed.get_scope().get_inner_scope_for_line(node.lineno)
            if scope.get_kind() != c.Infra.RopeScopeKind.MODULE or not (
                cls._lazy_callable(
                    node.func,
                    scope,
                    ("flext_core", "flext_core.lazy"),
                    installer,
                )
            ):
                continue
            mapping = cls._lazy_alias_source(source, node, parsed)
            for name, (provider, attribute) in cls._lazy_exports(mapping).items():
                resolved = cls._lazy_absolute(module, provider)
                if resolved is None:
                    message = f"Lazy provider escapes its package: {module}.{name}"
                    raise ValueError(message)
                aliases[name] = m.Infra.SourceClassReference(
                    target=resolved,
                    attributes=(attribute,) if attribute else (),
                    qualified_base=f"{module}.{name}",
                )
        cls._lazy_bindings_memo[key] = aliases
        return dict(aliases)

    @staticmethod
    def _lazy_initializer(
        project: p.Infra.RopeProject,
        source: str,
        pymodule: p.Infra.RopeSemanticModule | None,
    ) -> p.Infra.RopeSourceModule:
        """Return the native Rope module of one initializer text.

        A required initializer that does not parse remains a real input error.

        Returns:
            The supplied module, or the one Rope builds from ``source``.

        Raises:
            TypeError: The parsed module is not a native Rope source module.
            ValueError: The parsed module differs from its native Rope snapshot.

        """
        parsed = (
            pymodule.get_module()
            if pymodule is not None
            else FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, source
            )
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(parsed):
            message = "Lazy aliases require a native Rope source module"
            raise TypeError(message)
        if parsed.source_code != source:
            message = "Lazy aliases differ from their native Rope snapshot"
            raise ValueError(message)
        return parsed

    @classmethod
    def _lazy_alias_source(
        cls,
        source: str,
        call: ast.Call,
        module: p.Infra.RopeParsedModule,
    ) -> str:
        """Return the alias-mapping argument text of one lazy-exports call.

        Args:
            source: Full native source text of the parsed package initializer.
            call: Native call authenticated against the SDK import binding.
            module: Authenticated native module supplying the call bindings.

        Returns:
            The literal mapping source declared by the actual call argument.

        Raises:
            ValueError: The call does not declare one inspectable mapping argument.

        """
        arguments = [
            keyword.value for keyword in call.keywords if keyword.arg == "lazy_imports"
        ]
        arguments.extend(call.args[2:3])
        if len(arguments) != 1:
            message = "Lazy exports require one declared mapping argument"
            raise ValueError(message)
        expression = ast.get_source_segment(source, arguments[0])
        if expression is None:
            message = "Lazy export mapping has no native source span"
            raise ValueError(message)
        return cls._lazy_mapping_source(expression, module)

    @classmethod
    def _lazy_mapping_source(
        cls,
        expression: str,
        module: p.Infra.RopeParsedModule,
        ancestors: frozenset[tuple[str, int]] = frozenset(),
    ) -> str:
        """Read one declared alias map without executing its source expressions.

        Returns:
            The dictionary literal supplied directly or through native bindings.

        Raises:
            TypeError: A native assignment has no expression value.
            ValueError: The map is ambiguous, cyclic, or not a declared literal.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        node = ast.parse(expression, mode="eval").body
        scope = module.get_scope()
        visited = set(ancestors)
        while True:
            if isinstance(node, ast.Dict):
                return cls._lazy_literal_source(expression, node)
            if isinstance(node, ast.Call):
                if cls._lazy_callable(
                    node.func,
                    scope,
                    ("flext_core", "flext_core.lazy"),
                    "build_lazy_import_map",
                ):
                    return cls._lazy_built_mapping(
                        node, expression, module, frozenset(visited)
                    )
                if (
                    not cls._lazy_callable(
                        node.func, scope, ("types",), "MappingProxyType"
                    )
                    or len(node.args) != 1
                    or node.keywords
                ):
                    message = "Lazy alias mapping requires its native immutable wrapper"
                    raise ValueError(message)
                node = node.args[0]
                continue
            binding = runtime.resolve_symbol(scope, node)
            if (
                binding is None
                or not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
                or len(binding.assignments) != 1
            ):
                message = "Lazy alias mapping requires one native assignment"
                raise ValueError(message)
            provider, line = runtime.definition_location(binding)
            if (
                not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider)
                or line is None
            ):
                message = "Lazy alias mapping requires a source declaration"
                raise ValueError(message)
            identity = provider.get_name(), line
            if identity in visited:
                message = f"Cyclic lazy alias mapping declaration: {identity!r}"
                raise ValueError(message)
            visited.add(identity)
            value = binding.assignments[0].ast_node
            if not isinstance(value, ast.expr):
                message = "Lazy alias mapping assignment has no native expression"
                raise TypeError(message)
            node = value
            module = provider
            expression = provider.source_code
            scope = provider.get_scope()

    @staticmethod
    def _lazy_literal_source(source: str, node: ast.Dict) -> str:
        """Read the authenticated mapping's native source span.

        Returns:
            The complete dictionary expression.

        Raises:
            ValueError: The native mapping has no source span.

        """
        literal = ast.get_source_segment(source, node)
        if literal is None:
            message = "Lazy alias mapping has no native source span"
            raise ValueError(message)
        return literal

    @staticmethod
    def _lazy_callable(
        expression: ast.expr,
        scope: p.Infra.RopeScope,
        expected_modules: Sequence[str],
        expected_attribute: str,
    ) -> bool:
        """Prove a declared SDK callable from native import metadata alone.

        Returns:
            Whether the expression is the elected absolute native import.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        declarations = scope.get_defined_names()
        if isinstance(expression, ast.Name):
            binding = declarations.get(expression.id)
            if not types.imported_name(binding):
                return False
            module = binding.imported_module
            attribute = binding.imported_name
        elif isinstance(expression, ast.Attribute) and isinstance(
            expression.value, ast.Name
        ):
            binding = declarations.get(expression.value.id)
            if not types.imported_module(binding):
                return False
            module = binding
            attribute = expression.attr
        else:
            return False
        return (
            module.module_name in expected_modules
            and module.level == 0
            and attribute == expected_attribute
        )

    @classmethod
    def _lazy_built_mapping(
        cls,
        call: ast.Call,
        source: str,
        module: p.Infra.RopeParsedModule,
        ancestors: frozenset[tuple[str, int]],
    ) -> str:
        """Compile literal SDK builder arguments through the native map owner.

        Returns:
            The canonical flat mapping literal produced by the SDK.

        Raises:
            ValueError: If arguments are ambiguous, dynamic or unsupported.

        """
        arguments = {keyword.arg: keyword.value for keyword in call.keywords}
        if (
            len(call.args) > 1
            or len(arguments) != len(call.keywords)
            or set(arguments) - {"module_groups", "alias_groups", "sort_keys"}
            or (call.args and "module_groups" in arguments)
        ):
            message = "Lazy builder requires its declared literal arguments"
            raise ValueError(message)
        if call.args:
            arguments["module_groups"] = call.args[0]
        modules: Mapping[str, Sequence[str]] = {}
        aliases: Mapping[str, Sequence[tuple[str, str]]] = {}
        for name in ("module_groups", "alias_groups"):
            argument = arguments.get(name)
            if argument is None or (
                isinstance(argument, ast.Constant) and argument.value is None
            ):
                continue
            expression = ast.get_source_segment(source, argument)
            if expression is None:
                message = "Lazy builder mapping has no native source span"
                raise ValueError(message)
            literal = ast.literal_eval(
                cls._lazy_mapping_source(expression, module, ancestors)
            )
            if name == "module_groups":
                modules = u.type_adapter(
                    TypeForm(Mapping[str, Sequence[str]])
                ).validate_python(literal, strict=True)
            else:
                aliases = u.type_adapter(
                    TypeForm(Mapping[str, Sequence[tuple[str, str]]])
                ).validate_python(literal, strict=True)
        sort = arguments.get("sort_keys", ast.Constant(value=True))
        match sort:
            case ast.Constant(value=True):
                sort_keys = True
            case ast.Constant(value=False):
                sort_keys = False
            case _:
                message = "Lazy builder ordering requires a literal boolean"
                raise ValueError(message)
        return repr(
            build_lazy_import_map(modules, alias_groups=aliases, sort_keys=sort_keys)
        )

    @staticmethod
    def _lazy_absolute(package: str, value: str) -> str | None:
        """Rewrite one relative alias value to an absolute provider module path.

        Args:
            package: Absolute name of the package owning the alias map.
            value: Raw alias value read from the native mapping literal.

        Returns:
            The absolute module path, or None when the relative depth escapes
            the package root.

        """
        if not value.startswith("."):
            return value
        parts = package.split(".") if package else []
        depth = len(value) - len(value.lstrip("."))
        remainder = value.lstrip(".")
        if depth > len(parts):
            return None
        base = ".".join(parts[: len(parts) - depth + 1]) if depth else package
        return ".".join(part for part in (base, remainder) if part)

    @staticmethod
    def _lazy_literal_string(node: ast.expr) -> str | None:
        """Decode one native string constant without executing its expression.

        Returns:
            The sole primitive string constant, or None for another expression.

        """
        code = compile(
            ast.Expression(body=node), "<native constant>", "eval", dont_inherit=True
        )
        if code.co_names or code.co_freevars or len(code.co_consts) != 1:
            return None
        value = code.co_consts[0]
        return value if isinstance(value, str) else None

    @classmethod
    def _lazy_exports(cls, source: str) -> t.LazyAliasMap:
        """Read the current native lazy export encodings from source regions.

        Returns:
            Provider and attribute pairs, including explicit module exports.

        Raises:
            ValueError: An export name or provider binding is not a literal string
                or a provider/attribute pair.

        """
        source = source.strip()
        if not (source.startswith("{") and source.endswith("}")):
            return {}
        result: MutableMapping[str, tuple[str, str]] = {}
        mapping = ast.parse(source, mode="eval").body
        if not isinstance(mapping, ast.Dict):
            return {}
        for key_node, value_node in zip(mapping.keys, mapping.values, strict=True):
            if key_node is None:
                return {}
            key = cls._lazy_literal_string(key_node)
            if key is None:
                message = "Lazy export names require literal strings"
                raise ValueError(message)
            provider = cls._lazy_literal_string(value_node)
            if provider is not None:
                result[key] = (provider, key)
                continue
            pair = (
                tuple(cls._lazy_literal_string(element) for element in value_node.elts)
                if isinstance(value_node, ast.Tuple)
                else ()
            )
            match pair:
                case (str() as provider, str() as attribute):
                    result[key] = (provider, attribute)
                case _:
                    message = (
                        "Lazy export requires a provider or provider/attribute "
                        f"pair: {key}"
                    )
                    raise ValueError(message)
        return result

    _alias_indices: ClassVar[
        ContextVar[
            dict[
                p.Infra.RopeSourceModule,
                dict[
                    p.Infra.RopePyName, tuple[ast.TypeAlias, p.Infra.RopeScope] | None
                ],
            ]
            | None
        ]
    ] = ContextVar("rope_annotation_alias_indices", default=None)

    @classmethod
    @contextmanager
    def annotation_alias_context(cls) -> Generator[None]:
        """Bind native alias identities to one candidate epoch, including nesting.

        Yields:
            A fresh index discarded even when the source pass raises.

        """
        token = cls._alias_indices.set({})
        try:
            yield
        finally:
            cls._alias_indices.reset(token)
            cls.invalidate_annotation_alias_indices()

    @classmethod
    def invalidate_annotation_alias_indices(cls) -> None:
        """Discard lexical conclusions when the candidate's native resolver changes."""
        indices = cls._alias_indices.get()
        if indices is not None:
            indices.clear()


class FlextInfraUtilitiesRopeRuntimeModules(
    FlextInfraUtilitiesRopeRuntimeAliasIndices,
):
    """Resolve lexical identities and construct Rope module/import objects."""

    @staticmethod
    def native_object_identity(value: p.Infra.RopePyObject) -> str:
        """Retain a native object's declaring module and complete scope path.

        Returns:
            The module and qualified path separated by ``::``, or an empty
            identity when the native object has no supported declaration.

        """
        if FlextInfraUtilitiesRopeRuntimeTypes.py_class(
            value
        ) or FlextInfraUtilitiesRopeRuntimeTypes.py_function(value):
            module = value.get_module()
            scope = value.get_scope()
            names: list[str] = []
            while scope.parent is not None:
                names.append(scope.pyobject.get_name())
                scope = scope.parent
            return f"{module.get_name()}::{'.'.join(reversed(names))}"
        if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value) and isinstance(
            value, p.Infra.RopeBuiltinClass
        ):
            return f"{value.builtin.__module__}::{value.builtin.__qualname__}"
        return ""

    @classmethod
    def annotation_alias_definition(
        cls,
        binding: p.Infra.RopePyName,
    ) -> tuple[ast.TypeAlias, p.Infra.RopeScope] | None:
        """Locate one native alias identity without evaluating its deferred value.

        Returns:
            The unique declaration and lexical scope, or None without native proof.

        """
        supplier = cls.source_import_binding(binding)
        if (
            supplier is None
            or not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(supplier)
            or supplier.assignments
        ):
            return None
        module, _line = cls.definition_location(supplier)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            return None
        indices = cls._alias_indices.get()
        if indices is None:
            return cls._annotation_alias_index(module).get(supplier)
        if module not in indices:
            indices[module] = cls._annotation_alias_index(module)
        return indices[module].get(supplier)

    @classmethod
    def _annotation_alias_index(
        cls, module: p.Infra.RopeSourceModule
    ) -> dict[p.Infra.RopePyName, tuple[ast.TypeAlias, p.Infra.RopeScope] | None]:
        """Index exact native alias bindings once without evaluating alias values.

        Returns:
            Declaration and lexical scope by identity; ambiguous bindings stay None.

        """
        declarations: dict[
            p.Infra.RopePyName, tuple[ast.TypeAlias, p.Infra.RopeScope] | None
        ] = {}
        for node in ast.walk(module.get_ast()):
            if not isinstance(node, ast.TypeAlias):
                continue
            lexical = cls.scope_at(module, cls.source_offset(module.source_code, node))
            # TypeAlias bindings intentionally have no inferred assignment or
            # line in Rope. Only the source token's exact identity proves them.
            binding = cls.resolve_symbol(lexical, node.name)
            if binding is not None:
                declarations[binding] = (
                    None if binding in declarations else (node, lexical)
                )
        return declarations

    @classmethod
    def annotation_assignment_outer_type(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        *,
        path: tuple[int, ...] | None = None,
    ) -> tuple[p.Infra.RopePyName, bool] | None:
        """Resolve a native annotation identity and its value provenance.

        ``path`` selects a payload argument through the native declaration's
        Annotated and alias bindings; None retains its written outer identity.

        Returns:
            The native identity and RHS provenance, or None without proof.

        """
        supplier = cls.source_import_binding(binding)
        if supplier is None or not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(
            supplier
        ):
            return None
        assignments = [
            assignment for assignment in supplier.assignments if assignment.type_hint
        ]
        if len(assignments) != 1:
            return None
        assignment = assignments[0]
        assigned = assignment.ast_node
        annotation = assignment.type_hint
        module, _line = cls.definition_location(supplier)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            return None
        if isinstance(annotation, ast.Name | ast.Attribute | ast.Subscript):
            expression = annotation
            from_value = False
        elif isinstance(assigned, ast.Subscript):
            expression = assigned
            from_value = True
        else:
            return None
        scope = cls.scope_at(module, cls.source_offset(module.source_code, expression))
        origin = (
            cls.annotation_origin(project, expression, scope, path=path or ())
            if from_value or path is not None
            else cls.resolve_symbol(
                scope,
                expression.value
                if isinstance(expression, ast.Subscript)
                else expression,
            )
        )
        return (origin, from_value) if origin is not None else None

    @classmethod
    def annotation_origin(
        cls,
        project: p.Infra.RopeProject,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        *,
        visiting: frozenset[tuple[str, int]] = frozenset(),
        path: tuple[int, ...] = (),
    ) -> p.Infra.RopePyName | None:
        """Resolve native payload types and argument paths without alias execution.

        Returns:
            The native type identity, or None when no safe origin is proven.

        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return cls.annotation_origin(
                project,
                ast.parse(node.value, mode="eval").body,
                scope,
                visiting=visiting,
                path=path,
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
                project, node.slice.elts[0], scope, visiting=visiting, path=path
            )
        if path:
            return cls._annotation_argument_origin(
                project, node, scope, (path, visiting)
            )
        return cls._annotation_root_origin(project, binding, visiting)

    @classmethod
    def _annotation_root_origin(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName | None,
        visiting: frozenset[tuple[str, int]],
    ) -> p.Infra.RopePyName | None:
        """Follow the existing native alias chain at its declaring scope.

        Returns:
            The resolved native origin, or None when the alias chain cycles.

        """
        alias = None if binding is None else cls.annotation_alias_definition(binding)
        if alias is None:
            return binding
        declaration, lexical = alias
        identity = (lexical.pyobject.get_module().get_name(), declaration.lineno)
        if identity in visiting:
            return None
        return cls.annotation_origin(
            project, declaration.value, lexical, visiting=visiting | {identity}
        )

    @classmethod
    def _annotation_argument_origin(
        cls,
        project: p.Infra.RopeProject,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        traversal: tuple[tuple[int, ...], frozenset[tuple[str, int]]],
    ) -> p.Infra.RopePyName | None:
        """Select an argument from its authenticated source or direct alias.

        Returns:
            The selected argument's native origin, or None when it cannot be
            authenticated.

        """
        if not isinstance(node, ast.Subscript):
            return None
        path, visiting = traversal
        arguments = (
            node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        )
        binding = cls.resolve_symbol(scope, node.value)
        alias = None if binding is None else cls.annotation_alias_definition(binding)
        selected = (
            cls._annotation_alias_argument(alias, (arguments, scope), path[0])
            if alias is not None
            else (arguments[path[0]], scope)
            if 0 <= path[0] < len(arguments)
            else None
        )
        return (
            None
            if selected is None
            else cls.annotation_origin(
                project, selected[0], selected[1], visiting=visiting, path=path[1:]
            )
        )

    @classmethod
    def _annotation_alias_argument(
        cls,
        alias: tuple[ast.TypeAlias, p.Infra.RopeScope],
        supplied: tuple[Sequence[ast.expr], p.Infra.RopeScope],
        index: int,
    ) -> tuple[ast.expr, p.Infra.RopeScope] | None:
        """Project a direct generic alias's argument using declared parameter order.

        Returns:
            The argument expression and its lexical scope, or None when the
            alias does not project one declared parameter.

        """
        declaration, lexical = alias
        if not isinstance(declaration.value, ast.Subscript):
            return None
        binding = cls.resolve_symbol(lexical, declaration.value.value)
        if binding is None or cls.annotation_alias_definition(binding) is not None:
            return None
        arguments = (
            declaration.value.slice.elts
            if isinstance(declaration.value.slice, ast.Tuple)
            else [declaration.value.slice]
        )
        parameters = tuple(
            parameter.name
            for parameter in declaration.type_params
            if isinstance(parameter, ast.TypeVar)
        )
        if (
            not 0 <= index < len(arguments)
            or len(parameters) != len(declaration.type_params)
            or len(supplied[0]) != len(parameters)
        ):
            return None
        selected = arguments[index]
        if not isinstance(selected, ast.Name):
            return None
        return (
            (supplied[0][parameters.index(selected.id)], supplied[1])
            if selected.id in parameters
            else (selected, lexical)
        )

    @classmethod
    def call_data_return_constraint(
        cls,
        project: p.Infra.RopeProject,
        expression: ast.expr,
        scope: p.Infra.RopeScope,
        *,
        inferred: p.Infra.RopePyObject | None,
    ) -> bool:
        """Prove a source call's concrete data return without inventing a value.

        Returns:
            Whether its native return annotation excludes class identities.

        """
        if not isinstance(expression, ast.Call) or (
            inferred is not None
            and FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(inferred)
        ):
            return False
        binding = cls.resolve_symbol(scope, expression.func)
        function = None if binding is None else binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(function):
            return False
        declaration = function.get_ast()
        module = function.get_module()
        if (
            not isinstance(declaration, ast.FunctionDef)
            or declaration.returns is None
            or not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module)
        ):
            return False
        context = module.get_source_binding_index().context_at(
            cls.source_offset(module.source_code, declaration.returns)
        )
        origin = cls.annotation_origin(
            project, declaration.returns, context.environment
        )
        candidate = None if origin is None else origin.get_object()
        return cls.concrete_data_class(candidate)

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
        if not isinstance(result, p.Infra.RopePyName):
            return None
        target = cls._native_export_target(result)
        return result if target is None else target

    @classmethod
    def _native_export_target(
        cls, binding: p.Infra.RopePyName
    ) -> p.Infra.RopePyName | None:
        """Follow a native-export wrapper assignment to the value it republishes.

        A facade member declared as ``Name = <native export wrapper>(value)``
        denotes ``value`` itself: the wrapper exists only to keep the native
        callable's complete type, so both spellings are one declaration.

        Returns:
            The wrapped expression's binding, or None when ``binding`` is not the
            sole assignment of one native-export wrapper call.

        """
        if (
            not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
            or len(binding.assignments) != 1
        ):
            return None
        call = binding.assignments[0].ast_node
        if not isinstance(call, ast.Call) or len(call.args) != 1 or call.keywords:
            return None
        module, _line = cls.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            return None
        scope = cls.scope_at(module, cls.source_offset(module.source_code, call))
        wrapper = cls.expression_name(scope, ast.unparse(call.func))
        if (
            wrapper is None
            or cls.native_object_identity(wrapper.get_object())
            != c.Infra.NATIVE_EXPORT_IDENTITY
        ):
            return None
        return cls.expression_name(scope, ast.unparse(call.args[0]))

    @staticmethod
    def lexical_scope(scope: p.Infra.RopeScope, name: str) -> p.Infra.RopeScope | None:
        """Resolve lexical names without treating inherited members as locals.

        Returns:
            The native declaring scope, including global interpreter builtins.

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
            current = getattr(current, "parent", None)
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

        Args:
            project: The Rope project instance.
            expression: The dotted expression representing the attribute path.
            module_name: Optional explicit module name to resolve the
                expression against.

        Returns:
            The declaration reached through the native module object graph.

        Raises:
            ValueError: When the identity does not name an attribute.
            TypeError: The fetched provider violates its native semantic contract.
            AttributeNotFoundError: When the requested attribute is not found
                on the module.
            ModuleSyntaxError: When the module has invalid syntax.

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
        except rope_exceptions.ModuleSyntaxError:
            # Conteúdo candidate inválido no overlay (staging do
            # quoted-move troca conteúdos no mesmo path): resolve pela
            # rota lazy do pacote publicador quando existe; sem rota, a
            # identidade é ilegível neste ponto fixo — propaga limpa.
            target = (
                FlextInfraUtilitiesRopeRuntimeModules._lazy_route(
                    project, module.rpartition(".")[0], attributes[0]
                )
                if "." in module
                else None
            )
            if target is None:
                raise
            owner = f"{module.rpartition('.')[0]}{target}"
            return FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project,
                ".".join(attributes),
                module_name=owner,
            )
        try:
            identity = value.get_attribute(attributes[0])
        except rope_exceptions.AttributeNotFoundError:
            # Fachadas lazy-init (``install_lazy_exports``) publicam o mapa
            # de rotas como argumento literal do call no __init__ (SSOT
            # estática: ``nome -> ".caminho"`` ou ``(".caminho", nome)``).
            target = FlextInfraUtilitiesRopeRuntimeModules._lazy_route(
                project, module, attributes[0]
            )
            if target is None:
                raise
            owner = f"{module}{target}" if target.startswith(".") else target
            return FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project,
                ".".join(attributes[1:]) or attributes[0],
                module_name=owner,
            )
        for attribute in attributes[1:]:
            identity = identity.get_object().get_attribute(attribute)
        return identity

    @staticmethod
    def _lazy_route(
        project: p.Infra.RopeProject,
        module_name: str,
        name: str,
    ) -> str | None:
        """Reads the lazy-init route of one export from the package's SSOT call.

        Returns:
            The relative module path bound to ``name``, or none without the
            lazy contract.

        """
        package = project.get_module(module_name)
        resource = package.get_resource()
        if resource is None:
            return None
        tree = project.get_pymodule(resource).get_ast()
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", "") == "install_lazy_exports"
            ):
                continue
            mapping_index = c.Infra.LAZY_EXPORT_MAPPING_ARGUMENT_INDEX
            if len(node.value.args) <= mapping_index:
                continue
            mapping = node.value.args[mapping_index]
            inner = (
                mapping.args[0]
                if isinstance(mapping, ast.Call) and mapping.args
                else mapping
            )
            if not isinstance(inner, ast.Dict):
                continue
            for key_node, value_node in zip(inner.keys, inner.values, strict=False):
                if (
                    isinstance(key_node, ast.Constant)
                    and key_node.value == name
                    and isinstance(value_node, ast.Constant)
                    and isinstance(value_node.value, str)
                ):
                    return value_node.value
        return None

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
        expression: p.Infra.RopeAstNode | str,
    ) -> p.Infra.RopePyName | None:
        """Resolve native identifier syntax or a declared identifier route.

        Missing bindings retain their native absence. Hierarchy and integrity
        errors propagate to the caller's repository result boundary unchanged.

        Returns:
            The resulting ``p.Infra.RopePyName | None``.

        Raises:
            TypeError: If Rope identifier resolution returned an invalid name.
            ValueError: A declared route is not an identifier chain.

        """
        attributes: Sequence[str]
        if isinstance(expression, str):
            names = expression.split(".")
            if any(not name.isidentifier() or iskeyword(name) for name in names):
                message = f"Rope identifier route is invalid: {expression}"
                raise ValueError(message)
            attributes = names[1:]
            result = cls.runtime_callable("rope.base.evaluate", "eval_str")(
                scope, names[0]
            )
        else:
            primary = expression
            reversed_attributes: list[str] = []
            while isinstance(primary, ast.Attribute):
                reversed_attributes.append(primary.attr)
                primary = primary.value
            if not isinstance(primary, ast.Name):
                return None
            attributes = tuple(reversed(reversed_attributes))
            result = cls.runtime_callable("rope.base.evaluate", "eval_node")(
                scope,
                primary,
            )
        if result is not None and not isinstance(result, p.Infra.RopePyName):
            msg = "Rope identifier resolution returned an invalid name"
            raise TypeError(msg)
        for attribute in attributes:
            result = cls.class_assignment_binding(result)
            if result is None:
                return None
            result = result.get_object().get_attributes().get(attribute)
        return cls.class_assignment_binding(result)

    @classmethod
    def class_assignment_binding(
        cls,
        binding: p.Infra.RopePyName | None,
        *,
        visited: frozenset[tuple[str, int]] = frozenset(),
        classes_only: bool = True,
    ) -> p.Infra.RopePyName | None:
        """Resolve a class alias through its native pre-assignment name view.

        Returns:
            The proven native alias, or None for an ambiguous lexical binding.
            Kind queries may include value origins; binding queries retain them.

        Raises:
            TypeError: If the native alias holder does not expose its Python AST.
            ValueError: If the class assignment identity is cyclic.

        """
        if not isinstance(binding, p.Infra.RopeAssignedName):
            return binding
        holder, line = binding.get_definition_location()
        if holder is not None and line is not None:
            tree = holder.get_ast()
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
                    binding=binding,
                    visited=visited | {key},
                    classes_only=classes_only,
                )
        return binding

    @staticmethod
    def _class_alias_primary(
        declaration: ast.Assign | ast.AnnAssign,
    ) -> ast.expr | None:
        """Return the root name behind one alias declaration value.

        Returns:
            The referenced name expression, or None when the declaration
            value is not a bare name reference.

        """
        primary: ast.expr | None = declaration.value
        if primary is None or not isinstance(primary, c.Infra.AST_NAME_REFERENCE_TYPES):
            return None
        while isinstance(primary, ast.Attribute):
            primary = primary.value
        return primary

    @staticmethod
    def _class_alias_declaration(
        holder: p.Infra.RopeParsedModule,
        tree_index: dict[int, ast.AST | None],
        rhs_offset: int,
    ) -> ast.AST | None:
        """Return the unique statement at the alias RHS offset, if any.

        Returns:
            The unique assignment declaration, or None when the offset has
            no statement under the class alias policy.

        Raises:
            ValueError: The offset is shared by more than one statement.

        """
        declaration = tree_index.get(rhs_offset)
        if declaration is not None:
            return declaration
        if rhs_offset in tree_index:
            msg = (
                "native class alias RHS has no unique statement: "
                f"{holder.get_name()}:{rhs_offset}"
            )
            raise ValueError(msg)
        # Native loop/context/pattern bindings are outside class alias policy.
        return None

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
        # Single-read law (ADR-028 D17): one offset index per native tree,
        # not one whole-module walk per binding. The index is keyed by tree
        # identity; rope rebuilds the tree on change, so a rebuilt module
        # naturally becomes a new index and never serves stale offsets.
        tree_index = cls._tree_assignment_index(tree, source)
        declaration = cls._class_alias_declaration(holder, tree_index, rhs_offset)
        if (
            declaration is None
            or not isinstance(declaration, ast.Assign | ast.AnnAssign)
            or (primary := cls._class_alias_primary(declaration)) is None
        ):
            return None
        offset = cls.source_offset(source, declaration)
        scope = cls.scope_at(holder, offset)
        if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
            return None
        return holder, declaration, scope, offset, primary

    # Pass-scoped memo (single-invocation lifecycle): tree identity keys
    # keep entries fresh; the process boundary is the cache boundary.
    _tree_assignment_indexes: ClassVar[
        dict[int, tuple[ast.AST, dict[int, ast.AST | None]]]
    ] = {}

    @classmethod
    def _tree_assignment_index(
        cls,
        tree: ast.AST,
        source: str,
    ) -> dict[int, ast.AST | None]:
        """Return the tree's assignment-value offset index, walked once.

        A None entry marks an offset shared by two statements (ambiguous).
        The entry keeps a strong reference to its tree so an index cannot
        outlive the tree its identity keys.

        Returns:
            The map of each assignment value's source offset to its node,
            or None where the offset is ambiguous.

        """
        indexes = cls._tree_assignment_indexes
        entry = indexes.get(id(tree))
        if entry is not None and entry[0] is tree:
            return entry[1]
        index: dict[int, ast.AST | None] = {}
        for node in ast.walk(tree):
            if (
                isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
                and node.value is not None
            ):
                offset = cls.source_offset(source, node.value)
                if offset in index and index[offset] is not node:
                    # Two statements share one value offset: the offset is
                    # ambiguous and lookups must stay loud about it.
                    index[offset] = None
                else:
                    index[offset] = node
        indexes[id(tree)] = (tree, index)
        return index

    @classmethod
    def _class_alias_namespace(
        cls,
        holder: p.Infra.RopeSourceModule,
        tree: ast.AST,
        scope: p.Infra.RopeScope,
        primary: ast.Name,
        offset: int,
    ) -> tuple[p.Infra.RopeScope, dict[str, p.Infra.RopePyName]] | None:
        source = holder.source_code
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
        *,
        binding: p.Infra.RopePyName,
        visited: frozenset[tuple[str, int]],
        classes_only: bool,
    ) -> p.Infra.RopePyName | None:
        attributes: list[str] = []
        value = declaration.value
        while isinstance(value, ast.Attribute):
            attributes.append(value.attr)
            value = value.value
        if not isinstance(value, ast.Name):
            message = "native class alias has no identifier origin"
            raise TypeError(message)
        result = cls.runtime_callable("rope.base.evaluate", "eval_node")(
            temporary,
            value,
        )
        if result is not None and not isinstance(result, p.Infra.RopePyName):
            msg = "class RHS lookup returned an invalid native name"
            raise TypeError(msg)
        result = cls.class_assignment_binding(
            result, visited=visited, classes_only=classes_only
        )
        for attribute in reversed(attributes):
            if result is None:
                return None
            result = result.get_object().get_attributes().get(attribute)
            result = cls.class_assignment_binding(
                result, visited=visited, classes_only=classes_only
            )
        if (
            classes_only
            and result is not None
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
    ) -> list[tuple[ast.AST, bool]]:
        """Elect structural lexical writes and their actual execution positions.

        Returns:
            Matching lexical writes with their unconditional execution status.

        """
        parents = FlextInfraUtilitiesRopeAst.ast_parent_map(tree)
        frames = (
            ast.Module,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Lambda,
        )
        selected: list[tuple[ast.AST, bool]] = []
        for node in ast.walk(tree):
            if name not in FlextInfraUtilitiesRopeAstBindings.bound_identifiers(node):
                continue
            parent = parents.get(id(node))
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
                parent = parents.get(id(parent))
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
        resolved: MutableMapping[p.Infra.RopeImportedModule, Path] | None = None,
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
        *,
        binding_scopes: Sequence[p.Infra.RopeScope] = (),
    ) -> tuple[str, str]:
        """Plan an import and use the expression elected by Rope's import owner.

        ``name=None`` elects the module binding rather than a member binding.

        Returns:
            The resulting ``tuple[str, str]``.

        Raises:
            TypeError: If Rope add_import returned an invalid source and binding pair;
                or if Rope add_import returned non-text source or binding.

        """
        source_module = module.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(source_module):
            message = "Rope import insertion requires a source module"
            raise TypeError(message)
        if binding_scopes and name is not None:
            return cls._scoped_import_binding(
                project, source_module, (module_name, name), binding_scopes
            )
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
    def _scoped_import_binding(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeSourceModule,
        imported: tuple[str, str],
        scopes: Sequence[p.Infra.RopeScope],
    ) -> tuple[str, str]:
        """Elect a capture-free import binding through native lexical names.

        Returns:
            The native candidate and its elected member expression.

        """
        provider, name = imported
        target = cls.qualified_name(project, f"{provider}.{name}").get_object()
        if all(
            (binding := scope.lookup(name)) is not None
            and binding.get_object() is target
            for scope in scopes
        ):
            return module.source_code, name
        alias = name
        while any(scope.lookup(alias) is not None for scope in scopes):
            alias += "_"
        imports = cls.module_imports_for_pymodule(project, module)
        imports.add_import(cls.from_import(provider, 0, ((name, alias),)))
        return imports.get_changed_source(), alias

    @classmethod
    def file_resource_at(
        cls, rope_project: t.Infra.RopeProject, path: Path
    ) -> t.Infra.RopeFile:
        """Return the engine's file resource for one absolute source path.

        A path inside the project root is a project resource and follows its
        overlay; a path outside it is an external file the engine reads as is.

        Returns:
            The file resource of ``path``.

        """
        loader = cls.runtime_callable("rope.base.libutils", "path_to_resource")
        return FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            loader(rope_project, str(path), type="file"), path
        )

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
    def runtime_find_occurrences(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        resources: Sequence[t.Infra.RopeResource] | None,
        in_hierarchy: bool,
    ) -> Sequence[t.Infra.RopeLocation]:
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
        locations: MutableSequence[t.Infra.RopeLocation] = []
        for location in raw_locations:
            if not isinstance(location, p.Infra.RopeLocation):
                msg = "rope find_occurrences returned an invalid location"
                raise TypeError(msg)
            locations.append(location)
        return tuple(locations)


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModules"]
