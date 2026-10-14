"""Public evidence for callback admission before native compiler operations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from sys import executable

import pytest

from tests import c, tm, u


class TestsNativeCompilerAdmission:
    """Observe native consumers and unchanged effects during provenance rejection."""

    @staticmethod
    @pytest.mark.parametrize(
        "module_name",
        ["flext_native_module_provider", "vendor_native_module_provider"],
    )
    def test_native_module_subclass_is_observed_without_attribute_callbacks(
        tmp_path: Path,
        module_name: str,
    ) -> None:
        """Native module storage admits both namespaces without replaying getters."""
        package = tmp_path / module_name
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import sys\n"
                "from pathlib import Path\n"
                "from types import ModuleType\n"
                "reads = []\n"
                "marker = Path(__file__).with_suffix('.getter-effects')\n"
                "marker.write_bytes(b'')\n"
                "class Payload:\n"
                "    def operation(self):\n"
                "        return 'native'\n"
                "class NativeModule(ModuleType):\n"
                "    def __getattribute__(self, name):\n"
                "        reads.append(name)\n"
                "        with marker.open('a', encoding='utf-8') as stream:\n"
                "            stream.write(name + '\\n')\n"
                "        return ModuleType.__getattribute__(self, name)\n"
                "sys.modules[__name__].__class__ = NativeModule\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from types import ModuleType\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "name = sys.argv[2]\n"
            "module = importlib.import_module(name)\n"
            "namespace = vars(ModuleType)['__dict__'].__get__(module, type(module))\n"
            "assert module.Payload().operation() == 'native'\n"
            "before = tuple(namespace['reads'])\n"
            "assert before\n"
            "marker = namespace['marker']\n"
            "physical = marker.read_bytes()\n"
            "observed = native.capture((name,)).unwrap()\n"
            "assert tuple(namespace['reads']) == before\n"
            "assert marker.read_bytes() == physical\n"
            "assert any(item.binding == name and item.kind == 'module' "
            "for item in observed.bindings)\n"
            "bindings = {item.binding: item for item in observed.bindings}\n"
            "module_type = bindings[name + '.module_type']\n"
            "if module_type.kind == 'alias':\n"
            "    module_type = bindings[dict(module_type.operands)['target']]\n"
            "assert module_type.kind == 'class'\n"
            "assert module_type.supplier == name\n"
            "assert module_type.qualname == 'NativeModule'\n"
            "assert observed.modules == (name,)\n"
            "assert observed.sources\n"
            "result = provenance.loaded_import_sources(name)\n"
            "assert tuple(namespace['reads']) == before\n"
            "assert marker.read_bytes() == physical\n"
            "result.unwrap()\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), module_name],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["absent", "missing-spec", "broken-origin"])
    def test_imported_class_preserves_its_supplier_failure(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A failed supplier never becomes a successful third-party alias string."""
        package = tmp_path / "supplier_contract_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from .supplier import Payload\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "supplier.py",
                "class Payload:\n    def operation(self):\n        return 'native'\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('supplier_contract_provider')\n"
            "assert module.Payload().operation() == 'native'\n"
            "name = module.Payload.__module__\n"
            "supplier = sys.modules[name]\n"
            "defect = sys.argv[2]\n"
            "if defect == 'absent':\n"
            "    del sys.modules[name]\n"
            "elif defect == 'missing-spec':\n"
            "    supplier.__spec__ = None\n"
            "else:\n"
            "    supplier.__file__ = supplier.__file__ + '.absent'\n"
            "original = native.capture((name,))\n"
            "assert original.failure\n"
            "observed = native.capture((module.__name__,))\n"
            "assert observed.failure, observed\n"
            "assert observed.error == original.error, (observed, original)\n"
            "assert observed.error_code == original.error_code\n"
            "assert observed.exception is original.exception\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_source_proof_never_replays_an_absolute_import_effect(
        tmp_path: Path,
    ) -> None:
        """A source proof preserves effects even when staging cannot relocate them."""
        package = tmp_path / "absolute_effect_provider"
        marker = tmp_path / "absolute-import-effects"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "marker = __import__('pathlib').Path(" + repr(str(marker)) + ")\n"
                "with marker.open('a', encoding='utf-8') as stream:\n"
                "    stream.write('import\\n')\n"
                "class Payload:\n"
                "    def operation(self): return 'native'\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('absolute_effect_provider')\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
            "method = module.Payload.operation\n"
            "method.__code__ = method.__code__.replace(co_name='foreign')\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize(
        "feature",
        [
            "field-factory",
            "class-decorator",
            "metaclass",
            "set-name",
            "validator",
            "converter",
            "default-factory",
            "pre-init",
            "post-init",
            "field-transformer",
        ],
    )
    def test_attrs_callback_capabilities_authenticate_without_replay(
        tmp_path: Path,
        feature: str,
    ) -> None:
        """Authenticating native methods preserves legitimate construction callbacks."""
        package = tmp_path / "callback_provider"
        tm.ok(u.Cli.ensure_dir(package))
        options = "slots=True, unsafe_hash=True"
        declaration = "class Payload:\n"
        decorator = f"@attrs({options})\n"
        field = "    _value = attrib()\n"
        extra = ""
        if feature == "field-factory":
            field = "    _value = make_field()\n"
        elif feature == "class-decorator":
            decorator = "@decorate\n"
        elif feature == "metaclass":
            declaration = "class Payload(metaclass=Meta):\n"
        elif feature == "set-name":
            extra = "    marker = Descriptor()\n"
        elif feature == "validator":
            field = "    _value = attrib(validator=validate)\n"
        elif feature == "converter":
            field = "    _value = attrib(converter=convert)\n"
        elif feature == "default-factory":
            field = "    _value = attrib(factory=default_value)\n"
        elif feature == "pre-init":
            extra = "    def __attrs_pre_init__(self):\n        record('pre-init')\n"
        elif feature == "post-init":
            extra = "    def __attrs_post_init__(self):\n        record('post-init')\n"
        elif feature == "field-transformer":
            decorator = f"@attrs({options}, field_transformer=transform)\n"
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from attr import attrs, attrib\n"
                "from pathlib import Path\n"
                "effects = []\n"
                "marker = Path(__file__).with_suffix('.effects')\n"
                "marker.write_text('', encoding='utf-8')\n"
                "def record(effect):\n"
                "    effects.append(effect)\n"
                "    with marker.open('a', encoding='utf-8') as stream:\n"
                "        stream.write(effect + '\\n')\n"
                "def make_field():\n"
                "    record('field-factory')\n"
                "    return attrib()\n"
                "def decorate(cls):\n"
                "    record('class-decorator')\n"
                f"    return attrs({options})(cls)\n"
                "class Meta(type):\n"
                "    def __new__(cls, name, bases, namespace):\n"
                "        record('metaclass')\n"
                "        return super().__new__(cls, name, bases, namespace)\n"
                "class Descriptor:\n"
                "    def __set_name__(self, owner, name):\n"
                "        record('set-name')\n"
                "def validate(instance, attribute, value):\n"
                "    record('validator')\n"
                "    assert value >= 0\n"
                "def convert(value):\n"
                "    record('converter')\n"
                "    return int(value)\n"
                "def default_value():\n"
                "    record('default-factory')\n"
                "    return 1\n"
                "def transform(cls, attributes):\n"
                "    record('field-transformer')\n"
                "    return attributes\n" + decorator + declaration + field + extra,
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from attr import attrib\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('callback_provider')\n"
            "feature = sys.argv[2]\n"
            "payload = module.Payload() if feature == 'default-factory' "
            "else module.Payload(1)\n"
            "assert payload._value == 1\n"
            "assert feature in module.effects\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "counter = attrib().counter\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "assert attrib().counter == counter + 1\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
            "observed.unwrap()\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), feature],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        ["none", "field", "layout", "options", "alias", "code", "globals"],
    )
    def test_native_attrs_methods_preserve_fields_layout_and_factory_counter(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Slotted native methods authenticate without replaying field construction."""
        package = tmp_path / "attrs_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from attr import attrs, attrib\n"
                "@attrs(slots=True, unsafe_hash=True)\n"
                "class Payload:\n"
                "    _validators = attrib()\n",
            ),
        )
        consumer = (
            "import importlib, sys, types\n"
            "from attr import attrib\n"
            "from attrs import evolve, fields, inspect\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('attrs_provider')\n"
            "payload = module.Payload((1, 2))\n"
            "assert payload._validators == (1, 2)\n"
            "assert repr(payload) == 'Payload(_validators=(1, 2))'\n"
            "assert payload == module.Payload((1, 2))\n"
            "assert hash(payload) == hash(module.Payload((1, 2)))\n"
            "assert evolve(payload, validators=(3,))._validators == (3,)\n"
            "defect = sys.argv[2]\n"
            "if defect == 'field':\n"
            "    module.Payload.__attrs_attrs__ = "
            "(fields(module.Payload)[0].evolve(default=('foreign',)),)\n"
            "elif defect == 'layout':\n"
            "    module.Payload.__slots__ = ('foreign',)\n"
            "elif defect == 'options':\n"
            "    inspect(module.Payload).is_slotted = False\n"
            "elif defect == 'alias':\n"
            "    module.Payload.__attrs_attrs__ = "
            "(fields(module.Payload)[0].evolve(alias='foreign'),)\n"
            "elif defect == 'code':\n"
            "    supplier = module.Payload.__init__\n"
            "    supplier.__code__ = supplier.__code__.replace(co_name='foreign')\n"
            "elif defect == 'globals':\n"
            "    supplier = module.Payload.__init__\n"
            "    foreign_globals = dict(supplier.__globals__)\n"
            "    foreign_globals['__name__'] = 'foreign_supplier'\n"
            "    foreign = types.FunctionType(\n"
            "        supplier.__code__, foreign_globals,\n"
            "        supplier.__name__, supplier.__defaults__, supplier.__closure__)\n"
            "    foreign.__module__ = supplier.__module__\n"
            "    foreign.__qualname__ = supplier.__qualname__\n"
            "    foreign.__kwdefaults__ = supplier.__kwdefaults__\n"
            "    module.Payload.__init__ = foreign\n"
            "counter = attrib().counter\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "assert attrib().counter == counter + 1\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "    assert module.Payload((4,))._validators == (4,)\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "code", "globals"])
    def test_reexported_native_function_retains_physical_supplier(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Mutable library metadata cannot replace code and global supplier identity."""
        package = tmp_path / "reexport_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from attrs import evolve\n",
            ),
        )
        consumer = (
            "import importlib, sys, types\n"
            "from attrs import define\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('reexport_provider')\n"
            "@define\n"
            "class Consumer:\n"
            "    value: int\n"
            "before = Consumer(1)\n"
            "after = module.evolve(before, value=2)\n"
            "assert before.value == 1\n"
            "assert after.value == 2\n"
            "assert module.evolve.__module__ == Consumer.__module__\n"
            "defect = sys.argv[2]\n"
            "if defect == 'code':\n"
            "    module.evolve.__code__ = "
            "module.evolve.__code__.replace(co_name='foreign')\n"
            "elif defect == 'globals':\n"
            "    supplier = module.evolve\n"
            "    foreign = types.FunctionType(\n"
            "        supplier.__code__, dict(supplier.__globals__),\n"
            "        supplier.__name__, supplier.__defaults__, supplier.__closure__)\n"
            "    foreign.__module__ = supplier.__module__\n"
            "    foreign.__qualname__ = supplier.__qualname__\n"
            "    module.evolve = foreign\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "    assert module.evolve(before, value=3).value == 3\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("slots", [False, True])
    def test_frozen_dataclass_primitive_defaults_remain_native(
        tmp_path: Path,
        *,
        slots: bool,
    ) -> None:
        """Native scalar defaults support construction and compiler-generated methods."""
        package = tmp_path / "default_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                f"@dataclass(frozen=True, slots={slots!r})\n"
                "class Payload:\n"
                "    count: int = 3\n"
                "    text: str = 'literal'\n"
                "    absent: str | None = None\n",
            ),
        )
        consumer = (
            "import dataclasses, importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('default_provider')\n"
            "payload = module.Payload()\n"
            "assert dataclasses.astuple(payload) == (3, 'literal', None)\n"
            "assert repr(payload) == "
            "\"Payload(count=3, text='literal', absent=None)\"\n"
            "assert payload == module.Payload(3, 'literal', None)\n"
            "assert payload != module.Payload(4, 'literal', None)\n"
            "assert hash(payload) == hash(module.Payload())\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("location", ["workspace", "site-packages"])
    @pytest.mark.parametrize("defect", ["none", "descriptor", "code"])
    def test_class_method_alias_uses_its_physical_class_namespace(
        tmp_path: Path,
        location: str,
        defect: str,
    ) -> None:
        """A module shadow cannot replace an authored class-local method supplier."""
        source_root = tmp_path / location
        package = source_root / "alias_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "clone = 'module-shadow'\n"
                "def foreign(self):\n"
                "    return 'foreign'\n"
                "class Provider:\n"
                "    def clone(self):\n"
                "        return 'physical-class'\n"
                "    alias = clone\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('alias_provider')\n"
            "assert module.clone == 'module-shadow'\n"
            "assert module.Provider().alias() == 'physical-class'\n"
            "defect = sys.argv[2]\n"
            "if defect == 'descriptor':\n"
            "    module.Provider.alias = module.foreign\n"
            "elif defect == 'code':\n"
            "    module.Provider.clone.__code__ = "
            "module.Provider.clone.__code__.replace(co_name='foreign')\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "    assert module.Provider().alias() == 'physical-class'\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(source_root), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("location", ["workspace", "site-packages"])
    @pytest.mark.parametrize("ordering", ["before", "after"])
    @pytest.mark.parametrize("defect", ["none", "binding", "code"])
    def test_class_method_alias_preserves_lexical_binding_order(
        tmp_path: Path,
        location: str,
        ordering: str,
        defect: str,
    ) -> None:
        """A later class declaration cannot retroactively supply an earlier alias."""
        source_root = tmp_path / location
        package = source_root / "ordered_provider"
        tm.ok(u.Cli.ensure_dir(package))
        method = "    def clone(self):\n        return 'physical-class'\n"
        alias = "    alias = clone\n"
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "def clone(self):\n"
                "    return 'physical-module'\n"
                "class Provider:\n"
                + (alias + method if ordering == "before" else method + alias),
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('ordered_provider')\n"
            "ordering, defect = sys.argv[2:]\n"
            "expected = 'physical-module' if ordering == 'before' "
            "else 'physical-class'\n"
            "assert module.Provider().alias() == expected\n"
            "assert module.Provider().clone() == 'physical-class'\n"
            "if defect == 'binding':\n"
            "    module.Provider.alias = (module.Provider.clone "
            "if ordering == 'before' else module.clone)\n"
            "elif defect == 'code':\n"
            "    supplier = module.Provider.alias\n"
            "    supplier.__code__ = supplier.__code__.replace(co_name='foreign')\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "    assert module.Provider().alias() == expected\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [
                    executable,
                    "-c",
                    consumer,
                    str(source_root),
                    ordering,
                    defect,
                ],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("fields", [1, 3])
    @pytest.mark.parametrize("defect", ["none", "code", "filename", "closure"])
    def test_frozen_methods_authenticate_across_native_batch_positions(
        tmp_path: Path,
        fields: int,
        defect: str,
    ) -> None:
        """Native method offsets vary; executable code and bindings remain exact."""
        package = tmp_path / "frozen_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "@dataclass(frozen=True, repr=False, eq=False)\n"
                "class Payload:\n"
                + "".join(f"    value_{index}: int\n" for index in range(fields)),
            )
        )
        consumer = (
            "import dataclasses, importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('frozen_provider')\n"
            "values = tuple(range(int(sys.argv[2])))\n"
            "payload = module.Payload(*values)\n"
            "assert dataclasses.astuple(payload) == values\n"
            "try:\n"
            "    del payload.value_0\n"
            "except dataclasses.FrozenInstanceError:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('Frozen consumer allowed field deletion')\n"
            "descriptor = module.Payload.__delattr__\n"
            "defect = sys.argv[3]\n"
            "if defect == 'code':\n"
            "    descriptor.__code__ = descriptor.__code__.replace(co_name='foreign')\n"
            "elif defect == 'filename':\n"
            "    descriptor.__code__ = "
            "descriptor.__code__.replace(co_filename='foreign')\n"
            "elif defect == 'closure':\n"
            "    cells = dict(zip("
            "descriptor.__code__.co_freevars, descriptor.__closure__))\n"
            "    cells['__class__'].cell_contents = str\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), str(fields), defect],
                cwd=tmp_path,
            )
        )

    @staticmethod
    @pytest.mark.parametrize("hook", ["hash", "equality", "getattribute"])
    def test_annotation_operand_is_rejected_before_callbacks_repeat(
        tmp_path: Path,
        hook: str,
    ) -> None:
        """An authenticated stdlib compiler cannot admit authored operand hooks."""
        package = tmp_path / "operand_provider"
        tm.ok(u.Cli.ensure_dir(package))
        operation = {
            "hash": (
                "    def __hash__(cls):\n"
                "        record('hash')\n"
                "        return type.__hash__(cls)\n"
            ),
            "equality": (
                "    def __hash__(cls):\n"
                "        return type.__hash__(int)\n"
                "    def __eq__(cls, other):\n"
                "        record('equality')\n"
                "        return type.__eq__(cls, other)\n"
            ),
            "getattribute": (
                "    def __getattribute__(cls, name):\n"
                "        record('getattribute')\n"
                "        return type.__getattribute__(cls, name)\n"
            ),
        }[hook]
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "from pathlib import Path\n"
                "from typing import Union\n"
                "effects = []\n"
                "marker = Path(__file__).with_suffix('.effects')\n"
                "marker.write_text('', encoding='utf-8')\n"
                "def record(effect):\n"
                "    effects.append(effect)\n"
                "    with marker.open('a', encoding='utf-8') as stream:\n"
                "        stream.write(effect + '\\n')\n"
                "class Meta(type):\n" + operation + "class Operand(metaclass=Meta):\n"
                "    pass\n"
                "@dataclass\n"
                "class Payload:\n"
                "    value: Union[Operand, int]\n",
            )
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('operand_provider')\n"
            "value = module.Operand()\n"
            "assert module.Payload(value).value is value\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            )
        )

    @staticmethod
    @pytest.mark.parametrize("supplier", ["Field", "_FuncBuilder"])
    def test_foreign_native_constructor_is_rejected_before_invocation(
        tmp_path: Path,
        supplier: str,
    ) -> None:
        """A native function cannot authorize a replaced compiler class binding."""
        package = tmp_path / "constructor_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "from pathlib import Path\n"
                "effects = []\n"
                "marker = Path(__file__).with_suffix('.effects')\n"
                "marker.write_text('', encoding='utf-8')\n"
                "def record(effect):\n"
                "    effects.append(effect)\n"
                "    with marker.open('a', encoding='utf-8') as stream:\n"
                "        stream.write(effect + '\\n')\n"
                "class Foreign:\n"
                "    def __new__(cls, *args, **kwargs):\n"
                "        record('new')\n"
                "        return object.__new__(cls)\n"
                "    def __init__(self, *args, **kwargs):\n"
                "        record('init')\n"
                "@dataclass\n"
                "class Payload:\n"
                "    value: int = 1\n",
            )
        )
        consumer = (
            "import dataclasses, importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('constructor_provider')\n"
            "assert module.Payload(2).value == 2\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "setattr(dataclasses, sys.argv[2], module.Foreign)\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), supplier],
                cwd=tmp_path,
            )
        )
