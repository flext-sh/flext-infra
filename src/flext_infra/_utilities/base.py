"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, t
from flext_infra._settings import FlextInfraSettings

if os.name != "nt":
    import pwd


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    @staticmethod
    def env_lookup(name: str) -> str | None:
        """Return one raw environment value through the governed boundary.

        The only sanctioned escape hatch for keys that are dynamic by
        contract (caller-named CLI parameters, CI passthrough variables,
        subprocess environment merges). Static values must be typed
        ``settings.Infra.*`` fields instead; ambient ``os.environ`` reads
        elsewhere are banned by the ``ban-ambient-environ-read`` rule.

        Returns:
            One raw environment value through the governed boundary.

        """
        return FlextInfraSettings.env_lookup(name)

    @staticmethod
    def env_value(name: str, default: str = "") -> str:
        """Return one stripped dynamic environment value, or the stripped default.

        Only an unset variable falls back to ``default``; a set but blank value
        stays blank so callers can reject it explicitly.

        Returns:
            One stripped dynamic environment value, or the stripped default.

        """
        value = FlextInfraSettings.env_lookup(name)
        return default.strip() if value is None else value.strip()

    @staticmethod
    def resolve_repository_root_or_cwd(
        repository_root: t.Infra.Path | None = None,
    ) -> t.Infra.Path:
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

        Returns:
            The resulting ``Path``.

        """
        return m.Infra.CommandContext.model_validate(
            {"repository_root": repository_root} if repository_root is not None else {},
        ).repository_root

    @staticmethod
    def real_account_home() -> Path:
        """Return the real account home directory, never the ambient ``HOME``.

        A workspace contract target written as ``${HOME}/...`` describes machine
        state, so it probes the account's own home directory: check pipelines run
        under redirected homes where the referenced files legitimately live only
        in the real account. On Windows the process home is authoritative.

        Returns:
            The real account home directory, never the ambient ``HOME``.

        """
        return (
            Path.home() if os.name == "nt" else Path(pwd.getpwuid(os.getuid()).pw_dir)
        )

    @staticmethod
    def normalize_optional_path(value: t.Cli.TextPath | None) -> t.Infra.Path | None:
        """Resolve one optional path-like value when present.

        Returns:
            The resulting ``Path | None``.

        """
        return m.Infra.CommandContext.model_validate({"report_path": value}).report_path

    @staticmethod
    def normalize_cli_values(*values: str | None) -> t.StrSequence:
        """Normalize comma-separated or whitespace-separated CLI selectors.

        Returns:
            The resulting ``t.StrSequence``.

        """
        normalized = m.Infra.CommandContext.model_validate(
            {"project_filter": tuple(value for value in values if value is not None)},
        ).project_filter
        return tuple(normalized.split(",")) if normalized else ()

    @staticmethod
    def normalize_sequence_values(values: t.StrSequence | None) -> t.StrSequence | None:
        """Normalize repeated CLI sequence fields into a compact selector list.

        Returns:
            The resulting ``t.StrSequence | None``.

        """
        names = FlextInfraUtilitiesBase.normalize_cli_values(*(values or ()))
        return names or None

    @staticmethod
    def path_depth(path: Path) -> int:
        """Return the number of components in a path.

        Returns:
            The number of components in a path.

        """
        return len(path.parts)

    @staticmethod
    def path_depth_then_text(path: Path) -> t.Pair[int, str]:
        """Order paths by depth and then their stable POSIX representation.

        Returns:
            The resulting ``t.Pair[int, str]``.

        """
        return FlextInfraUtilitiesBase.path_depth(path), path.as_posix()

    @staticmethod
    def first_merge_conflict_marker(content: str) -> str | None:
        """Return the first Git merge-control line in rendered content.

        Returns:
            The first Git merge-control line in rendered content.

        """
        return next(
            (
                line
                for line in content.splitlines()
                if FlextInfraUtilitiesBase.merge_conflict_control(line) is not None
            ),
            None,
        )

    # Pre-computed merge-conflict token sets for O(1) dispatch (avoids
    # repeated isinstance/encode calls in the 1M+ hot path).
    _MERGE_CONFLICT_SEPARATOR_BYTES = frozenset(
        token.encode(c.Infra.MERGE_CONFLICT_ENCODING)
        for kind, token in c.Infra.MERGE_CONFLICT_CONTROLS
        if kind == c.Infra.MergeConflictControl.SEPARATOR
    )
    _MERGE_CONFLICT_SEPARATOR_STR = frozenset(
        token
        for kind, token in c.Infra.MERGE_CONFLICT_CONTROLS
        if kind == c.Infra.MergeConflictControl.SEPARATOR
    )
    _MERGE_CONFLICT_PREFIX_BYTES: tuple[
        tuple[bytes, c.Infra.MergeConflictControl], ...
    ] = tuple(
        (
            token.encode(c.Infra.MERGE_CONFLICT_ENCODING),
            kind,
        )
        for kind, token in c.Infra.MERGE_CONFLICT_CONTROLS
        if kind != c.Infra.MergeConflictControl.SEPARATOR
    )
    _MERGE_CONFLICT_PREFIX_STR: tuple[tuple[str, c.Infra.MergeConflictControl], ...] = (
        tuple(
            (token, kind)
            for kind, token in c.Infra.MERGE_CONFLICT_CONTROLS
            if kind != c.Infra.MergeConflictControl.SEPARATOR
        )
    )

    @classmethod
    def merge_conflict_control(
        cls,
        line: str | bytes,
    ) -> c.Infra.MergeConflictControl | None:
        """Classify one Git merge-control line from the protocol SSOT.

        Returns:
            The matching typed Git control, or ``None``.

        """
        if isinstance(line, bytes):
            stripped = line.rstrip(
                c.Infra.MERGE_CONFLICT_LINE_TERMINATORS.encode(
                    c.Infra.MERGE_CONFLICT_ENCODING,
                )
            )
            if stripped in FlextInfraUtilitiesBase._MERGE_CONFLICT_SEPARATOR_BYTES:
                return c.Infra.MergeConflictControl.SEPARATOR
            for token, kind in FlextInfraUtilitiesBase._MERGE_CONFLICT_PREFIX_BYTES:
                if line.startswith(token):
                    return kind
            return None
        stripped = line.rstrip(c.Infra.MERGE_CONFLICT_LINE_TERMINATORS)
        if stripped in FlextInfraUtilitiesBase._MERGE_CONFLICT_SEPARATOR_STR:
            return c.Infra.MergeConflictControl.SEPARATOR
        for token, kind in FlextInfraUtilitiesBase._MERGE_CONFLICT_PREFIX_STR:
            if line.startswith(token):
                return kind
        return None

    @staticmethod
    def ast_grep_scan_command(
        rule_path: Path,
        *,
        rule_ids: t.StrSequence = (),
        targets: t.StrSequence = (".",),
        json_stream: bool = False,
        update_all: bool = False,
    ) -> t.StrSequence:
        """Build one ast-grep scan command with explicit cwd-relative targets.

        Returns:
            The resulting ``t.StrSequence``.

        Raises:
            ValueError: If ast-grep scan targets must be nonempty and cwd-relative; or
                if ast-grep rule has no owning config; or if ast-grep rule IDs must be
                nonempty literal IDs.

        """
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
        selected_rule_ids = (
            tuple(rule_ids)
            if rule_ids
            else tuple(
                sorted(FlextInfraUtilitiesBase.ast_grep_rule_contract(rule_path)[0]),
            )
        )
        if any(not rule_id or "|" in rule_id for rule_id in selected_rule_ids):
            msg = "ast-grep rule IDs must be nonempty literal IDs"
            raise ValueError(msg)
        rule_pattern = "|".join(
            re.escape(rule_id) for rule_id in sorted(selected_rule_ids)
        )
        command = [
            c.Infra.SG,
            c.Infra.SCAN,
            c.Infra.SG_CONFIG_FLAG,
            str(config_path),
            c.Infra.SG_FILTER_FLAG,
            f"^(?:{rule_pattern})$",
        ]
        if json_stream:
            command.append("--json=stream")
        if update_all:
            command.append(c.Infra.SG_UPDATE_ALL)
        command.extend(targets)
        return tuple(command)

    @staticmethod
    def ast_grep_rule_contract(
        rule_path: Path,
    ) -> t.Pair[frozenset[str], frozenset[str]]:
        """Return every document ID and the subset carrying an automatic fix.

        Returns:
            Every document ID and the subset carrying an automatic fix.

        Raises:
            ValueError: If ast-grep rule file contains no rule documents; or if ast-grep
                rule document missing required id; or if duplicate ast-grep rule id.

        """
        rule_ids: set[str] = set()
        fixable_ids: set[str] = set()
        for raw_document in rule_path.read_text(encoding=c.DEFAULT_ENCODING).split(
            "\n---",
        ):
            if not any(
                line.strip() and not line.lstrip().startswith("#")
                for line in raw_document.splitlines()
            ):
                continue
            parsed = u.Cli.yaml_parse(raw_document).unwrap()
            rule_id = parsed.get("id")
            if not isinstance(rule_id, str) or not rule_id:
                msg = f"ast-grep rule document missing required id: {rule_path}"
                raise ValueError(msg)
            if rule_id in rule_ids:
                msg = f"duplicate ast-grep rule id {rule_id!r}: {rule_path}"
                raise ValueError(msg)
            rule_ids.add(rule_id)
            if "fix" in parsed:
                fixable_ids.add(rule_id)
        if not rule_ids:
            msg = f"ast-grep rule file contains no rule documents: {rule_path}"
            raise ValueError(msg)
        return frozenset(rule_ids), frozenset(fixable_ids)

    @staticmethod
    def classify_process_exit(exit_code: int) -> str:
        """Classify a nonzero process status as timeout, signal, or failure.

        Returns:
            The resulting ``str``.

        """
        if exit_code == c.Infra.PROCESS_TIMEOUT_EXIT_CODE:
            return "timeout"
        if exit_code < 0:
            return f"signal={-exit_code}"
        if exit_code >= c.Infra.PROCESS_SIGNAL_EXIT_OFFSET:
            return f"signal={exit_code - c.Infra.PROCESS_SIGNAL_EXIT_OFFSET}"
        return "failure"


__all__: list[str] = ["FlextInfraUtilitiesBase"]
