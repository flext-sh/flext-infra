"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    @staticmethod
    def resolve_repository_root_or_cwd(repository_root: Path | None = None) -> Path:
        """Resolve the root a verb operates on from its invocation point.

        Scope follows where the verb is invoked: run it at the workspace and it
        works on the whole active workspace; run it inside a project and it
        works on that project alone. The checkout is therefore the root, and a
        member is never escalated to its enclosing superproject.

        Escalating inverted that rule. A verb invoked inside one member
        resolved every relative path against the superproject shared by all
        sibling worktrees, so project-local inputs were resolved in the wrong
        checkout and `.reports/tests/latest.txt` was written to the shared root,
        where each project's run overwrote the previous one's evidence.
        """
        target = repository_root or Path.cwd()
        if target.is_file():
            target = target.parent
        return target.resolve()

    @staticmethod
    def normalize_optional_path(value: str | Path | None) -> Path | None:
        """Resolve one optional path-like value when present."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @staticmethod
    def normalize_cli_values(*values: str | None) -> t.StrSequence:
        """Normalize comma-separated or whitespace-separated CLI selectors."""
        return tuple(
            item.strip()
            for value in values
            for group in (value or "").split(",")
            for item in group.split()
            if item.strip()
        )

    @staticmethod
    def normalize_sequence_values(values: t.StrSequence | None) -> t.StrSequence | None:
        """Normalize repeated CLI sequence fields into a compact selector list."""
        names = FlextInfraUtilitiesBase.normalize_cli_values(*(values or ()))
        return names or None

    @staticmethod
    def path_depth(path: Path) -> int:
        """Return the number of components in a path."""
        return len(path.parts)

    @staticmethod
    def path_depth_then_text(path: Path) -> tuple[int, str]:
        """Order paths by depth and then their stable POSIX representation."""
        return FlextInfraUtilitiesBase.path_depth(path), path.as_posix()

    @staticmethod
    def first_merge_conflict_marker(content: str) -> str | None:
        """Return the first Git merge-control line in rendered content."""
        return next(
            (
                line
                for line in content.splitlines()
                if FlextInfraUtilitiesBase.merge_conflict_control(line) is not None
            ),
            None,
        )

    @staticmethod
    def merge_conflict_control(line: str) -> str | None:
        """Classify one Git merge-control line from the protocol SSOT."""
        return next(
            (
                kind
                for kind, token in c.Infra.MERGE_CONFLICT_CONTROLS
                if line.startswith(token)
            ),
            None,
        )

    @staticmethod
    def ast_grep_scan_command(
        rule_path: Path,
        *,
        rule_ids: t.StrSequence = (),
        targets: t.StrSequence = (".",),
        json_stream: bool = False,
        update_all: bool = False,
    ) -> t.StrSequence:
        """Build one ast-grep scan command with explicit cwd-relative targets."""
        if not targets or any(Path(target).is_absolute() for target in targets):
            msg = "ast-grep scan targets must be nonempty and cwd-relative"
            raise ValueError(msg)
        config_path = next(
            (
                ancestor / c.Infra.CODEMOD_CONFIG_FILENAME
                for ancestor in rule_path.resolve().parents
                if (ancestor / c.Infra.CODEMOD_CONFIG_FILENAME).is_file()
            ),
            None,
        )
        if config_path is None:
            msg = f"ast-grep rule has no owning config: {rule_path}"
            raise ValueError(msg)
        command = [c.Infra.SG, c.Infra.SCAN]
        if rule_ids:
            if any(not rule_id or "|" in rule_id for rule_id in rule_ids):
                msg = "ast-grep rule IDs must be nonempty literal IDs"
                raise ValueError(msg)
            command.extend((
                c.Infra.SG_CONFIG_FLAG,
                str(config_path),
                c.Infra.SG_FILTER_FLAG,
                "|".join(sorted(rule_ids)),
            ))
        else:
            command.extend(("--rule", str(rule_path)))
        if json_stream:
            command.append("--json=stream")
        if update_all:
            command.append(c.Infra.SG_UPDATE_ALL)
        command.extend(targets)
        return tuple(command)

    @staticmethod
    def strongly_connected_components(
        graph: t.MappingKV[str, set[str]],
    ) -> t.SequenceOf[t.StrSequence]:
        """Return every strongly connected component in one directed graph."""
        next_index = 0
        stack: list[str] = []
        indexes: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        on_stack: set[str] = set()
        components: list[t.StrSequence] = []

        def visit(node: str) -> None:
            nonlocal next_index
            indexes[node] = next_index
            lowlinks[node] = next_index
            next_index += 1
            stack.append(node)
            on_stack.add(node)
            for successor in graph.get(node, set()):
                if successor not in indexes:
                    visit(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif successor in on_stack:
                    lowlinks[node] = min(lowlinks[node], indexes[successor])
            if lowlinks[node] != indexes[node]:
                return
            component: list[str] = []
            while stack:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(tuple(component))

        for node in graph:
            if node not in indexes:
                visit(node)
        return tuple(components)

    @staticmethod
    def classify_process_exit(exit_code: int) -> str:
        """Classify a nonzero process status as timeout, signal, or failure."""
        if exit_code == c.Infra.PROCESS_TIMEOUT_EXIT_CODE:
            return "timeout"
        if exit_code < 0:
            return f"signal={-exit_code}"
        if exit_code >= c.Infra.PROCESS_SIGNAL_EXIT_OFFSET:
            return f"signal={exit_code - c.Infra.PROCESS_SIGNAL_EXIT_OFFSET}"
        return "failure"


__all__: list[str] = ["FlextInfraUtilitiesBase"]
