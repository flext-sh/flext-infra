# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Utilities. Matchers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _result_parts as _result_parts
    from ._assertions import (
        FlextTestsMatchersAssertionsMixin as FlextTestsMatchersAssertionsMixin,
    )
    from ._containment import (
        FlextTestsMatchersContainmentMixin as FlextTestsMatchersContainmentMixin,
    )
    from ._result import FlextTestsMatchersResultMixin as FlextTestsMatchersResultMixin
    from ._scope import FlextTestsMatchersScopeMixin as FlextTestsMatchersScopeMixin
    from ._that import FlextTestsMatchersThatMixin as FlextTestsMatchersThatMixin
    from ._typeguards import (
        FlextTestsMatchersTypeGuardsMixin as FlextTestsMatchersTypeGuardsMixin,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._assertions": ("FlextTestsMatchersAssertionsMixin",),
    "._containment": ("FlextTestsMatchersContainmentMixin",),
    "._result": ("FlextTestsMatchersResultMixin",),
    "._result_parts": ("_result_parts",),
    "._scope": ("FlextTestsMatchersScopeMixin",),
    "._that": ("FlextTestsMatchersThatMixin",),
    "._typeguards": ("FlextTestsMatchersTypeGuardsMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsMatchersAssertionsMixin",
    "FlextTestsMatchersContainmentMixin",
    "FlextTestsMatchersResultMixin",
    "FlextTestsMatchersScopeMixin",
    "FlextTestsMatchersThatMixin",
    "FlextTestsMatchersTypeGuardsMixin",
    "_result_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
