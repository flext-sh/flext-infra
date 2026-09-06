"""Typed jscpd invocation contracts for the duplication gate."""

from __future__ import annotations

from typing import Annotated, ClassVar

from flext_core import m
from flext_infra import t


class FlextInfraModelsDuplication:
    """Strict external-boundary models for jscpd 5 invocations."""

    class JscpdConfig(m.ContractModel):
        """Complete generated jscpd invocation configuration."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            extra="forbid", frozen=True, populate_by_name=True
        )

        absolute: Annotated[t.StrictBool, m.Field(description="Emit absolute paths")]
        formats_exts: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(alias="formatsExts", description="Extensions by parser format"),
        ]
        ignore: Annotated[t.StrSequence, m.Field(description="Ignored path patterns")]
        min_lines: Annotated[
            t.PositiveInt,
            m.Field(alias="minLines", description="Minimum duplicated line count"),
        ]
        min_tokens: Annotated[
            t.PositiveInt,
            m.Field(alias="minTokens", description="Minimum duplicated token count"),
        ]
        mode: Annotated[t.NonEmptyStr, m.Field(description="jscpd detection mode")]
        no_colors: Annotated[
            t.StrictBool, m.Field(alias="noColors", description="Disable color output")
        ]
        no_tips: Annotated[
            t.StrictBool, m.Field(alias="noTips", description="Disable tip output")
        ]
        reporters: Annotated[
            t.StrSequence, m.Field(description="Required report formats")
        ]
        threshold: Annotated[
            t.Percentage, m.Field(description="Maximum allowed duplication percentage")
        ]


__all__: list[str] = ["FlextInfraModelsDuplication"]
