# from flext-infra/docs/guides/using-flext-core.md:72
from flext_core import FlextSettings

settings = FlextSettings.fetch_global()
assert isinstance(settings.model_dump(), dict)
