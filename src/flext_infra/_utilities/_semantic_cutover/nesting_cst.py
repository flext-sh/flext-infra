"""Native region ownership moves for automatic class nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
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
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        module_name: str,
        is_package_init: bool,
        bindings_by_module: t.MappingKV[str, t.StrMapping],
        definitions: t.StrMapping,
    ) -> str:
        rewritten = cls._rewrite_class_nesting_references(
            source,
            project=project,
            resource=resource,
            module_name=module_name,
            is_package_init=is_package_init,
            bindings_by_module=bindings_by_module,
            definitions=definitions,
        )
        return cls._nest_definitions(project, resource, rewritten, definitions)

    @classmethod
    def _nest_definitions(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        definitions: t.StrMapping,
    ) -> str:
        if not definitions:
            return source
        owners = frozenset(definitions.values())
        if len(owners) != 1:
            msg = f"class-nesting file has multiple owners: {sorted(owners)}"
            raise ValueError(msg)
        owner_name = next(iter(owners))
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        module = runtime.build_string_module(project, source, resource=resource)
        facts = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        typing = project.get_module("typing")
        selected = [
            item
            for item in facts
            if item.indent == 0 and cls._native_member_name(item) in definitions
        ]
        scopes = {
            scope.pyobject.get_name(): scope
            for scope in module.get_scope().get_scopes()
        }
        classvar = any(
            item.category
            in {c.Infra.StatementCategory.ASSIGN, c.Infra.StatementCategory.ANN_ASSIGN}
            and cls._member_annotation(item, module, typing) is not None
            for item in selected
        )
        if classvar:
            source, classvar_name = runtime.import_binding(
                project, module, "typing", "ClassVar"
            )
            module = runtime.build_string_module(project, source, resource=resource)
            facts = FlextInfraUtilitiesRopeStructure.logical_statements(source)
            selected = [
                item
                for item in facts
                if item.indent == 0 and cls._native_member_name(item) in definitions
            ]
            scopes = {
                scope.pyobject.get_name(): scope
                for scope in module.get_scope().get_scopes()
            }
        else:
            classvar_name = ""
        if {cls._native_member_name(item) for item in selected} != set(definitions):
            msg_0 = f"class-nesting structure mismatch for {owner_name}"
            raise ValueError(msg_0)
        indentation = refactors.runtime_callable(
            "rope.refactor.sourceutils", "get_indent"
        )(project)
        if type(indentation) is not int or indentation <= 0:
            msg_1 = "native Rope project has no positive indentation policy"
            raise TypeError(msg_1)
        edits = []
        members = []
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
            body = source[begin:end]
            if item.category == c.Infra.StatementCategory.FUNC_DEF:
                body = "@staticmethod\n" + body
            elif (
                annotation := cls._member_annotation(item, module, typing)
            ) is not None:
                parts = (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                        item.text, 0, len(item.text), "="
                    )
                )
                value = item.text[parts[-1][0] : parts[-1][1]]
                body = f"{name}: {classvar_name}[{annotation}] = {value}\n"
            members.append(refactors.reindent_source(body.rstrip() + "\n", indentation))
            edits.append(m.Infra.SourceRewrite(start=begin, end=end, text=""))
        nested = "\n".join(members)
        owner = scopes.get(owner_name)
        if owner is None:
            doc = module.get_doc()
            summary = doc.splitlines()[0].strip() if doc else ""
            if not summary:
                msg_1 = (
                    f"class-nesting owner {owner_name} needs a module docstring summary"
                )
                raise TypeError(msg_1)
            position = min(edit.start for edit in edits)
            replacement = (
                f"class {owner_name}:\n"
                + " " * indentation
                + repr(summary)
                + "\n\n"
                + nested
            )
            edits = [
                edit.model_copy(update={"text": replacement})
                if edit.start == position
                else edit
                for edit in edits
            ]
        else:
            header = next(item for item in facts if item.line == owner.get_start())
            first = module.lines.get_line_start(owner.get_body_start())
            last = min(module.lines.get_line_end(owner.get_end()) + 1, len(source))
            if owner.get_body_start() == owner.get_start():
                regions = (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                        header.text, 0, len(header.text), ":"
                    )
                )
                if len(regions) != 2:
                    msg_1 = "native inline owner has no single body region"
                    raise ValueError(msg_1)
                first = header.start_offset + regions[1][0]
                body = source[first:last].strip()
                retained = (
                    ""
                    if body == "pass"
                    else refactors.reindent_source(body + "\n", indentation)
                )
                edits.append(
                    m.Infra.SourceRewrite(
                        start=first, end=last, text="\n" + retained + nested
                    )
                )
            else:
                own_body = [
                    item
                    for item in facts
                    if owner.get_body_start() <= item.line <= owner.get_end()
                ]
                if len(own_body) == 1 and own_body[0].text.strip() == "pass":
                    edits.append(
                        m.Infra.SourceRewrite(start=first, end=last, text=nested)
                    )
                else:
                    if (
                        own_body
                        and refactors.literal_string(own_body[0].text.strip())
                        is not None
                    ):
                        first = min(own_body[0].end_offset + 1, len(source))
                    edits.append(
                        m.Infra.SourceRewrite(
                            start=first, end=first, text="\n" + nested + "\n"
                        )
                    )
        exports = [
            item
            for item in facts
            if item.indent == 0
            and FlextInfraUtilitiesRopeStructure.target_name(item) == "__all__"
        ]
        if exports:
            for item in exports:
                parts = (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                        item.text, 0, len(item.text), "="
                    )
                )
                begin, end = parts[-1]
                value = item.text[begin:end]
                names = [owner_name]
                for start, stop, _metadata in refactors.ignored_regions(value):
                    if value[start] != "#":
                        name = refactors.literal_string(value[start:stop])
                        if (
                            name is not None
                            and name not in definitions
                            and name not in names
                        ):
                            names.append(name)
                rendered = ", ".join(map(repr, names))
                expression = (
                    f"({rendered},)" if value.startswith("(") else f"[{rendered}]"
                )
                edits.append(
                    m.Infra.SourceRewrite(
                        start=item.start_offset + begin,
                        end=item.start_offset + end,
                        text=expression,
                    )
                )
        else:
            edits.append(
                m.Infra.SourceRewrite(
                    start=len(source),
                    end=len(source),
                    text=f"\n__all__: list[str] = [{owner_name!r}]\n",
                )
            )
        return refactors.content_change(resource, source, edits).new_contents

    @staticmethod
    def _native_member_name(statement: m.Infra.LogicalStatement) -> str:
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
        typing: p.Infra.RopePyModule,
    ) -> str | None:
        if statement.category not in {
            c.Infra.StatementCategory.ANN_ASSIGN,
            c.Infra.StatementCategory.ASSIGN,
        }:
            return None
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        parts = types.expression_segments(statement.text, 0, len(statement.text), ":=")
        if len(parts) == 3:
            annotation = statement.text[parts[1][0] : parts[1][1]]
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
        if len(parts) == 2:
            constant = FlextInfraUtilitiesRopeRuntimeRefactors.compiled_constant(
                statement.text[parts[-1][0] : parts[-1][1]]
            )
            if constant.success:
                return type(constant.value).__name__
        return None


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingCst"]
