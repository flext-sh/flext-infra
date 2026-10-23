"""Native region ownership moves for automatic class nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import libcst as cst
from libcst.metadata import (
    MetadataWrapper,
    PositionProvider,
    WhitespaceInclusivePositionProvider,
)

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
    FlextInfraUtilitiesSemanticCutoverNestingReferences,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesSemanticCutoverNestingCst(
    FlextInfraUtilitiesSemanticCutoverNestingReferences,
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
):
    """Move identity-proven members using one native source graph and regions."""

    @classmethod
    def _rewrite_class_nesting_source(
        cls,
        source: str,
        *,
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeFile],
        bindings: t.Pair[
            t.MappingKV[str, t.StrMapping],
            t.MappingKV[str, p.Infra.RopeResource],
        ],
        selection: t.Pair[t.StrMapping, bool],
        sources: t.MappingKV[Path, str],
    ) -> str:
        """Return a binding-proven structural rewrite without filesystem effects.

        Returns:
            A binding-proven structural rewrite without filesystem effects.

        """
        project, resource = native
        definitions, is_pytest = selection
        rewritten = cls._rewrite_class_nesting_references(
            source,
            native=native,
            bindings=bindings,
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
            if item.indent == 0
            and all(
                cls._native_member_name(part) in definitions
                for part in cls._nesting_statement_parts(item)
            )
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
        members = cls._nesting_statement_parts(item)
        if len(members) > 1:
            for part in reversed(members):
                first = part.start_offset - item.start_offset
                last = part.end_offset - item.start_offset
                rendered = cls._nested_member_body(
                    part, part.text, native, classvar_name
                ).rstrip("\n")
                body = body[:first] + rendered + body[last:]
            return body
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
        native: t.Pair[p.Infra.RopePyModule, MetadataWrapper],
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
        module, wrapper = native
        selected = selection[0]
        edits: list[m.Infra.SourceRewrite] = []
        members: list[str] = []
        positions = wrapper.resolve(PositionProvider)
        inclusive = wrapper.resolve(WhitespaceInclusivePositionProvider)
        statements = {
            positions[node].start.line: node for node in wrapper.module.body
        }
        for item in selected:
            node = statements[item.line]
            region = inclusive[node]
            begin = module.lines.get_line_start(region.start.line) + region.start.column
            end = module.lines.get_line_start(region.end.line) + region.end.column
            code = (
                node.decorators[0]
                if isinstance(node, cst.FunctionDef | cst.ClassDef) and node.decorators
                else node
            )
            code_start = module.lines.get_line_start(positions[code].start.line)
            members.append(
                FlextInfraUtilitiesRopeRuntimeRefactors.reindent_source(
                    (source[begin:code_start] + cls._nested_member_body(
                        item, source[code_start:end], (module, typing), selection[2]
                    )).rstrip()
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
        docstring = (
            ast.unparse(
                ast.Module(
                    body=[ast.Expr(value=ast.Constant(value=summary))],
                    type_ignores=[],
                )
            )
            if summary
            else ""
        )
        position = min(edit.start for edit in edits)
        replacement = (
            f"class {owner_name}:\n"
            + (" " * indentation + docstring + "\n\n" if docstring else "")
            + nested
        )
        return [
            edit.model_copy(update={"text": replacement})
            if edit.start == position
            else edit
            for edit in edits
        ]

    @staticmethod
    def _owner_body_start(
        native: t.Pair[p.Infra.RopePyModule, MetadataWrapper],
        owner: p.Infra.RopeScope,
    ) -> t.Pair[int, int]:
        """Elect the first owned member, including its native decorator region.

        Returns:
            The complete owned prefix and code line offsets of the first member.

        Raises:
            TypeError: The owning object has no source AST capability.
            ValueError: The elected owner is not a nonempty source class.

        """
        module, wrapper = native
        if not isinstance(owner.pyobject, p.Infra.RopeSourceDefinition):
            msg = "native nesting owner has no source AST"
            raise TypeError(msg)
        node = owner.pyobject.get_ast()
        if not isinstance(node, ast.ClassDef) or not node.body:
            msg = "native nesting owner is not a nonempty source class"
            raise ValueError(msg)
        positions = wrapper.resolve(PositionProvider)
        declaration = next(
            item for item in wrapper.module.body
            if isinstance(item, cst.ClassDef) and positions[item].start.line == node.lineno
        )
        member = declaration.body.body[0]
        region = wrapper.resolve(WhitespaceInclusivePositionProvider)[member]
        return (
            module.lines.get_line_start(region.start.line) + region.start.column,
            module.lines.get_line_start(positions[member].start.line),
        )

    @classmethod
    def _existing_owner_edits(
        cls,
        source: str,
        native: t.Pair[p.Infra.RopePyModule, MetadataWrapper],
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
        module = native[0]
        header = next(item for item in facts if item.line == owner.get_start())
        first, code_start = cls._owner_body_start(native, owner)
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
            return (m.Infra.SourceRewrite(
                start=first, end=last, text=source[first:code_start] + nested
            ),)
        if own_body and owner.pyobject.get_doc() is not None:
            first = min(own_body[0].end_offset + 1, len(source))
        return (
            m.Infra.SourceRewrite(start=first, end=first, text="\n" + nested + "\n"),
        )

    @classmethod
    def _owner_nesting_edits(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
        structure: t.Triple[
            t.SequenceOf[m.Infra.LogicalStatement],
            t.MappingKV[str, p.Infra.RopeScope],
            MetadataWrapper,
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
                source, (module, structure[2]), structure[0], owner, (contents[1], contents[2])
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
        *,
        is_pytest: bool = False,
    ) -> t.SequenceOf[m.Infra.SourceRewrite]:
        """Rewrite the actual top-level export statements after nesting the owner.

        Returns:
            Exact native source edits preserving existing export statement order.
            A pytest module never keeps a loose module-level ``__all__``: the
            canonical registration owner publishes the exports from its own
            body, so the loose statements are only removed here.

        """
        exports = [
            item
            for item in facts
            if item.indent == 0
            and FlextInfraUtilitiesRopeStructure.target_name(item) == "__all__"
        ]
        if not exports:
            if is_pytest:
                return ()
            return (
                m.Infra.SourceRewrite(
                    start=len(source),
                    end=len(source),
                    text=f"\n__all__: list[str] = [{owner_name!r}]\n",
                ),
            )
        edits: list[m.Infra.SourceRewrite] = []
        for item in exports:
            if is_pytest:
                edits.append(
                    m.Infra.SourceRewrite(
                        start=item.start_offset,
                        end=min(item.end_offset + 1, len(source)),
                        text="",
                    )
                )
                continue
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
            for selected in selection[0]
            for item in cls._nesting_statement_parts(selected)
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
        wrapper = MetadataWrapper(cst.parse_module(source), unsafe_skip_copy=True)
        observed = {
            cls._native_member_name(part)
            for item in selection[0]
            for part in cls._nesting_statement_parts(item)
        }
        if observed != set(definitions):
            msg = (
                f"class-nesting structure mismatch for {owner_name}: "
                f"expected {sorted(definitions)}, observed {sorted(observed)}"
            )
            raise ValueError(msg)
        indentation = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.refactor.sourceutils", "get_indent"
        )(project)
        if type(indentation) is not int or indentation <= 0:
            msg = "native Rope project has no positive indentation policy"
            raise TypeError(msg)
        edits, nested = cls._nested_member_edits(
            source, (module, wrapper), typing, (*selection, classvar_name), indentation
        )
        edits = cls._owner_nesting_edits(
            source,
            module,
            (facts, selection[1], wrapper),
            (owner_name, nested, indentation),
            edits,
        )
        edits.extend(
            cls._nesting_export_edits(
                source, facts, owner_name, definitions, is_pytest=is_pytest
            )
        )
        nested_source = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents
        if not is_pytest:
            return nested_source
        return cls._publish_test_bindings(
            (project, resource),
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
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeResource],
        source: str,
        owner_name: str,
        *,
        original_bindings: frozenset[str] | None = None,
        composition: bool = False,
    ) -> str:
        """Keep pytest's original module registration owning every declaration.

        Args:
            native: The native project and original resource.
            source: Authored module text holding the owning class.
            owner_name: Class whose declarations this publication owns.
            original_bindings: Names that must survive publication unchanged.
            composition: Whether the plain composition root is hidden.

        Returns:
            The published module text with the owned bootstrap appended.

        """
        tree = ast.parse(source)
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == owner_name
        )
        if any(
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "publish"
            and isinstance(node.value.func.value, ast.Name | ast.Attribute)
            for node in owner.body
        ):
            return source
        bindings, metadata, registrations = cls._test_publication_members(
            owner, tree, native, (original_bindings, composition)
        )
        bindings["__all__"] = repr([owner_name])
        if not registrations:
            return cls._publish_owner_exports(
                native, source, owner, bindings["__all__"]
            )
        return cls._render_test_publication(
            native, source, owner_name, (bindings, metadata, composition)
        )

    @classmethod
    def _test_publication_members(
        cls,
        owner: ast.ClassDef,
        tree: ast.Module,
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeResource],
        policy: t.Pair[frozenset[str] | None, bool],
    ) -> t.Triple[t.MutableMappingKV[str, str], list[str], bool]:
        project, resource = native
        original_bindings, composition = policy
        fixtures = {"fixture", "hookimpl"} | {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "pytest"
            for alias in node.names
            if alias.name in {"fixture", "hookimpl"}
        }
        bindings: t.MutableMappingKV[str, str] = {}
        metadata: list[str] = []
        registrations = False
        patterns = cls._pytest_collection_patterns(Path(project.root.real_path))
        original = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        for node in owner.body:
            if isinstance(node, ast.ClassDef):
                if (
                    composition
                    and (original_bindings is None or node.name in original_bindings)
                    and cls._pytest_class_binding(
                        node.name, original.get_attribute(node.name), patterns[1]
                    )
                ):
                    bindings[node.name] = node.name
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if original_bindings is not None and node.name not in original_bindings:
                    continue
                if cls._pytest_function_publication(
                    node, fixtures, (composition, patterns[2]), resource.path
                ):
                    bindings[node.name] = f"{node.name}.__func__"
                    registrations = True
            elif isinstance(node, ast.Assign | ast.AnnAssign):
                for name in cls._pytest_metadata_names(node, original_bindings):
                    bindings[name] = name
                    metadata.append(name)
                    registrations = True
        return bindings, metadata, registrations

    @staticmethod
    def _pytest_metadata_names(
        node: ast.Assign | ast.AnnAssign,
        original_bindings: frozenset[str] | None,
    ) -> t.StrTuple:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return tuple(
            target.id
            for target in targets
            if isinstance(target, ast.Name)
            and (
                target.id in {"pytestmark", "pytest_plugins"}
                or (
                    target.id != "__all__"
                    and target.id.startswith("__")
                    and target.id.endswith("__")
                )
            )
            and (original_bindings is None or target.id in original_bindings)
        )

    @classmethod
    def _pytest_function_publication(
        cls,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        fixtures: set[str],
        policy: t.Pair[bool, t.StrSequence],
        resource_path: str,
    ) -> bool:
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
        selected = bool(
            node.name.startswith("pytest_")
            or node.name
            in {
                "setup_module",
                "teardown_module",
                "setup_function",
                "teardown_function",
            }
            or tails & fixtures
            or (policy[0] and cls._pytest_name_matches(node.name, policy[1]))
        )
        if selected and "staticmethod" not in tails:
            msg = (
                "pytest publication requires staticmethod outside "
                f"fixture/hook decorators: {resource_path}:{node.name}"
            )
            raise ValueError(msg)
        return selected

    @staticmethod
    def _publish_owner_exports(
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeResource],
        source: str,
        owner: ast.ClassDef,
        exports: str,
    ) -> str:
        project, resource = native
        if any(
            isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
            for node in owner.body
        ):
            return source
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project, source, resource=resource
        )
        scope = next(
            scope
            for scope in module.get_scope().get_scopes()
            if scope.pyobject.get_name() == owner.name
        )
        insertion = min(module.lines.get_line_end(scope.get_end()) + 1, len(source))
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (
                m.Infra.SourceRewrite(
                    start=insertion,
                    end=insertion,
                    text=f"\n    __all__: list[str] = {exports}\n",
                ),
            ),
        ).new_contents

    @staticmethod
    def _render_test_publication(
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeResource],
        source: str,
        owner_name: str,
        publication: t.Triple[t.StrMapping, t.StrSequence, bool],
    ) -> str:
        project, resource = native
        bindings, metadata, composition = publication
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
            msg = (
                "pytest publication bootstrap is shadowed by a class-owned "
                f"binding: {resource.path}:{owner_name}"
            )
            raise ValueError(msg)
        insertion = min(module.lines.get_line_end(scope.get_end()) + 1, len(source))
        rendered = ", ".join(f"{name!r}: {value}" for name, value in bindings.items())
        bootstrap = (
            f"\n    {publisher}.publish("
            f"module_globals=globals(), bindings={{{rendered}}})\n"
        )
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
    def _nesting_statement_parts(
        statement: m.Infra.LogicalStatement,
    ) -> t.SequenceOf[m.Infra.LogicalStatement]:
        """Retain each simple declaration inside its original logical region.

        Returns:
            Individually categorized members with character-based source offsets.

        """
        if ";" not in statement.text or statement.category not in {
            c.Infra.StatementCategory.ASSIGN,
            c.Infra.StatementCategory.ANN_ASSIGN,
            c.Infra.StatementCategory.TYPE_ALIAS,
        }:
            return (statement,)
        regions = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
            statement.text, 0, len(statement.text), ";"
        )
        if len(regions) <= 1:
            return (statement,)
        return tuple(
            FlextInfraUtilitiesRopeStructure.logical_statements(
                statement.text[first:last]
            )[0].model_copy(
                update={
                    "start_offset": statement.start_offset + first,
                    "end_offset": statement.start_offset + last,
                }
            )
            for first, last in regions
        )

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
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        if (
            statement.category
            not in {
                c.Infra.StatementCategory.ANN_ASSIGN,
                c.Infra.StatementCategory.ASSIGN,
            }
            or len(
                types.expression_segments(statement.text, 0, len(statement.text), "=")
            )
            == 1
        ):
            return None
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
