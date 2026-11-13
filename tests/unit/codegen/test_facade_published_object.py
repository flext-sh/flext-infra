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

    @staticmethod
    def test_published_generic_base_reaches_the_ancestry(tmp_path: Path) -> None:
        """A class extending a published generic member inherits its ancestry.

        Premise: flext-core's ``m`` publishes
        ``RootModel: TypeAlias = FlextModelsPydantic.RootModel``. A consumer
        declaring ``class Listing(m.RootModel[list[str]])`` held only an
        unresolved witness in its native ancestry, so the model-source
        collection raised "model ancestry is unresolved".
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = root / c.Infra.DEFAULT_SRC_DIR / "acme_upstream"
        sources = {
            upstream / c.Infra.INIT_PY: (
                "from acme_upstream.models import AcmeUpstreamModels, m\n"
                "__all__ = ['AcmeUpstreamModels', 'm']\n"
            ),
            upstream / "_models" / c.Infra.INIT_PY: "",
            upstream / "_models" / "pydantic.py": (
                "class AcmeUpstreamModelsRoot:\n"
                "    pass\n\n\n"
                "class AcmeUpstreamModelsPydantic:\n"
                "    class RootModel[RootT](AcmeUpstreamModelsRoot):\n"
                "        root: RootT\n\n\n"
                "__all__ = ['AcmeUpstreamModelsPydantic', 'AcmeUpstreamModelsRoot']\n"
            ),
            upstream / "models.py": (
                "from typing import TypeAlias\n\n"
                "from acme_upstream._models.pydantic import (\n"
                "    AcmeUpstreamModelsPydantic,\n"
                ")\n\n\n"
                "class AcmeUpstreamModels(AcmeUpstreamModelsPydantic):\n"
                "    RootModel: TypeAlias = AcmeUpstreamModelsPydantic.RootModel\n\n\n"
                "m = AcmeUpstreamModels\n\n"
                "__all__ = ['AcmeUpstreamModels', 'm']\n"
            ),
            package / "listing.py": (
                "from acme_upstream import m\n\n\n"
                "class FlextTestProjectListing:\n"
                "    class Listing(m.RootModel[list[str]]):\n"
                "        pass\n\n\n"
                "__all__ = ['FlextTestProjectListing']\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            part = project.get_module("acme_upstream._models.pydantic")
            generic = (
                part
                .get_attribute("AcmeUpstreamModelsPydantic")
                .get_object()
                .get_attribute("RootModel")
                .get_object()
            )
            ancestor = part.get_attribute("AcmeUpstreamModelsRoot").get_object()
            listing = (
                project
                .get_module(f"{package.name}.listing")
                .get_attribute("FlextTestProjectListing")
                .get_object()
                .get_attribute("Listing")
                .get_object()
            )
            tm.that(u.Infra.py_class(listing), eq=True)
            if u.Infra.py_class(listing):
                native = tuple(listing.get_mro())
                tm.that(generic in native, eq=False)
                ancestry = u.Infra.facade_published_ancestry(listing)
                tm.that(ancestry[: len(native)], eq=native)
                tm.that(generic in ancestry, eq=True)
                tm.that(ancestor in ancestry, eq=True)


__all__: list[str] = ["TestsFlextInfraFacadePublishedObject"]
