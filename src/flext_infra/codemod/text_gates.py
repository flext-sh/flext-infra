"""Declarative sed-by-list text rules for the ``make mod`` cascade.

Capability imported from the flext-infra ``0.20.0-dev`` line and namespaced
into this makemod cascade beside the ast-grep fixed point: every rule is one
list entry in ``config/rules/mod/sed.yaml``, one rewrite is a list-driven regex
replacement with an exact expected-count receipt, and the phase reaches a
verified rewrite fixed point before the canonical validate gate runs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import functools
import re
from bisect import bisect_right
from collections.abc import MutableMapping
from fnmatch import fnmatch
from pathlib import Path

from flext_infra import FlextInfraConfig, c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)


class FlextInfraModTextGateEngine:
    """Scan, apply, and prove the declarative sed-by-list rule cascade."""

    @classmethod
    def run(cls, root: Path, *, apply: bool) -> p.Result[t.Cli.ResultValue]:
        """Replay only text rules through their authenticated transaction.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        pending = cls.scan(root, fix=apply, validate_receipts=True)
        if pending.failure:
            return r[t.Cli.ResultValue].from_failure(pending)
        remaining = cls.scan(root, fix=False)
        if remaining.failure:
            return r[t.Cli.ResultValue].from_failure(remaining)
        if remaining.value.findings:
            return r[t.Cli.ResultValue].fail(
                f"mod-text has {remaining.value.findings} pending finding(s)",
            )
        return r[t.Cli.ResultValue].ok(
            f"mod-text: {pending.value.actionable if apply else 0} "
            "actionable finding(s) applied; fixed point verified",
        )

    @classmethod
    def load_rules(cls, root: Path) -> p.Result[t.VariadicTuple[m.Infra.ModTextRule]]:
        """Load package and workspace text rules into one validated tuple.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.ModTextRule]]``.

        """
        snapshots = cls._catalogue_states(root.absolute())
        if snapshots.failure:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].from_failure(snapshots)
        return cls._rules_from_states(snapshots.value)

    @classmethod
    def source_paths(cls, root: Path) -> p.Result[t.VariadicTuple[Path]]:
        """Return every source a text rewrite of ``root`` may publish to.

        Returns:
            The Python sources and declared Markdown globs of the elected
            cascade. Rules outside this root's distribution are not elected,
            so their Markdown includes never fail the inventory.

        """
        paths: set[Path] = set()
        for project in u.Infra.governed_project_roots(root.absolute()):
            elected = cls._elected_rules(project)
            if elected.failure:
                return r[t.VariadicTuple[Path]].from_failure(elected)
            issues = cls._include_issues(project, elected.value[2])
            if issues:
                error = ValueError(issues[0].message)
                return r[t.VariadicTuple[Path]].fail(
                    "\n".join(issue.formatted for issue in issues),
                    exception=error,
                    error_data={
                        "issues": tuple(issue.model_dump() for issue in issues)
                    },
                )
            sources = cls._source_paths(project, elected.value[2])
            if sources.failure:
                return sources
            paths.update(sources.value)
        return r[t.VariadicTuple[Path]].ok(tuple(sorted(paths)))

    @staticmethod
    def _selected_rules(
        identity: m.Cli.AtomicFileState,
        rules: t.VariadicTuple[m.Infra.ModTextRule],
    ) -> p.Result[t.VariadicTuple[m.Infra.ModTextRule]]:
        """Select rules from the exact project bytes authenticated for publication.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.ModTextRule]]``.
        """
        if identity.content is None:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].fail(
                f"text rule project identity is absent: {identity.path}",
            )
        recovered = u.Infra.recover_live_pyproject_text(
            identity.content.decode(c.DEFAULT_ENCODING),
        )
        if recovered.failure:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].from_failure(recovered)
        payload = u.Cli.toml_mapping_from_text(recovered.value)
        if payload is None:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].fail(
                f"text rule project identity is invalid TOML: {identity.path}",
            )
        validated = u.Infra.validate_infra_payload(payload)
        distribution = u.Infra.project_name_from_payload(identity.path, validated)
        return r[t.VariadicTuple[m.Infra.ModTextRule]].ok(
            tuple(
                rule
                for rule in rules
                if not rule.distributions or distribution in rule.distributions
            ),
        )

    @staticmethod
    def _catalogue_states(
        root: Path,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Capture the packaged rules and the consumer overlay exactly once.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]``.

        """
        # The packaged rules live at the same sub-path of whichever SSOT
        # config directory is active, including a declared relocation.

        provider = FlextInfraConfig.ssot_config_dir() / (
            c.Infra.CODEMOD_TEXT_RULES_RELPATH.relative_to(c.CONFIG_DIR_NAME)
        )
        consumer = root / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        snapshots: list[m.Cli.AtomicFileState] = []
        for path, required in ((provider, True), (consumer, False)):
            if snapshots and path == snapshots[0].path:
                continue
            # The consumer overlay is optional: a repository without the
            # overlay's directory declares no overlay, the same typed absence
            # as a missing file (the atomic read rejects an absent parent).
            if not required and not path.parent.is_dir():
                continue
            snapshot = u.Cli.atomic_read_binary_file_state(path, required=required)
            if snapshot.failure:
                return r[t.VariadicTuple[m.Cli.AtomicFileState]].from_failure(snapshot)
            snapshots.append(snapshot.value)
        return r[t.VariadicTuple[m.Cli.AtomicFileState]].ok(tuple(snapshots))

    @classmethod
    def _rules_from_states(
        cls,
        snapshots: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.ModTextRule]]:
        """Compose provider rules before local rules and reject ambiguous ids.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.ModTextRule]]``.

        """
        rules: list[m.Infra.ModTextRule] = []
        owners: t.MutableMappingKV[str, Path] = {}
        for snapshot in snapshots:
            parsed = cls._rules_from_state(snapshot)
            if parsed.failure:
                return r[t.VariadicTuple[m.Infra.ModTextRule]].from_failure(parsed)
            for rule in parsed.value:
                previous = owners.get(rule.rule_id)
                if previous is not None:
                    return r[t.VariadicTuple[m.Infra.ModTextRule]].fail(
                        f"duplicate text rule id {rule.rule_id} in "
                        f"{previous} and {snapshot.path}",
                    )
                owners[rule.rule_id] = snapshot.path
                rules.append(rule)
        return r[t.VariadicTuple[m.Infra.ModTextRule]].ok(tuple(rules))

    @classmethod
    def _rules_from_state(
        cls,
        snapshot: m.Cli.AtomicFileState,
    ) -> p.Result[t.VariadicTuple[m.Infra.ModTextRule]]:
        """Parse only the exact authenticated catalogue bytes used by the plan.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.ModTextRule]]``.

        """
        if snapshot.content is None:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].ok(())
        source = snapshot.path
        rules: list[m.Infra.ModTextRule] = []
        seen: set[str] = set()
        parsed = u.Cli.yaml_parse(snapshot.content.decode(c.DEFAULT_ENCODING))
        if parsed.failure:
            return r[t.VariadicTuple[m.Infra.ModTextRule]].from_failure(parsed)
        listing = parsed.value.get(c.Infra.CODEMOD_TEXT_RULES_KEY)
        if not isinstance(listing, list):
            return r[t.VariadicTuple[m.Infra.ModTextRule]].fail(
                f"text rule file declares no rules list: {source}",
            )
        for raw in listing:
            rule = cls._build_rule(raw, source)
            if rule.failure:
                return r[t.VariadicTuple[m.Infra.ModTextRule]].from_failure(rule)
            if rule.value.rule_id in seen:
                return r[t.VariadicTuple[m.Infra.ModTextRule]].fail(
                    f"duplicate text rule id {rule.value.rule_id} in {source}",
                )
            seen.add(rule.value.rule_id)
            rules.append(rule.value)
        return r[t.VariadicTuple[m.Infra.ModTextRule]].ok(tuple(rules))

    @staticmethod
    def _validated_entry(
        raw: t.JsonValue,
        source: Path,
    ) -> p.Result[t.MappingKV[str, t.JsonValue]]:
        """Require one catalogue entry to be a mapping with only known keys.

        Returns:
            The resulting ``p.Result[t.MappingKV[str, t.JsonValue]]``.

        """
        if not isinstance(raw, dict):
            return r[t.MappingKV[str, t.JsonValue]].fail(
                f"text rule entry must be a mapping in {source}: {raw!r}",
            )
        unknown = set(raw).difference((
            c.Infra.CODEMOD_TEXT_KEY_ID,
            c.Infra.CODEMOD_TEXT_KEY_DESCRIPTION,
            c.Infra.CODEMOD_TEXT_KEY_INCLUDE,
            c.Infra.CODEMOD_TEXT_KEY_EXCLUDE,
            c.Infra.CODEMOD_TEXT_KEY_FIND,
            c.Infra.CODEMOD_TEXT_KEY_REPLACE,
            c.Infra.CODEMOD_TEXT_KEY_FLAGS,
            c.Infra.CODEMOD_TEXT_KEY_EXPECTED,
            c.Infra.CODEMOD_TEXT_KEY_CAPTURE_EQUALS,
            c.Infra.CODEMOD_TEXT_KEY_DISTRIBUTIONS,
        ))
        if unknown:
            return r[t.MappingKV[str, t.JsonValue]].fail(
                f"unknown text rule keys {sorted(unknown)} in {source}",
            )
        return r[t.MappingKV[str, t.JsonValue]].ok(raw)

    @staticmethod
    def _entry_sequence(
        entry: t.MappingKV[str, t.JsonValue],
        key: str,
    ) -> tuple[t.JsonValue, ...]:
        """Read one entry field as a JSON sequence under bare iteration semantics.

        Returns:
            The declared sequence contents; a mapping contributes its keys and
            scalar or absent values contribute nothing.

        """
        declared = entry.get(key, ())
        if isinstance(declared, (list, tuple, str, dict)):
            return tuple(declared)
        return ()

    @staticmethod
    def _validated_pattern_fields(
        entry: t.MappingKV[str, t.JsonValue],
        source: Path,
    ) -> p.Result[tuple[str, t.VariadicTuple[str], re.Pattern[str]]]:
        """Validate the find regex and its declared flag names.

        Returns:
            The resulting validated ``(find, flags, compiled)`` pattern triple.

        """
        flag_names = tuple(
            str(flag)
            for flag in FlextInfraModTextGateEngine._entry_sequence(
                entry,
                c.Infra.CODEMOD_TEXT_KEY_FLAGS,
            )
        )
        unknown_flags = set(flag_names).difference(c.Infra.CODEMOD_TEXT_FLAG_NAMES)
        if unknown_flags:
            return r[tuple[str, t.VariadicTuple[str], re.Pattern[str]]].fail(
                f"unknown regex flag names {sorted(unknown_flags)} in {source}",
            )
        find = entry.get(c.Infra.CODEMOD_TEXT_KEY_FIND)
        if not isinstance(find, str) or not find:
            return r[tuple[str, t.VariadicTuple[str], re.Pattern[str]]].fail(
                f"text rule requires a non-empty find regex in {source}",
            )
        try:
            compiled = re.compile(find)
        except re.error as error:
            return r[tuple[str, t.VariadicTuple[str], re.Pattern[str]]].fail(
                f"invalid find regex in {source}: {error}",
            )
        return r[tuple[str, t.VariadicTuple[str], re.Pattern[str]]].ok(
            (find, flag_names, compiled),
        )

    @staticmethod
    def _validated_captures(
        entry: t.MappingKV[str, t.JsonValue],
        source: Path,
        compiled: re.Pattern[str],
    ) -> p.Result[t.MappingKV[str, str]]:
        """Validate the capture_equals map against the compiled pattern groups.

        Returns:
            The resulting ``p.Result[t.MappingKV[str, str]]``.

        """
        raw_captures = entry.get(c.Infra.CODEMOD_TEXT_KEY_CAPTURE_EQUALS, {})
        if not isinstance(raw_captures, dict):
            return FlextInfraModTextGateEngine._captures_failure(source)
        captures: t.MutableStrMapping = {}
        for name, value in raw_captures.items():
            if not isinstance(value, str):
                return FlextInfraModTextGateEngine._captures_failure(source)
            captures[name] = value
        unknown_captures = set(captures).difference(compiled.groupindex)
        if unknown_captures:
            return r[t.MappingKV[str, str]].fail(
                f"unknown regex captures {sorted(unknown_captures)} in {source}",
            )
        return r[t.MappingKV[str, str]].ok(captures)

    @staticmethod
    def _validated_selector_fields(
        entry: t.MappingKV[str, t.JsonValue],
        source: Path,
        compiled: re.Pattern[str],
    ) -> p.Result[tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]]:
        """Validate distributions, the capture map, and the expected receipt.

        Returns:
            The resulting validated ``(distributions, captures, expected)`` triple.

        """
        raw_declared = entry.get(c.Infra.CODEMOD_TEXT_KEY_DISTRIBUTIONS, ())
        declared = FlextInfraModTextGateEngine._entry_sequence(
            entry,
            c.Infra.CODEMOD_TEXT_KEY_DISTRIBUTIONS,
        )
        if not isinstance(raw_declared, (list, tuple)) or any(
            not isinstance(name, str) or not name.strip() or name != name.strip()
            for name in declared
        ):
            return FlextInfraModTextGateEngine._selector_failure(source)
        distributions = tuple(name for name in declared if isinstance(name, str))
        if len(set(distributions)) != len(distributions):
            return FlextInfraModTextGateEngine._selector_failure(source)
        captures = FlextInfraModTextGateEngine._validated_captures(
            entry,
            source,
            compiled,
        )
        if captures.failure:
            return r[
                tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]
            ].from_failure(captures)
        expected = entry.get(c.Infra.CODEMOD_TEXT_KEY_EXPECTED)
        if expected is not None and (
            not isinstance(expected, int) or isinstance(expected, bool) or expected < 0
        ):
            return r[
                tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]
            ].fail(
                f"text rule expected receipt must be non-negative in {source}",
            )
        return r[tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]].ok((
            distributions,
            captures.value,
            expected,
        ))

    @staticmethod
    def _selector_failure(
        source: Path,
    ) -> p.Result[tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]]:
        """Report invalid distribution declarations with the canonical message.

        Returns:
            The resulting failure for one invalid distributions declaration.

        """
        return r[tuple[t.VariadicTuple[str], t.MappingKV[str, str], int | None]].fail(
            f"text rule distributions must be unique non-empty names in {source}",
        )

    @staticmethod
    def _captures_failure(
        source: Path,
    ) -> p.Result[t.MappingKV[str, str]]:
        """Report invalid capture maps with the canonical message.

        Returns:
            The resulting failure for one invalid capture_equals mapping.

        """
        return r[t.MappingKV[str, str]].fail(
            f"text rule capture_equals must map captures to strings in {source}",
        )

    @staticmethod
    def _build_rule(
        raw: t.JsonValue,
        source: Path,
    ) -> p.Result[m.Infra.ModTextRule]:
        """Validate one raw list entry into a frozen text rule.

        Returns:
            The resulting ``p.Result[m.Infra.ModTextRule]``.

        """
        entry = FlextInfraModTextGateEngine._validated_entry(raw, source)
        if entry.failure:
            return r[m.Infra.ModTextRule].from_failure(entry)
        pattern = FlextInfraModTextGateEngine._validated_pattern_fields(
            entry.value,
            source,
        )
        if pattern.failure:
            return r[m.Infra.ModTextRule].from_failure(pattern)
        find, flags, compiled = pattern.value
        selector = FlextInfraModTextGateEngine._validated_selector_fields(
            entry.value,
            source,
            compiled,
        )
        if selector.failure:
            return r[m.Infra.ModTextRule].from_failure(selector)
        distributions, captures, expected = selector.value
        scopes: t.MutableMappingKV[str, t.VariadicTuple[str]] = {}
        for key in (
            c.Infra.CODEMOD_TEXT_KEY_INCLUDE,
            c.Infra.CODEMOD_TEXT_KEY_EXCLUDE,
        ):
            if key not in entry.value:
                continue
            declared = entry.value[key]
            if not isinstance(declared, (list, tuple)) or any(
                not isinstance(glob, str) or not glob.strip() for glob in declared
            ):
                return r[m.Infra.ModTextRule].fail(
                    f"text rule {key} must be a list of non-empty strings in {source}",
                )
            scopes[key] = tuple(glob for glob in declared if isinstance(glob, str))
        rule = m.Infra.ModTextRule(
            rule_id=str(entry.value.get(c.Infra.CODEMOD_TEXT_KEY_ID, "")),
            description=str(entry.value.get(c.Infra.CODEMOD_TEXT_KEY_DESCRIPTION, "")),
            distributions=distributions,
            find=find,
            replace=str(entry.value.get(c.Infra.CODEMOD_TEXT_KEY_REPLACE, "")),
            flags=flags,
            capture_equals=captures,
            expected=expected,
            **scopes,
        )
        if not rule.rule_id:
            return r[m.Infra.ModTextRule].fail(
                f"text rule requires a non-empty id in {source}",
            )
        return r[m.Infra.ModTextRule].ok(rule)

    @classmethod
    def _include_issues(
        cls,
        root: Path,
        rules: t.VariadicTuple[m.Infra.ModTextRule],
    ) -> t.VariadicTuple[m.Infra.Issue]:
        """Report declared formats outside this phase's existing source contract.

        Returns:
            Central issues for unsupported explicit input declarations. A scope
            glob without a suffix still selects the canonical Python inventory.
        """
        return tuple(
            cls._source_issue(
                root / pattern,
                f"text rule {rule.rule_id} declares an unsupported input: {pattern}",
            )
            for rule in rules
            for pattern in rule.include
            if Path(pattern).suffix
            and Path(pattern).suffix != c.Infra.EXT_PYTHON
            and Path(pattern).suffix != ".md"
        )

    @staticmethod
    def _source_paths(
        root: Path,
        rules: t.VariadicTuple[m.Infra.ModTextRule],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Inventory Python sources and only explicitly declared Markdown globs.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        paths: set[Path] = set()
        for target in u.Infra.ast_grep_scan_targets(root):
            candidate = root / target
            if candidate.is_dir():
                paths.update(candidate.rglob(f"*{c.Infra.EXT_PYTHON}"))
            else:
                paths.add(candidate)
        for rule in rules:
            for pattern in rule.include:
                declared = Path(pattern)
                if declared.suffix != ".md":
                    continue
                if declared.is_absolute() or ".." in declared.parts:
                    return r[t.VariadicTuple[Path]].fail(
                        f"text Markdown include escapes repository: {pattern}",
                    )
                matches = tuple(sorted(root.glob(pattern)))
                if not matches:
                    return r[t.VariadicTuple[Path]].fail(
                        f"text Markdown include has no source: {pattern}",
                    )
                for path in matches:
                    if (
                        not path.is_file()
                        or path.is_symlink()
                        or path.resolve() != path.absolute()
                        or path.stat().st_nlink != 1
                    ):
                        return r[t.VariadicTuple[Path]].fail(
                            f"text Markdown source must be physical: {path}",
                        )
                    paths.add(path)
        members = tuple(
            project
            for project in u.Infra.governed_project_roots(root)
            if project != root
        )
        return r[t.VariadicTuple[Path]].ok(
            tuple(
                path
                for path in sorted(paths)
                if not any(path.is_relative_to(member) for member in members)
            )
        )

    @classmethod
    def _elected_rules(
        cls,
        root: Path,
    ) -> p.Result[
        t.Triple[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Cli.AtomicFileState,
            t.VariadicTuple[m.Infra.ModTextRule],
        ]
    ]:
        """Authenticate the catalogues and the project identity, then elect rules.

        Returns:
            The resulting authenticated ``(catalogues, identity, rules)`` triple.

        """
        catalogues = cls._catalogue_states(root)
        if catalogues.failure:
            return r[
                t.Triple[
                    t.VariadicTuple[m.Cli.AtomicFileState],
                    m.Cli.AtomicFileState,
                    t.VariadicTuple[m.Infra.ModTextRule],
                ]
            ].from_failure(catalogues)
        loaded = cls._rules_from_states(catalogues.value)
        if loaded.failure:
            return r[
                t.Triple[
                    t.VariadicTuple[m.Cli.AtomicFileState],
                    m.Cli.AtomicFileState,
                    t.VariadicTuple[m.Infra.ModTextRule],
                ]
            ].from_failure(loaded)
        identity = u.Cli.atomic_read_binary_file_state(
            root / c.PYPROJECT_FILENAME,
            required=True,
        )
        if identity.failure:
            return r[
                t.Triple[
                    t.VariadicTuple[m.Cli.AtomicFileState],
                    m.Cli.AtomicFileState,
                    t.VariadicTuple[m.Infra.ModTextRule],
                ]
            ].from_failure(identity)
        selected = cls._selected_rules(identity.value, loaded.value)
        if selected.failure:
            return r[
                t.Triple[
                    t.VariadicTuple[m.Cli.AtomicFileState],
                    m.Cli.AtomicFileState,
                    t.VariadicTuple[m.Infra.ModTextRule],
                ]
            ].from_failure(selected)
        return r[
            t.Triple[
                t.VariadicTuple[m.Cli.AtomicFileState],
                m.Cli.AtomicFileState,
                t.VariadicTuple[m.Infra.ModTextRule],
            ]
        ].ok((catalogues.value, identity.value, selected.value))

    @staticmethod
    def _authenticated_source(
        root: Path,
        path: Path,
    ) -> p.Result[t.Triple[m.Cli.AtomicFileState, str, str]]:
        """Read one source's authenticated bytes with its repository-relative name.

        Returns:
            The resulting ``(state, text, relative)`` triple.

        """
        relative = path.relative_to(root).as_posix()
        captured = u.Cli.atomic_read_binary_file_state(path, required=True)
        if captured.failure:
            return r[t.Triple[m.Cli.AtomicFileState, str, str]].from_failure(captured)
        before = captured.value
        if before.content is None:
            return r[t.Triple[m.Cli.AtomicFileState, str, str]].fail(
                f"text source disappeared during inventory: {path}",
            )
        return r[t.Triple[m.Cli.AtomicFileState, str, str]].ok((
            before,
            before.content.decode(c.DEFAULT_ENCODING),
            relative,
        ))

    @staticmethod
    def _rewrite_plan(
        root: Path,
        path: Path,
        before: m.Cli.AtomicFileState,
        updated: str,
        base_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> m.Infra.CodegenFilePlan:
        """Build one authenticated publication plan for a rewritten source.

        Returns:
            The resulting ``m.Infra.CodegenFilePlan``.

        """
        return m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=before,
            desired_content=updated.encode(c.DEFAULT_ENCODING),
            desired_mode=before.mode,
            source_states=(*base_states, before),
            owner="mod-text",
        )

    @classmethod
    def _scan_paths(
        cls,
        root: Path,
        sources: t.SequenceOf[Path],
        rules: t.VariadicTuple[m.Infra.ModTextRule],
        base_states: t.VariadicTuple[m.Cli.AtomicFileState],
        *,
        fix: bool,
    ) -> p.Result[
        t.Pair[
            m.Infra.ModTextReport,
            m.Infra.CodegenPhaseAnalysis,
        ]
    ]:
        """Plan each source, preserving failures beside independent valid targets.

        Returns:
            Reported matches and the canonical phase analysis with its first cause.

        """
        entries: list[m.Infra.ModTextFinding] = []
        files: set[Path] = set()
        actionable = 0
        plans: list[m.Infra.CodegenFilePlan] = []
        issues: list[m.Infra.Issue] = []
        first_exception: BaseException | None = None
        for path in sources:
            try:
                prepared = cls._authenticated_source(root, path)
            except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
                first_exception = first_exception or exc
                issues.append(cls._source_issue(path, str(exc), exception=exc))
                continue
            if prepared.failure:
                issues.append(cls._source_issue(path, str(prepared.error)))
                first_exception = first_exception or prepared.exception
                continue
            before, source, relative = prepared.value
            try:
                updated, target_entries, target_actionable = cls._rewrite_source(
                    source, relative, rules
                )
            except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
                first_exception = first_exception or exc
                issues.append(cls._source_issue(path, str(exc), exception=exc))
                continue
            entries.extend(target_entries)
            actionable += target_actionable
            if target_entries:
                files.add(Path(relative))
            if updated != source and source.startswith(c.Infra.AUTOGEN_HEADERS):
                issues.append(
                    cls._source_issue(
                        path,
                        "generated findings require canonical generator repair",
                    )
                )
                continue
            if updated != source and path.suffix == c.Infra.EXT_PYTHON:
                try:
                    ast.parse(updated, filename=str(path))
                except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
                    first_exception = first_exception or exc
                    issues.append(cls._source_issue(path, str(exc), exception=exc))
                    continue
            if fix and updated != source:
                plans.append(
                    cls._rewrite_plan(root, path, before, updated, base_states),
                )
        report = m.Infra.ModTextReport(
            findings=len(entries),
            actionable=actionable,
            files=frozenset(files),
            entries=tuple(entries),
        )
        return r[
            t.Pair[
                m.Infra.ModTextReport,
                m.Infra.CodegenPhaseAnalysis,
            ]
        ].ok((
            report,
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.MOD_TEXT,
                files=tuple(plans),
                inputs=tuple(
                    {
                        state.path: state
                        for plan in plans
                        for state in plan.source_states
                    }.values()
                ),
                issues=tuple(issues),
                exception=first_exception,
            ),
        ))

    @staticmethod
    def _source_issue(
        path: Path, message: str, *, exception: BaseException | None = None
    ) -> m.Infra.Issue:
        """Use the canonical issue contract for one actual source failure.

        Args:
            path: The path to the source file that caused the failure.
            message: A human-readable message describing the failure.
            exception: The exception instance that triggered the failure, if any.

        Returns:
            An instance of `m.Infra.Issue` representing the source failure.

        """
        return m.Infra.Issue(
            file=str(path),
            line=exception.lineno or 0 if isinstance(exception, SyntaxError) else 0,
            column=exception.offset or 0 if isinstance(exception, SyntaxError) else 0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=message,
        )

    @classmethod
    def scan(
        cls,
        root: Path,
        *,
        fix: bool,
        validate_receipts: bool = False,
    ) -> p.Result[m.Infra.ModTextReport]:
        """Scan the governed surface or apply every rule rewrite in place.

        Returns:
            The resulting ``p.Result[m.Infra.ModTextReport]``.

        """
        root = root.absolute()
        entries: list[m.Infra.ModTextFinding] = []
        files: set[Path] = set()
        plans: list[m.Infra.CodegenFilePlan] = []
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        conflicting_dependencies: set[Path] = set()
        issues: list[m.Infra.Issue] = []
        first_exception: BaseException | None = None
        actionable = 0
        for project in u.Infra.governed_project_roots(root):
            try:
                outcome = cls._scan_project(
                    project,
                    fix=fix,
                    validate_receipts=validate_receipts,
                )
            except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
                issues.append(cls._source_issue(project, str(exc), exception=exc))
                first_exception = first_exception or exc
                continue
            if outcome.failure:
                issues.append(cls._source_issue(project, str(outcome.error)))
                first_exception = first_exception or outcome.exception
                continue
            report, analysis = outcome.value
            issues.extend(analysis.issues)
            first_exception = first_exception or analysis.exception
            prefix = project.relative_to(root)
            entries.extend(
                entry.model_copy(update={"file": prefix / entry.file})
                for entry in report.entries
            )
            files.update(prefix / path for path in report.files)
            plans.extend(analysis.files)
            actionable += report.actionable
            conflicting_dependencies.update(cls._conflicting_inputs(analysis, inputs))
        if conflicting_dependencies:
            plans = cls._without_conflicting_plans(
                plans, conflicting_dependencies, issues
            )
            inputs = {
                state.path: state for plan in plans for state in plan.source_states
            }
        report = m.Infra.ModTextReport(
            findings=len(entries),
            actionable=actionable,
            files=frozenset(files),
            entries=tuple(entries),
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.MOD_TEXT,
            files=tuple(plans),
            inputs=tuple(inputs.values()),
            issues=tuple(issues),
            exception=first_exception,
        )
        if fix and plans:
            published = cls._publish(root, analysis)
            if published.failure:
                details: t.MutableMappingKV[str, t.JsonValue] = {
                    "report": u.Cli.normalize_json_value(report.model_dump(mode="json"))
                }
                if published.error_data is not None:
                    details.update(published.error_data)
                return r[m.Infra.ModTextReport].fail(
                    str(published.error),
                    exception=published.exception,
                    error_code=published.error_code,
                    error_data=details,
                )
        if issues:
            return r[m.Infra.ModTextReport].fail(
                "\n".join(issue.formatted for issue in issues),
                exception=first_exception,
                error_code=c.Infra.ToolOutcome.ERROR.value,
                error_data={
                    "report": report.model_dump(mode="json"),
                    "issues": tuple(issue.model_dump() for issue in issues),
                    "written_files": (),
                },
            )
        return r[m.Infra.ModTextReport].ok(report)

    @staticmethod
    def _conflicting_inputs(
        analysis: m.Infra.CodegenPhaseAnalysis,
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> set[Path]:
        """Register publication inputs and identify inconsistent snapshots.

        Returns:
            Dependency paths with conflicting authenticated identities.
        """
        return {
            state.path
            for state in analysis.inputs
            if analysis.files
            if inputs.setdefault(state.path, state) != state
        }

    @classmethod
    def _without_conflicting_plans(
        cls,
        plans: list[m.Infra.CodegenFilePlan],
        conflicting_dependencies: set[Path],
        issues: list[m.Infra.Issue],
    ) -> list[m.Infra.CodegenFilePlan]:
        """Reject plans whose authenticated dependencies changed during scanning.

        Returns:
            Plans with consistent dependency identities.
        """
        allowed: list[m.Infra.CodegenFilePlan] = []
        for plan in plans:
            dependencies = tuple(
                str(state.path)
                for state in plan.source_states
                if state.path in conflicting_dependencies
            )
            if dependencies:
                issues.append(
                    cls._source_issue(
                        plan.path,
                        "text dependency identity changed during planning: "
                        f"{dependencies}",
                    )
                )
            else:
                allowed.append(plan)
        return allowed

    @classmethod
    def _scan_project(
        cls,
        root: Path,
        *,
        fix: bool,
        validate_receipts: bool,
    ) -> p.Result[
        t.Pair[
            m.Infra.ModTextReport,
            m.Infra.CodegenPhaseAnalysis,
        ]
    ]:
        """Plan one member's rules using its authenticated distribution identity.

        Returns:
            Reported matches and the authenticated phase analysis without effects.

        """
        context = cls._elected_rules(root)
        if context.failure:
            return r[
                t.Pair[
                    m.Infra.ModTextReport,
                    m.Infra.CodegenPhaseAnalysis,
                ]
            ].from_failure(context)
        catalogues, identity, rules = context.value
        include_issues = cls._include_issues(root, rules)
        sources = cls._source_paths(root, rules)
        if sources.failure:
            return r[
                t.Pair[
                    m.Infra.ModTextReport,
                    m.Infra.CodegenPhaseAnalysis,
                ]
            ].from_failure(sources)
        scanned = cls._scan_paths(
            root,
            sources.value,
            rules,
            (*catalogues, identity),
            fix=fix,
        )
        if scanned.failure:
            return scanned
        report, analysis = scanned.value
        if include_issues:
            analysis = analysis.model_copy(
                update={
                    "issues": (*include_issues, *analysis.issues),
                    "exception": ValueError(include_issues[0].message),
                }
            )
            scanned = r[t.Pair[m.Infra.ModTextReport, m.Infra.CodegenPhaseAnalysis]].ok((
                report,
                analysis,
            ))
        if validate_receipts:
            failed_rules: set[str] = set()
            receipt_issues: list[m.Infra.Issue] = []
            first_exception = analysis.exception
            for rule in rules:
                try:
                    cls._validate_expected_receipts((rule,), report)
                except RuntimeError as exc:
                    failed_rules.add(rule.rule_id)
                    receipt_issues.append(cls._source_issue(root, str(exc)))
                    first_exception = first_exception or exc
            if receipt_issues:
                blocked = {
                    root / entry.file
                    for entry in report.entries
                    if entry.rule_id in failed_rules
                }
                allowed = tuple(
                    plan for plan in analysis.files if plan.path not in blocked
                )
                analysis = analysis.model_copy(
                    update={
                        "files": allowed,
                        "inputs": tuple(
                            {
                                state.path: state
                                for plan in allowed
                                for state in plan.source_states
                            }.values()
                        ),
                        "issues": (*analysis.issues, *receipt_issues),
                        "exception": first_exception,
                    }
                )
                return r[
                    t.Pair[m.Infra.ModTextReport, m.Infra.CodegenPhaseAnalysis]
                ].ok((report, analysis))
        return scanned

    @classmethod
    def _publish(
        cls,
        root: Path,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish owned targets and their declared dependencies through the journal.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {
            f"@mod-text-{index}": project
            for index, project in enumerate(
                sorted({plan.project for plan in analysis.files})
            )
        }

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            published = transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            )
            if published.failure:
                return r[t.VariadicTuple[Path]].from_failure(published)
            verified = transaction.validate_phase_analysis_locked(analysis)
            if verified.failure:
                return r[t.VariadicTuple[Path]].from_failure(verified)
            return published

        return transaction.run_files_locked(roots, publish)

    @staticmethod
    def _validate_expected_receipts(
        rules: t.VariadicTuple[m.Infra.ModTextRule],
        report: m.Infra.ModTextReport,
    ) -> None:
        """Require exact migration preconditions, including zero-match mismatches.

        A positive expected count is a one-invocation precondition, not an
        idempotence promise after that migration has consumed its matches.

        Raises:
            RuntimeError: If text rule.

        """
        counts: MutableMapping[str, int] = {}
        for entry in report.entries:
            counts[entry.rule_id] = counts.get(entry.rule_id, 0) + 1
        for rule in rules:
            if rule.expected is not None and counts.get(rule.rule_id, 0) != (
                rule.expected
            ):
                msg = (
                    f"text rule {rule.rule_id} expected {rule.expected} finding(s), "
                    f"scan produced {counts.get(rule.rule_id, 0)}"
                )
                raise RuntimeError(msg)

    @classmethod
    def _rewrite_source(
        cls,
        source: str,
        target: str,
        rules: t.VariadicTuple[m.Infra.ModTextRule],
    ) -> t.Triple[str, list[m.Infra.ModTextFinding], int]:
        """Rewrite one source text through every elected rule entry.

        Returns:
            The resulting ``t.Triple[str, list[m.Infra.ModTextFinding], int]``.

        """
        updated = source
        entries: list[m.Infra.ModTextFinding] = []
        actionable = 0
        for rule in rules:
            if not cls._rule_elects(rule, target):
                continue
            line_starts = [0]
            for line in updated.splitlines(keepends=True):
                line_starts.append(line_starts[-1] + len(line))
            found: list[m.Infra.ModTextFinding] = []
            pattern = cls._compiled(rule)
            expand = functools.partial(
                cls._expand_match,
                rule,
                target,
                line_starts,
                found,
            )
            candidate = pattern.sub(expand, updated)
            if found:
                updated = candidate
                actionable += sum(
                    1 for entry in found if entry.text != entry.replacement
                )
                entries.extend(found)
        return (updated, entries, actionable)

    @staticmethod
    def _expand_match(
        rule: m.Infra.ModTextRule,
        target: str,
        line_starts: t.SequenceOf[int],
        found: list[m.Infra.ModTextFinding],
        match: re.Match[str],
    ) -> str:
        """Record and expand one match, binding every loop value explicitly.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If text rule.

        """
        for name, expected in rule.capture_equals.items():
            actual = match.group(name)
            if actual != expected:
                msg = (
                    f"text rule {rule.rule_id} capture {name} expected "
                    f"{expected!r}, matched {actual!r} in {target}"
                )
                raise ValueError(msg)
        replacement = match.expand(rule.replace)
        line_index = bisect_right(line_starts, match.start()) - 1
        found.append(
            m.Infra.ModTextFinding(
                rule_id=rule.rule_id,
                file=Path(target),
                line=line_index + 1,
                text=match.group(0),
                replacement=replacement,
            ),
        )
        return replacement

    @staticmethod
    def _rule_elects(rule: m.Infra.ModTextRule, target: str) -> bool:
        """Return whether one target path is elected by the rule globs.

        Returns:
            Whether one target path is elected by the rule globs.

        """
        if rule.exclude and any(fnmatch(target, glob) for glob in rule.exclude):
            return False
        return not (
            rule.include and not any(fnmatch(target, glob) for glob in rule.include)
        )

    @staticmethod
    def _compiled(rule: m.Infra.ModTextRule) -> re.Pattern[str]:
        """Compile one rule pattern with its declared SSOT flag names.

        Returns:
            The resulting ``re.Pattern[str]``.

        """
        flags = 0
        for name in rule.flags:
            flags |= c.Infra.CODEMOD_TEXT_FLAG_NAMES[name]
        return re.compile(rule.find, flags)


__all__: list[str] = ["FlextInfraModTextGateEngine"]
