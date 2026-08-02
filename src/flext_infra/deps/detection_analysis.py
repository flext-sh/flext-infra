"""Container-value conversion helpers for dependency detection."""

from __future__ import annotations

from typing import override

from flext_infra import c, t
from flext_infra.deps._detection_runners import (
    FlextInfraDependencyDetectionRunnersMixin,
)


class FlextInfraDependencyDetectionAnalysis(FlextInfraDependencyDetectionRunnersMixin):
    """Typings analysis + conversion helpers composed with the tool-runner mixin."""

    @override
    def _to_toml_config(
        self, payload: t.MappingKV[str, t.Infra.InfraValue]
    ) -> t.JsonMapping:
        """Materialize an already validated dependency payload."""
        return dict(payload)

    @staticmethod
    def to_infra_value(value: t.Infra.InfraValue | None) -> t.Infra.InfraValue | None:
        """Convert container value to namespaced infra value."""
        if value is None:
            return None
        if isinstance(value, t.PRIMITIVES_TYPES):
            return value
        if isinstance(value, list):
            try:
                return t.Cli.JSON_LIST_ADAPTER.validate_python(value)
            except c.ValidationError as exc:
                msg = "dependency value is not a valid JSON sequence"
                raise TypeError(msg) from exc
        try:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        except c.ValidationError as exc:
            msg = "dependency value is not a valid JSON mapping"
            raise TypeError(msg) from exc


__all__: list[str] = ["FlextInfraDependencyDetectionAnalysis"]
