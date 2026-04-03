"""Runtime import rewrites for namespace refactors."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra._utilities.rope import FlextInfraUtilitiesRope
from flext_infra.constants import FlextInfraConstants as c
from flext_infra.models import FlextInfraModels as m
from flext_infra.refactor._utilities_namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra.transformers._utilities_normalizer import (
    FlextInfraUtilitiesImportNormalizer,
)
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraUtilitiesRefactorNamespaceRuntime(
    FlextInfraUtilitiesRefactorNamespaceCommon
):
    """Rope-backed runtime import rewrite helpers."""

    @classmethod
    def rewrite_import_violations(
        cls,
        *,
        py_files: Sequence[Path],
        project_package: str,
    ) -> None:
        if not py_files:
            return
        rope_project = FlextInfraUtilitiesRope.init_rope_project(
            cls._shared_workspace_root(py_files=py_files),
        )
        try:
            for file_path in py_files:
                if file_path.name == c.Infra.Files.INIT_PY:
                    continue
                try:
                    source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                except OSError:
                    continue
                if FlextInfraUtilitiesParsing.looks_like_facade_file(
                    file_path=file_path, source=source
                ):
                    continue
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if resource is None:
                    continue
                rewritten = FlextInfraUtilitiesRope.collapse_submodule_alias_imports(
                    rope_project,
                    resource,
                    package_name=project_package,
                    aliases=tuple(sorted(c.Infra.RUNTIME_ALIAS_NAMES)),
                    apply=True,
                )
                if rewritten is None:
                    continue
                _ = FlextInfraUtilitiesRope.organize_imports(
                    rope_project,
                    resource,
                    apply=True,
                )
                FlextInfraUtilitiesFormatting.run_ruff_fix(file_path)
        finally:
            rope_project.close()

    @classmethod
    def migrate_runtime_alias_imports(
        cls,
        *,
        workspace_root: Path,
        aliases: t.StrSequence,
        apply: bool,
        project_names: t.StrSequence | None = None,
    ) -> Sequence[m.Infra.Result]:
        normalized_aliases = cls._normalize_runtime_aliases(aliases)
        if not normalized_aliases:
            return []
        resolved_root = workspace_root.resolve()
        project_roots = FlextInfraUtilitiesIteration.discover_project_roots(
            resolved_root,
        )
        if project_names is not None:
            project_roots = [
                project_root
                for project_root in project_roots
                if project_root.name in set(project_names)
            ]
        results: MutableSequence[m.Infra.Result] = []
        for project_root in project_roots:
            files_result = FlextInfraUtilitiesIteration.iter_python_files(
                workspace_root=resolved_root,
                project_roots=[project_root],
                src_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
            )
            if files_result.is_failure:
                results.append(
                    m.Infra.Result(
                        file_path=project_root,
                        success=False,
                        modified=False,
                        error=files_result.error,
                        changes=[],
                        refactored_code=None,
                    )
                )
                continue
            for file_path in files_result.value:
                result = cls._migrate_runtime_alias_imports_in_file(
                    file_path=file_path,
                    workspace_root=resolved_root,
                    aliases=normalized_aliases,
                    apply=apply,
                )
                if result is not None:
                    results.append(result)
        return results

    @staticmethod
    def _normalize_runtime_aliases(aliases: t.StrSequence) -> t.Infra.StrSet:
        return {
            alias.strip()
            for alias in aliases
            if len(alias.strip()) == 1 and alias.strip().islower()
        }

    @classmethod
    def _migrate_runtime_alias_imports_in_file(
        cls,
        *,
        file_path: Path,
        workspace_root: Path,
        aliases: t.Infra.StrSet,
        apply: bool,
    ) -> m.Infra.Result | None:
        if file_path.name == c.Infra.Files.INIT_PY:
            return None
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError as exc:
            return m.Infra.Result(
                file_path=file_path,
                success=False,
                modified=False,
                error=str(exc),
                changes=[],
                refactored_code=None,
            )
        if "from flext_core import" not in source:
            return None
        package_dir, package_name = FlextInfraUtilitiesDiscovery.package_context(
            file_path,
        )
        if not package_name or package_name == c.Infra.Packages.CORE_UNDERSCORE:
            return None
        current_module = cls._module_name_for_file(
            file_path=file_path,
            package_dir=package_dir,
            package_name=package_name,
        )
        if not current_module:
            return None
        local_targets = FlextInfraUtilitiesDiscovery.extract_lazy_import_targets(
            package_dir / c.Infra.Files.INIT_PY,
        )
        reachability = FlextInfraUtilitiesImportNormalizer.build_reachability(
            package_dir=package_dir,
            package_name=package_name,
        )
        rope_project = FlextInfraUtilitiesRope.init_rope_project(workspace_root)
        try:
            resource = FlextInfraUtilitiesRope.get_resource_from_path(
                rope_project,
                file_path.resolve(),
            )
            if resource is None:
                return None
            imported_core_aliases = (
                FlextInfraUtilitiesRope.get_plain_from_imported_names(
                    rope_project,
                    resource,
                    module_name=c.Infra.Packages.CORE_UNDERSCORE,
                )
            )
            requested_aliases = imported_core_aliases & aliases
            if not requested_aliases:
                return None
            imported_local_aliases = (
                FlextInfraUtilitiesRope.get_plain_from_imported_names(
                    rope_project,
                    resource,
                    module_name=package_name,
                )
            )
            safe_aliases: t.Infra.StrSet = set()
            changes: MutableSequence[str] = []
            action = "migrated" if apply else "planned"
            for alias_name in sorted(requested_aliases):
                if alias_name in imported_local_aliases:
                    continue
                target_module = local_targets.get(alias_name, "")
                if not target_module:
                    changes.append(
                        f"skipped missing export runtime alias import: {alias_name}",
                    )
                    continue
                if not cls._safe_runtime_alias_target(
                    alias_name=alias_name,
                    package_name=package_name,
                    current_module=current_module,
                    target_module=target_module,
                    reachability=reachability,
                ):
                    changes.append(
                        f"skipped unsafe runtime alias import: {alias_name}",
                    )
                    continue
                safe_aliases.add(alias_name)
                changes.append(f"{action} runtime alias import: {alias_name}")
            if not safe_aliases:
                return (
                    m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=False,
                        error=None,
                        changes=list(changes),
                        refactored_code=None,
                    )
                    if changes
                    else None
                )
            refactored_code = FlextInfraUtilitiesRope.relocate_from_import_aliases(
                rope_project,
                resource,
                source_module=c.Infra.Packages.CORE_UNDERSCORE,
                target_module=package_name,
                aliases=tuple(sorted(safe_aliases)),
                apply=apply,
            )
            if refactored_code is None:
                return None
            if apply:
                organized = FlextInfraUtilitiesRope.organize_imports(
                    rope_project,
                    resource,
                    apply=True,
                )
                if organized:
                    changes.append("organized imports with rope")
                FlextInfraUtilitiesFormatting.run_ruff_fix(file_path)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=apply,
                error=None,
                changes=list(changes),
                refactored_code=(None if apply else refactored_code),
            )
        finally:
            rope_project.close()

    @classmethod
    def _module_name_for_file(
        cls,
        *,
        file_path: Path,
        package_dir: Path,
        package_name: str,
    ) -> str:
        try:
            return FlextInfraUtilitiesImportNormalizer.file_to_module(
                file_path=file_path,
                package_dir=package_dir,
                package_name=package_name,
            )
        except ValueError:
            return ""

    @staticmethod
    def _safe_runtime_alias_target(
        *,
        alias_name: str,
        package_name: str,
        current_module: str,
        target_module: str,
        reachability: t.FrozensetMapping,
    ) -> bool:
        _ = alias_name
        if not target_module.startswith(f"{package_name}."):
            return True
        if target_module in {current_module, package_name}:
            return False
        return current_module not in reachability.get(target_module, frozenset())

    @staticmethod
    def rewrite_runtime_alias_violations(*, py_files: Sequence[Path]) -> None:
        if not py_files:
            return
        workspace_root = (
            FlextInfraUtilitiesRefactorNamespaceRuntime._shared_workspace_root(
                py_files=py_files,
            )
        )
        rope_project = FlextInfraUtilitiesRope.init_rope_project(workspace_root)
        try:
            for file_path in py_files:
                expected = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(file_path.name)
                if expected is None:
                    continue
                alias_name, expected_suffix = expected
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if resource is None:
                    continue
                class_candidates = [
                    info.name
                    for info in FlextInfraUtilitiesRope.get_class_info(
                        rope_project,
                        resource,
                    )
                    if info.name.endswith(expected_suffix)
                ]
                if len(class_candidates) != 1:
                    continue
                target_class = class_candidates[0]
                lines = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                ).splitlines()
                kept = [
                    line
                    for line in lines
                    if not line.strip().startswith(f"{alias_name} = ")
                ]
                rewritten = (
                    "\n".join(kept).rstrip() + f"\n\n{alias_name} = {target_class}\n"
                )
                _ = file_path.write_text(
                    rewritten,
                    encoding=c.Infra.Encoding.DEFAULT,
                )
        finally:
            rope_project.close()


__all__ = ["FlextInfraUtilitiesRefactorNamespaceRuntime"]
