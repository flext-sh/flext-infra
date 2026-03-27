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
from typing import ClassVar, cast

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.project import Project as RopeProject
from rope.base.pynames import DefinedName, ImportedName
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyClass
from rope.base.resources import File as RopeFile
from rope.contrib.findit import (
    Location as RopeLocation,
    find_occurrences as _rope_find_occurrences,
)
from rope.refactor.rename import Rename

from flext_infra import c, m, p, t


class FlextInfraUtilitiesRope:
    """Rope Project lifecycle and refactor helpers — exposed via u.Infra.*."""

    _post_hooks: ClassVar[MutableSequence[p.Infra.RopePostHook]] = []

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

        ropefolder="" prevents .ropeproject creation.
        Orchestrator controls project_prefix, src_dir, and ignored_resources.
        """
        source_folders = sorted(
            f"{p.name}/{src_dir}"
            for p in workspace_root.iterdir()
            if p.name.startswith(project_prefix) and (p / src_dir).is_dir()
        )
        return RopeProject(
            str(workspace_root),
            ropefolder="",
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
        for prefix in ("", "src/"):
            try:
                resource = rope_project.get_resource(prefix + rel)
                if isinstance(resource, RopeFile):
                    return resource
            except ResourceNotFoundError:
                continue
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
        source = resource.read()
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
            line_number = (
                definition_loc[1] if isinstance(definition_loc, tuple) else None
            )
            if line_number is None:
                return None
            return FlextInfraUtilitiesRope._line_offset_for_symbol(
                source=source,
                line_number=line_number,
                symbol=symbol,
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
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

    @staticmethod
    def get_class_bases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> Sequence[str]:
        """Return base class names for a given class in a module."""
        infos = FlextInfraUtilitiesRope.get_class_info(rope_project, resource)
        for info in infos:
            if info.name == class_name:
                return list(info.bases)
        return []

    @staticmethod
    def get_class_methods(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
        *,
        include_private: bool = False,
    ) -> Mapping[str, str]:
        """Return {method_name: kind} for methods of a class.

        kind is one of 'staticmethod', 'classmethod', or 'method'.
        By default excludes private methods (starting with _).
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
            for name, pyname in obj.get_attributes().items():
                if not include_private and name.startswith("_"):
                    continue
                child = pyname.get_object()
                kind = "method"
                if hasattr(child, "get_kind"):
                    raw_kind = child.get_kind()
                    if raw_kind == "staticmethod":
                        kind = "staticmethod"
                    elif raw_kind == "classmethod":
                        kind = "classmethod"
                result[name] = kind
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pass
        return result

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

    # ── Engine hook integration ────────────────────────────────────

    @classmethod
    def run_rope_pre_hooks(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Run declarative semantic pre-hooks before local CST refactors."""
        _ = path, dry_run
        return []

    @classmethod
    def run_rope_post_hooks(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Run workspace-scale semantic passes after local CST refactors."""
        results: MutableSequence[m.Infra.Result] = []
        for hook in cls._post_hooks:
            results.extend(hook(path, dry_run=dry_run))
        return results

    @classmethod
    def register_rope_post_hook(
        cls,
        hook: p.Infra.RopePostHook,
    ) -> None:
        """Register a post-processing hook for rope refactoring pipelines."""
        if hook not in cls._post_hooks:
            cls._post_hooks.append(hook)

    # ── Private helpers ────────────────────────────────────────────

    @staticmethod
    def _get_pycore(rope_project: t.Infra.RopeProject) -> p.Infra.RopePyCoreLike:
        """Extract PyCore via protocol — cast needed at rope boundary (no stubs)."""
        return cast("p.Infra.RopePyCoreLike", rope_project.pycore)

    @staticmethod
    def _line_offset_for_symbol(
        *,
        source: str,
        line_number: int,
        symbol: str,
    ) -> int | None:
        """Convert rope line metadata into a character offset for refactor APIs."""
        lines = source.splitlines(keepends=True)
        if line_number < 1 or line_number > len(lines):
            return None
        line = lines[line_number - 1]
        column = line.find(symbol)
        if column < 0:
            return None
        return sum(len(item) for item in lines[: line_number - 1]) + column


__all__ = ["FlextInfraUtilitiesRope"]
