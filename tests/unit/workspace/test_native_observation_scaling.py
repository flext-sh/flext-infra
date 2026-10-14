"""Public native observations preserve nested values with linear encoding size.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from sys import executable

from tests import tm, u


class TestsNativeObservationScaling:
    """Nested declaration inputs remain complete without repeated JSON escaping."""

    @staticmethod
    def test_nested_values_scale_linearly_and_detect_leaf_changes(
        tmp_path: Path,
    ) -> None:
        """Doubling nesting keeps transport bounded and retains tamper detection."""
        depth = 8
        shallow = "'original'"
        for _ in range(depth):
            shallow = f"({shallow},)"
        deep = shallow
        for _ in range(depth):
            deep = f"({deep},)"
        module_name = "native_nested_values"
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / f"{module_name}.py",
                "__all__ = ['Small', 'Large']\n"
                f"class Small:\n    value = {shallow}\n"
                f"class Large:\n    value = {deep}\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra import m\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "small = (m.Infra.SourceClassReference("
            "target=module.__name__, attributes=('Small',)),)\n"
            "large = (m.Infra.SourceClassReference("
            "target=module.__name__, attributes=('Large',)),)\n"
            "shallow = native.capture(small).unwrap()\n"
            "deep = native.capture(large).unwrap()\n"
            "assert len(deep.model_dump_json()) < 2 * len(shallow.model_dump_json())\n"
            "assert native.compare(deep, native.capture(large).unwrap()).unwrap() is True\n"
            "changed = 'modified'\n"
            "for _ in range(int(sys.argv[3])): changed = (changed,)\n"
            "module.Large.value = changed\n"
            "assert native.compare(deep, native.capture(large).unwrap()).failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [
                    executable,
                    "-c",
                    consumer,
                    str(tmp_path),
                    module_name,
                    str(depth * 2),
                ],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_nested_code_locations_preserve_native_filename_checks(
        tmp_path: Path,
    ) -> None:
        """Nested compiler metadata remains checked without recursive JSON strings."""
        depth = 16
        lines = ["__all__ = ['factory']", "def factory():"]
        lines.extend(
            "    " * level + f"def nested_{level}():" for level in range(1, depth)
        )
        lines.append("    " * depth + "return 'value'")
        lines.extend(
            "    " * level + f"return nested_{level}"
            for level in range(depth - 1, 0, -1)
        )
        module_name = "native_nested_code"
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / f"{module_name}.py",
                "\n".join(lines) + "\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from types import CodeType\n"
            "from flext_infra import m\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "selection = (m.Infra.SourceClassReference("
            "target=module.__name__, attributes=('factory',)),)\n"
            "before = native.capture(selection).unwrap()\n"
            "assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True\n"
            "chain = [module.factory.__code__]\n"
            "while children := [item for item in chain[-1].co_consts if type(item) is CodeType]:\n"
            "    chain.append(children[0])\n"
            "changed = chain[-1].replace(co_filename=chain[-1].co_filename + '.changed')\n"
            "assert changed == chain[-1]\n"
            "for parent, child in reversed(tuple(zip(chain[:-1], chain[1:], strict=True))):\n"
            "    changed = parent.replace(co_consts=tuple("
            "changed if item is child else item for item in parent.co_consts))\n"
            "module.factory.__code__ = changed\n"
            "assert native.compare(before, native.capture(selection).unwrap()).failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), module_name],
                cwd=tmp_path,
            ),
        )
