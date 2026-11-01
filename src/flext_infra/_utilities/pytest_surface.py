"""pytest public functions, declared once for the whole fleet.

``u.Infra.Pytest`` is the single owner: flext-tests inherits it under
``u.Tests``. Each member is the pytest function itself.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest


class FlextInfraUtilitiesPytest:
    """pytest functions published under ``u.Infra.Pytest``."""

    class Pytest:
        """pytest functions; flext-tests inherits them."""

        approx = staticmethod(pytest.approx)
        exit = staticmethod(pytest.exit)
        # ``fail`` and ``skip`` are pytest outcome objects called like
        # functions (their class declares ``__call__``), so ``u`` owns them
        # beside ``exit`` (operator ruling 2026-11-01).
        fail = staticmethod(pytest.fail)
        fixture = staticmethod(pytest.fixture)
        # ``pytest.hookimpl`` is a pluggy ``HookimplMarker`` instance, not a
        # function: it is not a descriptor, so wrapping it in ``staticmethod``
        # adds nothing at runtime and erases its overloaded ``__call__``
        # contract for static type checkers. Keep the bare instance.
        hookimpl = pytest.hookimpl
        importorskip = staticmethod(pytest.importorskip)
        main = staticmethod(pytest.main)
        monkeypatch_context = staticmethod(pytest.MonkeyPatch.context)
        param = staticmethod(pytest.param)
        raises = staticmethod(pytest.raises)
        skip = staticmethod(pytest.skip)
        warns = staticmethod(pytest.warns)


__all__: list[str] = ["FlextInfraUtilitiesPytest"]
