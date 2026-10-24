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
        member_path: t.StrPair,
        target_module: str,
    ) -> t.StrPair:
        """Split ``Outer.Inner`` out of ``source`` into its own module source.

        The source keeps ``Outer`` without ``Inner``, references ``Inner``
        through an import of ``target_module``, and every ``Outer.Inner`` in
        the module becomes ``Inner``. The extracted module carries ``Inner``
        at top level with only the imports it uses.

        Returns:
            The updated source and the extracted module source.

        Raises:
            ValueError: When the owner or member is absent, the owner would be
                left empty, or the member depends on another ``Outer`` member
                or on a module-local binding that the extracted module cannot
                import without a cycle.
            TypeError: When a rewrite does not preserve the class or module.

        """
        outer, inner = member_path
        module = cst.parse_module(source)
        owner = cls._top_level_class(module, outer)
        member = next(
            (
                statement
                for statement in owner.body.body
                if isinstance(statement, cst.ClassDef) and statement.name.value == inner
            ),
            None,
        )
        if member is None:
            msg = f"nested class {outer}.{inner} is not declared"
            raise ValueError(msg)
        remaining = tuple(
            statement for statement in owner.body.body if statement is not member
        )
        if all(cls._is_docstring(statement) for statement in remaining):
            msg = f"extracting {outer}.{inner} would leave {outer} empty"
            raise ValueError(msg)
        foreign = cstm.findall(
            member,
            cstm.Attribute(value=cstm.Name(outer), attr=~cstm.Name(inner)),
        )
        if foreign:
            msg = f"{outer}.{inner} references other {outer} members"
            raise ValueError(msg)
        reference = cstm.Attribute(value=cstm.Name(outer), attr=cstm.Name(inner))
        lifted = cstm.replace(member, reference, cst.Name(inner))
        if not isinstance(lifted, cst.ClassDef):
            msg = f"extracting {outer}.{inner} did not yield a class"
            raise TypeError(msg)
        used = cls._loaded_names(lifted) - {inner}
        local = cls._module_local_bindings(module) & used
        if local:
            msg = f"{outer}.{inner} depends on module-local {', '.join(sorted(local))}"
            raise ValueError(msg)
        updated = cstm.replace(
            module.with_deep_changes(owner.body, body=remaining),
            reference,
            cst.Name(inner),
        )
        if not isinstance(updated, cst.Module):
            msg = f"extracting {outer}.{inner} did not yield a module"
            raise TypeError(msg)
        return (
            cls._with_import(updated, target_module, inner).code,
            cls._extracted_module(module, lifted, used).code,
        )

    @staticmethod
    def _top_level_class(module: cst.Module, name: str) -> cst.ClassDef:
        owner = next(
            (
                statement
                for statement in module.body
                if isinstance(statement, cst.ClassDef) and statement.name.value == name
            ),
            None,
        )
        if owner is None or not isinstance(owner.body, cst.IndentedBlock):
            msg = f"top-level class {name} is not declared with a block body"
            raise ValueError(msg)
        return owner

    @staticmethod
    def _is_docstring(statement: cst.BaseStatement | cst.BaseSmallStatement) -> bool:
        return cstm.matches(
            statement,
            cstm.SimpleStatementLine(
                body=[cstm.Expr(value=cstm.SimpleString() | cstm.ConcatenatedString())]
            ),
        )

    @staticmethod
    def _loaded_names(node: cst.CSTNode) -> frozenset[str]:
        """Every bare name the node reads (attribute roots included).

        Returns:
            The names a module must bind for the node to resolve.

        """
        attributes = {
            id(found.attr)
            for found in cstm.findall(node, cstm.Attribute())
            if isinstance(found, cst.Attribute)
        }
        return frozenset(
            found.value
            for found in cstm.findall(node, cstm.Name())
            if isinstance(found, cst.Name) and id(found) not in attributes
        ) - frozenset(dir(builtins))

    @staticmethod
    def _import_statements(module: cst.Module) -> tuple[cst.SimpleStatementLine, ...]:
        return tuple(
            statement
            for statement in module.body
            if isinstance(statement, cst.SimpleStatementLine)
            and all(
                isinstance(item, cst.Import | cst.ImportFrom) for item in statement.body
            )
        )

    @classmethod
    def _module_local_bindings(cls, module: cst.Module) -> frozenset[str]:
        """Names the module binds other than by its top-level imports.

        Returns:
            Class, function and assignment names plus conditional imports.

        """
        imports = cls._import_statements(module)
        bound: set[str] = set()
        for statement in module.body:
            if statement in imports:
                continue
            if isinstance(statement, cst.ClassDef | cst.FunctionDef):
                bound.add(statement.name.value)
                continue
            bound.update(
                found.value
                for target in cstm.findall(
                    statement,
                    cstm.AssignTarget() | cstm.AnnAssign() | cstm.ImportAlias(),
                )
                for found in cstm.findall(target, cstm.Name())
                if isinstance(found, cst.Name)
            )
        return frozenset(bound)

    @classmethod
    def _extracted_module(
        cls,
        module: cst.Module,
        member: cst.ClassDef,
        used: frozenset[str],
    ) -> cst.Module:
        """Render the member at top level with only the imports it reads.

        Returns:
            The extracted module tree.

        """
        imports: list[cst.SimpleStatementLine] = []
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
        statement: cst.BaseSmallStatement,
        used: frozenset[str],
    ) -> cst.BaseSmallStatement | None:
        """Keep only the aliases of one import that the member reads.

        Returns:
            The narrowed import, or ``None`` when it binds nothing used.

        Raises:
            TypeError: When the import is a star import, which binds no
                declared alias to narrow.

        """
        if isinstance(statement, cst.ImportFrom) and isinstance(
            statement.names, cst.ImportStar
        ):
            msg = "a star import cannot be narrowed for an extracted member"
            raise TypeError(msg)
        if not isinstance(statement, cst.Import | cst.ImportFrom) or isinstance(
            statement.names, cst.ImportStar
        ):
            return None
        aliases = tuple(
            alias
            for alias in statement.names
            if (
                alias.asname.name.value
                if alias.asname is not None and isinstance(alias.asname.name, cst.Name)
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
    def _summary(member: cst.ClassDef) -> str:
        """First docstring line of the member, or a declaration summary.

        Returns:
            One sentence for the extracted module docstring.

        """
        docstring = member.get_docstring()
        first = docstring.splitlines()[0].strip() if docstring else ""
        return (first or f"{member.name.value} declaration.").replace('"""', "'''")

    @classmethod
    def _with_import(
        cls, module: cst.Module, target_module: str, name: str
    ) -> cst.Module:
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
