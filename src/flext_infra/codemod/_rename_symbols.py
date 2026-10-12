"""CSV symbol plans delegated to Rope's identity-aware restructuring owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from difflib import SequenceMatcher
from pathlib import Path

from flext_infra import m, p, t, u
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntime


class FlextInfraRenameSymbols:
    """Translate declared CSV prefixes into current-owner Rope constraints."""

    @staticmethod
    def _member_paths(source: str, path: Path) -> frozenset[tuple[str, ...]]:
        """Index AST attribute paths that can match a declared Rope pattern.

        Returns:
            The resulting ``frozenset[tuple[str, ...]]``.

        """
        paths: set[tuple[str, ...]] = set()
        for node in ast.walk(ast.parse(source, filename=str(path))):
            if not isinstance(node, ast.Attribute):
                continue
            parts: list[str] = []
            cursor: ast.expr = node
            while isinstance(cursor, ast.Attribute):
                parts.append(cursor.attr)
                paths.add(tuple(reversed(parts)))
                cursor = cursor.value
        return frozenset(paths)

    @staticmethod
    def resolve_member(
        project: p.Infra.RopeProject,
        owner: str,
        suffix: str,
    ) -> p.Infra.RopePyName | None:
        """Resolve the current destination without importing a retired object.

        Returns:
            The resulting ``p.Infra.RopePyName | None``.

        """
        module, *attributes = owner.split(".")
        value: p.Infra.RopePyModule | p.Infra.RopePyObject = project.get_module(module)
        binding: p.Infra.RopePyName | None = None
        for attribute in (*attributes, *suffix.split(".")):
            if attribute not in value.get_attributes():
                return None
            binding = value.get_attribute(attribute)
            value = binding.get_object()
        return binding

    @classmethod
    def _eligible_spans(
        cls,
        project: p.Infra.RopeProject,
        change: p.Infra.RopeChangeContents,
        source: str,
        symbols: t.Triple[str, str, str],
        rewrites: t.SequenceOf[m.Infra.SourceRewrite],
    ) -> t.VariadicTuple[t.Triple[int, int, bool]]:
        """Retain effective-member identity after Rope's receiver/MRO match.

        Returns:
            The resulting ``t.VariadicTuple[t.Triple[int, int, bool]]``.

        Raises:
            TypeError: If CSV symbol campaign does not own attribute mutation.
            ValueError: If CSV destination disappeared during planning; or if CSV symbol
                has no authenticated expression span; or if CSV target overrides the
                declared destination; or if retired member has an independently owned
                namespace.

        """
        module = project.get_pymodule(change.resource)
        owner, old, new = symbols
        expected = cls.resolve_member(project, owner, old)
        destination = cls.resolve_member(project, owner, new)
        if destination is None:
            msg = f"CSV destination disappeared during planning: {owner}.{new}"
            raise ValueError(msg)
        spans: t.MutableSequenceOf[t.Triple[int, int, bool]] = []
        old_parts = old.split(".")
        for node in ast.walk(ast.parse(source)):
            receiver = cls._matched_receiver(node, old_parts)
            if receiver is None:
                continue
            span = cls._authenticated_span(source, node, receiver, rewrites)
            if span is None:
                continue
            scope = u.Infra.scope_at(module, span[0])
            actual = u.Infra.resolve_symbol(scope, node)
            if actual is not None and (
                expected is None or not u.Infra.same_name(expected, actual)
            ):
                spans.append((span[0], span[0] + len(span[1]), False))
                continue
            if isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
                msg = "CSV symbol campaign does not own attribute mutation"
                raise TypeError(msg)
            cls._validate_prefix_ownership(
                project,
                owner,
                scope,
                old_parts,
                (span[2], span[1]),
            )
            target = u.Infra.resolve_symbol(
                scope,
                ast.parse(f"{span[2]}.{new}", mode="eval").body,
            )
            if not u.Infra.same_name(destination, target):
                msg = f"CSV target overrides the declared destination: {span[1]}"
                raise ValueError(msg)
            spans.append((span[0], span[0] + len(span[1]), True))
        return tuple(spans)

    @staticmethod
    def _matched_receiver(node: ast.AST, old_parts: t.StrSequence) -> ast.AST | None:
        """Return the expression whose member chain matches the old symbol path.

        Returns:
            The matched receiver expression, or ``None`` when the node's chain
            does not spell the declared member path.

        """
        receiver = node
        for part in reversed(old_parts):
            if not isinstance(receiver, ast.Attribute) or receiver.attr != part:
                return None
            receiver = receiver.value
        return receiver

    @staticmethod
    def _authenticated_span(
        source: str,
        node: ast.AST,
        receiver: ast.AST,
        rewrites: t.SequenceOf[m.Infra.SourceRewrite],
    ) -> t.Triple[int, str, str] | None:
        """Return one rewritten expression's authenticated source span.

        Returns:
            The ``(start, text, receiver_text)`` triple, or ``None`` when no
            declared rewrite covers the expression span.

        Raises:
            ValueError: If CSV symbol has no authenticated expression span.

        """
        text = ast.get_source_segment(source, node)
        receiver_text = ast.get_source_segment(source, receiver)
        if text is None or receiver_text is None:
            msg = "CSV symbol has no authenticated expression span"
            raise ValueError(msg)
        start = u.Infra.source_offset(source, node)
        if not any(
            start <= edit.start and edit.end <= start + len(text) for edit in rewrites
        ):
            return None
        return (start, text, receiver_text or "")

    @classmethod
    def _validate_prefix_ownership(
        cls,
        project: p.Infra.RopeProject,
        owner: str,
        scope: p.Infra.RopeScope,
        old_parts: t.StrSequence,
        texts: t.Pair[str, str],
    ) -> None:
        """Reject a retired prefix that resolves to an independent namespace.

        Raises:
            ValueError: If retired member has an independently owned namespace.

        """
        receiver_text, text = texts
        for depth in range(1, len(old_parts)):
            prefix = ".".join(old_parts[:depth])
            declared_prefix = cls.resolve_member(project, owner, prefix)
            actual_prefix = u.Infra.resolve_symbol(
                scope,
                ast.parse(f"{receiver_text}.{prefix}", mode="eval").body,
            )
            if actual_prefix is not None and (
                declared_prefix is None
                or not u.Infra.same_name(declared_prefix, actual_prefix)
            ):
                msg = f"retired member owns an independent namespace: {text}"
                raise ValueError(msg)

    @classmethod
    def plan(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        pairs: t.SequenceOf[t.Pair[str, str]],
        bindings: t.MappingKV[str, t.StrSequence],
        *,
        rename_definitions: bool = False,
    ) -> t.MappingKV[Path, t.VariadicTuple[m.Infra.SourceRewrite]]:
        """Merge non-overlapping Rope previews against one immutable snapshot.

        Returns:
            The resulting ``t.MappingKV[Path, t.VariadicTuple[m.Infra.SourceRewrite]]``.

        Raises:
            ValueError: If Rope input changed after authentication; or if CSV
                destination has no declared current public owner; or if symbol campaign
                requires identifier paths; or if CSV Rope campaign escaped authenticated
                inventory; or if Rope CSV edit has no single authenticated member span.

        """
        root = Path(project.root.real_path)
        ordered_paths = tuple(sorted(sources))
        members = {
            path: cls._member_paths(source, path) for path, source in sources.items()
        }
        resources = cls._assert_rope_inputs(project, sources, ordered_paths, root)
        planned: t.MutableMappingKV[
            Path,
            t.MutableSequenceOf[m.Infra.SourceRewrite],
        ] = {}
        for old, new in pairs:
            accepted = cls._plan_pair(
                project,
                ((old, new), bindings),
                (sources, members),
                (ordered_paths, resources),
                (planned, rename_definitions),
            )
            if bindings and not accepted:
                msg = f"CSV destination has no declared current public owner: {new}"
                raise ValueError(msg)
        return {path: tuple(edits) for path, edits in planned.items()}

    @staticmethod
    def _assert_rope_inputs(
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        ordered_paths: t.SequenceOf[Path],
        root: Path,
    ) -> t.MappingKV[Path, t.Infra.RopeFile]:
        """Authenticate every planned source against its live Rope resource.

        Returns:
            The authenticated ``path -> resource`` inventory.

        Raises:
            TypeError: If a planned source is not a Rope file resource.
            ValueError: If Rope input changed after authentication.

        """
        resources: t.MutableMappingKV[Path, t.Infra.RopeFile] = {}
        for path in ordered_paths:
            resource = project.get_resource(path.relative_to(root).as_posix())
            if not FlextInfraUtilitiesRopeRuntime.file_resource(resource):
                msg = f"expected a Rope file resource: {path}"
                raise TypeError(msg)
            if resource.read() != sources[path]:
                msg = f"Rope input changed after authentication: {path}"
                raise ValueError(msg)
            resources[path] = resource
        return resources

    @classmethod
    def _plan_pair(
        cls,
        project: p.Infra.RopeProject,
        campaign: t.Pair[t.Pair[str, str], t.MappingKV[str, t.StrSequence]],
        corpus: t.Pair[
            t.MappingKV[Path, str],
            t.MappingKV[Path, frozenset[tuple[str, ...]]],
        ],
        inventory: t.Pair[t.SequenceOf[Path], t.MappingKV[Path, t.Infra.RopeResource]],
        plan: t.Pair[
            t.MutableMappingKV[Path, t.MutableSequenceOf[m.Infra.SourceRewrite]],
            bool,
        ],
    ) -> bool:
        """Plan one old-to-new pair against every declared owner binding.

        Returns:
            Whether any declared owner accepted the pair.

        Raises:
            ValueError: If symbol campaign requires identifier paths; or if CSV Rope
                campaign escaped authenticated inventory; or if Rope CSV edit has no
                single authenticated member span.

        """
        (old, new), bindings = campaign
        members = corpus[1]
        ordered_paths, resources = inventory
        accepted = False
        for prefix, owners in bindings.items():
            qualifier = prefix + "." if prefix else ""
            if not old.startswith(qualifier) or not new.startswith(qualifier):
                continue
            old_suffix, new_suffix = (
                old.removeprefix(qualifier),
                new.removeprefix(qualifier),
            )
            if not all(
                part.isidentifier()
                for part in (*old_suffix.split("."), *new_suffix.split("."))
            ):
                msg = f"symbol campaign requires identifier paths: {old}, {new}"
                raise ValueError(msg)
            member_path = tuple(old_suffix.split("."))
            elected = tuple(
                resources[path]
                for path in ordered_paths
                if member_path in members[path]
            )
            for owner in owners:
                if plan[1]:
                    resolved = cls._plan_declaration_owner(
                        project,
                        (owner, old_suffix, new_suffix),
                        (corpus[0], resources),
                        plan[0],
                    )
                    accepted = accepted or resolved
                    continue
                if cls.resolve_member(project, owner, new_suffix) is None:
                    continue
                accepted = True
                if not elected:
                    continue
                changes = u.Infra.restructure_changes(
                    project,
                    f"${{owner}}.{old_suffix}",
                    f"${{owner}}.{new_suffix}",
                    arguments={"owner": "instance=" + owner},
                    resources=elected,
                )
                for change in changes.changes:
                    cls._record_campaign_change(
                        change,
                        context=(project, corpus[0]),
                        identity=(owner, old_suffix, new_suffix),
                        planned=plan[0],
                    )
        return accepted

    @classmethod
    def _plan_declaration_owner(
        cls,
        project: p.Infra.RopeProject,
        identity: t.Triple[str, str, str],
        corpus: t.Pair[
            t.MappingKV[Path, str],
            t.MappingKV[Path, t.Infra.RopeResource],
        ],
        planned: t.MutableMappingKV[Path, t.MutableSequenceOf[m.Infra.SourceRewrite]],
    ) -> bool:
        """Plan a declaration rename without weakening its authenticated inventory.

        Returns:
            Whether the old or already-renamed destination has a declared owner.

        Raises:
            ValueError: A rename has no source or identifier, or its target conflicts.

        """
        owner, old_suffix, new_suffix = identity
        sources, resources = corpus
        expected = cls.resolve_member(project, owner, old_suffix)
        destination = cls.resolve_member(project, owner, new_suffix)
        if expected is None:
            return destination is not None
        if destination is not None or not new_suffix.isidentifier():
            msg = f"declaration rename destination is occupied: {owner}.{new_suffix}"
            raise ValueError(msg)
        module, line = expected.get_definition_location()
        resource = module.get_resource() if module is not None else None
        if resource is None or line is None:
            msg = f"declaration rename has no source: {owner}.{old_suffix}"
            raise ValueError(msg)
        path = Path(resource.real_path)
        if path not in sources:
            msg = f"declaration rename escapes authenticated inventory: {path}"
            raise ValueError(msg)
        offset = u.Infra.find_identifier_offset_in_lines(
            sources[path].splitlines(keepends=True),
            line=line,
            symbol=old_suffix.split(".")[-1],
            pyname=expected,
        )
        if offset is None:
            msg = f"declaration rename has no identifier: {owner}.{old_suffix}"
            raise ValueError(msg)
        changes = u.Infra.rename_changes(
            project,
            resource,
            offset,
            new_suffix,
            options=m.Infra.RopeRenameOptions(
                resources=tuple(resources.values()),
                in_hierarchy=True,
            ),
        )
        for change in changes.changes:
            cls._record_campaign_change(
                change,
                context=(project, sources),
                identity=identity,
                planned=planned,
                rename_definitions=True,
            )
        return True

    @classmethod
    def _record_campaign_change(
        cls,
        change: p.AttributeProbe,
        *,
        context: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        identity: t.StrSequence,
        planned: t.MutableMappingKV[Path, t.MutableSequenceOf[m.Infra.SourceRewrite]],
        rename_definitions: bool = False,
    ) -> None:
        """Validate and record one Rope content change from a CSV campaign.

        Raises:
            TypeError: If the campaign produced a non-content effect.
            ValueError: If an edit has no single authenticated span or escapes
                the known inventory.
        """
        project, sources = context
        if not isinstance(change, p.Infra.RopeChangeContents):
            msg = "CSV Rope campaign produced a non-content effect"
            raise TypeError(msg)
        path = Path(change.resource.real_path)
        if path not in sources:
            msg = f"CSV Rope campaign escaped known inventory: {path}"
            raise ValueError(msg)
        original = sources[path]
        matcher = SequenceMatcher(
            a=original,
            b=change.new_contents,
            autojunk=False,
        ).get_opcodes()
        rewrites = tuple(
            m.Infra.SourceRewrite(
                start=start,
                end=end,
                text=change.new_contents[updated_start:updated_end],
            )
            for kind, start, end, updated_start, updated_end in matcher
            if kind != "equal"
        )
        if rename_definitions:
            edits = planned.setdefault(path, [])
            edits.extend(edit for edit in rewrites if edit not in edits)
            return
        owner, old_suffix, new_suffix = identity
        spans = cls._eligible_spans(
            project,
            change,
            original,
            (owner, old_suffix, new_suffix),
            rewrites,
        )
        for edit in rewrites:
            containing = tuple(
                allowed
                for begin, finish, allowed in spans
                if begin <= edit.start and edit.end <= finish
            )
            if not containing:
                msg = f"Rope CSV edit has no single authenticated member span: {path}"
                raise ValueError(msg)
            if not all(containing):
                continue
            edits = planned.setdefault(path, [])
            if edit not in edits:
                edits.append(edit)


__all__: list[str] = ["FlextInfraRenameSymbols"]
