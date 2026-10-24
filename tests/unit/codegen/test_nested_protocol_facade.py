"""Native owner identity for protocol facades in nested packages.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import p, tm, u


class TestsNestedProtocolFacade:
    """Exercise qualified imports and rendering convergence through public utilities."""

    @pytest.mark.parametrize("inherited", [False, True])
    def test_nested_package_protocol_owners_keep_native_identity(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        inherited: bool,
    ) -> None:
        """A nested package never binds an unrelated top-level namesake."""
        root, source_package = u.Tests.create_lazy_init_workspace(tmp_path)
        package = source_package / "contracts"
        qualified = f"{source_package.name}.{package.name}"
        self._write(source_package / "__init__.py", "")
        self._write(package / "__init__.py", "")
        self._write(package / "_protocols" / "__init__.py", "")
        owner = (
            "from typing import Protocol, runtime_checkable\n"
            "class PayloadOwner:\n"
            "    @runtime_checkable\n"
            "    class Payload(Protocol):\n        value: str\n"
            "__all__ = ['PayloadOwner']\n"
        )
        self._write(package / "_protocols" / "payload.py", owner)
        self._write(source_package.parent / "contracts" / "__init__.py", "")
        self._write(
            source_package.parent / "contracts" / "_protocols" / "__init__.py", ""
        )
        self._write(
            source_package.parent / "contracts" / "_protocols" / "payload.py", owner
        )
        facade = package / "protocols.py"
        self._write(
            facade,
            f"from {qualified}._protocols.payload import PayloadOwner\n"
            "class PublicProtocols:\n"
            + (
                "    class Sample(PayloadOwner):\n"
                if inherited
                else "    class Sample:\n"
            )
            + "        Payload: type[PayloadOwner.Payload] = PayloadOwner.Payload\n"
            "p = PublicProtocols\n__all__ = ['PublicProtocols', 'p']\n",
        )
        with u.Infra.facade_source_project(root) as (project, sources):
            rendered = tm.not_none(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                )
            )
        self._write(facade, rendered)
        with u.Infra.facade_source_project(root) as (project, sources):
            tm.that(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                ),
                eq=rendered,
            )
        native_consumer(
            f"sys.path.insert(0, {str(source_package.parent)!r})\n"
            f"from {qualified}.protocols import p\n"
            f"from {qualified}._protocols.payload import PayloadOwner\n"
            "assert p.Sample.Payload is PayloadOwner.Payload\n"
            "assert PayloadOwner in p.Sample.__mro__\n",
            cwd=root,
        )

    @staticmethod
    def _write(path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
