"""Native model ancestry projected through the public protocol owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from flext_infra import c, infra
from flext_infra._models.codegen_toolchain import FlextInfraModelsCodegenToolchain
from flext_infra._models.deps import FlextInfraModelsDeps
from flext_infra._models.gates import FlextInfraModelsGates
from flext_infra._models.workspace import FlextInfraModelsWorkspace
from flext_infra._utilities.protocol_models import FlextInfraUtilitiesModelsProtocol
from tests import p, tm, u


class TestsModelProtocolNativeMro:
    """Compare generated contracts with the real Pydantic consumer."""

    @staticmethod
    @pytest.mark.parametrize("requested", ["visible", "foreign"])
    def test_existing_narrow_port_retains_model_owner(
        tmp_path: Path, requested: str
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
                with pytest.raises(ValueError, match="model contract collides"):
                    u.Infra.protocol_model_sources_from_source(root, binding[0])
                return
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        witness = next(
            text
            for path, text in projected.items()
            if path.name == c.Infra.MODEL_PROTOCOL_CONFORMANCE_FILENAME
        )
        tm.ok("type[p.Project.Packet]" in witness)
        tm.ok("return m.Project.Packet" in witness)
        tm.that(
            (package / "_protocols" / "reader.py").read_text(),
            eq=sources[package / "_protocols" / "reader.py"],
        )

    @staticmethod
    def test_runtime_dependency_plan_schema_uses_the_port_owner() -> None:
        """A structural manifest remains schema-safe at the public model boundary."""
        schema = FlextInfraModelsDeps.RuntimeDependencyPlan.model_json_schema()
        tm.ok(isinstance(schema, dict))

    @staticmethod
    def test_deptry_scan_schema_uses_the_port_owner() -> None:
        """A gate model schema accepts its structural source manifest port."""
        schema = FlextInfraModelsGates.DeptryScan.model_json_schema()
        tm.ok(isinstance(schema, dict))

    @staticmethod
    def test_codegen_source_authority_schema_uses_the_port_owner() -> None:
        """Source authority completes its runtime Pydantic core schema."""
        FlextInfraModelsWorkspace.CodegenSourceAuthority.model_rebuild()
        tm.ok(FlextInfraModelsWorkspace.CodegenSourceAuthority.__pydantic_complete__)
        tm.ok(
            isinstance(
                FlextInfraModelsWorkspace.CodegenSourceAuthority.__pydantic_core_schema__,
                dict,
            )
        )

    @staticmethod
    def test_mise_toolchain_sources_schema_uses_the_port_owner() -> None:
        """Computed source fields rebuild with their structural state port."""
        FlextInfraModelsCodegenToolchain.MiseToolchainWorkspacePlan.model_rebuild()
        tm.ok(
            FlextInfraModelsCodegenToolchain.MiseToolchainWorkspacePlan.__pydantic_complete__
        )

    @staticmethod
    def test_source_inventory_does_not_open_missing_protocol_model_facade(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The real repository plans before its incomplete facade is importable."""
        root = Path(__file__).parents[3]
        module_name = "flext_infra._models.workspace"
        monkeypatch.setattr(infra, "rope_workspace", None)
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        destination = Path("src/flext_infra/_protocols/workspace.py")
        tm.ok(destination in projected)
        tm.ok("ProcessNativeToolEvidence" in projected[destination])
        tm.ok(module_name not in sys.modules)

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
                "        receipt: TypeMetadata[p.Cli.AtomicFileState | None, m.Field()]\n"
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
        tm.ok("@property\n        def title(self) -> str: ..." in generated)
        tm.ok(
            "@property\n        def receipt(self) -> p.Cli.AtomicFileState | None: ..."
            in generated
        )
        tm.ok(
            "@property\n        def workspace(self) -> p.Infra.WorkspaceThing: ..."
            in generated
        )
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
            "tm.that(get_type_hints(owner.Request.title.fget)['return'], eq=str)\n"
            "tm.that(get_type_hints(owner.Request.receipt.fget)['return'], "
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
        tm.ok("@property\n        def title(self) -> str: ..." in generated)
        tm.ok("@property\n        def summary(self) -> str: ..." in generated)
        tm.fail("incomplete" in generated)
        ast.parse(generated, filename="generated-payload.py")

    @staticmethod
    def test_generated_source_parse_error_identifies_owner_and_path() -> None:
        """Plan diagnostics identify the invalid generated Protocol artifact."""
        with pytest.raises(
            ValueError,
            match=(
                "generated Protocol source is invalid: "
                "owner=ProtocolsPayload path=generated-payload.py"
            ),
        ):
            FlextInfraUtilitiesModelsProtocol._ModelProtocolProjection._source_validate_generated_module(
                "class Broken:\n    @property\n",
                Path("generated-payload.py"),
                "ProtocolsPayload",
            )

    @staticmethod
    def test_source_mirror_resolves_model_holder_from_another_module(
        tmp_path: Path,
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
        tm.that(
            generated.count(
                "@property\n        def entity(self) -> p.Infra.Entity: ..."
            ),
            eq=2,
        )
        tm.ok("ModelHolderB.Entity" not in generated)
        tm.ok("m." not in generated)
        tm.ok("@runtime_checkable" in generated)
        tm.ok(
            "if TYPE_CHECKING:\n"
            f"    from {package.name}.protocols import p" in generated
        )

    @staticmethod
    @pytest.mark.parametrize("bases", ["Left, Right", "Right, Left"])
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
        tm.that(
            tuple(projected),
            eq=((package / "_protocols" / "diamond.py").relative_to(root),),
        )
        for path, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, source))
        modules = tuple(
            ".".join((root / path).relative_to(package.parent).with_suffix("").parts)
            for path in projected
        )
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"modules = [importlib.import_module(name) for name in {modules!r}]\n"
            "contracts = [member for module in modules\n"
            "    for owner in vars(module).values() if isinstance(owner, type)\n"
            "    for member in vars(owner).values() if isinstance(member, type)\n"
            "    and is_protocol(member) and member.__name__ == 'Payload']\n"
            "tm.that(len(contracts), eq=1)\n"
            "model = m.Domain.Payload\n"
            "hints = {name: get_type_hints(getattr(contracts[0], name).fget)['return']\n"
            "    for name in model.model_fields}\n"
            "tm.that(set(hints), eq=set(model.model_fields))\n"
            "for name, field in model.model_fields.items():\n"
            "    tm.that(hints[name], eq=field.annotation)\n"
            "payload = model(marker=model.model_fields['marker'].annotation('17'),\n"
            "                title='projected')\n"
            "tm.that(type(payload.marker), eq=hints['marker'])\n"
            "tm.ok(isinstance(payload, contracts[0]))\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("authored", [False, True])
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
        tm.that(set(projected), eq=expected)
        for path, source in projected.items():
            tm.ok(u.Cli.ensure_dir((root / path).parent))
            tm.ok(u.Cli.atomic_write_text_file(root / path, source))
        with infra.rope_workspace(root) as workspace:
            repeated = tm.ok(u.Infra.protocol_model_sources(workspace))
        tm.that(repeated, eq=projected)
        module_name = f"{package.name}._protocols._config.payload"
        native_consumer(
            "from typing import get_type_hints, is_protocol\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"module = importlib.import_module({module_name!r})\n"
            f"owner = getattr(module, {owner!r})\n"
            "tm.ok(is_protocol(owner.Request))\n"
            "tm.that(get_type_hints(owner.Request.title.fget)['return'], eq=str)\n"
            "tm.that(get_type_hints(owner.Response.count.fget)['return'], eq=int)\n"
            + ("tm.ok(callable(owner.Worker.execute))\n" if authored else ""),
            cwd=root,
        )
        if authored:
            result = projected[(package / "_protocols" / relative).relative_to(root)]
            tm.ok(
                "    # Keep the authored interface and its documentation "
                "byte-for-byte.\n"
                "    class Worker(Protocol):\n"
                "        def execute(self, command: str) -> int: ...\n" in result,
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
            pytest.raises(ValueError, match="incompatible authored protocol contract"),
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
    def test_explicit_writable_authored_property_is_not_normalized(
        tmp_path: Path,
    ) -> None:
        """An authored setter remains the contract owner, not a generated default."""
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
        rendered = projected[destination.relative_to(root)]
        tm.ok(
            "@title.setter\n        def title(self, value: str) -> None: ..."
            in rendered
        )
        tm.fail("title: str" in rendered)

    @staticmethod
    def test_authored_protocol_annotation_facades_stay_type_checking(
        tmp_path: Path,
    ) -> None:
        """Source completion keeps protocol annotation facades out of runtime imports."""
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
