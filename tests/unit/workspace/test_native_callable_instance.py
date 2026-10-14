"""Public callable observations retain receiver state without invoking it.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import t, u


class TestsNativeCallableInstance:
    """Exercise callable behavior and passive binding observations."""

    @staticmethod
    @pytest.mark.parametrize("storage", ["dict", "slots"])
    @pytest.mark.parametrize(
        ("defect", "expected"), [("none", 7), ("receiver", 15), ("implementation", -1)]
    )
    def test_callable_receiver_and_implementation_retain_their_native_state(
        real_python_package: t.DirectoryPath,
        storage: t.StrictStr,
        defect: t.StrictStr,
        expected: t.StrictInt,
    ) -> None:
        """Both storage forms expose tampering without capture invoking callbacks."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            f"""from flext_infra import t
call_count = 0
class Receiver:
    {"__slots__ = ('offset',)" if storage == "slots" else ""}
    def __call__(self, value: t.StrictInt) -> t.StrictInt:
        global call_count
        call_count += 1
        return self.offset + value
    def alternate(self, value: t.StrictInt) -> t.StrictInt:
        global call_count
        call_count += 1
        return self.offset - value
callback = Receiver()
callback.offset = 3
""",
        )
        u.Tests.run_lazy_init_probe(
            f"""from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
assert module.callback(4) == 7
before = module.call_count
selection = (m.Infra.SourceClassReference(target=module.__name__, attributes=('callback',)),)
original = native.capture(selection).unwrap()
assert module.call_count == before
repeated = native.capture(selection).unwrap()
assert native.compare(original, repeated).unwrap() is True
assert module.call_count == before
defect = {defect!r}
if defect == 'receiver':
    module.callback.offset = 11
elif defect == 'implementation':
    module.Receiver.__call__ = module.Receiver.alternate
observed = native.capture(selection).unwrap()
compared = native.compare(original, observed)
assert compared.success == (defect == 'none'), compared.error
assert module.call_count == before
assert module.callback(4) == {expected}
assert module.call_count == before + 1
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )

    @staticmethod
    def test_typing_unpack_retains_its_public_subscription_contract(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """The real typing callable remains usable after passive recapture."""
        root = real_python_package / "src"
        u.Tests.write_package_init(root / "test_pkg", "from typing import Unpack\n")
        u.Tests.run_lazy_init_probe(
            """from typing import get_args, get_origin
from flext_infra import m
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native
import test_pkg as module
annotation = module.Unpack[tuple[int, str]]
assert get_origin(annotation) is module.Unpack
assert get_args(annotation) == (tuple[int, str],)
selection = (m.Infra.SourceClassReference(target=module.__name__, attributes=('Unpack',)),)
original = native.capture(selection).unwrap()
assert native.compare(original, native.capture(selection).unwrap()).unwrap() is True
assert module.Unpack[tuple[int, str]] == annotation
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
