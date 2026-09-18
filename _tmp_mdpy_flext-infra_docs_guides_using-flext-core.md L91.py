# from flext-infra/docs/guides/using-flext-core.md:91
from flext_core import FlextContainer, p

container = FlextContainer()
container.bind("service", "ready")
resolved: p.Result[str] = container.resolve("service", type_cls=str)

assert resolved.success
assert resolved.value == "ready"
