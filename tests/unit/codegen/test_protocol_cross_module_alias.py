"""A cross-module model alias projects its owner's Protocol, never itself.

A model family may re-export a model another module declares under the same
name (``Routing = AcmeModelsRouting.Routing``) so the public facade reaches it
through that family. Its Protocol mirror aliases the owning Protocol holder.
Once the alias is published, the facade route resolves to the alias itself;
electing it as the declaring owner emitted ``type Routing = <own>.Routing``, a
cyclic alias that pyright and mypy reject (bead aihub-057kp).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u


class TestsProtocolCrossModuleAlias:
    """Project a re-exported model alias on a physical source tree, twice."""

    @staticmethod
    def _workspace(tmp_path: Path, *, referenced: bool) -> tuple[Path, Path]:
        """Build one family that re-exports a model another module declares.

        ``referenced`` adds a field reading the owner through its own module.

        Returns:
            The repository root and the package directory.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        name = package.name
        field = (
            "        routes: Mapping[str, AcmeModelsRouting.Routing]\n"
            if referenced
            else ""
        )
        sources = {
            "models.py": (
                f"from {name}._models.proxy import AcmeModelsProxy\n"
                "class AcmeModels:\n"
                "    class Acme(AcmeModelsProxy): pass\n"
                "m = AcmeModels\n__all__ = ['AcmeModels', 'm']\n"
            ),
            "protocols.py": (
                f"from {name}._protocols.proxy import AcmeProtocolsProxy\n"
                "class AcmeProtocols:\n"
                "    class Acme(AcmeProtocolsProxy): pass\n"
                "p = AcmeProtocols\n__all__ = ['AcmeProtocols', 'p']\n"
            ),
            "_models/routing.py": (
                "from pydantic import BaseModel\n"
                "class AcmeModelsRouting:\n"
                "    class Routing(BaseModel):\n        strategy: str\n"
                "__all__ = ['AcmeModelsRouting']\n"
            ),
            "_models/proxy.py": (
                "from collections.abc import Mapping\n"
                "from pydantic import BaseModel\n"
                f"from {name}._models.routing import AcmeModelsRouting\n"
                "class AcmeModelsProxy:\n"
                "    Routing = AcmeModelsRouting.Routing\n"
                "    class Proxy(BaseModel):\n"
                "        name: str\n" + field + "__all__ = ['AcmeModelsProxy']\n"
            ),
            "_protocols/__init__.py": "",
            "_protocols/proxy.py": (
                "class AcmeProtocolsProxy: pass\n__all__ = ['AcmeProtocolsProxy']\n"
            ),
        }
        for relative, source in sources.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return root, package

    @staticmethod
    def _project(root: Path) -> dict[Path, str]:
        """Project the model mirrors and publish them with their initializers.

        Returns:
            The projected sources keyed by their repository-relative path.

        """
        with u.Infra.facade_source_project(root) as binding:
            projected = dict(
                tm.ok(u.Infra.protocol_model_sources_from_source(root, binding[0]))
            )
        for relative, source in projected.items():
            path = root / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        return projected

    @classmethod
    @c.Tests.MARK.parametrize("referenced", [False, True])
    def test_alias_targets_owner_protocol_at_fixed_point(
        cls,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        referenced: bool,
    ) -> None:
        """The published alias resolves to the owner, and regeneration keeps it."""
        root, package = cls._workspace(tmp_path, referenced=referenced)
        mirror = (package / "_protocols/proxy.py").relative_to(root)
        first = cls._project(root)
        second = cls._project(root)
        tm.that(second[mirror], has="type Routing = AcmeProtocolsRouting.Routing")
        tm.that(second[mirror], lacks="type Routing = AcmeProtocolsProxy.Routing")
        tm.that(second[mirror], eq=first[mirror])
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.protocols import p\n"
            f"from {package.name}._protocols.routing import AcmeProtocolsRouting\n"
            "from flext_tests import tm\n"
            "tm.ok(p.Acme.Routing.__value__ is AcmeProtocolsRouting.Routing)\n",
            cwd=root,
        )
