"""Public native capture retains callable state without invoking accessors.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import t, u


class TestsNativeCallableAdmission:
    """Inherited dict and slots callables preserve behavior and binding evidence."""

    @staticmethod
    def test_git_resolution_preserves_native_producer_identity(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """A real repository lookup retains the configured Git producer identity."""
        root = u.Tests.git_repository(real_python_package)
        u.Tests.run_lazy_init_probe(
            """from pathlib import Path
from git import Git
from flext_infra import m, u
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
selection = (m.Infra.SourceClassReference(target="git.cmd", attributes=("Git",)),)
before = native.capture(selection).unwrap()
root = Path.cwd()
resolved = u.Infra.git_repository_root(m.Infra.GitRepoRequest(repo_root=root)).unwrap()
assert resolved.repository_root == root
after = native.capture(selection).unwrap()
compared = native.compare(before, after)
assert compared.success, compared.error
""",
            python_paths=(),
            cwd=root,
        )

    @staticmethod
    def test_metadata_read_preserves_native_producer_identity(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Reading a real manifest retains its metadata ingress model identity."""
        u.Tests.run_lazy_init_probe(
            """from pathlib import Path
from flext_infra import m, u
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
selection = (m.Infra.SourceClassReference(
    target="flext_infra._models.deps",
    attributes=("FlextInfraModelsDeps", "ProjectMetadataState"),
),)
before = native.capture(selection).unwrap()
root = Path.cwd()
metadata = u.Infra.read_project_metadata_result(root).unwrap()
assert metadata.root == root
after = native.capture(selection).unwrap()
compared = native.compare(before, after)
assert compared.success, compared.error
""",
            python_paths=(),
            cwd=real_python_package,
        )

    @staticmethod
    def test_model_use_preserves_native_producer_identity(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Using a real model must retain its declared producer identity."""
        u.Tests.run_lazy_init_probe(
            """from pathlib import Path
from flext_infra import m, u
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
selection = (m.Infra.SourceClassReference(
    target="flext_infra._models.codegen_toolchain",
    attributes=("FlextInfraModelsCodegenToolchain", "CodegenParticipantPolicy"),
),)
before = native.capture(selection).unwrap()
root = Path.cwd()
policy = m.Infra.CodegenParticipantPolicy(
    scope_root=root,
    roots=(u.Cli.atomic_plan_directory_chain(root).unwrap(),),
)
assert policy.scope_root == root and policy.roots[0].target == root
after = native.capture(selection).unwrap()
compared = native.compare(before, after)
assert compared.success, compared.error
""",
            python_paths=(),
            cwd=real_python_package,
        )

    @staticmethod
    @pytest.mark.parametrize("storage", ["dict", "slots"])
    @pytest.mark.parametrize(
        ("defect", "expected"),
        [("none", 7), ("state", 15), ("implementation", -1), ("replacement", 15)],
    )
    def test_inherited_callable_observation_avoids_authored_accessors(
        real_python_package: t.DirectoryPath,
        storage: t.StrictStr,
        defect: t.StrictStr,
        expected: t.StrictInt,
    ) -> None:
        """Real calls work; passive observations reject changed state or methods."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            f"""from flext_infra import p, t
from typing import Unpack
call_count = 0
accessor_calls = 0
class CallableBase:
    __slots__ = ()
    def __call__(self, value: t.StrictInt) -> t.StrictInt:
        global call_count
        call_count += 1
        return self.offset + value
    def alternate(self, value: t.StrictInt) -> t.StrictInt:
        global call_count
        call_count += 1
        return self.offset - value
class Receiver(CallableBase):
    {"__slots__ = ('offset',)" if storage == "slots" else ""}
    def __init__(self, offset: t.StrictInt) -> None:
        self.offset = offset
    def __getattribute__(self, name: t.StrictStr) -> p.AttributeProbe:
        global accessor_calls
        accessor_calls += 1
        return object.__getattribute__(self, name)
    @property
    def metadata(self) -> t.StrictStr:
        raise AssertionError('authored metadata accessor invoked')
class Consumer:
    callback = Receiver(3)
    @staticmethod
    def execute(value: t.StrictInt) -> t.StrictInt:
        return Consumer.callback(value)
""",
        )
        u.Tests.run_lazy_init_probe(
            f"""from typing import get_args, get_origin
from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
assert module.Consumer.execute(4) == 7
assert hasattr(module.Consumer.callback, '__dict__') is ({storage!r} == 'dict')
assert module.accessor_calls > 0
module.accessor_calls = 0
before = module.call_count
annotation = module.Unpack[tuple[int, str]]
assert get_origin(annotation) is module.Unpack
assert get_args(annotation) == (tuple[int, str],)
selection = (
    m.Infra.SourceClassReference(target=module.__name__, attributes=('Consumer', 'execute')),
    m.Infra.SourceClassReference(target=module.__name__, attributes=('Unpack',)),
)
original = native.capture(selection).unwrap()
assert module.call_count == before and module.accessor_calls == 0
repeated = native.capture(selection).unwrap()
assert native.compare(original, repeated).unwrap() is True
assert module.call_count == before and module.accessor_calls == 0
defect = {defect!r}
if defect == 'state':
    module.Consumer.callback.offset = 11
elif defect == 'implementation':
    module.CallableBase.__call__ = module.CallableBase.alternate
elif defect == 'replacement':
    module.Consumer.callback = module.Receiver(11)
observed = native.capture(selection).unwrap()
compared = native.compare(original, observed)
assert compared.success == (defect == 'none'), compared.error
assert module.call_count == before and module.accessor_calls == 0
assert module.Unpack[tuple[int, str]] == annotation
assert module.Consumer.execute(4) == {expected}
assert module.call_count == before + 1 and module.accessor_calls > 0
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("factory", "replacement", "expression", "expected", "changed"),
        [
            (
                "itemgetter(slice(2, None))",
                "itemgetter(slice(3, None))",
                "module.operation('abcdef')",
                "'cdef'",
                "'def'",
            ),
            (
                "attrgetter('real')",
                "attrgetter('imag')",
                "module.operation(3 + 4j)",
                "3.0",
                "4.0",
            ),
            (
                "methodcaller('lower')",
                "methodcaller('upper')",
                "module.operation('NaTiVe')",
                "'native'",
                "'NATIVE'",
            ),
            (
                "partial(bytes.maketrans, b'a', b'b')",
                "partial(bytes.maketrans, b'a', b'c')",
                "b'a'.translate(module.operation())",
                "b'b'",
                "b'c'",
            ),
        ],
    )
    def test_native_callable_state_retains_real_behavior(
        real_python_package: t.DirectoryPath,
        factory: t.StrictStr,
        replacement: t.StrictStr,
        expression: t.StrictStr,
        expected: t.StrictStr,
        changed: t.StrictStr,
    ) -> None:
        """Observe native callable arguments without invoking their operations."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "from functools import partial\n"
            "from operator import attrgetter, itemgetter, methodcaller\n"
            f"operation = {factory}\n",
        )
        u.Tests.run_lazy_init_probe(
            f"""from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
assert {expression} == {expected}
selection = (m.Infra.SourceClassReference(target=module.__name__, attributes=('operation',)),)
original = native.capture(selection).unwrap()
repeated = native.capture(selection).unwrap()
assert native.compare(original, repeated).unwrap() is True
module.operation = module.{replacement}
observed = native.capture(selection).unwrap()
assert native.compare(original, observed).failure
assert {expression} == {changed}
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
