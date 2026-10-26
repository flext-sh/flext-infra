"""Method categorization for class-body reordering — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, t


class FlextInfraUtilitiesRopeMethodOrderMixin:
    """Categorize methods by decorators and name pattern.

    Composed into FlextInfraUtilitiesRopeHelpers via inheritance (no state).
    """

    _DECORATOR_TO_CATEGORY: ClassVar[t.StrPairSequence] = [
        ("staticmethod", "static"),
        ("classmethod", "class"),
    ]

    @staticmethod
    def categorize_method(name: str, decorators: t.StrSequence) -> str:
        """Categorize a method by its decorators and name pattern.

        Returns:
            The resulting ``str``.

        """
        result: str
        if c.Infra.PROPERTY_DECORATORS.intersection(decorators):
            result = c.Infra.MethodCategory.PROPERTY
        else:
            for (
                decorator_name,
                category,
            ) in FlextInfraUtilitiesRopeMethodOrderMixin._DECORATOR_TO_CATEGORY:
                if decorator_name in decorators:
                    result = category
                    break
            else:
                if name.startswith("__") and name.endswith("__"):
                    result = c.Infra.MethodCategory.MAGIC
                elif name.startswith("__"):
                    result = c.Infra.MethodCategory.PRIVATE
                elif name.startswith("_"):
                    result = c.Infra.MethodCategory.PROTECTED
                else:
                    result = c.Infra.MethodCategory.PUBLIC
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeMethodOrderMixin"]
