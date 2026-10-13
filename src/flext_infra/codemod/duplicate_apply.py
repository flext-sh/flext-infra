"""Automatic cure of proven-duplicate objects and manual plans for the rest.

The census rope inventory proves which module-level object is defined two or
more times (``DuplicateGroup``); jscpd proves which code blocks are clones.
Neither unified anything: this engine is the cure. Identity-proven groups whose
definitions are byte-identical and reference no free name evaluate to one
shared object, so the engine keeps the elected owner, deletes every copy,
rebinds the copy consumers' imports to the owner module, and publishes the
joined rewrite through the journaled transaction under the lint, pyrefly and
fresh-import gates. Every other duplicate — free references, generated
modules, published exports, unsupported consumer forms, structural jscpd
clones — becomes a typed manual assisted-cure plan; the engine writes nothing
for those.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.gates.duplication import FlextInfraDuplicationGate
from flext_infra.refactor._census_objects import FlextInfraRefactorCensusObjectsMixin
from flext_infra.transformers import FlextInfraSemanticPublication

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping, MutableSet


class FlextInfraCodemodDuplicateApply(FlextInfraRefactorCensusObjectsMixin):
    """Unify identity-proven duplicate objects; plan every structural clone.

    The owner is the definition in the lowest workspace layer (repository root
    first, then declared member order), ties broken by the existing consumer
    count and finally by path and line. The cure publishes through the
    journaled semantic transaction, so a rejected gate leaves the sources
    byte-identical and the failure loud.
    """

    name: str = "duplicate-apply"

    # ---------------------------------------------------------------- surface

    @classmethod
    def census_duplicates(
        cls,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        groups: t.SequenceOf[m.Infra.DuplicateGroup],
        *,
        apply: bool,
    ) -> p.Result[m.Infra.DuplicateCureOutcome]:
        """Cure the trivial duplicate groups and plan every other duplicate.

        Returns:
            The resulting ``p.Result[m.Infra.DuplicateCureOutcome]``.

        """
        layers = cls._project_layers(root)
        working: MutableMapping[Path, str] = {}
        edits: list[m.Infra.SemanticMigrationEdit] = []
        plans: list[m.Infra.DuplicateCurePlan] = []
        deletions: list[m.Infra.DuplicateDeletion] = []
        bindings = 0
        for group in groups:
            planned = cls._plan_group(
                rope_workspace,
                group,
                layers=layers,
                working=working,
            )
            if isinstance(planned, m.Infra.DuplicateCurePlan):
                plans.append(planned)
                continue
            edits.extend(planned.edits)
            cls._collect_working(working, planned.edits)
            deletions.extend(
                m.Infra.DuplicateDeletion(
                    path=copy.definition.path,
                    name=group.name,
                    line=copy.definition.item.line,
                    project=copy.definition.item.project,
                )
                for copy in planned.copies
            )
            bindings += sum(len(copy.consumer_files) for copy in planned.copies)
        plans.extend(cls._jscpd_plans(root, layers=layers))
        if not apply or not edits:
            return r[m.Infra.DuplicateCureOutcome].ok(
                m.Infra.DuplicateCureOutcome(plans=tuple(plans)),
            )
        published = cls._publish(
            root,
            working=working,
            rope_workspace=rope_workspace,
            edits=tuple(edits),
            deletions=tuple(deletions),
        )
        if published.failure:
            return r[m.Infra.DuplicateCureOutcome].from_failure(published)
        return r[m.Infra.DuplicateCureOutcome].ok(
            m.Infra.DuplicateCureOutcome(
                edits=tuple(edits),
                plans=tuple(plans),
                files_changed=len(edits),
                copies_removed=len(deletions),
                bindings_rewired=bindings,
            ),
        )

    # -------------------------------------------------------------- planning

    @classmethod
    def _plan_group(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        group: m.Infra.DuplicateGroup,
        *,
        layers: t.MappingKV[Path, int],
        working: MutableMapping[Path, str],
    ) -> m.Infra.DuplicateCurePlan | m.Infra.DuplicateGroupCure:
        """Plan one group either as a trivial cure or as a manual plan.

        Returns:
            A ``m.Infra.DuplicateGroupCure`` for the trivial tier or a typed plan.

        """
        definitions = cls._definitions(group, layers=layers)
        blocker = cls._trivial_blocker(rope_workspace, group, definitions)
        if blocker is not None:
            return cls._group_plan(group, definitions, blocker)
        cure = cls._consumer_cure(rope_workspace, definitions)
        if isinstance(cure, str):
            return cls._group_plan(group, definitions, cure)
        if cure.owner.definition.path in working:
            return cls._group_plan(
                group,
                definitions,
                "owner module is already planned by another group in this run",
            )
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for copy in cure.copies:
            if copy is cure.owner:
                continue
            overlapping = (copy.definition.path, *copy.consumer_files)
            if any(path in working for path in overlapping):
                return cls._group_plan(
                    group,
                    definitions,
                    "a copy or its consumers are already planned by another "
                    "group in this run",
                )
            copy_edits = cls._copy_edits(rope_workspace, group, cure.owner, copy)
            if isinstance(copy_edits, str):
                return cls._group_plan(group, definitions, copy_edits)
            edits.extend(copy_edits)
        return m.Infra.DuplicateGroupCure(
            owner=cure.owner,
            copies=tuple(copy for copy in cure.copies if copy is not cure.owner),
            edits=tuple(edits),
        )

    @classmethod
    def _trivial_blocker(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        group: m.Infra.DuplicateGroup,
        definitions: t.SequenceOf[m.Infra.DuplicateDefinition],
    ) -> str | None:
        """Return why the group is outside the trivial contract, or ``None``.

        Returns:
            The blocking reason, or ``None`` when the group is trivially
            curable up to its consumer forms.

        """
        if not group.value_identical:
            return "definitions are not value-identical by the rope fingerprint"
        if len({definition.body for definition in definitions}) != 1:
            return "definition bodies are not byte-identical"
        for definition in definitions:
            blocker = cls._definition_blocker(definition)
            if blocker is not None:
                return blocker
        star = cls._star_importers(rope_workspace, group)
        if star:
            return f"a module star-imports the copy: {star[0]}"
        return None

    @classmethod
    def _definition_blocker(cls, definition: m.Infra.DuplicateDefinition) -> str | None:
        """Return why one definition is outside the trivial contract.

        Returns:
            The blocking reason, or ``None`` when the definition is a pure
            module-level declaration the cure may delete.

        """
        checks: t.SequenceOf[t.Pair[bool, str]] = (
            (
                definition.source.startswith(c.Infra.AUTOGEN_HEADERS),
                "a definition lives in a generated module",
            ),
            (
                bool(c.Infra.GENERATED_EXPORT_SIDECAR_RE.match(definition.path.name)),
                "a definition lives in a generated export sidecar",
            ),
            (
                cls._is_published_export(definition.item),
                "a definition is a published package export",
            ),
            (
                definition.item.scope_path != definition.item.name,
                "a definition is not module-level",
            ),
            (
                definition.item.kind not in c.Infra.DUPLICATE_TRIVIAL_KINDS,
                (
                    "definition kind is outside the trivial contract: "
                    f"{definition.item.kind}"
                ),
            ),
            (
                not cls._statement_is_pure(definition.statement),
                (
                    "a definition references a free name or an impure call, "
                    "so byte identity is not value identity"
                ),
            ),
        )
        return next((reason for blocked, reason in checks if blocked), None)

    @classmethod
    def _definitions(
        cls,
        group: m.Infra.DuplicateGroup,
        *,
        layers: t.MappingKV[Path, int],
    ) -> t.SequenceOf[m.Infra.DuplicateDefinition]:
        """Read every group definition with its exact statement body.

        Returns:
            The resulting definitions ordered by file and line.

        """
        definitions: list[m.Infra.DuplicateDefinition] = []
        for item in group.definitions:
            path = Path(item.file_path).resolve()
            source = path.read_text(encoding=c.DEFAULT_ENCODING)
            statement = cls._definition_statement(source, item)
            definitions.append(
                m.Infra.DuplicateDefinition(
                    item=item,
                    path=path,
                    source=source,
                    statement=statement,
                    body=(
                        cls._statement_body(statement, source)
                        if statement is not None
                        else ""
                    ),
                    consumers=item.references_count,
                    layer=cls._layer_of(path, layers),
                ),
            )
        return sorted(
            definitions,
            key=lambda definition: (
                definition.path.as_posix(),
                definition.item.line,
            ),
        )

    @staticmethod
    def _definition_statement(
        source: str,
        item: m.Infra.Object,
    ) -> ast.stmt | None:
        """Return the module-level statement that defines one inventory object.

        Returns:
            The resulting ``ast.stmt | None``.

        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        for statement in tree.body:
            if not statement.lineno <= item.line <= (statement.end_lineno or 0):
                continue
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else (statement.target,)
                )
                if any(
                    isinstance(target, ast.Name) and target.id == item.name
                    for target in targets
                ):
                    return statement
                continue
            if (
                isinstance(
                    statement,
                    (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
                )
                and statement.name == item.name
            ):
                return statement
        return None

    @staticmethod
    def _statement_body(statement: ast.stmt | None, source: str) -> str:
        """Return the exact source text of one definition statement.

        Returns:
            The resulting ``str``.

        """
        if statement is None or statement.end_lineno is None:
            return ""
        lines = source.splitlines(keepends=True)
        return "".join(lines[statement.lineno - 1 : statement.end_lineno])

    @classmethod
    def _statement_is_pure(cls, statement: ast.stmt | None) -> bool:
        """Return whether the statement is byte-identity-safe to unify.

        Every loaded name must be a builtin and every call must invoke one of
        the pure builtin constructors, so the copied text cannot read a module
        context (``__name__``), an imported global, or a side-effectful
        factory that would make equal text mean different values in two
        modules.

        Returns:
            Whether the statement is a pure module-level definition.

        """
        if statement is None:
            return False
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id not in c.Infra.DUPLICATE_BUILTIN_NAMES
            ):
                return False
            if isinstance(node, ast.Call) and not (
                isinstance(node.func, ast.Name)
                and node.func.id in c.Infra.DUPLICATE_PURE_CONSTRUCTORS
            ):
                return False
        return True

    @classmethod
    def _star_importers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        group: m.Infra.DuplicateGroup,
    ) -> t.StrSequence:
        """Return the workspace modules that star-import a copy module.

        Returns:
            The resulting ``t.StrSequence``.

        """
        copy_modules = {
            item.module_name for item in group.definitions if item.module_name
        }
        importers: list[str] = []
        for entry in rope_workspace.modules():
            path = entry.file_path
            if not path.is_file():
                continue
            try:
                tree = ast.parse(path.read_text(encoding=c.DEFAULT_ENCODING))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                star = (
                    isinstance(node, ast.ImportFrom)
                    and not node.level
                    and node.module in copy_modules
                    and any(alias.name == "*" for alias in node.names)
                )
                if star:
                    importers.append(path.as_posix())
        return tuple(sorted(importers))

    # ------------------------------------------------------------- consumers

    @classmethod
    def _consumer_cure(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        definitions: t.SequenceOf[m.Infra.DuplicateDefinition],
    ) -> m.Infra.DuplicateGroupCure | str:
        """Partition every copy's rope occurrences into rewritable consumers.

        Returns:
            The trivial cure with its elected owner, or the reason the
            consumer forms exceed the trivial contract.

        """
        cure_copies: list[m.Infra.DuplicateCopyCure] = []
        for definition in definitions:
            located = cls._located_occurrences(rope_workspace, definition)
            if isinstance(located, str):
                return located
            consumer_files: list[Path] = []
            in_module_uses = 0
            for path, line in located:
                if path == definition.path and line == definition.item.line:
                    continue
                if path == definition.path:
                    in_module_uses += 1
                    continue
                if cls._is_generated(path):
                    return f"a consumer is generated: {path}"
                if not cls._consumer_is_rebindable(
                    path,
                    line,
                    name=definition.item.name,
                    module=definition.item.module_name,
                ):
                    return (
                        f"consumer {path}:{line} does not rebind the copy "
                        "through its import"
                    )
                if path not in consumer_files:
                    consumer_files.append(path)
            cure_copies.append(
                m.Infra.DuplicateCopyCure(
                    definition=definition,
                    consumer_files=tuple(sorted(consumer_files)),
                    in_module_uses=in_module_uses,
                ),
            )
        owner = min(
            cure_copies,
            key=lambda copy: (
                copy.definition.layer,
                -(
                    len(copy.consumer_files)
                    + copy.in_module_uses
                    + copy.definition.consumers
                ),
                copy.definition.path.as_posix(),
                copy.definition.item.line,
            ),
        )
        return m.Infra.DuplicateGroupCure(
            owner=owner,
            copies=tuple(cure_copies),
            edits=(),
        )

    @classmethod
    def _located_occurrences(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        definition: m.Infra.DuplicateDefinition,
    ) -> t.SequenceOf[t.Pair[Path, int]] | str:
        """Locate every rope occurrence of one definition's binding.

        Returns:
            ``(file, line)`` pairs, or the reason the definition cannot be
            located in its module.

        """
        resource = rope_workspace.resource(definition.path)
        if resource is None:
            return f"definition is not a rope resource: {definition.path}"
        lines = definition.source.splitlines(keepends=True)
        offset = u.Infra.find_identifier_offset_in_lines(
            lines,
            line=definition.item.line,
            symbol=definition.item.name,
        )
        if offset is None:
            return (
                f"definition identifier unavailable: "
                f"{definition.path}:{definition.item.line}"
            )
        hits = u.Infra.find_occurrences(rope_workspace.rope_project, resource, offset)
        located: list[t.Pair[Path, int]] = []
        for hit in hits:
            path = u.Infra.location_file_path(hit)
            line = getattr(hit, "lineno", None)
            if path is None or not isinstance(line, int):
                return f"rope occurrence is not locatable for {definition.path}"
            located.append((path, line))
        return located

    @classmethod
    def _consumer_is_rebindable(
        cls,
        path: Path,
        line: int,
        *,
        name: str,
        module: str,
    ) -> bool:
        """Return whether one consumer occurrence rebinds through its import.

        The trivial tier rewrites ``from <copy module> import <name>`` — one
        alias moved by the rope import owner, whatever else the statement
        imports. So the occurrence is rewritable exactly when it is the alias
        site of such an import or a plain name read bound by one; module
        attribute reads, relative imports and star bindings leave the trivial
        tier with the group.

        Returns:
            Whether the consumer occurrence rebinds as an import.

        """
        try:
            tree = ast.parse(path.read_text(encoding=c.DEFAULT_ENCODING))
        except SyntaxError:
            return False
        imported = False
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.ImportFrom)
                and not node.level
                and node.module == module
            ):
                continue
            if not any(name in {alias.name, alias.asname} for alias in node.names):
                continue
            imported = True
            if node.lineno <= line <= (node.end_lineno or node.lineno):
                return True
        if not imported:
            return False
        return any(
            isinstance(node, ast.Name) and node.id == name and node.lineno == line
            for node in ast.walk(tree)
        )

    @staticmethod
    def _is_generated(path: Path) -> bool:
        """Return whether one path is a generated module or export sidecar.

        Returns:
            Whether the path is generated surface the engine never rewrites.

        """
        if c.Infra.GENERATED_EXPORT_SIDECAR_RE.match(path.name):
            return True
        if not path.is_file():
            return False
        return path.read_text(encoding=c.DEFAULT_ENCODING).startswith(
            c.Infra.AUTOGEN_HEADERS,
        )

    # ----------------------------------------------------------------- edits

    @classmethod
    def _copy_edits(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        group: m.Infra.DuplicateGroup,
        owner: m.Infra.DuplicateCopyCure,
        copy: m.Infra.DuplicateCopyCure,
    ) -> t.SequenceOf[m.Infra.SemanticMigrationEdit] | str:
        """Plan one copy's deletion plus its consumer and in-module rebinds.

        Returns:
            The resulting edits, or the reason the copy cannot be rewritten.

        """
        owner_module = owner.definition.item.module_name
        if not owner_module:
            return f"owner module name is unresolved: {owner.definition.path}"
        if copy.definition.path == owner.definition.path:
            return "owner and copy share one definition"
        deletion = cls._deletion_edit(rope_workspace, group.name, owner_module, copy)
        if isinstance(deletion, str):
            return deletion
        consumer_edits = cls._consumer_edits(
            rope_workspace,
            name=group.name,
            owner_module=owner_module,
            copy=copy,
        )
        if isinstance(consumer_edits, str):
            return consumer_edits
        return (deletion, *consumer_edits)

    @classmethod
    def _deletion_edit(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        name: str,
        owner_module: str,
        copy: m.Infra.DuplicateCopyCure,
    ) -> m.Infra.SemanticMigrationEdit | str:
        """Plan one copy module's statement deletion and its in-module rebind.

        Returns:
            The resulting edit, or the reason the copy cannot be rewritten.

        """
        copy_file = copy.definition.path
        resource = rope_workspace.resource(copy_file)
        if resource is None:
            return f"copy is not a rope resource: {copy_file}"
        original = copy.definition.source
        if copy.in_module_uses:
            rebound = u.Infra.add_import(
                rope_workspace.rope_project,
                resource,
                owner_module,
                (name,),
                apply=False,
            )
            if rebound is None:
                return f"in-module owner import did not plan: {copy_file}"
            updated = cls._remove_statement(rebound, copy.definition)
            if updated is None:
                return f"copy statement vanished while planning: {copy_file}"
        else:
            updated = cls._remove_statement(original, copy.definition)
            if updated is None:
                return f"copy statement did not match while planning: {copy_file}"
        detail = (
            (
                f"deleted duplicate {name} from {copy_file} in favour of "
                f"owner {owner_module}"
            ),
        )
        return m.Infra.SemanticMigrationEdit(
            file_path=copy_file,
            original_source=original,
            updated_source=updated,
            changes=detail,
        )

    @classmethod
    def _consumer_edits(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        name: str,
        owner_module: str,
        copy: m.Infra.DuplicateCopyCure,
    ) -> t.SequenceOf[m.Infra.SemanticMigrationEdit] | str:
        """Rebind every consumer import of one copy onto the owner module.

        Returns:
            The resulting edits, or the reason a consumer cannot be rewritten.

        """
        copy_module = copy.definition.item.module_name
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for consumer in copy.consumer_files:
            consumer_resource = rope_workspace.resource(consumer)
            if consumer_resource is None:
                return f"consumer is not a rope resource: {consumer}"
            planned = u.Infra.plan_from_import_aliases(
                rope_workspace.rope_project,
                consumer_resource,
                source_module=copy_module,
                target_module=owner_module,
                aliases=(name,),
            )
            if planned is None:
                return f"consumer import did not plan: {consumer}"
            detail = (f"rebound {name} from {copy_module} to owner {owner_module}",)
            edits.append(
                m.Infra.SemanticMigrationEdit(
                    file_path=consumer,
                    original_source=consumer_resource.read(),
                    updated_source=planned,
                    changes=detail,
                ),
            )
        return edits

    @classmethod
    def _remove_statement(
        cls,
        source: str,
        definition: m.Infra.DuplicateDefinition,
    ) -> str | None:
        """Delete one definition statement from its module source.

        Returns:
            The rewritten source, or ``None`` when the statement no longer
            matches the planned definition.

        """
        statement = cls._definition_statement(source, definition.item)
        if statement is None or cls._statement_body(statement, source) != (
            definition.body
        ):
            return None
        without = u.Infra.apply_line_ranges(
            source,
            ((statement.lineno, statement.end_lineno or statement.lineno),),
        )
        return u.Infra.normalize_top_level_spacing(without)

    @staticmethod
    def _collect_working(
        working: MutableMapping[Path, str],
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
    ) -> None:
        """Compose validated edits into the shared working map.

        Raises:
            ValueError: If two plans disagree about one file's base.

        """
        for edit in edits:
            current = working.setdefault(edit.file_path, edit.original_source)
            if current != edit.original_source:
                msg = f"duplicate cure plans disagree for {edit.file_path}"
                raise ValueError(msg)
            working[edit.file_path] = edit.updated_source

    # --------------------------------------------------------------- publish

    @classmethod
    def _publish(
        cls,
        root: Path,
        *,
        working: t.MappingKV[Path, str],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
        deletions: t.SequenceOf[m.Infra.DuplicateDeletion],
    ) -> p.Result[bool]:
        """Normalize every planned source and publish the journaled batch.

        Returns:
            The resulting ``p.Result[bool]``.

        Raises:
            ValueError: If source changed after semantic preflight.

        """
        semantic_plans: list[m.Infra.SemanticFilePlan] = []
        for path in sorted(working):
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            content = state.content
            original = next(
                edit.original_source for edit in edits if edit.file_path == path
            )
            if content is None or content.decode(c.DEFAULT_ENCODING) != original:
                msg = f"source changed after duplicate-cure preflight: {path}"
                raise ValueError(msg)
            project_root = u.Infra.project_root(path)
            if project_root is None:
                project_root = root
            normalized = u.Infra.normalize_source(
                root,
                path,
                working[path],
            )
            if normalized.failure:
                return r[bool].from_failure(normalized)
            new_content = normalized.value.encode(c.DEFAULT_ENCODING)
            if content == new_content:
                continue
            semantic_plans.append(
                m.Infra.SemanticFilePlan(
                    project=project_root.resolve(),
                    path=path.resolve(),
                    before=state,
                    desired_content=new_content,
                    desired_mode=state.mode,
                    changes=("duplicate cure",),
                ),
            )

        def verify() -> p.Result[bool]:
            """Prove the published bytes, then run the joint gates.

            Returns:
                The resulting ``p.Result[bool]``.

            """
            rope_workspace.refresh()
            residue = cls._published_residue(edits, deletions)
            if residue is not None:
                return r[bool].fail(residue)
            return FlextInfraWorkspaceChecker(
                repository_root=root,
            ).execute_payload(
                m.Infra.RunCommand(
                    repository_root=root,
                    projects=cls._publication_projects(root, semantic_plans),
                    gates=(c.Infra.LINT, c.Infra.PYREFLY, c.Infra.FRESH_IMPORT),
                ),
            )

        return FlextInfraSemanticPublication.publish_semantic_file_plans(
            semantic_plans,
            repository_root=root,
            validator=verify,
            projection_roots=tuple(sorted(u.Infra.governed_project_roots(root))),
        ).map(_published_true)

    @staticmethod
    def _publication_projects(
        root: Path,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
    ) -> tuple[str, ...]:
        """Collect the governed projects affected by the publication batch.

        Returns:
            Sorted, unique project paths relative to the repository root.

        """
        projects: set[str] = set()
        for plan in plans:
            project = u.Infra.project_root(plan.path)
            if project is not None:
                projects.add(str(project.relative_to(root)))
        return tuple(sorted(projects))

    @classmethod
    def _published_residue(
        cls,
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
        deletions: t.SequenceOf[m.Infra.DuplicateDeletion],
    ) -> str | None:
        """Return the first planned rewrite the published sources contradict.

        Returns:
            The residue description, or ``None`` when the published bytes
            carry every planned deletion and rebind.

        """
        for deletion in deletions:
            published = Path(deletion.path).read_text(encoding=c.DEFAULT_ENCODING)
            probe = m.Infra.Object(
                name=deletion.name,
                kind="constant",
                file_path=str(deletion.path),
                line=deletion.line,
                project=deletion.project,
            )
            if cls._definition_statement(published, probe) is not None:
                return f"published source still defines the copy: {deletion.path}"
        for edit in edits:
            published = Path(edit.file_path).read_text(encoding=c.DEFAULT_ENCODING)
            if published != edit.updated_source and not cls._normalized_equal(
                published,
                edit.updated_source,
            ):
                return (
                    f"published source does not carry the planned rewrite: "
                    f"{edit.file_path}"
                )
        return None

    @staticmethod
    def _normalized_equal(published: str, planned: str) -> bool:
        """Compare published and planned sources ignoring blank-line layout.

        The publication normalizes each file with the real Ruff configuration,
        so the published bytes may differ from the planned text in import
        order and blank-line runs only. Blank-line-insensitive equality keeps
        that normalization visible without re-running the formatter.

        Returns:
            Whether the two sources agree modulo blank lines.

        """
        published_lines = [line for line in published.splitlines() if line.strip()]
        planned_lines = [line for line in planned.splitlines() if line.strip()]
        return published_lines == planned_lines

    # ----------------------------------------------------------------- plans

    @classmethod
    def _group_plan(
        cls,
        group: m.Infra.DuplicateGroup,
        definitions: t.SequenceOf[m.Infra.DuplicateDefinition],
        reason: str,
    ) -> m.Infra.DuplicateCurePlan:
        """Build the manual assisted-cure plan of one non-trivial group.

        Returns:
            The resulting ``m.Infra.DuplicateCurePlan``.

        """
        owner = min(
            definitions,
            key=lambda definition: (
                definition.layer,
                -definition.consumers,
                definition.path.as_posix(),
                definition.item.line,
            ),
        )
        edits = [
            m.Infra.DuplicateCureEdit(
                file_path=owner.path,
                line=owner.item.line,
                action=c.Infra.DUPLICATE_KEEP_ACTION,
                detail=f"keep owner {owner.item.module_name}.{group.name}",
            ),
        ]
        edits.extend(
            m.Infra.DuplicateCureEdit(
                file_path=copy.path,
                line=copy.item.line,
                action=c.Infra.DUPLICATE_DELETE_ACTION,
                detail=(
                    "unify into the owner and delete this definition of "
                    f"{group.name} after rewiring its consumers"
                ),
            )
            for copy in definitions
            if copy is not owner
        )
        return m.Infra.DuplicateCurePlan(
            name=group.name,
            kind=group.kind,
            origin="census",
            reason=reason,
            owner_file_path=owner.path,
            owner_line=owner.item.line,
            owner_project=owner.item.project,
            edits=tuple(edits),
        )

    @classmethod
    def _jscpd_plans(
        cls,
        root: Path,
        *,
        layers: t.MappingKV[Path, int],
    ) -> t.VariadicTuple[m.Infra.DuplicateCurePlan]:
        """Plan every semantic jscpd clone the engine does not auto-unify.

        Returns:
            The resulting plans; an absent report yields none.

        Raises:
            ValueError: If the jscpd report exists but does not validate.

        """
        report_path = (
            root / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_REPORT_FILENAME
        )
        if not report_path.is_file():
            return ()
        parsed = u.Cli.json_parse(report_path.read_text(encoding=c.DEFAULT_ENCODING))
        if parsed.failure:
            msg = f"jscpd report is not parseable: {report_path}: {parsed.error}"
            raise ValueError(msg)
        validated = u.validate_value(
            m.Infra.JscpdReport,
            u.Cli.json_as_mapping(parsed.value),
        )
        if validated.failure:
            msg = f"jscpd report is not a typed report: {report_path}"
            raise ValueError(msg)
        plans: list[m.Infra.DuplicateCurePlan] = []
        seen: set[str] = set()
        for report_duplicate in validated.value.duplicates:
            plan = cls._semantic_clone_plan(
                report_duplicate,
                seen=seen,
                layers=layers,
            )
            if plan is not None:
                plans.append(plan)
        return tuple(plans)

    @classmethod
    def _semantic_clone_plan(
        cls,
        report_duplicate: m.Infra.JscpdDuplicate,
        *,
        seen: MutableSet[str],
        layers: t.MappingKV[Path, int],
    ) -> m.Infra.DuplicateCurePlan | None:
        """Plan one jscpd clone when it is a semantic structural candidate.

        Returns:
            The resulting plan, or ``None`` when the clone is a double-scan
            mirror, already seen, or carries no executable python behavior.

        """
        duplicate = report_duplicate.model_dump(by_alias=True)
        first = duplicate["firstFile"]
        second = duplicate["secondFile"]
        sides = (
            (
                first,
                FlextInfraDuplicationGate.report_file_name(first),
                FlextInfraDuplicationGate.side_span_key(first),
            ),
            (
                second,
                FlextInfraDuplicationGate.report_file_name(second),
                FlextInfraDuplicationGate.side_span_key(second),
            ),
        )
        if sides[0][2] == sides[1][2]:
            return None
        mirror = "|".join(sorted((sides[0][2], sides[1][2])))
        if mirror in seen:
            return None
        seen.add(mirror)
        if not FlextInfraDuplicationGate.is_semantic_clone(duplicate, first, second):
            return None
        owner_side, other_side = sorted(sides, key=cls._side_layer_key(layers))
        return cls._clone_plan(report_duplicate.lines, owner_side, other_side)

    @staticmethod
    def _side_layer_key(
        layers: t.MappingKV[Path, int],
    ) -> Callable[[t.Triple[t.JsonMapping, str, str]], t.Pair[int, str]]:
        """Order one clone side by its containing project layer and path.

        Returns:
            The sort key over ``(side, name, span)`` triples.

        """

        def key(side: t.Triple[t.JsonMapping, str, str]) -> t.Pair[int, str]:
            """Layer then path.

            Returns:
                The resulting ``t.Pair[int, str]``.

            """
            return (
                FlextInfraCodemodDuplicateApply._layer_of(Path(side[1]), layers),
                side[1],
            )

        return key

    @classmethod
    def _clone_plan(
        cls,
        lines: int,
        owner_side: t.Triple[t.JsonMapping, str, str],
        other_side: t.Triple[t.JsonMapping, str, str],
    ) -> m.Infra.DuplicateCurePlan:
        """Build one manual plan for a structural two-sided jscpd clone.

        Returns:
            The resulting ``m.Infra.DuplicateCurePlan``.

        """

        def side_line(side: t.JsonMapping) -> int:
            """Start line.

            Returns:
                The resulting ``int``.

            """
            return u.Cli.json_nested_int(side, "startLoc", "line", default=1)

        return m.Infra.DuplicateCurePlan(
            name=Path(owner_side[1]).name,
            kind="clone",
            origin="jscpd",
            reason=(
                "structural clone: automated extraction has no proven owner, "
                "captured-binding, and consumer-rebinding contract"
            ),
            owner_file_path=Path(owner_side[1]),
            owner_line=side_line(owner_side[0]),
            edits=(
                m.Infra.DuplicateCureEdit(
                    file_path=Path(owner_side[1]),
                    line=side_line(owner_side[0]),
                    action=c.Infra.DUPLICATE_KEEP_ACTION,
                    detail=(
                        f"extend this owner block ({owner_side[2]}, {lines} "
                        "lines) and rewire the clone's consumers onto a "
                        "shared helper"
                    ),
                ),
                m.Infra.DuplicateCureEdit(
                    file_path=Path(other_side[1]),
                    line=side_line(other_side[0]),
                    action=c.Infra.DUPLICATE_DELETE_ACTION,
                    detail=(
                        f"delete the clone block ({other_side[2]}) after the "
                        "manual rewire"
                    ),
                ),
            ),
        )

    # ---------------------------------------------------------------- layers

    @classmethod
    def _project_layers(cls, root: Path) -> t.MappingKV[Path, int]:
        """Order the workspace projects from the most shared layer down.

        The repository root itself is layer ``-1``; declared members follow
        their declaration order, so the lowest index is the most shared layer.

        Returns:
            The resulting mapping of project root to layer index.

        """
        resolved = root.resolve()
        layers: MutableMapping[Path, int] = {resolved: -1}
        for index, project in enumerate(u.Infra.discover_project_roots(resolved)):
            layers.setdefault(project.resolve(), index)
        return layers

    @staticmethod
    def _layer_of(path: Path, layers: t.MappingKV[Path, int]) -> int:
        """Return the lowest layer whose project root contains ``path``.

        Returns:
            The containing layer index, or the unowned layer past the last.

        """
        containing = [
            (project, layer)
            for project, layer in layers.items()
            if path.is_relative_to(project)
        ]
        if not containing:
            return len(layers)
        return max(containing, key=lambda item: len(item[0].parts))[1]


def _published_true(_paths: t.VariadicTuple[Path]) -> bool:
    """Collapse one published-path tuple to the boolean success the caller owns.

    Returns:
        The resulting ``bool``.

    """
    return True


__all__: list[str] = ["FlextInfraCodemodDuplicateApply"]
