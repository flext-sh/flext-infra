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
        fixture = staticmethod(pytest.fixture)
        hookimpl = staticmethod(pytest.hookimpl)
        importorskip = staticmethod(pytest.importorskip)
        main = staticmethod(pytest.main)
        monkeypatch_context = staticmethod(pytest.MonkeyPatch.context)
        param = staticmethod(pytest.param)
        raises = staticmethod(pytest.raises)
        warns = staticmethod(pytest.warns)


__all__: list[str] = ["FlextInfraUtilitiesPytest"]
