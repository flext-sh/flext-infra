"""Native alias identity remains available inside its declaring class scope."""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import u
from tests import tm


class TestsFlextInfraProtocolAliasLexicalScope:
    """Resolve chained generic aliases through the real Rope boundary."""

    @staticmethod
    def test_nested_alias_keeps_its_generic_alias_owner(tmp_path: Path) -> None:
        """A class-owned alias retains the identity of its sibling generic alias."""
        source = (
            "from collections.abc import Sequence\n"
            "class Types:\n"
            "    type SequenceOf[ItemT] = Sequence[ItemT]\n"
            "    type StrSequence = SequenceOf[str]\n"
        )
        path = tmp_path / "aliases.py"
        path.write_text(source, encoding="utf-8")
        with u.Infra.open_project(tmp_path) as project:
            module = u.Infra.build_string_module(
                project,
                source,
                resource=tm.not_none(u.Infra.fetch_python_resource(project, path)),
            )
            binding = tm.not_none(
                u.Infra.expression_name(module.get_scope(), "Types.StrSequence"),
            )
            declaration, scope = tm.not_none(
                u.Infra.annotation_alias_definition(binding),
            )
            tm.that(declaration.name.id, eq="StrSequence")
            annotation = declaration.value
            tm.that(isinstance(annotation, ast.Subscript), eq=True)
            if not isinstance(annotation, ast.Subscript):
                msg = "the fixture declares a parameterized alias"
                raise TypeError(msg)
            sibling = tm.not_none(u.Infra.resolve_symbol(scope, annotation.value))
            resolved = u.Infra.annotation_alias_definition(sibling)
            tm.that(
                resolved is not None,
                eq=True,
                msg=(
                    "native alias identity was lost: "
                    f"expression={ast.unparse(annotation)}; "
                    f"name={type(sibling).__name__}; "
                    f"{sibling.get_definition_location()!r}; "
                    f"scope={scope.get_kind()}"
                ),
            )
