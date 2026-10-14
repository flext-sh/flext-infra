"""Public native observations preserve nested values with linear encoding size.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import t, u


class TestsNativeObservationScaling:
    """Nested declaration inputs remain complete without repeated JSON escaping."""

    @staticmethod
    def test_optional_attribute_presence_remains_observable(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Conditional native lookups retain absence and detect later injection."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "import sys\n"
            "module = sys.modules[__name__]\n"
            "def execute():\n"
            "    return module.optional if hasattr(module, 'optional') else None\n",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
selection = (m.Infra.SourceClassReference(target=module.__name__, attributes=('execute',)),)
assert module.execute() is None
before = native.capture(selection).unwrap()
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
module.optional = 'available'
assert module.execute() == 'available'
assert native.compare(before, native.capture(selection).unwrap()).failure
del module.optional
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    def test_nested_values_scale_linearly_and_detect_leaf_changes(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Doubling nesting keeps transport bounded and retains tamper detection."""
        depth = 8
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "__all__ = ['Small', 'Large']\n"
            + "".join(
                f"class {name}:\n    value = {'(' * size}'original'{',)' * size}\n"
                for name, size in (("Small", depth), ("Large", depth * 2))
            ),
        )
        u.Tests.run_lazy_init_probe(
            f"""from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
small, large = (
    (m.Infra.SourceClassReference(target=module.__name__, attributes=(name,)),)
    for name in ('Small', 'Large')
)
shallow, deep = (native.capture(selection).unwrap() for selection in (small, large))
assert len(deep.model_dump_json()) < 2 * len(shallow.model_dump_json())
assert native.compare(deep, native.capture(large).unwrap()).unwrap() is True
changed = 'modified'
for _ in range({depth * 2}): changed = (changed,)
module.Large.value = changed
assert native.compare(deep, native.capture(large).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    def test_nested_code_locations_preserve_native_filename_checks(
        real_python_package: t.DirectoryPath,
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
        root = real_python_package / "src"
        u.Tests.write_package_init(root / "test_pkg", "\n".join(lines) + "\n")
        u.Tests.run_lazy_init_probe(
            """from types import CodeType
from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
selection = (m.Infra.SourceClassReference(target=module.__name__, attributes=('factory',)),)
before = native.capture(selection).unwrap()
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
chain = [module.factory.__code__]
while children := [item for item in chain[-1].co_consts if type(item) is CodeType]:
    chain.append(children[0])
changed = chain[-1].replace(co_filename=chain[-1].co_filename + '.changed')
assert changed == chain[-1]
for parent, child in reversed(tuple(zip(chain[:-1], chain[1:], strict=True))):
    changed = parent.replace(co_consts=tuple(
        changed if item is child else item for item in parent.co_consts))
module.factory.__code__ = changed
assert native.compare(before, native.capture(selection).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
