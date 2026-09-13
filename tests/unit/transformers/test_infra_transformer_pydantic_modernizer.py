"""Unit tests for the Pydantic modernizer transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.transformers.pydantic_modernizer import (
    FlextInfraRefactorPydanticModernizer,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def _transform(source: str) -> str:
    """Apply the Pydantic modernizer to source text."""
    transformer = FlextInfraRefactorPydanticModernizer()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result[0]


class TestsFlextInfraTransformersPydanticModernizer:
    """Behavior contract for FlextInfraRefactorPydanticModernizer."""

    def test_config_class_to_config_dict(self) -> None:
        source = (
            "from pydantic import BaseModel\n\n"
            "class User(BaseModel):\n"
            '    name: str = ""\n'
            "    class Config:\n"
            "        str_strip_whitespace = True\n"
        )
        code = _transform(source)
        tm.that(code, has="model_config = ConfigDict(str_strip_whitespace = True)")
        tm.that(code, lacks="class Config:")

    def test_preserves_ambiguous_dict_method(self) -> None:
        source = "payload = response.dict()\n"
        code = _transform(source)
        tm.that(code, has="response.dict()")
        tm.that(code, lacks="model_dump()")

    def test_preserves_ambiguous_json_method(self) -> None:
        source = "payload = response.json()\n"
        code = _transform(source)
        tm.that(code, has="response.json()")
        tm.that(code, lacks="model_dump_json()")

    def test_parse_obj_to_model_validate(self) -> None:
        source = "user = User.parse_obj({})\n"
        code = _transform(source)
        tm.that(code, has="model_validate({})")
        tm.that(code, lacks="parse_obj")

    def test_preserves_ambiguous_schema_method(self) -> None:
        source = "schema = document.schema()\n"
        code = _transform(source)
        tm.that(code, has="document.schema()")
        tm.that(code, lacks="model_json_schema()")

    def test_validator_to_field_validator(self) -> None:
        source = (
            "from pydantic import validator\n\n"
            "class User(BaseModel):\n"
            "    name: str\n\n"
            '    @validator("name")\n'
            "    def _check_name(cls, value: str) -> str:\n"
            "        return value\n"
        )
        code = _transform(source)
        tm.that(code, has='@field_validator("name", mode="after")')
        tm.that(code, lacks="@validator(")

    def test_root_validator_to_model_validator(self) -> None:
        source = (
            "from pydantic import root_validator\n\n"
            "class User(BaseModel):\n"
            "    name: str\n\n"
            "    @root_validator(pre=True)\n"
            "    def _check(cls, values):\n"
            "        return values\n"
        )
        code = _transform(source)
        tm.that(code, has='@model_validator(pre=True, mode="before")')
        tm.that(code, lacks="@root_validator(")

    def test_dunder_fields_to_model_fields(self) -> None:
        source = "fields = User.__fields__\n"
        code = _transform(source)
        tm.that(code, has="User.model_fields")
        tm.that(code, lacks="__fields__")

    def test_preserves_non_pydantic_class(self) -> None:
        source = "class Config:\n    value = 1\n\nclass User(Config):\n    pass\n"
        code = _transform(source)
        tm.that(code, has="class Config:")
        tm.that(code, lacks="ConfigDict")
