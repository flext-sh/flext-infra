"""Runtime settings for flext-infra tests."""

from __future__ import annotations

from flext_tests.settings import FlextTestsSettings

from flext_infra.settings import FlextInfraSettings


class TestsFlextInfraSettings(FlextInfraSettings, FlextTestsSettings):
    """Infra settings extended with the shared test namespace."""


__all__: list[str] = ["TestsFlextInfraSettings"]
