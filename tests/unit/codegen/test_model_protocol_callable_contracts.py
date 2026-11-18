"""Model protocols preserve native instance capabilities without implementation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsModelProtocolCallableContracts:
    """Exercise public projection, actual Pydantic models and native consumers."""

    @staticmethod
    def _import_generated_module(path: Path) -> ModuleType:
        """Import a generated module from its file through the import system.

        Returns:
            The imported module.

        """
        spec = tm.not_none(spec_from_file_location("generated_protocols", path))
        module = module_from_spec(spec)
        tm.not_none(spec.loader).exec_module(module)
        return module

    @staticmethod
    def _model_workspace(tmp_path: Path, declaration: str) -> tuple[Path, Path]:
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
            package / "_models/payload.py": declaration,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return root, package

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("declaration", "base", "expectation"),
        [
            (
                (
                    "class Mutable(BaseModel):\n    name: str\n"
                    "    def read(self) -> str:\n        return self.name\n"
                ),
                "Mutable",
                ("str", "'sample'"),
            ),
            (
                (
                    "class Mutable[T](BaseModel):\n    name: T\n"
                    "    def read(self) -> T:\n        return self.name\n"
                ),
                "Mutable[str]",
                ("str", "'sample'"),
            ),
            (
                (
                    "class Mutable[T](BaseModel):\n    name: T\n"
                    "    def read(self) -> T:\n        return self.name\n"
                    "class Intermediate[U](Mutable[U]): pass\n"
                ),
                "Intermediate[str]",
                ("str", "'sample'"),
            ),
            (
                (
                    "class Mutable[T](BaseModel):\n    name: T\n"
                    "    def read(self) -> T:\n        return self.name\n"
                ),
                "Mutable[dict[str, list[int]]]",
                ("dict[str, list[int]]", "{'sample': [1]}"),
            ),
        ],
    )
    def test_frozen_model_does_not_inherit_a_writable_protocol(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        declaration: str,
        base: str,
        expectation: tuple[str, str],
    ) -> None:
        """A frozen descendant retains specialized inherited fields and methods."""
        annotation, sample = expectation
        root, package = TestsModelProtocolCallableContracts._model_workspace(
            tmp_path,
            "from pydantic import BaseModel, ConfigDict\n"
            + declaration
            + "class ModelsPayload:\n"
            f"    class Frozen({base}):\n"
            "        model_config = ConfigDict(frozen=True)\n"
            "__all__ = ['Mutable', 'ModelsPayload']\n",
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in planned.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            "from inspect import getattr_static\n"
            "from typing import get_type_hints\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            f"value = m.Frozen(name={sample})\n"
            "assert isinstance(value, p.Frozen)\n"
            "descriptor = getattr_static(p.Frozen, 'name')\n"
            "assert isinstance(descriptor, property)\n"
            "assert descriptor.fset is None\n"
            f"assert get_type_hints(descriptor.fget)['return'] == {annotation}\n"
            f"assert get_type_hints(p.Frozen.read)['return'] == {annotation}\n"
            f"assert value.read() == {sample}\n"
            f"assert value.name == {sample}\n",
            cwd=root,
        )

    @staticmethod
    def test_decorated_model_behavior_is_not_projected_as_a_protocol_member(
        tmp_path: Path,
    ) -> None:
        """Validators stay model behavior; properties stay structural contracts."""
        root, package = TestsModelProtocolCallableContracts._model_workspace(
            tmp_path,
            "from typing import Annotated, Self\n"
            "from pydantic import BaseModel, field_validator\n\n"
            "def require_release_commands(function):\n    return function\n\n"
            "class ModelsPayload:\n"
            "    class Request(BaseModel):\n"
            "        name: str\n\n"
            "        @field_validator('name')\n"
            "        @classmethod\n"
            "        def normalize_name(cls, value: str) -> str:\n"
            "            return value.strip()\n\n"
            "        @require_release_commands\n"
            "        def require_name(self) -> Self:\n"
            "            return self\n\n"
            "        @property\n"
            "        def normal_name(self) -> str:\n"
            "            return self.name\n\n"
            "        @property\n"
            "        def annotated_name(self) -> Annotated[str, 'metadata']:\n"
            "            return self.name\n",
        )

        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = projected[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("@runtime_checkable" in generated)
        tm.ok("@property\n        def normal_name(self) -> str: ..." in generated)
        tm.ok("@property\n        def annotated_name(self) -> str: ..." in generated)
        for name in ("normalize_name", "require_name"):
            tm.fail(name in generated)
        tm.fail("require_release_commands" in generated)
        tm.fail("pydantic" in generated)
        ast.parse(generated, filename="generated-payload.py")

    @staticmethod
    def test_cached_property_member_keeps_its_source_descriptor(
        tmp_path: Path,
    ) -> None:
        """A cached model member projects the descriptor the checkers accept."""
        root, package = TestsModelProtocolCallableContracts._model_workspace(
            tmp_path,
            "from functools import cached_property\n"
            "from pydantic import BaseModel\n\n"
            "class ModelsPayload:\n"
            "    class Artifact(BaseModel):\n"
            "        name: str\n\n"
            "        @cached_property\n"
            "        def artifact(self) -> str:\n"
            "            return self.name\n",
        )

        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = projected[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("from functools import cached_property" in generated)
        tm.ok("@cached_property\n        def artifact(self) -> str: ..." in generated)
        tm.fail("@property\n        def artifact(self)" in generated)
        ast.parse(generated, filename="generated-payload.py")

    @staticmethod
    def test_quoted_root_model_reference_projects_sibling_protocol(
        tmp_path: Path,
    ) -> None:
        """A quoted nested model reference maps to its projected protocol."""
        root, package = TestsModelProtocolCallableContracts._model_workspace(
            tmp_path,
            "from __future__ import annotations\n"
            "from typing import Literal\n"
            "from pydantic import BaseModel, RootModel\n\n"
            "class ModelsPayload:\n"
            "    class Bead(BaseModel):\n"
            "        status: Literal['open']\n\n"
            "    class BeadShow(RootModel[tuple['ModelsPayload.Bead']]):\n"
            "        pass\n",
        )

        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = projected[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("def root(self) -> tuple[ProtocolsPayload.Bead]:" in generated)
        tm.ok('Literal["open"]' in generated)
        tm.fail("ModelsPayload.Bead" in generated)
        ast.parse(generated, filename="generated-payload.py")

    @staticmethod
    def test_sole_upstream_letter_must_expose_every_reference(
        tmp_path: Path,
    ) -> None:
        """A single upstream provider is not elected for members it lacks."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-infra",
            package_name="flext_infra",
        )
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import FlextInfraModelsPayload\n"
                "class FlextInfraModels(FlextInfraModelsPayload): pass\n"
                "m = FlextInfraModels\n"
            ),
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class FlextInfraProtocols(FlextCliProtocols): pass\n"
                "p = FlextInfraProtocols\n"
            ),
            package / "_models/payload.py": (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                "from pydantic import BaseModel\n"
                "if TYPE_CHECKING:\n"
                "    from flext_infra.protocols import p\n"
                "class FlextInfraModelsPayload:\n"
                "    class Request(BaseModel):\n"
                "        value: p.AbsentUpstreamContract\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        before = {path: path.read_bytes() for path in package.rglob("*.py")}

        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(ValueError, match="no unique upstream package exposing"),
        ):
            u.Infra.protocol_model_sources_from_source(root, binding[0])
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("frozen", "typed_config"), [(False, True), (True, True), (True, False)]
    )
    def test_authored_methods_and_copy_port_preserve_native_behavior(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        frozen: bool,
        typed_config: bool,
    ) -> None:
        """Fields, decorators, async methods and RootModel copy remain truthful."""
        config_type = ": ClassVar[ConfigDict]" if typed_config else ""
        root, package = TestsModelProtocolCallableContracts._model_workspace(
            tmp_path,
            (
                "from __future__ import annotations\n"
                "from typing import ClassVar\n"
                "from pydantic import BaseModel, ConfigDict, RootModel\n"
                "class ModelsPayload:\n"
                "    class Entity(BaseModel):\n"
                f"        model_config{config_type} = ConfigDict(\n"
                f"            frozen={frozen!r})\n"
                "        owner: str\n        table: str\n"
                "        def nome(self) -> str:\n"
                "            return self.owner + '.' + self.table\n"
                "        def format(self, value: int"
                ", /, *, prefix: str = 'x') -> str:\n"
                "            return prefix + str(value)\n"
                "        @staticmethod\n"
                "        def ordinal(value: int) ->"
                " int:\n            return value + 1\n"
                "        @classmethod\n"
                "        def label(cls, value: str) -> "
                "str:\n            return value.upper()\n"
                "        async def text(self, value: s"
                "tr) -> str:\n            return value\n"
                "        @property\n"
                "        def dotted(self) -> str:\n            return self.nome()\n"
                "    class Names(RootModel[tuple[str, ...]]):\n"
                "        def join(self, separator: str = ',') -> str:\n"
                "            return separator.join(self.root)\n"
                "__all__ = ['ModelsPayload']\n"
            ),
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in planned.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        generated = planned[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("from flext_core import FlextProtocols" in generated)
        tm.ok("class Entity(FlextProtocols.ModelCopy, Protocol):" in generated)
        tm.fail("from flext_core import p\n" in generated)
        native_consumer(
            "import asyncio\n"
            "from inspect import iscoroutinefunction, signature\n"
            "from typing import get_type_hints, is_protocol, Self\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_core import FlextProtocols\n"
            "from flext_tests import tm\n"
            "value = m.Entity(owner='O', table='T')\n"
            "tm.ok(is_protocol(p.Entity))\n"
            "tm.ok(isinstance(value, p.Entity))\n"
            "tm.ok(issubclass(p.Entity, FlextProtocols.ModelCopy))\n"
            "tm.that(value.nome(), eq='O.T')\n"
            "for name in ('nome', 'format', 'ordinal', 'label', 'text'):\n"
            "    tm.that(signature(getattr(p.Entity, name)), eq=signature(geta"
            "ttr(m.Entity, name)))\n"
            "tm.ok(iscoroutinefunction(p.Entity.text))\n"
            "tm.that(asyncio.run(value.text('actual')), eq='actual')\n"
            "tm.ok(get_type_hints(p.Entity.model_copy)['return'] is Self)\n"
            "copy = value.model_copy(update={'owner': 'P'})\n"
            "tm.ok(type(copy) is type(value))\n"
            "tm.that(copy.nome(), eq='P.T')\n"
            "tm.that(value.nome(), eq='O.T')\n"
            "names = m.Names(('first', 'second'))\n"
            "tm.ok(isinstance(names, p.Names))\n"
            "tm.that(names.model_copy().join('|'), eq='first|second')\n"
            "tm.ok(isinstance(vars(p.Entity).get('owner'), property))\n"
            "tm.ok(isinstance(vars(p.Entity)['dotted'], property))\n",
            cwd=root,
        )

    @staticmethod
    def test_infra_source_protocol_uses_cli_base_without_core_facade_name(
        tmp_path: Path,
    ) -> None:
        """An Infra mirror executes with its actual CLI protocol ancestry bound."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-infra",
            package_name="flext_infra",
        )
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import FlextInfraModelsPayload\n"
                "class FlextInfraModels(FlextInfraModelsPayload): pass\n"
                "m = FlextInfraModels\n"
            ),
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class FlextInfraProtocols(FlextCliProtocols): pass\n"
                "p = FlextInfraProtocols\n"
            ),
            package / "_models/payload.py": (
                "from pydantic import BaseModel\n"
                "class FlextInfraModelsPayload:\n"
                "    class Request(BaseModel):\n"
                "        name: str\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        generated = planned[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("from flext_cli import FlextCliProtocols" in generated)
        tm.ok("class Request(FlextCliProtocols.ModelCopy, Protocol):" in generated)
        tm.fail("from flext_core import p\n" in generated)
        destination = package / "_protocols" / "payload.py"
        tm.ok(u.Cli.ensure_dir(destination.parent))
        tm.ok(u.Cli.atomic_write_text_file(destination, generated))
        holder = TestsModelProtocolCallableContracts._import_generated_module(
            destination
        ).FlextInfraProtocolsPayload
        tm.that(isinstance(holder, type), eq=True)
        tm.that("Request" in vars(holder), eq=True)

    @staticmethod
    def test_authored_protocol_keeps_runtime_base_import_outside_type_checking(
        tmp_path: Path,
    ) -> None:
        """An authored header retains imports required while class bases evaluate."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-infra",
            package_name="flext_infra",
        )
        sources = {
            package / "models.py": (
                f"from {package.name}._models.payload import FlextInfraModelsPayload\n"
                "class FlextInfraModels(FlextInfraModelsPayload): pass\n"
                "m = FlextInfraModels\n"
            ),
            package / "protocols.py": (
                "from flext_cli import FlextCliProtocols\n"
                "class FlextInfraProtocols(FlextCliProtocols): pass\n"
                "p = FlextInfraProtocols\n"
            ),
            package / "_models/payload.py": (
                "from pydantic import BaseModel\n"
                "class FlextInfraModelsPayload:\n"
                "    class Request(BaseModel):\n"
                "        name: str\n"
            ),
            package / "_protocols/payload.py": (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING, Protocol\n\n"
                "if TYPE_CHECKING:\n"
                "    from flext_infra.protocols import p\n\n"
                "class FlextInfraProtocolsPayload:\n"
                "    class Existing(Protocol):\n"
                "        value: p.Infra.Existing\n"
                "__all__ = ['FlextInfraProtocolsPayload']\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )

        destination = (package / "_protocols" / "payload.py").relative_to(root)
        generated = planned[destination]
        tm.ok("from flext_cli import FlextCliProtocols\n" in generated)
        tm.ok(u.Cli.atomic_write_text_file(root / destination, generated))
        holder = TestsModelProtocolCallableContracts._import_generated_module(
            root / destination
        ).FlextInfraProtocolsPayload
        tm.that("Request" in vars(holder), eq=True)

    @classmethod
    @c.Tests.MARK.parametrize(
        ("declaration", "failure", "message"),
        [
            (
                "        @staticmethod\n        def method(self) -> int: return 1\n",
                TypeError,
                "parameter has no annotation",
            ),
            (
                "        def method(self, value) -> int: return value\n",
                TypeError,
                "parameter has no annotation",
            ),
            (
                (
                    "        def method(self, value: int = default()) -> int:\n"
                    "            return value\n"
                ),
                ValueError,
                "default has unproved runtime effects",
            ),
        ],
    )
    def test_unproved_callable_contract_fails_without_source_effects(
        cls,
        tmp_path: Path,
        declaration: str,
        failure: type[Exception],
        message: str,
    ) -> None:
        """The projector rejects missing evidence rather than emitting a false port."""
        root, package = cls._model_workspace(
            tmp_path,
            "from pydantic import BaseModel\n"
            "def wrapper(function): return function\n"
            "def default() -> int: return 1\n"
            "class ModelsPayload:\n"
            "    class Entity(BaseModel):\n"
            "        value: int\n" + declaration,
        )
        before = {path: path.read_bytes() for path in package.rglob("*.py")}
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(failure, match=message),
        ):
            u.Infra.protocol_model_sources_from_source(root, binding[0])
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @classmethod
    def test_local_copy_override_retains_its_actual_signature(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A local override is not widened to the broader native update capability."""
        root, package = cls._model_workspace(
            tmp_path,
            "from __future__ import annotations\n"
            "from typing import Self\n"
            "from pydantic import BaseModel\n"
            "class ModelsPayload:\n"
            "    class Entity(BaseModel):\n"
            "        value: int\n"
            "        def model_copy(self, *, deep: bool = False) -> Self:\n"
            "            return super().model_copy(deep=deep)\n",
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in planned.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            "from inspect import signature\n"
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "value = m.Entity(value=3)\n"
            "tm.ok(isinstance(value, p.Entity))\n"
            "tm.that(signature(p.Entity.model_copy"
            "), eq=signature(m.Entity.model_copy))\n"
            "tm.that(tuple(signature(p.Entity.model_"
            "copy).parameters), eq=('self', 'deep'))\n"
            "tm.that(value.model_copy().value, eq=3)\n",
            cwd=root,
        )

    @classmethod
    def test_nested_model_contracts_have_authenticated_sibling_owners(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """Hoisting the declaring path keeps the model class API and value ports."""
        root, package = cls._model_workspace(
            tmp_path,
            "from pydantic import BaseModel, ConfigDict\n"
            "class ModelsPayload:\n"
            "    class Envelope(BaseModel):\n"
            "        model_config = ConfigDict(frozen=True)\n"
            "        class Page(BaseModel):\n"
            "            value: int\n"
            "        data: Page\n",
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in planned.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        native_consumer(
            "from typing import is_protocol\n"
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_tests import tm\n"
            "page = m.Envelope.Page(value=7)\n"
            "value = m.Envelope(data=page)\n"
            "tm.ok(value.data is page)\n"
            "tm.ok(is_protocol(p.Envelope))\n"
            "tm.ok(is_protocol(p.EnvelopePage))\n"
            "tm.ok(isinstance(value, p.Envelope))\n"
            "tm.ok(isinstance(page, p.EnvelopePage))\n"
            "tm.fail(hasattr(p.Envelope, 'Page'))\n"
            "tm.that(value.model_dump(), eq={'data': {'value': 7}})\n"
            "tm.ok(type(value.data) is m.Envelope.Page)\n",
            cwd=root,
        )

    @classmethod
    def test_native_schema_preserves_mutable_structural_field_capabilities(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """Native schemas preserve mutable field and container capabilities."""
        root, package = cls._model_workspace(
            tmp_path,
            "from __future__ import annotations\n"
            "from typing import Annotated\n"
            "from pydantic import BaseModel\n"
            "from flext_core import t\n"
            "from flext_test_project.protocols import p\n"
            "class ModelsPayload:\n"
            "    class Envelope(BaseModel):\n"
            "        class Page(BaseModel):\n"
            "            value: int\n"
            "        child: Page\n"
            "        pages: dict[str, Page]\n",
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        for relative, source in planned.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        generated = planned[(package / "_protocols" / "payload.py").relative_to(root)]
        tm.ok("child: p.EnvelopePage" in generated)
        tm.ok("pages: dict[str, p.EnvelopePage]" in generated)
        tm.fail("def child(" in generated)
        tm.fail("def pages(" in generated)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_tests import tm\n"
            "page = m.Envelope.Page(value=7)\n"
            "value = m.Envelope(child=page, pages={'first': page})\n"
            "tm.ok(isinstance(value, p.Envelope))\n"
            "tm.ok(isinstance(value.child, p.EnvelopePage))\n"
            "tm.ok(isinstance(value.pages['first'], p.EnvelopePage))\n"
            "identity = id(value)\n"
            "replacement = m.Envelope.Page(value=8)\n"
            "value.child = replacement\n"
            "value.pages['second'] = replacement\n"
            "tm.ok(value.child is replacement)\n"
            "tm.ok(value.pages['second'] is replacement)\n"
            "tm.that(id(value), eq=identity)\n",
            cwd=root,
        )

    @classmethod
    def test_nested_qualified_owner_collision_is_explicit(cls, tmp_path: Path) -> None:
        """Two distinct declarations cannot acquire the same projected identity."""
        root, package = cls._model_workspace(
            tmp_path,
            "from pydantic import BaseModel\n"
            "class ModelsPayload:\n"
            "    class Envelope(BaseModel):\n"
            "        class Page(BaseModel):\n"
            "            value: int\n"
            "    class EnvelopePage(BaseModel):\n"
            "        value: str\n",
        )
        before = {path: path.read_bytes() for path in package.rglob("*.py")}
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(ValueError, match="competing generated Protocol route"),
        ):
            u.Infra.protocol_model_sources_from_source(root, binding[0])
        tm.that({path: path.read_bytes() for path in before}, eq=before)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("language", "model_text"),
        [
            ("en", "Source-derived structural"),
            ("pt-BR", "Contratos estruturais"),
        ],
    )
    def test_protocol_templates_preserve_the_declared_documentation_language(
        language: t.Infra.DocumentationLanguage,
        model_text: str,
    ) -> None:
        """The same native render contexts serve English and Portuguese owners."""
        templates = u.Infra.codegen_templates_root(config.Infra.codegen)
        model = m.Infra.ModelProtocolRenderContext(
            header=c.Infra.AUTOGEN_HEADER,
            copyright_notice="Copyright (c) 2026 FLEXT Team.",
            owner="ProtocolsPayload",
            imports=("from typing import Protocol, runtime_checkable",),
            sibling_import_lines=(),
            contracts=(
                m.Infra.ModelProtocolRenderContext.ModelProtocolContract(
                    name="Payload", type_parameters=(), declarations=("value: str",)
                ),
            ),
            documentation_language=language,
        )
        rendered = tm.ok(
            u.Cli.template_render(templates / c.Infra.TEMPLATE_MODEL_PROTOCOL, model)
        )
        tm.ok(model_text in rendered)
        ast.parse(rendered)
