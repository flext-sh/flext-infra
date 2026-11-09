"""Promoted-command test utilities for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from flext_infra import config, u
from tests import c, m, p, tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraUtilitiesPromoted:
    """Promoted-command builders shared by the promoted test modules.

    The builder is declared here, not beside one test, because two promoted
    test modules construct the same command and a module-level builder is a
    second owner the namespace contract forbids. ``params`` is typed as the
    model tuple the ``Command`` field actually declares; typing it as the
    protocol made every call a type error while still running.
    """

    # Markers of the retired ``flext-command`` block. Only the reference of
    # what a consumer declared before the PEP 723 cutover reads them.
    PROMOTED_LEGACY_START: Final = "/// flext-command"
    PROMOTED_LEGACY_END: Final = "///"

    @staticmethod
    def promoted_legacy_header(source: str) -> tuple[str, t.JsonMapping]:
        """Return the retired block of ``source`` and the mapping it declared.

        The payload is read exactly as the retired parser read it: every line
        loses its comment marker and surrounding whitespace before TOML.

        Returns:
            The exact block text and the TOML mapping of its payload.

        Raises:
            ValueError: If ``source`` carries no complete retired block.

        """
        marker = TestsFlextInfraUtilitiesPromoted
        lines = source.splitlines(keepends=True)
        contents = [line.strip().removeprefix("#").strip() for line in lines]
        start = contents.index(marker.PROMOTED_LEGACY_START)
        end = contents.index(marker.PROMOTED_LEGACY_END, start + 1)
        mapping = u.Cli.toml_mapping_from_text("\n".join(contents[start + 1 : end]))
        if mapping is None:
            msg = "retired flext-command block carries invalid TOML"
            raise ValueError(msg)
        return "".join(lines[start : end + 1]), mapping

    @staticmethod
    def write_promoted_command(path: Path, command: t.JsonMapping) -> Path:
        """Write one command file whose canonical header declares ``command``.

        The header is the PEP 723 block the dispatcher and the Makefile
        projection both read, rendered within the configured Ruff width.

        Returns:
            The written command path.

        """
        width = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        shebang = (
            "#!/usr/bin/env python3"
            if path.suffix == c.Infra.EXT_PYTHON
            else "#!/usr/bin/env bash"
        )
        header = u.Infra.promoted_render_header(command, width=width)
        tm.ok(u.Cli.atomic_write_text_file(path, f"{shebang}\n{header}\n"))
        return path

    @staticmethod
    def promoted_command(
        *,
        path: Path,
        mutates: bool = True,
        params: tuple[p.Infra.PromotedParam, ...] = (),
        verb: str = "probe",
        what: str = "all",
    ) -> p.Infra.PromotedCommand:
        """Build one real promoted command model for contract tests.

        Returns:
            The resulting ``m.Infra.PromotedCommand``.

        """
        return m.Infra.PromotedCommand(
            verb=verb,
            what=what,
            domain="probe",
            summary="probe",
            description="probe",
            example=f"make {verb} WHAT={what}",
            path=path,
            mutates=mutates,
            aliases=(),
            params=params,
            rules=(),
        )


__all__: list[str] = ["TestsFlextInfraUtilitiesPromoted"]
