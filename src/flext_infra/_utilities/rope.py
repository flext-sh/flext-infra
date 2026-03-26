"""Rope Project lifecycle and refactor utilities — zero disk artifacts.

Inspired by pylsp-rope's approach: thin wrappers over rope's refactor APIs
that return ChangeSet objects. Orchestrators decide whether to apply.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import cast

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.project import Project as RopeProject
from rope.base.pynames import DefinedName, ImportedName
from rope.base.pyobjects import AbstractClass, AbstractFunction
from rope.base.pyobjectsdef import PyClass, PyFunction
from rope.base.resources import File as RopeFile
from rope.contrib.findit import (
    Location as RopeLocation,
    find_occurrences as _rope_find_occurrences,
)
from rope.refactor.extract import ExtractMethod
from rope.refactor.importutils import ImportOrganizer
from rope.refactor.inline import create_inline as _rope_create_inline
from rope.refactor.move import MoveGlobal
from rope.refactor.rename import Rename
from rope.refactor.restructure import Restructure

from flext_infra import c, m, p, t


class FlextInfraUtilitiesRope:
    """Rope Project lifecycle and refactor helpers — exposed via u.Infra.*."""

    # ── Project lifecycle ──────────────────────────────────────────

    @staticmethod
    def init_rope_project(
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.ROPE_PROJECT_PREFIX,
        src_dir: str = c.Infra.ROPE_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> t.Infra.RopeProject:
        """Create a rope Project over workspace_root with no disk artifacts.

        ropefolder=None prevents .ropeproject creation.
        Orchestrator controls project_prefix, src_dir, and ignored_resources.
        """
        source_folders = sorted(
            f"{p.name}/{src_dir}"
            for p in workspace_root.iterdir()
            if p.name.startswith(project_prefix) and (p / src_dir).is_dir()
        )
        return RopeProject(
            str(workspace_root),
            ropefolder=None,
            save_objectdb=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )

    # ── Resource resolution ────────────────────────────────────────

    @staticmethod
    def get_file_resource(
        rope_project: t.Infra.RopeProject,
        module_name: str,
    ) -> t.Infra.RopeResource | None:
        """Return rope File for a dotted module name, or None if not found."""
        rel = module_name.replace(".", "/") + ".py"
        try:
            resource = rope_project.get_resource(rel)
            return resource if isinstance(resource, RopeFile) else None
        except ResourceNotFoundError:
            return None

    @staticmethod
    def get_resource_from_path(
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> t.Infra.RopeResource | None:
        """Return rope File for a filesystem Path, or None if outside project."""
        try:
            project_root = Path(rope_project.root.real_path)
            rel = str(file_path.resolve().relative_to(project_root))
            resource = rope_project.get_resource(rel)
            return resource if isinstance(resource, RopeFile) else None
        except (ResourceNotFoundError, ValueError):
            return None

    # ── Semantic analysis (PyCore) ─────────────────────────────────

    @staticmethod
    def find_definition_offset(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        symbol: str,
    ) -> int | None:
        """Return offset of symbol's definition via semantic analysis.

        Uses rope's PyCore to perform semantic lookup, handling inheritance,
        imports, and complex patterns. Falls back to regex for edge cases.
        """
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pyobject = pycore.resource_to_pyobject(resource)
            attrs = pyobject.get_attributes()
            if symbol not in attrs:
                return None
            pyname = attrs[symbol]
            definition_loc = pyname.get_definition_location()
            if definition_loc is None:
                return None
            return definition_loc[1] if isinstance(definition_loc, tuple) else None
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            source = resource.read()
            pattern = re.compile(
                rf"(?:class|def)\s+({re.escape(symbol)})\b|^({re.escape(symbol)})\s*=",
                re.MULTILINE,
            )
            match = pattern.search(source)
            if match is None:
                return None
            return match.start(1) if match.group(1) is not None else match.start(2)

    @staticmethod
    def get_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Mapping[str, str]:
        """Return {local_name: fully_qualified_name} for all imports in a module.

        Replaces manual LibCST/AST import visitors with rope's semantic
        resolution. Handles re-exports, aliased imports, and star imports.
        """
        result: MutableMapping[str, str] = {}
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            for name, pyname in pymodule.get_attributes().items():
                if isinstance(pyname, ImportedName):
                    obj = pyname.get_object()
                    module = obj.get_module()
                    if module is not None:
                        mod_name = module.get_name() or ""
                        result[name] = f"{mod_name}.{name}" if mod_name else name
                    else:
                        result[name] = name
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return result

    @staticmethod
    def get_module_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[str]:
        """Return names of all classes defined (not imported/aliased) in a module."""
        classes: MutableSequence[str] = []
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            for name, pyname in pymodule.get_attributes().items():
                if not isinstance(pyname, DefinedName):
                    continue
                obj = pyname.get_object()
                if isinstance(obj, AbstractClass):
                    classes.append(name)
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return classes

    @staticmethod
    def get_module_class_lines(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Mapping[str, int]:
        """Return {class_name: line_number} for all classes defined in a module.

        Replaces LibCST MetadataWrapper + PositionProvider pattern for
        collecting class names with their source locations.
        """
        result: MutableMapping[str, int] = {}
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            for name, pyname in pymodule.get_attributes().items():
                if not isinstance(pyname, DefinedName):
                    continue
                obj = pyname.get_object()
                if not isinstance(obj, AbstractClass):
                    continue
                _resource, line = pyname.get_definition_location()
                result[name] = line
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return result

    @staticmethod
    def get_class_bases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> Sequence[str]:
        """Return base class names for a class defined in this module.

        Replaces manual ast.ClassDef base inspection and ast.unparse() with
        rope's semantic superclass resolution. Follows imports to resolve
        qualified and aliased base names.
        """
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            attrs = pymodule.get_attributes()
            if class_name not in attrs:
                return []
            obj = attrs[class_name].get_object()
            if not isinstance(obj, (PyClass, AbstractClass)):
                return []
            return [base.get_name() for base in obj.get_superclasses()]
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return []

    @staticmethod
    def get_class_methods(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
        *,
        include_private: bool = False,
    ) -> Mapping[str, str]:
        """Return {method_name: kind} for methods in a class.

        kind is one of 'staticmethod', 'classmethod', 'method'.
        Replaces manual ast.FunctionDef + decorator inspection with rope's
        PyFunction.get_kind() which handles inherited and decorated methods.
        """
        result: MutableMapping[str, str] = {}
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            attrs = pymodule.get_attributes()
            if class_name not in attrs:
                return {}
            obj = attrs[class_name].get_object()
            if not isinstance(obj, (PyClass, AbstractClass)):
                return {}
            for name, member_pyname in obj.get_attributes().items():
                if not include_private and name.startswith("_"):
                    continue
                member_obj = member_pyname.get_object()
                if isinstance(member_obj, (PyFunction, AbstractFunction)):
                    kind = "method"
                    if isinstance(member_obj, PyFunction):
                        kind = member_obj.get_kind()
                    result[name] = kind
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return result

    @staticmethod
    def find_facade_alias(
        resource: t.Infra.RopeResource,
        family: str,
    ) -> str | None:
        """Find facade alias assignment (e.g. ``m = FlextFooModels``) in a module.

        Returns the class name or None if no alias for this family exists.
        Uses c.Infra.FACADE_ALIAS_RE — no CST needed.
        """
        for hit in c.Infra.FACADE_ALIAS_RE.finditer(resource.read()):
            if hit.group(1) == family:
                return hit.group(2)
        return None

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module.

        Combines get_module_class_lines + get_class_bases in one pass.
        """
        result: MutableSequence[m.Infra.ClassInfo] = []
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            for name, pyname in pymodule.get_attributes().items():
                if not isinstance(pyname, DefinedName):
                    continue
                obj = pyname.get_object()
                if not isinstance(obj, AbstractClass):
                    continue
                _res, line = pyname.get_definition_location()
                bases = [b.get_name() for b in obj.get_superclasses()]
                result.append(
                    m.Infra.ClassInfo(
                        name=name,
                        line=line,
                        bases=tuple(bases),
                    )
                )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return result

    @staticmethod
    def get_class_symbol_count(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> int:
        """Return total attribute count (methods, nested classes, assignments) for a class."""
        try:
            pycore = FlextInfraUtilitiesRope._get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            attrs = pymodule.get_attributes()
            if class_name not in attrs:
                return 0
            obj = attrs[class_name].get_object()
            if not isinstance(obj, (PyClass, AbstractClass)):
                return 0
            return len(obj.get_attributes())
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return 0

    # ── Refactoring operations (inspired by pylsp-rope) ────────────

    @staticmethod
    def rename_symbol_workspace(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        new_name: str,
        *,
        apply: bool,
    ) -> Sequence[str]:
        """Rename symbol at offset across the whole project.

        Returns list of file paths changed. Orchestrator decides whether to apply.
        """
        changed_files: t.Infra.MutableStrIndex = {}
        try:
            changes = Rename(rope_project, resource, offset).get_changes(new_name)
        except RefactoringError:
            return []
        for change in changes.changes:
            changed_files[change.resource.path] = 1
        if apply:
            rope_project.do(changes)
        return list(changed_files)

    @staticmethod
    def find_occurrences(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        in_hierarchy: bool = False,
    ) -> Sequence[RopeLocation]:
        """Find all occurrences of the symbol at offset across the project.

        Returns list of rope Location objects with .resource, .lineno, .region.
        Replaces manual grep/ast-grep for cross-file symbol usage search.
        """
        try:
            return list(
                _rope_find_occurrences(
                    rope_project, resource, offset, in_hierarchy=in_hierarchy
                )
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return []

    @staticmethod
    def move_global(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        dest_module: str,
        *,
        apply: bool,
    ) -> Sequence[str]:
        """Move a top-level class/function/variable to another module.

        Updates all imports and references workspace-wide.
        Returns list of changed file paths.
        """
        try:
            refactor = MoveGlobal(rope_project, resource, offset)
            changes = refactor.get_changes(dest_module)
        except RefactoringError:
            return []
        if apply:
            rope_project.do(changes)
        return FlextInfraUtilitiesRope._collect_changed_paths(changes.changes)

    @staticmethod
    def organize_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool,
    ) -> str | None:
        """Sort and deduplicate imports in a module.

        Returns new source if changes were made, None otherwise.
        """
        try:
            organizer = ImportOrganizer(rope_project)
            changes = organizer.organize_imports(resource)
            if changes is None:
                return None
            if apply:
                rope_project.do(changes)
            for change in changes.changes:
                if change.resource == resource:
                    return change.new_contents  # type: ignore[union-attr]
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return None

    @staticmethod
    def restructure(
        rope_project: t.Infra.RopeProject,
        pattern: str,
        goal: str,
        *,
        args: Mapping[str, str] | None = None,
        imports: Sequence[str] | None = None,
        apply: bool,
    ) -> Sequence[str]:
        """Pattern-based find-replace across the project.

        Uses rope's wildcard pattern matching with optional type constraints.
        Returns list of changed file paths.
        """
        try:
            refactor = Restructure(
                rope_project,
                pattern,
                goal,
                args=dict(args) if args else None,
                imports=list(imports) if imports else None,
            )
            changes = refactor.get_changes()
        except RefactoringError:
            return []
        if apply:
            rope_project.do(changes)
        return FlextInfraUtilitiesRope._collect_changed_paths(changes.changes)

    @staticmethod
    def extract_method(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        start_offset: int,
        end_offset: int,
        extracted_name: str,
        *,
        similar: bool = False,
        global_: bool = False,
        apply: bool,
    ) -> str | None:
        """Extract a code range into a new method.

        Returns new source if successful, None otherwise.
        """
        try:
            refactor = ExtractMethod(rope_project, resource, start_offset, end_offset)
            changes = refactor.get_changes(
                extracted_name, similar=similar, global_=global_
            )
        except RefactoringError:
            return None
        if apply:
            rope_project.do(changes)
        for change in changes.changes:
            if change.resource == resource:
                return change.new_contents  # type: ignore[union-attr]
        return None

    @staticmethod
    def inline_symbol(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        remove: bool = True,
        apply: bool,
    ) -> Sequence[str]:
        """Inline a variable, method, or parameter at offset.

        Returns list of changed file paths.
        """
        try:
            refactor = _rope_create_inline(rope_project, resource, offset)
            changes = refactor.get_changes(remove=remove)
        except RefactoringError:
            return []
        if apply:
            rope_project.do(changes)
        return FlextInfraUtilitiesRope._collect_changed_paths(changes.changes)

    # ── Stubs for engine hook integration ──────────────────────────

    @staticmethod
    def run_rope_pre_hooks(path: Path, *, dry_run: bool) -> Sequence[m.Infra.Result]:
        """Pre-hook stub — orchestrator wires transformers here."""
        del path, dry_run
        return []

    @staticmethod
    def run_rope_post_hooks(path: Path, *, dry_run: bool) -> Sequence[m.Infra.Result]:
        """Post-hook stub — cleanup pass after LibCST rules."""
        del path, dry_run
        return []

    # ── Private helpers ────────────────────────────────────────────

    @staticmethod
    def _get_pycore(rope_project: t.Infra.RopeProject) -> p.Infra.RopePyCoreLike:
        """Extract PyCore via protocol — cast needed at rope boundary (no stubs)."""
        return cast("p.Infra.RopePyCoreLike", rope_project.pycore)

    @staticmethod
    def _collect_changed_paths(
        changes: Sequence[p.Infra.RopeChangeLike],
    ) -> MutableSequence[str]:
        """Extract file paths from a rope ChangeSet.changes list."""
        return [change.resource.path for change in changes]


__all__ = ["FlextInfraUtilitiesRope"]
