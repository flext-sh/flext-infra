"""Native model ancestry projected through the public protocol owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import infra
from tests import c, m, p, tm, u


class TestsModelProtocolNativeMro:
    """Compare generated contracts with the real Pydantic consumer."""

    @staticmethod
    @c.Tests.MARK.parametrize("requested", ["visible", "foreign"])
    def test_existing_narrow_port_retains_model_owner(
        tmp_path: Path, requested: str, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A deliberate consumer view is reused; unrelated fields remain conflicts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "_models" / "payload.py": (
                "from flext_core import m\n"
                "class ModelsPayload:\n"
                "    class Packet(m.ContractModel):\n"
                "        visible: str\n        internal: int = 0\n"
                "__all__ = ['ModelsPayload']\n"
            ),
            package / "models.py": (
                f"from {package.name}._models.payload import ModelsPayload\n"
                "class Models:\n    class Project(ModelsPayload):\n        pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "_protocols" / "reader.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsReader:\n"
                "    @runtime_checkable\n    class Packet(Protocol):\n"
                f"        @property\n        def {requested}(self) -> str: ...\n"
                "__all__ = ['ProtocolsReader']\n"
            ),
            package / "protocols.py": (
                f"from {package.name}._protocols.reader import ProtocolsReader\n"
                "class Protocols:\n    class Project(ProtocolsReader):\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "consumer.py": (
                f"from {package.name}.protocols import p\n"
                "def read(value: p.Project.Packet) -> str:\n"
                f"    return value.{requested}\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.facade_source_project(root) as binding:
            if requested == "foreign":
                with u.Tests.raises(
                    ValueError, match="declares members its model lacks"
                ):
                    u.Infra.protocol_model_sources_from_source(root, binding[0])
                return
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        tm.that(
            (package / "_protocols" / "reader.py").read_text(),
            eq=sources[package / "_protocols" / "reader.py"],
        )
        for relative, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / relative).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_tests import tm\n"
            "value = m.Project.Packet(visible='payload')\n"
            "tm.ok(isinstance(value, p.Project.Packet))\n"
            "tm.that(value.visible, eq='payload')\n",
            cwd=root,
        )

    @staticmethod
    def test_runtime_dependency_plan_schema_uses_the_port_owner() -> None:
        """A structural manifest remains schema-safe at the public model boundary."""
        schema = m.Infra.RuntimeDependencyPlan.model_json_schema()
        tm.ok(isinstance(schema, dict))

    @staticmethod
    def test_deptry_scan_schema_uses_the_port_owner() -> None:
        """A gate model schema accepts its structural source manifest port."""
        schema = m.Infra.DeptryScan.model_json_schema()
        tm.ok(isinstance(schema, dict))

    @staticmethod
    def test_codegen_source_authority_schema_uses_the_port_owner() -> None:
        """Source authority completes its runtime Pydantic core schema."""
        m.Infra.CodegenSourceAuthority.model_rebuild()
        tm.ok(m.Infra.CodegenSourceAuthority.__pydantic_complete__)
        tm.ok(
            isinstance(
                m.Infra.CodegenSourceAuthority.__pydantic_core_schema__,
                dict,
            )
        )

    @staticmethod
    def test_mise_toolchain_sources_schema_uses_the_port_owner() -> None:
        """Computed source fields rebuild with their structural state port."""
        m.Infra.MiseToolchainWorkspacePlan.model_rebuild()
        tm.ok(m.Infra.MiseToolchainWorkspacePlan.__pydantic_complete__)

    @staticmethod
    def test_source_inventory_does_not_open_missing_protocol_model_facade(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Source projection never executes the model module it describes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import ModelsPayload\n"
                "class Models(ModelsPayload): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols: pass\np = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from flext_core import m\n"
                "class ModelsPayload:\n"
                "    class Packet(m.ContractModel):\n        visible: str\n"
                "__all__ = ['ModelsPayload']\n"
                "raise RuntimeError('model module executed during projection')\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        native_consumer(
            "from flext_infra import u\n"
            "from flext_tests import tm\n"
            f"root = Path({str(root)!r})\n"
            "with u.Infra.facade_source_project(root) as binding:\n"
            "    projected = tm.ok(\n"
            "        u.Infra.protocol_model_sources_from_source(root, binding[0]))\n"
            f"destination = Path('src/{package.name}/_protocols/payload.py')\n"
            "tm.ok(destination in projected)\n"
            "tm.ok('class Packet(' in projected[destination])\n"
            f"tm.fail('{package.name}._models.payload' in sys.modules)\n",
            cwd=root,
        )

    @staticmethod
    def test_source_mirror_projects_field_annotations_without_field_metadata(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Model metadata stays concrete while consumers use real protocol facades."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                "from flext_cli import m as cli_m\n"
                f"from {package.name}._models.payload import ModelsPayload\n"
                f"from {package.name}._models.workspace import ModelsWorkspace\n"
                "class Models(cli_m):\n"
                "    class Project(ModelsPayload, ModelsWorkspace): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "from flext_cli import p as cli_p\n"
                "class Protocols(cli_p):\n    class Project: pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "workspace.py": (
                "from flext_cli import m\n"
                "class ModelsWorkspace:\n"
                "    class WorkspaceThing(m.ContractModel):\n        value: str\n"
                "__all__ = ['ModelsWorkspace']\n"
            ),
            package / "_models" / "payload.py": (
                "from __future__ import annotations\n"
                "from typing import Annotated as TypeMetadata\n"
                "from flext_cli import m\n"
                f"from {package.name}._models.workspace import ModelsWorkspace\n"
                "class ModelsPayload:\n"
                "    class Request(m.ContractModel):\n"
                "        title: TypeMetadata[str, m.Field(description='title')]\n"
                "        receipt: TypeMetadata[m.Cli.AtomicFileState | None, "
                "m.Field(default=None)]\n"
                "        workspace: ModelsWorkspace.WorkspaceThing\n"
                "__all__ = ['ModelsPayload']\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        generated = projected[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.fail("m.Field" in generated)
        tm.fail("TypeMetadata" in generated)
        for relative, content in projected.items():
            tm.ok(u.Cli.ensure_dir((root / relative).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "thing = m.Project.WorkspaceThing(value='ready')\n"
            "value = m.Project.Request(title='metadata', workspace=thing)\n"
            "tm.ok(isinstance(value, p.Project.Request))\n"
            "tm.ok(isinstance(value.workspace, p.Project.WorkspaceThing))\n"
            "tm.ok(value.workspace is thing)\n"
            "tm.that(value.title, eq='metadata')\n"
            "tm.that(value.receipt, eq=None)\n"
            "tm.that(value.model_dump()['workspace']['value'], eq='ready')\n"
            "tm.ok(isinstance(m.Project.Request.model_json_schema(), dict))\n",
            cwd=root,
        )

    @staticmethod
    def test_source_mirror_skips_unannotated_computed_property(
        tmp_path: Path,
    ) -> None:
        """Only annotated computed properties become complete Protocol properties."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": "class Models:\n    pass\nm = Models\n",
            package / "protocols.py": "class Protocols:\n    pass\np = Protocols\n",
            package / "_models" / "payload.py": (
                "from pydantic import BaseModel, computed_field\n\n"
                "class ModelsPayload:\n"
                "    class Payload(BaseModel):\n"
                "        title: str\n\n"
                "        @computed_field\n"
                "        @property\n"
                "        def summary(self) -> str:\n"
                "            return self.title\n\n"
                "        @computed_field\n"
                "        @property\n"
                "        def incomplete(self):\n"
                "            return self.title\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = projected[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("title: str" in generated)
        tm.ok("def summary(self) -> str:" in generated)
        tm.fail("incomplete" in generated)
        ast.parse(generated, filename="generated-payload.py")

    @staticmethod
    def test_source_mirror_resolves_model_holder_from_another_module(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Inherited cross-module fields retain the public Protocol facade import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                f"from {package.name}._models.holder import ModelHolderB\n"
                f"from {package.name}._models.consumer import ModelHolderA\n"
                "class Models:\n"
                "    class Infra(ModelHolderA, ModelHolderB): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Infra:\n        pass\np = Protocols\n"
            ),
            package / "_models" / "holder.py": (
                "from pydantic import BaseModel\n"
                "class ModelHolderB:\n"
                "    class Entity(BaseModel):\n        title: str\n"
            ),
            package / "_models" / "consumer.py": (
                "from pydantic import BaseModel\n"
                f"from {package.name}._models.holder import ModelHolderB\n"
                "class ModelHolderA:\n"
                "    class Base(BaseModel):\n"
                "        entity: ModelHolderB.Entity\n"
                "    class Request(Base):\n"
                "        pass\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        destination = (package / "_protocols" / "consumer.py").relative_to(root)
        generated = projected[destination]
        tm.ok("ModelHolderB.Entity" not in generated)
        tm.fail(
            any(
                isinstance(node, ast.Name) and node.id == "m"
                for node in ast.walk(ast.parse(generated))
            )
        )
        tm.ok("@runtime_checkable" in generated)
        for relative, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / relative).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "entity = m.Infra.Entity(title='inherited')\n"
            "value = m.Infra.Request(entity=entity)\n"
            "tm.ok(value.entity is entity)\n"
            "tm.ok(isinstance(value, p.Infra.Request))\n"
            "tm.ok(isinstance(value.entity, p.Infra.Entity))\n"
            "tm.ok(m.Infra.Request.model_fields['entity'].annotation is "
            "m.Infra.Entity)\n"
            "tm.ok(isinstance(m.Infra.Request.model_json_schema(), dict))\n",
            cwd=root,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("bases", ["Left, Right", "Right, Left"])
    def test_diamond_override_matches_the_runtime_model(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        bases: str,
    ) -> None:
        """Base order changes effective fields identically in model and protocol."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                f"from {package.name}._models import ModelDiamond\n"
                "class Models:\n"
                "    class Domain(ModelDiamond):\n"
                "        pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "_models" / "__init__.py": (
                "from .diamond import ModelDiamond\n__all__ = ['ModelDiamond']\n"
            ),
            package / "_models" / "diamond.py": (
                "from pydantic import BaseModel\n"
                "class ModelDiamond:\n"
                "    class Root(BaseModel):\n"
                "        marker: float\n"
                "    class Left(Root):\n"
                "        marker: int\n"
                "    class Right(Root):\n"
                "        marker: str\n"
                f"    class Payload({bases}):\n"
                "        title: str\n"
                "__all__ = ['ModelDiamond']\n"
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
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            projected = tm.ok(u.Infra.protocol_model_sources(workspace))
        tm.that(projected, empty=False)
        tm.ok((package / "_protocols" / "diamond.py").relative_to(root) in projected)
        for path, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, source))
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"module = importlib.import_module('{package.name}._protocols.diamond')\n"
            "contract = getattr(module, module.__all__[0]).Payload\n"
            "tm.ok(is_protocol(contract))\n"
            "model = m.Domain.Payload\n"
            "hints = get_type_hints(contract)\n"
            "tm.that(set(hints), eq=set(model.model_fields))\n"
            "for name, field in model.model_fields.items():\n"
            "    tm.that(hints[name], eq=field.annotation)\n"
            "payload = model(marker=model.model_fields['marker'].annotation('17'),\n"
            "                title='projected')\n"
            "tm.that(type(payload.marker), eq=hints['marker'])\n"
            "tm.ok(isinstance(payload, contract))\n",
            cwd=root,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("authored", [False, True])
    def test_unpublished_models_mirror_module_and_preserve_authored_ports(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        authored: bool,
    ) -> None:
        """Inventory is declaration-driven, grouped and stable on a second pass."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        relative = Path("_config") / "payload.py"
        owner = "FlextTestProjectProtocolsConfigPayload"
        existing = (
            '"""Authored contract module, not generator-owned."""\n'
            "from typing import Protocol\n\n"
            f"class {owner}:\n"
            "    # Keep the authored interface and its documentation byte-for-byte.\n"
            "    class Worker(Protocol):\n"
            "        def execute(self, command: str) -> int: ...\n\n"
            f"__all__ = ['{owner}']\n"
        )
        sources = {
            package / "models.py": (
                "class Models:\n    class Project:\n        pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Project:\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / relative: (
                "from pydantic import BaseModel\n"
                "class ModelsConfigPayload:\n"
                "    class Request(BaseModel):\n        title: str\n"
                "    class Response(BaseModel):\n        count: int\n"
                "__all__ = ['ModelsConfigPayload']\n"
            ),
            package / "_models" / "other.py": (
                "from pydantic import BaseModel\n"
                "class ModelsOther:\n"
                "    class Status(BaseModel):\n        ready: bool\n"
                "__all__ = ['ModelsOther']\n"
            ),
        }
        if authored:
            sources[package / "_protocols" / relative] = existing
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            projected = tm.ok(u.Infra.protocol_model_sources(workspace))
        expected = {
            (package / "_protocols" / relative).relative_to(root),
            (package / "_protocols" / "other.py").relative_to(root),
        }
        tm.ok(expected <= projected.keys())
        for path, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, source))
        with infra.rope_workspace(root) as workspace:
            repeated = tm.ok(u.Infra.protocol_model_sources(workspace))
        for path, source in repeated.items():
            tm.that((root / path).read_text(), eq=source)
        module_name = f"{package.name}._protocols._config.payload"
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"module = importlib.import_module({module_name!r})\n"
            "owner = getattr(module, module.__all__[0])\n"
            "tm.ok(is_protocol(owner.Request))\n"
            "tm.that(get_type_hints(owner.Request)['title'], eq=str)\n"
            "tm.that(get_type_hints(owner.Response)['count'], eq=int)\n"
            + (
                "tm.ok(is_protocol(owner.Worker))\n"
                "tm.that(get_type_hints(owner.Worker.execute), "
                "eq={'command': str, 'return': int})\n"
                if authored
                else ""
            ),
            cwd=root,
        )

    @staticmethod
    def test_incompatible_authored_contract_blocks_projection(tmp_path: Path) -> None:
        """A conflicting authored entity is diagnosed without source mutation."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "_protocols" / "payload.py"
        authored = (
            "from typing import Protocol\n"
            "class FlextTestProjectProtocolsPayload:\n"
            "    class Request(Protocol):\n        title: int\n"
            "__all__ = ['FlextTestProjectProtocolsPayload']\n"
        )
        sources = {
            package / "models.py": (
                "class Models:\n    pass\nm = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    pass\np = Protocols\n"
                "__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from pydantic import BaseModel\n"
                "class ModelsPayload:\n"
                "    class Request(BaseModel):\n        title: str\n"
                "__all__ = ['ModelsPayload']\n"
            ),
            destination: authored,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with (
            infra.rope_workspace(root) as workspace,
            u.Tests.raises(ValueError, match="incompatible authored protocol contract"),
        ):
            tm.ok(u.Infra.protocol_model_sources(workspace))
        tm.that(destination.read_text(), eq=authored)

    @staticmethod
    def test_authored_concrete_container_matches_projected_read_only_abc(
        tmp_path: Path,
    ) -> None:
        """A concrete authored container implements the projected read-only ABC."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "_protocols" / "payload.py"
        owner = u.derive_class_stem(package.name.replace("_", "-"))
        owner += "ProtocolsPayload"
        authored = (
            "from __future__ import annotations\n"
            "from typing import Protocol, runtime_checkable\n"
            f"class {owner}:\n"
            "    @runtime_checkable\n"
            "    class Target(Protocol):\n        title: str\n"
            "    @runtime_checkable\n"
            "    class Request(Protocol):\n"
            f"        targets: list[{owner}.Target]\n"
            f"        mapping: dict[str, {owner}.Target]\n"
            f"__all__ = ['{owner}']\n"
        )
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import FlextInfraModelsPayload\n"
                "class Models(FlextInfraModelsPayload): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Infra:\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from __future__ import annotations\n"
                "from pydantic import BaseModel\n"
                "class FlextInfraModelsPayload:\n"
                "    class Target(BaseModel):\n"
                "        title: str\n"
                "    class Request(BaseModel):\n"
                "        targets: list[FlextInfraModelsPayload.Target]\n"
                "        mapping: dict[str, FlextInfraModelsPayload.Target]\n"
            ),
            destination: authored,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            projected = tm.ok(u.Infra.protocol_model_sources(workspace))
        rendered = projected[destination.relative_to(root)]
        tm.ok(f"def targets(self) -> Sequence[{owner}.Target]:" in rendered)
        tm.ok(f"def mapping(self) -> Mapping[str, {owner}.Target]:" in rendered)

    @staticmethod
    def test_model_projection_owns_existing_structural_contract(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """The model owns nested validation and its generated consumer contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "_protocols" / "payload.py"
        owner = u.derive_class_stem(package.name.replace("_", "-"))
        owner += "ProtocolsPayload"
        authored = (
            "from typing import Protocol, runtime_checkable\n"
            f"class {owner}:\n"
            "    @runtime_checkable\n"
            "    class Target(Protocol):\n        title: str\n"
            "    @runtime_checkable\n"
            "    class Request(Protocol):\n"
            f"        target: {owner}.Target\n"
            f"__all__ = ['{owner}']\n"
        )
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import FlextInfraModelsPayload\n"
                "class Models(FlextInfraModelsPayload): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Infra:\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from __future__ import annotations\n"
                "from typing import Annotated\n"
                "from flext_cli import m\n"
                "from pydantic import BaseModel\n"
                "class FlextInfraModelsPayload:\n"
                "    class Target(BaseModel):\n"
                "        title: Annotated[str, m.Field(description='title')]\n"
                "    class Request(BaseModel):\n"
                "        target: FlextInfraModelsPayload.Target\n"
            ),
            destination: authored,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        relative = destination.relative_to(root)
        tm.ok(relative in projected)
        for path, content in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, content))
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "m.Request.model_rebuild()\n"
            "target = m.Target(title='native')\n"
            "value = m.Request(target=target)\n"
            "tm.ok(isinstance(value, p.Request))\n"
            "tm.ok(isinstance(value.target, p.Target))\n"
            "restored = m.Request.model_validate(value.model_dump())\n"
            "tm.ok(type(restored.target) is m.Target)\n"
            "tm.that(restored.target.title, eq=target.title)\n",
            cwd=root,
        )

    @staticmethod
    def test_model_projection_replaces_duplicate_authored_property(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """The model's mutable field replaces its duplicated authored accessor."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "_protocols" / "payload.py"
        owner = "FlextTestProjectProtocolsPayload"
        authored = (
            "from typing import Protocol\n"
            f"class {owner}:\n"
            "    class Request(Protocol):\n"
            "        @property\n"
            "        def title(self) -> str: ...\n"
            "        @title.setter\n"
            "        def title(self, value: str) -> None: ...\n"
            f"__all__ = ['{owner}']\n"
        )
        sources = {
            package / "models.py": "class Models: pass\nm = Models\n",
            package / "protocols.py": "class Protocols: pass\np = Protocols\n",
            package / "_models" / "payload.py": (
                "from pydantic import BaseModel\n"
                "class ModelsPayload:\n"
                "    class Request(BaseModel):\n"
                "        title: str\n"
            ),
            destination: authored,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / relative).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            "from typing import get_type_hints\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"module = importlib.import_module('{package.name}._protocols.payload')\n"
            f"contract = getattr(module, {owner!r}).Request\n"
            "tm.that(get_type_hints(contract)['title'], eq=str)\n"
            "tm.fail(hasattr(contract, 'title'))\n",
            cwd=root,
        )

    @staticmethod
    def test_authored_protocol_annotation_facades_stay_type_checking(
        tmp_path: Path,
    ) -> None:
        """Source completion keeps protocol annotation facades type-checking only."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "_protocols" / "payload.py"
        owner = "FlextTestProjectProtocolsPayload"
        authored = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING, Protocol\n"
            "if TYPE_CHECKING:\n"
            "    from flext_core import p as core_p, t\n\n"
            f"class {owner}:\n"
            "    class Reader(Protocol):\n"
            "        record: core_p.Result[str]\n"
            "        value: t.JsonValue\n"
            "        def read(self, value: t.JsonValue) -> core_p.Result[str]: ...\n"
            f"__all__ = ['{owner}']\n"
        )
        sources = {
            package / "models.py": (
                "class Models:\n    pass\nm = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Infra:\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "typings.py": (
                "from flext_core import t as core_t\n"
                "class Typings(core_t): pass\n"
                "t = Typings\n__all__ = ['Typings', 't']\n"
            ),
            package / "_models" / "payload.py": (
                "from flext_core import t\n"
                "from pydantic import BaseModel\n"
                "class FlextTestProjectModelsPayload:\n"
                "    class Payload(BaseModel):\n"
                "        value: t.JsonValue\n"
            ),
            destination: authored,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with infra.rope_workspace(root) as workspace:
            projected = tm.ok(u.Infra.protocol_model_sources(workspace))

        rendered = projected[destination.relative_to(root)]
        module = ast.parse(rendered)
        guarded = {
            alias.asname or alias.name
            for node in module.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
            for statement in node.body
            if isinstance(statement, ast.ImportFrom)
            for alias in statement.names
        }
        imports = {
            alias.asname or alias.name
            for node in ast.walk(module)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        annotations = (
            node.annotation
            for node in ast.walk(module)
            if isinstance(node, ast.AnnAssign | ast.arg) and node.annotation is not None
        )
        referenced = {
            name.id
            for annotation in annotations
            for name in ast.walk(annotation)
            if isinstance(name, ast.Name) and name.id in imports
        }
        runtime_names = {
            name.id
            for node in ast.walk(module)
            if isinstance(node, ast.ClassDef)
            for expression in (*node.bases, *node.decorator_list)
            for name in ast.walk(expression)
            if isinstance(name, ast.Name)
        }
        annotation_only = referenced - runtime_names
        tm.that(annotation_only, empty=False)
        tm.ok(
            annotation_only <= guarded,
            msg=f"unguarded annotation imports: "
            f"{annotation_only - guarded}\n{rendered}",
        )

    @staticmethod
    def test_type_checking_annotation_imports_reach_the_projection(
        tmp_path: Path,
    ) -> None:
        """Names a model imports only under TYPE_CHECKING are imported by its mirror."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                "class Models:\n    pass\nm = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "views.py": (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                "from pydantic import BaseModel\n"
                "if TYPE_CHECKING:\n"
                "    from collections.abc import KeysView\n"
                "class FlextTestProjectModelsViews:\n"
                "    class Bag(BaseModel):\n"
                "        def keys(self) -> KeysView[str]:\n"
                "            return {}.keys()\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with infra.rope_workspace(root) as workspace:
            projected = tm.ok(u.Infra.protocol_model_sources(workspace))

        rendered = next(
            source for path, source in projected.items() if path.name == "views.py"
        )
        tm.ok("KeysView[str]" in rendered)
        tm.ok("from collections.abc import KeysView" in rendered)

    @staticmethod
    def test_consumer_bootstrap_never_plans_the_infra_facade(tmp_path: Path) -> None:
        """A non-infra package with protocol sources bootstraps in its own tree."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "_models" / "payload.py": (
                "from flext_core import m\n"
                "class FlextTestProjectModelsPayload:\n"
                "    class Packet(m.ContractModel):\n"
                "        visible: str\n"
                "__all__ = ['FlextTestProjectModelsPayload']\n"
            ),
            package / "models.py": (
                f"from {package.name}._models.payload import "
                "FlextTestProjectModelsPayload\n"
                "class FlextTestProjectModels(FlextTestProjectModelsPayload):\n"
                "    pass\n"
                "m = FlextTestProjectModels\n"
                "__all__ = ['FlextTestProjectModels', 'm']\n"
            ),
            package / "_protocols" / "reader.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class FlextTestProjectProtocolsReader:\n"
                "    @runtime_checkable\n    class Reader(Protocol):\n"
                "        @property\n        def visible(self) -> str: ...\n"
                "__all__ = ['FlextTestProjectProtocolsReader']\n"
            ),
            package / "protocols.py": (
                f"from {package.name}._protocols.reader import "
                "FlextTestProjectProtocolsReader\n"
                "class FlextTestProjectProtocols(FlextTestProjectProtocolsReader):\n"
                "    pass\n"
                "p = FlextTestProjectProtocols\n"
                "__all__ = ['FlextTestProjectProtocols', 'p']\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))

        tm.ok(
            u.Infra.bootstrap_protocol_model_sources(
                root, ports=infra.codegen_conform_collaborators()
            )
        )

        tm.fail((root / c.Infra.DEFAULT_SRC_DIR / c.Infra.PACKAGE_IMPORT_NAME).exists())
