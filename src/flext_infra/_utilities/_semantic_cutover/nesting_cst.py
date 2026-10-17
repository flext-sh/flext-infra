"""Native region ownership moves for automatic class nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverNestingReferences,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesSemanticCutoverNestingCst(
    FlextInfraUtilitiesSemanticCutoverNestingReferences,
):
    """Move identity-proven members using one native source graph and regions."""

    @classmethod
    def _rewrite_class_nesting_source(
        cls,
        source: str,
        *,
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeResource],
        scope: t.Pair[str, bool],
        bindings_by_module: t.MappingKV[str, t.StrMapping],
        definitions: t.StrMapping,
        sources: t.MappingKV[Path, str],
        is_pytest: bool = False,
    ) -> str:
        project, resource = native
        module_name, is_package_init = scope
        rewritten = cls._rewrite_class_nesting_references(
            source,
            native=native,
            module_name=module_name,
            is_package_init=is_package_init,
            bindings_by_module=bindings_by_module,
            definitions=definitions,
            sources=sources,
        )
        return cls._nest_definitions(
            project, resource, rewritten, definitions, is_pytest=is_pytest
        )

    @classmethod
    def _nesting_selection(
        cls,
        module: p.Infra.RopePyModule,
        facts: t.SequenceOf[m.Infra.LogicalStatement],
        definitions: t.StrMapping,
    ) -> t.Pair[
        t.SequenceOf[m.Infra.LogicalStatement],
        t.MappingKV[str, p.Infra.RopeScope],
    ]:
        """Elect source statements and native scope identities from one parsed module.

        Returns:
            The original ordered top-level members and actual native scopes.

        """
        selected = [
            item
            for item in facts
            if item.indent == 0 and cls._native_member_name(item) in definitions
        ]
        scopes = {
            scope.pyobject.get_name(): scope
            for scope in module.get_scope().get_scopes()
        }
        return selected, scopes

    @classmethod
    def _nested_member_body(
        cls,
        item: m.Infra.LogicalStatement,
        body: str,
        native: t.Pair[p.Infra.RopePyModule, p.Infra.RopeSemanticModule],
        classvar_name: str,
    ) -> str:
        """Render the original member category through its real native annotation.

        Returns:
            The unchanged class, static function or source-derived ClassVar body.

        """
        if item.category == c.Infra.StatementCategory.FUNC_DEF:
            return "@staticmethod\n" + body
        annotation = cls._member_annotation(item, *native)
        if annotation is not None:
            parts = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                item.text, 0, len(item.text), "="
            )
            value = item.text[parts[-1][0] : parts[-1][1]]
            return (
                f"{cls._native_member_name(item)}: "
                f"{classvar_name}[{annotation}] = {value}\n"
            )
        return body

    @classmethod
    def _nested_member_edits(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
        typing: p.Infra.RopeSemanticModule,
        selection: t.Triple[
            t.SequenceOf[m.Infra.LogicalStatement],
            t.MappingKV[str, p.Infra.RopeScope],
            str,
        ],
        indentation: int,
    ) -> t.Pair[list[m.Infra.SourceRewrite], str]:
        """Retain native member regions while rendering their ordered nested bodies.

        Returns:
            Actual source-removal edits and their ordered reindented member bodies.

        """
        selected, scopes = selection[0], selection[1]
        edits: list[m.Infra.SourceRewrite] = []
        members: list[str] = []
        decorated = {
            node.name: min(decorator.lineno for decorator in node.decorator_list)
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node.decorator_list
        }
        for item in selected:
            name = cls._native_member_name(item)
            scope = scopes.get(name)
            begin = item.start_offset
            end = min(item.end_offset + 1, len(source))
            if scope is not None:
                begin = module.lines.get_line_start(
                    module.lines.get_line_number(scope.get_region()[0])
                )
                end = min(module.lines.get_line_end(scope.get_end()) + 1, len(source))
            if name in decorated:
                begin = min(begin, module.lines.get_line_start(decorated[name]))
            members.append(
                FlextInfraUtilitiesRopeRuntimeRefactors.reindent_source(
                    cls._nested_member_body(
                        item, source[begin:end], (module, typing), selection[2]
                    ).rstrip()
                    + "\n",
                    indentation,
                )
            )
            edits.append(m.Infra.SourceRewrite(start=begin, end=end, text=""))
        return edits, "\n".join(members)

    @staticmethod
    def _new_nesting_owner(
        module: p.Infra.RopePyModule,
        owner: t.Triple[str, str, int],
        edits: t.SequenceOf[m.Infra.SourceRewrite],
    ) -> list[m.Infra.SourceRewrite]:
        """Build a real owner declaration at the first moved member's source region.

        Returns:
            Original removal edits with the first owner declaration substituted.

        """
        owner_name, nested, indentation = owner
        doc = module.get_doc()
        summary = doc.splitlines()[0].strip() if doc else ""
        position = min(edit.start for edit in edits)
        replacement = (
            f"class {owner_name}:\n"
            + (" " * indentation + repr(summary) + "\n\n" if summary else "")
            + nested
        )
        return [
            edit.model_copy(update={"text": replacement})
            if edit.start == position
            else edit
            for edit in edits
        ]

    @staticmethod
    def _existing_owner_edits(
        source: str,
        module: p.Infra.RopePyModule,
        facts: t.SequenceOf[m.Infra.LogicalStatement],
        owner: p.Infra.RopeScope,
        contents: t.Pair[str, int],
    ) -> t.SequenceOf[m.Infra.SourceRewrite]:
        """Extend the exact existing native owner body without rediscovering regions.

        Returns:
            Real replacement or insertion edits for the original owner scope.

        Raises:
            ValueError: An inline owner has no single native body region.

        """
        nested, indentation = contents
        header = next(item for item in facts if item.line == owner.get_start())
        first = module.lines.get_line_start(owner.get_body_start())
        last = min(module.lines.get_line_end(owner.get_end()) + 1, len(source))
        if owner.get_body_start() == owner.get_start():
            regions = (
                FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                    header.text, 0, len(header.text), ":"
                )
            )
            match regions:
                case [_, body_region]:
                    first = header.start_offset + body_region[0]
                case _:
                    msg = "native inline owner has no single body region"
                    raise ValueError(msg)
            body = source[first:last].strip()
            retained = (
                ""
                if body == "pass"
                else FlextInfraUtilitiesRopeRuntimeRefactors.reindent_source(
                    body + "\n", indentation
                )
            )
            return (
                m.Infra.SourceRewrite(
                    start=first, end=last, text="\n" + retained + nested
                ),
            )
        own_body = [
            item
            for item in facts
            if owner.get_body_start() <= item.line <= owner.get_end()
        ]
        if len(own_body) == 1 and own_body[0].text.strip() == "pass":
            return (m.Infra.SourceRewrite(start=first, end=last, text=nested),)
        if (
            own_body
            and FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(
                own_body[0].text.strip()
            )
            is not None
        ):
            first = min(own_body[0].end_offset + 1, len(source))
        return (
            m.Infra.SourceRewrite(start=first, end=first, text="\n" + nested + "\n"),
        )

    @classmethod
    def _owner_nesting_edits(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
        structure: t.Pair[
            t.SequenceOf[m.Infra.LogicalStatement],
            t.MappingKV[str, p.Infra.RopeScope],
        ],
        contents: t.Triple[str, str, int],
        edits: t.SequenceOf[m.Infra.SourceRewrite],
    ) -> list[m.Infra.SourceRewrite]:
        """Choose the actual existing owner or create its source-defined declaration.

        Returns:
            Original removals plus the exact owner insertion/replacement edits.

        """
        owner = structure[1].get(contents[0])
        if owner is None:
            return cls._new_nesting_owner(module, contents, edits)
        return [
            *edits,
            *cls._existing_owner_edits(
                source, module, structure[0], owner, (contents[1], contents[2])
            ),
        ]

    @staticmethod
    def _nested_exports(value: str, owner_name: str, definitions: t.StrMapping) -> str:
        """Retain original public names while replacing moved members by their owner.

        Returns:
            The original tuple/list export shape with stable surviving name order.

        """
        names = [owner_name]
        for (
            start,
            stop,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(value):
            if value[start] != "#":
                name = FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(
                    value[start:stop]
                )
                if name is not None and name not in definitions and name not in names:
                    names.append(name)
        rendered = ", ".join(map(repr, names))
        return f"({rendered},)" if value.startswith("(") else f"[{rendered}]"

    @classmethod
    def _nesting_export_edits(
        cls,
        source: str,
        facts: t.SequenceOf[m.Infra.LogicalStatement],
        owner_name: str,
        definitions: t.StrMapping,
    ) -> t.SequenceOf[m.Infra.SourceRewrite]:
        """Rewrite the actual top-level export statements after nesting the owner.

        Returns:
            Exact native source edits preserving existing export statement order.

        """
        exports = [
            item
            for item in facts
            if item.indent == 0
            and FlextInfraUtilitiesRopeStructure.target_name(item) == "__all__"
        ]
        if not exports:
            return (
                m.Infra.SourceRewrite(
                    start=len(source),
                    end=len(source),
                    text=f"\n__all__: list[str] = [{owner_name!r}]\n",
                ),
            )
        edits: list[m.Infra.SourceRewrite] = []
        for item in exports:
            parts = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                item.text, 0, len(item.text), "="
            )
            begin, end = parts[-1]
            edits.append(
                m.Infra.SourceRewrite(
                    start=item.start_offset + begin,
                    end=item.start_offset + end,
                    text=cls._nested_exports(
                        item.text[begin:end], owner_name, definitions
                    ),
                )
            )
        return edits

    @classmethod
    def _nest_definitions(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        definitions: t.StrMapping,
        *,
        is_pytest: bool = False,
    ) -> str:
        if not definitions:
            return source
        owners = frozenset(definitions.values())
        if len(owners) != 1:
            msg = f"class-nesting file has multiple owners: {sorted(owners)}"
            raise ValueError(msg)
        owner_name = next(iter(owners))
        composition = is_pytest and not any(
            isinstance(node, ast.ClassDef) and node.name == owner_name
            for node in ast.parse(source).body
        )
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project, source, resource=resource
        )
        facts = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        typing = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
            project.get_module("typing")
        )
        selection = cls._nesting_selection(module, facts, definitions)
        if any(
            item.category
            in {c.Infra.StatementCategory.ASSIGN, c.Infra.StatementCategory.ANN_ASSIGN}
            and cls._member_annotation(item, module, typing) is not None
            for item in selection[0]
        ):
            source, classvar_name = (
                FlextInfraUtilitiesRopeRuntimeModules.import_binding(
                    project, module, "typing", "ClassVar"
                )
            )
            module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, source, resource=resource
            )
            facts = FlextInfraUtilitiesRopeStructure.logical_statements(source)
            selection = cls._nesting_selection(module, facts, definitions)
        else:
            classvar_name = ""
        if {cls._native_member_name(item) for item in selection[0]} != set(definitions):
            msg = f"class-nesting structure mismatch for {owner_name}"
            raise ValueError(msg)
        indentation = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.refactor.sourceutils", "get_indent"
        )(project)
        if type(indentation) is not int or indentation <= 0:
            msg = "native Rope project has no positive indentation policy"
            raise TypeError(msg)
        edits, nested = cls._nested_member_edits(
            source, module, typing, (*selection, classvar_name), indentation
        )
        edits = cls._owner_nesting_edits(
            source,
            module,
            (facts, selection[1]),
            (owner_name, nested, indentation),
            edits,
        )
        edits.extend(
            cls._nesting_export_edits(source, facts, owner_name, definitions)
        )
        nested_source = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents
        if not is_pytest:
            return nested_source
        return cls._publish_test_bindings(
            project,
            resource,
            nested_source,
            owner_name,
            original_bindings=None
            if Path(resource.real_path).name == "conftest.py"
            else frozenset(definitions),
            composition=composition,
        )

    @classmethod
    def _publish_test_bindings(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        owner_name: str,
        *,
        original_bindings: frozenset[str] | None = None,
        composition: bool = False,
    ) -> str:
        """Keep pytest's original module registration while owning every declaration."""
        tree = ast.parse(source)
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == owner_name
        )
        publishers = {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "flext_tests.conftest_plugin"
            for alias in node.names
            if alias.name == "FlextTestsConftestPlugin"
        }
        if any(
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "publish"
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id in publishers
            for node in owner.body
        ):
            return source
        fixtures = {"fixture", "hookimpl"} | {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "pytest"
            for alias in node.names
            if alias.name in {"fixture", "hookimpl"}
        }
        bindings: dict[str, str] = {}
        metadata: list[str] = []
        patterns = cls._pytest_collection_patterns(Path(project.root.real_path))
        original = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        for node in owner.body:
            if isinstance(node, ast.ClassDef):
                if (
                    composition
                    and (original_bindings is None or node.name in original_bindings)
                    and cls._pytest_class_binding(node.name, original.get_attribute(node.name), patterns[1])
                ):
                    bindings[node.name] = node.name
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if original_bindings is not None and node.name not in original_bindings:
                    continue
                decorators = [
                    decorator.func if isinstance(decorator, ast.Call) else decorator
                    for decorator in node.decorator_list
                ]
                tails = {
                    decorator.attr
                    if isinstance(decorator, ast.Attribute)
                    else decorator.id
                    if isinstance(decorator, ast.Name)
                    else ""
                    for decorator in decorators
                }
                if (
                    node.name.startswith("pytest_")
                    or node.name in {"setup_module", "teardown_module", "setup_function", "teardown_function"}
                    or tails & fixtures
                    or composition and cls._pytest_name_matches(node.name, patterns[2])
                ):
                    if "staticmethod" not in tails:
                        msg = f"pytest publication requires staticmethod outside fixture/hook decorators: {resource.path}:{node.name}"
                        raise ValueError(msg)
                    bindings[node.name] = f"{node.name}.__func__"
            elif isinstance(node, ast.Assign | ast.AnnAssign):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name) and (
                        target.id in {"pytestmark", "pytest_plugins"}
                        or (
                            target.id != "__all__"
                            and target.id.startswith("__")
                            and target.id.endswith("__")
                        )
                    ):
                        if (
                            original_bindings is not None
                            and target.id not in original_bindings
                        ):
                            continue
                        bindings[target.id] = target.id
                        metadata.append(target.id)
        bindings["__all__"] = repr((owner_name,))
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project, source, resource=resource
        )
        source, publisher = FlextInfraUtilitiesRopeRuntimeModules.import_binding(
            project,
            module,
            "flext_tests.conftest_plugin",
            "FlextTestsConftestPlugin",
        )
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project, source, resource=resource
        )
        scope = next(
            scope
            for scope in module.get_scope().get_scopes()
            if scope.pyobject.get_name() == owner_name
        )
        occupied = scope.get_defined_names()
        if "globals" in occupied or publisher.partition(".")[0] in occupied:
            msg = f"pytest publication bootstrap is shadowed by a class-owned binding: {resource.path}:{owner_name}"
            raise ValueError(msg)
        insertion = min(module.lines.get_line_end(scope.get_end()) + 1, len(source))
        rendered = ", ".join(f"{name!r}: {value}" for name, value in bindings.items())
        bootstrap = f"\n    {publisher}.publish(module_globals=globals(), bindings={{{rendered}}})\n"
        if composition:
            # Only this ordinary composition root is hidden. Original suite and
            # free-function objects remain children of their original module.
            bootstrap += "    __test__ = False\n"
        elif metadata:
            # Module marks must not also become inherited class marks.
            bootstrap += "    del " + ", ".join(metadata) + "\n"
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=insertion, end=insertion, text=bootstrap),),
        ).new_contents

    @staticmethod
    def _native_member_name(statement: m.Infra.LogicalStatement) -> str:
        if statement.category == c.Infra.StatementCategory.TYPE_ALIAS:
            return FlextInfraUtilitiesRopeStructure.header_name(
                statement.text.partition("=")[0],
            )
        if statement.category in {
            c.Infra.StatementCategory.CLASS_DEF,
            c.Infra.StatementCategory.FUNC_DEF,
        }:
            return FlextInfraUtilitiesRopeStructure.header_name(statement.text)
        return FlextInfraUtilitiesRopeStructure.target_name(statement)

    @staticmethod
    def _member_annotation(
        statement: m.Infra.LogicalStatement,
        module: p.Infra.RopePyModule,
        typing: p.Infra.RopeSemanticModule,
    ) -> str | None:
        if statement.category not in {
            c.Infra.StatementCategory.ANN_ASSIGN,
            c.Infra.StatementCategory.ASSIGN,
        }:
            return None
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        parts = types.expression_segments(statement.text, 0, len(statement.text), ":=")
        match parts:
            case [_, annotation_region, _]:
                annotation = statement.text[annotation_region[0] : annotation_region[1]]
                qualifier = annotation.partition("[")[0].strip()
                binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                    module.get_scope(), qualifier
                )
                if any(
                    FlextInfraUtilitiesRopeRuntimeModules.same_name(
                        typing.get_attribute(name), binding
                    )
                    for name in ("ClassVar", "Final")
                ):
                    return None
                return annotation
            case [_, value_region]:
                constant = FlextInfraUtilitiesRopeRuntimeRefactors.compiled_constant(
                    statement.text[value_region[0] : value_region[1]]
                )
                if constant.success:
                    return type(constant.value).__name__
            case _:
                return None
        return None


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingCst"]
