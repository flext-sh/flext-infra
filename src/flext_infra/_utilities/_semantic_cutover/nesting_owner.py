"""Module-owner derivation for class nesting of loose modules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import os
import typing
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_cli import u

from flext_infra import c, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._rope._analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraUtilitiesSemanticCutoverNestingOwner:
    """Derive one module owner and the loose members it absorbs.

    Family owners follow their declared facade contract. Ordinary modules elect
    their existing unique owner before deriving a new name from the convention.
    Functions (including entry points), values and helper classes become members;
    definition-time dependencies remain subject to the same safety checks.
    """

    @staticmethod
    def _nesting_declaration_destinations(
        module: p.Infra.RopePyModule,
        definitions: t.StrMapping,
    ) -> t.StrMapping:
        """Elect real declaration scopes when class locals shadow type parameters.

        Python annotation scopes consult their containing class dictionary.
        Moving an alias whose parameter collides with that dictionary therefore
        requires a separate declaration class, not a re-export or a new alias.
        Native declaration names supply the existing class-stem naming owner.

        Returns:
            Original destinations, or the elected hierarchical declaration paths.

        Raises:
            TypeError: The provider lacks a native module AST.
            ValueError: An isolated declaration scope cannot preserve its bindings.

        """
        if not definitions:
            return definitions
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            msg = "class-nesting declarations require a native module AST"
            raise TypeError(msg)
        owner = next(iter(definitions.values()))
        binding = module.get_scope().get_defined_names().get(owner)
        scope = (
            FlextInfraUtilitiesRopeRuntimeTypes.require_source_object(
                binding.get_object(), owner
            ).get_scope()
            if binding is not None
            else None
        )
        occupied = set(definitions)
        if scope is not None:
            occupied.update(scope.get_defined_names())
        isolated: t.MutableMappingKV[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.TypeAlias) or node.name.id not in definitions:
                continue
            parameters = frozenset(
                parameter.name
                for parameter in node.type_params
                if isinstance(parameter, c.Infra.AST_TYPE_PARAM_TYPES)
            )
            if not parameters.intersection(occupied):
                continue
            namespace = u.derive_class_stem(node.name.id)
            if (
                node.name.id in parameters
                or not namespace.isidentifier()
                or namespace in occupied - {node.name.id}
                or namespace in isolated.values()
            ):
                msg = (
                    "class-nesting cannot preserve native type parameter scope: "
                    f"{module.get_name()}.{node.name.id} under {owner}.{namespace}"
                )
                raise ValueError(msg)
            isolated[node.name.id] = namespace
        if not isolated:
            return definitions
        return {
            name: f"{destination}.{isolated[name]}" if name in isolated else destination
            for name, destination in definitions.items()
        }

    @staticmethod
    def _pytest_collection_patterns(
        root: Path,
    ) -> t.Triple[t.StrTuple, t.StrTuple, t.StrTuple]:
        """Read native configuration and defaults without running consumer plugins.

        Returns:
            A triple of ``(python_files, python_classes, python_functions)``
            collection pattern tuples.

        """
        manager = pytest.PytestPluginManager()
        for plugin in ("main", "helpconfig", "python"):
            manager.import_plugin(plugin)
        # Blocking precedes native consider_env, which otherwise imports these
        # modules even when entry-point autoload and conftest loading are disabled.
        for plugin in os.environ.get("PYTEST_PLUGINS", "").split(","):
            if plugin and not manager.has_plugin(plugin):
                manager.set_blocked(plugin)
        arguments = [
            str(root),
            "--disable-plugin-autoload",
            "--noconftest",
            "-o",
            "pythonpath=",
            "-o",
            "required_plugins=",
            "-o",
            "minversion=",
        ]
        configured = pytest.Config(
            manager,
            invocation_params=pytest.Config.InvocationParams(
                args=arguments, plugins=None, dir=root
            ),
        )
        # This is configuration discovery, not test startup: no consumer addopts,
        # sys.path mutation, plugin prerequisites, or assertion-rewrite plugin.
        configured.parse(arguments, addopts=False)

        def patterns(key: str) -> t.StrTuple:
            value: p.AttributeProbe = configured.getini(key)
            if isinstance(value, p.Infra.RopeRuntimeSequence):
                iterate = value.__iter__
                if isinstance(value, list) and all(
                    isinstance(item, str) for item in iterate()
                ):
                    return tuple(item for item in iterate() if isinstance(item, str))
            msg = f"pytest collection setting {key} must contain strings"
            raise TypeError(msg)

        return (
            patterns("python_files"),
            patterns("python_classes"),
            patterns("python_functions"),
        )

    @staticmethod
    def _pytest_name_matches(name: str, patterns: t.StrSequence) -> bool:
        """Match pytest's native prefix-or-glob class/function selectors.

        Returns:
            Whether ``name`` matches any prefix or glob pattern.

        """
        return any(
            name.startswith(pattern) or fnmatch(name, pattern) for pattern in patterns
        )

    @classmethod
    def _pytest_class_binding(
        cls,
        name: str,
        binding: p.Infra.RopePyName,
        patterns: t.StrSequence,
    ) -> bool:
        """Prove native class selection, including source-owned inherited flags.

        The suite need not define test methods itself: native pytest also visits
        inherited tests and custom method collectors on the original class object.

        Returns:
            Whether the binding is a natively collected test class.

        Raises:
            TypeError: When the ``__test__`` flag's definition location is not
                a captured source module.
            ValueError: When the ``__test__`` flag lacks native collection
                evidence.

        """
        if not cls._pytest_name_matches(name, patterns):
            return False
        definition = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(definition):
            return False
        scope = definition.get_scope()
        if scope.get_kind() != "Class":
            return False
        flag = definition.get_attributes().get("__test__")
        if flag is None:
            return True
        provider, line = flag.get_definition_location()
        if not isinstance(provider, p.Infra.RopePyModule):
            msg = f"pytest class flag has no captured source: {name}"
            raise TypeError(msg)
        for node in ast.walk(ast.parse(provider.source_code)):
            if (
                isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
                and node.lineno == line
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, bool)
            ):
                return node.value.value
        msg = (
            "pytest class flag requires native collection "
            f"evidence: {provider.get_name()}.{name}"
        )
        raise ValueError(msg)

    @staticmethod
    def _pytest_mark_decorator(decorator: ast.expr, tree: ast.Module) -> bool:
        """Prove a decorator comes from pytest.mark, including imported spellings.

        Returns:
            Whether the decorator resolves to ``pytest.mark``.

        """
        expression = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not isinstance(expression, ast.Attribute):
            return False
        mark = expression.value
        for statement in tree.body:
            if isinstance(statement, ast.Import) and any(
                alias.name == "pytest"
                and isinstance(mark, ast.Attribute)
                and mark.attr == "mark"
                and isinstance(mark.value, ast.Name)
                and mark.value.id == (alias.asname or alias.name)
                for alias in statement.names
            ):
                return True
            if (
                isinstance(statement, ast.ImportFrom)
                and statement.module == "pytest"
                and any(
                    alias.name == "mark"
                    and isinstance(mark, ast.Name)
                    and mark.id == (alias.asname or alias.name)
                    for alias in statement.names
                )
            ):
                return True
        return False

    @classmethod
    def _test_module_owner(
        cls,
        convention: m.Infra.RopeModuleConvention,
        file_path: Path,
        classes: t.MappingKV[str, ast.ClassDef],
        patterns: t.Pair[t.StrSequence, t.StrSequence],
        *,
        collection: t.Pair[bool, bool],
    ) -> p.Result[str]:
        """Elect an existing collected suite, otherwise derive Tests<Unit>.

        Returns:
            The elected or derived suite class name, or a failure when
            collection is ambiguous or the derived suite is not collected.

        """
        class_patterns, function_patterns = patterns
        require_collection, composition = collection
        elected = r[str]
        prefix = convention.module_policy.project_prefix
        prefix = prefix if prefix.startswith("Tests") else f"Tests{prefix}"
        if composition:
            stem = (
                file_path.stem
                .removeprefix("test_")
                .removesuffix("_tests")
                .removesuffix("_test")
            )
            owner = prefix + u.derive_class_stem(stem)
            while owner in classes:
                owner += u.derive_class_stem("module")
            return elected.ok(owner)
        suites = [
            name
            for name, node in classes.items()
            if cls._pytest_name_matches(name, class_patterns)
            and any(
                isinstance(member, c.Infra.AST_FUNCTION_TYPES)
                and cls._pytest_name_matches(member.name, function_patterns)
                for member in node.body
            )
        ]
        if len(suites) > 1:
            return elected.fail(
                f"class-nesting requires exactly one collected suite for "
                f"{convention.module_name}: {', '.join(suites)}",
            )
        if suites:
            if suites[0].startswith(prefix):
                return elected.ok(suites[0])
            return elected.fail(
                f"class-nesting requires native Rope prefix rename before electing "
                f"{convention.module_name}.{suites[0]} (required prefix {prefix})",
            )
        if len(classes) == 1:
            existing = next(iter(classes))
            if existing.startswith(prefix) and (
                not require_collection
                or cls._pytest_name_matches(existing, class_patterns)
            ):
                return elected.ok(existing)
        stem = (
            file_path.stem
            .removeprefix("test_")
            .removesuffix("_tests")
            .removesuffix("_test")
        )
        return cls._derived_test_owner(
            convention,
            stem,
            prefix,
            class_patterns,
            require_collection=require_collection,
        )

    @classmethod
    def _derived_test_owner(
        cls,
        convention: m.Infra.RopeModuleConvention,
        stem: str,
        prefix: str,
        patterns: t.StrSequence,
        *,
        require_collection: bool,
    ) -> p.Result[str]:
        elected = r[str]
        owner = (
            prefix if prefix.startswith("Tests") else f"Tests{prefix}"
        ) + u.derive_class_stem(stem)
        if not owner.isidentifier() or (
            require_collection and not cls._pytest_name_matches(owner, patterns)
        ):
            return elected.fail(
                f"class-nesting derived suite {owner} is not collected by pytest "
                f"in {convention.module_name}",
            )
        return elected.ok(owner)

    @staticmethod
    def _tail_name(node: ast.expr) -> str:
        """Return the last dotted segment of a name or attribute expression.

        Returns:
            The trailing identifier, or an empty string for other shapes.

        """
        if isinstance(node, ast.Subscript):
            node = node.value
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Name):
            return node.id
        return ""

    @classmethod
    def _is_typing_declaration(
        cls,
        value: ast.expr,
        annotation: ast.expr | None,
    ) -> bool:
        """Whether a binding is a typing declaration, not a module value.

        Typing declarations belong to ban-manual-typing-alias-outside-typings:
        an explicit ``TypeAlias`` binding, or a binding constructed by a class
        the ``typing`` module exports (TypeVar, ParamSpec, NewType...).

        Returns:
            The resulting ``bool``.

        """
        if (
            annotation is not None
            and getattr(typing, cls._tail_name(annotation), None) is typing.TypeAlias
        ):
            return True
        return isinstance(value, ast.Call) and isinstance(
            getattr(typing, cls._tail_name(value.func), None),
            type,
        )

    @classmethod
    def _is_pure_reference(cls, value: ast.expr) -> bool:
        """Whether ``value`` only names another binding (``A`` or ``A.B.C``).

        A pure reference is a compatibility alias the compat-alias phase owns
        (inline every consumer, then delete it); nesting it under the facade
        owner would publish the alias instead of removing it.

        Returns:
            The resulting ``bool``.

        """
        if isinstance(value, ast.Attribute):
            return cls._is_pure_reference(value.value)
        return isinstance(value, ast.Name)

    @classmethod
    def _loose_value_name(cls, node: ast.stmt, *, strict: bool = False) -> str | None:
        """Return the bound name of a loose value or explicit PEP 695 alias.

        Returns:
            The bound identifier, or ``None`` for an allowed or foreign shape.

        """
        if isinstance(node, ast.TypeAlias):
            return node.name.id
        if (
            strict
            and isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
        ):
            return node.target.id
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value, annotation = node.targets[0], node.value, None
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value, annotation = node.target, node.value, node.annotation
        else:
            return None
        loose = isinstance(target, ast.Name) and (
            strict
            or (
                not (target.id.startswith("__") and target.id.endswith("__"))
                and not cls._is_pure_reference(value)
                and not cls._is_typing_declaration(value, annotation)
            )
        )
        return target.id if loose and isinstance(target, ast.Name) else None

    @classmethod
    def _loose_members(
        cls,
        tree: ast.Module,
        *,
        values: bool,
        strict: bool = False,
    ) -> t.VariadicTuple[str]:
        """Return loose functions and value bindings in module order.

        Returns:
            Every loose member name, in source order.

        """
        names: list[str] = []
        for node in tree.body:
            if isinstance(node, c.Infra.AST_FUNCTION_TYPES):
                names.append(node.name)
            elif isinstance(node, ast.TypeAlias):
                names.append(node.name.id)
            elif (
                values
                and (name := cls._loose_value_name(node, strict=strict)) is not None
            ):
                names.append(name)
        return tuple(dict.fromkeys(names))

    @staticmethod
    def _declared_names(tree: ast.Module) -> frozenset[str]:
        """Return the names the module declares in a literal ``__all__``.

        Returns:
            The declared export names, empty without a literal declaration.

        """
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign):
                target, value = node.target, node.value
            else:
                continue
            if (
                isinstance(target, ast.Name)
                and target.id == "__all__"
                and isinstance(value, c.Infra.AST_SEQUENCE_DISPLAY_TYPES)
            ):
                return frozenset(
                    item.value
                    for item in value.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
        return frozenset()

    @staticmethod
    def _definition_time_names(node: ast.stmt) -> frozenset[str]:
        """Names a member reads while its own definition executes.

        Returns:
            The identifiers loaded by decorators, defaults and bound values.

        """
        roots: list[ast.AST] = []
        if isinstance(node, c.Infra.AST_FUNCTION_TYPES):
            roots.extend(node.decorator_list)
            roots.extend(node.args.defaults)
            roots.extend(
                default for default in node.args.kw_defaults if default is not None
            )
        elif isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES) and node.value is not None:
            roots.append(node.value)
        return frozenset(
            name.id
            for root in roots
            for name in ast.walk(root)
            if isinstance(name, ast.Name)
        )

    @classmethod
    def _movable_members(
        cls,
        tree: ast.Module,
        members: t.VariadicTuple[str],
        *,
        owner: str,
        module_name: str,
        strict: bool = False,
    ) -> p.Result[t.VariadicTuple[str]]:
        """Return the loose members the owner body can hold, in module order.

        A member that reads the owner while it is being defined (an alias of
        an owner member, a decorator or default built from it) cannot live in
        the owner's body, exactly like a class bound to the owner by
        inheritance: it stays at module level. A member the owner reads while
        ITSELF is being created (a base, or a ``metaclass=`` factory call)
        stays module level too: the owner does not exist while its creation
        expressions evaluate. Every member such a bound member references in
        its body stays module level as well, so the bound member's bare-name
        resolution keeps resolving at module scope. A function rebinding
        module state through ``global`` would lose that state as a static
        method, so it fails the plan naming the module and the member.

        Returns:
            The movable members, or a failure naming the module and member.

        """
        checked = r[t.VariadicTuple[str]]
        selected = frozenset(members)
        nodes_by_member: t.MutableMappingKV[str, ast.stmt] = {}
        for node in tree.body:
            name = (
                node.name
                if isinstance(node, c.Infra.AST_FUNCTION_TYPES)
                else cls._loose_value_name(node, strict=strict)
            )
            if name is not None and name in selected:
                nodes_by_member[name] = node
        bound: set[str] = cls._creation_bound(tree, nodes_by_member, selected, owner)
        for node in tree.body:
            name = (
                node.name
                if isinstance(node, c.Infra.AST_FUNCTION_TYPES)
                else cls._loose_value_name(node, strict=strict)
            )
            if name is None or name not in selected or name in bound:
                continue
            if owner in cls._definition_time_names(node):
                bound.add(name)
                continue
            if any(isinstance(inner, ast.Global) for inner in ast.walk(node)):
                return checked.fail(
                    f"class-nesting cannot move {module_name}.{name} under "
                    f"{owner}: it rebinds module state through global",
                )
        return checked.ok(tuple(name for name in members if name not in bound))

    @classmethod
    def _creation_bound(
        cls,
        tree: ast.Module,
        nodes_by_member: t.MappingKV[str, ast.stmt],
        selected: frozenset[str],
        owner: str,
    ) -> set[str]:
        """Members the owner creation expressions and their closure read.

        The seed binds every selected member the owner reads while being
        created (a base, or a ``metaclass=`` factory call); the closure keeps
        every member such a bound member loads, so the bound member's
        bare-name resolution keeps resolving at module scope.

        Returns:
            The members that must stay at module level.

        """
        owner_node = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == owner
            ),
            None,
        )
        bound: set[str] = set()
        if owner_node is not None:
            creation_roots: tuple[ast.AST, ...] = (
                *owner_node.decorator_list,
                *owner_node.bases,
                *owner_node.keywords,
            )
            creation_reads = frozenset(
                name.id
                for root in creation_roots
                for name in ast.walk(root)
                if isinstance(name, ast.Name)
            )
            bound.update(creation_reads & selected)
        while True:
            loaded_by_bound: set[str] = set()
            for name in bound:
                member_node = nodes_by_member.get(name)
                if member_node is not None:
                    loaded_by_bound |= cls._body_load_names(member_node)
            newly_bound = (loaded_by_bound & selected) - bound
            if not newly_bound:
                break
            bound.update(newly_bound)
        return bound

    @staticmethod
    def _body_load_names(node: ast.stmt) -> frozenset[str]:
        """Names a member's whole body loads.

        Returns:
            Every identifier read anywhere inside the member, including the
            definition-time reads (decorators, defaults, bound values).

        """
        return frozenset(
            name.id
            for name in ast.walk(node)
            if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Load)
        )

    @classmethod
    def _model_namespace_candidate(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeSourceModule,
    ) -> t.Pair[p.Infra.RopeSourceClass, t.StrTuple] | None:
        """Select an exported pure namespace, including its redundant wrapper.

        Returns:
            The native declaration and payload names eligible for use census.

        """
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            return None
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        if len(classes) != 1:
            return None
        node = classes[0]
        if node.name not in (
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                module.source_code
            )
        ):
            return None
        owner = module.get_attribute(node.name).get_object()
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        if not runtime.py_class(owner):
            return None
        names = cls._model_namespace_payloads(project, owner)
        if names:
            return owner, names
        return cls._model_namespace_wrapped_candidate(project, owner, node)

    @classmethod
    def _model_namespace_wrapped_candidate(
        cls,
        project: p.Infra.RopeProject,
        owner: p.Infra.RopeSourceClass,
        node: ast.ClassDef,
    ) -> t.Pair[p.Infra.RopeSourceClass, t.StrTuple] | None:
        """Admit only a transparent holder around the same pure namespace.

        Returns:
            The native nested namespace, or refusal for nontransparent holders.

        """
        if node.bases or node.keywords or node.decorator_list or node.type_params:
            return None
        children = owner.get_scope().get_scopes()
        if len(children) != 1 or set(owner.get_scope().get_defined_names()) != {
            node.name
        }:
            return None
        child = children[0].pyobject
        if (
            not FlextInfraUtilitiesRopeRuntimeTypes.py_class(child)
            or child.get_name() != node.name
        ):
            return None
        names = cls._model_namespace_payloads(project, child)
        return (child, names) if names else None

    @staticmethod
    def _model_namespace_payloads(
        project: p.Infra.RopeProject,
        owner: p.Infra.RopePyObject,
    ) -> t.StrTuple:
        """Prove a fieldless payload namespace at its native preset boundary.

        Returns:
            Nested model names, or no admission for an entity or custom base.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        if not runtime.py_class(owner):
            return ()
        node = owner.get_ast()
        if not isinstance(node, ast.ClassDef) or (
            node.decorator_list or node.keywords or node.type_params
        ):
            return ()
        children = tuple(
            member for member in node.body if isinstance(member, ast.ClassDef)
        )
        if not children or any(
            not isinstance(member, ast.ClassDef | ast.Pass)
            and not (
                isinstance(member, ast.Expr)
                and isinstance(member.value, ast.Constant)
                and isinstance(member.value.value, str)
            )
            for member in node.body
        ):
            return ()
        payloads = FlextInfraUtilitiesDeclarationPayload
        bases = tuple(payloads.direct_bases(owner))
        if len(bases) != 1:
            return ()
        preset = payloads.qualified_name(
            project, "flext_core.m.ArbitraryTypesModel"
        ).get_object()
        if bases != (preset,):
            return ()
        model = payloads.identity_name(
            project, c.Infra.PYDANTIC_MODEL_IDENTITY
        ).get_object()
        return (
            tuple(child.name for child in children)
            if all(
                model in payloads.class_ancestry(
                    owner.get_attribute(child.name).get_object()
                )
                for child in children
            )
            else ()
        )

    @classmethod
    def _singleton_model_namespace(
        cls,
        project: p.Infra.RopeProject,
        file_path: Path,
        classes: t.MappingKV[str, ast.ClassDef],
    ) -> t.StrMapping:
        """Wrap an exported singleton model without renaming its entity.

        Returns:
            The existing nesting mapping, or no move for a namespace holder.

        Raises:
            TypeError: If Singleton model owner requires a native source module.
            ValueError: A pure model namespace still has actual entity consumers.

        """
        if (
            len(classes) != 1
            or FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                file_path.parent.name
            )
            != c.Infra.FacadeFamily.M
        ):
            return {}
        name = next(iter(classes))
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                file_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = (
                f"Singleton model owner requires a native source module: {file_path}"
            )
            raise TypeError(message)
        if (
            name
            not in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                module.source_code
            )
        ):
            return {}
        payloads = FlextInfraUtilitiesDeclarationPayload
        model = payloads.identity_name(project, c.Infra.PYDANTIC_MODEL_IDENTITY)
        owner = module.get_attribute(name).get_object()
        if cls._model_namespace_payloads(project, owner):
            message = (
                "Fieldless model namespace has entity consumers; "
                f"native namespace normalization was refused: {file_path}:{name}"
            )
            raise ValueError(message)
        ancestry = payloads.class_ancestry(owner)
        parents = tuple(
            (item.get_module().get_name(), item.get_name())
            for item in ancestry[:8]
            if FlextInfraUtilitiesRopeRuntimeTypes.py_class(item)
        )
        u.Cli.info(
            f"  stage=singleton-model-detection module={module.get_name()} "
            f"owner={name} native_model={model.get_object() in ancestry} "
            f"model_config={c.Infra.MODEL_CONFIG_ATTRIBUTE in owner.get_attributes()} "
            f"ancestry={parents}"
        )
        return (
            {name: name}
            if model.get_object() in ancestry
            else {}
        )

    @classmethod
    def _module_owner(
        cls,
        convention: m.Infra.RopeModuleConvention,
        file_path: Path,
        classes: t.MappingKV[str, ast.ClassDef],
        exports: frozenset[str],
    ) -> p.Result[str]:
        """Return the semantic owner, or derive one from the module convention.

        Returns:
            The owner class name, or a failure when the derivation is ambiguous.

        """
        derived = r[str]
        policy = convention.module_policy
        namespace = FlextInfraUtilitiesCodegenNamespace
        families = namespace.facade_families()
        directory_family = namespace.facade_family_of_directory(file_path.parent.name)
        file_family = namespace.facade_family_of_file(file_path.name)
        if directory_family is None and file_family is None:
            return cls._ordinary_module_owner(convention, file_path, classes, exports)
        if directory_family is not None:
            suffix_root = families[directory_family].suffix
            suffix = suffix_root + u.derive_class_stem(file_path.stem.strip("_"))
        elif file_family is not None:
            suffix_root = suffix = families[file_family].suffix
        else:
            return derived.fail(
                f"class-nesting found no facade family for {convention.module_name}",
            )
        prefix = policy.project_prefix
        if not prefix:
            return derived.fail(
                "class-nesting cannot derive a module owner without a project "
                f"class stem for {convention.module_name}",
            )
        family_prefix = f"{prefix}{suffix_root}"
        declared = policy.expected_family
        # The declared owner is the published facade class, or a class the
        # module declares that carries the family name; a record or sentinel
        # the module happens to export alone is never the module's owner.
        if (
            declared is not None
            and declared in classes
            and (
                policy.expected_alias is not None or declared.startswith(family_prefix)
            )
        ):
            return derived.ok(declared)
        owner = f"{prefix}{suffix}"
        if owner in classes:
            return derived.ok(owner)
        # A rival is a class the module itself publishes as a family owner:
        # declared in ``__all__`` and named by the project stem plus the family
        # suffix. Any other class (a record, a sentinel, an unpublished
        # helper) is a member, whatever its name.
        rivals = sorted(
            name
            for name in classes
            if name.startswith(family_prefix) and name in exports
        )
        return (
            derived.fail(
                "class-nesting requires exactly one declared module owner for "
                f"{convention.module_name}; discovered: {', '.join(rivals)} "
                f"(derived owner {owner})",
            )
            if rivals
            else derived.ok(owner)
        )

    @staticmethod
    def _ordinary_module_owner(
        convention: m.Infra.RopeModuleConvention,
        file_path: Path,
        classes: t.MappingKV[str, ast.ClassDef],
        exports: frozenset[str],
    ) -> p.Result[str]:
        derived = r[str]
        policy = convention.module_policy
        owner = policy.expected_family
        if owner is not None and owner in classes:
            return derived.ok(owner)
        owner = policy.project_prefix + u.derive_class_stem(
            file_path.stem.strip("_")
            if policy.project_prefix
            else convention.module_name,
        )
        if owner in classes or len(classes) == 1:
            return derived.ok(owner if owner in classes else next(iter(classes)))
        candidates = sorted(name for name in classes if name in exports)
        if not candidates:
            candidates = sorted(name for name in classes if not name.startswith("_"))
        if len(candidates) == 1:
            return derived.ok(candidates[0])
        if candidates:
            return derived.fail(
                "class-nesting requires exactly one declared module owner for "
                f"{convention.module_name}; discovered: {', '.join(candidates)}",
            )
        if not owner.isidentifier():
            return derived.fail(
                "class-nesting cannot derive a valid owner for "
                f"{convention.module_name}",
            )
        return derived.ok(owner)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingOwner"]
