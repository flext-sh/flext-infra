"""Wrapper-root namespace refactor command for tests/examples/scripts aliases."""

from __future__ import annotations

import ast
from collections import defaultdict
from operator import itemgetter
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraWrapperRootNamespaceRefactor(
    FlextInfraProjectSelectionServiceBase[t.JsonPayload],
):
    """Refactor wrapper alias imports and deprecated ``*.Core.Tests`` paths."""

    _WRAPPER_PACKAGES: ClassVar[tuple[str, ...]] = tuple(
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
        resolved = u.Infra.resolve_projects(
            self.workspace_root,
            self.project_names or (),
        )
        if resolved.failure:
            return r[t.JsonPayload].fail(
                resolved.error or "project resolution failed",
            )

        iter_result = u.Infra.iter_python_files(
            self.workspace_root,
            project_roots=[project.path for project in resolved.value],
        )
        if iter_result.failure:
            return r[t.JsonPayload].fail(
                iter_result.error or "python file iteration failed",
            )

        project_runtime_aliases = {
            project.path.name: frozenset(layout.runtime_aliases)
            for project in resolved.value
            if (layout := u.Infra.layout(project.path)) is not None
        }

        updates: dict[Path, str] = {}
        wrapper_candidates: list[Path] = []
        changed_files: list[str] = []
        total_replacements = 0
        total_core_replacements = 0
        import_rewrite_candidates = 0
        per_project_changes: dict[str, int] = defaultdict(int)
        per_project_replacements: dict[str, int] = defaultdict(int)
        wrapper_submodules = c.FACADE_MODULE_NAMES

        for file_path in iter_result.value:
            try:
                rel = file_path.relative_to(self.workspace_root)
            except ValueError:
                rel = file_path
            project_name = rel.parts[0] if rel.parts else "."
            runtime_aliases = project_runtime_aliases.get(
                project_name,
                frozenset(c.RUNTIME_ALIAS_NAMES),
            )
            if not any(
                part in c.Infra.ROOT_WRAPPER_SEGMENTS
                and part != c.Infra.DEFAULT_SRC_DIR
                for part in rel.parts
            ):
                continue
            if file_path.name == c.Infra.INIT_PY and (not self.include_init):
                continue

            source = file_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            module_ast = ast.parse(source)
            line_offsets = [0]
            for line_text in source.splitlines(keepends=True):
                line_offsets.append(line_offsets[-1] + len(line_text))
            core_rewrites: list[tuple[int, int, str]] = []
            has_import_candidate = False
            for node in ast.walk(module_ast):
                if isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""
                    parent, dot, child = module_name.partition(".")
                    if (
                        dot
                        and parent in self._WRAPPER_PACKAGES
                        and child in wrapper_submodules
                        and any(
                            (alias.asname or alias.name) in runtime_aliases
                            for alias in node.names
                        )
                    ):
                        has_import_candidate = True
                if not isinstance(node, ast.Attribute) or node.attr != "Tests":
                    continue
                parent_attr = (
                    node.value if isinstance(node.value, ast.Attribute) else None
                )
                if parent_attr is None or parent_attr.attr != "Core":
                    continue
                base_name = (
                    parent_attr.value
                    if isinstance(parent_attr.value, ast.Name)
                    else None
                )
                if base_name is None or base_name.id not in runtime_aliases:
                    continue
                end_lineno = node.end_lineno
                end_col_offset = node.end_col_offset
                if end_lineno is None or end_col_offset is None:
                    continue
                start = line_offsets[node.lineno - 1] + node.col_offset
                end = line_offsets[end_lineno - 1] + end_col_offset
                core_rewrites.append((start, end, f"{base_name.id}.Tests"))
            core_count = len(core_rewrites)
            core_updated = source
            for start, end, replacement in sorted(
                core_rewrites,
                key=itemgetter(0),
                reverse=True,
            ):
                core_updated = core_updated[:start] + replacement + core_updated[end:]
            replacements = core_count + (1 if has_import_candidate else 0)
            if replacements == 0:
                continue

            changed_files.append(str(file_path))
            total_replacements += replacements
            total_core_replacements += core_count
            if has_import_candidate:
                import_rewrite_candidates += 1
                wrapper_candidates.append(file_path)
            per_project_changes[project_name] += 1
            per_project_replacements[project_name] += replacements
            if not self.effective_dry_run and core_updated != source:
                updates[file_path] = core_updated

        if updates:
            ok, report = u.Infra.protected_source_writes(
                updates,
                workspace=self.workspace_root,
                skip_pytest=True,
            )
            if not ok:
                snippet = " ; ".join(report[:5]) or "protected write failed"
                return r[t.JsonPayload].fail(snippet)

        if not self.effective_dry_run and wrapper_candidates:
            for wrapper in self._WRAPPER_PACKAGES:
                u.Infra.rewrite_import_violations(
                    py_files=wrapper_candidates,
                    project_package=wrapper,
                )

        per_project_changes_payload: dict[str, t.JsonValue] = {  # noqa: C416
            project: count for project, count in per_project_changes.items()
        }
        per_project_replacements_payload: dict[str, t.JsonValue] = {  # noqa: C416
            project: count for project, count in per_project_replacements.items()
        }
        changed_files_preview: list[t.JsonValue] = [  # noqa: C416
            entry for entry in changed_files[:200]
        ]
        mode_value = (
            "check"
            if self.check_only
            else "dry-run"
            if self.effective_dry_run
            else "apply"
        )
        report_payload: t.MutableJsonMapping = {
            "files_scanned": len(iter_result.value),
            "files_changed": len(changed_files),
            "replacements": total_replacements,
            "core_tests_replacements": total_core_replacements,
            "import_rewrite_candidates": import_rewrite_candidates,
            "per_project_changes": per_project_changes_payload,
            "per_project_replacements": per_project_replacements_payload,
            "changed_files_preview": changed_files_preview,
            "workspace": str(self.workspace_root),
            "mode": mode_value,
        }

        if self.check_only and changed_files:
            return r[t.JsonPayload].fail(
                "pending wrapper-root namespace rewrites detected",
            )

        return r[t.JsonPayload].ok(report_payload)


__all__: list[str] = ["FlextInfraWrapperRootNamespaceRefactor"]
