# from flext-infra_docs/guides/using-flext-cli.md:52
from flext_cli import FlextCliSettings

settings = FlextCliSettings.fetch_global()
assert settings is FlextCliSettings.fetch_global()
