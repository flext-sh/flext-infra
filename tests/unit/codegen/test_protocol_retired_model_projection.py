"""Generation retires the protocol projection of a deleted model.

``make gen`` is the single writer of model protocol projections, so it must
stay idempotent under deletions too: once a source model disappears, the same
stage removes its projected contract from an authored protocol module and
retires a generated protocol module whose models are all gone, together with
its lazy export. Regression for flext-b4gw3.6.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsProtocolRetiredModelProjection:
    """Delete a model, regenerate, and prove nothing of its projection stays."""

    _DISTRIBUTION = "sample-library"

    _PAYLOAD_MODELS = (
        '"""Payload models."""\n\n'
        "from __future__ import annotations\n\n"
        "from flext_core import m\n\n\n"
        "class SampleLibraryModelsPayload:\n"
        '    """Payload models."""\n\n'
        "    class Packet(m.ContractModel):\n"
        '        """Packet that stays."""\n\n'
        "        visible: str\n\n"
        "{retired}"
        '__all__: list[str] = ["SampleLibraryModelsPayload"]\n'
    )

    _RETIRED_MODEL = (
        "    class Retired(m.ContractModel):\n"
        '        """Model the test deletes."""\n\n'
        "        name: str\n\n\n"
    )

    _LEGACY_MODELS = (
        '"""Legacy models."""\n\n'
        "from __future__ import annotations\n\n"
        "from flext_core import m\n\n\n"
        "class SampleLibraryModelsLegacy:\n"
        '    """Legacy models."""\n\n'
        "    class Ledger(m.ContractModel):\n"
        '        """Model whose whole module the test deletes."""\n\n'
        "        total: int\n\n\n"
        '__all__: list[str] = ["SampleLibraryModelsLegacy"]\n'
    )

    # An authored protocol module: its holder keeps the authored contract,
    # and generation appends the projected ones beside it.
    _AUTHORED_PROTOCOLS = (
        '"""Payload protocols."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Protocol, runtime_checkable\n\n\n"
        "class SampleLibraryProtocolsPayload:\n"
        '    """Payload protocols."""\n\n'
        "    @runtime_checkable\n"
        "    class Reader(Protocol):\n"
        '        """Authored reader contract."""\n\n'
        "        def read(self) -> str:\n"
        '            """Read one payload."""\n'
        "            ...\n\n\n"
        '__all__: list[str] = ["SampleLibraryProtocolsPayload"]\n'
    )

    @classmethod
    def _project(cls, tmp_path: Path) -> Path:
        """Create one governed repository owning models and protocols.

        Returns:
            The repository's package directory.

        """
        root = tmp_path / cls._DISTRIBUTION
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            cls._DISTRIBUTION,
            beads=u.Tests.BeadsIdentity(
                workspace=cls._DISTRIBUTION,
                database=cls._DISTRIBUTION.replace("-", "_"),
                issue_prefix=cls._DISTRIBUTION,
            ),
        )
        project = u.Tests.project_spec(cls._DISTRIBUTION)
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {"project": project.model_dump(mode="json")},
                        },
                    },
                },
            ),
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / tm.not_none(project.package_name)
        for path, content in {
            package / "_models" / "payload.py": cls._PAYLOAD_MODELS.format(
                retired=cls._RETIRED_MODEL
            ),
            package / "_models" / "legacy.py": cls._LEGACY_MODELS,
            package / "_protocols" / "payload.py": cls._AUTHORED_PROTOCOLS,
        }.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        return package

    @classmethod
    def _generate(cls, package: Path) -> p.Infra.CodegenResult:
        """Run the public generation of the projected facades once.

        Returns:
            The conform outcome, carrying every file the run wrote.

        """
        root = package.parents[1]
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.FACADES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        return tm.ok(
            TestsFlextInfraConformSupport.conform_in_workspace(
                request,
                u.Tests.standalone_workspace(root, cls._DISTRIBUTION),
            )
        )

    @c.Tests.MARK.slow
    def test_deleted_model_leaves_no_projection_and_converges(
        self, tmp_path: Path
    ) -> None:
        """A deleted model's contract, module and export retire in one run."""
        package = self._project(tmp_path)
        authored = package / "_protocols" / "payload.py"
        generated = package / "_protocols" / "legacy.py"
        initializer = package / "_protocols" / c.Infra.INIT_PY
        self._generate(package)
        tm.that(authored.read_text(encoding="utf-8"), has="class Retired(")
        tm.that(authored.read_text(encoding="utf-8"), has="class Packet(")
        tm.ok(generated.is_file())
        tm.that(
            initializer.read_text(encoding="utf-8"),
            has="SampleLibraryProtocolsLegacy",
        )

        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "_models" / "payload.py",
                self._PAYLOAD_MODELS.format(retired=""),
            )
        )
        (package / "_models" / "legacy.py").unlink()
        self._generate(package)

        projection = authored.read_text(encoding="utf-8")
        tm.that(projection, lacks="Retired")
        tm.that(projection, has="class Packet(")
        tm.that(projection, has="class Reader(Protocol)")
        tm.fail(generated.exists())
        tm.that(
            initializer.read_text(encoding="utf-8"),
            lacks="SampleLibraryProtocolsLegacy",
        )
        tm.that(
            (package / "protocols.py").read_text(encoding="utf-8"),
            lacks="SampleLibraryProtocolsLegacy",
        )
        tm.that(self._generate(package).written_files, eq=())


__all__: list[str] = ["TestsProtocolRetiredModelProjection"]
