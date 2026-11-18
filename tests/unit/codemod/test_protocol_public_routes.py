"""Native protocol routes retain deep aliases and terminate namespace cycles.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import infra
from tests import p, tm, u


class TestsFlextInfraProtocolPublicRoutes:
    """Exercise complete published paths through the public census entrypoint."""

    @staticmethod
    def test_deep_routes_aliases_and_cycles(
        tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """Census records simple public paths and excludes unpublished contracts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "__init__.py": "from .protocols import p\n__all__ = ['p']\n",
            package / "_protocols" / "__init__.py": "__all__ = []\n",
            package / "_protocols" / "contracts.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class Contracts:\n"
                "    @runtime_checkable\n"
                "    class Target(Protocol):\n"
                "        def execute(self) -> str: ...\n"
                "    @runtime_checkable\n"
                "    class Unpublished(Protocol):\n"
                "        def hidden(self) -> None: ...\n"
                "__all__ = ['Contracts']\n"
            ),
            package / "protocols.py": (
                "from ._protocols.contracts import Contracts\n"
                "class Protocols:\n"
                "    Direct = Contracts.Target\n"
                "    class Nested:\n"
                "        class One:\n"
                "            class Two:\n"
                "                class Three:\n"
                "                    Target = Contracts.Target\n"
                "Protocols.Nested.One.Two.Three.Loop = Protocols.Nested\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            census = u.Infra.protocol_contract_census(workspace, sources=sources)
        contracts = {row.source_class: row for row in census.contracts}
        tm.that(
            set(contracts["Contracts.Target"].public_routes),
            eq={"p.Direct", "p.Nested.One.Two.Three.Target"},
        )
        tm.that(len(contracts["Contracts.Target"].public_routes), eq=2)
        tm.that(contracts["Contracts.Unpublished"].public_routes, eq=())
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.protocols import p\n"
            "assert p.Direct is p.Nested.One.Two.Three.Target\n"
            "assert p.Nested.One.Two.Three.Loop is p.Nested\n",
            cwd=root,
        )
