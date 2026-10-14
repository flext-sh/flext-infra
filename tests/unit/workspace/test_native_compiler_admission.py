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
        method = (
            "    def clone(self):\n"
            "        return 'physical-class'\n"
        )
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
