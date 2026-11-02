"""Public family cutovers preserve quoted type identities and literal payloads.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import runpy
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFamilyTypeReferences:
    """Exercise the real Rope graph for generic bases and deferred annotations."""

    @staticmethod
    @pytest.mark.parametrize("protocol_imported", [False, True])
    def test_nested_result_regions_publish_one_native_protocol_cutover(
        tmp_path: Path,
        *,
        protocol_imported: bool,
    ) -> None:
        """Nested and declared regions produce disjoint, executable Rope edits."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        (package / c.Infra.INIT_PY).write_text(
            "from flext_cli import p\n", encoding=c.DEFAULT_ENCODING
        )
        path = package / "consumer.py"
        imports = "m, p, r, u" if protocol_imported else "m, r, u"
        source = (
            "from pathlib import Path\n"
            f"from flext_cli import {imports}\n"
            "state = u.Cli.atomic_read_binary_file_state(\n"
            "    Path(__file__).resolve(), required=True).unwrap()\n"
            "declared: r[m.Cli.AtomicFileState] = (\n"
            "    r[m.Cli.AtomicFileState].ok(state))\n"
            "nested = r[tuple[m.Cli.AtomicFileState, r[m.Cli.AtomicFileState]]]\n"
            "constructor = m.Cli.AtomicFileState\n"
            "literal = 'm.Cli.AtomicFileState'\n"
            "parsed = m.Cli.AtomicFileState.model_validate_json(\n"
            "    state.model_dump_json())\n"
            "assert declared.value is state\n"
            "assert isinstance(declared.value, p.Cli.AtomicFileState)\n"
            "assert constructor is m.Cli.AtomicFileState\n"
            "assert literal == 'm.Cli.AtomicFileState'\n"
            "assert parsed == state\n"
        )
        if protocol_imported:
            source += "retained: p.Cli.AtomicFileState = state\n"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rule = m.Infra.RopeContractRule(
            id="result-runtime-protocol-owner",
            pattern="${receiver}.${member}",
            goal="p.Cli.${member}",
            arguments={},
            annotation_member_source="m.Cli",
            bindings={
                "m.Cli": "flext_cli.models.FlextCliModels.Cli",
                "p.Cli": "flext_cli.protocols.FlextCliProtocols.Cli",
            },
            annotation_only=True,
            scope=m.Infra.RopeContractScope(
                targets=(
                    m.Infra.RopeContractScopeTarget(
                        distribution=root.name,
                        module=f"{package.name}.consumer",
                    ),
                )
            ),
        )
        with infra.rope_workspace(root) as rope:
            (edit,) = tm.ok(u.Infra.plan_contract_rules(rope, {path: source}, (rule,)))
            tm.that(
                tm.ok(
                    u.Infra.plan_contract_rules(
                        rope, {path: edit.updated_source}, (rule,)
                    )
                ),
                empty=True,
            )
        tm.that(edit.updated_source, has="declared: r[p.Cli.AtomicFileState]")
        tm.that(
            edit.updated_source,
            has="nested = r[tuple[p.Cli.AtomicFileState, r[p.Cli.AtomicFileState]]]",
        )
        tm.that(edit.updated_source, has="constructor = m.Cli.AtomicFileState")
        tm.that(edit.updated_source, has="m.Cli.AtomicFileState.model_validate_json(")
        tm.that(edit.updated_source, has="literal = 'm.Cli.AtomicFileState'")
        if protocol_imported:
            tm.that(edit.updated_source, has="retained: p.Cli.AtomicFileState = state")
        candidate = package / "candidate.py"
        candidate.write_text(edit.updated_source, encoding=c.DEFAULT_ENCODING)
        runpy.run_path(str(candidate))
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (
                "from flext_core import r\nvalue = r['Domain.Item']\n",
                ("Domain.Item",),
            ),
            (
                (
                    "from flext_core.result import FlextResult as Outcome\n"
                    "value = Outcome[tuple['Domain.Item', int]]\n"
                ),
                ("Domain.Item",),
            ),
            (
                (
                    "from flext_core import r\n"
                    "def consume(r):\n    return r['Domain.Item']\n"
                ),
                (),
            ),
            (
                (
                    "from flext_core import r\n"
                    "def consume():\n    r = list\n    return r['Domain.Item']\n"
                ),
                (),
            ),
            ("value = list['Domain.Item']\n", ()),
            (
                "from flext_core import r\nvalue = r[str].ok('Domain.Item')\n",
                (),
            ),
            (
                (
                    "from typing import Annotated\nfrom flext_core import m, r\n"
                    "value = r[Annotated[str, m.Field(description='Domain.Item')]]\n"
                ),
                (),
            ),
        ],
    )
    def test_result_runtime_type_arguments_keep_native_identity(
        tmp_path: Path, source: str, expected: tuple[str, ...]
    ) -> None:
        """Only real Core result subscriptions contribute quoted type arguments."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            resource = tm.not_none(rope.resource(path))
            module = u.Infra.resolve_pymodule(rope.rope_project, resource)
            references = u.Infra.scoped_quoted_type_references(
                source, rope.rope_project, module
            )
            tm.that(
                tuple(expression for expression, _scope, _line in references),
                eq=expected,
            )

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
            (
                "from typing import Annotated\n"
                "def consume(value: Annotated[str, 'Domain.Item']):\n"
                "    Annotated = list\n"
            ),
            (
                "from typing import Annotated as Meta, Literal as Choice\n"
                "def consume[T](value: Meta[T, 'Domain.Item'])"
                " -> Choice['Domain.Item']:\n"
                "    Meta = list\n"
                "    Choice = list\n"
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
            resource = tm.not_none(rope.resource(path))
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
    def _models_family(package: Path) -> tuple[str, Path]:
        """Create the declared models family directory with its package init.

        Returns:
            The family directory name and its path.

        """
        directory = u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        family = package / directory
        family.mkdir()
        (family / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        return directory, family

    @staticmethod
    def _consumer_references(package_name: str, directory: str, owner: str) -> str:
        """Return the consumer source exercising quoted type references.

        Returns:
            The consumer module source.

        """
        return (
            "from __future__ import annotations\n"
            "from typing import Annotated as Meta, Literal as Choice\n"
            f"from {package_name}.{directory}.payload import {owner} as Part\n"
            f"from {package_name}.entities import Container, Other\n\n"
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
            '\ndef header[T](value: Meta["Part.Domain.Item", "Part.Domain.Item"])'
            ' -> Choice["Part.Domain.Item"]:\n'
            "    Meta = list\n"
            "    Choice = list\n"
            "    return value\n"
            '\ndef inverse(value: Container["Part.Domain.Item"]):\n'
            "    from typing import Annotated as Container\n"
            "    return value\n"
        )

    @staticmethod
    def test_quoted_types_follow_symbols_without_rewriting_literal_homonyms(
        tmp_path: Path,
    ) -> None:
        """Test quoted types follow symbols without rewriting literal homonyms."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory, family = TestsFlextInfraFamilyTypeReferences._models_family(package)
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
        references = TestsFlextInfraFamilyTypeReferences._consumer_references(
            package.name, directory, owner
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
            TestsFlextInfraFamilyTypeReferences._assert_string_payloads_preserved(
                references, proposed[consumer]
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
                (
                    "def header[T](value: Meta['Part.DomainItem',"
                    ' "Part.Domain.Item"]) -> Choice["Part.Domain.Item"]:'
                ),
                "def inverse(value: Container['Part.DomainItem']):",
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
    def _assert_string_payloads_preserved(original: str, candidate: str) -> None:
        """Require the candidate to bind every module string payload verbatim."""
        payloads = TestsFlextInfraFamilyTypeReferences._string_assignments(original)
        tm.that({name for name, _literal in payloads}, eq={"LABEL", "TEXT"})
        tm.that(
            TestsFlextInfraFamilyTypeReferences._string_assignments(candidate),
            eq=payloads,
        )

    @staticmethod
    def _string_assignments(source: str) -> tuple[tuple[str, str | None], ...]:
        """Read module-level string payload bindings with their exact spelling.

        Args:
            source: The module source whose top-level bindings are read.

        Returns:
            Bound names and their literal source segments, in source order.

        """
        bindings: list[tuple[str, str | None]] = []
        target: ast.expr
        value: ast.expr | None
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign):
                target, value = node.target, node.value
            else:
                continue
            if (
                isinstance(target, ast.Name)
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                bindings.append((target.id, ast.get_source_segment(source, value)))
        return tuple(bindings)
