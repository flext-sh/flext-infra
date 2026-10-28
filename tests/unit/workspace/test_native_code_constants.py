"""Native code observations retain the types of executable constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import t, u


class TestsNativeCodeConstants:
    """Changes visible to the executing function cannot disappear in transport."""

    @staticmethod
    @pytest.mark.parametrize(
        ("initial", "replacement"),
        [
            ("True", "1"),
            ("1", "True"),
            ("0.0", "-0.0"),
            ("-0.0", "0.0"),
            ("0j", "-0j"),
            ("(True, (0.0, 0j))", "(1, (-0.0, -0j))"),
            ("b'native'", "bytearray(b'native')"),
            ("b'native'", "memoryview(b'native')"),
        ],
    )
    def test_changed_constant_retains_its_native_execution_contract(
        real_python_package: t.DirectoryPath,
        initial: t.StrictStr,
        replacement: t.StrictStr,
    ) -> None:
        """Different native code and return objects require different evidence."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            f"def operation():\n    return {initial}\n"
            f"def replacement():\n    return {replacement}\n",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_tests import tm
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('operation',)
    ),
)
original = module.operation()
original_code = module.operation.__code__
before = native.capture(selection).unwrap()
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
replacement = module.replacement()
module.operation.__code__ = original_code.replace(co_consts=tuple(
    replacement if value is original else value for value in original_code.co_consts))
assert module.operation() is replacement
assert original_code != module.operation.__code__
assert native.compare(before, native.capture(selection).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
