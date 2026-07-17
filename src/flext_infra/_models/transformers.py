"""Domain models for the transformers subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, ClassVar

from flext_cli import m

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraModelsTransformers:
    """Models for source transformers — exposed through the ``m.Infra`` facade."""

    class SourceRewrite(m.ArbitraryTypesModel):
        """One source rewrite: replace ``source[start:end]`` with ``text``."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(frozen=True)

        start: Annotated[int, m.Field(description="Start byte offset in the source")]
        end: Annotated[int, m.Field(description="End byte offset in the source")]
        text: Annotated[str, m.Field(description="Replacement text")]

    class HeaderSpan(m.ArbitraryTypesModel):
        """Byte offsets for the logical sections of a Python module header.

        Mutable accumulator populated incrementally by the header tokenizer
        (``transformers/_header.py``); never frozen while a parse is open.
        """

        shebang_end: Annotated[
            int, m.Field(description="Byte offset just after the shebang line")
        ] = 0
        encoding_end: Annotated[
            int, m.Field(description="Byte offset just after the encoding cookie")
        ] = 0
        comments_end: Annotated[
            int, m.Field(description="Byte offset after the leading comment block")
        ] = 0
        docstring_end: Annotated[
            int, m.Field(description="Byte offset after the module docstring")
        ] = 0
        last_import_end: Annotated[
            int, m.Field(description="Byte offset after the last import statement")
        ] = 0

    class HeaderInfo(m.ArbitraryTypesModel):
        """Structural summary of a module header."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(frozen=True)

        has_future_annotations: Annotated[
            bool, m.Field(description="Whether the module already imports annotations")
        ]
        aliases: Annotated[
            frozenset[str],
            m.Field(description="Local names bound by from-import statements"),
        ]
        span: Annotated[
            FlextInfraModelsTransformers.HeaderSpan,
            m.Field(description="Byte offsets for the header sections"),
        ]


__all__: list[str] = ["FlextInfraModelsTransformers"]
