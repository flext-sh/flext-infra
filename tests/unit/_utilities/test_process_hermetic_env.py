"""Behaviour tests for ``u.Infra.make_hermetic_env_remove_keys``."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm
from tests import c, u


class TestsMakeHermeticEnvRemoveKeys:
    """The removal set is derived from every declared Make variable owner."""

    def test_covers_selector_apply_recursion_and_pytest_keys(self) -> None:
        keys = u.Infra.make_hermetic_env_remove_keys()
        make = config.Infra.codegen.make
        tm.that(make.selector in keys, eq=True)
        tm.that(make.apply_variable in keys, eq=True)
        for key in c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS:
            tm.that(key in keys, eq=True)
        for name, _default in c.Infra.PROJECT_VARIABLE_DEFAULTS:
            tm.that(name in keys, eq=True)
        for key in c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS:
            tm.that(key in keys, eq=True)

    def test_is_deduplicated_and_stable(self) -> None:
        keys = u.Infra.make_hermetic_env_remove_keys()
        tm.that(len(keys), eq=len(set(keys)))
        tm.that(keys, eq=u.Infra.make_hermetic_env_remove_keys())
