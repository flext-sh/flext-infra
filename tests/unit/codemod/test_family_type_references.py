"""Public family cutovers preserve quoted type identities and literal payloads.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFamilyTypeReferences:
    """Exercise the real Rope graph for generic bases and deferred annotations."""

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        [
            "VALUE = 'payload'\n",
            "def identity(value: int) -> int:\n    return value\n",
            (
                "from typing import Annotated, Literal\n"
                "value: Literal['payload']\n"
                "other: Annotated[int, 'metadata']\n"
            ),
        ],
    )
    def test_non_type_strings_do_not_become_quoted_references(
        tmp_path: Path, source: str
    ) -> None:
        """Empty, unquoted and protected payloads retain their native identities."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            resource = rope.resource(path)
            tm.that(resource, none=False)
            module = u.Infra.resolve_pymodule(rope.rope_project, resource)
            tm.that(
                tuple(
                    u.Infra.scoped_quoted_type_references(
                        source, rope.rope_project, module
                    )
                ),
                empty=True,
            )

    @staticmethod
    @pytest.mark.parametrize("label", ["é", "payload; kept"])
    def test_semicolon_members_keep_values_and_uninitialized_annotations(
        tmp_path: Path, label: str
    ) -> None:
        """Every simple binding nests without inventing an annotation value."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "class Public:\n    pass\n\n"
            f"LABEL = {label!r}; item: str\n\n"
            "__all__ = ['Public']\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
            updated = planned[0].updated_source
            tm.that(updated, has="    LABEL:")
            tm.that(updated, has=f"ClassVar[str] = {label!r}; item: str")
            compile(updated, str(path), "exec")
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={path: updated},
                )
            )
            tm.that(remaining, empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_quoted_types_follow_symbols_without_rewriting_literal_homonyms(
        tmp_path: Path,
    ) -> None:
        """Test quoted types follow symbols without rewriting literal homonyms."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        family = package / directory
        family.mkdir()
        (family / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        (package / "entities.py").write_text(
            "class Container[T]:\n    pass\n\n"
            "class Other:\n    class Domain:\n        class Item:\n            pass\n",
            encoding="utf-8",
        )
        owner = f"{u.derive_class_stem(root.name)}ModelsPayload"
        path = family / "payload.py"
        source = (
            f"from {package.name}.entities import Container\n\n"
            f"class {owner}:\n"
            "    class Domain:\n"
            "        class Item:\n            pass\n"
            f'        class Builder(Container["{owner}.Domain.Item"]):\n'
            "            pass\n"
            f"\n__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        consumer = package / "consumer.py"
        references = (
            "from __future__ import annotations\n"
            "from typing import Annotated as Meta, Literal as Choice\n"
            f"from {package.name}.{directory}.payload import {owner} as Part\n"
            f"from {package.name}.entities import Container, Other\n\n"
            "class Public(Part):\n    pass\n\n"
            'class Specialized(Container["Part.Domain.Item"]):\n    pass\n\n'
            'class Generic[T: "Part.Domain.Item" = "Part.Domain.Item"]:\n'
            "    pass\n\n"
            "LABEL = 'é'; item: \"Public.Domain.Item\"\n"
            'items: list["Part.Domain.Item"]\n'
            'meta: Meta["Part.Domain.Item", "Part.Domain.Item"]\n'
            'choice: Choice["Part.Domain.Item"]\n'
            'unrelated: "Other.Domain.Item"\n'
            'type Items = list["Part.Domain.Item"]\n'
            'TEXT = "Part.Domain.Item"\n\n'
            "__all__ = ['Public']\n\n"
            'def convert(value: "Part.Domain.Item" = "Part.Domain.Item")'
            ' -> "Part.Domain.Item":\n'
            "    Part = Other\n"
            '    local: "Part.Domain.Item"\n'
            "    return Part.Domain.Item()\n"
        )
        consumer.write_text(references, encoding="utf-8")
        sources = {path: source, consumer: references}
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            proposed = dict(sources)
            proposed.update({edit.file_path: edit.updated_source for edit in planned})
            tm.that(proposed[path], has=f"Container['{owner}.DomainItem']")
            for preserved in (
                'choice: Choice["Part.Domain.Item"]',
                'unrelated: "Other.Domain.Item"',
                '    local: "Part.Domain.Item"',
            ):
                tm.that(proposed[consumer], has=preserved)
            tm.that(
                TestsFlextInfraFamilyTypeReferences._string_assignments(
                    proposed[consumer]
                ),
                eq=TestsFlextInfraFamilyTypeReferences._string_assignments(references),
            )
            for rewritten in (
                "Container['Part.DomainItem']",
                "class Generic[T: 'Part.DomainItem' = 'Part.DomainItem']:",
                "item: 'Public.DomainItem'",
                "items: list['Part.DomainItem']",
                "meta: Meta['Part.DomainItem', \"Part.Domain.Item\"]",
                "type Items = list['Part.DomainItem']",
                (
                    "def convert(value: 'Part.DomainItem' = \"Part.Domain.Item\")"
                    " -> 'Part.DomainItem':"
                ),
            ):
                tm.that(proposed[consumer], has=rewritten)
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources=proposed,
                ),
            )
            tm.that(remaining, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(consumer.read_text(encoding="utf-8"), eq=references)

    @staticmethod
    def _string_assignments(source: str) -> t.StrMapping:
        """Read string payloads independently of assignment annotations or layout.

        Args:
            source: The Python source code to analyze.

        Returns:
            A mapping from variable names to their string values.

        """
        return {
            target.id: node.value.value
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            if isinstance(target, ast.Name)
        }
