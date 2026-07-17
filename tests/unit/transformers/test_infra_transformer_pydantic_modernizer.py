"""Unit tests for the Pydantic modernizer transformer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.transformers.pydantic_modernizer import (
    FlextInfraRefactorPydanticModernizer,
)


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

    def test_dict_to_model_dump(self) -> None:
        source = "user = User().dict()\n"
        code = _transform(source)
        tm.that(code, has="model_dump()")
        tm.that(code, lacks=".dict()")

    def test_json_to_model_dump_json(self) -> None:
        source = "user = User().json()\n"
        code = _transform(source)
        tm.that(code, has="model_dump_json()")
        tm.that(code, lacks=".json()")

    def test_parse_obj_to_model_validate(self) -> None:
        source = "user = User.parse_obj({})\n"
        code = _transform(source)
        tm.that(code, has="model_validate({})")
        tm.that(code, lacks="parse_obj")

    def test_schema_to_model_json_schema(self) -> None:
        source = "schema = User.schema()\n"
        code = _transform(source)
        tm.that(code, has="model_json_schema()")
        tm.that(code, lacks=".schema()")

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
