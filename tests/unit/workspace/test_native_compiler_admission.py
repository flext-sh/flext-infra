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
