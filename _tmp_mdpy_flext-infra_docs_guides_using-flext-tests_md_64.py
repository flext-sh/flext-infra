# from flext-infra_docs/guides/using-flext-tests.md:64
from __future__ import annotations

from flext_core import FlextSettings
from flext_tests import FlextTestsSettings


def test_settings_isolation(settings: FlextTestsSettings) -> None:
    settings.debug = True
    # The settings plugin resets runtime singletons between test functions.
    assert FlextSettings.fetch_global() is not settings
