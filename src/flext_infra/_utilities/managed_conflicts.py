"""Owner-declared managed document conflict recovery utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, t

from .._utilities.base import FlextInfraUtilitiesBase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesManagedConflicts:
    """Recover only merge blocks authorized by the document owner."""

    @staticmethod
    def recover_managed_toml(
        content: str, *, conflict_sections: t.StrSequence
    ) -> p.Result[str]:
        """Choose current TOML bytes only inside explicitly owned sections."""
        if FlextInfraUtilitiesBase.first_merge_conflict_marker(content) is None:
            return r[str].ok(content)
        allowed = frozenset(conflict_sections)
        lines = content.splitlines(keepends=True)
        recovered: list[str] = []
        section = ""
        index = 0
        while index < len(lines):
            line = lines[index]
            control = FlextInfraUtilitiesBase.merge_conflict_control(line)
            if control is None:
                section_match = c.Infra.TOML_SECTION_HEADER_RE.fullmatch(
                    line.rstrip("\r\n")
                )
                if section_match is not None:
                    section = section_match.group(1)
                recovered.append(line)
                index += 1
                continue
            if control != "current":
                return r[str].fail("orphan TOML merge-control marker")
            if section not in allowed:
                return r[str].fail(
                    "merge conflict is outside owner-declared TOML sections: "
                    f"{section or '<document-root>'}"
                )
            index += 1
            current: list[str] = []
            while index < len(lines):
                control = FlextInfraUtilitiesBase.merge_conflict_control(lines[index])
                if control in {"ancestor", "separator"}:
                    break
                if control is not None:
                    return r[str].fail("nested or malformed TOML merge conflict")
                current.append(lines[index])
                index += 1
            if index >= len(lines):
                return r[str].fail("TOML merge conflict has no separator")
            if control == "ancestor":
                index += 1
                while index < len(lines):
                    control = FlextInfraUtilitiesBase.merge_conflict_control(
                        lines[index]
                    )
                    if control == "separator":
                        break
                    if control is not None:
                        return r[str].fail("nested or malformed TOML merge conflict")
                    index += 1
                if index >= len(lines):
                    return r[str].fail("TOML merge conflict has no separator")
            index += 1
            while index < len(lines):
                control = FlextInfraUtilitiesBase.merge_conflict_control(lines[index])
                if control == "incoming":
                    break
                if control is not None:
                    return r[str].fail("nested or malformed TOML merge conflict")
                index += 1
            if index >= len(lines):
                return r[str].fail("TOML merge conflict has no closing marker")
            for current_line in current:
                section_match = c.Infra.TOML_SECTION_HEADER_RE.fullmatch(
                    current_line.rstrip("\r\n")
                )
                if section_match is not None:
                    section = section_match.group(1)
            recovered.extend(current)
            index += 1
        return r[str].ok("".join(recovered))


__all__: tuple[str, ...] = ("FlextInfraUtilitiesManagedConflicts",)
