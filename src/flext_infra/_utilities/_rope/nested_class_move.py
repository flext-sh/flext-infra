"""Extract a self-referenced nested family member into its own module.

A field annotation of a nested model that names a sibling through its own
enclosing family class cannot resolve while the family body executes, so the
model stays incomplete at import. The sibling moves to a module of its own as
a top-level class; the existing orphan nesting then wraps it into the family
owner the module convention derives, and the move keeps one owner per step.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence

import libcst as cst
import libcst.helpers as csth
import libcst.matchers as cstm

from flext_infra import c, t


class FlextInfraUtilitiesRopeNestedClassMove:
    """Plan the source-level extraction of ``Outer.Inner`` without effects."""

    @classmethod
    def extract_nested_class(
        cls,
        source: str,
        member_path: Sequence[str],
        target_module: str,
    ) -> tuple[str, str]:
        """Split ``Outer[.Middle...].Inner`` out of ``source`` into its own module.

        ``member_path`` names the top-level family class, every enclosing
        nested class, and the member last. The source keeps the enclosing
        classes without the member, references it through an import of
        ``target_module``, and every fully qualified reference to it in the
        module becomes its bare name. The extracted module carries the member
        at top level with only the imports it uses.

        Returns:
            The updated source and the extracted module source.

        Raises:
            ValueError: When the path is shorter than two names, a class on it
                is absent, the direct parent would be left empty, or the member
                reads another member of its enclosing family or a module-local
                binding that the extracted module cannot import without a cycle.
            TypeError: When a rewrite does not preserve the class or module.

        """
        path = tuple(member_path)
        if not path[1:]:
            msg = f"nested member path needs a family and a member: {path}"
            raise ValueError(msg)
        qualified = ".".join(path)
        inner = path[-1]
        module = cst.parse_module(source)
        parent = cls._child_class(module, path[0], qualified)
        for name in path[1:-1]:
            parent = cls._child_class(parent, name, qualified)
        member = cls._child_class(parent, inner, qualified)
        remaining = tuple(
            statement for statement in parent.body.body if statement is not member
        )
        if all(cls._is_docstring(statement) for statement in remaining):
            msg = f"extracting {qualified} would leave {'.'.join(path[:-1])} empty"
            raise ValueError(msg)
        reference = cls._qualified_matcher(path)
        foreign = cls._foreign_family_references(member, path)
        if foreign:
            msg = (
                f"{qualified} references other {path[0]} members: {', '.join(foreign)}"
            )
            raise ValueError(msg)
        lifted = cstm.replace(member, reference, cst.Name(inner))
        if not isinstance(lifted, c.Infra.Cst.ClassDef):
            msg = f"extracting {qualified} did not yield a class"
            raise TypeError(msg)
        used = cls._loaded_names(lifted) - {inner}
        local = cls._module_local_bindings(module) & used
        if local:
            msg = f"{qualified} depends on module-local {', '.join(sorted(local))}"
            raise ValueError(msg)
        updated = cstm.replace(
            module.with_deep_changes(parent.body, body=remaining),
            reference,
            cst.Name(inner),
        )
        if not isinstance(updated, c.Infra.Cst.Module):
            msg = f"extracting {qualified} did not yield a module"
            raise TypeError(msg)
        return (
            cls._with_import(updated, target_module, inner).code,
            cls._extracted_module(module, lifted, used).code,
        )

    @staticmethod
    def _foreign_family_references(
        member: t.Infra.Cst.ClassDef, path: Sequence[str]
    ) -> Sequence[str]:
        """Return the other family members ``member`` reads by qualified name.

        Only outermost attribute chains rooted at the family class count; the
        member's own qualified name and its descendants are not foreign.

        Returns:
            The sorted foreign qualified names.

        """
        qualified = ".".join(path)
        attributes = tuple(
            found
            for found in cstm.findall(member, cstm.Attribute())
            if isinstance(found, c.Infra.Cst.Attribute)
        )
        objects = {id(found.value) for found in attributes}
        return tuple(
            sorted({
                name
                for found in attributes
                if id(found) not in objects
                and (name := csth.get_full_name_for_node_or_raise(found)).split(".")[0]
                == path[0]
                and name != qualified
                and not name.startswith(f"{qualified}.")
            })
        )

    @staticmethod
    def _child_class(
        owner: t.Infra.Cst.Module | t.Infra.Cst.ClassDef,
        name: str,
        qualified: str,
    ) -> t.Infra.Cst.ClassDef:
        """Return the class ``name`` declared directly in ``owner``'s body.

        Returns:
            The class statement, declared with a block body.

        Raises:
            ValueError: When ``owner`` declares no block-bodied class ``name``.

        """
        statements = (
            owner.body if isinstance(owner, c.Infra.Cst.Module) else owner.body.body
        )
        found = next(
            (
                statement
                for statement in statements
                if isinstance(statement, c.Infra.Cst.ClassDef)
                and statement.name.value == name
            ),
            None,
        )
        if found is None or not isinstance(found.body, c.Infra.Cst.IndentedBlock):
            msg = f"class {name} on {qualified} is not declared with a block body"
            raise ValueError(msg)
        return found

    @staticmethod
    def _qualified_matcher(path: Sequence[str]) -> t.Infra.Cst.AttributeMatcher:
        """Match the dotted reference ``path[0].path[1]...path[-1]``.

        Returns:
            The attribute-chain matcher for the fully qualified member.

        """
        matcher = cstm.Attribute(value=cstm.Name(path[0]), attr=cstm.Name(path[1]))
        for name in path[2:]:
            matcher = cstm.Attribute(value=matcher, attr=cstm.Name(name))
        return matcher

    @staticmethod
    def _is_docstring(
        statement: t.Infra.Cst.BaseStatement | t.Infra.Cst.BaseSmallStatement,
    ) -> bool:
        return cstm.matches(
            statement,
            cstm.SimpleStatementLine(
                body=[cstm.Expr(value=cstm.SimpleString() | cstm.ConcatenatedString())]
            ),
        )

    @staticmethod
    def _loaded_names(node: t.Infra.Cst.CSTNode) -> frozenset[str]:
        """Every bare name the node reads (attribute roots included).

        Returns:
            The names a module must bind for the node to resolve.

        """
        attributes = {
            id(found.attr)
            for found in cstm.findall(node, cstm.Attribute())
            if isinstance(found, c.Infra.Cst.Attribute)
        }
        return frozenset(
            found.value
            for found in cstm.findall(node, cstm.Name())
            if isinstance(found, c.Infra.Cst.Name) and id(found) not in attributes
        ) - frozenset(dir(builtins))

    @staticmethod
    def _import_statements(
        module: t.Infra.Cst.Module,
    ) -> tuple[t.Infra.Cst.SimpleStatementLine, ...]:
        return tuple(
            statement
            for statement in module.body
            if isinstance(statement, c.Infra.Cst.SimpleStatementLine)
            and all(
                isinstance(item, c.Infra.CST_IMPORT_TYPES) for item in statement.body
            )
        )

    @classmethod
    def _module_local_bindings(cls, module: t.Infra.Cst.Module) -> frozenset[str]:
        """Names the module binds other than by its top-level imports.

        Returns:
            Class, function and assignment names plus conditional imports.

        """
        imports = cls._import_statements(module)
        bound: set[str] = set()
        for statement in module.body:
            if statement in imports:
                continue
            if isinstance(statement, c.Infra.CST_DEFINITION_TYPES):
                bound.add(statement.name.value)
                continue
            bound.update(
                found.value
                for target in cstm.findall(
                    statement,
                    cstm.AssignTarget() | cstm.AnnAssign() | cstm.ImportAlias(),
                )
                for found in cstm.findall(target, cstm.Name())
                if isinstance(found, c.Infra.Cst.Name)
            )
        return frozenset(bound)

    @classmethod
    def _extracted_module(
        cls,
        module: t.Infra.Cst.Module,
        member: t.Infra.Cst.ClassDef,
        used: frozenset[str],
    ) -> t.Infra.Cst.Module:
        """Render the member at top level with only the imports it reads.

        Returns:
            The extracted module tree.

        """
        imports: list[t.Infra.Cst.SimpleStatementLine] = []
        for statement in cls._import_statements(module):
            kept = tuple(
                item
                for item in (cls._kept_import(raw, used) for raw in statement.body)
                if item is not None
            )
            if kept:
                imports.append(statement.with_changes(body=kept, leading_lines=()))
        # The extracted module keeps the source module's legal notice: the
        # paragraphs after its summary are carried verbatim.
        notice = (module.get_docstring() or "").partition("\n\n")[2]
        summary = cls._summary(member)
        docstring = f"{summary}\n\n{notice}\n" if notice else summary
        header = (
            cst.parse_statement(f'"""{docstring}"""\n'),
            cst.parse_statement(f"{c.Infra.FUTURE_ANNOTATIONS}\n").with_changes(
                leading_lines=(cst.EmptyLine(),)
            ),
        )
        export = cst.parse_statement(f'__all__: list[str] = ["{member.name.value}"]\n')
        blank = (cst.EmptyLine(), cst.EmptyLine())
        return module.with_changes(
            header=(),
            body=(
                *header,
                *(
                    statement.with_changes(leading_lines=(cst.EmptyLine(),))
                    if index == 0
                    else statement
                    for index, statement in enumerate(imports)
                ),
                member.with_changes(leading_lines=blank),
                export.with_changes(leading_lines=blank),
            ),
            footer=(),
        )

    @staticmethod
    def _kept_import(
        statement: t.Infra.Cst.BaseSmallStatement,
        used: frozenset[str],
    ) -> t.Infra.Cst.BaseSmallStatement | None:
        """Keep only the aliases of one import that the member reads.

        Returns:
            The narrowed import, or ``None`` when it binds nothing used.

        Raises:
            TypeError: When the import is a star import, which binds no
                declared alias to narrow.

        """
        if isinstance(statement, c.Infra.Cst.ImportFrom) and isinstance(
            statement.names, c.Infra.Cst.ImportStar
        ):
            msg = "a star import cannot be narrowed for an extracted member"
            raise TypeError(msg)
        if not isinstance(statement, c.Infra.CST_IMPORT_TYPES) or isinstance(
            statement.names, c.Infra.Cst.ImportStar
        ):
            return None
        aliases = tuple(
            alias
            for alias in statement.names
            if (
                alias.asname.name.value
                if alias.asname is not None
                and isinstance(alias.asname.name, c.Infra.Cst.Name)
                else csth.get_full_name_for_node_or_raise(alias.name).split(".")[0]
            )
            in used
        )
        if not aliases:
            return None
        return statement.with_changes(
            names=tuple(
                alias.with_changes(comma=cst.MaybeSentinel.DEFAULT) for alias in aliases
            )
        )

    @staticmethod
    def _summary(member: t.Infra.Cst.ClassDef) -> str:
        """First docstring line of the member, or a declaration summary.

        Returns:
            One sentence for the extracted module docstring.

        """
        docstring = member.get_docstring()
        first = docstring.splitlines()[0].strip() if docstring else ""
        return (first or f"{member.name.value} declaration.").replace('"""', "'''")

    @classmethod
    def _with_import(
        cls, module: t.Infra.Cst.Module, target_module: str, name: str
    ) -> t.Infra.Cst.Module:
        """Bind ``name`` from ``target_module`` after the last top-level import.

        Returns:
            The module importing the extracted member.

        """
        statement = cst.parse_statement(f"from {target_module} import {name}\n")
        imports = cls._import_statements(module)
        position = (
            max(module.body.index(item) for item in imports) + 1 if imports else 0
        )
        return module.with_changes(
            body=(*module.body[:position], statement, *module.body[position:])
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeNestedClassMove"]
