"""Public native capture observes callable receivers without authored accessors.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from sys import executable

from tests import tm, u


class TestsNativeCallableAdmission:
    """Inherited Python callables retain behavior and receiver tamper detection."""

    @staticmethod
    def test_inherited_callable_observation_avoids_authored_accessors(
        tmp_path: Path,
    ) -> None:
        """Capture stays passive while a changed callable slot changes execution."""
        module_name = "native_callable_provider"
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / f"{module_name}.py",
                "__all__ = ['Consumer']\n"
                "accessor_calls = 0\n"
                "class CallableBase:\n"
                "    def __call__(self, value):\n"
                "        return self.offset + value\n"
                "class Receiver(CallableBase):\n"
                "    def __init__(self, offset):\n"
                "        self.offset = offset\n"
                "    def __getattribute__(self, name):\n"
                "        global accessor_calls\n"
                "        accessor_calls += 1\n"
                "        return object.__getattribute__(self, name)\n"
                "    @property\n"
                "    def metadata(self):\n"
                "        raise AssertionError('authored metadata accessor invoked')\n"
                "class Consumer:\n"
                "    callback = Receiver(3)\n"
                "    @staticmethod\n"
                "    def execute(value):\n"
                "        return Consumer.callback(value)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra import m\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "assert module.Consumer.execute(4) == 7\n"
            "assert module.accessor_calls > 0\n"
            "module.accessor_calls = 0\n"
            "selection = (m.Infra.SourceClassReference("
            "target=module.__name__, attributes=('Consumer', 'execute')),)\n"
            "original = native.capture(selection).unwrap()\n"
            "assert module.accessor_calls == 0\n"
            "repeated = native.capture(selection).unwrap()\n"
            "assert module.accessor_calls == 0\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "module.Consumer.callback = module.Receiver(11)\n"
            "changed = native.capture(selection).unwrap()\n"
            "assert module.accessor_calls == 0\n"
            "assert native.compare(original, changed).failure\n"
            "assert module.Consumer.execute(4) == 15\n"
            "assert module.accessor_calls > 0\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), module_name],
                cwd=tmp_path,
            ),
        )
