"""Public native observations preserve nested values with linear encoding size.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import t, u


class TestsNativeObservationScaling:
    """Nested declaration inputs remain complete without repeated JSON escaping."""

    @staticmethod
    @pytest.mark.parametrize("decorator", ["classmethod", "staticmethod"])
    def test_declared_writer_state_preserves_constant_and_code_checks(
        real_python_package: t.DirectoryPath,
        decorator: t.StrictStr,
    ) -> None:
        """Actual cache writes preserve identity; constant and callback edits fail."""
        root = real_python_package / "src"
        receiver = "cls" if decorator == "classmethod" else "Consumer"
        parameters = "cls" if decorator == "classmethod" else ""
        u.Tests.write_package_init(
            root / "test_pkg",
            "class Consumer:\n"
            "    cache = None\n"
            "    mode = 'original'\n"
            f"    @{decorator}\n"
            f"    def prime({parameters}):\n"
            f"        {receiver}.cache = ('populated',)\n"
            "    @staticmethod\n"
            "    def execute():\n"
            "        Consumer.prime()\n"
            "        return Consumer.mode\n"
            f"def replacement({parameters}):\n"
            f"    {receiver}.cache = ('different',)\n",
        )
        u.Tests.run_lazy_init_probe(
            f"""from flext_infra import m
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('Consumer', 'execute')
    ),
)
before = native.capture(selection).unwrap()
assert module.Consumer.execute() == 'original'
assert module.Consumer.cache == ('populated',)
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
module.Consumer.mode = 'changed'
assert module.Consumer.execute() == 'changed'
assert native.compare(before, native.capture(selection).unwrap()).failure
module.Consumer.mode = 'original'
module.Consumer.prime = {decorator}(module.replacement)
assert native.compare(before, native.capture(selection).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    def test_repeated_lexical_edges_preserve_classes_and_distinct_aliases(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Repeated loads of one binding do not turn its declaration into an alias."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "class Payload:\n"
            "    value = 'original'\n"
            "Alias = Payload\n"
            "def execute():\n"
            "    return Payload.value, Payload.value, Alias.value\n",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('execute',)
    ),
)
assert module.execute() == ('original', 'original', 'original')
before = native.capture(selection).unwrap()
assert len({item.binding for item in before.bindings}) == len(before.bindings)
assert any(item.kind == 'alias' for item in before.bindings)
assert native.compare(before, native.capture(selection).unwrap()).unwrap() is True
module.Payload.value = 'modified'
assert module.execute() == ('modified', 'modified', 'modified')
assert native.compare(before, native.capture(selection).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    def test_wrapper_code_uses_declared_staging_paths_and_detects_mutation(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Wrapper storage and direct code evidence share the same physical mapping."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "from functools import lru_cache, partial\n"
            "@lru_cache()\n"
            "def execute():\n"
            "    return 'original'\n"
            "bound = partial(execute)\n",
        )
        u.Tests.run_lazy_init_probe(
            """from pathlib import Path
from flext_infra import m
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('bound',)
    ),
)
assert module.bound() == 'original'
before = native.capture(selection).unwrap()
original_root = Path(module.__file__).parent.parent
staged_root = original_root.parent / 'staged'
function = module.execute.__wrapped__
code = function.__code__
function.__code__ = code.replace(
    co_filename=str(staged_root / Path(code.co_filename).relative_to(original_root)))
assert native.compare(before, native.capture(selection).unwrap()).failure
mapping = ((staged_root, original_root),)
assert native.compare(
    before, native.capture(selection, paths=mapping).unwrap()
).unwrap() is True
function.__code__ = function.__code__.replace(co_consts=tuple(
    'modified' if value == 'original' else value for value in code.co_consts))
module.execute.cache_clear()
assert module.bound() == 'modified'
assert native.compare(before, native.capture(selection, paths=mapping).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

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
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('execute',)
    ),
)
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
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
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
from flext_infra.workspace import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('factory',)
    ),
)
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
