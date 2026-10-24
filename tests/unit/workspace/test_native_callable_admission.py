"""Public native capture retains callable state without invoking accessors.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference
from tests import m, t, tm, u

_MAX_SUPPLIER_EDGES = 16
_MAX_SUPPLIER_PATH = 64


class TestsFlextInfraNativeCallableAdmission:
    """Inherited dict and slots callables preserve behavior and binding evidence."""

    _THREAD_HOOK_PROBE = """\
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
selection = native.producer_selections(
    FlextInfraSemanticPublication.publish_source_candidate, (),
).unwrap()
print(native.capture(selection).unwrap().model_dump_json())
"""

    _GATE_BASE_PROBE = """\
from pathlib import Path
from flext_infra import check
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
selection = native.producer_selections(
    FlextInfraSemanticPublication.publish_source_candidate, (),
).unwrap()
before = native.capture(selection).unwrap()
checker = check.FlextInfraWorkspaceChecker(repository_root=Path.cwd())
after = native.capture(selection).unwrap()
print(before.model_dump_json())
print(after.model_dump_json())
"""

    @staticmethod
    @pytest.mark.parametrize("subject", ["thread-hook", "gate-base"])
    def test_publication_producer_retains_reached_thread_hook(
        real_python_package: t.DirectoryPath,
        subject: t.StrictStr,
    ) -> None:
        """Report real publication aliases before any publication guard executes."""
        selections = tm.ok(
            FlextInfraWorkspaceNativeReference.producer_selections(
                FlextInfraSemanticPublication.publish_source_candidate,
                (),
            )
        )
        if subject == "thread-hook":
            live = tm.ok(FlextInfraWorkspaceNativeReference.capture(selections))
            output = u.Tests.run_lazy_init_probe(
                TestsFlextInfraNativeCallableAdmission._THREAD_HOOK_PROBE,
                python_paths=(),
                cwd=real_python_package,
            )
        else:
            output = u.Tests.run_lazy_init_probe(
                TestsFlextInfraNativeCallableAdmission._GATE_BASE_PROBE,
                python_paths=(),
                cwd=real_python_package,
            )
            live = m.Infra.NativeImportObservation.model_validate_json(output[-2])
        cold = m.Infra.NativeImportObservation.model_validate_json(output[-1])
        tm.that(cold.modules, eq=selections)
        for phase, observation in (
            (f"{subject}-before", live),
            (f"{subject}-after", cold),
        ):
            TestsFlextInfraNativeCallableAdmission._assert_reached_edges(
                phase, observation, selections, thread_hook=subject == "thread-hook"
            )
        compared = FlextInfraWorkspaceNativeReference.compare(live, cold)
        if subject == "gate-base":
            tm.ok(compared)
        else:
            tm.fail(compared)

    @staticmethod
    def _alias_paths(
        aliases: t.SequenceOf[m.Infra.NativeBindingEvidence],
        roots: t.StrSequence,
    ) -> t.Pair[
        t.MappingKV[str, t.VariadicTuple[m.Infra.NativeBindingEvidence]],
        t.MappingKV[str, t.SequenceOf[m.Infra.NativeBindingEvidence]],
    ]:
        """Index the alias chain reaching each target from the selected roots.

        Returns:
            The alias path per target and the outgoing aliases per parent.

        """
        paths: t.DictKV[str, t.VariadicTuple[m.Infra.NativeBindingEvidence]] = {}
        pending = [item for item in aliases if item.binding in roots]
        outgoing: t.DictKV[str, list[m.Infra.NativeBindingEvidence]] = {}
        for edge in aliases:
            parent = edge.binding.partition(".")[0]
            outgoing.setdefault(parent, []).append(edge)
        while pending:
            edge = pending.pop()
            (target,) = (value for name, value in edge.operands if name == "target")
            if target in paths:
                continue
            parent = edge.binding.partition(".")[0]
            paths[target] = (*paths.get(parent, ()), edge)
            pending.extend(outgoing.get(target, ()))
        return paths, outgoing

    @staticmethod
    def _assert_reached_edges(
        phase: str,
        observation: m.Infra.NativeImportObservation,
        selections: t.SequenceOf[m.Infra.SourceClassReference],
        *,
        thread_hook: bool,
    ) -> None:
        """Bound the supplier edges and paths reached from the selected roots."""
        indexed = {item.binding: item for item in observation.bindings}
        aliases = tuple(item for item in observation.bindings if item.kind == "alias")
        roots = tuple(
            f"{item.target}::{'.'.join(item.attributes)}" for item in selections
        )
        paths, _ = TestsFlextInfraNativeCallableAdmission._alias_paths(aliases, roots)
        reached = tuple(
            edge
            for edge in aliases
            if (
                edge.binding.endswith((
                    ".global.excepthook",
                    ".global.threading.excepthook",
                ))
                if thread_hook
                else any(
                    indexed[value].supplier == "flext_infra.gates.base_gate"
                    and indexed[value].qualname == "FlextInfraGate"
                    for name, value in edge.operands
                    if name == "target"
                )
            )
            and edge.binding.partition(".")[0] in paths
        )
        if thread_hook:
            tm.that(reached, empty=False)
        tm.that(
            len(reached),
            lte=_MAX_SUPPLIER_EDGES,
            msg=f"{phase}: too many supplier edges: {len(reached)}",
        )
        for edge in reached:
            chain = (*paths[edge.binding.partition(".")[0]], edge)
            tm.that(
                len(chain),
                lte=_MAX_SUPPLIER_PATH,
                msg=f"{phase}: supplier path exceeds diagnostic bound",
            )

    @staticmethod
    def test_global_hook_alias_retains_actual_supplier_boundary(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Ambient imports preserve capture; a reached hook replacement does not."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            """import threading
