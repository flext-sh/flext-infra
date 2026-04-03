# pyright: reportMissingTypeStubs=false
"""Shared Rope lifecycle and validation helpers."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from rope.base.change import ChangeContents, ChangeSet
from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.base.project import Project
from rope.base.resources import File
from rope.refactor.importutils import get_module_imports

import flext_infra
from flext_infra import c, m, p, t


class FlextInfraUtilitiesRopeCore:
    """Core Rope lifecycle, hooks, and boundary validation."""

    _post_hooks: ClassVar[MutableSequence[p.Infra.RopePostHook]] = []

    @staticmethod
    def init_rope_project(
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.ROPE_PROJECT_PREFIX,
        src_dir: str = c.Infra.ROPE_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> t.Infra.RopeProject:
        """Create a rope Project over workspace_root with no disk artifacts."""
        source_folders = sorted(
            f"{project.name}/{src_dir}"
            for project in workspace_root.iterdir()
            if project.name.startswith(project_prefix) and (project / src_dir).is_dir()
        )
        return FlextInfraUtilitiesRopeCore._ensure_rope_project(
            Project(
                str(workspace_root),
                ropefolder="",
                save_objectdb=False,
                ignored_resources=list(ignored_resources),
                source_folders=source_folders,
            )
        )

    @staticmethod
    def get_file_resource(
        rope_project: t.Infra.RopeProject,
        module_name: str,
    ) -> t.Infra.RopeResource | None:
        """Return rope File for a dotted module name, or None if not found."""
        relative_path = module_name.replace(".", "/") + c.Infra.Extensions.PYTHON
        for prefix in ("", "src/"):
            try:
                resource = rope_project.get_resource(prefix + relative_path)
                if isinstance(resource, File):
                    return FlextInfraUtilitiesRopeCore._ensure_rope_resource(resource)
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
            relative_path = str(file_path.resolve().relative_to(project_root))
            resource = rope_project.get_resource(relative_path)
            if isinstance(resource, File):
                return FlextInfraUtilitiesRopeCore._ensure_rope_resource(resource)
        except (ResourceNotFoundError, ValueError):
            return None
        return None

    @staticmethod
    def module_syntax_error_type() -> type[BaseException]:
        """Expose rope's ``ModuleSyntaxError`` class without duplicating imports."""
        return ModuleSyntaxError

    @classmethod
    def run_rope_pre_hooks(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Run declarative semantic pre-hooks before local refactors."""
        _ = path, dry_run
        return []

    @classmethod
    def run_rope_post_hooks(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Run workspace-scale semantic passes after local refactors."""
        cls._ensure_default_post_hooks()
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

    @classmethod
    def _ensure_default_post_hooks(cls) -> None:
        if cls._post_hooks:
            return
        cls.register_rope_post_hook(
            flext_infra.FlextInfraRefactorMigrateToClassMRO.run_as_hook,
        )

    @staticmethod
    def get_pycore(rope_project: t.Infra.RopeProject) -> p.Infra.RopePyCoreLike:
        """Extract PyCore via protocol validation at the Rope boundary."""
        pycore = rope_project.pycore
        if not isinstance(pycore, p.Infra.RopePyCoreLike):
            msg = "rope project pycore does not satisfy RopePyCoreLike"
            raise TypeError(msg)
        return pycore

    @staticmethod
    def _ensure_rope_project(value: object) -> t.Infra.RopeProject:
        """Validate one concrete rope Project against the public contract."""
        if not isinstance(value, p.Infra.RopeProjectLike):
            msg = "rope project does not satisfy RopeProjectLike"
            raise TypeError(msg)
        return value

    @staticmethod
    def _ensure_rope_resource(value: object) -> t.Infra.RopeResource:
        """Validate one concrete rope resource against the public contract."""
        if not isinstance(value, p.Infra.RopeResourceLike):
            msg = "rope resource does not satisfy RopeResourceLike"
            raise TypeError(msg)
        return value

    @staticmethod
    def _get_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> p.Infra.RopeModuleImportsLike | None:
        try:
            pymodule = rope_project.get_pymodule(resource)
            return FlextInfraUtilitiesRopeCore._ensure_module_imports(
                get_module_imports(rope_project, pymodule)
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return None

    @staticmethod
    def _ensure_module_imports(
        value: object,
    ) -> p.Infra.RopeModuleImportsLike:
        """Validate one concrete ModuleImports helper against the protocol."""
        if not isinstance(value, p.Infra.RopeModuleImportsLike):
            msg = "rope module imports helper does not satisfy RopeModuleImportsLike"
            raise TypeError(msg)
        return value

    @staticmethod
    def ensure_module_imports(
        value: object,
    ) -> p.Infra.RopeModuleImportsLike:
        """Validate module-import helpers through the public Rope core boundary."""
        return FlextInfraUtilitiesRopeCore._ensure_module_imports(value)

    @staticmethod
    def _absolute_from_import(
        import_info: object,
        *,
        module_name: str,
    ) -> p.Infra.RopeFromImportLike | None:
        absolute_import = FlextInfraUtilitiesRopeCore._absolute_from_import_any(
            import_info
        )
        return (
            absolute_import
            if absolute_import is not None
            and absolute_import.module_name == module_name
            else None
        )

    @staticmethod
    def _absolute_from_import_any(
        import_info: object,
    ) -> p.Infra.RopeFromImportLike | None:
        if not isinstance(import_info, p.Infra.RopeFromImportLike):
            return None
        return import_info if import_info.level == 0 else None

    @staticmethod
    def apply_source_change(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        content: str,
        *,
        description: str,
    ) -> None:
        """Apply a single-file content change via rope ChangeSet."""
        change_set = ChangeSet(description)
        change_set.add_change(ChangeContents(resource, content))
        rope_project.do(change_set)

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


__all__ = ["FlextInfraUtilitiesRopeCore"]
