"""jscpd report parsing for the duplication gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m, r, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDuplicationReport:
    """Map one native jscpd report to the clones a project owns."""

    gate_id: ClassVar[str]

    @staticmethod
    def _failure_issue(message: str | None) -> m.Infra.Issue:
        """Represent malformed or absent jscpd output as a blocking issue.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=c.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=message or "jscpd returned no parseable report",
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )

    @classmethod
    def _issues_from_report(
        cls,
        project_dir: Path,
        report: m.Infra.JscpdReport | None,
    ) -> p.Result[t.VariadicTuple[m.Infra.Issue]]:
        """Extract one Issue per clone side that falls inside ``project_dir``.

        jscpd can emit both A->B and B->A for one clone; one finding is
        published per unordered span pair.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.Issue]]``.

        """
        if report is None:
            return r[tuple[m.Infra.Issue, ...]].fail(
                f"duplication scan did not produce its required JSON report "
                f"for project {project_dir.name}",
            )
        data = u.Cli.json_as_mapping(report.model_dump(mode="json", by_alias=True))
        issues: dict[str, m.Infra.Issue] = {}
        for duplicate in u.Cli.json_deep_mapping_list(data, "duplicates"):
            owned = cls._owned_clone_issue(duplicate, project_dir)
            if owned is not None:
                issues.setdefault(owned[0], owned[1])
        return r[tuple[m.Infra.Issue, ...]].ok(tuple(issues.values()))

    @classmethod
    def _owned_clone_issue(
        cls,
        duplicate: t.JsonMapping,
        project_dir: Path,
    ) -> t.Pair[str, m.Infra.Issue] | None:
        """Map one reported clone to its owned side, keyed by its span pair.

        The two sides of a clone are the same span only when the same
        directory reached jscpd twice (the double-scan artifact): that is
        never an owned clone. The same file with two different spans is
        genuine intra-file duplication and is reported. Ownership is path
        containment, never a string prefix: a sibling project whose name
        extends this one owns its own clones.

        Returns:
            The unordered span-pair key and the owned side's issue, or
            ``None`` when no side is owned here.

        """
        first = u.Cli.json_deep_mapping(duplicate, "firstFile")
        second = u.Cli.json_deep_mapping(duplicate, "secondFile")
        spans = (cls.side_span_key(first), cls.side_span_key(second))
        if spans[0] == spans[1]:
            return None
        first_owned = Path(cls.report_file_name(first)).is_relative_to(project_dir)
        own, other = (first, second) if first_owned else (second, first)
        if not Path(cls.report_file_name(own)).is_relative_to(project_dir):
            return None
        return "|".join(sorted(spans)), cls._issue_from_duplicate(
            duplicate, own, cls.report_file_name(other), project_dir
        )

    @staticmethod
    def report_file_name(side: t.JsonMapping) -> str:
        """Return one jscpd clone side's on-disk file name.

        jscpd names markdown-embedded code blocks ``<file>:<language>``; the
        range belongs to that embedded block, and ownership to the real file.

        Returns:
            The clone side's file name without any virtual suffix.

        """
        raw = u.Cli.json_pick_str(side, "name")
        file_name, separator, _language = raw.rpartition(":")
        return file_name if separator and file_name and "." in file_name else raw

    @classmethod
    def side_span_key(cls, side: t.JsonMapping) -> str:
        """Return one clone side's on-disk span identity.

        Returns:
            The clone side's ``<file>:<start-line>:<end-line>`` identity.

        """
        name = cls.report_file_name(side)
        start = u.Cli.json_nested_int(side, "startLoc", "line", default=0)
        end = u.Cli.json_nested_int(side, "endLoc", "line", default=start)
        return f"{name}:{start}:{end}"

    @classmethod
    def _issue_from_duplicate(
        cls,
        duplicate: t.JsonMapping,
        own_side: t.JsonMapping,
        other_name: str,
        root: Path,
    ) -> m.Infra.Issue:
        """Map one clone side inside ``root`` to a strict error.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=str(Path(cls.report_file_name(own_side)).relative_to(root)),
            line=u.Cli.json_nested_int(own_side, "startLoc", "line", default=1),
            column=u.Cli.json_nested_int(own_side, "startLoc", "column", default=0),
            code=cls.gate_id,
            message=(
                f"{u.Cli.json_pick_int(duplicate, 'lines', default=0)}-line "
                f"({u.Cli.json_pick_int(duplicate, 'tokens', default=0)}-token) "
                f"clone of {other_name} "
                f"— extend one owner, rewire consumers, delete the duplicate"
            ),
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )


__all__: list[str] = ["FlextInfraDuplicationReport"]
