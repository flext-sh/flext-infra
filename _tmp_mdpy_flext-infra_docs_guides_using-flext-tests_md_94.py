# from flext-infra_docs/guides/using-flext-tests.md:94
from flext_tests import r


def safe_divide(a: float, b: float) -> p.Result[float]:
    if b == 0:
        return r[float].fail("division_by_zero")
    return r[float].ok(a / b)


def test_safe_divide() -> None:
    result = safe_divide(10, 2)
    assert result.success
    assert result.unwrap() == 5.0

    failure = safe_divide(10, 0)
    assert failure.failure
