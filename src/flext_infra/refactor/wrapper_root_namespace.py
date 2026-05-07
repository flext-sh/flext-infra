"""Wrapper-root namespace refactor command for tests/examples/scripts aliases."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from operator import itemgetter
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    FlextInfraUtilitiesRopeAnalysis,
    c,
    m,
    p,
    r,
    t,
    u,
)


@dataclass(slots=True)
class _WrapperRewriteAccumulator:
    """Aggregates per-file rewrite stats across the wrapper-root verb run."""

    updates: dict[Path, str] = field(default_factory=dict)
    wrapper_candidates: list[Path] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    total_replacements: int = 0
    total_core_replacements: int = 0
    import_rewrite_candidates: int = 0
    per_project_changes: defaultdict[str, int] = field(
        default_factory=lambda: defaultdict(int),
    )
    per_project_replacements: defaultdict[str, int] = field(
        default_factory=lambda: defaultdict(int),
    )


class FlextInfraWrapperRootNamespaceRefactor(
    FlextInfraProjectSelectionServiceBase[t.JsonPayload],
):
    """Refactor wrapper alias imports and deprecated ``*.Core.Tests`` paths."""

    _WRAPPER_PACKAGES: ClassVar[t.StrSequence] = tuple(
        segment
        for segment in c.Infra.ROOT_WRAPPER_SEGMENTS
        if segment != c.Infra.DEFAULT_SRC_DIR
    )

    include_init: Annotated[
        bool,
        m.Field(
            alias="include-init",
            description="Also process __init__.py files (default: false)",
        ),
    ] = False

    @override
    def execute(self) -> p.Result[t.JsonPayload]:
        """Discover wrapper files, rewrite ``Core.Tests`` chains, persist results."""
        scan = self._scan_workspace()
        if scan.failure:
            return r[t.JsonPayload].fail(scan.error or "wrapper scan failed")
        py_files, project_runtime_aliases, wrapper_submodules = scan.value
        accumulator = _WrapperRewriteAccumulator()
        metadata = u.read_project_constants("flext-infra")
        metadata_aliases = frozenset(metadata.RUNTIME_ALIAS_NAMES)
        for file_path in py_files:
            self._process_wrapper_file(
                file_path,
                accumulator=accumulator,
                project_runtime_aliases=project_runtime_aliases,
                wrapper_submodules=wrapper_submodules,
                metadata_runtime_aliases=metadata_aliases,
            )
        write_failure = self._persist_updates(accumulator.updates)
        if write_failure is not None:
            return r[t.JsonPayload].fail(write_failure)
        if not self.effective_dry_run and accumulator.wrapper_candidates:
            for wrapper in self._WRAPPER_PACKAGES:
                u.Infra.rewrite_import_violations(
                    py_files=accumulator.wrapper_candidates,
                    project_package=wrapper,
                )
        report_payload = self._build_report_payload(
            len(py_files),
            accumulator,
        )
        if self.check_only and accumulator.changed_files:
            return r[t.JsonPayload].fail(
                "pending wrapper-root namespace rewrites detected",
            )
        return r[t.JsonPayload].ok(report_payload)

    def _scan_workspace(
        self,
    ) -> p.Result[tuple[t.SequenceOf[Path], dict[str, frozenset[str]], frozenset[str]]]:
        """Resolve project paths and discover Python files + runtime alias map."""
        resolved = u.Infra.resolve_projects(
            self.workspace_root,
            self.project_names or (),
        )
        if resolved.failure:
            return r[
                tuple[t.SequenceOf[Path], dict[str, frozenset[str]], frozenset[str]]
            ].fail(resolved.error or "project resolution failed")
        iter_result = u.Infra.iter_python_files(
            self.workspace_root,
            project_roots=[project.path for project in resolved.value],
        )
        if iter_result.failure:
            return r[
                tuple[t.SequenceOf[Path], dict[str, frozenset[str]], frozenset[str]]
            ].fail(iter_result.error or "python file iteration failed")
        project_runtime_aliases = {
            project.path.name: frozenset(layout.runtime_aliases)
            for project in resolved.value
            if (layout := u.Infra.layout(project.path)) is not None
        }
        metadata = u.read_project_constants("flext-infra")
        return r[
            tuple[t.SequenceOf[Path], dict[str, frozenset[str]], frozenset[str]]
        ].ok(
            (
                iter_result.value,
                project_runtime_aliases,
                frozenset(metadata.FACADE_MODULE_NAMES),
            ),
        )

    def _process_wrapper_file(
        self,
        file_path: Path,
        *,
        accumulator: _WrapperRewriteAccumulator,
        project_runtime_aliases: Mapping[str, frozenset[str]],
        wrapper_submodules: frozenset[str],
        metadata_runtime_aliases: frozenset[str],
    ) -> None:
        """Detect Core.Tests chain rewrites and import candidates for one file."""
        try:
            rel = file_path.relative_to(self.workspace_root)
        except ValueError:
            rel = file_path
        project_name = rel.parts[0] if rel.parts else "."
        runtime_aliases = project_runtime_aliases.get(
            project_name,
            metadata_runtime_aliases,
        )
        if not any(
            part in c.Infra.ROOT_WRAPPER_SEGMENTS and part != c.Infra.DEFAULT_SRC_DIR
            for part in rel.parts
        ):
            return
        if file_path.name == c.Infra.INIT_PY and (not self.include_init):
            return
        source = file_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return
        module_ast = pymodule.get_ast()
        line_offsets = self._build_line_offsets(source)
        core_rewrites = self._collect_core_test_rewrites(
            module_ast,
            line_offsets=line_offsets,
            runtime_aliases=runtime_aliases,
        )
        has_import_candidate = self._has_wrapper_import_candidate(
            module_ast,
            wrapper_submodules=wrapper_submodules,
            runtime_aliases=runtime_aliases,
        )
        replacements = len(core_rewrites) + (1 if has_import_candidate else 0)
        if replacements == 0:
            return
        core_updated = self._apply_byte_rewrites(source, core_rewrites)
        accumulator.changed_files.append(str(file_path))
        accumulator.total_replacements += replacements
        accumulator.total_core_replacements += len(core_rewrites)
        if has_import_candidate:
            accumulator.import_rewrite_candidates += 1
            accumulator.wrapper_candidates.append(file_path)
        accumulator.per_project_changes[project_name] += 1
        accumulator.per_project_replacements[project_name] += replacements
        if not self.effective_dry_run and core_updated != source:
            accumulator.updates[file_path] = core_updated

    @staticmethod
    def _build_line_offsets(source: str) -> list[int]:
        """Return cumulative line-start byte offsets for ``source``."""
        line_offsets = [0]
        for line_text in source.splitlines(keepends=True):
            line_offsets.append(line_offsets[-1] + len(line_text))
        return line_offsets

    def _collect_core_test_rewrites(
        self,
        module_ast: object,
        *,
        line_offsets: list[int],
        runtime_aliases: frozenset[str],
    ) -> list[tuple[int, int, str]]:
        """Find every ``<alias>.Core.Tests`` chain and emit ``(start, end, repl)``."""
        rewrites: list[tuple[int, int, str]] = []
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(module_ast):
            if (
                FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "Attribute"
                or getattr(node, "attr", "") != "Tests"
            ):
                continue
            parent_attr = getattr(node, "value", None)
            if (
                parent_attr is None
                or FlextInfraUtilitiesRopeAnalysis.node_kind(parent_attr) != "Attribute"
                or getattr(parent_attr, "attr", "") != "Core"
            ):
                continue
            base_name = getattr(parent_attr, "value", None)
            if (
                base_name is None
                or FlextInfraUtilitiesRopeAnalysis.node_kind(base_name) != "Name"
            ):
                continue
            base_id = getattr(base_name, "id", "")
            if base_id not in runtime_aliases:
                continue
            line_col = FlextInfraUtilitiesRopeAnalysis.line_col_range(node)
            if line_col is None:
                continue
            lineno, col_offset, end_lineno, end_col_offset = line_col
            start = line_offsets[lineno - 1] + col_offset
            end = line_offsets[end_lineno - 1] + end_col_offset
            rewrites.append((start, end, f"{base_id}.Tests"))
        return rewrites

    def _has_wrapper_import_candidate(
        self,
        module_ast: object,
        *,
        wrapper_submodules: frozenset[str],
        runtime_aliases: frozenset[str],
    ) -> bool:
        """Return whether any ``from wrapper.<sub> import <alias>`` exists."""
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(module_ast):
            if FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "ImportFrom":
                continue
            module_name = getattr(node, "module", "") or ""
            parent, dot, child = module_name.partition(".")
            if not (
                dot and parent in self._WRAPPER_PACKAGES and child in wrapper_submodules
            ):
                continue
            names = getattr(node, "names", []) or []
            if any(
                (getattr(alias, "asname", None) or getattr(alias, "name", ""))
                in runtime_aliases
                for alias in names
            ):
                return True
        return False

    @staticmethod
    def _apply_byte_rewrites(
        source: str,
        rewrites: t.SequenceOf[tuple[int, int, str]],
    ) -> str:
        """Apply ``(start, end, replacement)`` triples to ``source`` (right-to-left)."""
        updated = source
        for start, end, replacement in sorted(
            rewrites, key=itemgetter(0), reverse=True
        ):
            updated = updated[:start] + replacement + updated[end:]
        return updated

    def _persist_updates(self, updates: Mapping[Path, str]) -> str | None:
        """Write batched updates via the protected pipeline; ``None`` on success."""
        if not updates:
            return None
        ok, report = u.Infra.protected_source_writes(
            dict(updates),
            request=m.Infra.ProtectedSourceWritesRequest(
                workspace=self.workspace_root,
                skip_pytest=True,
            ),
        )
        if ok:
            return None
        return " ; ".join(report[:5]) or "protected write failed"

    def _build_report_payload(
        self,
        files_scanned: int,
        accumulator: _WrapperRewriteAccumulator,
    ) -> t.MutableJsonMapping:
        """Build the canonical JSON payload from the accumulated wrapper run state."""
        mode_value = (
            "check"
            if self.check_only
            else "dry-run"
            if self.effective_dry_run
            else "apply"
        )
        per_project_changes_payload: t.JsonDict = dict(
            accumulator.per_project_changes.items()
        )
        per_project_replacements_payload: t.JsonDict = dict(
            accumulator.per_project_replacements.items()
        )
        changed_files_preview: t.JsonValueList = list(accumulator.changed_files[:200])
        report_payload: t.MutableJsonMapping = {
            "files_scanned": files_scanned,
            "files_changed": len(accumulator.changed_files),
            "replacements": accumulator.total_replacements,
            "core_tests_replacements": accumulator.total_core_replacements,
            "import_rewrite_candidates": accumulator.import_rewrite_candidates,
            "per_project_changes": per_project_changes_payload,
            "per_project_replacements": per_project_replacements_payload,
            "changed_files_preview": changed_files_preview,
            "workspace": str(self.workspace_root),
            "mode": mode_value,
        }
        return report_payload


__all__: list[str] = ["FlextInfraWrapperRootNamespaceRefactor"]
