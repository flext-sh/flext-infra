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


class FlextInfraCodemodRenameSources:
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
    def compose_candidate(
        candidate: m.Infra.SemanticSourcePlan,
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Fold phase file plans into the staged candidate view.

        Returns:
            The candidate carrying every phase effect over the union of the
            original observations, or the first effect planned on other bytes.

        """
        known = {state.path: state for state in candidate.candidate.inputs}
        updates = dict(candidate.candidate.updates)
        modes = dict(candidate.candidate.modes)
        for effect in plans:
            if effect.before != known.setdefault(effect.path, effect.before):
                return r[m.Infra.SemanticSourcePlan].fail(
                    f"phase replaced original physical evidence: {effect.path}"
                )
            if effect.desired_content is None:
                updates[effect.path] = None
                modes.pop(effect.path, None)
                continue
            updates[effect.path] = effect.desired_content.decode(c.DEFAULT_ENCODING)
            if effect.desired_mode is not None:
                modes[effect.path] = effect.desired_mode
        return FlextInfraStagedPackage.plan_sources(
            candidate.candidate.workspace,
            updates,
            options=m.Infra.StageSourceOptions(
                workspaces=candidate.candidate.workspaces,
                modes=modes,
                inputs=tuple(known.values()),
            ),
        ).map(
            lambda stage: m.Infra.SemanticSourcePlan(
                candidate=stage, consumer_roots=candidate.consumer_roots
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
        *,
        needles: frozenset[str] | None = None,
        python_sources: bool = True,
    ) -> t.Pair[t.MappingKV[Path, m.Cli.AtomicFileState], int]:
        """Index scanned files minus ignored, generated, and driver paths.

        ``needles`` bounds the authenticated reads of an identifier campaign to
        the Python files whose bytes contain one of the retired identifiers: an
        identifier match in the syntax tree requires that substring, so every
        other file is neither read authenticated nor planned. Without
        ``python_sources`` only the declared text surfaces are indexed; the
        workspace snapshot owns the Python sources.

        Returns:
            The authenticated file states of every electable rename source and
            the number of electable files scanned.

        """
        files: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        scanned = 0
        raw_needles = tuple(
            needle.encode(c.DEFAULT_ENCODING) for needle in needles or ()
        )
        exclusions = FlextInfraCodemodRenameSources.exclusions(params)
        for root in roots:
            paths = u.Infra.git_source_scope_paths(root)
            for path in sorted(root.rglob("*") if paths is None else paths):
                if not python_sources and path.suffix == c.Infra.EXT_PYTHON:
                    continue
                if not FlextInfraCodemodRenameSources._electable(
                    path, root, roots, params, exclusions
                ):
                    continue
                scanned += 1
                if needles is not None and not any(
                    needle in path.read_bytes() for needle in raw_needles
                ):
                    continue
                state = FlextInfraCodemodRenameSources._source_state(
                    path, exclusions[2]
                )
                if state is not None:
                    files[path.absolute()] = state
        return files, scanned

    @staticmethod
    def exclusions(
        params: m.Infra.ApplyRenamesInput,
    ) -> t.Triple[t.Pair[frozenset[str], set[Path]], frozenset[Path], frozenset[Path]]:
        """Resolve the declared exclusions every inventory pass shares.

        Returns:
            The ignored names with generated paths, the campaign drivers and
            the manifest-declared template sources.

        """
        configuration_root = params.repository_root
        codegen = u.Infra.load_codegen_inputs(configuration_root).unwrap().spec
        drivers = frozenset({
            Path(params.csv).resolve(),
            *(
                (configuration_root / c.CONFIG_DIR_NAME / campaign.csv).resolve()
                for campaign in u.Infra
                .load_refactor_csv_campaigns(configuration_root)
                .unwrap()
                .campaigns
            ),
        })
        return (
            (
                frozenset(codegen.source_scan_ignored),
                {item.path for item in codegen.managed_file_specs},
            ),
            drivers,
            frozenset(u.Infra.codegen_template_sources(codegen)),
        )

    @staticmethod
    def _electable(
        path: Path,
        root: Path,
        roots: t.SequenceOf[Path],
        params: m.Infra.ApplyRenamesInput,
        exclusions: t.Triple[
            t.Pair[frozenset[str], set[Path]], frozenset[Path], frozenset[Path]
        ],
    ) -> bool:
        """Whether one scoped path is a rename source under the declared surfaces.

        Returns:
            True when the path is neither excluded nor outside the surfaces.

        """
        (ignored, generated), drivers, _templates = exclusions
        python = path.suffix == c.Infra.EXT_PYTHON
        if not python and not params.text_globs:
            return False
        relative = path.relative_to(root)
        if not python and not any(
            relative.full_match(pattern) for pattern in params.text_globs
        ):
            return False
        if (
            not path.is_file()
            or path.resolve() in drivers
            or relative in generated
            or any(part in ignored for part in relative.parts)
            or any(relative.full_match(pattern) for pattern in params.exclude_globs)
        ):
            return False
        return not FlextInfraCodemodRenameSources._rooted_symlink(path, roots)

    @staticmethod
    def _source_state(
        path: Path,
        templates: frozenset[Path],
    ) -> m.Cli.AtomicFileState | None:
        """Authenticate one rename source, skipping generated and driver data.

        Returns:
            The authenticated state, or ``None`` for a generated projection or a
            rename-list driver.

        Raises:
            ValueError: If the rename source disappeared.

        """
        state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        if state.content is None:
            msg = f"rename source disappeared: {path}"
            raise ValueError(msg)
        source = state.content.decode(c.DEFAULT_ENCODING)
        if (
            source.startswith(c.Infra.AUTOGEN_HEADER)
            and path.resolve() not in templates
        ):
            return None
        if path.suffix.lower() == ".csv" and u.Cli.csv_loads(source).unwrap()[:1] == [
            ["old", "new"]
        ]:
            return None
        return state

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
            if not isinstance(node, c.Infra.AST_SCOPE_OWNER_TYPES):
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


__all__: list[str] = ["FlextInfraCodemodRenameSources"]
