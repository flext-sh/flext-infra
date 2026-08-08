"""Base result matcher methods."""

from __future__ import annotations

from collections.abc import MutableMapping

from flext_tests._utilities._matchers._containment import (
    FlextTestsMatchersContainmentMixin,
)
from flext_tests._utilities.payload import FlextTestsPayloadUtilities
from flext_tests._utilities.result import FlextTestsResultUtilitiesMixin
from flext_tests.constants import c
from flext_tests.models import m
from flext_tests.protocols import p
from flext_tests.typings import t
from flext_tests.utilities import u


class FlextTestsMatchersResultMixin:
    """Result assertion helpers exposed under ``Tests.Matchers``."""

    class Tests:
        """Container for test utility storages and aliases."""

        class Matchers:
            """Result matcher methods."""

            @staticmethod
            def check[TResult](result: p.Result[TResult]) -> m.Tests.Chain[TResult]:
                """Start chained assertions on result."""
                return m.Tests.Chain(result=result)

            @classmethod
            def fail[TResult](
                cls, result: p.Result[TResult], **kwargs: t.Tests.MatcherKwargValue
            ) -> str:
                """Assert that a result failed and validate its error payload."""
                try:
                    params = m.Tests.FailParams.model_validate(kwargs)
                except c.EXC_BASIC_TYPE as exc:
                    message = f"Parameter validation failed: {exc}"
                    raise ValueError(message) from exc
                err: str = FlextTestsResultUtilitiesMixin.assert_failure(result)
                cls._fail_text(err, params)
                cls._fail_code(result, params)
                cls._fail_data(result, params)
                return err

            @staticmethod
            def _fail_text(err: str, params: m.Tests.FailParams) -> None:
                """Validate textual error constraints."""
                if not any(
                    getattr(params, name)
                    for name in ("has", "lacks", "starts", "ends", "match")
                ):
                    return
                FlextTestsMatchersContainmentMixin.check_has_lacks(
                    err, params.has, params.lacks, params.msg, as_str=True
                )
                if params.starts is not None and (
                    not u.chk(err, m.GuardCheckSpec(starts=params.starts))
                ):
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_NOT_STARTSWITH.format(
                            text=err, prefix=params.starts
                        )
                    )
                if params.ends is not None and (
                    not u.chk(err, m.GuardCheckSpec(ends=params.ends))
                ):
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_NOT_ENDSWITH.format(text=err, suffix=params.ends)
                    )
                if params.match is not None and params.match.search(err) is None:
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_NOT_MATCHES.format(
                            text=err, pattern=params.match.pattern
                        )
                    )

            @staticmethod
            def _fail_code[TResult](
                result: p.Result[TResult], params: m.Tests.FailParams
            ) -> None:
                """Validate error code constraints."""
                if params.code is not None and result.error_code != params.code:
                    raise AssertionError(
                        params.msg
                        or c.Tests.ERR_ERROR_CODE_MISMATCH.format(
                            expected=params.code, actual=result.error_code
                        )
                    )
                if params.code_has is None:
                    return
                actual_code = result.error_code or ""
                code_items: t.StrSequence = (
                    [params.code_has]
                    if isinstance(params.code_has, str)
                    else list(params.code_has)
                )
                for item in code_items:
                    if item not in actual_code:
                        raise AssertionError(
                            params.msg
                            or c.Tests.ERR_ERROR_CODE_NOT_CONTAINS.format(
                                expected=item, actual=actual_code
                            )
                        )

            @staticmethod
            def _fail_data[TResult](
                result: p.Result[TResult], params: m.Tests.FailParams
            ) -> None:
                """Validate structured error data constraints."""
                if params.data is None:
                    return
                actual_raw = result.error_data
                actual_data: MutableMapping[str, t.Tests.TestobjectSerializable] = {}
                if actual_raw is not None:
                    actual_data = {
                        key: FlextTestsPayloadUtilities.to_payload(value)
                        for key, value in actual_raw.items()
                    }
                for key, expected_value in params.data.items():
                    if key not in actual_data:
                        raise AssertionError(
                            params.msg
                            or c.Tests.ERR_ERROR_DATA_KEY_MISSING.format(key=key)
                        )
                    if actual_data[key] != expected_value:
                        raise AssertionError(
                            params.msg
                            or c.Tests.ERR_ERROR_DATA_VALUE_MISMATCH.format(
                                key=key,
                                expected=expected_value,
                                actual=actual_data[key],
                            )
                        )


__all__: list[str] = ["FlextTestsMatchersResultMixin"]
