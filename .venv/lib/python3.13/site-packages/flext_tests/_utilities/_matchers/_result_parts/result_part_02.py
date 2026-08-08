"""Result matcher helpers for success assertions."""

from __future__ import annotations

from collections.abc import Mapping

from flext_tests import c, m, t
from flext_tests._utilities._matchers._result_parts.result_part_01 import (
    FlextTestsMatchersResultMixin as FlextTestsMatchersResultMixinPart01,
)
from flext_tests._utilities._matchers._typeguards import (
    FlextTestsMatchersTypeGuardsMixin,
)
from flext_tests._utilities.payload import FlextTestsPayloadUtilities
from flext_tests.utilities import u


class FlextTestsMatchersResultMixin(FlextTestsMatchersResultMixinPart01):
    """Helper methods for successful result assertions."""

    class Tests:
        """Container for test utility storages and aliases."""

        class Matchers(FlextTestsMatchersResultMixinPart01.Tests.Matchers):
            """Reusable success matcher helpers."""

            @staticmethod
            def _ok_extract_path(
                result_value: t.Tests.TestResultValue, params: m.Tests.OkParams
            ) -> tuple[t.Tests.TestResultValue, t.Tests.TestobjectSerializable | None]:
                """Apply optional path extraction to a successful result value."""
                if params.path is None:
                    return result_value, None
                path_str = (
                    params.path
                    if isinstance(params.path, str)
                    else ".".join(params.path)
                )
                if not isinstance(result_value, (m.BaseModel, Mapping)):
                    message = params.msg or (
                        "Path extraction requires dict or model, got "
                        f"{type(result_value).__name__}"
                    )
                    raise TypeError(message)
                try:
                    extract_data = FlextTestsPayloadUtilities.to_config_map(
                        result_value
                    )
                except c.ValidationError as exc:
                    raise AssertionError(
                        params.msg or f"Path extraction payload is invalid: {exc}"
                    ) from exc
                extracted = u.extract(extract_data, path_str)
                if extracted.failure:
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_SCOPE_PATH_NOT_FOUND.format(
                            path=path_str, error=extracted.error
                        )
                    )
                extracted_payload = FlextTestsPayloadUtilities.to_payload(
                    extracted.value
                )
                return extracted_payload, extracted_payload

            @staticmethod
            def _ok_has_scalar_validation(params: m.Tests.OkParams) -> bool:
                """Return whether scalar guard validation is requested."""
                return any(
                    getattr(params, name) is not None
                    for name in (
                        "eq",
                        "ne",
                        "none",
                        "empty",
                        "gt",
                        "gte",
                        "lt",
                        "lte",
                        "starts",
                        "ends",
                        "match",
                    )
                )

            @staticmethod
            def _ok_preserves_result_identity(params: m.Tests.OkParams) -> bool:
                """True when no structural extraction kwargs are set (return TResult)."""
                return all(
                    getattr(params, name) is None
                    for name in (
                        "path",
                        "len",
                        "deep",
                        "paths",
                        "items",
                        "attrs_match",
                        "where",
                    )
                )

            @classmethod
            def _ok_validate_scalar[TResult: t.Tests.TestResultValue](
                cls,
                result_value: TResult | t.Tests.TestobjectSerializable,
                params: m.Tests.OkParams,
            ) -> TResult | t.Tests.TestobjectSerializable:
                """Validate scalar predicates for a successful result."""
                if not cls._ok_has_scalar_validation(params):
                    return result_value
                is_type = params.is_ if not isinstance(params.is_, tuple) else None
                result_payload = FlextTestsPayloadUtilities.to_payload(result_value)
                eq_payload, ne_payload = (
                    FlextTestsMatchersTypeGuardsMixin.prepare_eq_ne_payloads(
                        result_payload,
                        params.eq,
                        params.ne,
                        msg=params.msg,
                        default_msg=f"Value {result_value!r} did not satisfy constraints",
                    )
                )
                chk_value: t.GuardInput | None = (
                    None
                    if result_payload is None
                    else FlextTestsPayloadUtilities.to_normalized_value(result_payload)
                )
                guard = m.GuardCheckSpec.model_validate({
                    "eq": FlextTestsPayloadUtilities.to_normalized_value(eq_payload)
                    if eq_payload is not None
                    else None,
                    "ne": FlextTestsPayloadUtilities.to_normalized_value(ne_payload)
                    if ne_payload is not None
                    else None,
                    "is_": is_type,
                    "none": params.none,
                    "empty": params.empty,
                    "gt": params.gt,
                    "gte": params.gte,
                    "lt": params.lt,
                    "lte": params.lte,
                    "starts": params.starts,
                    "ends": params.ends,
                })
                if not u.chk(chk_value, guard):
                    raise AssertionError(
                        params.msg
                        or f"Value {result_value!r} did not satisfy constraints"
                    )
                if (
                    params.match is not None
                    and isinstance(result_payload, str)
                    and params.match.search(result_payload) is None
                ):
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_NOT_MATCHES.format(
                            text=result_payload, pattern=params.match.pattern
                        )
                    )
                return result_value

            @staticmethod
            def _ok_validate_type[TResult: t.Tests.TestResultValue](
                result_value: TResult | t.Tests.TestobjectSerializable,
                params: m.Tests.OkParams,
            ) -> TResult | t.Tests.TestobjectSerializable:
                """Validate tuple-based runtime type constraints."""
                if not (
                    params.is_ is not None
                    and isinstance(params.is_, tuple)
                    and not any(
                        FlextTestsMatchersTypeGuardsMixin.matches_runtime_type(
                            result_value, expected_type
                        )
                        for expected_type in params.is_
                    )
                ):
                    return result_value
                raise AssertionError(
                    params.msg
                    or c.Tests.ERR_TYPE_FAILED.format(
                        expected=params.is_, actual=type(result_value).__name__
                    )
                )


__all__: list[str] = ["FlextTestsMatchersResultMixin"]
