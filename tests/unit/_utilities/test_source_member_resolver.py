"""Captured member resolution and ordering through the public native boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from tests import m, tm, u


class TestsFlextInfraSourceMemberResolver:
    """A bound source resolver retains its capture across member and C3 queries."""

    @staticmethod
    def test_bound_source_resolver_reads_a_member_before_ordering_classes(
        tmp_path: Path,
    ) -> None:
        """One captured view resolves an inherited member and orders its owners."""
        source = tmp_path / "resolver_port.py"
        content = (
            "class Base:\n"
            "    @staticmethod\n"
            "    def item() -> str:\n"
            '        return "shared"\n'
            "class Child(Base): pass\n"
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
