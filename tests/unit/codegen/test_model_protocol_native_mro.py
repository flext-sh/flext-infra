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
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.facade_source_project(root) as binding:
            if requested == "foreign":
                with u.Tests.raises(ValueError, match="model contract collides"):
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
        """Protocol imports and type hints do not execute Pydantic Field metadata."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "models.py": (
                "class Models:\n    class Project:\n        pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n"
                "    class Project:\n        pass\n"
                "    class Cli:\n"
                "        class AtomicFileState:\n            pass\n"
                "    class Infra:\n"
                "        class WorkspaceThing:\n            pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
                "from typing import Annotated as TypeMetadata\n"
                "from flext_cli import m\n"
                "from pydantic import BaseModel\n\n"
                "class FlextInfraModelsWorkspace:\n"
                "    class WorkspaceThing:\n        pass\n\n"
                "class ModelsPayload:\n"
                "    class Request(BaseModel):\n"
                "        title: TypeMetadata[str, m.Field(description='title')]\n"
                "        receipt: TypeMetadata[p.Cli.AtomicFileState | None, "
                "m.Field()]\n"
                "        workspace: FlextInfraModelsWorkspace.WorkspaceThing\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        destination = (package / "_protocols" / "payload.py").relative_to(root)
        generated = projected[destination]
        tm.ok("title: str" in generated)
        tm.ok("receipt: p.Cli.AtomicFileState | None" in generated)
        tm.ok(f"from {package.name}.protocols import p" in generated)
        tm.ok("m.Field" not in generated)
        tm.ok("m.Cli" not in generated)
        tm.ok("FlextInfraModelsWorkspace" not in generated)
        tm.ok("TypeMetadata" not in generated)
        tm.ok(u.Cli.atomic_write_text_file(root / destination, generated))
        owner = u.derive_class_stem(package.name.replace("_", "-"))
        owner += "ProtocolsPayload"
        module_name = package.name + "._protocols.payload"
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"module = importlib.import_module({module_name!r})\n"
            f"owner = getattr(module, {owner!r})\n"
            "tm.ok(is_protocol(owner.Request))\n"
            "tm.that(get_type_hints(owner.Request)['title'], eq=str)\n"
            "tm.that(get_type_hints(owner.Request)['receipt'], "
            "eq=module.p.Cli.AtomicFileState | None)\n"
            "tm.that(get_type_hints(owner.Request.workspace.fget)['return'], "
            "eq=module.p.Infra.WorkspaceThing)\n"
            "tm.ok('m' not in vars(module))\n",
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
            package / "models.py": "class Models:\n    pass\nm = Models\n",
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
        owner = u.derive_class_stem(package.name.replace("_", "-"))
        owner += "ProtocolsConsumer"
        native_consumer(
            "from typing import get_type_hints\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"module = importlib.import_module('{package.name}._protocols.consumer')\n"
            f"from {package.name}.protocols import p\n"
            f"owner = getattr(module, {owner!r})\n"
            "for contract in (owner.Base, owner.Request):\n"
            "    tm.that(get_type_hints(contract.entity.fget)['return'], "
            "eq=p.Infra.Entity)\n",
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
        owner = u.derive_class_stem(package.name.replace("_", "-"))
        owner += "ProtocolsDiamond"
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"module = importlib.import_module('{package.name}._protocols.diamond')\n"
            f"contract = getattr(module, {owner!r}).Payload\n"
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
            f"owner = getattr(module, {owner!r})\n"
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
    def test_normalized_authored_contract_converges_with_field_model_source(
        tmp_path: Path,
    ) -> None:
        """A normalized protocol holder compares structurally with its model."""
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
                "class Models:\n    pass\nm = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "class Protocols:\n    class Infra:\n        pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "_models" / "payload.py": (
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
        tm.that(projected[relative], eq=authored)

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
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from flext_test_project import p, t\n\n"
            f"class {owner}:\n"
            "    class Reader(t.Protocol):\n"
            "        record: p.Infra.Record\n"
            "        value: t.JsonValue\n"
            "        def read(self, value: t.JsonValue) -> p.Infra.Record: ...\n"
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
                "class Typings:\n    JsonValue = str\nt = Typings\n"
            ),
            package / "_models" / "payload.py": (
                "from flext_test_project import p, t\n"
                "from pydantic import BaseModel\n"
                "class FlextTestProjectModelsPayload:\n"
                "    class Payload(BaseModel):\n"
                "        record: p.Infra.Record\n"
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
        tm.ok("if TYPE_CHECKING:\n    from flext_test_project import p, t" in rendered)
        tm.fail("\nfrom flext_test_project import p\n" in rendered)
        tm.fail("\nfrom flext_test_project import t\n" in rendered)

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
