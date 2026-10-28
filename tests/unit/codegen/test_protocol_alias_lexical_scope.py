"""Native alias identity remains available inside its declaring class scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import ast
from pathlib import Path

from flext_infra import u
from tests import tm


class TestsFlextInfraProtocolAliasLexicalScope:
    """Resolve chained generic aliases through the real Rope boundary."""

    @staticmethod
    def test_nested_alias_keeps_its_generic_alias_owner(tmp_path: Path) -> None:
        """A class-owned alias retains the identity of its sibling generic alias.

        Raises:
            TypeError: When the fixture alias is not a parameterized subscript.

        """
        source = (
            "from collections.abc import Sequence\n"
            "class Types:\n"
            "    type Sequence[ItemT] = Sequence[ItemT]\n"
            "    type Sequence[str] = Sequence[str]\n"
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
                u.Infra.expression_name(module.get_scope(), "Types.Sequence[str]"),
            )
            declaration, scope = tm.not_none(
                u.Infra.annotation_alias_definition(binding),
            )
            tm.that(declaration.name.id, eq="Sequence[str]")
            annotation = declaration.value
            tm.ok(isinstance(annotation, ast.Subscript))
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
