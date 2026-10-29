"""Native model ancestry projected through the public protocol owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra
from tests import p, tm, u


class TestsModelProtocolNativeMro:
    """Compare generated contracts with the real Pydantic consumer."""

    @staticmethod
    @pytest.mark.parametrize("bases", ["Left, Right", "Right, Left"])
    def test_diamond_override_matches_the_runtime_model(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        bases: str,
    ) -> None:
        """Base order changes effective fields identically in model and protocol."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                "from pydantic import BaseModel\n"
                "class Models:\n"
                "    class Domain:\n"
                "        class Root(BaseModel):\n"
                "            marker: float\n"
                "        class Left(Root):\n"
                "            marker: int\n"
                "        class Right(Root):\n"
                "            marker: str\n"
                f"        class Payload({bases}):\n"
                "            title: str\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n"
                "    class Domain:\n"
                "        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "consumer.py": (
                "from __future__ import annotations\n"
                f"from {package.name}.protocols import p\n"
                "def consume(payload: p.Domain.Payload) -> str:\n"
                "    return payload.title\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            projected = u.Infra.protocol_model_sources(workspace)
        tm.that(projected, empty=False)
        for path, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, source))
        modules = tuple(
            ".".join((root / path).relative_to(package.parent).with_suffix("").parts)
            for path in projected
        )
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"modules = [importlib.import_module(name) for name in {modules!r}]\n"
            "contracts = [member for module in modules\n"
            "    for owner in vars(module).values() if isinstance(owner, type)\n"
            "    for member in vars(owner).values() if isinstance(member, type)\n"
            "    and is_protocol(member) and 'marker' in get_type_hints(member)]\n"
            "tm.that(len(contracts), eq=1)\n"
            "hints = get_type_hints(contracts[0])\n"
            "model = m.Domain.Payload\n"
            "tm.that(set(hints), eq=set(model.model_fields))\n"
            "for name, field in model.model_fields.items():\n"
            "    tm.that(hints[name], eq=field.annotation)\n"
            "payload = model(marker=model.model_fields['marker'].annotation('17'),\n"
            "                title='projected')\n"
            "tm.that(type(payload.marker), eq=hints['marker'])\n"
            "tm.ok(isinstance(payload, contracts[0]))\n",
            cwd=root,
        )
