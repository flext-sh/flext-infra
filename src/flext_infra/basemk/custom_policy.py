"""Reserved-target blacklist for member custom.mk surfaces.

Policy (mro-ga9q): custom.mk is a BLACKLIST surface, not a whitelist. A member
project may define ANY custom verb/WHAT through ``_custom_<verb>_<what>``
handlers and ``(pre|post)-<verb>[-<what>]`` lifecycle hooks EXCEPT the reserved
verbs/WHATs that stay a flext-infra monopoly:

* every public verb name (the workspace ``make.verbs`` SSOT plus the generated
  base.mk project verbs) is reserved as a target name, and
* every builtin ``(verb, WHAT)`` pair is reserved as a ``_custom_<verb>_<what>``
  handler, so a member cannot shadow a builtin implementation.

Everything else is permitted. The generated base.mk enforces the same
blacklist at make parse time (``base_preflight.mk.j2``), so a redefinition
fails every invocation loud; this module is the typed Python owner of the
same rule and the SSOT the template guard is rendered from.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraCustomMkPolicy(s[bool]):
    """Enforce the custom.mk reserved-target blacklist."""

    path: Annotated[Path | None, m.Field(description="custom.mk path to validate")] = (
        None
    )

    @override
    def execute(self) -> p.Result[bool]:
        """Validate the configured custom.mk file against the blacklist."""
        if self.path is None:
            return r[bool].fail("custom.mk path is required")
        read = u.Cli.files_read_text(self.path)
        if read.failure:
            return r[bool].fail(read.error or f"custom.mk read failed: {self.path}")
        return self.validate_content(read.value)

    @classmethod
    def reserved_verbs(cls) -> frozenset[str]:
        """Reserved verb names: workspace SSOT plus generated base.mk verbs."""
        declared = {verb.name for verb in config.Infra.codegen.make.verbs}
        return frozenset(declared | set(c.Infra.CUSTOM_MK_RESERVED_PROJECT_VERBS))

    @classmethod
    def reserved_targets(cls) -> frozenset[str]:
        """Reserved targets: verbs plus builtin ``_custom_<verb>_<what>`` pairs."""
        targets = set(cls.reserved_verbs())
        prefix = c.Infra.CUSTOM_HANDLER_PREFIX
        for verb, whats in config.Infra.codegen.make.handler_whats.items():
            targets.update(f"{prefix}{verb}_{what}" for what in whats)
        return frozenset(targets)

    @classmethod
    def validate_content(cls, content: str) -> p.Result[bool]:
        """Fail loud when content redefines a reserved verb or WHAT handler."""
        reserved = cls.reserved_targets()
        offenders = [
            f"line {line_number} redefines '{name}'"
            for line_number, name in cls._target_definitions(content)
            if name in reserved
        ]
        if offenders:
            return r[bool].fail(
                f"{c.Infra.CUSTOM_MAKE_FILENAME} redefines reserved flext-infra "
                f"target(s): {', '.join(offenders)} - "
                f"{c.Infra.CUSTOM_MK_BLACKLIST_ERROR}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _target_definitions(content: str) -> list[tuple[int, str]]:
        """Return ``(line, name)`` for every target defined at column 0."""
        found: list[tuple[int, str]] = []
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if not raw_line or raw_line[0].isspace():
                continue
            if raw_line.startswith((".", "#")):
                continue
            if (
                c.Infra.MAKE_CONDITIONAL_RE.match(raw_line)
                or c.Infra.MAKE_DIRECTIVE_RE.match(raw_line)
                or c.Infra.MAKE_ASSIGNMENT_RE.match(raw_line)
            ):
                continue
            head, separator, _ = raw_line.partition(":")
            if not separator or "=" in head:
                continue
            found.extend(
                (line_number, name)
                for name in head.split()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name)
            )
        return found


__all__: list[str] = ["FlextInfraCustomMkPolicy"]
