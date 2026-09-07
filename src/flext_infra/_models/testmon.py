"""Typed pytest-testmon cache state owned by the model namespace."""

from __future__ import annotations

from typing import Annotated

from flext_core import m


class FlextInfraModelsTestmon:
    """Models produced by the persistent testmon lifecycle."""

    class TestmonCacheState(m.Value):
        """Decision record after a testmon database integrity pass."""

        seed_needed: Annotated[bool, m.Field(description="No usable DB was present.")]
        restored_accepted: Annotated[
            bool, m.Field(description="An existing DB passed integrity checks.")
        ]
        changed: Annotated[
            bool,
            m.Field(description="DB content changed relative to its input digest."),
        ]
        saveable: Annotated[
            bool, m.Field(description="DB may be published as a cache generation.")
        ]
        reason: Annotated[
            str, m.Field(min_length=1, description="Decisive cache-state reason.")
        ]

    class TestmonRunAccounting(m.Value):
        """Typed proof for one successful testmon-backed pytest invocation."""

        executed_count: Annotated[
            int, m.Field(ge=0, description="JUnit testcase count.")
        ]
        deselected_count: Annotated[
            int,
            m.Field(ge=0, description="Testmon-deselected count reported by pytest."),
        ]
        cache_restored: Annotated[
            bool, m.Field(description="Input database passed SQLite integrity checks.")
        ]


__all__: list[str] = ["FlextInfraModelsTestmon"]
