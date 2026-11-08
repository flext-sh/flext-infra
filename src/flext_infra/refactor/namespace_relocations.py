"""Rule-catalog relocation cascade shared by the enforcer and the mod loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import io
import keyword
import tokenize
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.transformers._semantic import FlextInfraTransformersSemanticPublication


class FlextInfraNamespaceRelocationCascade:
    """Run the rope relocation each finding's rule declares; count the rest.

    The rule catalog owns detection: every namespace law is a rule document
    the one scan engine evaluates. A rule that a rope relocation repairs
    names it under ``metadata.relocation``; this cascade runs those
    relocations over the captured findings — both for the standalone
    namespace enforcer and as the mod loop's relocation callback. Callers
    retain the complete scans used to measure progress and regressions.
    """

    @staticmethod
    def scoped_py_files(project_root: Path) -> Sequence[Path]:
        """Collect the project's namespace-scoped Python files.

        Returns:
            The resulting ``Sequence[Path]``.

        Raises:
            RuntimeError: If ``py_files_result.failure``.

        """
        py_files_result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(project_root,)),
        )
        if py_files_result.failure:
            msg = py_files_result.error or (
                f"failed to collect Python files for {project_root}"
            )
            raise RuntimeError(msg)
        declared = u.Infra.namespace_meta(project_root).get("scan_dirs")
        if not isinstance(declared, list) or not declared:
            return py_files_result.value
        scope = frozenset(str(item).strip() for item in declared if str(item).strip())
        return tuple(
            path
            for path in py_files_result.value
            if path.relative_to(project_root).parts[0] in scope
        )

    @staticmethod
    def relocation_by_rule(
        project_root: Path,
    ) -> Mapping[str, c.Infra.CodemodRelocation]:
        """Map every relocation-declaring rule id to its relocation kind.

        Returns:
            The resulting ``Mapping[str, c.Infra.CodemodRelocation]``.

        """
        with u.Infra.codemod_workspace_snapshot(project_root) as snapshot:
            rules = u.Infra.codemod_rule_plan(snapshot).unwrap().rules
        return {
            rule.id: rule.relocation for rule in rules if rule.relocation is not None
        }

    @classmethod
    def findings_from_report(
        cls,
        project_root: Path,
        py_files: Sequence[Path],
        entries: Sequence[p.Infra.ModScanFinding],
        *,
        scan_root: Path,
    ) -> tuple[tuple[c.Infra.CodemodRelocation, p.Infra.ModScanFinding], ...]:
        """Filter one scan report's entries down to in-scope relocation findings.

        The scope is the project's namespace file set (its declared scan
        directories), so a relocation never reaches a file the namespace pass
        does not govern. Finding paths belong to ``scan_root``; returned targets
        are project-relative even when captured by the workspace scan.

        Returns:
            The resulting ``tuple[
                tuple[c.Infra.CodemodRelocation, m.Infra.ModScanFinding], ...]``.

        """
        relocation_by_rule = cls.relocation_by_rule(project_root)
        scoped = frozenset(path.resolve() for path in py_files)
        return tuple(
            (
                relocation_by_rule[entry.rule_id],
                entry.model_copy(
                    update={
                        "file": (scan_root / entry.file)
                        .resolve()
                        .relative_to(project_root),
                    }
                ),
            )
            for entry in entries
            if entry.rule_id in relocation_by_rule
            and (scan_root / entry.file).resolve() in scoped
        )

    def run(
        self,
        *,
        project_root: Path,
        rope_project: t.Infra.RopeProject,
        findings: Sequence[tuple[c.Infra.CodemodRelocation, p.Infra.ModScanFinding]],
        py_files: Sequence[Path],
        gates: Sequence[str] | None = None,
    ) -> None:
        """Publish the same complete relocation plan once through the shared owner."""
        if not findings:
            return
        paths = tuple(
            dict.fromkeys((
                *py_files,
                *(
                    Path(resource.real_path).resolve()
                    for resource in rope_project.get_python_files()
                ),
            ))
        )
        planned = self.plan(
            m.Infra.NamespaceRelocationRequest(
                project_root=project_root,
                findings=findings,
                py_files=py_files,
                sources={
                    path: path.read_text(encoding=c.DEFAULT_ENCODING) for path in paths
                },
            ),
            rope_project=rope_project,
        ).unwrap()
        self.publish_plan(project_root, planned, gates=gates).unwrap()

    @staticmethod
    def publish_plan(
        project_root: Path,
        plans: Sequence[p.Infra.CodegenFilePlan],
        *,
        gates: Sequence[str] | None = None,
    ) -> p.Result[bool]:
        """Publish the complete relocation plan once with its projections.

        Returns:
            Whether any plan was published, or the first publication failure.

        """
        if not plans:
            return r[bool].ok(value=False)

        def verify(published_root: Path) -> p.Result[bool]:
            return FlextInfraWorkspaceChecker(
                repository_root=published_root
            ).execute_payload(
                m.Infra.RunCommand(
                    repository_root=published_root,
                    gates=tuple(gates or ()),
                )
            )

        return (
            FlextInfraTransformersSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=project_root,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(project_root,),
                    validator=verify if gates is not None else None,
                ),
            ).map(bool)
        )

    def plan(
        self,
        request: p.Infra.NamespaceRelocationRequest,
        *,
        rope_project: p.Infra.RopeProject,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Compose native relocation effects without performing any Rope changes.

        Returns:
            The composed file plans, or the first planning failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        initialized = self._capture_relocation_state(request)
        if initialized.failure:
            return result_type.from_failure(initialized)
        state = initialized.value
        future_files, spans, imports, families = self._grouped_targets(
            request.project_root, request.findings
        )
        for file_path, statement_lines in spans.items():
            state.working[file_path] = u.Infra.plan_hoist_inline_imports(
                file_path, state.working[file_path], statement_lines
            )
        for file_path in sorted(future_files):
            state.working[file_path] = u.Infra.plan_future_annotations(
                state.working[file_path]
            )
        effect = self._relocate_imports(state, rope_project, imports)
        if effect.failure:
            return result_type.from_failure(effect)
        selected = self._family_targets(request, state, rope_project, families)
        if selected.failure:
            return result_type.from_failure(selected)
        declarations, members = selected.value
        effect = (
            self
            ._prepare_destinations(
                state, declarations, members, project_root=request.project_root
            )
            .flat_map(
                lambda _: self._move_declarations(
                    request, state, rope_project, declarations
                )
            )
            .flat_map(
                lambda _: self._transfer_members(request, state, rope_project, members)
            )
        )
        if effect.failure:
            return result_type.from_failure(effect)
        return self._relocation_plans(request, state)

    @staticmethod
    def _capture_relocation_state(
        request: p.Infra.NamespaceRelocationRequest,
    ) -> p.Result[p.Infra.NamespaceRelocationState]:
        """Bind the working bytes after checking every target selection.

        Returns:
            Mutable candidate state, or the first selection failure.

        """
        selected = frozenset(request.py_files)
        for _relocation, finding in request.findings:
            path = request.project_root / finding.file
            if not path.is_relative_to(request.project_root) or path not in selected:
                return r[p.Infra.NamespaceRelocationState].fail(
                    f"relocation declaration is outside its selected targets: {path}"
                )
            if path not in request.sources:
                return r[p.Infra.NamespaceRelocationState].fail(
                    f"relocation source lacks its working view: {path}"
                )
        return r[p.Infra.NamespaceRelocationState].ok(
            m.Infra.NamespaceRelocationState(
                working=dict(request.sources), originals={}, modes={}
            )
        )

    @staticmethod
    def _relocate_imports(
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        imports: Mapping[Path, Mapping[tuple[str, str], set[str]]],
    ) -> p.Result[bool]:
        """Plan each import relocation against the current candidate.

        Returns:
            Acceptance of all import moves, or the first native planning failure.

        """
        working = state.working
        for file_path, moves in imports.items():
            for (source_module, target_module), aliases in sorted(moves.items()):
                snapshot = u.Infra.snapshot_project(rope_project, working)
                resource = u.Infra.require_file_resource(
                    snapshot.get_resource(
                        file_path.relative_to(Path(snapshot.root.real_path)).as_posix()
                    ),
                    file_path,
                )
                updated = u.Infra.plan_from_import_aliases(
                    snapshot,
                    resource,
                    source_module=source_module,
                    target_module=target_module,
                    aliases=tuple(sorted(aliases)),
                )
                if updated.failure:
                    return r[bool].from_failure(updated)
                if updated.value == working[file_path]:
                    return r[bool].fail(
                        f"native import relocation did not plan: {file_path}"
                    )
                working[file_path] = updated.value
        return r[bool].ok(value=True)

    @classmethod
    def _family_targets(
        cls,
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        findings: Sequence[tuple[Path, str, str, int]],
    ) -> p.Result[tuple[list[tuple[Path, str, Path]], list[tuple[Path, str, Path]]]]:
        """Elect each finding's family domain module and classify its binding.

        The native binding at the finding decides the primitive: a module-level
        binding moves whole (``declarations``), a static or class method
        transfers into the destination owner class (``members``). A method
        that needs a receiver rewrite is not derivable and stays a finding.

        Returns:
            ``(declarations, members)`` as ``(source, name, destination)``
            triples, or the first finding without a native declaration.

        """
        result_type = r[
            tuple[list[tuple[Path, str, Path]], list[tuple[Path, str, Path]]]
        ]
        declarations: list[tuple[Path, str, Path]] = []
        members: list[tuple[Path, str, Path]] = []
        if not findings:
            return result_type.ok((declarations, members))
        snapshot = cls._relocation_snapshot(request, state, rope_project)
        coordinate = Path(snapshot.root.real_path)
        for path, name, family, line in findings:
            target = u.Infra.family_declaration_target_file(
                project_root=request.project_root, source_file=path, family=family
            )
            module = u.Infra.resolve_pymodule(
                snapshot,
                u.Infra.require_file_resource(
                    snapshot.get_resource(path.relative_to(coordinate).as_posix()),
                    path,
                ),
            )
            binding = module.get_scope().get_defined_names().get(name)
            location = None if binding is None else binding.get_definition_location()
            module_level = location is not None and location[0] is module
            if module_level and location[1] == line:
                declarations.append((path, name, target))
                continue
            member = cls._transferable_member(module, name, line)
            if member is not None:
                members.append((path, member, target))
            elif module_level:
                declarations.append((path, name, target))
        return result_type.ok((declarations, members))

    @staticmethod
    def _transferable_member(
        module: p.Infra.RopePyModule, name: str, line: int
    ) -> str | None:
        """Return the qualified name of the static or class method at ``line``.

        Returns:
            ``Owner.method`` for a native static or class method declared at the
            finding line, otherwise ``None`` (instance methods, properties and
            nested functions need receiver rewrites no derivation supplies).

        """
        pending = [(module.get_scope(), ())]
        while pending:
            scope, chain = pending.pop()
            for child in scope.get_scopes():
                declared = child.pyobject
                if child.get_kind() == "Class":
                    pending.append((child, (*chain, declared.get_name())))
                elif (
                    scope.get_kind() == "Class"
                    and child.get_kind() == "Function"
                    and declared.get_name() == name
                    and declared.get_ast().lineno == line
                    and declared.get_kind()
                    in {
                        c.Infra.RopeFunctionKind.STATICMETHOD,
                        c.Infra.RopeFunctionKind.CLASSMETHOD,
                    }
                ):
                    return ".".join((*chain, name))
        return None

    @classmethod
    def _prepare_destinations(
        cls,
        state: p.Infra.NamespaceRelocationState,
        declarations: Sequence[tuple[Path, str, Path]],
        members: Sequence[tuple[Path, str, Path]],
        *,
        project_root: Path,
    ) -> p.Result[bool]:
        """Seed each absent destination; an existing unread file fails.

        A member transfer needs an existing owner class, so its absent
        destination is seeded with the derived owner skeleton.

        Returns:
            Acceptance of each destination, or the first foreign-file failure.

        """
        working = state.working
        owners = {target for _path, _name, target in members}
        for path, _name, target in (*declarations, *members):
            if target in working:
                continue
            destination = u.Infra.codegen_target_snapshot(target)
            if destination.failure:
                return r[bool].from_failure(destination)
            if destination.value.content is not None:
                return r[bool].fail(
                    f"relocation destination is outside its working view: {target}"
                )
            source = u.Infra.codegen_target_snapshot(path)
            if source.failure:
                return r[bool].from_failure(source)
            seed = f"{c.Infra.FUTURE_ANNOTATIONS}\n"
            if target in owners:
                owner = cls._derived_owner(project_root, target)
                if owner.failure:
                    return r[bool].from_failure(owner)
                seed = (
                    f'{seed}\n\nclass {owner.value}:\n    """Relocated behavior."""\n'
                    f'\n\n__all__: list[str] = ["{owner.value}"]\n'
                )
            state.originals[target] = destination.value
            state.modes[target] = source.value.mode
            working[target] = seed
        return r[bool].ok(value=True)

    @staticmethod
    def _derived_owner(project_root: Path, target: Path) -> p.Result[str]:
        """Derive the family owner class a new domain module declares.

        The grammar is the class-nesting owner grammar: project class stem,
        family suffix, then the module stem.

        Returns:
            The owner class name, or the failure naming the underivable tier.

        """
        layout = u.Infra.layout(project_root)
        letter = u.Infra.facade_family_of_directory(target.parent.name)
        if (
            layout is None
            or letter is None
            or not target.is_relative_to(layout.package_dir)
        ):
            return r[str].fail(
                f"member transfer cannot derive the owner class of {target}"
            )
        suffix = u.Infra.facade_families()[letter].suffix
        return r[str].ok(
            f"{layout.class_stem}{suffix}{u.derive_class_stem(target.stem.strip('_'))}"
        )

    @classmethod
    def _move_declarations(
        cls,
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        declarations: Sequence[tuple[Path, str, Path]],
    ) -> p.Result[bool]:
        """Apply native move effects to candidate bytes, never to the filesystem.

        Returns:
            Acceptance of all declaration effects, or their first native failure.

        """
        working = state.working
        for path, declared, target in declarations:
            name = declared
            if declared.startswith("_"):
                published = cls._publish_private_name(
                    request, state, rope_project, (path, declared, target)
                )
                if published.failure:
                    return r[bool].from_failure(published)
                name = published.value
            snapshot = cls._relocation_snapshot(request, state, rope_project)
            coordinate = Path(snapshot.root.real_path)
            resource = u.Infra.require_file_resource(
                snapshot.get_resource(path.relative_to(coordinate).as_posix()),
                path,
            )
            quoted = cls._quoted_reference_line(working[path], name)
            if quoted is not None:
                return r[bool].fail(
                    f"relocation of {name} has a quoted forward reference at "
                    f"{path}:{quoted}: native occurrences cannot rewire a string; "
                    "write it as a real annotation first"
                )
            occupied = cls._destination_occupied(snapshot, target, name)
            if occupied.failure:
                return r[bool].from_failure(occupied)
            offset = cls._declaration_offset(snapshot, resource, working[path], name)
            if offset.failure:
                return r[bool].from_failure(offset)
            changes = u.Infra.create_move(snapshot, resource, offset.value).get_changes(
                u.Infra.require_file_resource(
                    snapshot.get_resource(target.relative_to(coordinate).as_posix()),
                    target,
                ),
                resources=cls._python_resources(snapshot, working),
            )
            applied = cls._apply_changes(working, changes.changes)
            if applied.failure:
                return applied
        return r[bool].ok(value=True)

    @staticmethod
    def _python_resources(
        snapshot: p.Infra.RopeProject, working: Mapping[Path, str]
    ) -> list[p.Infra.RopeResource]:
        """Bind every candidate Python source to its native snapshot resource.

        Returns:
            The Rope resources of the candidate view, in view order.

        """
        coordinate = Path(snapshot.root.real_path)
        return [
            u.Infra.require_file_resource(
                snapshot.get_resource(candidate.relative_to(coordinate).as_posix()),
                candidate,
            )
            for candidate in working
            if candidate.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
        ]

    @staticmethod
    def _apply_changes(
        working: MutableMapping[Path, str],
        changes: Sequence[p.AttributeProbe],
    ) -> p.Result[bool]:
        """Apply native content effects to the candidate bytes only.

        Returns:
            Acceptance of every effect, or the first escaping or non-content one.

        """
        for change in changes:
            if not isinstance(change, p.Infra.RopeChangeContents):
                return r[bool].fail(
                    "native declaration relocation produced a non-content effect"
                )
            destination = Path(change.resource.real_path).resolve()
            if destination not in working:
                return r[bool].fail(
                    f"native relocation escaped its working view: {destination}"
                )
            working[destination] = change.new_contents
        return r[bool].ok(value=True)

    @staticmethod
    def _quoted_reference_line(source: str, name: str) -> int | None:
        """Locate a string literal that spells ``name`` as a forward reference.

        Returns:
            The 1-based line of the first quoted spelling, or ``None``.

        """
        exporting = False
        line_start = True
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NEWLINE:
                exporting = False
                line_start = True
                continue
            if token.type in {
                tokenize.NL,
                tokenize.COMMENT,
                tokenize.INDENT,
                tokenize.DEDENT,
            }:
                continue
            if line_start:
                exporting = token.string == c.Infra.DUNDER_ALL
                line_start = False
            if (
                not exporting
                and token.type == tokenize.STRING
                and token.string[:1] in {'"', "'"}
                and token.string.strip("\"'") == name
            ):
                return token.start[0]
        return None

    @staticmethod
    def _destination_occupied(
        snapshot: p.Infra.RopeProject, target: Path, name: str
    ) -> p.Result[bool]:
        """Reject a move onto a name the destination module already declares.

        Returns:
            Acceptance when ``name`` is free at module level and in its classes.

        """
        coordinate = Path(snapshot.root.real_path)
        module = u.Infra.resolve_pymodule(
            snapshot,
            u.Infra.require_file_resource(
                snapshot.get_resource(target.relative_to(coordinate).as_posix()),
                target,
            ),
        )
        scope = module.get_scope()
        if name in scope.get_names() or any(
            child.get_kind() == "Class" and name in child.pyobject.get_attributes()
            for child in scope.get_scopes()
        ):
            return r[bool].fail(
                f"relocation destination already declares {name}: {target}"
            )
        return r[bool].ok(value=True)

    @classmethod
    def _publish_private_name(
        cls,
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        declaration: tuple[Path, str, Path],
    ) -> p.Result[str]:
        """Rename a module-private declaration to the public family member it becomes.

        A family namespace has no privacy: the relocated name is read as
        ``t.<Domain>.<Name>`` by its former module, so the leading underscores
        leave through the native rename before the move.

        Returns:
            The public name, or the first collision or native rename failure.

        """
        path, private, target = declaration
        public = private.lstrip("_")
        if not public.isidentifier() or keyword.iskeyword(public):
            return r[str].fail(f"private declaration has no public name: {private}")
        working = state.working
        snapshot = cls._relocation_snapshot(request, state, rope_project)
        coordinate = Path(snapshot.root.real_path)
        resource = u.Infra.require_file_resource(
            snapshot.get_resource(path.relative_to(coordinate).as_posix()), path
        )
        if (
            public
            in u.Infra.resolve_pymodule(snapshot, resource).get_scope().get_names()
        ):
            return r[str].fail(
                f"private declaration {private} cannot become public: "
                f"{public} is occupied in {path}"
            )
        occupied = cls._destination_occupied(snapshot, target, public)
        if occupied.failure:
            return r[str].from_failure(occupied)
        offset = cls._declaration_offset(snapshot, resource, working[path], private)
        if offset.failure:
            return r[str].from_failure(offset)
        changes = u.Infra.rename_changes(
            snapshot,
            resource,
            offset.value,
            public,
            options=m.Infra.RopeRenameOptions(
                resources=cls._python_resources(snapshot, working),
                in_hierarchy=False,
                docs=False,
            ),
        )
        applied = cls._apply_changes(working, changes.changes)
        return r[str].from_failure(applied) if applied.failure else r[str].ok(public)

    @classmethod
    def _transfer_members(
        cls,
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        members: Sequence[tuple[Path, str, Path]],
    ) -> p.Result[bool]:
        """Transfer static and class methods into their family owner class.

        The native Rope class transfer rewrites every proven reference and
        rejects the whole transfer when a reference is unproven; that rejection
        is the method's own unresolved finding (its rule keeps reporting it),
        never a plan crash, so the member stays where it is.

        Returns:
            Acceptance of every attempted transfer, or the first non-Rope failure.

        """
        working = state.working
        refused = u.Infra.exception_type("rope.base.exceptions", "RefactoringError")
        for path, qualified, target in members:
            snapshot = cls._relocation_snapshot(request, state, rope_project)
            owner = cls._destination_owner(request, snapshot, target)
            if owner.failure:
                return r[bool].from_failure(owner)
            transfer = m.Infra.RopeMethodTransfer(
                id=f"family-declaration:{path.name}:{qualified}",
                destination=(
                    u.Infra.module_name_for_file(
                        target,
                        project_root=request.project_root,
                        source_project=snapshot,
                    ),
                    owner.value,
                ),
                methods=(
                    (
                        u.Infra.module_name_for_file(
                            path,
                            project_root=request.project_root,
                            source_project=snapshot,
                        ),
                        qualified,
                    ),
                ),
            )
            try:
                changes = u.Infra.method_transfer_changes(
                    snapshot,
                    transfer,
                    tuple(candidate.resolve() for candidate in working),
                    u.Infra.source_member_resolver(snapshot, sources={}),
                )
            except refused as error:
                u.Cli.info(f"family transfer unresolved: {qualified}: {error}")
                continue
            if changes is None:
                continue
            applied = cls._apply_changes(working, changes.changes)
            if applied.failure:
                return applied
        return r[bool].ok(value=True)

    @staticmethod
    def _destination_owner(
        request: p.Infra.NamespaceRelocationRequest,
        snapshot: p.Infra.RopeProject,
        target: Path,
    ) -> p.Result[str]:
        """Elect the single owner class of a member transfer destination.

        Returns:
            The owner class name, or the failure naming an ambiguous module.

        """
        coordinate = Path(snapshot.root.real_path)
        module = u.Infra.resolve_pymodule(
            snapshot,
            u.Infra.require_file_resource(
                snapshot.get_resource(target.relative_to(coordinate).as_posix()),
                target,
            ),
        )
        classes = tuple(
            child.pyobject.get_name()
            for child in module.get_scope().get_scopes()
            if child.get_kind() == "Class"
        )
        if len(classes) == 1:
            return r[str].ok(classes[0])
        derived = FlextInfraNamespaceRelocationCascade._derived_owner(
            request.project_root, target
        )
        if derived.success and derived.value in classes:
            return derived
        return r[str].fail(
            f"member transfer destination has no single owner class: {target}"
        )

    @staticmethod
    def _relocation_snapshot(
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
    ) -> p.Infra.RopeProject:
        """Build one native snapshot of the current candidate, new files included.

        Returns:
            The Rope snapshot of the current candidate view.

        """
        return u.Infra.snapshot_project(
            rope_project,
            state.working,
            declared_files=tuple(
                m.Infra.CodegenFilePlan(
                    project=request.project_root,
                    path=destination,
                    before=before,
                    desired_content=state.working[destination].encode(
                        c.DEFAULT_ENCODING
                    ),
                    desired_mode=state.modes[destination],
                    owner="namespace-relocations",
                )
                for destination, before in state.originals.items()
            ),
        )

    @staticmethod
    def _declaration_offset(
        snapshot: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        name: str,
    ) -> p.Result[int]:
        """Authenticate a local declaration before selecting its native identifier.

        Returns:
            The native source offset or the first missing-declaration failure.

        """
        path = Path(resource.real_path)
        module = u.Infra.resolve_pymodule(snapshot, resource)
        binding = module.get_scope().get_defined_names().get(name)
        if binding is None:
            return r[int].fail(
                f"native relocation declaration is absent: {path}:{name}"
            )
        owner, line = binding.get_definition_location()
        if owner is not module or line is None:
            return r[int].fail(
                f"native relocation declaration is not local: {path}:{name}"
            )
        offset = u.Infra.find_identifier_offset_in_lines(
            source.splitlines(keepends=True), line=line, symbol=name
        )
        if offset is None:
            return r[int].fail(f"native relocation identifier is absent: {path}:{name}")
        return r[int].ok(offset)

    @staticmethod
    def _relocation_plans(
        request: p.Infra.NamespaceRelocationRequest,
        state: p.Infra.NamespaceRelocationState,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Bind every changed candidate source to its destination state once.

        Returns:
            The relocation file plans, or the first destination read failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        plans: list[p.Infra.CodegenFilePlan] = []
        for path, source in state.working.items():
            if request.sources.get(path) == source:
                continue
            before = state.originals.get(path)
            if before is None:
                observed = u.Infra.codegen_target_snapshot(path)
                if observed.failure:
                    return result_type.from_failure(observed)
                before = observed.value
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(path) or request.project_root,
                    path=path,
                    before=before,
                    desired_content=source.encode(c.DEFAULT_ENCODING),
                    desired_mode=state.modes.get(path, before.mode),
                    owner="namespace-relocations",
                )
            )
        return result_type.ok(tuple(plans))

    @classmethod
    def import_relocation_targets(
        cls,
        project_root: Path,
        findings: Sequence[tuple[c.Infra.CodemodRelocation, p.Infra.ModScanFinding]],
    ) -> Mapping[Path, Mapping[tuple[str, str], set[str]]]:
        """Map each file's import moves: ``(source module, target module)`` to aliases.

        An own-package symbol always rebinds to the own package's root. A
        package-root finding whose source module lies under a foreign
        top-level package is not this project's finding: it stays residue
        and keeps the verb loud instead of binding the alias into the
        foreign package — the defect that rewrote own-package
        ``from flext_infra import u`` bindings to ``from flext_cli import u``.

        Returns:
            The resulting mapping of file paths to import moves.

        """
        own_package = u.Infra.project_package_name(project_root)
        targets: MutableMapping[Path, MutableMapping[tuple[str, str], set[str]]] = (
            defaultdict(lambda: defaultdict(set))
        )
        artifacts = tuple(
            {
                finding.native_receipt.path: finding.native_receipt
                for _relocation, finding in findings
                if finding.native_receipt is not None
            }.values()
        )
        with u.Infra.mod_native_readers(artifacts) as readers:
            for relocation, finding in findings:
                if relocation not in {
                    c.Infra.CodemodRelocation.PACKAGE_ROOT_IMPORT,
                    c.Infra.CodemodRelocation.OWN_PACKAGE_IMPORT,
                }:
                    continue
                module = cls._captured(
                    finding,
                    c.Infra.CODEMOD_RULE_MODULE_METAVARIABLE,
                    readers,
                )
                if (
                    relocation is c.Infra.CodemodRelocation.PACKAGE_ROOT_IMPORT
                    and module.split(".", maxsplit=1)[0] != own_package
                ):
                    continue
                targets[project_root / finding.file][module, own_package].add(
                    cls._captured(
                        finding, c.Infra.CODEMOD_RULE_NAME_METAVARIABLE, readers
                    ),
                )
        return targets

    def _grouped_targets(
        self,
        project_root: Path,
        findings: Sequence[tuple[c.Infra.CodemodRelocation, p.Infra.ModScanFinding]],
    ) -> tuple[
        set[Path],
        MutableMapping[Path, list[tuple[int, int]]],
        MutableMapping[Path, MutableMapping[tuple[str, str], set[str]]],
        list[tuple[Path, str, str, int]],
    ]:
        """Group findings into the batched targets each relocation consumes.

        Returns:
            The resulting ``(future_files, spans, imports, families)`` batches.

        """
        future_files: set[Path] = set()
        spans: MutableMapping[Path, list[tuple[int, int]]] = defaultdict(list)
        imports: MutableMapping[Path, MutableMapping[tuple[str, str], set[str]]] = (
            defaultdict(lambda: defaultdict(set))
        )
        families: list[tuple[Path, str, str, int]] = []
        artifacts = tuple(
            {
                finding.native_receipt.path: finding.native_receipt
                for _relocation, finding in findings
                if finding.native_receipt is not None
            }.values()
        )
        with u.Infra.mod_native_readers(artifacts) as readers:
            for relocation, finding in findings:
                file_path = project_root / finding.file
                match relocation:
                    case c.Infra.CodemodRelocation.MODULE_IMPORT:
                        spans[file_path].append(self._finding_lines(finding))
                    case c.Infra.CodemodRelocation.FUTURE_ANNOTATIONS:
                        future_files.add(file_path)
                    case (
                        c.Infra.CodemodRelocation.PACKAGE_ROOT_IMPORT
                        | c.Infra.CodemodRelocation.OWN_PACKAGE_IMPORT
                    ):
                        # Grouped by the public import_relocation_targets owner,
                        # which binds own-package symbols to the own package and
                        # leaves foreign-package findings as residue.
                        pass
                    case c.Infra.CodemodRelocation.FAMILY_DECLARATION:
                        families.append((
                            file_path,
                            self._captured(
                                finding,
                                c.Infra.CODEMOD_RULE_NAME_METAVARIABLE,
                                readers,
                            ),
                            self._captured(
                                finding,
                                c.Infra.CODEMOD_RULE_FAMILY_METAVARIABLE,
                                readers,
                            ),
                            self._finding_lines(finding)[0],
                        ))
        for file_path, moves in self.import_relocation_targets(
            project_root,
            findings,
        ).items():
            for (source_module, target_module), aliases in moves.items():
                imports[file_path][source_module, target_module].update(aliases)
        return future_files, spans, imports, families

    @staticmethod
    def _finding_lines(finding: p.Infra.ModScanFinding) -> tuple[int, int]:
        """Return the 1-based inclusive line span of one finding.

        Returns:
            The resulting ``tuple[int, int]``.

        Raises:
            TypeError: If ast-grep finding without a line range; or if ast-grep finding
                with a non-integer line.

        """
        start = finding.range["start"]
        end = finding.range["end"]
        if not (isinstance(start, Mapping) and isinstance(end, Mapping)):
            msg = f"ast-grep finding without a line range: {finding.rule_id}"
            raise TypeError(msg)
        start_line = start["line"]
        end_line = end["line"]
        if not (isinstance(start_line, int) and isinstance(end_line, int)):
            msg = f"ast-grep finding with a non-integer line: {finding.rule_id}"
            raise TypeError(msg)
        return start_line + 1, end_line + 1

    @staticmethod
    def _captured(
        finding: p.Infra.ModScanFinding,
        variable: str,
        readers: Mapping[Path, p.Cli.AtomicFileReader],
    ) -> str:
        """Return one metavariable a relocation rule captured or derived.

        Returns:
            One metavariable a relocation rule captured or derived.

        Raises:
            TypeError: If ast-grep finding without metaVariables; or if relocation rule.

        """
        metavariables = u.Infra.mod_native_payload(finding, readers)["metaVariables"]
        if not isinstance(metavariables, Mapping):
            msg = f"ast-grep finding without metaVariables: {finding.rule_id}"
            raise TypeError(msg)
        single = metavariables.get("single")
        transformed = metavariables.get("transformed")
        captured = single.get(variable) if isinstance(single, Mapping) else None
        if captured is None and isinstance(transformed, Mapping):
            captured = transformed.get(variable)
        text = captured.get("text") if isinstance(captured, Mapping) else captured
        if not isinstance(text, str) or not text:
            msg = f"relocation rule {finding.rule_id} did not capture ${variable}"
            raise TypeError(msg)
        return text


__all__: list[str] = ["FlextInfraNamespaceRelocationCascade"]
