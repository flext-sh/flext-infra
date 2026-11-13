"""A facade's generic member publication resolves to the class it names.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFacadePublishedObject:
    """``BaseModel: TypeAlias = Part.BaseModel`` keeps the port reachable."""

    @staticmethod
    def test_published_port_resolves_its_upstream_facade(tmp_path: Path) -> None:
        """Port lookup through a ``TypeAlias`` publication elects its facade.

        Premise: flext-core's ``p`` publishes
        ``BaseModel: TypeAlias = FlextProtocolsPydantic.BaseModel``. Rope reads
        that attribute from its annotation, so the upstream facade that
        exposes the copy port was never elected and the model-protocol stage
        raised "protocol facade chain has no upstream owner of BaseModel".
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = root / c.Infra.DEFAULT_SRC_DIR / "acme_upstream"
        sources = {
            upstream / c.Infra.INIT_PY: (
                "from acme_upstream.protocols import AcmeUpstreamProtocols, p\n"
                "__all__ = ['AcmeUpstreamProtocols', 'p']\n"
            ),
            upstream / "_protocols" / c.Infra.INIT_PY: "",
            upstream / "_protocols" / "pydantic.py": (
                "from typing import Protocol, runtime_checkable\n\n\n"
                "class AcmeUpstreamProtocolsPydantic:\n"
                "    @runtime_checkable\n"
                "    class BaseModel[DumpT](Protocol):\n"
                "        def model_dump(self) -> DumpT: ...\n\n\n"
                "__all__ = ['AcmeUpstreamProtocolsPydantic']\n"
            ),
            upstream / "protocols.py": (
                "from typing import TypeAlias\n\n"
                "from acme_upstream._protocols.pydantic import (\n"
                "    AcmeUpstreamProtocolsPydantic,\n"
                ")\n\n\n"
                "class AcmeUpstreamProtocols(AcmeUpstreamProtocolsPydantic):\n"
                "    BaseModel: TypeAlias = (\n"
                "        AcmeUpstreamProtocolsPydantic.BaseModel\n"
                "    )\n"
                "    Port: TypeAlias = AcmeUpstreamProtocolsPydantic.BaseModel\n\n\n"
                "p = AcmeUpstreamProtocols\n\n"
                "__all__ = ['AcmeUpstreamProtocols', 'p']\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            facade_module = project.get_module("acme_upstream.protocols")
            facade = facade_module.get_attribute("AcmeUpstreamProtocols").get_object()
            part = (
                project
                .get_module("acme_upstream._protocols.pydantic")
                .get_attribute("AcmeUpstreamProtocolsPydantic")
                .get_object()
            )
            port = part.get_attribute("BaseModel").get_object()
            tm.that(u.Infra.py_class(port), eq=True)
            if u.Infra.py_class(port):
                tm.that(
                    u.Infra.upstream_protocol_facade(
                        (facade,), package, port, source_project=project
                    ),
                    eq=(
                        "AcmeUpstreamProtocols",
                        "from acme_upstream import AcmeUpstreamProtocols",
                    ),
                )
            published = u.Infra.facade_published_object(
                facade.get_attribute("BaseModel")
            )
            tm.that(published is port, eq=True)
            single = u.Infra.facade_published_object(facade.get_attribute("Port"))
            tm.that(single is port, eq=True)


__all__: list[str] = ["TestsFlextInfraFacadePublishedObject"]
