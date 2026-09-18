# from flext-infra_docs/guides/using-flext-core.md:53
from __future__ import annotations

from flext_core import p, r


def safe_divide(a: float, b: float) -> p.Result[float]:
    if b == 0:
        return r[float].fail("division_by_zero")
    return r[float].ok(a / b)


assert safe_divide(10, 2).success
assert safe_divide(10, 2).value == 5.0
assert safe_divide(10, 0).failure
