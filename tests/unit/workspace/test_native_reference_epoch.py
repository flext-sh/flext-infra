"""Real nested operand observations retain every elected source identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import t, u


class TestsNativeReferenceEpoch:
    """Native container traversal preserves source and declaration change guards."""

    @staticmethod
    def test_nested_native_operands_retain_distinct_source_owners(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Slices and aliases retain both classes across independent captures."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "from types import GenericAlias\n"
            "class First:\n"
            "    value = 'first'\n"
            "class Second:\n"
            "    value = 'second'\n"
            "retained = tuple(\n"
            "    (slice(None, owner), GenericAlias(tuple, (owner,)))\n"
            "    for owner in (First, Second)\n"
            ")\n"
            "def execute(inputs=retained):\n"
            "    return inputs\n",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_tests import tm
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(target=module.__name__, attributes=('execute',)),
)
before = tm.ok(native.capture(selection))
tm.that(tm.ok(native.compare(before, tm.ok(native.capture(selection)))), eq=True)
elected = {source[0] for source in before.sources}
tm.that('test_pkg::First' in elected, eq=True)
tm.that('test_pkg::Second' in elected, eq=True)
module.Second.value = 'changed'
tm.fail(native.compare(before, tm.ok(native.capture(selection))))
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
