# from flext-infra_docs/guides/using-flext-core.md:81
from flext_core import FlextSettings, m


class GreetingSettings(FlextSettings):
    model_config = m.SettingsConfigDict(env_prefix="GREETING_", extra="forbid")
