"""Pipeline execution constants."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_core import t


class FlextCliConstantsPipeline:
    """Flat pipeline execution constants namespace."""

    PIPELINE_DEFAULT_FAIL_FAST: Final[bool] = True
    PIPELINE_DEFAULT_RETRY: Final[t.RetryCount] = 0
    PIPELINE_MAX_RETRY: Final[t.RetryCount] = 3


__all__: t.MutableSequenceOf[str] = ["FlextCliConstantsPipeline"]
