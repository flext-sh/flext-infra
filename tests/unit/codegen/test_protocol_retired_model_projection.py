"""Generation retires the protocol projection of a deleted model.

``make gen`` is the single writer of model protocol projections, so it must
stay idempotent under deletions too: once a source model disappears, the same
stage removes its projected contract from an authored protocol module and
retires a generated protocol module whose models are all gone, so the protocol
facade and the lazy exports drop it. Regression for flext-b4gw3.6.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tests import c, tm, u


class TestsProtocolRetiredModelProjection:
    """Delete a model, regenerate, and prove nothing of its projection stays."""

    _PAYLOAD_MODELS = (
        "from flext_core import m\n"
        "class FlextInfraModelsPayload:\n"
        "    class Packet(m.ContractModel):\n"
        "        visible: str\n"
        "{retired}"
        "__all__ = ['FlextInfraModelsPayload']\n"
    )
    _RETIRED_MODEL = "    class Retired(m.ContractModel):\n        name: str\n"
    _LEGACY_MODELS = (
        "from flext_core import m\n"
        "class FlextInfraModelsLegacy:\n"
        "    class Ledger(m.ContractModel):\n"
        "        total: int\n"
        "__all__ = ['FlextInfraModelsLegacy']\n"
    )
    _MODEL_FACADE = (
        "{imports}"
        "class FlextInfraModels({bases}): pass\n"
        "m = FlextInfraModels\n"
        "__all__ = ['FlextInfraModels', 'm']\n"
    )
    # An authored protocol module: generation appends the projected contracts
    # beside the authored one and never removes the authored one.
    _AUTHORED_PROTOCOLS = (
        "from typing import Protocol, runtime_checkable\n"
        "class FlextInfraProtocolsPayload:\n"
        '    """Payload protocols."""\n'
        "    @runtime_checkable\n"
        "    class Reader(Protocol):\n"
        '        """Authored reader contract."""\n'
        "        def read(self) -> str: ...\n"
        "__all__ = ['FlextInfraProtocolsPayload']\n"
    )

    @staticmethod
    def _write(sources: Mapping[Path, str]) -> None:
        # Fixture inputs need no durable atomic publication.
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

    @classmethod
    def _models(cls, package: Path, *, legacy: bool) -> dict[Path, str]:
        holders = ("Payload", "Legacy") if legacy else ("Payload",)
        return {
            package / "models.py": cls._MODEL_FACADE.format(
                imports="".join(
                    f"from flext_infra._models.{name.lower()} import "
                    f"FlextInfraModels{name}\n"
                    for name in holders
                ),
                bases=", ".join(f"FlextInfraModels{name}" for name in holders),
            ),
        }

    @classmethod
    def _generate(cls, root: Path) -> int:
        """Publish one model protocol projection and its lazy exports.

        Returns:
            How many files the projection and the lazy exports changed.

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
        cls._write({root / relative: sources[relative] for relative in changed})
        for relative in retired:
            (root / relative).unlink()
        exported = u.Tests.run_lazy_init(root, check_only=True)
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        return len(changed) + len(retired) + exported

    @c.Tests.MARK.slow
    def test_deleted_model_leaves_no_projection_and_converges(
        self, tmp_path: Path
    ) -> None:
        """A deleted model's contract, module and export retire in one run."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-infra", package_name="flext_infra"
        )
        authored = package / "_protocols" / "payload.py"
        generated = package / "_protocols" / "legacy.py"
        self._write({
            package / "_models" / "payload.py": self._PAYLOAD_MODELS.format(
                retired=self._RETIRED_MODEL
            ),
            package / "_models" / "legacy.py": self._LEGACY_MODELS,
            **self._models(package, legacy=True),
            authored: self._AUTHORED_PROTOCOLS,
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class FlextInfraProtocols(FlextCliProtocols): pass\n"
                "p = FlextInfraProtocols\n"
                "__all__ = ['FlextInfraProtocols', 'p']\n"
            ),
        })
        self._generate(root)
        tm.that(authored.read_text(encoding="utf-8"), has="class Retired(")
        tm.ok(generated.is_file())
        tm.that(
            (package / "_protocols" / c.Infra.INIT_PY).read_text(encoding="utf-8"),
            has="FlextInfraProtocolsLegacy",
        )

        self._write({
            package / "_models" / "payload.py": self._PAYLOAD_MODELS.format(retired=""),
            **self._models(package, legacy=False),
        })
        (package / "_models" / "legacy.py").unlink()
        self._generate(root)

        projection = authored.read_text(encoding="utf-8")
        tm.that(projection, lacks="Retired")
        tm.that(projection, has="class Packet(")
        tm.that(projection, has="class Reader(Protocol)")
        tm.fail(generated.exists())
        for facade in (
            package / "_protocols" / c.Infra.INIT_PY,
            package / "protocols.py",
        ):
            tm.that(
                facade.read_text(encoding="utf-8"), lacks="FlextInfraProtocolsLegacy"
            )
        tm.that(self._generate(root), eq=0)


__all__: list[str] = ["TestsProtocolRetiredModelProjection"]
