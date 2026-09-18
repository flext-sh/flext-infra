# from flext-infra/docs/guides/using-flext-core.md:113
from typing import override

from flext_core import p, r, s


class GreetingService(s[str]):
    @override
    def execute(self) -> p.Result[str]:
        return r[str].ok("Hello!")


runtime = GreetingService.fetch_global()
result = runtime.execute()
assert result.success
assert result.value == "Hello!"
