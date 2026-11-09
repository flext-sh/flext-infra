"""Lint snapshot support for protected edit workflows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import concurrent.futures
import difflib
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, MutableMapping, MutableSequence, Sequence
from itertools import islice
from pathlib import Path
from typing import ClassVar

from flext_cli import u

from flext_infra import c, codegen, config, gates, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesProcess,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesResourceLimits,
)
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitMutationScope,
    FlextInfraUtilitiesGitSemanticPaths,
    FlextInfraUtilitiesGitStateCheckpoint,
)
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeModules


class FlextInfraUtilitiesProtectedEditLinting:
    """Shared linting and path helpers for protected edit workflows."""

    @classmethod
    def normalize_source(
        cls,
        repository_root: Path,
        path: Path,
        source: str,
        *,
        before_source: str | None = None,
        settings: tuple[Sequence[str], int | None] = ((), None),
    ) -> p.Result[str]:
        """Normalize only what a rewrite changed, then format the candidate.

        A rewrite of existing bytes repairs exactly the Ruff rules its edit
        introduced (codes absent from ``before_source``), so no unchanged
        binding or pre-existing finding is touched; a whole new file receives
        the declared full repair. Formatting follows the same law: a
        generated projection (``c.Infra.AUTOGEN_HEADER``) is always formatted,
        but an authored module with existing format debt receives only native
        range formatting of changed lines. Ruff owns logical-line expansion;
        untouched authored format debt remains for ``make fmt``.
        ``settings`` carry the staged pyproject's Ruff table when the same
        plan set rewrites it.

        Returns:
            Normalized source, or the original configured repair failure.

        Raises:
            SyntaxError: If the candidate is not parseable Python; a broken
                candidate is a caller defect, not a repair condition.

        """
        arguments, line_limit = settings
        try:
            FlextInfraUtilitiesRopeRuntimeModules.build_string_module(None, source)
        except Exception as syntax_error:  # ruff: ignore[blind-except] - convert any rope parse failure to SyntaxError
            raise SyntaxError(str(syntax_error)) from None
        if before_source is None:
            normalized = cls.normalize_python_text(path, source, settings=arguments)
        else:
            normalized = cls._normalize_edited_source(
                path, source, before_source, settings=arguments
            )
        if normalized.failure:
            return normalized
        # A protected edit never publishes bytes the destination's own format
        # policy rejects: the declared width recipe and formatter must satisfy
        # an introduced E501, or the live source stays untouched. An E501 already
        # in authored bytes, like every finding the repair set does not own,
        # belongs to ``make check``.
        diagnostics: list[tuple[str, int, str]] = []
        remaining = cls._ruff_stdin_codes(
            path, normalized.value, settings=arguments, diagnostics=diagnostics
        )
        if remaining.failure:
            return r[str].from_failure(remaining)
        width = c.Infra.FORMATTER_UNSATISFIED_CODE
        inherited: frozenset[str] = frozenset()
        if before_source is not None:
            before = cls._ruff_stdin_codes(path, before_source, settings=arguments)
            if before.failure:
                return r[str].from_failure(before)
            inherited = before.value
        if width in remaining.value and width not in inherited:
            original = f"ruff check failed for {path}: {width}\n" + "\n".join(
                detail for _name, _row, detail in diagnostics
            )
            tooling = (
                FlextInfraUtilitiesProjectManagedArtifacts
                .load_tooling_inputs(repository_root)
                .unwrap()
                .document
            )
            rows = [
                row
                for name, row, _detail in diagnostics
                if tooling.tools.ruff.lint.fix_recipes.get(name)
                is c.Infra.LintFixRecipe.WRAP_LONG_LINE
            ]
            if not rows or (arguments and line_limit is None):
                return r[str].fail(original)
            limit = (
                line_limit
                if line_limit is not None
                else FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
                    tooling, "ruff", "line-length", int
                )
            )
            repaired = FlextInfraUtilitiesLintRecipes.wrap_long_lines(
                normalized.value, rows, limit=limit
            )
            formatted = (
                cls._ruff_stdin_pass(
                    path,
                    repaired,
                    (c.Infra.FORMAT, *config.Infra.codegen.make.ruff.format_apply),
                    settings=arguments,
                )
                if before_source is None
                else cls._format_rewrite(
                    path, (before_source, repaired), settings=arguments
                )
            )
            return formatted.flat_map(
                lambda formatted: cls._checked_width_repair(
                    path, formatted, original, settings=arguments
                )
            )
        return normalized

    @classmethod
    def _checked_width_repair(
        cls,
        path: Path,
        source: str,
        original: str,
        *,
        settings: Sequence[str],
    ) -> p.Result[str]:
        """Keep the original width failure unless the native final guard passes.

        Returns:
            Repaired source or the unchanged original failure.

        """
        return cls._ruff_stdin_codes(path, source, settings=settings).flat_map(
            lambda codes: (
                r[str].fail(original)
                if c.Infra.FORMATTER_UNSATISFIED_CODE in codes
                else r[str].ok(source)
            )
        )

    @classmethod
    def _normalize_edited_source(
        cls,
        path: Path,
        source: str,
        before_source: str,
        *,
        settings: Sequence[str] = (),
    ) -> p.Result[str]:
        """Repair only the findings the edit introduced, then format.

        Returns:
            The repaired and formatted source, or the repair failure.

        """
        source = cls.remove_orphaned_text_imports(before_source, source)
        before_codes = cls._ruff_stdin_codes(path, before_source, settings=settings)
        if before_codes.failure:
            return r[str].from_failure(before_codes)
        after_codes = cls._ruff_stdin_codes(path, source, settings=settings)
        if after_codes.failure:
            return r[str].from_failure(after_codes)
        introduced = sorted(after_codes.value - before_codes.value)
        if introduced:
            repaired = cls.ruff_select_fix(path, source, introduced, settings=settings)
            if repaired.failure:
                return repaired
            source = repaired.value
        return cls._format_rewrite(path, (before_source, source), settings=settings)

    @classmethod
    def _format_rewrite(
        cls,
        path: Path,
        rewrite: tuple[str, str],
        *,
        settings: Sequence[str],
    ) -> p.Result[str]:
        """Format a rewrite of existing bytes without touching authored debt.

        ``rewrite`` pairs the existing bytes with the repaired candidate. A
        generated projection (``c.Infra.AUTOGEN_HEADER``) is formatted in
        full. An already formatter-clean authored module also receives the
        full native pass. Otherwise stdlib diff ranges select only changed
        candidate lines, and Ruff owns their logical-statement expansion.

        Returns:
            The candidate, formatted when the law allows, or Ruff's failure.

        """
        before_source, source = rewrite
        arguments = (c.Infra.FORMAT, *config.Infra.codegen.make.ruff.format_apply)
        if source.startswith(c.Infra.AUTOGEN_HEADER):
            return cls._ruff_stdin_pass(path, source, arguments, settings=settings)
        formatted = cls._ruff_stdin_pass(
            path, before_source, arguments, settings=settings
        )
        if formatted.failure:
            return formatted
        if formatted.value == before_source:
            return cls._ruff_stdin_pass(path, source, arguments, settings=settings)
        changes = difflib.SequenceMatcher(
            a=before_source.splitlines(keepends=True),
            b=source.splitlines(keepends=True),
            autojunk=False,
        ).get_opcodes()
        pending = [
            (start, end)
            for operation, _before_start, _before_end, start, end in changes
            if operation != "equal" and start < end
        ]
        while pending:
            start, end = pending.pop()
            formatted = cls._ruff_stdin_pass(
                path,
                source,
                (*arguments, "--range", f"{start + 1}-{end + 1}"),
                settings=settings,
            )
            if formatted.failure:
                return formatted
            changes = difflib.SequenceMatcher(
                a=source.splitlines(keepends=True),
                b=formatted.value.splitlines(keepends=True),
                autojunk=False,
            ).get_opcodes()
            # Ruff may expand or contract the enclosing logical statement.
            remapped: list[tuple[int, int]] = []
            for pending_start, pending_end in pending:
                for operation, left, right, new_start, _new_end in changes:
                    if operation != "equal":
                        continue
                    lower, upper = max(pending_start, left), min(pending_end, right)
                    if lower < upper:
                        remapped.append((
                            new_start + lower - left,
                            new_start + upper - left,
                        ))
            pending = remapped
            source = formatted.value
        return r[str].ok(source)

    @classmethod
    def normalized_codegen_changes(
        cls,
        plans: Sequence[p.Infra.CodegenFilePlan],
    ) -> p.Result[tuple[p.Cli.FileChange, ...]]:
        """Normalize Python destinations once; pass every other plan through.

        Check and publication share this view, so they never disagree. A plan
        over existing bytes repairs only the findings its change introduced
        (``normalize_source``); a new file receives the declared full repair.

        Returns:
            The file changes with normalized Python bytes, or the first failure.

        """
        result_type = r[tuple[p.Cli.FileChange, ...]]
        staged_limits: dict[Path, int] = {}
        staged_settings = cls._staged_ruff_settings(plans, line_limits=staged_limits)
        # A plan that keeps its bytes changed nothing, so it has nothing to
        # normalize; only rewritten or new sources go through ruff. Each file's
        # normalization is independent, so they run concurrently.
        pending = [
            plan
            for plan in plans
            if plan.path.suffix == c.Infra.EXT_PYTHON
            and plan.desired_content is not None
            and plan.desired_mode is not None
            and plan.desired_content != plan.before.content
        ]
        retired = {plan.path: plan for plan in plans if plan.desired_content is None}
        before_sources: dict[Path, str | None] = {}
        for plan in pending:
            original = plan.before
            if plan.move_source is not None:
                source = retired.get(plan.move_source)
                if (
                    source is None
                    or source.project != plan.project
                    or source.before.content is None
                    or source.before.mode is None
                    or source.before not in plan.inputs
                ):
                    return result_type.fail(
                        "native move requires its captured paired source retirement: "
                        f"{plan.move_source} -> {plan.path}"
                    )
                original = source.before
            before_sources[plan.path] = (
                None
                if original.content is None
                else original.content.decode(c.DEFAULT_ENCODING)
            )
        normalized: dict[Path, str] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=config.Infra.codegen.lint_snapshot_workers
        ) as pool:
            futures = {
                pool.submit(
                    cls.normalize_source,
                    plan.project,
                    plan.path,
                    (plan.desired_content or b"").decode(c.DEFAULT_ENCODING),
                    before_source=before_sources[plan.path],
                    settings=(
                        staged_settings.get(plan.project, ()),
                        staged_limits.get(plan.project),
                    ),
                ): plan.path
                for plan in pending
            }
            for future in concurrent.futures.as_completed(futures):
                outcome = future.result()
                if outcome.failure:
                    pool.shutdown(wait=False, cancel_futures=True)
                    return result_type.from_failure(outcome)
                normalized[futures[future]] = outcome.value
        return result_type.ok(
            tuple(
                m.Cli.FileChange(
                    path=plan.path,
                    before=plan.before,
                    desired_content=normalized[plan.path].encode(c.DEFAULT_ENCODING),
                    desired_mode=plan.desired_mode,
                )
                if plan.path in normalized
                else plan
                for plan in plans
            )
        )

    @classmethod
    def publish_codegen_plans(
        cls,
        root: Path,
        plans: Sequence[p.Infra.CodegenFilePlan],
    ) -> p.Result[tuple[Path, ...]]:
        """Publish generated plans through the shared file-change publisher.

        Every plan's target must physically live inside its declared project
        and that project must be FLEXT-writable for ``root`` before any effect;
        the containment owner raises otherwise. Python is normalized first;
        runtime-local index entries are retired and the cached project
        document is invalidated after its file changes.

        Returns:
            The written or deleted paths, or the first failure.

        """
        return cls.normalized_codegen_changes(plans).flat_map(
            lambda changes: cls.publish_normalized_codegen_plans(root, plans, changes)
        )

    @classmethod
    def publish_normalized_codegen_plans(
        cls,
        root: Path,
        plans: Sequence[p.Infra.CodegenFilePlan],
        changes: Sequence[p.Cli.FileChange],
    ) -> p.Result[tuple[Path, ...]]:
        """Publish plans whose Python bytes the caller already normalized.

        Generation normalizes once, when it admits the candidate; publishing
        the admitted bytes must not run the formatters a second time.
        All source observations and destinations are verified under the same
        publication lock before any effect, including unchanged carriers.

        Returns:
            The written or deleted paths, or the first failure.

        """
        result_type = r[tuple[Path, ...]]
        grouped: MutableMapping[Path, list[Path]] = {}
        for plan in plans:
            grouped.setdefault(plan.project, []).append(plan.path)
        for project, targets in grouped.items():
            FlextInfraUtilitiesProjectManagedArtifacts.contained_write_targets(
                project, targets, authority=root
            )
        lock = FlextInfraUtilitiesGitMutationScope.mutation_lock_path(root)
        if lock.failure:
            return result_type.from_failure(lock)
        owners = tuple(dict.fromkeys((root, *(plan.project for plan in plans))))
        with (
            FlextInfraUtilitiesGitStateCheckpoint.state_leases(owners),
            u.Cli.file_changes_lock(lock.value),
        ):
            verified = u.Cli.atomic_verify_binary_file_states(
                tuple(state for plan in plans for state in (plan.before, *plan.inputs))
            )
            if verified.failure:
                return result_type.from_failure(verified)
            published = u.Cli.publish_file_changes(
                changes,
                lock_path=lock.value,
                directory_mode=config.Infra.codegen.modes.directory_generated,
                nonsecret_source_paths=tuple(
                    plan.path
                    for plan in plans
                    if plan.path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
                ),
            )
            if published.failure:
                return published
            completed = cls._retire_published_index_entries(plans).flat_map(
                lambda _: cls._prune_emptied_directories(
                    lock.value, plans, published.value
                )
            )
            if completed.failure:
                return result_type.fail(
                    completed.error or "publication finalization failed",
                    error_code=completed.error_code,
                    error_data={
                        **(completed.error_data or {}),
                        "written_files": [str(path) for path in published.value],
                    },
                    exception=completed.exception,
                )
            if any(path.name == c.PYPROJECT_FILENAME for path in published.value):
                u.read_project_document_cached.cache_clear()
            return published

    @classmethod
    def _retire_published_index_entries(
        cls,
        plans: Sequence[p.Infra.CodegenFilePlan],
    ) -> p.Result[bool]:
        """Retire runtime-local index entries replaced by published plans.

        Returns:
            True when every replaced entry retired, or the first failure.

        """
        for plan in plans:
            if plan.index_before is None:
                continue
            retired = FlextInfraUtilitiesGitSemanticPaths.git_retire_index_file(
                m.Infra.GitIndexRetirementRequest.model_validate({
                    "repo_root": (plan.project),
                    "entry": (plan.index_before),
                }),
            )
            if retired.failure:
                return r[bool].from_failure(retired)
        return r[bool].ok(value=True)

    @staticmethod
    def _prune_emptied_directories(
        lock_path: Path,
        plans: Sequence[p.Infra.CodegenFilePlan],
        published: tuple[Path, ...],
    ) -> p.Result[bool]:
        """Remove the directories a published deletion left empty.

        Publication creates the missing parents of a written projection; a
        deleted projection symmetrically removes each parent it emptied, under
        the same lock, stopping at the first non-empty directory and never at
        or above the owning project.

        Returns:
            True once every emptied parent is removed, or the first failure.

        """
        deleted = frozenset(published)
        with u.Cli.file_changes_lock(lock_path):
            for plan in plans:
                if plan.desired_content is not None or plan.path not in deleted:
                    continue
                for directory in plan.path.parents:
                    if (
                        directory == plan.project
                        or not directory.is_relative_to(plan.project)
                        or not directory.is_dir()
                        or any(directory.iterdir())
                    ):
                        break
                    directory_state = u.Cli.atomic_read_empty_directory_state(
                        directory, required=True
                    )
                    if directory_state.failure:
                        return r[bool].from_failure(directory_state)
                    removed = u.Cli.atomic_delete_empty_directory_guarded(
                        directory_state.value
                    )
                    if removed.failure:
                        return removed
        return r[bool].ok(value=True)

    @classmethod
    def normalize_python_text(
        cls, path: Path, source: str, *, settings: Sequence[str] = ()
    ) -> p.Result[str]:
        """Repair then format one Python candidate through Ruff on stdin.

        ``path`` is the destination; it selects the owning project's Ruff
        configuration, overridden by ``settings`` when the same plan set stages
        that project's pyproject. The flags are the declared ``make.ruff``
        repair and format surfaces; remaining findings never break repair
        (``make check`` enforces them), only a Ruff error does.

        Returns:
            The repaired and formatted source, or Ruff's native failure.

        """
        declared = config.Infra.codegen.make.ruff
        return (
            cls
            ._ruff_stdin_pass(
                path, source, (c.Infra.CHECK, *declared.lint_fix), settings=settings
            )
            .flat_map(
                lambda repaired: cls._ruff_stdin_pass(
                    path,
                    repaired,
                    (c.Infra.FORMAT, *declared.format_apply),
                    settings=settings,
                )
            )
            .flat_map(
                lambda formatted: cls._wrap_long_annotations(
                    path, formatted, settings=settings
                )
            )
        )

    @classmethod
    def _wrap_long_annotations(
        cls, path: Path, source: str, *, settings: Sequence[str] = ()
    ) -> p.Result[str]:
        """Parenthesize annotated parameters the formatter cannot split.

        A ``name: Holder.Member,`` line longer than the project's limit has no
        break point; inside parentheses the formatter splits it. The long
        lines are those Ruff itself reports (E501) under the destination's
        configuration, so no limit is restated here.

        Returns:
            The source with only its long annotation lines reformatted.

        """
        listed = cls._ruff_stdin_pass(
            path,
            source,
            (
                c.Infra.CHECK,
                "--select",
                "E501",
                "--output-format",
                "json",
                "--exit-zero",
                "--no-fix",
            ),
            settings=settings,
        )
        if listed.failure:
            return listed
        rows = {
            int(finding["location"]["row"])
            for finding in json.loads(listed.value or "[]")
        }
        lines = source.splitlines(keepends=True)
        wrapped = False
        for row in rows:
            match = re.fullmatch(
                r"([ \t]+)(\w+): ([\w.\[\], |]+?)(,?)\n", lines[row - 1]
            )
            if match is None:
                continue
            indent, name, annotation, comma = match.groups()
            lines[row - 1] = (
                f"{indent}{name}: (\n{indent}    {annotation}\n{indent}){comma}\n"
            )
            wrapped = True
        if not wrapped:
            return r[str].ok(source)
        return cls._ruff_stdin_pass(
            path,
            "".join(lines),
            (c.Infra.FORMAT, *config.Infra.codegen.make.ruff.format_apply),
            settings=settings,
        )

    @classmethod
    def ruff_select_fix(
        cls,
        path: Path,
        source: str,
        select: Sequence[str],
        *,
        settings: Sequence[str] = (),
    ) -> p.Result[str]:
        """Repair exactly the selected Ruff codes of one candidate on stdin.

        ``path`` is the destination; it selects the owning project's Ruff
        configuration. The flags are the declared ``make.ruff`` repair surface.

        Returns:
            The repaired source, or Ruff's native failure.

        """
        declared = config.Infra.codegen.make.ruff
        return cls._ruff_stdin_pass(
            path,
            source,
            (c.Infra.CHECK, *declared.lint_fix, "--select", ",".join(select)),
            settings=settings,
        )

    @classmethod
    def _staged_ruff_settings(
        cls,
        plans: Sequence[p.Infra.CodegenFilePlan],
        *,
        line_limits: MutableMapping[Path, int],
    ) -> Mapping[Path, Sequence[str]]:
        """Render each staged pyproject's Ruff table as ``--config`` overrides.

        The line limit is retained from that same parsed table for the declared
        width recipe; it never borrows a global value for a staged project.

        A plan set that rewrites a project's ``pyproject.toml`` also rewrites
        its Ruff settings; normalizing that project's Python candidates with
        the on-disk copy reads the settings the run replaces (an UP040 that is
        unfixable in the new settings once rewrote ``Name: TypeAlias = Owner``
        into a runtime-different ``type`` statement). Ruff runs ``--isolated``
        and every top-level key of the complete staged ``[tool.ruff]`` table,
        ``src`` and first-party settings included, becomes one quoted
        ``--config`` key carrying its table inline, so on-disk state is
        irrelevant and the run's rule selection matches the projection
        exactly. Paths resolve against the project root, which is the pass's
        working directory.

        Returns:
            Override arguments per project root that stages a pyproject.

        """
        staged: MutableMapping[Path, Sequence[str]] = {}
        for plan in plans:
            if (
                plan.path != plan.project / c.PYPROJECT_FILENAME
                or plan.desired_content is None
            ):
                continue
            payload = u.Cli.toml_mapping_from_text_result(
                plan.desired_content.decode(c.DEFAULT_ENCODING)
            ).unwrap()
            tool = payload.get(c.Infra.TOOL)
            ruff = tool.get(c.Infra.RUFF) if isinstance(tool, Mapping) else None
            if not isinstance(ruff, Mapping):
                continue
            if "line-length" in ruff:
                line_limits[plan.project] = u.type_adapter(int).validate_python(
                    ruff["line-length"], strict=True
                )
            # `--isolated` makes Ruff ignore every on-disk configuration, so the
            # complete staged table below is the whole configuration: a key the
            # staged file drops is dropped here too, never merged from disk.
            # Each top-level key is one override whose table is inline: Ruff
            # layers every `--config` as its own rule selection, so a
            # `lint.select` override split from its `lint.ignore` re-selects
            # what the project ignores; one inline `lint` table is one
            # selection, exactly as the pyproject declares it.
            overrides: list[str] = ["--isolated"]
            for key, value in ruff.items():
                inline = cls._ruff_inline_value(value)
                overrides.extend((
                    "--config",
                    f"{u.Cli.json_dumps(key).unwrap()} = {inline}",
                ))
            staged[plan.project] = tuple(overrides)
        return staged

    @classmethod
    def _ruff_inline_value(cls, value: t.JsonValue) -> str:
        """Render one staged Ruff value as a TOML inline value.

        Keys and scalars are JSON literals, which TOML reads unchanged;
        tables become inline tables and arrays keep their order.

        Returns:
            The TOML inline literal of ``value``.

        """
        if isinstance(value, Mapping):
            members = ", ".join(
                f"{u.Cli.json_dumps(key).unwrap()} = {cls._ruff_inline_value(nested)}"
                for key, nested in value.items()
            )
            return f"{{{members}}}"
        if isinstance(value, list):
            return f"[{', '.join(cls._ruff_inline_value(item) for item in value)}]"
        return u.Cli.json_dumps(value).unwrap()

    @classmethod
    def _ruff_stdin_codes(
        cls,
        path: Path,
        source: str,
        *,
        settings: Sequence[str] = (),
        diagnostics: MutableSequence[tuple[str, int, str]] | None = None,
    ) -> p.Result[frozenset[str]]:
        """Return the Ruff rule codes one candidate reports on stdin.

        Returns:
            The reported rule codes, or Ruff's native failure.

        Raises:
            TypeError: If Ruff's JSON report is not a list of finding objects.

        """
        declared = config.Infra.codegen.make.ruff
        reported = cls._ruff_stdin_pass(
            path,
            source,
            (
                c.Infra.CHECK,
                *declared.lint_check,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--exit-zero",
                "--quiet",
            ),
            settings=settings,
        )
        if reported.failure:
            return r[frozenset[str]].from_failure(reported)
        report = u.Cli.json_parse(reported.value or "[]").unwrap()
        if not isinstance(report, list):
            msg = f"Ruff JSON report is not a list: {type(report).__name__}"
            raise TypeError(msg)
        codes: set[str] = set()
        for entry in report:
            if not isinstance(entry, Mapping):
                msg = f"Ruff JSON finding is not an object: {type(entry).__name__}"
                raise TypeError(msg)
            code = u.Cli.json_pick_str(entry, "code")
            if code:
                codes.add(code)
                if (
                    diagnostics is not None
                    and code == c.Infra.FORMATTER_UNSATISFIED_CODE
                ):
                    diagnostics.append(
                        cls._ruff_diagnostic_excerpt(path, source, entry)
                    )
        return r[frozenset[str]].ok(frozenset(codes))

    @staticmethod
    def _ruff_diagnostic_excerpt(
        path: Path, source: str, finding: t.JsonMapping
    ) -> tuple[str, int, str]:
        """Retain Ruff's native location/message and the actual candidate line.

        Returns:
            The native recipe identity, row, diagnostic and candidate source line.

        Raises:
            TypeError: The native location or row has an invalid JSON shape.
            ValueError: Ruff reported a row outside the supplied candidate.

        """
        location = finding.get("location")
        if not isinstance(location, Mapping) or not isinstance(
            row := location.get("row"), int
        ):
            message = "Ruff diagnostic has no native integer source row"
            raise TypeError(message)
        lines = source.splitlines()
        if not 1 <= row <= len(lines):
            message = "Ruff diagnostic row leaves its source candidate"
            raise ValueError(message)
        detail = (
            f"{path}: {u.Cli.json_dumps(dict(finding)).unwrap()}\n"
            f"{row}: {lines[row - 1]}"
        )
        return u.Cli.json_pick_str(finding, "name"), row, detail

    @classmethod
    def _ruff_environment(cls, command_cwd: Path) -> Mapping[str, str]:
        """Run Ruff with the gate environment and its external project cache.

        Returns:
            The lint environment carrying the project's external Ruff cache.

        """
        return {
            **cls._command_env(),
            c.Infra.RUFF_CACHE_ENVIRONMENT_VARIABLE: str(
                FlextInfraUtilitiesResourceLimits.ruff_cache_directory(command_cwd)
            ),
        }

    @classmethod
    def ruff_files(
        cls, arguments: Sequence[str], paths: Sequence[Path]
    ) -> p.Result[bool]:
        """Run one declared Ruff surface on files through the gate runtime.

        Files are grouped by owning project: each group runs the active
        environment's Ruff from that project with its external cache, so no
        cache lands in the caller's working directory or the source tree.

        Returns:
            Success when every group's Ruff run exits cleanly, else its failure.

        """
        grouped: MutableMapping[Path, list[Path]] = {}
        for path in paths:
            grouped.setdefault(cls._command_cwd(path, path.parent), []).append(path)
        for project, members in grouped.items():
            executed = u.Cli.run_checked(
                (
                    *cls._workspace_tool_command(c.Infra.RUFF),
                    *arguments,
                    *(str(path) for path in members),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env=cls._ruff_environment(project),
                    remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                ),
                timeout=cls._gate_deadline(c.Infra.RUFF),
            )
            if executed.failure:
                return r[bool].from_failure(executed)
        return r[bool].ok(value=True)

    @classmethod
    def _ruff_stdin_pass(
        cls,
        path: Path,
        source: str,
        arguments: Sequence[str],
        *,
        settings: Sequence[str] = (),
    ) -> p.Result[str]:
        """Run one declared Ruff surface on stdin with the destination's config.

        ``settings`` are the ``--config`` overrides of a pyproject staged in the
        same plan set (``_staged_ruff_settings``), so the pass reads the Ruff
        settings the run publishes, never the stale on-disk copy.

        Returns:
            Ruff's stdout, or its native failure; findings never fail the pass.

        """
        command_cwd = cls._command_cwd(path, path.parent)
        u.debug(
            f"normalize: ruff {arguments[0]} settings source="
            f"{'staged' if settings else 'none'} project={command_cwd} path={path}"
        ).unwrap()
        environment = cls._ruff_environment(command_cwd)
        executed = u.Cli.run_raw(
            (
                *cls._workspace_tool_command(c.Infra.RUFF),
                *arguments,
                *settings,
                "--stdin-filename",
                str(path),
                "-",
            ),
            cwd=command_cwd,
            options=m.Cli.ProcessOptions(
                env=environment,
                remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                input_data=source,
            ),
            timeout=cls._gate_deadline(c.Infra.RUFF),
        )
        if executed.failure:
            return r[str].from_failure(executed)
        output = executed.value
        outcome = FlextInfraUtilitiesProcess.tool_outcome(
            output.outcome,
            findings=int(bool(output.stderr.strip())),
            findings_exit_codes=config.Infra.tooling.tools.ruff.findings_exit_codes,
        )
        if outcome is c.Infra.ToolOutcome.ERROR:
            return r[str].fail(
                f"ruff {arguments[0]} failed for {path}: "
                f"{(output.stderr or output.stdout).strip()}"
            )
        return r[str].ok(output.stdout)

    @classmethod
    def normalize_sources(
        cls,
        repository_root: Path,
        updates: Mapping[Path, str | None],
    ) -> p.Result[Mapping[Path, str | None]]:
        """Prepare composed sources through the destination's native repair gates.

        Returns:
            Prepared updates keyed by live destination, or the first failure.

        """
        return codegen.FlextInfraStagedPackage.plan_sources(
            repository_root, updates
        ).flat_map(
            lambda plan: codegen.FlextInfraStagedPackage.prepare_sources(
                plan, cls._repair_staged_sources
            )
        )

    @classmethod
    def _repair_staged_sources(
        cls,
        root: Path,
        candidates: Mapping[Path, Path],
    ) -> p.Result[bool]:
        """Delegate every repair phase to the native gates, never copy recipes.

        Returns:
            Acceptance only when lint and format both confirm the prepared bytes.

        """
        grouped: MutableMapping[Path, list[Path]] = {}
        for path in candidates.values():
            project = cls._command_cwd(path, root)
            grouped.setdefault(project, []).append(path)
        for project, paths in grouped.items():
            context = m.Infra.GateContext(
                repository_root=root,
                reports_dir=root,
                apply_fixes=True,
                selected_files=tuple(paths),
            )
            lint = gates.FlextInfraGatesRuffLint(root).fix(project, context)
            if lint.outcome is c.Infra.ToolOutcome.ERROR:
                return r[bool].fail(lint.raw_output or "configured lint repair failed")
            formatted = gates.FlextInfraGatesRuffFormat(root).fix(project, context)
            if not formatted.result.passed:
                return r[bool].fail(
                    formatted.raw_output or "configured format repair failed"
                )
            checked = gates.FlextInfraGatesRuffLint(root).check_files(
                paths, project, context
            )
            if not checked.result.passed:
                return r[bool].fail(
                    checked.raw_output or "prepared source is not lint clean"
                )
        return r[bool].ok(value=True)

    @classmethod
    def remove_orphaned_text_imports(cls, original: str, proposed: str) -> str:
        """Remove only imports whose last executable use the transformation removed.

        Returns:
            The candidate retaining existing unused, string, and exported bindings.

        """
        before = ast.parse(original)
        after = ast.parse(proposed)
        lost = {
            item.id
            for item in ast.walk(before)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        } - {
            item.id
            for item in ast.walk(after)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        strings = tuple(
            item.value
            for item in ast.walk(after)
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        lost = {name for name in lost if not any(name in value for value in strings)}
        # No executable use was lost, so no import can have become orphaned and
        # the alias-stripping pass would return the proposal byte for byte.
        if not lost:
            return proposed
        return cls._strip_lost_import_aliases(
            proposed,
            after,
            frozenset(lost),
        )

    @classmethod
    def _strip_lost_import_aliases(
        cls,
        proposed: str,
        tree: ast.Module,
        lost: frozenset[str],
    ) -> str:
        """Remove import statements whose aliases all lost their executable use.

        Returns:
            The candidate without the orphaned import statements.

        Raises:
            ValueError: If a partially orphaned import has no complete span.

        """

        def selected_alias(alias: ast.alias) -> bool:
            return (alias.asname or alias.name.split(".")[0]) in lost

        lines = proposed.splitlines(keepends=True)
        plans: list[tuple[int, int, str | None]] = []
        for imported in ast.walk(tree):
            if not isinstance(imported, c.Infra.AST_IMPORT_TYPES):
                continue
            selected = [alias for alias in imported.names if selected_alias(alias)]
            if not selected:
                continue
            if imported.end_lineno is None or imported.end_col_offset is None:
                msg = "orphaned import statement has no complete source span"
                raise ValueError(msg)
            start, end = imported.lineno, imported.end_lineno
            if len(selected) == len(imported.names) and cls._spans_whole_lines(
                lines, imported
            ):
                plans.append((start, end, None))
                continue
            indent = lines[start - 1][: imported.col_offset]
            retained = [alias for alias in imported.names if not selected_alias(alias)]
            reduced = (
                ast.ImportFrom(
                    level=imported.level,
                    module=imported.module,
                    names=retained,
                )
                if isinstance(imported, ast.ImportFrom)
                else ast.Import(names=retained)
            )
            plans.append((start, end, f"{indent}{ast.unparse(reduced)}\n"))
        for start, end, replacement in sorted(plans, reverse=True):
            lines[start - 1 : end] = [replacement] if replacement is not None else []
        return "".join(lines)

    @staticmethod
    def _spans_whole_lines(
        lines: Sequence[str],
        statement: ast.stmt,
    ) -> bool:
        """Return whether one import statement occupies its lines completely.

        Returns:
            Whether nothing but whitespace and comments shares its lines.

        """
        head = lines[statement.lineno - 1][: statement.col_offset]
        tail = (
            lines[statement.end_lineno - 1][statement.end_col_offset :]
            if statement.end_lineno is not None and statement.end_col_offset is not None
            else ""
        )
        return not head.strip() and (not tail.strip() or tail.strip().startswith("#"))

    @classmethod
    def normalize_touched_files(
        cls,
        paths: Iterable[Path],
        repository_root: Path,
    ) -> None:
        """Prepare touched sources with their complete destination repair policy.

        Raises:
            RuntimeError: If a Ruff subprocess rejects the touched files.

        """
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path.resolve(), required=True).unwrap()
            for path in sorted(set(paths))
            if path.is_file()
        )
        if not states:
            return
        sources = {
            state.path: state.content.decode(c.DEFAULT_ENCODING)
            for state in states
            if state.content is not None
        }
        prepared = cls.normalize_sources(repository_root, sources).unwrap()
        originals = {state.path: state for state in states}
        for path, content in prepared.items():
            if content is None:
                msg = f"touched source preparation retired a file: {path}"
                raise RuntimeError(msg)
            if content != sources[path]:
                u.Cli.atomic_write_text_file_guarded(originals[path], content).unwrap()

    @staticmethod
    def unified_diff_lines(
        before: str,
        after: str,
        *,
        fromfile: str,
        tofile: str,
        max_lines: int,
    ) -> Sequence[str]:
        """Return a bounded unified diff without materializing omitted lines.

        Returns:
            A bounded unified diff without materializing omitted lines.

        Raises:
            ValueError: If max_lines must be positive.

        """
        if max_lines < 1:
            msg = "max_lines must be positive"
            raise ValueError(msg)
        return tuple(
            islice(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=fromfile,
                    tofile=tofile,
                    n=3,
                ),
                max_lines,
            ),
        )

    @staticmethod
    def _workspace_tool_command(tool_name: str) -> Sequence[str]:
        """Resolve one fleet lint tool from the active runtime environment.

        Returns:
            The resulting ``Sequence[str]``.

        Raises:
            FileNotFoundError: If the active environment lacks the tool.

        """
        environment = Path(sys.executable).parent
        executable = tool_name + (".exe" if os.name == "nt" else "")
        tool_path = environment / executable
        if not tool_path.is_file():
            msg = f"active runtime environment tool is missing: {tool_path}"
            raise FileNotFoundError(msg)
        return (str(tool_path),)

    @staticmethod
    def _normalize_lint_line(line: str) -> str:
        """Normalize lint line.

        Returns:
            The resulting ``str``.

        """
        if c.Infra.CODE_FRAME_RE.match(line) or c.Infra.CODE_FRAME_BODY_RE.match(line):
            return ""

        def normalize_unused_import(match: t.RegexMatch) -> str:
            imported_name = match.group(1).rsplit(".", maxsplit=1)[-1]
            return f"`{imported_name}` imported but unused"

        normalized_line: str = c.Infra.LINE_COL_RE.sub("", line)
        # The comparison pairs one logical file's before and after snapshots,
        # whose linted locations differ (live path vs staged source-view path):
        # the leading file-path token normalizes away so only the diagnostic
        # content itself can differ.
        head, separator, remainder = normalized_line.partition(" ")
        if separator and "/" in head:
            normalized_line = remainder
        normalized_without_unused_imports: str = c.Infra.UNUSED_IMPORT_RE.sub(
            normalize_unused_import,
            normalized_line,
        )
        if c.Infra.LINT_SUMMARY_RE.match(normalized_without_unused_imports):
            return ""
        return normalized_without_unused_imports.strip()

    @staticmethod
    def snapshot_lint_gates() -> Sequence[str]:
        """Return the lint gates a protected edit validates its snapshots with.

        One owner: ``make.check_gates_ci`` (config) — the active budgeted gate set
        whose strict complement is the slow whole-program checkers owned by
        ``make check CI=N``. A per-file snapshot validator never runs those.

        Returns:
            The lint gates a protected edit validates its snapshots with.

        """
        lint_tool_gates = {
            "lint" if entry[0] == "ruff" else entry[0] for entry in c.Infra.LINT_TOOLS
        }
        return tuple(
            gate
            for gate in config.Infra.codegen.make.check_gates_ci
            if gate in lint_tool_gates
        )

    @staticmethod
    def _selected_lint_tools(
        gates: Sequence[str] | None = None,
    ) -> t.StrSequencePairTuple:
        """Return the lint tools for the requested gates (SSOT gates when omitted).

        Returns:
            The lint tools for the requested gates (SSOT gates when omitted).

        Raises:
            ValueError: If lint snapshot gates select no lint tool.

        """
        requested = tuple(
            gate.strip().lower() for gate in (gates or ()) if gate.strip()
        )
        gate_names = set(
            requested or FlextInfraUtilitiesProtectedEditLinting.snapshot_lint_gates(),
        )
        selected = tuple(
            entry
            for entry in c.Infra.LINT_TOOLS
            if gate_names.intersection({
                "lint" if entry[0] == "ruff" else entry[0],
                entry[0],
            })
        )
        if not selected:
            msg = (
                "lint snapshot gates select no lint tool: "
                f"{sorted(gate_names)} (tools: "
                f"{', '.join(entry[0] for entry in c.Infra.LINT_TOOLS)})"
            )
            raise ValueError(msg)
        return selected

    @classmethod
    def selected_lint_tool_names(
        cls,
        gates: Sequence[str] | None = None,
    ) -> Sequence[str]:
        """Return the canonical lint tool names selected for a gate set.

        Returns:
            The canonical lint tool names selected for a gate set.

        """
        return tuple(entry[0] for entry in cls._selected_lint_tools(gates))

    @staticmethod
    def _relative_path(py_file: Path, workspace: Path) -> Path:
        """Return ``py_file`` relative to the workspace when it lies inside it.

        Returns:
            ``py_file`` relative to the workspace when it lies inside it.

        """
        if py_file.is_relative_to(workspace):
            return py_file.relative_to(workspace)
        return py_file

    @staticmethod
    def _command_cwd(py_file: Path, workspace: Path) -> Path:
        """Command cwd.

        Returns:
            The resulting ``Path``.

        """
        resolved_workspace = workspace.resolve()
        project_root: Path | None = FlextInfraUtilitiesDiscovery.project_root(py_file)
        if project_root is None:
            return resolved_workspace
        return project_root

    _COMMAND_ENV_REMOVE_KEYS: ClassVar[Sequence[str]] = (
        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,
        c.Infra.ENV_VAR_FORCE_COLOR,
    )

    @staticmethod
    def _command_env() -> Mapping[str, str]:
        """Return subprocess env overrides for lint and validation commands.

        ``run_raw`` merges this mapping over ``os.environ``, so keys can only be
        dropped by passing ``_COMMAND_ENV_REMOVE_KEYS`` as ``remove_env_keys``.

        Returns:
            Subprocess env overrides for lint and validation commands.

        """
        return {c.Infra.ORCHESTRATOR_ENV_NO_COLOR: c.ParserBooleanToken.ONE}

    @classmethod
    def _lint_command(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        command_cwd: Path,
        tool_name: str,
        template: Sequence[str],
    ) -> Sequence[str]:
        """Build one canonical protected-edit lint command.

        Returns:
            The resulting ``Sequence[str]``.

        """
        if tool_name == c.Infra.MYPY:
            return FlextInfraUtilitiesResourceLimits.mypy_limited_command(
                m.Infra.MypyInvocation(
                    targets=(py_file.resolve(),),
                    workspace=workspace,
                    report_json=True,
                ),
            )
        command: Sequence[str] = (
            *cls._workspace_tool_command(template[0]),
            *(item.replace("{file}", str(py_file)) for item in template[1:]),
        )
        if tool_name == c.Infra.RUFF:
            command = (*command, "--output-format", c.Infra.OUTPUT_JSON)
        elif tool_name == c.Infra.PYRIGHT:
            command = (*command, "--outputjson")
        elif tool_name == c.Infra.PYREFLY:
            command = (
                *command,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "-o",
                "-",
                "--summary=none",
            )
        if (
            tool_name == c.Infra.PYREFLY
            and (project_config := command_cwd / c.PYPROJECT_FILENAME).is_file()
        ):
            command = (*command, "--config", str(project_config))
        return command

    @classmethod
    def lint_commands(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: Sequence[str] | None = None,
    ) -> t.StrSequencePairTuple:
        """Return the exact public command plan used by protected linting.

        Returns:
            The exact public command plan used by protected linting.

        """
        command_cwd = cls._command_cwd(py_file, workspace)
        return tuple(
            (
                entry[0],
                cls._lint_command(
                    py_file,
                    workspace,
                    command_cwd=command_cwd,
                    tool_name=entry[0],
                    template=entry[1],
                ),
            )
            for entry in cls._selected_lint_tools(gates)
        )

    @classmethod
    def _execute_selected_lint_tools(
        cls,
        py_file: Path,
        workspace: Path,
        selected_tools: t.StrSequencePairTuple,
    ) -> t.Infra.LintSnapshot[p.Infra.LintGateResult]:
        """Execute selected lint tools.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        """
        # Every gate is an independent subprocess -- _run_lint_gate
        # builds its own command and returns a value, touching no shared state.
        # Running any one of them ahead of the pool made a snapshot cost that
        # gate's full wall clock PLUS the slowest of the rest, instead of just
        # the slowest. Measured: 8 snapshots x 4 gates at 0.297s each.
        results: list[p.Infra.LintGateResult] = []
        if not selected_tools:
            return cls._lint_snapshot_from_results(())

        # The pool waits for the slowest DECLARED gate deadline (mypy owns a
        # resource-limited deadline of its own); a shorter pool budget cut the
        # gate short and reported the cut as lint errors, reverting valid edits.
        timeout_budget = (
            max(cls._gate_deadline(entry[0]) for entry in selected_tools) + 10
        )
        pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(
                1, min(config.Infra.codegen.lint_snapshot_workers, len(selected_tools))
            ),
        )
        futures_by_tool = {
            pool.submit(
                cls._run_lint_gate,
                py_file=py_file,
                workspace=workspace,
                tool_name=entry[0],
                template=entry[1],
            ): entry[0]
            for entry in selected_tools
        }
        try:
            done, not_done = concurrent.futures.wait(
                tuple(futures_by_tool),
                timeout=timeout_budget,
            )
            results.extend(
                future.result() for future in futures_by_tool if future in done
            )
            for future in not_done:
                tool_name = futures_by_tool[future]
                _ = future.cancel()
                results.append(
                    m.Infra.LintGateResult(
                        tool_name=tool_name,
                        execution_error=(
                            f"timeout {timeout_budget}s: lint gate "
                            f"'{tool_name}' did not finish; native outcome unavailable"
                        ),
                    ),
                )
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        return cls._lint_snapshot_from_results(tuple(results))

    @staticmethod
    def _gate_deadline(tool_name: str) -> int:
        """Return the one declared deadline for a lint gate subprocess.

        Returns:
            The one declared deadline for a lint gate subprocess.

        """
        if tool_name == c.Infra.MYPY:
            return FlextInfraUtilitiesResourceLimits.mypy_runner_timeout()
        return max(5, min(15, c.Infra.TIMEOUT_SHORT))

    @classmethod
    def _run_lint_gate(
        cls,
        *,
        py_file: Path,
        workspace: Path,
        tool_name: str,
        template: Sequence[str],
        source: str | None = None,
    ) -> p.Infra.LintGateResult:
        """Run one lint gate and return a validated result model.

        Returns:
            The resulting ``m.Infra.LintGateResult``.

        """
        command_cwd = cls._command_cwd(py_file, workspace)
        cmd = cls._lint_command(
            py_file,
            workspace,
            command_cwd=command_cwd,
            tool_name=tool_name,
            template=template,
        )
        if source is not None:
            cmd = (
                *tuple(item for item in cmd if item != str(py_file)),
                # Why: a candidate stdin snapshot must honor the destination
                # project's exclude policy; Ruff applies exclusions to stdin
                # only under --force-exclude, and excluded trees are not this
                # gate's to judge.
                *(
                    ("--force-exclude",)
                    if tool_name == c.Infra.RUFF and "--force-exclude" not in cmd
                    else ()
                ),
                "--stdin-filename",
                str(py_file),
                "-",
            )
        environment = dict(cls._command_env())
        if tool_name == c.Infra.RUFF:
            environment = dict(cls._ruff_environment(command_cwd))
        elif tool_name == c.Infra.MYPY:
            environment[c.Infra.MypyCacheEnvironment.CACHE_DIR.value] = str(
                FlextInfraUtilitiesResourceLimits.mypy_cache_directory(command_cwd)
            )
        run_result = u.Cli.run_raw(
            cmd,
            cwd=command_cwd,
            options=m.Cli.ProcessOptions(
                env=environment,
                remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                input_data=source,
            ),
            timeout=cls._gate_deadline(tool_name),
        )
        return cls.lint_gate_result(tool_name, run_result)

    @staticmethod
    def lint_gate_result(
        tool_name: str,
        executed: p.Result[p.Cli.CommandOutput],
    ) -> p.Infra.LintGateResult:
        """Retain the native receipt without turning an absent report into success.

        A process that never produced a native outcome stops the gate at once:
        its original exception propagates unchanged.

        Returns:
            Diagnostic evidence and the independent first execution failure.

        """
        output = m.Cli.CommandOutput.model_validate(
            executed.unwrap(), from_attributes=True
        )
        parsed = FlextInfraUtilitiesProtectedEditLinting._lint_report_errors(
            tool_name, output.stdout
        )
        lines = parsed.value if parsed.success else ()
        classification = FlextInfraUtilitiesProcess.tool_outcome(
            output.outcome,
            findings=len(lines),
            findings_exit_codes=(
                config.Infra.tooling.tools.ruff.findings_exit_codes
                if tool_name == c.Infra.RUFF
                else (c.Cli.EXIT_CODE_FAILURE,)
            ),
        )
        resource_error = (
            FlextInfraUtilitiesResourceLimits.mypy_failure_diagnostic(output)
            if tool_name == c.Infra.MYPY
            else None
        )
        failure = resource_error
        if classification is c.Infra.ToolOutcome.ERROR:
            failure = failure or (
                f"{tool_name} execution failed: "
                f"exit={output.outcome.raw_return_code}, "
                f"timed_out={output.outcome.timed_out}, "
                f"forwarded_signal={output.outcome.forwarded_signal}: "
                f"{(output.stderr or output.stdout).strip()}"
            )
        failure = failure or (str(parsed.error) if parsed.failure else None)
        return m.Infra.LintGateResult(
            tool_name=tool_name,
            errors=lines,
            output=output,
            execution_error=failure,
        )

    @classmethod
    def _lint_report_errors(
        cls, tool_name: str, source: str
    ) -> p.Result[Sequence[str]]:
        """Validate the selected tool's native machine report before counting findings.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[Sequence[str]]
        if tool_name == c.Infra.MYPY:
            return cls._mypy_report_errors(source)
        if tool_name == c.Infra.PYRIGHT:
            return cls._pyright_report_errors(source)
        if tool_name == c.Infra.PYREFLY:
            pyrefly = u.validate_value(
                m.Infra.PyreflyReport, source, from_json=True, strict=True
            )
            return pyrefly.map(
                lambda observed: tuple(
                    f"{entry.path}:{entry.line}:{entry.column}: "
                    f"{entry.severity}: {entry.description} [{entry.name}]"
                    for entry in observed.errors
                    if entry.severity in {"error", "warn"}
                )
            )
        if tool_name != c.Infra.RUFF:
            return result.fail(f"unsupported lint report contract: {tool_name}")
        return cls._ruff_report_errors(source)

    @staticmethod
    def _pyright_report_errors(source: str) -> p.Result[Sequence[str]]:
        """Validate native diagnostics and require actual analyzed sources.

        Returns:
            Complete findings or the original malformed/empty-analysis failure.

        """
        result = r[Sequence[str]]
        report = u.validate_value(
            m.Infra.PyrightReport, source, from_json=True, strict=True
        )
        if report.failure:
            return result.from_failure(report)
        observed = report.value
        if not observed.summary.files_analyzed:
            return result.fail("pyright analyzed no files for the selected source")
        return result.ok(
            tuple(
                f"{entry.file}:"
                f"{entry.range.start.line + 1 if entry.range else 0}:"
                f"{entry.range.start.character + 1 if entry.range else 0}: "
                f"{entry.severity}: {entry.message} [{entry.rule or ''}]"
                for entry in observed.general_diagnostics
                if entry.severity in {"error", "warning"}
            ),
        )

    @staticmethod
    def _mypy_report_errors(source: str) -> p.Result[Sequence[str]]:
        """Validate every native JSON-lines diagnostic, retaining hints and failures.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[Sequence[str]]
        lines: list[str] = []
        for line in filter(str.strip, source.splitlines()):
            diagnostic = u.validate_value(
                m.Infra.MypyDiagnostic, line, from_json=True, strict=True
            )
            if diagnostic.failure:
                return result.from_failure(diagnostic)
            entry = diagnostic.value
            if entry.severity != "error":
                continue
            lines.append(
                f"{entry.file}:{entry.line}:{entry.column}: "
                f"{entry.severity}: {entry.message} [{entry.code or ''}]"
                + (f"\n{entry.hint}" if entry.hint else "")
            )
        return result.ok(tuple(lines))

    @staticmethod
    def _ruff_report_errors(source: str) -> p.Result[Sequence[str]]:
        """Validate Ruff's complete native finding list before projecting diagnostics.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[Sequence[str]]
        loaded = u.Cli.json_parse(source)
        if loaded.failure or not isinstance(loaded.value, list):
            return (
                result.from_failure(loaded)
                if loaded.failure
                else result.fail("Ruff JSON report is not a list of findings")
            )
        errors: list[str] = []
        for finding in loaded.value:
            if not isinstance(finding, dict):
                return result.fail("Ruff JSON finding is not an object")
            location = finding.get("location")
            if not isinstance(location, dict):
                return result.fail("Ruff JSON finding lacks its native location")
            issue = u.validate_value(
                m.Infra.Issue,
                {
                    "file": finding.get("filename"),
                    "line": location.get("row"),
                    "column": location.get("column"),
                    "code": finding.get("code"),
                    "message": finding.get("message"),
                },
                strict=True,
            )
            if issue.failure:
                return result.from_failure(issue)
            if (
                not issue.value.file.strip()
                or not issue.value.code.strip()
                or not issue.value.message.strip()
                or issue.value.line < 1
                or issue.value.column < 1
            ):
                return result.fail(
                    "Ruff JSON finding has invalid native diagnostic fields"
                )
            errors.append(issue.value.formatted)
        return result.ok(tuple(errors))

    @staticmethod
    def lint_execution_errors(
        snapshot: t.Infra.LintSnapshot[p.Infra.LintGateResult],
    ) -> Sequence[str]:
        """Return execution failures independently of diagnostic occurrence deltas.

        Returns:
            Every native execution failure in declared tool order.

        """
        return tuple(
            result.execution_error
            for result in snapshot.values()
            if result.execution_error is not None
        )

    @staticmethod
    def _lint_snapshot_from_results(
        results: Sequence[p.Infra.LintGateResult],
    ) -> t.Infra.LintSnapshot[p.Infra.LintGateResult]:
        """Convert validated lint gate results into the public snapshot contract.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        """
        return {result.tool_name: result for result in results}

    @classmethod
    def lint_snapshot(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: Sequence[str] | None = None,
        source: str | None = None,
    ) -> t.Infra.LintSnapshot[p.Infra.LintGateResult]:
        """Run selected tools, or uncached Ruff on candidate source at *py_file*.

        Candidate stdin retains the destination's filename and configuration;
        it never materializes the proposed bytes on the live filesystem.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        Raises:
            ValueError: If source snapshots select a tool other than Ruff.

        """
        selected_tools = cls._selected_lint_tools(gates)
        if source is not None:
            if tuple(entry[0] for entry in selected_tools) != (c.Infra.RUFF,):
                msg = "source lint snapshots require the Ruff lint gate"
                raise ValueError(msg)
            return cls._lint_snapshot_from_results((
                cls._run_lint_gate(
                    py_file=py_file,
                    workspace=workspace,
                    tool_name=selected_tools[0][0],
                    template=selected_tools[0][1],
                    source=source,
                ),
            ))
        return cls._execute_selected_lint_tools(
            py_file=py_file,
            workspace=workspace,
            selected_tools=selected_tools,
        )

    @classmethod
    def lint_snapshots(
        cls,
        paths: Sequence[Path],
        workspace: Path,
        *,
        gates: Sequence[str] | None = None,
    ) -> MutableMapping[Path, t.Infra.LintSnapshot[p.Infra.LintGateResult]]:
        """Validate files in order while each file runs its tools concurrently.

        Returns:
            The resulting ``MutableMapping[Path, t.Infra.LintSnapshot]``.

        """
        ordered_paths = tuple(paths)
        if not ordered_paths:
            return {}
        if len(ordered_paths) == 1:
            path = ordered_paths[0]
            return {path: cls.lint_snapshot(path, workspace, gates=gates)}

        snapshots_by_path: MutableMapping[
            Path, t.Infra.LintSnapshot[p.Infra.LintGateResult]
        ] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(
                1, min(config.Infra.codegen.lint_snapshot_workers, len(ordered_paths))
            ),
        ) as pool:
            futures_by_path = {
                pool.submit(cls.lint_snapshot, path, workspace, gates=gates): path
                for path in ordered_paths
            }
            for future in concurrent.futures.as_completed(futures_by_path):
                snapshots_by_path[futures_by_path[future]] = future.result()

        return {path: snapshots_by_path[path] for path in ordered_paths}

    @staticmethod
    def lint_new_errors(
        before: t.Infra.LintSnapshot[p.Infra.LintGateResult],
        after: t.Infra.LintSnapshot[p.Infra.LintGateResult],
    ) -> t.Infra.LintSnapshot[Sequence[str]]:
        """Return introduced diagnostic occurrences, ignoring shifted coordinates.

        Matching consumes each baseline occurrence once; resolving another rule
        never compensates for a new message or an additional identical finding.

        Returns:
            Only lint errors introduced relative to *before*.

        """
        introduced: MutableMapping[str, Sequence[str]] = {}
        normalize = FlextInfraUtilitiesProtectedEditLinting._normalize_lint_line
        for tool, candidate in after.items():
            baseline = before.get(tool)
            remaining = (
                Counter(normalize(line) for line in baseline.errors)
                if baseline is not None
                else Counter[str]()
            )
            added: list[str] = []
            for line in candidate.errors:
                identity = normalize(line)
                if not identity:
                    continue
                if remaining[identity]:
                    remaining[identity] -= 1
                else:
                    added.append(line)
            if added:
                introduced[tool] = tuple(added)
        return introduced


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditLinting"]
