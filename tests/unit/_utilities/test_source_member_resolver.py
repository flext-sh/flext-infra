"""Captured member resolution and ordering through the public native boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from tests import m, tm, u


class TestsFlextInfraSourceMemberResolver:
    """A bound source resolver retains its capture across member and C3 queries."""

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
            resolver = u.Infra.source_member_resolver(project, sources=sources)
            sources.clear()
            member = resolver(f"{child.qualified_base}.item")
            tm.that(
                u.Infra.require_source_object(member.get_object(), "item").get_name(),
                eq="item",
            )
            tm.that(
                resolver.class_order((child, base)),
                eq=(child.qualified_base, base.qualified_base),
            )
            tm.that(
                u.Infra.require_class_object(
                    resolver(child).get_object(), child.qualified_base
                ).get_name(),
                eq="Child",
            )
            published = m.Infra.SourceClassReference(
                target=child.target,
                attributes=("c",),
                qualified_base=f"{child.target}.c",
            )
            for captured in ({}, {"resolver_port": (source, content)}):
                completed = u.Infra.source_member_resolver(project, sources=captured)
                tm.that(
                    completed(published).get_object()
                    is completed(child).get_object(),
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
