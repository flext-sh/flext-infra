"""Automatic class-nesting plans derived from the public Rope workspace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import traceback
from collections.abc import MutableMapping
from difflib import SequenceMatcher
from fnmatch import fnmatch
from pathlib import Path

import libcst as cst

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverClassScope,
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
    FlextInfraUtilitiesSemanticFamilyFlatten,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities._semantic_cutover.test_helpers import (
    FlextInfraUtilitiesSemanticTestHelpers,
)


class FlextInfraUtilitiesSemanticCutoverNesting(
    FlextInfraUtilitiesSemanticTestHelpers,
    FlextInfraUtilitiesSemanticFamilyFlatten,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverClassScope,
):
    """Plan class nesting from semantic module ownership instead of record lists."""

    @staticmethod
    def _inheritance_bound_to_owner(
        classes: t.MappingKV[str, ast.ClassDef],
        owner_name: str,
    ) -> frozenset[str]:
        """Return top-level classes an owner cannot contain.

        Nesting is a definition-time move, so it fails in both directions of an
        inheritance edge. A class that inherits from the owner cannot live in
        the owner's body, because a class body cannot reference the class being
        defined around it. An owner that inherits from the class cannot contain
        it either, because the owner's base list is evaluated before its body
        exists. Either move produces a NameError at import, so both are excluded
        from the plan and stay at module level.

        Returns:
            Top-level classes an owner cannot contain.

        """

        def ancestors(name: str) -> frozenset[str]:
            found: set[str] = set()
            pending = [name]
            while pending:
                for base in classes[pending.pop()].bases:
                    current: ast.expr = base
                    while isinstance(current, ast.Attribute):
                        current = current.value
                    if (
                        isinstance(current, ast.Name)
                        and current.id in classes
                        and current.id not in found
                    ):
                        found.add(current.id)
                        pending.append(current.id)
            return frozenset(found)

        return ancestors(owner_name) | {
            name for name in classes if owner_name in ancestors(name)
        }

    @classmethod
    def _suite_reference_pins(
        cls,
        tree: ast.Module,
        classes: t.MappingKV[str, ast.ClassDef],
        movable: frozenset[str],
        owner: str,
    ) -> frozenset[str]:
        """Return classes that must stay at module level to keep suite lookups.

        A nested class suite looks names up in the module globals. The owner
        name is not bound until its class statement finishes, so neither the
        bare sibling nor ``Owner.Sibling`` resolves during that suite. A base
        in the class header does see the enclosing scope. An immediate load
        from a class that is moving, or from a class already nested in the
        owner, keeps its target at module level. A class that stays outside
        also keeps the bases it names there: qualifying those bases through
        the owner fails when the owner statement has not run yet.

        Returns:
            The movable classes pinned by an immediate suite reference.

        """
        pinned = cls._pins_from_suite_loads(tree, movable, owner)
        return cls._pins_from_outside_bases(classes, movable, pinned)

    @classmethod
    def _pins_from_suite_loads(
        cls,
        tree: ast.Module,
        movable: frozenset[str],
        owner: str,
    ) -> set[str]:
        """Return classes pinned because a suite loads them immediately.

        Returns:
            The movable classes named by an immediate suite load.

        """
        pinned: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name == owner:
                continue
            for statement in node.body:
                referenced = set(cls._immediate_suite_loads(statement) & movable)
                referenced.discard(node.name)
                if not referenced:
                    continue
                if node.name in movable:
                    pinned.add(node.name)
                pinned.update(referenced)
        return pinned

    @staticmethod
    def _pins_from_outside_bases(
        classes: t.MappingKV[str, ast.ClassDef],
        movable: frozenset[str],
        pinned: set[str],
    ) -> frozenset[str]:
        """Pin bases of classes that stay at module level.

        Returns:
            ``pinned`` plus every movable base those classes name.

        """
        changed = True
        while changed:
            changed = False
            for name, node in classes.items():
                if name in movable and name not in pinned:
                    continue
                for base in node.bases:
                    current: ast.expr = base
                    while isinstance(current, ast.Attribute):
                        current = current.value
                    if (
                        isinstance(current, ast.Name)
                        and current.id in movable
                        and current.id not in pinned
                    ):
                        pinned.add(current.id)
                        changed = True
        return frozenset(pinned)

    @classmethod
    def _canonical_module_bindings(
        cls,
        project: p.Infra.RopeProject,
        file_path: Path,
        tree: ast.Module,
        policy: m.Infra.NamespaceModulePolicy,
    ) -> frozenset[str]:
        """Preserve policy-owned native aliases and Python's export protocol."""
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                file_path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            file_path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        attributes = module.get_attributes()
        exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            module.source_code,
        )
        aliases: set[str] = set()
        singleton = FlextInfraUtilitiesCodegenNamespace.runtime_singleton_export(
            file_path.name
        )
        for node in tree.body:
            target, value = (
                FlextInfraUtilitiesPrivateImportFacades._assigned_target_value(node)
            )
            if not isinstance(target, ast.Name) or value is None:
                continue
            if target.id == "__all__":
                if not isinstance(value, ast.List | ast.Tuple) or any(
                    not isinstance(item, ast.Constant)
                    or not isinstance(item.value, str)
                    or item.value not in attributes
                    for item in value.elts
                ):
                    msg = f"unresolved native module export declaration: {module.get_name()}"
                    raise ValueError(msg)
                aliases.add(target.id)
                continue
            if target.id not in {policy.expected_alias, singleton}:
                continue
            declared = FlextInfraUtilitiesPrivateImportFacades._facade_class_name(value)
            name = attributes.get(declared) if declared is not None else None
            binding = attributes.get(target.id)
            if (
                name is None
                or binding is None
                or not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(
                    name.get_object()
                )
                or target.id not in exports
                or (
                    policy.expected_family is not None
                    and declared != policy.expected_family
                )
            ):
                msg = (
                    f"unproven canonical module alias: {module.get_name()}.{target.id}"
                )
                raise ValueError(msg)
            native = binding.get_object()
            if native is name.get_object():
                aliases.add(target.id)
                continue
            annotation = (
                runtime.expression_name(
                    module.get_scope(), ast.unparse(node.annotation)
                )
                if isinstance(node, ast.AnnAssign)
                else None
            )
            if (
                runtime.same_name(name, annotation)
                and native.get_type() is name.get_object()
            ):
                aliases.add(target.id)
                continue
            msg = f"invalid native canonical singleton: {module.get_name()}.{target.id}"
            raise ValueError(msg)
        return frozenset(aliases)

    @staticmethod
    def _is_pytest_module(
        project: p.Infra.RopeProject,
        file_path: Path,
        tree: ast.Module,
        patterns: t.Triple[t.StrTuple, t.StrTuple, t.StrTuple],
    ) -> bool:
        """Use native collection configuration or real pytest decorator identity."""
        if file_path.name == "conftest.py" or any(
            fnmatch(file_path.name, pattern) for pattern in patterns[0]
        ):
            return True
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            file_path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for decorator in node.decorator_list:
                expression = (
                    decorator.func if isinstance(decorator, ast.Call) else decorator
                )
                scope = runtime.scope_at(
                    module, runtime.source_offset(module.source_code, decorator)
                )
                actual = runtime.expression_name(scope, ast.unparse(expression))
                owner = actual.get_object().get_module() if actual is not None else None
                if owner is None or owner.get_name().partition(".")[0] not in {
                    "pytest",
                    "_pytest",
                }:
                    continue
                pytest_module = (
                    FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                        project.get_module("pytest"),
                    )
                )
                if any(
                    runtime.same_name(pytest_module.get_attribute(name), actual)
                    for name in ("fixture", "hookimpl")
                ):
                    return True
        return False

    @classmethod
    def _canonical_main_guard(
        cls,
        project: p.Infra.RopeProject,
        file_path: Path,
        tree: ast.Module,
        statement: ast.stmt,
    ) -> bool:
        """Keep the standard executable guard, never conditional declarations."""
        if not isinstance(statement, ast.If) or statement.orelse:
            return False
        test = statement.test
        if not (
            isinstance(test, ast.Compare)
            and len(test.ops) == len(test.comparators) == 1
            and isinstance(test.ops[0], ast.Eq)
        ):
            return False
        left, right = test.left, test.comparators[0]
        if not (
            isinstance(left, ast.Name)
            and left.id == "__name__"
            and isinstance(right, ast.Constant)
            and right.value == "__main__"
        ) or any("__name__" in cls._scope_bindings(node) for node in tree.body):
            return False
        if len(statement.body) != 1:
            return False
        body = statement.body[0]
        if any(
            isinstance(
                node,
                ast.NamedExpr | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
            )
            for node in ast.walk(body)
        ):
            return False
        call = (
            body.value
            if isinstance(body, ast.Expr)
            else body.exc
            if isinstance(body, ast.Raise)
            else None
        )
        if not isinstance(call, ast.Call):
            return False
        resource = project.get_resource(
            file_path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if isinstance(body, ast.Raise):
            actual = runtime.expression_name(module.get_scope(), ast.unparse(call.func))
            builtin = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module("builtins")
            )
            if (
                not runtime.same_name(builtin.get_attribute("SystemExit"), actual)
                or len(call.args) != 1
                or call.keywords
            ):
                return False
            call = call.args[0]
        if not isinstance(call, ast.Call):
            return False
        target = runtime.expression_name(module.get_scope(), ast.unparse(call.func))
        if target is None:
            return False
        holder, _line = target.get_definition_location()
        return holder is module and FlextInfraUtilitiesRopeRuntimeTypes.py_function(
            target.get_object()
        )

    @staticmethod
    def _module_declaration_entities(
        project: p.Infra.RopeProject,
        file_path: Path,
        classes: t.MappingKV[str, ast.ClassDef],
    ) -> frozenset[str]:
        """Use declaration-relocation's native payload/protocol role identities."""
        payloads = FlextInfraUtilitiesDeclarationPayload
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                file_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        entities: set[str] = set()
        for name in classes:
            target = module.get_attribute(name).get_object()
            ancestry = payloads.class_ancestry(target)
            if any(
                base.get_module() is not None
                and base.get_module().get_name().partition(".")[0] == "pydantic"
                for base in ancestry
            ):
                model = payloads.identity_name(project, c.Infra.PYDANTIC_MODEL_IDENTITY)
                if model is not None and model.get_object() in ancestry:
                    entities.add(name)
            if (
                payloads.protocol_declaration(
                    project,
                    file_path,
                    f"{module.get_name()}.{name}",
                )
                is not None
            ):
                entities.add(name)
        return frozenset(entities)

    @classmethod
    def _canonical_metadata_rebind(
        cls,
        project: p.Infra.RopeProject,
        file_path: Path,
        tree: ast.Module,
        node: ast.stmt,
    ) -> bool:
        """Admit Python class provenance metadata only on its native local owner."""
        target, value = FlextInfraUtilitiesPrivateImportFacades._assigned_target_value(
            node
        )
        if not isinstance(target, ast.Attribute) or target.attr != "__module__":
            return False
        if not (
            (isinstance(value, ast.Constant) and isinstance(value.value, str))
            or (
                isinstance(value, ast.Name)
                and value.id == "__name__"
                and not any(
                    "__name__" in cls._scope_bindings(item) for item in tree.body
                )
            )
        ):
            return False
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                file_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            module.get_scope(),
            ast.unparse(target.value),
        )
        return binding is not None and (
            FlextInfraUtilitiesRopeRuntimeTypes.py_class(binding.get_object())
            and binding.get_object().get_module() is module
        )

    @classmethod
    def _class_nesting_definitions(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject,
        pytest_patterns: t.Triple[t.StrTuple, t.StrTuple, t.StrTuple],
    ) -> p.Result[t.StrMapping]:
        """Map each loose top-level class to the owner Rope's module policy elects.

        Returns:
            The resulting ``p.Result[t.StrMapping]``.

        """
        planned = r[t.StrMapping]
        convention = rope_workspace.convention(file_path)
        if file_path.name == c.Infra.INIT_PY:
            return planned.ok({})
        tree = ast.parse(source, filename=str(file_path))
        classes = {
            node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
        }
        test_module = any(
            fnmatch(file_path.name, pattern) for pattern in pytest_patterns[0]
        )
        canonical = cls._canonical_module_bindings(
            project,
            file_path,
            tree,
            convention.module_policy,
        )
        # Full syntactic collection precedes native canonical admission everywhere.
        loose = cls._loose_members(tree, values=True, strict=True)
        loose = tuple(name for name in loose if name not in canonical)
        unsupported = tuple(
            f"{type(node).__name__}@{node.lineno}"
            for node in tree.body
            if not isinstance(
                node,
                ast.Import
                | ast.ImportFrom
                | ast.ClassDef
                | ast.FunctionDef
                | ast.AsyncFunctionDef
                | ast.Assign
                | ast.AnnAssign
                | ast.TypeAlias,
            )
            and not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            and not cls._type_checking_import_block(node, tree)
            and not cls._canonical_main_guard(project, file_path, tree, node)
        )
        if unsupported:
            return planned.fail(
                f"owned module {convention.module_name} has unsupported "
                f"module statements: {', '.join(unsupported)}",
            )
        unowned = tuple(
            f"{type(node).__name__}@{node.lineno}"
            for node in tree.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and cls._loose_value_name(node, strict=True) is None
            and not cls._canonical_metadata_rebind(project, file_path, tree, node)
        )
        if unowned:
            return planned.fail(
                f"owned module {convention.module_name} requires a single "
                f"owned assignment target: {', '.join(unowned)}",
            )
        composition = (test_module or file_path.name == "conftest.py") and (
            len(classes) != 1 or bool(loose)
        )
        if len(classes) <= 1 and not loose and not composition:
            return planned.ok({})
        registered_decorators = {"fixture", "hookimpl"} | {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "pytest"
            for alias in node.names
            if alias.name in {"fixture", "hookimpl"}
        }
        entities = cls._module_declaration_entities(project, file_path, classes)
        if entities:
            return planned.fail(
                f"class-nesting requires canonical declaration relocation before "
                f"electing a namespace in {convention.module_name}: "
                f"{', '.join(sorted(entities))}; data/protocol entities cannot own utility behavior",
            )
        family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
            file_path.name,
        ) or FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
            file_path.parent.name,
        )
        utility_family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
            c.Infra.UTILITIES_PY
        )
        if (
            family is not None
            and family != utility_family
            and any(
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node.name in loose
                for node in tree.body
            )
        ):
            return planned.fail(
                f"class-nesting requires utility-owner relocation for behavior in "
                f"declaration family {convention.module_name}",
            )
        owned = (
            cls._test_module_owner(
                convention,
                file_path,
                classes,
                pytest_patterns[1],
                pytest_patterns[2],
                require_collection=test_module,
                composition=composition,
            )
            if test_module or file_path.name == "conftest.py"
            else cls._module_owner(
                convention,
                file_path,
                classes,
                cls._declared_names(tree),
            )
        )
        if owned.failure:
            return planned.from_failure(owned)
        owner = owned.value
        suite = classes.get(owner)
        if (
            test_module
            and suite is not None
            and any(
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and cls._pytest_name_matches(node.name, pytest_patterns[2])
                for node in tree.body
            )
            and (
                suite.bases
                or suite.keywords
                or suite.decorator_list
                or any(
                    any(
                        name in {"__test__", "pytestmark"}
                        for name in cls._scope_bindings(node)
                    )
                    or (
                        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                        and (
                            node.name
                            in {
                                "__init__",
                                "__new__",
                                "setup_class",
                                "teardown_class",
                                "setup_method",
                                "teardown_method",
                            }
                            or any(
                                cls._tail_name(
                                    decorator.func
                                    if isinstance(decorator, ast.Call)
                                    else decorator
                                )
                                in registered_decorators
                                for decorator in node.decorator_list
                            )
                        )
                    )
                    for node in suite.body
                )
            )
        ):
            return planned.fail(
                f"class-nesting cannot add free tests to {convention.module_name}.{owner}: "
                "existing suite registration or lifecycle would change",
            )
        if owner not in classes and any(
            owner in cls._scope_bindings(node) for node in tree.body
        ):
            return planned.fail(
                f"class-nesting owner {owner} collides with a module binding in "
                f"{convention.module_name}",
            )
        movable = cls._movable_members(
            tree,
            loose,
            owner=owner,
            module_name=convention.module_name,
            strict=True,
        )
        if movable.failure:
            return planned.from_failure(movable)
        bound: frozenset[str] = (
            cls._inheritance_bound_to_owner(classes, owner)
            if owner in classes
            else frozenset()
        )
        definitions = {
            name: owner for name in classes if name != owner and name not in bound
        }
        definitions.update((name, owner) for name in movable.value)
        pinned = cls._suite_reference_pins(
            tree,
            classes,
            frozenset(definitions),
            owner,
        )
        blocked = bound | pinned | (frozenset(loose) - frozenset(movable.value))
        if blocked:
            return planned.fail(
                f"class-nesting cannot safely nest {convention.module_name} under "
                f"{owner}: definition-time dependencies pin "
                f"{', '.join(sorted(blocked))}",
            )
        owner_node = classes.get(owner)
        occupied = (
            frozenset(
                name for node in owner_node.body for name in cls._scope_bindings(node)
            )
            if owner_node is not None
            else frozenset()
        )
        collisions = occupied & definitions.keys()
        if collisions:
            return planned.fail(
                f"class-nesting owner {owner} already defines "
                f"{', '.join(sorted(collisions))} in {convention.module_name}",
            )
        return planned.ok({
            name: owner for name, owner in definitions.items() if name not in pinned
        })

    @classmethod
    def _type_checking_import_block(cls, node: ast.stmt, tree: ast.Module) -> bool:
        """Admit only an imported typing.TYPE_CHECKING guard containing imports."""
        if not isinstance(node, ast.If) or node.orelse or not node.body:
            return False
        if not all(isinstance(item, ast.Import | ast.ImportFrom) for item in node.body):
            return False
        guarded_name = (
            node.test.id
            if isinstance(node.test, ast.Name)
            else node.test.value.id
            if isinstance(node.test, ast.Attribute)
            and isinstance(node.test.value, ast.Name)
            else None
        )
        if guarded_name is None or any(
            guarded_name in cls._scope_bindings(statement)
            for statement in tree.body
            if statement is not node
            and not isinstance(statement, ast.Import | ast.ImportFrom)
        ):
            return False
        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom) and statement.module == "typing":
                if any(
                    alias.name == "TYPE_CHECKING"
                    and isinstance(node.test, ast.Name)
                    and node.test.id == (alias.asname or alias.name)
                    for alias in statement.names
                ):
                    return True
            if isinstance(statement, ast.Import) and any(
                alias.name == "typing"
                and isinstance(node.test, ast.Attribute)
                and node.test.attr == "TYPE_CHECKING"
                and isinstance(node.test.value, ast.Name)
                and node.test.value.id == (alias.asname or alias.name)
                for alias in statement.names
            ):
                return True
        return False

    @classmethod
    def _test_prefix_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Rename every local test class through native Rope, including local scopes."""
        working = dict(sources)
        patterns = cls._pytest_collection_patterns(
            Path(workspace.rope_project.root.real_path)
        )
        for path, _source in cls._editable_sources(sources):
            if not path.is_relative_to(Path(workspace.repository_root).resolve()):
                continue
            if path.name == c.Infra.INIT_PY or not (
                path.name == "conftest.py"
                or any(fnmatch(path.name, pattern) for pattern in patterns[0])
            ):
                continue
            prefix = workspace.convention(path).module_policy.project_prefix
            if not prefix.startswith("Tests"):
                prefix = f"Tests{prefix}"
            while True:
                previous_source = working[path]
                tree = ast.parse(previous_source)
                declaration = next(
                    (
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, ast.ClassDef)
                        and not node.name.startswith(prefix)
                    ),
                    None,
                )
                if declaration is None:
                    break
                replacement = prefix + declaration.name.removeprefix(
                    "Tests"
                ).removeprefix("Test").lstrip("_")
                if (
                    any(fnmatch(path.name, pattern) for pattern in patterns[0])
                    and not cls._pytest_name_matches(declaration.name, patterns[1])
                    and cls._pytest_name_matches(replacement, patterns[1])
                    and cls._new_suite_collection_risk(tree, declaration, patterns[2])
                ):
                    msg = (
                        f"test class prefix rename would newly collect helper {path}:{declaration.name}; "
                        "an explicit class-owned non-suite lifecycle contract is required"
                    )
                    raise ValueError(msg)
                project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    workspace.rope_project,
                    working,
                )
                try:
                    root = Path(project.root.real_path)
                    resource = project.get_resource(path.relative_to(root).as_posix())
                    module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                        project, resource
                    )
                    pending = [module.get_scope()]
                    defining: p.Infra.RopeScope | None = None
                    while pending:
                        scope = pending.pop()
                        if (
                            scope.get_kind() == "Class"
                            and scope.pyobject.get_name() == declaration.name
                            and scope.get_start() == declaration.lineno
                        ):
                            defining = scope.parent
                            break
                        pending.extend(scope.get_scopes())
                    if defining is None:
                        msg = f"test class has no unique native defining scope: {path}:{declaration.name}"
                        raise ValueError(msg)
                    # Rope's scope ``__getitem__`` raises for absent names; the
                    # native defined-name contract decides presence first.
                    # ``get_names`` lazily fills function-scope locals, which
                    # ``get_defined_names`` reports empty.
                    defined = defining.get_names()
                    expected = defined.get(declaration.name)
                    if expected is None:
                        msg = f"test class has no native defining binding: {path}:{declaration.name}"
                        raise ValueError(msg)
                    if replacement in defined:
                        msg = f"test class prefix rename collides: {path}:{replacement}"
                        raise ValueError(msg)
                    offset = (
                        FlextInfraUtilitiesRopeCore.find_identifier_offset_in_lines(
                            working[path].splitlines(keepends=True),
                            line=declaration.lineno,
                            symbol=declaration.name,
                            pyname=expected,
                        )
                    )
                    if offset is None:
                        msg = f"test class has no native identifier: {path}:{declaration.name}"
                        raise ValueError(msg)
                    changes = FlextInfraUtilitiesRopeRuntimeRefactors.rename_changes(
                        project,
                        resource,
                        offset,
                        replacement,
                        options=m.Infra.RopeRenameOptions(
                            resources=tuple(
                                project.get_resource(item.relative_to(root).as_posix())
                                for item in working
                            ),
                            in_hierarchy=True,
                        ),
                    )
                    rewrites: MutableMapping[Path, list[m.Infra.SourceRewrite]] = {}
                    for change in changes.changes:
                        if not isinstance(change, p.Infra.RopeChangeContents):
                            msg = "test class rename produced a non-content effect"
                            raise TypeError(msg)
                        consumer = Path(change.resource.real_path).resolve()
                        if consumer not in working:
                            msg = f"test class rename escaped source inventory: {consumer}"
                            raise ValueError(msg)
                        rewrites[consumer] = [
                            m.Infra.SourceRewrite(
                                start=begin,
                                end=end,
                                text=change.new_contents[first:last],
                            )
                            for kind, begin, end, first, last in SequenceMatcher(
                                a=working[consumer],
                                b=change.new_contents,
                                autojunk=False,
                            ).get_opcodes()
                            if kind != "equal"
                        ]

                    def quoted_replacement(
                        current: p.Infra.RopeScope, expression: str
                    ) -> str | None:
                        parts = expression.split(".")
                        for count in range(1, len(parts) + 1):
                            actual = (
                                FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                                    current, ".".join(parts[:count])
                                )
                            )
                            if (
                                parts[count - 1] == declaration.name
                                and FlextInfraUtilitiesRopeRuntimeModules.same_name(
                                    expected, actual
                                )
                            ):
                                return ".".join((
                                    *parts[: count - 1],
                                    replacement,
                                    *parts[count:],
                                ))
                        return None

                    for consumer, text in working.items():
                        candidate = project.get_resource(
                            consumer.relative_to(root).as_posix()
                        )
                        quotes = cls._quoted_type_edits(
                            project, candidate, text, quoted_replacement
                        )
                        if quotes:
                            rewrites.setdefault(consumer, []).extend(quotes)
                    exports = cls._test_export_rename_edits(
                        project,
                        resource,
                        offset,
                        replacement,
                        working,
                    )
                    for consumer, edits in exports.items():
                        rewrites.setdefault(consumer, []).extend(edits)
                    changed = False
                    for consumer, edits in rewrites.items():
                        candidate = project.get_resource(
                            consumer.relative_to(root).as_posix()
                        )
                        updated = (
                            FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                                candidate, working[consumer], edits
                            ).new_contents
                        )
                        changed |= working[consumer] != updated
                        working[consumer] = updated
                    if not changed or working[path] == previous_source:
                        msg = f"native test class rename made no progress: {path}"
                        raise ValueError(msg)
                finally:
                    project.close()
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=source,
                updated_source=working[path],
                changes=("native Rope test class prefix cutover",),
            )
            for path, source in sources.items()
            if working[path] != source
        )

    @classmethod
    def _new_suite_collection_risk(
        cls,
        tree: ast.Module,
        declaration: ast.ClassDef,
        function_patterns: t.StrSequence,
    ) -> bool:
        """Do not turn helper constructors, protocols or inherited tests into suites."""
        if any(
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda)
            and declaration in ast.walk(node)
            for node in ast.walk(tree)
        ):
            return False
        if any(
            isinstance(member, ast.Assign | ast.AnnAssign)
            and isinstance(member.value, ast.Constant)
            and member.value.value is False
            and any(
                isinstance(target, ast.Name) and target.id == "__test__"
                for target in (
                    member.targets
                    if isinstance(member, ast.Assign)
                    else [member.target]
                )
            )
            for member in declaration.body
        ):
            return False
        return bool(declaration.bases or declaration.decorator_list) or any(
            isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
            and (
                member.name in {"__init__", "__new__"}
                or cls._pytest_name_matches(member.name, function_patterns)
            )
            for member in declaration.body
        )

    @classmethod
    def _test_export_rename_edits(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        offset: int,
        replacement: str,
        sources: t.MappingKV[Path, str],
    ) -> t.MappingKV[Path, t.VariadicTuple[m.Infra.SourceRewrite]]:
        """Retain native string renames only inside declared export literals."""
        root = Path(project.root.real_path)
        changes = FlextInfraUtilitiesRopeRuntimeRefactors.rename_changes(
            project,
            resource,
            offset,
            replacement,
            options=m.Infra.RopeRenameOptions(
                resources=tuple(
                    project.get_resource(path.relative_to(root).as_posix())
                    for path in sources
                ),
                in_hierarchy=True,
                docs=True,
            ),
        )
        planned: dict[Path, t.VariadicTuple[m.Infra.SourceRewrite]] = {}
        for change in changes.changes:
            if not isinstance(change, p.Infra.RopeChangeContents):
                msg = "native export rename produced a non-content effect"
                raise TypeError(msg)
            path = Path(change.resource.real_path).resolve()
            if path not in sources:
                msg = f"native export rename escaped source inventory: {path}"
                raise ValueError(msg)
            source = sources[path]
            exports = tuple(
                item
                for item in FlextInfraUtilitiesRopeStructure.logical_statements(source)
                if cls._native_member_name(item) == "__all__"
            )
            regions = tuple(
                (begin, end)
                for begin, end, _kind in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(
                    source
                )
                if FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(
                    source[begin:end]
                )
                is not None
                and any(
                    item.start_offset <= begin < end <= item.end_offset + 1
                    for item in exports
                )
            )
            edits = tuple(
                m.Infra.SourceRewrite(
                    start=begin, end=end, text=change.new_contents[first:last]
                )
                for kind, begin, end, first, last in SequenceMatcher(
                    a=source,
                    b=change.new_contents,
                    autojunk=False,
                ).get_opcodes()
                if kind != "equal"
                and any(start <= begin <= end <= stop for start, stop in regions)
            )
            if edits:
                planned[path] = edits
        return planned

    @classmethod
    def _plan_class_nesting(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose helper promotion, family flattening, and orphan nesting.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        planned = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        # The planner contract keeps every failure in the Result (see
        # plan_semantic_cutover); helper promotion raises per rejected move.
        # A promotion ValueError IS the rejected move's loud contract (one
        # utilities facade, unshadowed destination, unchanged bindings), so it
        # propagates instead of demoting to a Result the caller would retry.
        promotion = planned.create_from_callable(
            lambda: cls._test_helper_edits(rope_workspace, sources),
        )
        if promotion.failure:
            error = promotion.exception
            if isinstance(error, ValueError):
                raise error
            return promotion
        promoted = promotion.value
        proposed = dict(sources)
        merged = {edit.file_path: edit for edit in promoted}
        for edit in promoted:
            proposed[edit.file_path] = edit.updated_source
        consolidated = cls._facade_namespace_edits(rope_workspace, proposed)
        for edit in consolidated:
            proposed[edit.file_path] = edit.updated_source
        flattened = cls._family_flatten_edits(rope_workspace, proposed)
        for edit in flattened:
            proposed[edit.file_path] = edit.updated_source
        nested = cls._plan_orphan_nesting(rope_workspace, proposed)
        if nested.failure:
            return planned.from_failure(nested)
        for edit in (*consolidated, *flattened, *nested.value):
            previous = merged.get(edit.file_path)
            merged[edit.file_path] = m.Infra.SemanticMigrationEdit(
                file_path=edit.file_path,
                original_source=(
                    previous.original_source if previous else edit.original_source
                ),
                updated_source=edit.updated_source,
                changes=(*previous.changes, *edit.changes)
                if previous
                else edit.changes,
            )
            proposed[edit.file_path] = edit.updated_source
        for edit in cls._test_prefix_edits(rope_workspace, proposed):
            previous = merged.get(edit.file_path)
            merged[edit.file_path] = m.Infra.SemanticMigrationEdit(
                file_path=edit.file_path,
                original_source=previous.original_source
                if previous
                else edit.original_source,
                updated_source=edit.updated_source,
                changes=(*previous.changes, *edit.changes)
                if previous
                else edit.changes,
            )
            proposed[edit.file_path] = edit.updated_source
        for edit in cls._test_registration_edits(rope_workspace, proposed):
            previous = merged.get(edit.file_path)
            merged[edit.file_path] = m.Infra.SemanticMigrationEdit(
                file_path=edit.file_path,
                original_source=previous.original_source
                if previous
                else edit.original_source,
                updated_source=edit.updated_source,
                changes=(*previous.changes, *edit.changes)
                if previous
                else edit.changes,
            )
        return planned.ok(tuple(merged[path] for path in sorted(merged)))

    @classmethod
    def _test_registration_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Publish already class-owned plugins as well as newly nested declarations."""
        edits: list[m.Infra.SemanticMigrationEdit] = []
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project, sources
        )
        try:
            root = Path(project.root.real_path)
            pytest_patterns = cls._pytest_collection_patterns(root)
            for path, source in cls._editable_sources(sources):
                if not path.is_relative_to(Path(workspace.repository_root).resolve()):
                    continue
                tree = ast.parse(source)
                if path.name == c.Infra.INIT_PY or not cls._is_pytest_module(
                    project,
                    path,
                    tree,
                    pytest_patterns,
                ):
                    continue
                owners = [node for node in tree.body if isinstance(node, ast.ClassDef)]
                if not owners and not cls._loose_members(
                    tree, values=True, strict=True
                ):
                    continue
                if len(owners) != 1:
                    msg = f"pytest module has no sole root owner: {path}"
                    raise ValueError(msg)
                resource = project.get_resource(path.relative_to(root).as_posix())
                updated = cls._publish_test_bindings(
                    project,
                    resource,
                    source,
                    owners[0].name,
                    original_bindings=None
                    if path.name == "conftest.py"
                    else frozenset(),
                )
                final_tree = ast.parse(updated)
                canonical = cls._canonical_module_bindings(
                    project,
                    path,
                    final_tree,
                    workspace.convention(path).module_policy,
                )
                outside = tuple(
                    type(node).__name__
                    for node in final_tree.body
                    if not isinstance(node, ast.Import | ast.ImportFrom | ast.ClassDef)
                    and not cls._type_checking_import_block(node, final_tree)
                    and not cls._canonical_main_guard(project, path, final_tree, node)
                    and not cls._canonical_metadata_rebind(
                        project, path, final_tree, node
                    )
                    and not (
                        isinstance(node, ast.Expr)
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    )
                    and not (
                        isinstance(node, ast.Assign | ast.AnnAssign)
                        and cls._loose_value_name(node, strict=True) in canonical
                    )
                )
                if outside:
                    msg = f"pytest module retains unowned declarations: {path}: {', '.join(outside)}"
                    raise ValueError(msg)
                prefix = workspace.convention(path).module_policy.project_prefix
                if not prefix.startswith("Tests"):
                    prefix = f"Tests{prefix}"
                collected = path.name == "conftest.py" or any(
                    fnmatch(path.name, pattern) for pattern in pytest_patterns[0]
                )
                if collected and any(
                    isinstance(node, ast.ClassDef) and not node.name.startswith(prefix)
                    for node in ast.walk(final_tree)
                ):
                    msg = f"strict test module retains a local class without prefix {prefix}: {path}"
                    raise ValueError(msg)
                if updated != source:
                    edits.append(
                        m.Infra.SemanticMigrationEdit(
                            file_path=path,
                            original_source=source,
                            updated_source=updated,
                            changes=("published original pytest module registration",),
                        )
                    )
        finally:
            project.close()
        return tuple(edits)

    @classmethod
    def _facade_namespace_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Move duplicate facade namespaces to their declared inherited owners.

        The canonical namespace's base identities elect destinations. No symbol
        catalog participates; an occupied declaration owner is never overwritten.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SemanticMigrationEdit]``.

        """
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project,
            sources,
        )
        cutover = m.Infra.FacadeNamespaceCutover(
            project=project,
            root=Path(project.root.real_path),
            sources=sources,
            working=dict(sources),
        )
        try:
            for path, source in cls._editable_sources(sources):
                if not path.is_relative_to(Path(workspace.repository_root).resolve()):
                    continue
                site = cls._facade_namespace_site(workspace, path, source)
                if site is not None:
                    cls._apply_facade_namespace_site(cutover, site)
            return cls._facade_namespace_result(cutover)
        finally:
            project.close()

    @classmethod
    def _facade_namespace_site(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
    ) -> m.Infra.FacadeNamespaceSite | None:
        """Resolve one source's duplicate facade site, or ``None`` to skip it.

        Returns:
            The resolved site, or ``None`` when the source declares no single
            internal composed namespace facade.

        """
        policy = workspace.convention(path).module_policy
        if not policy.is_internal_namespace or policy.expected_alias is None:
            return None
        tree = ast.parse(source)
        facade = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == policy.expected_family
            ),
            None,
        )
        if facade is None:
            return None
        children = [node for node in facade.body if isinstance(node, ast.ClassDef)]
        composed = [node for node in children if node.bases]
        if len(composed) != 1:
            return None
        namespace = composed[0]
        return m.Infra.FacadeNamespaceSite(
            path=path,
            source=source,
            facade=facade,
            namespace=namespace,
            children=tuple(children),
            tree=tree,
        )

    @classmethod
    def _apply_facade_namespace_site(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
    ) -> None:
        """Plan child moves and consumer rewrites for one resolved facade site."""
        rewrites: MutableMapping[Path, list[m.Infra.SourceRewrite]] = {}
        for child in site.children:
            if child is site.namespace or child.bases or child.decorator_list:
                continue
            cls._apply_facade_namespace_child(cutover, site, child, rewrites)
        for consumer, changes in rewrites.items():
            consumer_resource = cutover.project.get_resource(
                consumer.relative_to(cutover.root).as_posix()
            )
            cutover.working[consumer] = (
                FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                    consumer_resource,
                    cutover.sources[consumer],
                    changes,
                ).new_contents
            )

    @classmethod
    def _apply_facade_namespace_child(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
        rewrites: MutableMapping[Path, list[m.Infra.SourceRewrite]],
    ) -> None:
        """Move one duplicate child declaration and record its consumer rewrites."""
        resource = cutover.project.get_resource(
            site.path.relative_to(cutover.root).as_posix()
        )
        owner = (
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(cutover.project, resource)
            .get_attribute(site.facade.name)
            .get_object()
        )
        target = owner.get_attribute(site.namespace.name).get_object()
        destinations = [
            base for base in target.get_superclasses() if base.get_name() == child.name
        ]
        if len(destinations) != 1:
            return
        destination_path = cls._facade_namespace_destination(
            cutover,
            site,
            child,
            destinations[0],
        )
        binding = owner.get_attribute(child.name)
        for consumer, rewrite in cls._collect_namespace_occurrence_rewrites(
            cutover,
            binding,
            child.name,
            site.namespace.name,
        ):
            rewrites.setdefault(consumer, []).append(rewrite)
        child_cst = cls._facade_namespace_child_cst(site, child)
        cutover.working[destination_path] = cls._facade_namespace_child_module(
            site.tree,
            child,
            child_cst,
        )
        rewrites.setdefault(site.path, []).append(
            cls._facade_namespace_removal(site.source, child)
        )

    @classmethod
    def _facade_namespace_destination(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
        destination: t.Infra.RopePyObject,
    ) -> Path:
        """Resolve one child's inherited declaration-owner destination.

        Returns:
            The editable path that carries the child's declaration owner.

        Raises:
            ValueError: If the owner has no scope, no module resource, lies
                outside the editable inventory, or is already occupied.

        """
        if destination.get_scope() is None:
            msg = "namespace declaration owner has no source scope"
            raise ValueError(msg)
        module = destination.get_module()
        if module is None or (destination_resource := module.get_resource()) is None:
            msg = "namespace declaration owner has no module resource"
            raise ValueError(msg)
        destination_path = Path(destination_resource.real_path).resolve()
        if destination_path not in cutover.sources or destination_path == site.path:
            msg = "namespace declaration owner is outside the editable inventory"
            raise ValueError(msg)
        declaration = next(
            node
            for node in ast.parse(cutover.sources[destination_path]).body
            if isinstance(node, ast.ClassDef) and node.name == child.name
        )
        if declaration.bases or any(
            not isinstance(node, ast.Pass)
            and not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            for node in declaration.body
        ):
            msg = "namespace declaration owner is already occupied"
            raise ValueError(msg)
        return destination_path

    @staticmethod
    def _facade_namespace_child_cst(
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
    ) -> cst.ClassDef:
        """Extract one facade child's concrete-syntax node.

        Returns:
            The child's CST class definition.

        Raises:
            TypeError: If the facade body is not an indented declaration.

        """
        parsed = cst.parse_module(site.source)
        facade_cst = next(
            node
            for node in parsed.body
            if isinstance(node, cst.ClassDef) and node.name.value == site.facade.name
        )
        if not isinstance(facade_cst.body, cst.IndentedBlock):
            msg = "namespace facade requires an indented declaration"
            raise TypeError(msg)
        return next(
            node
            for node in facade_cst.body.body
            if isinstance(node, cst.ClassDef) and node.name.value == child.name
        )

    @staticmethod
    def _facade_namespace_child_module(
        tree: ast.Module,
        child: ast.ClassDef,
        child_cst: cst.ClassDef,
    ) -> str:
        """Render one relocated child module with the imports it still uses.

        Returns:
            The relocated child's module source text.

        """
        used = {node.id for node in ast.walk(child) if isinstance(node, ast.Name)}
        imports = [
            node
            for node in tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
            and any(
                (alias.asname or alias.name.partition(".")[0]) in used
                for alias in node.names
            )
        ]
        return (
            "from __future__ import annotations\n\n"
            + "\n".join(ast.unparse(node) for node in imports)
            + "\n\n"
            + cst.Module(body=(child_cst,)).code
            + f"\n__all__ = [{child.name!r}]\n"
        )

    @staticmethod
    def _facade_namespace_removal(
        source: str,
        child: ast.ClassDef,
    ) -> m.Infra.SourceRewrite:
        """Compute the byte range removing a relocated child from its facade.

        Returns:
            The deletion rewrite for the child's source span.

        Raises:
            ValueError: If the child has no complete source range.

        """
        if child.end_lineno is None:
            msg = "namespace declaration has no complete source range"
            raise ValueError(msg)
        lines = source.splitlines(keepends=True)
        start = sum(map(len, lines[: child.lineno - 1]))
        end = sum(map(len, lines[: child.end_lineno]))
        return m.Infra.SourceRewrite(start=start, end=end, text="")

    @classmethod
    def _collect_namespace_occurrence_rewrites(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        binding: t.Infra.RopePyName,
        child_name: str,
        namespace_name: str,
    ) -> t.VariadicTuple[t.Pair[Path, m.Infra.SourceRewrite]]:
        """Collect consumer rewrites for one duplicate namespace declaration.

        Every non-defining occurrence of the duplicate child name across the
        editable sources is rewritten to the canonical namespace name.

        Returns:
            Each consumer path paired with the canonical-name rewrite it needs.

        """
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            cutover.project,
            child_name,
            binding,
            imports=True,
            in_hierarchy=False,
        )
        collected: list[t.Pair[Path, m.Infra.SourceRewrite]] = []
        for consumer, _consumer_source in cls._editable_sources(cutover.sources):
            consumer_resource = cutover.project.get_resource(
                consumer.relative_to(cutover.root).as_posix()
            )
            for occurrence in finder.find_occurrences(resource=consumer_resource):
                if occurrence.is_defined():
                    continue
                start, end = occurrence.get_word_range()
                collected.append((
                    consumer,
                    m.Infra.SourceRewrite(
                        start=start,
                        end=end,
                        text=namespace_name,
                    ),
                ))
        return tuple(collected)

    @classmethod
    def _facade_namespace_result(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Assemble the edits for every path whose prospective bytes changed.

        Returns:
            The edits for every source whose prospective bytes changed.

        """
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=source,
                updated_source=cutover.working[path],
                changes=(
                    (
                        "consolidated facade namespace through declaration-owner "
                        "inheritance"
                    ),
                ),
            )
            for path, source in cutover.sources.items()
            if cutover.working[path] != source
        )

    @classmethod
    def _plan_orphan_nesting(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan all structural nesting and consumer rewrites without effects.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        planned_edits = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        modules = {
            entry.file_path.resolve(): entry for entry in rope_workspace.modules()
        }
        editable = cls._editable_sources(sources)
        owned = tuple(
            item
            for item in editable
            if item[0] in modules
            and item[0].is_relative_to(Path(rope_workspace.repository_root).resolve())
        )
        # Parse native collection policy without importing consumer conftests or
        # installed plugins. Planning must not execute their registration hooks.
        pytest_patterns = cls._pytest_collection_patterns(
            Path(rope_workspace.rope_project.root.real_path),
        )
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            rope_workspace.rope_project,
            sources,
        )

        def definitions_for(item: t.Pair[Path, str]) -> p.Result[t.StrMapping]:
            try:
                return cls._class_nesting_definitions(
                    rope_workspace,
                    *item,
                    project=project,
                    pytest_patterns=pytest_patterns,
                )
            except Exception:
                traceback.print_exc()
                raise

        planned = r[t.StrMapping].traverse(owned, definitions_for, fail_fast=False)
        if planned.failure:
            project.close()
            return planned_edits.from_failure(planned)
        definitions_by_file = {
            path: definitions
            for (path, _source), definitions in zip(owned, planned.value, strict=True)
            if definitions
        }
        module_names = {
            path: modules[path].module_name
            or FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
                project.get_resource(modules[path].resource_path),
            ).get_name()
            for path, _source in owned
        }
        bindings_by_module: MutableMapping[str, MutableMapping[str, str]] = {}
        for path, definitions in definitions_by_file.items():
            module_name = module_names[path]
            bindings = bindings_by_module.setdefault(module_name, {})
            for name, owner in definitions.items():
                if bindings.setdefault(name, owner) != owner:
                    project.close()
                    return planned_edits.fail(
                        f"ambiguous class-nesting owner for {module_name}.{name}: "
                        f"{bindings[name]}, {owner}",
                    )
        nested_names = frozenset(
            name for bindings in bindings_by_module.values() for name in bindings
        )
        if not nested_names:
            project.close()
            return planned_edits.ok(())
        providers_by_module = {
            module_names[path]: project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            )
            for path in definitions_by_file
        }
        try:

            def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
                module = modules.get(path)
                definitions = definitions_by_file.get(path, {})
                updated = cls._rewrite_class_nesting_source(
                    source,
                    native=(
                        project,
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix(),
                        ),
                    ),
                    scope=(
                        module_names.get(path, ""),
                        module.is_package_init if module is not None else False,
                    ),
                    bindings_by_module=bindings_by_module,
                    providers_by_module=providers_by_module,
                    definitions=definitions,
                    sources=sources,
                    is_pytest=bool(definitions)
                    and cls._is_pytest_module(
                        project,
                        path,
                        ast.parse(source),
                        pytest_patterns,
                    ),
                )
                if definitions and updated == source:
                    msg = "class-nesting owner produced no structural edit"
                    raise ValueError(msg)
                return updated, tuple(
                    f"nested {name} under {owner}"
                    for name, owner in definitions.items()
                ) or ("rewired nested-class consumer",)

            return cls._semantic_edits(
                tuple((path, source) for path, source in editable),
                rewrite,
            )
        finally:
            project.close()


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNesting"]
