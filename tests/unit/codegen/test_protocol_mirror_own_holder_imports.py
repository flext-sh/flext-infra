"""Protocol mirrors read their own holder from module scope, never by import.

A mirror whose contracts reference sibling contracts through the holder it
declares (``Holder.Item``) must not import that holder back from its family
package: the import shadows the class it then redeclares (mypy ``no-redef``)
and every facade route through it becomes undefined. Two inputs produced it:
a nested package (``infra.contracts``) whose declaring module was named from
its parent directory, and a source model that imports the holder itself.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests import tm, u


class TestsProtocolMirrorOwnHolderImports:
    """Exercise the public projection on physical source trees."""

    _MODEL = (
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n"
        "from pydantic import BaseModel\n"
        "{holder_import}"
        "class {stem}ModelsPayload:\n"
        "    class Entry(BaseModel):\n"
        "        name: str\n"
        "    class Batch(BaseModel):\n"
        "        entries: tuple[{holder}.Entry, ...]\n"
    )

    @staticmethod
    def _own_holder_imports(generated: str, holder: str) -> list[str]:
        """Return every import statement that binds ``holder`` in the mirror."""
        return [
            ast.unparse(node)
            for node in ast.walk(ast.parse(generated))
            if isinstance(node, ast.ImportFrom)
            and any((alias.asname or alias.name) == holder for alias in node.names)
        ]

    @classmethod
    def _write(cls, sources: dict[Path, str]) -> None:
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

    @classmethod
    def test_source_model_holder_import_is_not_retained(cls, tmp_path: Path) -> None:
        """A model importing the holder its mirror declares projects no self-import."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-infra", package_name="flext_infra"
        )
        holder = "FlextInfraProtocolsPayload"
        cls._write({
            package / "models.py": (
                "from flext_infra._models.payload import FlextInfraModelsPayload\n"
                "class FlextInfraModels(FlextInfraModelsPayload): pass\n"
                "m = FlextInfraModels\n"
            ),
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class FlextInfraProtocols(FlextCliProtocols): pass\n"
                "p = FlextInfraProtocols\n"
            ),
            package / "_models/payload.py": cls._MODEL.format(
                holder_import=(
                    "if TYPE_CHECKING:\n"
                    f"    from flext_infra._protocols import {holder}\n"
                ),
                stem="FlextInfra",
                holder=holder,
            ),
        })

        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = planned[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.that(cls._own_holder_imports(generated, holder), eq=[])
        tm.ok(f"class {holder}:" in generated)
        tm.ok(f"{holder}.Entry" in generated)

    @classmethod
    def test_nested_package_mirror_does_not_import_its_holder(
        cls, tmp_path: Path
    ) -> None:
        """A nested package names its declaring module with every package segment."""
        root, _src_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-infra", package_name="flext_infra"
        )
        package = root / "infra" / "contracts"
        holder = "InfraContractsProtocolsPayload"
        cls._write({
            root / "infra" / "__init__.py": "",
            package / "__init__.py": "",
            package / "models.py": (
                "from infra.contracts._models.payload import "
                "InfraContractsModelsPayload\n"
                "class InfraContractsModels(InfraContractsModelsPayload): pass\n"
                "m = InfraContractsModels\n"
            ),
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class InfraContractsProtocols(FlextCliProtocols): pass\n"
                "p = InfraContractsProtocols\n"
            ),
            # As in ``infra/contracts/_models/state.py``, the model refers to a
            # sibling through its own model holder; the mirror rewrites that
            # reference to the protocol holder it declares.
            package / "_models/payload.py": cls._MODEL.format(
                holder_import="",
                stem="InfraContracts",
                holder="InfraContractsModelsPayload",
            ),
        })

        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(
                    root, binding[0], package_name="infra.contracts"
                )
            )

        generated = planned[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.that(cls._own_holder_imports(generated, holder), eq=[])
        tm.ok(f"class {holder}:" in generated)
