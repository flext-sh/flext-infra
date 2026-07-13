"""Parent-package resolution (constants-module walk) for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra import c
from flext_infra.codegen._lazy_init_planner_parent_ast import (
    FlextInfraCodegenLazyInitPlannerParentAstMixin,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodegenLazyInitPlannerParentsMixin(
    FlextInfraCodegenLazyInitPlannerParentAstMixin
):
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl

        def _export_names_for_package(self, package_name: str) -> frozenset[str]: ...

    @override
    def _parents_from_constants_module(
        self, module_path: Path, current_pkg: str, visited: set[str] | None = None
    ) -> t.StrSequence:
        """Extract upstream package parents from a constants module.

        Single rule: collect external packages from (1) class bases,
        (2) declared imports, and (3) recursive walks into same-package
        imports. Both class-defining and thin-facade modules go through
        the same path; the recursion handles ``constants.py`` ->
        ``_constants/base.py`` -> ... chains until external packages surface.
        """
        seen = visited if visited is not None else set()
        seen.add(str(module_path.resolve()))
        state = self.rope_workspace.semantic(module_path)
        base_packages = tuple(
            package_name
            for class_info in state.class_infos
            if "Constants" in class_info.name
            for base_name in class_info.bases
            if (
                package_name := self._package_name_from_target(
                    state.declared_imports.get(base_name)
                    or state.semantic_imports.get(base_name, "")
                )
            )
        )
        declared_packages = tuple(
            package_name
            for target in state.declared_imports.values()
            if (package_name := self._package_name_from_target(target))
            and package_name != current_pkg
        )
        same_package_parents = tuple(
            parent
            for target in state.declared_imports.values()
            if target.startswith(f"{current_pkg}.")
            and (
                module_file := self._module_file(self._module_path_from_target(target))
            )
            is not None
            and str(module_file.resolve()) not in seen
            for parent in self._parents_from_constants_module(
                module_file, current_pkg, seen
            )
        )
        rope_parents = tuple(
            dict.fromkeys(
                package_name
                for package_name in (
                    *base_packages,
                    *declared_packages,
                    *same_package_parents,
                )
                if package_name and package_name != current_pkg
            )
        )
        ast_parents = self._parents_from_constants_ast(module_path, current_pkg, seen)
        return tuple(dict.fromkeys((*rope_parents, *ast_parents)))

    @staticmethod
    @override
    def _module_path_from_target(target: str) -> str:
        """Strip the trailing CapWords class name (if any) to yield a module path.

        ``rope`` ``declared_imports`` values are fully-qualified dotted symbol
        paths -- for ``from pkg.sub import FooBar`` the value is
        ``pkg.sub.FooBar``. Drop the last segment when it starts with an
        uppercase letter (class convention).
        """
        if "." not in target:
            return target
        prefix, suffix = target.rsplit(".", maxsplit=1)
        if suffix and suffix[0].isupper():
            return prefix
        return target

    def _resolve_inherited_alias_source(
        self,
        package_names: t.StrSequence,
        alias_name: str,
        *,
        current_pkg: str,
        use_test_runtime_aliases: bool,
    ) -> str:
        """Return the package that owns the given alias in the inheritance chain."""
        candidate_packages: t.StrSequence = tuple(
            name for name in package_names if name
        )
        canonical_target = (
            c.Infra.TEST_RUNTIME_ALIAS_TARGETS.get(alias_name)
            if use_test_runtime_aliases
            else None
        )
        if canonical_target is not None:
            # mro-j47u (codex): TEST_RUNTIME_ALIAS_TARGETS is a StrPair mapping.
            canonical_package = canonical_target[0]
            if canonical_package != current_pkg:
                return canonical_package
        for package_name in candidate_packages:
            if alias_name in self._export_names_for_package(package_name):
                return f"{package_name}"
        # Project-scoped generation only indexes the selected project.
        # When parent packages live outside that Rope workspace, fall back to
        # the nearest declared parent facade instead of dropping the alias.
        for package_name in candidate_packages:
            if (
                package_name
                not in self.rope_workspace.workspace_index.package_dir_by_name
            ):
                return f"{package_name}"
        return ""

    @override
    def _package_name_from_target(self, target: str) -> str:
        """Return the longest workspace package name matching the dotted target."""
        parts = tuple(part for part in target.split(".") if part)
        for size in range(len(parts), 0, -1):
            package_name = ".".join(parts[:size])
            if package_name in self.rope_workspace.workspace_index.package_dir_by_name:
                return package_name
        if not parts:
            return ""
        sibling_project_root = self.rope_workspace.workspace_root.parent / parts[
            0
        ].replace("_", "-")
        sibling_package_root = sibling_project_root / c.Infra.DEFAULT_SRC_DIR / parts[0]
        if (
            sibling_project_root.joinpath(c.Infra.PYPROJECT_FILENAME).is_file()
            and sibling_package_root.joinpath(c.Infra.INIT_PY).is_file()
        ):
            return parts[0]
        return ""
