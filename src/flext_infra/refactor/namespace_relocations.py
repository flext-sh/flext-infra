"""Rule-catalog relocation cascade shared by the enforcer and the mod loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.transformers import FlextInfraTransformersSemanticPublication

if TYPE_CHECKING:
    from collections.abc import MutableMapping


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
    def scoped_py_files(project_root: Path) -> t.SequenceOf[Path]:
        """Collect the project's namespace-scoped Python files.

        Returns:
            The resulting ``t.SequenceOf[Path]``.

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
    ) -> t.MappingKV[str, c.Infra.CodemodRelocation]:
        """Map every relocation-declaring rule id to its relocation kind.

        Returns:
            The resulting ``t.MappingKV[str, c.Infra.CodemodRelocation]``.

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
        py_files: t.SequenceOf[Path],
        entries: t.SequenceOf[m.Infra.ModScanFinding],
        *,
        scan_root: Path,
    ) -> t.VariadicTuple[t.Pair[c.Infra.CodemodRelocation, m.Infra.ModScanFinding]]:
        """Filter one scan report's entries down to in-scope relocation findings.

        The scope is the project's namespace file set (its declared scan
        directories), so a relocation never reaches a file the namespace pass
        does not govern. Finding paths belong to ``scan_root``; returned targets
        are project-relative even when captured by the workspace scan.

        Returns:
            The resulting ``t.VariadicTuple[
                t.Pair[c.Infra.CodemodRelocation, m.Infra.ModScanFinding]]``.

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
        findings: t.SequenceOf[
            t.Pair[c.Infra.CodemodRelocation, m.Infra.ModScanFinding]
        ],
        py_files: t.SequenceOf[Path],
        gates: t.StrSequence | None = None,
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
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        gates: t.StrSequence | None = None,
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
                    repository_root=published_root, gates=tuple(gates or ())
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
        request: m.Infra.NamespaceRelocationRequest,
        *,
        rope_project: p.Infra.RopeProject,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Compose native relocation effects without performing any Rope changes.

        Returns:
            The composed file plans, or the first planning failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        initialized = self._capture_relocation_state(request)
        if initialized.failure:
            return result_type.from_failure(initialized)
        state = initialized.value
        names, spans, imports, classes = self._grouped_targets(
            request.project_root, request.findings
        )
        for file_path, statement_lines in spans.items():
            state.working[file_path] = u.Infra.plan_hoist_inline_imports(
                file_path, state.working[file_path], statement_lines
            )
        effect = self._relocate_imports(state, rope_project, imports)
        if effect.failure:
            return result_type.from_failure(effect)
        selected = self._declaration_targets(request, state, names, classes)
        if selected.failure:
            return result_type.from_failure(selected)
        effect = self._prepare_destinations(state, selected.value)
        if effect.failure:
            return result_type.from_failure(effect)
        effect = self._move_declarations(request, state, rope_project, selected.value)
        if effect.failure:
            return result_type.from_failure(effect)
        return self._relocation_plans(request, state)

    @staticmethod
    def _capture_relocation_state(
        request: m.Infra.NamespaceRelocationRequest,
    ) -> p.Result[m.Infra.NamespaceRelocationState]:
        """Bind the working bytes after checking every target selection.

        Returns:
            Mutable candidate state, or the first selection failure.

        """
        selected = frozenset(request.py_files)
        for _relocation, finding in request.findings:
            path = request.project_root / finding.file
            if not path.is_relative_to(request.project_root) or path not in selected:
                return r[m.Infra.NamespaceRelocationState].fail(
                    f"relocation declaration is outside its selected targets: {path}"
                )
            if path not in request.sources:
                return r[m.Infra.NamespaceRelocationState].fail(
                    f"relocation source lacks its working view: {path}"
                )
        return r[m.Infra.NamespaceRelocationState].ok(
            m.Infra.NamespaceRelocationState(
                working=dict(request.sources), originals={}, modes={}
            )
        )

    @staticmethod
    def _relocate_imports(
        state: m.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        imports: t.MappingKV[Path, t.MappingKV[t.StrPair, set[str]]],
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
                if updated is None:
                    return r[bool].fail(
                        f"native import relocation did not plan: {file_path}"
                    )
                working[file_path] = updated
        return r[bool].ok(value=True)

    @staticmethod
    def _declaration_targets(
        request: m.Infra.NamespaceRelocationRequest,
        state: m.Infra.NamespaceRelocationState,
        names: t.MappingKV[c.Infra.CodemodRelocation, t.MappingKV[Path, set[str]]],
        classes: t.SequenceOf[tuple[Path, str, str, int]],
    ) -> p.Result[list[tuple[Path, str, Path]]]:
        """Elect native class, protocol and type-alias destinations in phase order.

        Returns:
            Ordered declaration moves, or the first unsupported relocation failure.

        """
        project_root = request.project_root
        working = state.working
        declarations: list[tuple[Path, str, Path]] = []
        if classes:
            layout = u.Infra.layout(project_root)
            if layout is None:
                return r[list[tuple[Path, str, Path]]].fail(
                    f"facade-class relocation requires a project layout: {project_root}"
                )
            declarations.extend(
                (
                    path,
                    name,
                    u.Infra.class_target_file(
                        package_dir=layout.package_dir,
                        source_file=path,
                        class_name=name,
                        family=family,
                    ),
                )
                for path, name, family, _line in classes
            )
        for relocation, names_by_file in names.items():
            if relocation is c.Infra.CodemodRelocation.FUTURE_ANNOTATIONS:
                for path in names_by_file:
                    working[path] = u.Infra.plan_future_annotations(working[path])
                continue
            if relocation not in {
                c.Infra.CodemodRelocation.PROTOCOL,
                c.Infra.CodemodRelocation.TYPING_ALIAS,
            }:
                return r[list[tuple[Path, str, Path]]].fail(
                    f"relocation has no native planning primitive: {relocation}"
                )
            filename = (
                c.Infra.PROTOCOLS_PY
                if relocation is c.Infra.CodemodRelocation.PROTOCOL
                else c.Infra.TYPINGS_PY
            )
            declarations.extend(
                (
                    path,
                    name,
                    u.Infra.canonical_target_file(
                        project_root=project_root,
                        source_file=path,
                        filename=filename,
                    ),
                )
                for path, declared in names_by_file.items()
                for name in sorted(declared)
            )
        return r[list[tuple[Path, str, Path]]].ok(declarations)

    @staticmethod
    def _prepare_destinations(
        state: m.Infra.NamespaceRelocationState,
        declarations: t.SequenceOf[tuple[Path, str, Path]],
    ) -> p.Result[bool]:
        """Seed each absent destination; an existing unread file fails.

        Returns:
            Acceptance of each destination, or the first foreign-file failure.

        """
        working = state.working
        for path, _name, target in declarations:
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
            state.originals[target] = destination.value
            state.modes[target] = source.value.mode
            working[target] = f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        return r[bool].ok(value=True)

    @classmethod
    def _move_declarations(
        cls,
        request: m.Infra.NamespaceRelocationRequest,
        state: m.Infra.NamespaceRelocationState,
        rope_project: p.Infra.RopeProject,
        declarations: t.SequenceOf[tuple[Path, str, Path]],
    ) -> p.Result[bool]:
        """Apply native move effects to candidate bytes, never to the filesystem.

        Returns:
            Acceptance of all declaration effects, or their first native failure.

        """
        working = state.working
        for path, name, target in declarations:
            snapshot = cls._relocation_snapshot(request, state, rope_project)
            coordinate = Path(snapshot.root.real_path)
            resource = u.Infra.require_file_resource(
                snapshot.get_resource(path.relative_to(coordinate).as_posix()),
                path,
            )
            offset = cls._declaration_offset(snapshot, resource, working[path], name)
            if offset.failure:
                return r[bool].from_failure(offset)
            changes = u.Infra.create_move(snapshot, resource, offset.value).get_changes(
                u.Infra.require_file_resource(
                    snapshot.get_resource(target.relative_to(coordinate).as_posix()),
                    target,
                ),
                resources=[
                    u.Infra.require_file_resource(
                        snapshot.get_resource(
                            candidate.relative_to(coordinate).as_posix()
                        ),
                        candidate,
                    )
                    for candidate in working
                    if candidate.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                ],
            )
            for change in changes.changes:
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
    def _relocation_snapshot(
        request: m.Infra.NamespaceRelocationRequest,
        state: m.Infra.NamespaceRelocationState,
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
        request: m.Infra.NamespaceRelocationRequest,
        state: m.Infra.NamespaceRelocationState,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind every changed candidate source to its destination state once.

        Returns:
            The relocation file plans, or the first destination read failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        plans: list[m.Infra.CodegenFilePlan] = []
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
        findings: t.SequenceOf[
            t.Pair[c.Infra.CodemodRelocation, m.Infra.ModScanFinding]
        ],
    ) -> t.MappingKV[Path, t.MappingKV[t.StrPair, set[str]]]:
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
        targets: MutableMapping[Path, MutableMapping[t.StrPair, set[str]]] = (
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
        findings: t.SequenceOf[
            t.Pair[c.Infra.CodemodRelocation, m.Infra.ModScanFinding]
        ],
    ) -> tuple[
        MutableMapping[
            c.Infra.CodemodRelocation,
            MutableMapping[Path, set[str]],
        ],
        MutableMapping[Path, list[t.IntPair]],
        MutableMapping[Path, MutableMapping[t.StrPair, set[str]]],
        list[tuple[Path, str, str, int]],
    ]:
        """Group findings into the batched targets each relocation consumes.

        Returns:
            The resulting ``(names, spans, imports, classes)`` batches.

        """
        names: MutableMapping[
            c.Infra.CodemodRelocation,
            MutableMapping[Path, set[str]],
        ] = defaultdict(lambda: defaultdict(set))
        spans: MutableMapping[Path, list[t.IntPair]] = defaultdict(list)
        imports: MutableMapping[Path, MutableMapping[t.StrPair, set[str]]] = (
            defaultdict(lambda: defaultdict(set))
        )
        classes: list[tuple[Path, str, str, int]] = []
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
                        names[relocation].setdefault(file_path, set())
                    case (
                        c.Infra.CodemodRelocation.PACKAGE_ROOT_IMPORT
                        | c.Infra.CodemodRelocation.OWN_PACKAGE_IMPORT
                    ):
                        # Grouped by the public import_relocation_targets owner,
                        # which binds own-package symbols to the own package and
                        # leaves foreign-package findings as residue.
                        pass
                    case c.Infra.CodemodRelocation.FACADE_CLASS:
                        classes.append((
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
                    case _:
                        names[relocation][file_path].add(
                            self._captured(
                                finding,
                                c.Infra.CODEMOD_RULE_NAME_METAVARIABLE,
                                readers,
                            ),
                        )
        for file_path, moves in self.import_relocation_targets(
            project_root,
            findings,
        ).items():
            for (source_module, target_module), aliases in moves.items():
                imports[file_path][source_module, target_module].update(aliases)
        return names, spans, imports, classes

    @staticmethod
    def _finding_lines(finding: m.Infra.ModScanFinding) -> t.IntPair:
        """Return the 1-based inclusive line span of one finding.

        Returns:
            The resulting ``t.IntPair``.

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
        finding: m.Infra.ModScanFinding,
        variable: str,
        readers: t.MappingKV[Path, p.Cli.AtomicFileReader],
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
