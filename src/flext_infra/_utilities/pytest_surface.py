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
        # ``skip`` is a pytest outcome object called like a function (its
        # class declares ``__call__``), so ``u`` owns it beside ``exit``.
        # ``fail`` is not published: ``u.Tests`` inherits this class ahead of
        # its result matchers, and the matcher ``fail`` owns that name.
        # An overloaded pytest function (``fixture``'s bare and keyword-factory
        # forms, ``raises``, ``warns``) is published bare: ``staticmethod``
        # takes one ``Callable[P, R]``, so static type checkers keep only its
        # first overload. Read through this class, a function is the function
        # itself, with every overload.
        fixture = pytest.fixture
        # ``pytest.hookimpl`` is a pluggy ``HookimplMarker`` instance, not a
        # function: it is not a descriptor, so wrapping it in ``staticmethod``
        # adds nothing at runtime and erases its overloaded ``__call__``
        # contract for static type checkers. Keep the bare instance.
        hookimpl = pytest.hookimpl
        importorskip = staticmethod(pytest.importorskip)
        main = staticmethod(pytest.main)
        monkeypatch_context = staticmethod(pytest.MonkeyPatch.context)
        param = staticmethod(pytest.param)
        raises = pytest.raises
        skip = staticmethod(pytest.skip)
        warns = pytest.warns


__all__: list[str] = ["FlextInfraUtilitiesPytest"]
