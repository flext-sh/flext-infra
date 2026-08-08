"""Public success result matcher method."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast, overload

from flext_tests import c, m, t
from flext_tests._utilities._matchers._assertions import (
    FlextTestsMatchersAssertionsMixin,
)
from flext_tests._utilities._matchers._containment import (
    FlextTestsMatchersContainmentMixin,
)
from flext_tests._utilities._matchers._result_parts.result_part_02 import (
    FlextTestsMatchersResultMixin as FlextTestsMatchersResultMixinPart02,
)
from flext_tests._utilities._matchers._that import (
    FlextTestsMatchersThatMixin as FlextTestsMatchersRulesMixin,
)
from flext_tests._utilities.payload import FlextTestsPayloadUtilities
from flext_tests._utilities.result import FlextTestsResultUtilitiesMixin
from flext_tests.protocols import p as core_p


class FlextTestsMatchersResultMixin(FlextTestsMatchersResultMixinPart02):
    class Tests:
        class Matchers(FlextTestsMatchersResultMixinPart02.Tests.Matchers):
            @classmethod
            @overload
            def ok[TResult: t.Tests.TestResultValue](
                cls, result: core_p.Result[TResult]
            ) -> TResult: ...

            @classmethod
            @overload
            def ok[TResult: t.Tests.TestResultValue](
                cls, result: core_p.Result[TResult], **kwargs: t.Tests.MatcherKwargValue
            ) -> TResult | t.Tests.TestobjectSerializable: ...

            @classmethod
            def ok[TResult: t.Tests.TestResultValue](
                cls, result: core_p.Result[TResult], **kwargs: t.Tests.MatcherKwargValue
            ) -> TResult | t.Tests.TestobjectSerializable:
                try:
                    params = m.Tests.OkParams.model_validate(kwargs)
                except c.EXC_BASIC_TYPE as exc:
                    message = f"Parameter validation failed: {exc}"
                    raise ValueError(message) from exc
                result_value: t.Tests.TestResultValue = (
                    FlextTestsResultUtilitiesMixin.assert_success(
                        result, error_msg=params.msg
                    )
                )
                result_value, extracted_payload = cls._ok_extract_path(
                    result_value, params
                )
                result_value = cls._ok_validate_scalar(result_value, params)
                result_value = cls._ok_validate_type(result_value, params)
                FlextTestsMatchersContainmentMixin.check_has_lacks(
                    result_value, params.has, params.lacks, params.msg
                )
                result_payload = cls._ok_payload(
                    result, result_value, extracted_payload, params
                )
                cls._ok_validate_structured(
                    result, result_value, result_payload, params
                )
                if result_value is None:
                    raise AssertionError(
                        params.msg
                        or "Value is None but validation passed - this should not happen"
                    )
                if cls._ok_preserves_result_identity(params):
                    return cast("TResult", result_value)
                return result_payload

            @staticmethod
            def _ok_payload[TResult: t.Tests.TestResultValue](
                result: core_p.Result[TResult],
                result_value: t.Tests.TestResultValue,
                extracted_payload: t.Tests.TestobjectSerializable | None,
                params: m.Tests.OkParams,
            ) -> t.Tests.TestobjectSerializable:
                if params.path is None:
                    return FlextTestsPayloadUtilities.to_payload(result.value)
                if extracted_payload is not None:
                    return extracted_payload
                return FlextTestsPayloadUtilities.to_payload(result_value)

            @classmethod
            def _ok_validate_structured[TResult: t.Tests.TestResultValue](
                cls,
                result: core_p.Result[TResult],
                result_value: t.Tests.TestResultValue,
                result_payload: t.Tests.TestobjectSerializable,
                params: m.Tests.OkParams,
            ) -> None:
                if params.len is not None:
                    FlextTestsMatchersAssertionsMixin.assert_len_match(
                        payload=result_payload,
                        sized=result_value,
                        length_spec=params.len,
                        msg=params.msg,
                    )
                if params.deep is not None:
                    cls._ok_validate_deep(result_value, params)
                if params.paths is not None:
                    FlextTestsMatchersRulesMixin.apply_path_rules(
                        result_payload, params.paths, inherited_msg=params.msg
                    )
                if params.items is not None:
                    FlextTestsMatchersRulesMixin.apply_item_rules(
                        result_payload, params.items, inherited_msg=params.msg
                    )
                if params.attrs_match is not None:
                    FlextTestsMatchersRulesMixin.apply_attribute_rules(
                        result.value, params.attrs_match, inherited_msg=params.msg
                    )
                if params.where is not None and (not params.where(result_payload)):
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_PREDICATE_FAILED.format(value=result_payload)
                    )

            @staticmethod
            def _ok_validate_deep[TResult: t.Tests.TestResultValue](
                result_value: TResult | t.Tests.TestobjectSerializable,
                params: m.Tests.OkParams,
            ) -> TResult | t.Tests.TestobjectSerializable:
                deep_spec = params.deep
                if deep_spec is None:
                    return result_value
                if not isinstance(result_value, (m.BaseModel, Mapping)):
                    message = params.msg or (
                        "Deep matching requires dict or model, got "
                        f"{type(result_value).__name__}"
                    )
                    raise TypeError(message)
                deep_input: (
                    m.BaseModel | t.MappingKV[str, t.Tests.TestobjectSerializable]
                )
                if isinstance(result_value, m.BaseModel):
                    deep_input = result_value
                else:
                    try:
                        deep_input = t.Tests.TESTOBJECT_SERIALIZABLE_MAPPING_ADAPTER.validate_python(
                            result_value
                        )
                    except c.ValidationError as exc:
                        raise AssertionError(
                            params.msg or f"Deep matching payload is invalid: {exc}"
                        ) from exc
                match_result = FlextTestsPayloadUtilities.deep_match(
                    deep_input, deep_spec
                )
                if not match_result.matched:
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_DEEP_PATH_FAILED.format(
                            path=match_result.path, reason=match_result.reason
                        )
                    )
                return result_value


__all__: list[str] = ["FlextTestsMatchersResultMixin"]
