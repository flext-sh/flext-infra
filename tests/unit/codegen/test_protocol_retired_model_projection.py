"""Generation retires the protocol projection of a deleted model.

``make check`` is the single writer of model protocol projections, so it must
stay idempotent under deletions too: once a source model disappears, the same
stage removes its projected contract from an authored protocol module and
retires a generated protocol module whose models are all gone, so the protocol
facade and the lazy exports drop it. Regression for flext-b4gw3.6, starting
from the projection a previous run left behind (the dc-finan shape).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tests import c, tm, u


class TestsProtocolRetiredModelProjection:
    """Regenerate over stale projections and prove nothing of them stays."""

    _PAYLOAD_MODELS = (
        "from flext_core import m\n"
        "class FlextInfraModelsPayload:\n"
        "    class Packet(m.ContractModel):\n"
        "        visible: str\n"
        "__all__ = ['FlextInfraModelsPayload']\n"
    )
    _MODEL_FACADE = (
        "from flext_infra._models.payload import FlextInfraModelsPayload\n"
        "class FlextInfraModels(FlextInfraModelsPayload): pass\n"
        "m = FlextInfraModels\n"
        "__all__ = ['FlextInfraModels', 'm']\n"
    )
    _PROTOCOL_FACADE = (
        "from flext_cli import FlextCliProtocols\n"
        "from flext_infra._protocols.legacy import FlextInfraProtocolsLegacy\n"
        "from flext_infra._protocols.payload import FlextInfraProtocolsPayload\n"
        "class FlextInfraProtocols(\n"
        "    FlextCliProtocols, FlextInfraProtocolsPayload, FlextInfraProtocolsLegacy\n"
        "): pass\n"
        "p = FlextInfraProtocols\n"
        "__all__ = ['FlextInfraProtocols', 'p']\n"
    )

    # An authored service port: it carries no projection marker and must
    # survive byte for byte.
    _AUTHORED_PORT = (
        "from typing import Protocol, runtime_checkable\n"
        "class FlextInfraProtocolsServicesPort:\n"
        '    """Service ports."""\n'
        "    @runtime_checkable\n"
        "    class Reader(Protocol):\n"
        '        """Authored port."""\n'
        "        def read(self) -> str: ...\n"
        "__all__ = ['FlextInfraProtocolsServicesPort']\n"
    )

    @staticmethod
    def _stale_contract(name: str, field: str) -> str:
        """Render one contract exactly as a previous projection emitted it.

        Returns:
            The nested contract source, marked by the owner's projection text.

        """
        projected = c.Infra.DocumentationText.MODEL_PROTOCOL_CONTRACT.value[0]
        return (
            "    @runtime_checkable\n"
            f"    class {name}(Protocol):\n"
            f'        """{projected}"""\n'
            "        @property\n"
            f"        def {field}(self) -> str: ...\n"
        )

    @classmethod
    def _stale_sources(cls, package: Path) -> dict[Path, str]:
        """Write the tree a previous run left after its models were deleted.

        Returns:
            The model sources, the authored protocol module still holding the
            projection of the deleted ``Retired`` model, and the generated
            module of the deleted ``legacy`` model module.

        """
        owner = c.Infra.DocumentationText.MODEL_PROTOCOL_OWNER.value[0]
        imports = "from typing import Protocol, runtime_checkable\n"
        return {
            package / "_models" / "payload.py": cls._PAYLOAD_MODELS,
            package / "models.py": cls._MODEL_FACADE,
            package / "protocols.py": cls._PROTOCOL_FACADE,
            package / "_protocols" / "payload.py": (
                imports + "class FlextInfraProtocolsPayload:\n"
                '    """Payload protocols."""\n'
                "    @runtime_checkable\n"
                "    class Reader(Protocol):\n"
                '        """Authored reader contract."""\n'
                "        def read(self) -> str: ...\n"
                + cls._stale_contract("Retired", "name")
                + "__all__ = ['FlextInfraProtocolsPayload']\n"
            ),
            package / "_protocols" / "legacy.py": (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                + imports
                + "class FlextInfraProtocolsLegacy:\n"
                f'    """{owner}"""\n'
                + cls._stale_contract("Ledger", "total")
                + "__all__ = ['FlextInfraProtocolsLegacy']\n"
            ),
            # A mirror of a deleted nested model package retires as well.
            package / "_protocols" / "_config" / "archive.py": (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                + imports
                + "class FlextInfraProtocolsConfigArchive:\n"
                f'    """{owner}"""\n'
                + cls._stale_contract("Archive", "path")
                + "__all__ = ['FlextInfraProtocolsConfigArchive']\n"
            ),
            package / "_protocols" / "_services" / "port.py": cls._AUTHORED_PORT,
        }

    @staticmethod
    def _write(sources: Mapping[Path, str]) -> None:
        # Fixture inputs need no durable atomic publication.
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

    @classmethod
    def _generate(cls, root: Path, *, check_only: bool = False) -> int:
        """Run one model protocol projection and its lazy exports.

        ``check_only`` publishes nothing and counts the pending effects.

        Returns:
            How many files the projection and the lazy exports would change.

        """
        with u.Infra.facade_source_project(root) as binding:
            sources, retired = tm.ok(
                u.Infra.protocol_model_projection_from_source(root, binding[0])
            )
        changed = [
            relative
            for relative, source in sources.items()
            if not (root / relative).is_file()
            or (root / relative).read_text(encoding="utf-8") != source
        ]
        if check_only:
            return (
                len(changed)
                + len(retired)
                + u.Tests.run_lazy_init(root, check_only=True)
            )
        cls._write({root / relative: sources[relative] for relative in changed})
        for relative in retired:
            (root / relative).unlink()
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        return len(changed) + len(retired)

    @c.Tests.MARK.slow
    def test_deleted_model_leaves_no_projection_and_converges(
        self, tmp_path: Path
    ) -> None:
        """Stale projected contracts, modules and exports retire in one run."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-infra", package_name="flext_infra"
        )
        authored = package / "_protocols" / "payload.py"
        generated = package / "_protocols" / "legacy.py"
        initializer = package / "_protocols" / c.Infra.INIT_PY
        self._write(self._stale_sources(package))

        self._generate(root)

        projection = authored.read_text(encoding="utf-8")
        tm.that(projection, lacks="Retired")
        tm.that(projection, has="class Packet(")
        tm.that(projection, has="class Reader(Protocol)")
        tm.fail(generated.exists())
        tm.fail((package / "_protocols" / "_config" / "archive.py").exists())
        tm.that(
            (package / "_protocols" / "_services" / "port.py").read_text(
                encoding="utf-8"
            ),
            eq=self._AUTHORED_PORT,
        )
        for facade in (initializer, package / "protocols.py"):
            tm.that(
                facade.read_text(encoding="utf-8"), lacks="FlextInfraProtocolsLegacy"
            )
        tm.that(self._generate(root, check_only=True), eq=0)


__all__: list[str] = ["TestsProtocolRetiredModelProjection"]
