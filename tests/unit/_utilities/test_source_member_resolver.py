"""Captured member resolution and ordering through the public native boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from tests import c, m, tm, u


class TestsFlextInfraSourceMemberResolver:
    """A bound source resolver retains its capture across member and C3 queries."""

    @staticmethod
    def test_installed_pydantic_import_keeps_the_exact_declaring_class(
        tmp_path: Path,
    ) -> None:
        """An absent external lexical export retains its real native import origin."""
        with closing(u.Infra.init_rope_project(tmp_path)) as project:
            binding = u.Infra.source_member_binding(
                project,
                m.Infra.SourceClassReference(
                    target="pydantic",
                    attributes=("BaseModel",),
                    qualified_base="pydantic.BaseModel",
                ),
            )
            declared = u.Infra.require_semantic_module(
                project.get_module("pydantic.main")
            ).get_attributes()["BaseModel"]
            tm.that(binding.get_object() is declared.get_object(), eq=True)
            tm.that(
                binding.get_definition_location(),
                eq=declared.get_definition_location(),
            )

    @staticmethod
    def test_unresolved_external_binding_cannot_reuse_an_earlier_import(
        tmp_path: Path, installed_dependency_path: Path
    ) -> None:
        """A completed unknown assignment never forwards the stale native import."""
        (installed_dependency_path / "unresolved_provider.py").write_text(
            "from pydantic import BaseModel\nBaseModel = None\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as project,
            pytest.raises(
                ValueError,
                match=(
                    r"Unresolved declared provider base: "
                    r"unresolved_provider\.BaseModel"
                ),
            ),
        ):
            u.Infra.source_member_binding(
                project,
                m.Infra.SourceClassReference(
                    target="unresolved_provider",
                    attributes=("BaseModel",),
                    qualified_base="unresolved_provider.BaseModel",
                ),
            )

    @staticmethod
    def test_bound_source_resolver_reads_a_member_before_ordering_classes(
        tmp_path: Path,
    ) -> None:
        """Keep capture ownership, C3 order and competing-owner rejection intact."""
        source = tmp_path / "resolver_port.py"
        content = (
            "from builtins import object as c\n"
            "class Base:\n"
            "    @staticmethod\n"
            "    def item() -> str:\n"
            '        return "shared"\n'
            "class Child(Base): pass\n"
            "c = Child\n"
        )
        sources = {"resolver_port": (source, content)}
        base = m.Infra.SourceClassReference(
            target="resolver_port",
            attributes=("Base",),
            qualified_base="resolver_port.Base",
        )
        child = m.Infra.SourceClassReference(
            target="resolver_port",
            attributes=("Child",),
            qualified_base="resolver_port.Child",
        )
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(u.Infra.snapshot_project(original, {source: content})) as project,
        ):
            resolver_factory = u.Infra.source_member_resolver_factory(
                project, sources=sources
            )
            sources.clear()
            resolver = resolver_factory()
            member = resolver(f"{child.qualified_base}.item")
            tm.that(
                u.Infra.require_source_object(member.get_object(), "item").get_name(),
                eq="item",
            )
            tm.that(
                resolver_factory().class_order((child, base)),
                eq=(child.qualified_base, base.qualified_base),
            )
            tm.that(
                u.Infra.require_class_object(
                    resolver_factory()(child).get_object(), child.qualified_base
                ).get_name(),
                eq="Child",
            )
            published = m.Infra.SourceClassReference(
                target=child.target,
                attributes=("c",),
                qualified_base=f"{child.target}.c",
            )
            for capture in (False, True):
                completed = u.Infra.source_member_resolver(
                    project,
                    sources={"resolver_port": (source, content)} if capture else {},
                )
                tm.that(
                    completed(published).get_object() is completed(child).get_object(),
                    eq=True,
                )
            names = ("resolver_first", "resolver_second")
            for order in (names, tuple(reversed(names))):
                ambiguous = u.Infra.source_member_resolver(
                    project,
                    sources=dict.fromkeys(order, (source, content)),
                )
                with pytest.raises(
                    ValueError, match="Ambiguous captured source owner:"
                ) as failure:
                    ambiguous(child)
                tm.that(
                    str(failure.value),
                    eq=f"Ambiguous captured source owner: {source}",
                )
