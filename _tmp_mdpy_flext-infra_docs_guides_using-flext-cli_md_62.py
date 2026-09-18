# from flext-infra_docs/guides/using-flext-cli.md:62
from flext_core import FlextSettings, m


class FlextApiSettings(FlextSettings):
    model_config = m.SettingsConfigDict(env_prefix="FLEXT_API_", extra="ignore")
