"""Census and introspection utilities for the refactor subpackage."""

from __future__ import annotations

import contextlib
import re
import shutil
from collections import defaultdict
from collections.abc import (
    Callable as _CensusCallable,
    Mapping,
    Sequence,
)
from pathlib import Path

from flext_infra import FlextInfraModelsRefactorCensus as mrc, c, m, p, t
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports


class FlextInfraUtilitiesRefactorCensus:
    """Census and source introspection helpers for refactor tools."""

    @staticmethod
    def identify_project_by_roots(
        file_path: Path,
        project_roots: Sequence[Path],
    ) -> str:
        """Identify project name for a file path (most-specific root wins)."""
        matching_roots = [
            root for root in project_roots if file_path.is_relative_to(root)
        ]
        if not matching_roots:
            unknown: str = c.Infra.DEFAULT_UNKNOWN
            return unknown
        best = max(matching_roots, key=lambda root: len(root.parts))
        name: str = best.name
        return name

    @staticmethod
    def build_mro_target(
        family: str,
        core_project: str = c.Infra.PKG_CORE,
    ) -> mrc.MROFamilyTarget:
        """Create a generic target settings from a family code."""
        if family not in c.Infra.MRO_FAMILIES:
            msg = f"Invalid MRO family {family}"
            raise ValueError(msg)
        sf = c.Infra.FAMILY_SUFFIXES[family]
        return mrc.MROFamilyTarget(
            family=family,
            class_suffix=sf,
            package_dir=c.Infra.MRO_FAMILY_PACKAGE_DIRS[family],
            facade_module=c.Infra.MRO_FAMILY_FACADE_MODULES[family],
            facade_class_prefix=f"Flext{sf}",
            core_project=core_project,
        )

    @staticmethod
    def export_pydantic_json(model_payload: m.BaseModel, export_path: Path) -> None:
        """Serialize any Pydantic model payload to a JSON file."""
        export_path.write_text(
            model_payload.model_dump_json(indent=2),
            encoding=c.Cli.ENCODING_DEFAULT,
        )

    @staticmethod
    def plan_simple_removal_edits(
        rope: p.Infra.RopeWorkspaceDsl,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> Mapping[Path, tuple[t.IntPair, ...]] | None:
        """Plan safe line-range removals for simple top-level removal candidates."""
        if candidate.scope_path != candidate.object_name:
            return None
        if candidate.object_kind not in {"class", "function"}:
            return None
        definition_path = Path(candidate.file_path).resolve()
        definition_range = FlextInfraUtilitiesRefactorCensus._definition_line_range(
            rope.source(definition_path),
            candidate,
        )
        if definition_range is None:
            return None
        ranges_by_file: dict[Path, list[t.IntPair]] = defaultdict(list)
        ranges_by_file[definition_path].append(definition_range)
        for site in FlextInfraUtilitiesRefactorCensus._supporting_reference_sites(
            candidate
        ):
            site_path = Path(site.file_path).resolve()
            site_range = FlextInfraUtilitiesRefactorCensus._reference_line_range(
                rope.source(site_path),
                site,
            )
            if site_range is None:
                return None
            ranges_by_file[site_path].append(site_range)
        return {
            file_path: FlextInfraUtilitiesRefactorCensus.merge_line_ranges(ranges)
            for file_path, ranges in ranges_by_file.items()
        }

    @staticmethod
    def build_simple_removal_sources(
        rope: p.Infra.RopeWorkspaceDsl,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> Mapping[Path, str] | None:
        """Build updated sources for a simple removal candidate without writing."""
        edit_plan = FlextInfraUtilitiesRefactorCensus.plan_simple_removal_edits(
            rope,
            candidate,
        )
        if edit_plan is None:
            return None
        definition_path = Path(candidate.file_path).resolve()
        updates: dict[Path, str] = {}
        for file_path, ranges in edit_plan.items():
            source = FlextInfraUtilitiesRefactorCensus.apply_line_ranges(
                rope.source(file_path),
                ranges,
            )
            if file_path.resolve() == definition_path:
                source = FlextInfraUtilitiesRefactorCensus.strip_module_all_entry(
                    source,
                    candidate.object_name,
                )
            updates[file_path] = source
        facade_cascade = (
            FlextInfraUtilitiesRefactorCensus.build_facade_base_cascade_updates(
                rope,
                candidate,
            )
        )
        if facade_cascade is None:
            return None
        updates.update(facade_cascade)
        return updates

    @staticmethod
    def build_facade_base_cascade_updates(
        rope: p.Infra.RopeWorkspaceDsl,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> Mapping[Path, str] | None:
        """Drop ``candidate`` from class-base lists in facade modules.

        Returns an empty mapping when no facade references the candidate, a
        populated mapping with rewritten sources otherwise, or ``None`` when
        removing the base would leave a facade class with no bases at all
        (unsafe — candidate must be handled manually).
        """
        target_name = candidate.object_name
        updates: dict[Path, str] = {}
        for module in rope.modules():
            file_path = module.file_path
            if file_path.name == c.Infra.INIT_PY:
                continue
            if file_path.resolve() == Path(candidate.file_path).resolve():
                continue
            source = rope.source(file_path)
            if target_name not in source:
                continue
            rewritten, disqualified = (
                FlextInfraUtilitiesRefactorCensus._strip_class_base(
                    source,
                    target_name,
                )
            )
            if disqualified:
                return None
            if rewritten == source:
                continue
            updates[file_path.resolve()] = rewritten
        return updates

    @staticmethod
    def _strip_class_base(source: str, base_name: str) -> tuple[str, bool]:
        """Return (new_source, disqualified) after removing ``base_name`` from bases.

        Handles single-line class declarations ``class X(A, B, C):``. When the
        removed base was the sole entry, the candidate is flagged as
        disqualified so the caller can abort the cascade safely.
        """
        escaped = re.escape(base_name)
        pattern = re.compile(
            r"^(?P<indent>[ \t]*)class[ \t]+(?P<name>\w+)[ \t]*\((?P<bases>[^()\n]*)\)[ \t]*:",
            re.MULTILINE,
        )
        disqualified = False

        def _rewrite(match: re.Match[str]) -> str:
            nonlocal disqualified
            bases_raw = match.group("bases")
            entries = [entry.strip() for entry in bases_raw.split(",") if entry.strip()]
            remaining = [
                entry
                for entry in entries
                if entry != base_name
                and not re.fullmatch(rf"{escaped}(?:\[.*\])?", entry)
            ]
            if len(remaining) == len(entries):
                return match.group(0)
            if not remaining:
                disqualified = True
                return match.group(0)
            return (
                f"{match.group('indent')}class {match.group('name')}("
                f"{', '.join(remaining)}):"
            )

        new_source = pattern.sub(_rewrite, source)
        return new_source, disqualified

    @staticmethod
    def strip_module_all_entry(source: str, name: str) -> str:
        """Remove ``name`` from a module-level ``__all__`` list declaration.

        Handles both single-line and multi-line ``__all__`` forms. The list is
        normalised to single-line ``[...]`` when all remaining entries fit on
        one line; otherwise each remaining entry stays on its own line. When
        the removed entry was the only element, the list is collapsed to
        ``[]``.
        """
        single_line = re.compile(
            r"^(?P<prefix>__all__(?:\s*:\s*[^\n=]+)?\s*=\s*)\[(?P<body>[^\[\]\n]*)\]",
            re.MULTILINE,
        )
        multi_line = re.compile(
            r"^(?P<prefix>__all__(?:\s*:\s*[^\n=]+)?\s*=\s*)\[(?P<body>[^\[\]]*?)\]",
            re.MULTILINE | re.DOTALL,
        )
        quoted_target = {f'"{name}"', f"'{name}'"}

        def _rewrite_single(match: re.Match[str]) -> str:
            body = match.group("body")
            entries = [entry.strip() for entry in body.split(",") if entry.strip()]
            remaining = [entry for entry in entries if entry not in quoted_target]
            if len(remaining) == len(entries):
                return match.group(0)
            return f"{match.group('prefix')}[{', '.join(remaining)}]"

        def _rewrite_multi(match: re.Match[str]) -> str:
            body = match.group("body")
            if "\n" not in body:
                return match.group(0)
            entries = [entry.strip() for entry in body.split(",") if entry.strip()]
            remaining = [entry for entry in entries if entry not in quoted_target]
            if len(remaining) == len(entries):
                return match.group(0)
            prefix = match.group("prefix")
            if not remaining:
                return f"{prefix}[]"
            lines = ",\n".join(f"    {entry}" for entry in remaining)
            return f"{prefix}[\n{lines},\n]"

        first = single_line.sub(_rewrite_single, source)
        return multi_line.sub(_rewrite_multi, first)

    @staticmethod
    def preview_simple_removal_candidate(
        rope: p.Infra.RopeWorkspaceDsl,
        workspace: Path,
        candidate: m.Infra.Census.RemovalCandidate,
        *,
        gates: t.StrSequence,
    ) -> bool:
        """Preview one simple removal candidate and require clean Ruff/Pyrefly gates."""
        updates = FlextInfraUtilitiesRefactorCensus.build_simple_removal_sources(
            rope,
            candidate,
        )
        if updates is None:
            return False
        file_paths = tuple(sorted(updates))

        def _post_write() -> None:
            with contextlib.suppress(RecursionError):
                rope.rope_project.validate()
            for file_path in file_paths:
                resource = rope.resource(file_path)
                if resource is None:
                    continue
                with contextlib.suppress(RecursionError):
                    FlextInfraUtilitiesRopeImports.organize_imports(
                        rope.rope_project,
                        resource,
                        apply=True,
                    )

        result = FlextInfraUtilitiesProtectedEdit.preview_source_writes(
            updates,
            workspace=workspace,
            gates=gates,
            post_write=_post_write,
        )
        rope.reload()
        return result[0]

    @staticmethod
    def apply_simple_removal_candidate(
        rope: p.Infra.RopeWorkspaceDsl,
        workspace: Path,
        candidate: m.Infra.Census.RemovalCandidate,
        *,
        gates: t.StrSequence,
        post_apply_hook: _CensusCallable[[Path], None] | None = None,
    ) -> bool:
        """Apply one simple removal candidate permanently, gates-validated.

        ``post_apply_hook`` is executed **after** sources are written and rope
        imports are organised, but **before** the gate snapshot runs. Callers
        that need to regenerate governance artefacts (e.g. ``__init__.py``
        lazy maps via ``FlextInfraCodegenLazyInit``) pass the regeneration
        routine here. This keeps ``flext_infra._utilities.census`` outside
        the ``flext_infra.codegen.lazy_init`` import cycle while still
        giving gates a chance to verify post-cascade correctness.
        """
        updates = FlextInfraUtilitiesRefactorCensus.build_simple_removal_sources(
            rope,
            candidate,
        )
        if updates is None:
            return False
        file_paths = tuple(sorted(updates))

        def _post_write() -> None:
            with contextlib.suppress(RecursionError):
                rope.rope_project.validate()
            for file_path in file_paths:
                resource = rope.resource(file_path)
                if resource is None:
                    continue
                with contextlib.suppress(RecursionError):
                    FlextInfraUtilitiesRopeImports.organize_imports(
                        rope.rope_project,
                        resource,
                        apply=True,
                    )
            if post_apply_hook is not None:
                with contextlib.suppress(Exception):
                    post_apply_hook(workspace)

        result = FlextInfraUtilitiesProtectedEdit.protected_source_writes(
            updates,
            workspace=workspace,
            gates=gates,
            post_write=_post_write,
            skip_pytest=True,
        )
        rope.reload()
        return result[0]

    @staticmethod
    def apply_line_ranges(
        source: str,
        ranges: Sequence[t.IntPair],
    ) -> str:
        """Remove one or more 1-based inclusive line ranges from Python source."""
        merged_ranges = FlextInfraUtilitiesRefactorCensus.merge_line_ranges(ranges)
        if not merged_ranges:
            return source
        removed_lines = {
            line_number
            for start, end in merged_ranges
            for line_number in range(start, end + 1)
        }
        lines = source.splitlines(keepends=True)
        return "".join(
            line
            for index, line in enumerate(lines, start=1)
            if index not in removed_lines
        )

    @staticmethod
    def clone_project_for_validation(source: Path, destination: Path) -> Path:
        """Copy a project tree into a scratch directory for post-apply validation.

        Skips cache and virtual-env directories so the clone is minimal and the
        downstream rope workspace opens on source-only state. Returns the
        resolved destination path.
        """
        resolved_source = source.resolve()
        resolved_destination = destination.resolve()
        if not resolved_source.is_dir():
            msg = f"clone source is not a directory: {resolved_source}"
            raise NotADirectoryError(msg)
        if resolved_destination.exists():
            shutil.rmtree(resolved_destination)
        shutil.copytree(
            resolved_source,
            resolved_destination,
            ignore=shutil.ignore_patterns(*c.Infra.VALIDATION_CLONE_EXCLUDES),
            symlinks=False,
        )
        return resolved_destination

    @staticmethod
    def merge_line_ranges(
        ranges: Sequence[t.IntPair],
    ) -> tuple[t.IntPair, ...]:
        """Merge overlapping or adjacent 1-based inclusive line ranges."""
        if not ranges:
            return ()
        ordered_ranges = sorted(ranges)
        merged: list[t.IntPair] = [ordered_ranges[0]]
        for start, end in ordered_ranges[1:]:
            previous_start, previous_end = merged[-1]
            if start <= previous_end + 1:
                merged[-1] = (previous_start, max(previous_end, end))
                continue
            merged.append((start, end))
        return tuple(merged)

    @staticmethod
    def _supporting_reference_sites(
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> tuple[m.Infra.Census.ReferenceSite, ...]:
        return (
            *candidate.test_reference_sites,
            *candidate.example_reference_sites,
            *candidate.script_reference_sites,
        )

    @staticmethod
    def _definition_line_range(
        source: str,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> t.IntPair | None:
        block = FlextInfraUtilitiesRopeHelpers.extract_definition(
            source,
            candidate.object_name,
            kind=candidate.object_kind,
        )
        if block is None:
            return None
        return FlextInfraUtilitiesRefactorCensus._line_range_for_snippet(source, block)

    @staticmethod
    def _reference_line_range(
        source: str,
        site: m.Infra.Census.ReferenceSite,
    ) -> t.IntPair | None:
        lines = source.splitlines()
        if site.line < 1 or site.line > len(lines):
            return None
        start = FlextInfraUtilitiesRefactorCensus._top_level_statement_start(
            lines,
            line_index=site.line - 1,
        )
        if start is None:
            return None
        if lines[start].lstrip().startswith("class "):
            return None
        end = FlextInfraUtilitiesRefactorCensus._top_level_statement_end(
            lines,
            start_index=start,
        )
        if end is None:
            return None
        return start + 1, end + 1

    @staticmethod
    def _line_range_for_snippet(
        source: str,
        snippet: str,
    ) -> t.IntPair | None:
        start_offset = source.find(snippet)
        if start_offset < 0:
            return None
        start_line = source[:start_offset].count("\n") + 1
        end_line = start_line + snippet.count("\n")
        return start_line, end_line

    @staticmethod
    def _top_level_statement_start(
        lines: Sequence[str],
        *,
        line_index: int,
    ) -> int | None:
        start = line_index
        while start >= 0:
            line = lines[start]
            stripped = line.strip()
            if not stripped:
                start -= 1
                continue
            if line.startswith((" ", "\t")):
                start -= 1
                continue
            prior_balance = sum(
                FlextInfraUtilitiesRopeHelpers.bracket_balance_line(lines[i])
                for i in range(start)
            )
            if prior_balance > 0:
                start -= 1
                continue
            while start > 0:
                previous = lines[start - 1]
                if previous.startswith("@"):
                    start -= 1
                    continue
                break
            return start
        return None

    @staticmethod
    def _top_level_statement_end(
        lines: Sequence[str],
        *,
        start_index: int,
    ) -> int | None:
        if start_index < 0 or start_index >= len(lines):
            return None
        bracket_balance = FlextInfraUtilitiesRopeHelpers.bracket_balance_line(
            lines[start_index]
        )
        end = start_index
        for index in range(start_index + 1, len(lines)):
            line = lines[index]
            stripped = line.strip()
            if bracket_balance > 0:
                end = index
                bracket_balance += FlextInfraUtilitiesRopeHelpers.bracket_balance_line(
                    line
                )
                continue
            if not stripped:
                end = index
                continue
            if not line.startswith((" ", "\t")):
                return end
            end = index
            bracket_balance += FlextInfraUtilitiesRopeHelpers.bracket_balance_line(line)
        return end


__all__: list[str] = ["FlextInfraUtilitiesRefactorCensus"]
