# from flext-infra/docs/guides/using-flext-tests.md:143
from flext_core import FlextSettings


def test_settings_override() -> None:
    FlextSettings.reset_for_testing()
    try:
        settings = FlextSettings.fetch_global()
        settings.debug = True
        assert settings.debug
    finally:
        FlextSettings.reset_for_testing()
