"""PEP 723 ``# /// <type>`` comment blocks and their TOML documents.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesScriptMetadata:
    """Locate structured comment blocks and read them as PEP 723 defines.

    The grammar is the specification's reference expression, so every block
    type shares one reader: the ``script`` metadata a promoted command
    declares, and any other ``# /// <type>`` block a repair must preserve.
    """

    @staticmethod
    def script_metadata_blocks(source: str) -> tuple[t.RegexMatch, ...]:
        """Return every ``# /// <type>`` ... ``# ///`` block of ``source``.

        Returns:
            The block matches in source order; ``type`` names the block.

        """
        return tuple(c.Infra.SCRIPT_METADATA_BLOCK_RE.finditer(source))

    @staticmethod
    def script_metadata_toml(block: t.RegexMatch) -> str:
        """Return the TOML document one block carries.

        Each content line loses its leading ``# ``, or ``#`` when it holds
        nothing else, exactly as PEP 723 reads the block.

        Returns:
            The block's TOML text.

        """
        prefix = c.Infra.SCRIPT_METADATA_LINE_PREFIX
        return "".join(
            line.removeprefix(prefix)
            if line.startswith(prefix)
            else line.removeprefix(c.Infra.SCRIPT_METADATA_COMMENT)
            for line in str(block.group("content")).splitlines(keepends=True)
        )


__all__: list[str] = ["FlextInfraUtilitiesScriptMetadata"]
