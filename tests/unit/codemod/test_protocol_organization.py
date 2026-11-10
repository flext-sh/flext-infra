"""Native mixed-holder protocol placement and retained public facade contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import infra
from tests import c, p, tm, u


class TestsFlextInfraProtocolOrganization:
    """Exercise classification, movement and a fresh real consumer together."""

    @staticmethod
    @c.Tests.MARK.parametrize("published", [False, True])
    def test_model_inventory_resolves_existing_or_planned_protocol_owner(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        published: bool,
    ) -> None:
        """Native public bindings win over the not-yet-materialized mirror path."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package.name
        sources = {
            package / "__init__.py": (
                "from .models import m\nfrom .protocols import p\n"
                "__all__ = ['m', 'p']\n"
            ),
            package / "_models" / "__init__.py": '"""Model family."""\n',
            package / "_protocols" / "__init__.py": '"""Protocol family."""\n',
            package / "_models" / "payload.py": (
                "from pydantic import BaseModel\n"
                "class ModelsPayload:\n"
                "    class Packet(BaseModel):\n        value: int\n"
            ),
            package / "models.py": (
                f"from {module}._models.payload import ModelsPayload\n"
                "class Models(ModelsPayload): pass\nm = Models\n"
            ),
            package / "protocols.py": (
                f"from {module}._protocols.combined import ProtocolsCombined\n"
                "class Protocols(ProtocolsCombined): pass\np = Protocols\n"
                if published
                else "class Protocols: pass\np = Protocols\n"
            ),
        }
        if published:
            sources[package / "_protocols" / "combined.py"] = (
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsCombined:\n"
                "    @runtime_checkable\n    class Packet(Protocol):\n"
                "        value: int\n"
            )
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        protocol_module = "combined" if published else "payload"
        holder = "ProtocolsCombined" if published else "ProtocolsPayload"
        model_identity = f"{module}._models.payload.ModelsPayload.Packet"
        protocol_identity = f"{module}._protocols.{protocol_module}.{holder}.Packet"
        protocol_source = package / "_protocols" / f"{protocol_module}.py"
        with infra.rope_workspace(root) as workspace:
            with workspace.rope_project.source_view(
                declared_files=None, additional_source_folders=None
            ) as project:
                declarations = u.Infra.protocol_model_declarations_from_source(
                    root, project
                )
            tm.that(
                declarations,
                eq=((model_identity, protocol_identity, protocol_source),),
            )
            tm.that(
                workspace.model_protocol_identities[model_identity],
                eq=protocol_identity,
            )
        tm.that(protocol_source.exists(), eq=published)
        native_consumer(
            f"sys.path.insert(0, {str(root / 'src')!r})\n"
            f"from {module} import m, p\n"
            + (
                "assert isinstance(m.Packet(value=7), p.Packet)\n"
                if published
                else "assert m.Packet(value=7).value == 7\n"
                "assert not hasattr(p, 'Packet')\n"
            ),
            cwd=root,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("nested", [False, True])
    @c.Tests.MARK.parametrize("narrowing", [False, True])
    def test_mixed_holder_preserves_public_names_and_recursive_contracts(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        nested: bool,
        narrowing: bool,
    ) -> None:
        """Safe cohorts proceed while an unrelated unresolved port stays visible."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package.name
        if nested:
            declaration = u.Tests.project_spec(root.name).model_copy(
                update={"repository_namespace_packages": ("infra",)}
            )
            tm.ok(
                u.Cli.yaml_dump(
                    root / "config" / "codegen.yaml",
                    {
                        "Infra": {
                            "codegen": {
                                "repository": {
                                    "project": declaration.model_dump(mode="json")
                                }
                            }
                        }
                    },
                )
            )
            package = root / "infra" / "contracts"
            package.mkdir(parents=True)
            module = "infra.contracts"
        sources = {
            package / "__init__.py": (
                "from .models import m\nfrom .protocols import p\n"
                "__all__ = ['m', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from pydantic import BaseModel\n"
                "class ModelsPayload:\n"
                "    class Packet(BaseModel):\n        value: int\n"
                "__all__ = ['ModelsPayload']\n"
            ),
            package / "models.py": (
                f"from {module}._models.payload import ModelsPayload\n"
                "class Models(ModelsPayload):\n    pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "_protocols" / "combined.py": (
                "from __future__ import annotations\n"
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsCombined:\n"
                "    @runtime_checkable\n    class Packet(Protocol):\n        value: "
                "int\n"
                "    @runtime_checkable\n    class ServicePort(Protocol):\n"
                "        def execute(self) -> str: ...\n"
                "    @runtime_checkable\n    class ExternalPath(Protocol):\n"
                "        def exists(self) -> bool: ...\n"
                "        @property\n"
                "        def parent(self) -> ProtocolsCombined.ExternalDirectory: ...\n"
                "        def absolute(self) -> ProtocolsCombined.ExternalPath: ...\n"
                "    @runtime_checkable\n    class ExternalDirectory(Protocol):\n"
                "        def exists(self) -> bool: ...\n"
                "        @property\n"
                "        def parent(self) -> ProtocolsCombined.ExternalPath: ...\n"
                "    @runtime_checkable\n    class UnusedPort(Protocol):\n"
                "        def unobserved(self) -> None: ...\n"
                "__all__ = ['ProtocolsCombined']\n"
            ),
            package / "protocols.py": (
                f"from {module}._protocols.combined import ProtocolsCombined\n"
                "class Protocols(ProtocolsCombined):\n    pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "consumer.py": (
                "from __future__ import annotations\n"
                "from pathlib import Path\nfrom typing import TypeGuard\n"
                "from flext_core import t\n"
                f"from {module}.protocols import p\n"
                f"from {module}._protocols.combined import ProtocolsCombined\n"
                "def service(value: t.Port[p.ServicePort]) -> str:\n"
                "    return value.execute()\n"
                + (
                    "def native_path(value: object) -> bool:\n"
                    "    return isinstance(value, Path)\n"
                    "def external(value: object) -> TypeGuard[p.ExternalPath]:\n"
                    "    return native_path(value)\n"
                    "def directory(value: object) -> TypeGuard[p.ExternalDirectory]:\n"
                    "    return isinstance(value, Path)\n"
                    if narrowing
                    else "def external(value: p.ExternalPath) -> bool:\n"
                    "    return value.exists()\n"
                )
                + "def direct(value: ProtocolsCombined.ServicePort) -> str:\n"
                "    return value.execute()\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        for family in ("_models", "_protocols"):
            path = package / family / "__init__.py"
            tm.ok(u.Cli.atomic_write_text_file(path, '"""Contract family."""\n'))
            sources[path] = path.read_text()
        with infra.rope_workspace(root) as workspace:
            inventory = tuple(
                item
                for path in sources
                for item in workspace.objects(
                    path, include_local_scopes=True, include_references=True
                )
            )
            census = u.Infra.protocol_contract_census(
                workspace, sources=sources, objects=inventory
            )
            categories = {
                row.source_class.rsplit(".", 1)[-1]: row.category
                for row in census.contracts
            }
            contracts = {
                row.source_class.rsplit(".", 1)[-1]: row for row in census.contracts
            }
            path_contract = contracts["ExternalPath"]
            directory_contract = contracts["ExternalDirectory"]
            tm.that(
                directory_contract.source_module + "." + directory_contract.source_class
                in path_contract.dependencies,
                eq=True,
            )
            tm.that(
                path_contract.source_module + "." + path_contract.source_class
                in directory_contract.dependencies,
                eq=True,
            )
            tm.that(
                (categories["Packet"], workspace.model_protocol_identities),
                eq=(c.Infra.ProtocolOrigin.MODEL, workspace.model_protocol_identities),
            )
            tm.that(categories["ServicePort"], eq=c.Infra.ProtocolOrigin.SERVICE)
            tm.that(
                categories["ExternalPath"],
                eq=c.Infra.ProtocolOrigin.EXTERNAL
                if narrowing
                else c.Infra.ProtocolOrigin.UNRESOLVED,
            )
            tm.that(categories["UnusedPort"], eq=c.Infra.ProtocolOrigin.UNRESOLVED)
            plan = u.Infra.plan_protocol_contract_organization(
                workspace, sources=sources, census=census
            )
            tm.that(bool(plan.files), eq=True)
            tm.that(len(plan.census.contracts), eq=1 + 2 * int(narrowing))
            tm.that(bool(census.findings), eq=True)
            tm.that(
                all(
                    row.source_module.startswith(module + ".")
                    for row in census.contracts
                ),
                eq=True,
            )
            tm.ok(u.Infra.publish_codegen_plans(root, plan.files))
        native_consumer(
            f"sys.path.insert(0, {str(root)!r})\n"
            f"sys.path.insert(0, {str(root / 'src')!r})\n"
            "from pathlib import Path\n"
            "from typing import get_type_hints\n"
            f"from {module}.models import m\n"
            f"from {module}.protocols import p\n"
            f"from {module}.consumer import direct, external, service\n"
            "class Service:\n    def execute(self):\n        return 'executed'\n"
            "assert service(Service()) == direct(Service()) == 'executed'\n"
            "assert isinstance(m.Packet(value=7), p.Packet)\n"
            "assert isinstance(Path('.'), p.ExternalPath)\n"
            "assert external(Path('.'))\n"
            "assert get_type_hints(p.ExternalPath.parent.fget)['return'] is "
            "p.ExternalDirectory\n"
            "assert get_type_hints(p.ExternalDirectory.parent.fget)['return'] is "
            "p.ExternalPath\n"
            "assert not hasattr(p, 'Services') and not hasattr(p, 'External')\n",
            cwd=root,
        )