def execute():
    return threading.excepthook
def replacement(args):
    return 'replacement hook'
""",
        )
        u.Tests.run_lazy_init_probe(
            """import importlib
import threading
from flext_infra import m
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (m.Infra.SourceClassReference(
    target=module.__name__, attributes=('execute',)
),)
original_hook = threading.excepthook
assert module.execute() is original_hook
before = native.capture(selection).unwrap()
importlib.import_module('fractions')
stable = native.capture(selection).unwrap()
compared = native.compare(before, stable)
assert compared.success, compared.error
try:
    threading.excepthook = module.replacement
    assert module.execute() is module.replacement
    assert module.execute()(None) == 'replacement hook'
    changed = native.capture(selection).unwrap()
    for observation, hook in (
        (before, original_hook), (stable, original_hook),
        (changed, module.replacement),
    ):
        producer, = (
            item for item in observation.bindings
            if item.kind != 'alias' and item.supplier == module.__name__
            and item.qualname == 'execute'
        )
        edge, = (
            item for item in observation.bindings
            if item.binding == producer.binding + '.global.threading.excepthook'
        )
        assert edge.kind == 'alias', edge.model_dump_json()
        target, = (value for name, value in edge.operands if name == 'target')
        body, = (item for item in observation.bindings if item.binding == target)
        assert body.supplier == hook.__module__, body.model_dump_json()
        assert body.qualname == hook.__qualname__, body.model_dump_json()
    compared = native.compare(before, changed)
    assert compared.failure, 'a reached replacement hook was admitted'
    assert compared.error, 'hook replacement refusal has no diagnostic'
finally:
    threading.excepthook = original_hook
assert module.execute() is original_hook
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    @pytest.mark.parametrize("expression", ["value", "Consumer.offset + value"])
    def test_unrelated_generated_function_is_not_a_class_state_writer(
        real_python_package: t.DirectoryPath,
        expression: t.StrictStr,
    ) -> None:
        """Inapplicable generated callables cannot block real writer observation."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            """from types import FunctionType
class Consumer:
    offset = 3
    mode = 'original'
    @staticmethod
    def execute(value: int) -> int:
        return Consumer.offset + value
def prototype(value: int) -> int:
"""
            f"    return {expression}\n"
            """generated = FunctionType(prototype.__code__, {'Consumer': Consumer})
def update_consumer(value: int) -> None:
    Consumer.offset = value
def replacement(value: int) -> None:
    Consumer.offset = value + 1
""",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
assert module.generated.__module__ is None
assert module.generated(4) == module.prototype(4)
assert module.Consumer.execute(4) == 7
selection = (m.Infra.SourceClassReference(
    target=module.__name__, attributes=('Consumer',)
),)
before = native.capture(selection).unwrap()
repeated = native.capture(selection).unwrap()
assert native.compare(before, repeated).unwrap() is True
module.update_consumer(11)
after = native.capture(selection).unwrap()
assert native.compare(before, after).unwrap() is True
assert module.Consumer.execute(4) == 15
module.Consumer.mode = 'changed'
assert native.compare(before, native.capture(selection).unwrap()).failure
module.Consumer.mode = 'original'
module.update_consumer.__code__ = module.replacement.__code__
assert native.compare(before, native.capture(selection).unwrap()).failure
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

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
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
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
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
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
metaclass_hash_calls = 0
class ReceiverMeta(type):
    def __hash__(cls) -> t.StrictInt:
        global metaclass_hash_calls
        metaclass_hash_calls += 1
        return type.__hash__(cls)
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
class Receiver(CallableBase, metaclass=ReceiverMeta):
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
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
assert module.Consumer.execute(4) == 7
assert hasattr(module.Consumer.callback, '__dict__') is ({storage!r} == 'dict')
assert module.accessor_calls > 0
module.accessor_calls = 0
module.metaclass_hash_calls = 0
before = module.call_count
annotation = module.Unpack[tuple[int, str]]
assert get_origin(annotation) is module.Unpack
assert get_args(annotation) == (tuple[int, str],)
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('Consumer', 'execute')
    ),
    m.Infra.SourceClassReference(target=module.__name__, attributes=('Unpack',)),
)
original = native.capture(selection).unwrap()
assert module.call_count == before and module.accessor_calls == 0
assert module.metaclass_hash_calls == 0
repeated = native.capture(selection).unwrap()
assert native.compare(original, repeated).unwrap() is True
assert module.call_count == before and module.accessor_calls == 0
assert module.metaclass_hash_calls == 0
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
assert module.metaclass_hash_calls == 0
assert module.Unpack[tuple[int, str]] == annotation
assert module.Consumer.execute(4) == {expected}
assert module.call_count == before + 1 and module.accessor_calls > 0
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "behavior",
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
        behavior: t.StrSequence,
    ) -> None:
        """Observe native callable arguments without invoking their operations."""
        factory, replacement, expression, expected, changed = behavior
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "from functools import partial\n"
            "from operator import attrgetter, itemgetter, methodcaller\n"
            f"operation = {factory}\n",
        )
        u.Tests.run_lazy_init_probe(
            f"""from flext_infra import m
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
assert {expression} == {expected}
selection = (
    m.Infra.SourceClassReference(
        target=module.__name__, attributes=('operation',)
    ),
)
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
