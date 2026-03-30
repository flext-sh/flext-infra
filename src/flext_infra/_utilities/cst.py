"""CST name extraction utilities — accessed via u.Infra.*."""

from __future__ import annotations

import libcst as cst


class FlextInfraUtilitiesCst:
    """Minimal libcst name utilities — accessed via u.Infra.*."""

    @staticmethod
    def cst_root_name(expr: cst.BaseExpression) -> str:
        """Extract the leftmost root name from a CST expression.

        Examples:
            Name("foo") → "foo"
            Attribute(Name("foo"), "bar") → "foo"

        """
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return FlextInfraUtilitiesCst.cst_root_name(expr.value)
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesCst.cst_root_name(expr.func)
        return ""


__all__ = ["FlextInfraUtilitiesCst"]
