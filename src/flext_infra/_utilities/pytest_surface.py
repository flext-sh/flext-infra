"""pytest public functions, declared once for the whole fleet.

``u.Infra.Pytest`` is the single owner: flext-tests inherits it under
``u.Tests``. Each member is the pytest function itself.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_core import FlextTypingNativeExport


class FlextInfraUtilitiesPytest:
    """pytest functions published under ``u.Infra.Pytest``."""

    class Pytest:
        """pytest functions; flext-tests inherits them.

        Every member is republished through ``FlextTypingNativeExport``, which
        returns pytest's object unchanged for class and instance reads with
        its complete static type. ``staticmethod`` takes one
        ``Callable[P, R]``, so it would keep only the first overload of
        ``fixture`` (whose keyword factory form is the second), ``raises``
        and ``warns``; a bare function would bind the facade class to the
        first parameter.
        """

        approx = FlextTypingNativeExport(pytest.approx)
        exit = FlextTypingNativeExport(pytest.exit)
        # ``skip`` is a pytest outcome object called like a function (its
        # class declares ``__call__``), so ``u`` owns it beside ``exit``.
        # ``fail`` is not published: ``u.Tests`` inherits this class ahead of
        # its result matchers, and the matcher ``fail`` owns that name.
        fixture = FlextTypingNativeExport(pytest.fixture)
        hookimpl = FlextTypingNativeExport(pytest.hookimpl)
        importorskip = FlextTypingNativeExport(pytest.importorskip)
        main = FlextTypingNativeExport(pytest.main)
        monkeypatch_context = FlextTypingNativeExport(pytest.MonkeyPatch.context)
        param = FlextTypingNativeExport(pytest.param)
        raises = FlextTypingNativeExport(pytest.raises)
        skip = FlextTypingNativeExport(pytest.skip)
        warns = FlextTypingNativeExport(pytest.warns)


__all__: list[str] = ["FlextInfraUtilitiesPytest"]
