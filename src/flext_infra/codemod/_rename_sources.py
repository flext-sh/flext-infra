"""Authenticated input and explicitly declared text surfaces for CSV campaigns.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraStagedPackage


class FlextInfraRenameSources:
    """Read campaign data and source snapshots without granting write effects."""

    @staticmethod
    def rename_selections(
        artifact: m.Infra.SemanticRenamePlan,
    ) -> m.Infra.SemanticRenameSelections:
        """Reconstruct execution intent without treating artifacts as rule authority.

        Returns:
            The original typed native selections and elected consumers.

        """
        return m.Infra.SemanticRenameSelections(
            decisions=tuple(
                m.Infra.SemanticRenameSelection(
                    qualified_name=".".join(
                        part
                        for part in (
                            item.declaration.module_name,
                            item.declaration.scope_path,
                        )
                        if part
                    ),
                    replacement_name=item.replacement_name,
                    reason=item.reason,
                    contracts=tuple(
                        f"{part.module_name}.{part.scope_path}"
                        for part in item.contracts
                    ),
                )
                for item in artifact.decisions
            ),
            consumer_roots=artifact.consumer_roots,
        )

    @staticmethod
    def compose_candidate[PlanT: m.Infra.SemanticSourcePlan](
        candidate: PlanT,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[PlanT]:
        """Fold phase effects without replacing their physical originals.

        Returns:
            The staged view with the union of original source witnesses.
            The first original planning exception escapes unchanged.

        """
        if analysis.exception is not None:
            raise analysis.exception
        if analysis.issues:
            return r[PlanT].fail("; ".join(issue.message for issue in analysis.issues))
        known = {
            state.path: state
            for state in m.Infra.CodemodBindingSnapshot(
                states=(*candidate.candidate.inputs, *candidate.source_states)
            ).states
        }
        updates = dict(candidate.candidate.updates)
        modes = dict(candidate.candidate.modes)
        effect_states: list[m.Cli.AtomicFileState] = []
        for effect in analysis.files:
            before = effect.before
            if not isinstance(before, m.Cli.AtomicFileState):
                return r[PlanT].fail(
                    f"phase effect lost its original file evidence: {effect.path}"
                )
            if before != known.setdefault(effect.path, before):
                return r[PlanT].fail(
                    f"phase replaced original physical evidence: {effect.path}"
                )
            effect_states.append(before)
            updates[effect.path] = (
                None
                if effect.desired_content is None
                else effect.desired_content.decode(c.DEFAULT_ENCODING)
            )
            if effect.desired_content is None:
                modes.pop(effect.path, None)
            elif effect.desired_mode is not None:
                modes[effect.path] = effect.desired_mode
        captured = m.Infra.CodemodBindingSnapshot(
            states=(
                *candidate.candidate.inputs,
                *candidate.source_states,
                *analysis.inputs,
                *effect_states,
                *(state for effect in analysis.files for state in effect.source_states),
            )
        )
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            (
                *candidate.candidate.source_directories,
                *candidate.source_directories,
                *analysis.source_directories,
                *(
                    item
                    for effect in analysis.files
                    for item in effect.source_directories
                ),
            ),
            (
                *candidate.candidate.source_query_topology,
                *candidate.source_query_topology,
                *analysis.source_query_topology,
                *(
                    item
                    for effect in analysis.files
                    for item in effect.source_query_topology
                ),
            ),
        )
        return FlextInfraStagedPackage.plan_sources(
            candidate.candidate.workspace,
            updates,
            options=m.Infra.StageSourceOptions(
                inputs=captured.states,
                workspaces=candidate.candidate.workspaces,
                modes=modes,
                source_directories=directories,
                source_query_topology=topology,
            ),
        ).map(
            lambda stage: candidate.model_copy(
                update={
                    "candidate": stage,
                    "source_states": captured.states,
                    "source_directories": stage.source_directories,
                    "source_query_topology": stage.source_query_topology,
                }
            )
        )

    @staticmethod
    def symbol_paths(
        sources: t.MappingKV[Path, str],
        symbols: frozenset[str],
    ) -> frozenset[Path]:
        """Elect actual identifier syntax, never executable string payloads.

        Returns:
            Candidate paths whose bindings must still be resolved by Rope.

        """
        selected: set[Path] = set()
        for path, source in sources.items():
            for node in ast.walk(ast.parse(source, filename=str(path))):
                match node:
                    case (
                        ast.Name(id=name)
                        | ast.Attribute(attr=name)
                        | ast.ClassDef(name=name)
                        | ast.FunctionDef(name=name)
                        | ast.AsyncFunctionDef(name=name)
                        | ast.arg(arg=name)
                        | ast.keyword(arg=name)
                    ):
                        found = name in symbols
                    case ast.alias(name=imported, asname=local):
                        found = local in symbols or bool(
                            symbols.intersection(imported.split("."))
                        )
                    case ast.ImportFrom(module=module) if module is not None:
                        found = bool(symbols.intersection(module.split(".")))
                    case _:
                        found = False
                if found:
                    selected.add(path)
                    break
        return frozenset(selected)

    @staticmethod
    def pairs(source: str) -> t.VariadicTuple[t.Pair[str, str]]:
        rows = u.Cli.csv_loads(source).unwrap()
        if not rows or rows[0] != ["old", "new"]:
            msg = "rename CSV header must be exactly 'old,new'"
            raise ValueError(msg)
        pairs: t.MutableMappingKV[str, str] = {}
        for row in rows[1:]:
            if len(row) != len(rows[0]) or not all(value.strip() for value in row):
                msg = "every row must contain non-empty old,new values"
                raise ValueError(msg)
            old, new = (value.strip() for value in row)
            if old == new or (old in pairs and pairs[old] != new):
                msg = f"rename CSV contains identity or conflicting duplicate: {old}"
                raise ValueError(msg)
            pairs[old] = new
        if not pairs:
            msg = "rename CSV must declare at least one change"
            raise ValueError(msg)
        for old, new in pairs.items():
            for other in pairs:
                pattern = rf"\b{re.escape(other)}\b"
                if re.search(pattern, new) or (
                    old != other and re.search(pattern, old)
                ):
                    msg = (
                        f"rename CSV contains overlapping or cascading mappings: "
                        f"{old}, {other}"
                    )
                    raise ValueError(msg)
        return tuple(sorted(pairs.items()))

    @staticmethod
    def _rooted_symlink(path: Path, roots: t.SequenceOf[Path]) -> bool:
        """Authorize an in-tree symlink target and mark the link projected.

        Returns:
            Whether ``path`` is a symlink whose target stays inside the
            declared scan roots.

        Raises:
            ValueError: If the symlink target escapes the declared scan roots.

        """
        if not path.is_symlink():
            return False
        destination = path.resolve(strict=True)
        if not any(
            destination.is_relative_to(candidate.resolve()) for candidate in roots
        ):
            msg = f"rename source escapes declared scan roots: {path}"
            raise ValueError(msg)
        # The target is the writable authority; an in-tree link
        # remains a projection and is never an atomic destination.
        return True

    @staticmethod
    def inventory(
        roots: t.SequenceOf[Path],
        params: m.Infra.ApplyRenamesInput,
    ) -> t.MappingKV[Path, m.Cli.AtomicFileState]:
        """Index scanned files minus ignored, generated, and driver paths.

        Returns:
            The authenticated file states of every electable rename source.

        Raises:
            ValueError: If a rename source disappeared or escapes the scan roots.

        """
        files: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        configuration_root = params.repository_root
        codegen = u.Infra.load_codegen_inputs(configuration_root).unwrap().spec
        ignored = codegen.source_scan_ignored
        generated = {item.path for item in codegen.managed_file_specs}
        templates = u.Infra.codegen_template_sources(codegen)
        drivers = {
            Path(params.csv).resolve(),
            *(
                (configuration_root / c.CONFIG_DIR_NAME / campaign.csv).resolve()
                for campaign in u.Infra
                .load_refactor_csv_campaigns(
                    configuration_root,
                )
                .unwrap()
                .campaigns
            ),
        }
        for root in roots:
            paths = u.Infra.git_tracked_scope_paths(root)
            candidates = root.rglob("*") if paths is None else paths
            for path in sorted(candidates):
                relative = path.relative_to(root)
                if (
                    not path.is_file()
                    or path.resolve() in drivers
                    or relative in generated
                    or any(part in ignored for part in relative.parts)
                    or any(
                        relative.full_match(pattern) for pattern in params.exclude_globs
                    )
                ):
                    continue
                python = path.suffix == c.Infra.EXT_PYTHON
                text = any(
                    relative.full_match(pattern) for pattern in params.text_globs
                )
                if not python and not text:
                    continue
                if FlextInfraRenameSources._rooted_symlink(path, roots):
                    continue
                state = u.Cli.atomic_read_binary_file_state(
                    path,
                    required=True,
                ).unwrap()
                if state.content is None:
                    msg = f"rename source disappeared: {path}"
                    raise ValueError(msg)
                source = state.content.decode(c.DEFAULT_ENCODING)
                if (
                    source.startswith(c.Infra.AUTOGEN_HEADERS)
                    and path.resolve() not in templates
                ):
                    continue
                if path.suffix.lower() == ".csv" and u.Cli.csv_loads(source).unwrap()[
                    :1
                ] == [["old", "new"]]:
                    continue
                files[path.absolute()] = state
        return files

    @staticmethod
    def text_edits(
        source: str,
        pairs: t.SequenceOf[t.Pair[str, str]],
        *,
        start: int = 0,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        replacements = dict(pairs)
        pattern = re.compile(
            r"\b(?:" + "|".join(re.escape(old) for old in replacements) + r")\b",
        )
        return tuple(
            m.Infra.SourceRewrite(
                start=start + match.start(),
                end=start + match.end(),
                text=replacements[match.group()],
            )
            for match in pattern.finditer(source)
        )

    @classmethod
    def documentation_edits(
        cls,
        source: str,
        pairs: t.SequenceOf[t.Pair[str, str]],
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        """Select real docstrings and comments; executable literals retain bytes.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SourceRewrite]``.

        Raises:
            ValueError: If Python docstring lacks an authenticated source span.

        """
        lines = source.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        tree = ast.parse(source)
        docstrings: t.MutableSequenceOf[t.Pair[t.Pair[int, int], t.Pair[int, int]]] = []
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue
            if not node.body or not isinstance(node.body[0], ast.Expr):
                continue
            value = node.body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                column = len(
                    lines[value.lineno - 1]
                    .encode(c.DEFAULT_ENCODING)[: value.col_offset]
                    .decode(c.DEFAULT_ENCODING),
                )
                if value.end_lineno is None or value.end_col_offset is None:
                    msg = "Python docstring lacks an authenticated source span"
                    raise ValueError(msg)
                end_column = len(
                    lines[value.end_lineno - 1]
                    .encode(c.DEFAULT_ENCODING)[: value.end_col_offset]
                    .decode(c.DEFAULT_ENCODING),
                )
                docstrings.append((
                    (value.lineno, column),
                    (value.end_lineno, end_column),
                ))
        edits: t.MutableSequenceOf[m.Infra.SourceRewrite] = []
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT or (
                token.type == tokenize.STRING
                and any(
                    start <= token.start and token.end <= end
                    for start, end in docstrings
                )
            ):
                edits.extend(
                    cls.text_edits(
                        token.string,
                        pairs,
                        start=offsets[token.start[0] - 1] + token.start[1],
                    ),
                )
        return tuple(edits)


__all__: list[str] = ["FlextInfraRenameSources"]
