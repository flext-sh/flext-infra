"""Service base for flext-infra tests."""

from __future__ import annotations

from flext_tests import s as tests_s


class TestsFlextInfraServiceBase(tests_s):
    """Infra test service base composed directly from flext-tests."""

    # NOTE (multi-agent, mro-wkii.17.14): flext-tests is the sole owner of
    # settings bootstrap behavior; this project adds no forwarding override.


s = TestsFlextInfraServiceBase

__all__: list[str] = ["TestsFlextInfraServiceBase", "s"]
