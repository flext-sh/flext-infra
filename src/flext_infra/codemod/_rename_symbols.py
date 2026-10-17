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
    """Supply domain decisions and translate rename plans into Rope constraints."""

    def __init__(self, decisions: t.SequenceOf[m.Infra.SemanticRenameDecision]) -> None:
        self.decisions = tuple(decisions)

    def rename_decision(
        self, declaration: m.Infra.Object
    ) -> m.Infra.SemanticRenameDecision | None:
        """Return the unique explicit decision for this introducing declaration.

        Returns:
            The domain decision, or no candidate when the domain declared none.

        Raises:
            ValueError: If the domain supplied competing decisions for one owner.

        """
        decisions = tuple(
            decision
            for decision in self.decisions
            if decision.declaration == declaration
        )
        if len(decisions) > 1:
            msg = f"competing semantic rename decisions: {declaration.scope_path}"
            raise ValueError(msg)
        return next(iter(decisions), None)

    @classmethod
    def inventoried_declaration(
        cls, workspace: p.Infra.RopeWorkspaceDsl, qualified_name: str
    ) -> m.Infra.Object:
        """Resolve an explicit identity through native bindings and actual inventory.

        Returns:
            The unique introducing callable object observed in its source module.

        Raises:
            ValueError: If the identity is missing, inherited, or ambiguous.

        """
        owner, _, name = qualified_name.rpartition(".")
        binding = cls.resolve_member(workspace.rope_project, owner, name)
        module, _ = (
            binding.get_definition_location() if binding is not None else (None, None)
        )
        resource = module.get_resource() if module is not None else None
        if resource is None:
            msg = f"semantic rename has no inventoried source: {qualified_name}"
            raise ValueError(msg)
        matches = tuple(
            item
            for item in workspace.objects(
                Path(resource.real_path), include_references=False
            )
            if f"{item.module_name}.{item.scope_path}" == qualified_name
            and item.kind in {"method", "function"}
        )
        if len(matches) != 1:
            msg = f"semantic rename requires one introducing object: {qualified_name}"
            raise ValueError(msg)
        return matches[0]

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
        parts = owner.split(".")
        module = parts[0]
        for end in range(2, len(parts) + 1):
            candidate = ".".join(parts[:end])
            if project.find_module(candidate) is None:
                break
            module = candidate
        attributes = parts[len(module.split(".")) :]
        value: p.Infra.RopeSemanticModule | p.Infra.RopePyObject = (
            FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                project.get_module(module)
            )
        )
        binding: p.Infra.RopePyName | None = None
        for attribute in (*attributes, *suffix.split(".")):
            if attribute not in value.get_attributes():
                return None
            binding = value.get_attribute(attribute)
            value = binding.get_object()
        return binding

    @classmethod
    def plan_candidates(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        declarations: t.SequenceOf[m.Infra.Object],
        provider: p.Infra.SemanticRenameCandidateProvider,
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Compose explicit domain decisions through the existing Rope planner.

        Independent typing stubs enter only as declared contracts of the observed
        introducer. No lexical prefix policy chooses a replacement or a consumer.
        The returned original bytes make the plan reversible and publication-free.

        Returns:
            Complete changed-source plans against one authenticated snapshot.

        Raises:
            ValueError: If a decision changes identity, repeats an owner, or names
                an inherited declaration or incompatible independent contract.

        """
        planned: t.MutableMappingKV[
            Path, t.MutableSequenceOf[m.Infra.SourceRewrite]
        ] = {}
        selected: set[t.Pair[str, str]] = set()
        for declaration in declarations:
            decision = provider.rename_decision(declaration)
            if decision is None:
                continue
            if decision.declaration != declaration:
                msg = "semantic rename decision changed its observed declaration"
                raise ValueError(msg)
            signature = cls._candidate_signature(project, sources, declaration)
            for item in (declaration, *decision.contracts):
                owner, _, name = item.scope_path.rpartition(".")
                identity = (f"{item.module_name}.{owner}".rstrip("."), name)
                identities = (identity, (identity[0], decision.replacement_name))
                if not selected.isdisjoint(identities):
                    msg = f"semantic rename has competing owner names: {identity}"
                    raise ValueError(msg)
                selected.update(identities)
                if (
                    cls._candidate_signature(
                        project, sources, item, contract=item != declaration
                    )
                    != signature
                ):
                    msg = f"semantic rename has incompatible contract: {identity}"
                    raise ValueError(msg)
                changes = cls.plan(
                    project,
                    sources,
                    ((name, decision.replacement_name),),
                    {"": (identity[0],)},
                    rename_definitions=True,
                )
                for path, edits in changes.items():
                    target = planned.setdefault(path, [])
                    target.extend(edit for edit in edits if edit not in target)
        root = Path(project.root.real_path)
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=sources[path],
                updated_source=u.Infra.content_change(
                    project.get_resource(path.relative_to(root).as_posix()),
                    sources[path],
                    edits,
                ).new_contents,
                changes=("applied explicit domain semantic rename decisions",),
            )
            for path, edits in sorted(planned.items())
        )

    @classmethod
    def _candidate_signature(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        declaration: m.Infra.Object,
        *,
        contract: bool = False,
    ) -> t.Pair[str, str]:
        """Authenticate a direct method/function and retain its callable contract.

        Returns:
            The AST argument and return-annotation identities.

        Raises:
            ValueError: If discovery does not identify the actual declaration.

        """
        owner, _, name = declaration.scope_path.rpartition(".")
        binding = cls.resolve_member(
            project, f"{declaration.module_name}.{owner}".rstrip("."), name
        )
        if binding is None:
            msg = (
                f"semantic rename declaration has no binding: {declaration.scope_path}"
            )
            raise ValueError(msg)
        module, line = binding.get_definition_location()
        resource = module.get_resource() if module is not None else None
        path = Path(declaration.file_path)
        if (
            module is None
            or resource is None
            or Path(resource.real_path) != path
            or line != declaration.line
            or path not in sources
        ):
            msg = (
                "semantic rename is not an observed direct declaration: "
                f"{declaration.scope_path}"
            )
            raise ValueError(msg)
        if declaration.kind not in {"function", "method"} or name != declaration.name:
            msg = (
                "semantic rename requires a callable identity: "
                f"{declaration.scope_path}"
            )
            raise ValueError(msg)
        tree = ast.parse(sources[path])
        function = next(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.lineno == line
                and node.name == name
            ),
            None,
        )
        if function is None:
            msg = f"semantic rename declaration has no callable body: {path}:{line}"
            raise ValueError(msg)
        owner_binding = cls.resolve_member(project, declaration.module_name, owner)
        scope = (
            owner_binding.get_object().get_scope()
            if owner_binding is not None
            else module.get_scope()
        )
        if scope is None or not u.Infra.same_name(
            binding, scope.get_defined_names().get(name)
        ):
            msg = (
                "semantic rename is inherited rather than introduced: "
                f"{declaration.scope_path}"
            )
            raise ValueError(msg)
        if contract and not all(
            isinstance(node, ast.Pass)
            or (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and (node.value.value is Ellipsis or isinstance(node.value.value, str))
            )
            for node in function.body
        ):
            msg = (
                "semantic rename companion has behavior, not a typing contract: "
                f"{path}:{line}"
            )
            raise ValueError(msg)
        return (
            f"{type(function).__name__}:{ast.dump(function.args)}",
            ast.dump(function.returns) if function.returns else "",
        )

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
        module = u.Infra.resolve_pymodule(
            project,
            u.Infra.require_file_resource(change.resource, change.resource.path),
        )
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
                    m.Infra.RopeRestructureRequest(
                        pattern=f"${{owner}}.{old_suffix}",
                        goal=f"${{owner}}.{new_suffix}",
                        arguments={"owner": "instance=" + owner},
                        resources=elected,
                    ),
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
                resources=tuple(
                    {
                        resource.real_path: resource
                        for resource in (
                            *resources.values(),
                            *project.get_python_files(),
                        )
                    }.values()
                ),
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
