# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._constants._exports import (
        FLEXT_INFRA__UTILITIES_LAZY_IMPORTS as FLEXT_INFRA__UTILITIES_LAZY_IMPORTS,
    )
    from flext_infra._utilities._constants._exports_lazy_part_01 import (
        FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_01 as FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_01,
    )
    from flext_infra._utilities._constants._exports_lazy_part_02 import (
        FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_02 as FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_02,
    )
    from flext_infra._utilities._constants._exports_lazy_part_03 import (
        FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_03 as FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_03,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._exports": ("FLEXT_INFRA__UTILITIES_LAZY_IMPORTS",),
        "._exports_lazy_part_01": ("FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_01",),
        "._exports_lazy_part_02": ("FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_02",),
        "._exports_lazy_part_03": ("FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_03",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
