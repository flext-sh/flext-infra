"""Codegen CLI consolidate handler mixin."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
    u,
)

__all__ = ["FlextInfraCliCodegenConsolidate"]


class FlextInfraCliCodegenConsolidate:
    """Mixin providing the consolidate command handler."""

    @staticmethod
    def _handle_consolidate(params: m.Infra.CodegenConsolidateInput) -> r[str]:
        """Consolidate inline constants into ``c.*`` references.

        Dynamically resolves each project's namespace via rope MRO — no
        hardcoded namespace assumptions.  Validates each file after
        replacement and reverts on lint failure.
        """
        workspace = Path(params.workspace).resolve()
        dry_run = not params.apply
        lines: list[str] = []
        if dry_run:
            lines.append("[DRY-RUN] Scanning for inline canonicals...\n")

        # Discover projects via existing SSOT API
        projects_result = u.Infra.discover_projects(workspace)
        if projects_result.is_failure:
            return r[str].fail("Failed to discover projects")
        projects: Sequence[m.Infra.ProjectInfo] = projects_result.value
        if params.project:
            projects = [p for p in projects if p.name == params.project]

        total_found = 0
        total_applied = 0
        total_failed = 0
        file_results: list[dict[str, t.Infra.InfraValue]] = []

        for project in projects:
            project_root = workspace / project.name
            src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
            if not src_dir.is_dir():
                continue
            pkg_name = project.name.replace("-", "_")
            pkg_dir = src_dir / pkg_name
            if not pkg_dir.is_dir():
                continue

            # ── Dynamic namespace resolution ─────────────────────
            aliases = u.Infra.discover_project_aliases(project_root)
            if "c" not in aliases:
                continue

            # Find the project's constants facade via runtime import
            # (rope can't parse constants.py due to lazy import chains)
            constants_file = pkg_dir / c.Infra.Files.CONSTANTS_PY
            if not constants_file.is_file():
                continue
            try:
                pkg_module = importlib.import_module(pkg_name)
            except (ImportError, ModuleNotFoundError):
                continue
            # Find the Constants facade class in the module
            # The facade's __module__ is <pkg>.constants, not <pkg>
            facade_cls: type | None = None
            expected_module = f"{pkg_name}.constants"
            for attr in vars(pkg_module).values():
                if (
                    isinstance(attr, type)
                    and getattr(attr, "__module__", "") == expected_module
                    and "Constants" in attr.__name__
                    and len(attr.__name__) > 1
                ):
                    facade_cls = attr
                    break
            if facade_cls is None:
                continue

            # ── Build canonical value map from runtime MRO ─────
            value_to_ref: dict[str, tuple[str, str]] = {}
            # Walk the facade and its inner classes
            cls_targets: list[tuple[type, str]] = [(facade_cls, "")]
            cls_targets.extend(
                (attr, attr.__name__)
                for attr in dict(vars(facade_cls)).values()
                if isinstance(attr, type) and attr is not type
            )

            for target_cls, prefix in cls_targets:
                for klass in reversed(target_cls.__mro__):
                    if klass is object:
                        continue
                    klass_vars = dict(vars(klass))
                    for attr_name, attr_value in klass_vars.items():
                        if attr_name.startswith("_"):
                            continue
                        if isinstance(attr_value, type):
                            continue
                        raw = repr(attr_value)[:200]
                        if not raw:
                            continue
                        canon_path = f"{prefix}.{attr_name}" if prefix else attr_name
                        entry = (canon_path, "")
                        value_to_ref[raw] = entry
                        # Normalize string quotes
                        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:  # noqa: PLR2004
                            inner = raw[1:-1]
                            value_to_ref[f"'{inner}'"] = entry
                            value_to_ref[f'"{inner}"'] = entry

            # ── Init rope project for this project ────────────────
            rope_project = FlextInfraUtilitiesRope.init_rope_project(
                project_root,
            )

            for py_file in sorted(
                pkg_dir.rglob(c.Infra.Extensions.PYTHON_GLOB),
            ):
                if c.Infra.Dunders.PYCACHE in py_file.parts:
                    continue
                if "_constants" in py_file.parts:
                    continue  # SSOT files — never rewrite

                # ── Detect assignments via rope semantic analysis ──
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    py_file,
                )
                if resource is None:
                    continue
                symbols = FlextInfraUtilitiesRope.get_module_symbols(
                    rope_project,
                    resource,
                )
                assignments = [sym for sym in symbols if sym.kind == "assignment"]
                if not assignments:
                    continue

                source = FlextInfraUtilitiesRope.read_source(resource)
                source_lines = source.splitlines()

                # ── Match assignment values against canonical map ──
                # Skip trivial values that cause false positives
                trivial_values: frozenset[str] = frozenset({
                    "True",
                    "False",
                    "None",
                    "0",
                    "1",
                    "-1",
                    '""',
                    "''",
                    "[]",
                    "{}",
                    "()",
                })
                matches: list[
                    tuple[m.Infra.SymbolInfo, str, str]
                ] = []  # (symbol, canonical_ref, value_repr)
                for sym in assignments:
                    if sym.line < 1 or sym.line > len(source_lines):
                        continue
                    line_text = source_lines[sym.line - 1]
                    eq_idx = line_text.find("=")
                    if eq_idx < 0:
                        continue
                    raw_value = line_text[eq_idx + 1 :].strip()
                    if raw_value in trivial_values:
                        continue
                    hit = value_to_ref.get(raw_value)
                    if hit is None:
                        continue
                    canon_name, canon_class = hit
                    if canon_name == sym.name:
                        continue  # Already canonical
                    # Require semantic name similarity to avoid
                    # false positives on coincidental numeric values
                    if (
                        FlextInfraUtilitiesCodegenConstantDetection.semantic_name_matches(
                            sym.name, canon_name
                        )
                        or sym.name.isupper()
                    ):
                        ref = (
                            f"c.{canon_class}.{canon_name}"
                            if canon_class
                            else f"c.{canon_name}"
                        )
                        matches.append((sym, ref, raw_value))

                if not matches:
                    continue
                total_found += len(matches)
                rel = py_file.relative_to(workspace)

                # ── Phase 1: dry-run report ───────────────────────
                if dry_run:
                    for sym, ref, val in matches:
                        lines.append(
                            f"  {rel}:{sym.line}  {sym.name} = {val} -> {ref}",
                        )
                    continue

                # ── Phase 2: apply via rope + validate + rollback ─
                backup = source
                source_with_newlines = backup.splitlines(keepends=True)

                offset_edits: list[tuple[int, int, str]] = []
                descriptions: list[str] = []
                for sym, ref, val in matches:
                    if sym.line < 1 or sym.line > len(source_with_newlines):
                        continue
                    line_text = source_with_newlines[sym.line - 1]
                    eq_idx = line_text.find("=")
                    if eq_idx < 0:
                        continue
                    line_offset = sum(
                        len(source_with_newlines[i]) for i in range(sym.line - 1)
                    )
                    value_start = line_offset + eq_idx + 1
                    value_end = value_start + len(
                        line_text[eq_idx + 1 :].rstrip(),
                    )
                    offset_edits.append((value_start, value_end, f" {ref}"))
                    descriptions.append(
                        f"{sym.name} = {val} -> {ref}",
                    )

                if not offset_edits:
                    continue

                FlextInfraUtilitiesRope.rewrite_source_at_offsets(
                    rope_project,
                    resource,
                    offset_edits,
                    apply=True,
                )
                # Ensure the 'c' alias import exists
                FlextInfraUtilitiesRope.add_import(
                    rope_project,
                    resource,
                    pkg_name,
                    ["c"],
                    apply=True,
                )

                # ── Validate with linters ─────────────────────────
                ok = True
                for tool_cmd in (
                    [
                        "ruff",
                        "check",
                        str(py_file),
                        "--no-fix",
                        "--select",
                        "E,F",
                    ],
                    ["pyright", str(py_file)],
                ):
                    check_result = u.Infra.run_raw(
                        tool_cmd,
                        cwd=workspace,
                        timeout=c.Infra.Timeouts.SHORT,
                    )
                    if check_result.is_failure:
                        continue
                    if check_result.value.exit_code != 0:
                        ok = False
                        out = (check_result.value.stdout + check_result.value.stderr)[
                            :200
                        ]
                        lines.append(
                            f"  FAILED {rel} [{tool_cmd[0]}]: {out}",
                        )
                        break

                if not ok:
                    FlextInfraUtilitiesRope.write_source(
                        rope_project,
                        resource,
                        backup,
                    )
                    total_failed += 1
                    file_results.append({
                        "file": str(rel),
                        "status": "reverted",
                        "changes": descriptions,
                    })
                else:
                    total_applied += len(descriptions)
                    lines.extend(f"  APPLIED {rel}: {d}" for d in descriptions)
                    file_results.append({
                        "file": str(rel),
                        "status": "applied",
                        "changes": descriptions,
                    })

        # ── Summary ───────────────────────────────────────────────
        lines.append("")
        if dry_run:
            lines.append(
                f"Found {total_found} canonical matches"
                f" across {len(projects)} projects",
            )
        else:
            lines.append(
                f"Applied {total_applied} replacements, {total_failed} files reverted",
            )

        if params.output_format == "json":
            text = t.Infra.CONTAINER_MAPPING_ADAPTER.dump_json({
                "total_found": total_found,
                "total_applied": total_applied,
                "total_failed": total_failed,
                "files": file_results,
            }).decode()
            return r[str].ok(text)
        return r[str].ok("\n".join(lines))
