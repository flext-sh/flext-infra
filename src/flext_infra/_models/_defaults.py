"""Typed immutable defaults shared by Pydantic model fields."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType
from typing import Never, override

from flext_cli import m

from flext_infra import t


class FlextInfraModelsDefaults:
    """Facade for typed immutable defaults shared by Pydantic model fields."""

    class ImmutableEmptyMapping[K, V](Mapping[K, V]):
        """Fully typed immutable empty mapping used as a field factory."""

        @override
        def __getitem__(self, key: K) -> V:
            """Reject every key because the mapping is empty."""
            raise KeyError(key)

        @override
        def __iter__(self) -> Iterator[K]:
            """Iterate over no keys."""
            return iter(())

        @override
        def __len__(self) -> int:
            """Return the invariant empty size."""
            return 0

    @staticmethod
    def immutable_empty_mapping() -> Mapping[str, Never]:
        """Return a fresh immutable empty mapping for any ``Mapping[str, X]`` field.

        The proxy holds no values, so its value type is ``Never``: mapping
        covariance makes the result assignable to every concrete
        ``Mapping[str, X]`` a field declares without inventing key/value
        types the empty factory never produces.
        """
        empty: dict[str, Never] = {}
        return MappingProxyType(empty)

    @staticmethod
    def tool_version_field(description: str) -> t.Infra.ModelFieldSpec:
        """Return the shared field metadata for one native-toolchain version.

        Every toolchain version field previously repeated an identical
        ``m.Field(description=...)`` shape, differing only in the description —
        a structural clone the duplication detector flags as one family whatever
        the literal string. One factory collapses every call site.

        It lives here because ``_models`` declaration modules carry data, not
        behaviour: a field factory is a shared default, so its owner is this
        module, beside ``immutable_empty_mapping``, not a model module.
        """
        return m.Field(description=description)


ImmutableEmptyMapping = FlextInfraModelsDefaults.ImmutableEmptyMapping
immutable_empty_mapping = FlextInfraModelsDefaults.immutable_empty_mapping
tool_version_field = FlextInfraModelsDefaults.tool_version_field

__all__: list[str] = [
    "FlextInfraModelsDefaults",
    "ImmutableEmptyMapping",
    "immutable_empty_mapping",
    "tool_version_field",
]
