"""Runtime import rewrites for namespace refactors."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactorNamespaceCommon,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)


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
                project_root = (
                    FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
                        file_path,
                    )
                )
                if project_root is not None and (
                    FlextInfraUtilitiesDiscovery.contextual_runtime_alias_sources(
                        project_root=project_root,
                        file_path=file_path,
                    )
                ):
                    continue
                try:
                    source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                except OSError:
                    continue
                if FlextInfraUtilitiesParsing.looks_like_facade_file(
                    file_path=file_path,
                    source=source,
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
        package_dir, package_name = FlextInfraUtilitiesDiscovery.package_context(
            file_path,
        )
        if not package_name:
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
        requested_aliases = {
            alias_name for alias_name in aliases if alias_name in local_targets
        }
        if not requested_aliases:
            return None
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        contextual_sources: Mapping[str, frozenset[str]] = (
            FlextInfraUtilitiesDiscovery.contextual_runtime_alias_sources(
                project_root=project_root,
                file_path=file_path,
            )
            if project_root is not None
            else {}
        )
        alias_target_roots: t.MutableStrMapping = dict.fromkeys(
            requested_aliases, package_name
        )
        for alias_name, allowed_sources in contextual_sources.items():
            if alias_name not in requested_aliases or not allowed_sources:
                continue
            alias_target_roots[alias_name] = min(allowed_sources)
        reachability = FlextInfraUtilitiesImportNormalizer.build_reachability(
            package_dir=package_dir,
            package_name=package_name,
        )
        safe_aliases: t.Infra.StrSet = set()
        changes: MutableSequence[str] = []
        action = "migrated" if apply else "planned"
        for alias_name in sorted(requested_aliases):
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
        workspace_package_roots = cls._workspace_package_roots(workspace_root)

        def _transform(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
        ) -> t.Infra.TransformResult:
            alias_moves: MutableMapping[
                t.Infra.StrPair,
                t.Infra.StrSet,
            ] = {}
            class_alias_moves: MutableMapping[
                t.Infra.StrPair,
                t.MutableStrMapping,
            ] = {}
            changed_aliases: t.Infra.StrSet = set()
            for from_import in FlextInfraUtilitiesRope.get_absolute_from_imports(
                rope_project,
                resource,
            ):
                current_source = from_import.module_name
                if not cls._is_runtime_alias_source_candidate(
                    current_source=current_source,
                    target_module=package_name,
                    workspace_package_roots=workspace_package_roots,
                ):
                    continue
                for imported_name, alias_name in from_import.names_and_aliases:
                    bound_name = alias_name or imported_name
                    if bound_name not in safe_aliases:
                        continue
                    target_root = alias_target_roots[bound_name]
                    if alias_name is None and current_source != target_root:
                        alias_moves.setdefault(
                            (current_source, target_root),
                            set(),
                        ).add(bound_name)
                        continue
                    if alias_name == bound_name and imported_name != bound_name:
                        class_alias_moves.setdefault(
                            (current_source, target_root),
                            {},
                        )[imported_name] = bound_name
            for source_module, target_module in sorted(alias_moves):
                moved_aliases = tuple(sorted(alias_moves[source_module, target_module]))
                rewritten = FlextInfraUtilitiesRope.relocate_from_import_aliases(
                    rope_project,
                    resource,
                    source_module=source_module,
                    target_module=target_module,
                    aliases=moved_aliases,
                    apply=True,
                )
                if rewritten is not None:
                    changed_aliases.update(moved_aliases)
            for source_module, target_module in sorted(class_alias_moves):
                alias_map = class_alias_moves[source_module, target_module]
                removed = FlextInfraUtilitiesRope.remove_import_names(
                    rope_project,
                    resource,
                    source_module,
                    tuple(sorted(alias_map)),
                    apply=True,
                )
                if removed is None:
                    continue
                normalized_aliases = tuple(sorted(set(alias_map.values())))
                _ = FlextInfraUtilitiesRope.add_import(
                    rope_project,
                    resource,
                    target_module,
                    normalized_aliases,
                    apply=True,
                )
                changed_aliases.update(normalized_aliases)
            if not changed_aliases:
                return resource.read(), []
            return resource.read(), [
                f"{action} runtime alias import: {alias_name}"
                for alias_name in sorted(changed_aliases)
            ]

        refactored_code, transformer_changes = (
            FlextInfraUtilitiesRope.apply_transformer_to_source(
                source,
                file_path,
                _transform,
            )
        )
        changes.extend(transformer_changes)
        if refactored_code == source:
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
        if apply:
            validation_root = project_root or workspace_root
            ok, report = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                file_path,
                workspace=validation_root,
                updated_source=refactored_code,
                keep_backup=True,
            )
            if not ok:
                return m.Infra.Result(
                    file_path=file_path,
                    success=False,
                    modified=False,
                    error="Protected refactor validation failed",
                    changes=[*changes, *report],
                    refactored_code=source,
                )
            changes.extend(report)
        return m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=apply,
            error=None,
            changes=list(changes),
            refactored_code=(None if apply else refactored_code),
        )

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
        target_leaf = target_module.rsplit(".", maxsplit=1)[-1]
        private_family_prefix = f"{package_name}._{target_leaf}"
        if current_module == private_family_prefix or current_module.startswith(
            f"{private_family_prefix}."
        ):
            return False
        return current_module not in reachability.get(target_module, frozenset())

    @classmethod
    def _workspace_package_roots(cls, workspace_root: Path) -> t.Infra.StrSet:
        return {
            package_name
            for project_root in FlextInfraUtilitiesIteration.discover_project_roots(
                workspace_root.resolve()
            )
            if (
                package_name
                := FlextInfraUtilitiesDiscovery.discover_project_package_name(
                    project_root=project_root,
                )
            )
        }

    @staticmethod
    def _is_runtime_alias_source_candidate(
        *,
        current_source: str,
        target_module: str,
        workspace_package_roots: t.Infra.StrSet,
    ) -> bool:
        if current_source == target_module or current_source.startswith(
            f"{target_module}.",
        ):
            return True
        source_root = current_source.split(".", maxsplit=1)[0]
        return source_root in (
            workspace_package_roots
            | {
                c.Infra.Packages.CORE_UNDERSCORE,
                c.Infra.Directories.TESTS,
                c.Infra.Directories.EXAMPLES,
                c.Infra.Directories.SCRIPTS,
            }
        )

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

                original_source = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                if rewritten == original_source:
                    continue
                _ = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                    file_path,
                    workspace=workspace_root,
                    updated_source=rewritten,
                    keep_backup=True,
                )
        finally:
            rope_project.close()


__all__ = ["FlextInfraUtilitiesRefactorNamespaceRuntime"]
