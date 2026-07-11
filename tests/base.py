"""Service base for flext-infra tests."""

from __future__ import annotations

from typing import override

from flext_tests import s as tests_s

from flext_infra import m
from tests.settings import TestsFlextInfraSettings


class TestsFlextInfraServiceBase(tests_s):
    """Infra test service base with source and test settings namespaces."""

    # NOTE (multi-agent, mro-wkii.17.14): flext-tests owns fetch_settings;
    # this project declares only its more-specific bootstrap settings type.
    @classmethod
    @override
    def _runtime_bootstrap_options(cls) -> m.RuntimeBootstrapOptions:
        return m.RuntimeBootstrapOptions(settings_type=TestsFlextInfraSettings)


s = TestsFlextInfraServiceBase

__all__: list[str] = ["TestsFlextInfraServiceBase", "s"]
