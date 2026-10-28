"""Public evidence for passive capture and authenticated native imports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import p, tm, u


class TestsNativeCompilerAdmission:
    """Separate passive native observations from isolated import effects."""

    @staticmethod
    @pytest.mark.parametrize("defect", ["absent", "missing-spec", "broken-origin"])
    def test_imported_class_preserves_its_supplier_failure(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A failed supplier never becomes a successful third-party alias string."""
        package = tmp_path / "supplier_contract_provider"
        u.Tests.write_package_init(
            package,
            "from .supplier import Payload\n",
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "supplier.py",
                "class Payload:\n    def operation(self):\n        return 'native'\n",
            ),
        )
        consumer = (
            "from flext_infra.workspace import "
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
            "original = native.capture((m.Infra.SourceClassReference(target=name),))\n"
            "assert original.failure\n"
            "observed = "
            "native.capture((m.Infra.SourceClassReference(target=module.__name__),))\n"
            "assert observed.failure, observed\n"
            "assert observed.error == original.error, (observed, original)\n"
            "assert observed.error_code == original.error_code\n"
            "assert observed.exception is original.exception\n"
        )
        native_consumer(consumer, str(tmp_path), defect)
