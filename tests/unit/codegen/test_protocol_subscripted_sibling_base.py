"""A subscripted base naming a sibling model projects a bare sibling argument.

A protocol class base evaluates in its holder's class body, before the holder
name is bound. A model ``Batch(Envelope[Item])`` whose ``Item`` is mirrored in
the same holder must project ``Envelope[Item]``, never
``Envelope[Holder.Item]``, which raises ``NameError`` at import.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from tests import tm, u


class TestsProtocolSubscriptedSiblingBase:
    """Exercise the public projection on a physical source tree."""

    _HOLDER: ClassVar[str] = "FlextInfraProtocolsEnvelope"

    _SOURCES: ClassVar[Mapping[str, str]] = {
        "models.py": ("class FlextInfraModels: pass\nm = FlextInfraModels\n"),
        "protocols.py": (
            "from flext_cli import FlextCliProtocols\n"
            "class FlextInfraProtocols(FlextCliProtocols): pass\n"
            "p = FlextInfraProtocols\n"
        ),
        "_models/envelope.py": (
            "from __future__ import annotations\n"
            "from pydantic import BaseModel\n"
            "class Envelope[ItemT](BaseModel):\n"
            "    item: ItemT\n"
            "class Item(BaseModel):\n"
            "    name: str\n"
            "class Batch(Envelope[Item]):\n"
            "    size: int\n"
        ),
    }

    @classmethod
    def test_sibling_type_argument_is_spelled_bare(cls, tmp_path: Path) -> None:
        """The projected base reads the sibling contract already bound."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-infra", package_name="flext_infra"
        )
        for relative, source in cls._SOURCES.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = planned[(package / "_protocols" / "envelope.py").relative_to(root)]
        batch = next(
            node
            for node in ast.walk(ast.parse(generated))
            if isinstance(node, ast.ClassDef) and node.name == "Batch"
        )
        bases = [ast.unparse(base) for base in batch.bases]
        tm.that(bases[0], eq="Envelope[Item]")
        tm.ok(not any(cls._HOLDER in base for base in bases))
