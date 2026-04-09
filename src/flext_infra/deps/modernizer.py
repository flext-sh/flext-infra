"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from tomlkit.items import AoT, Table

from flext_infra import (
    FlextInfraConsolidateGroupsPhase,
    FlextInfraEnsureCoverageConfigPhase,
    FlextInfraEnsureExtraPathsPhase,
    FlextInfraEnsureFormattingToolingPhase,
    FlextInfraEnsureMypyConfigPhase,
    FlextInfraEnsureNamespaceToolingPhase,
    FlextInfraEnsurePydanticMypyConfigPhase,
    FlextInfraEnsurePyreflyConfigPhase,
    FlextInfraEnsurePyrightConfigPhase,
    FlextInfraEnsurePytestConfigPhase,
    FlextInfraEnsureRuffConfigPhase,
    FlextInfraExtraPathsManager,
    FlextInfraInjectCommentsPhase,
    FlextInfraProjectClassifier,
    FlextInfraUtilitiesTomlParse,
    c,
    r,
    t,
    u,
)


class FlextInfraPyprojectModernizer:
    """Modernize all workspace pyproject.toml files."""

    ROOT = u.Infra.resolve_workspace_root(__file__)

    def __init__(
        self,
        workspace_root: Path | None = None,
        *,
        workspace: Path | None = None,
    ) -> None:
        """Initialize pyproject modernizer."""
        self.root = workspace_root or workspace or self.ROOT
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.is_failure:
            msg = tool_config_result.error or "failed to load deps tool config"
            raise ValueError(msg)
        self._tool_config = tool_config_result.value
        self._paths_manager: FlextInfraExtraPathsManager | None = None

    @property
    def paths_manager(self) -> FlextInfraExtraPathsManager:
        """Create the extra-paths manager only when a phase actually needs it."""
        if self._paths_manager is None:
            self._paths_manager = FlextInfraExtraPathsManager(
                workspace_root=self.root,
            )
        return self._paths_manager

    def _classify_project(self, project_dir: Path) -> r[str]:
        """Classify project kind for pyright/coverage config selection."""
        kind = FlextInfraProjectClassifier(project_dir).classify().project_kind
        return r[str].ok(kind)

    def _ensure_build_system(self, doc: t.Infra.TomlDocument) -> t.StrSequence:
        """Ensure canonical build-system backend/requirements."""
        changes: MutableSequence[str] = []
        build_system = u.Cli.toml_get_table(doc, "build-system")
        if build_system is None:
            build_system = u.Cli.toml_table()
            doc["build-system"] = build_system
            changes.append("created [build-system]")
        expected_backend = "hatchling.build"
        backend_item = u.Cli.toml_get_item(build_system, "build-backend")
        current_backend = u.norm_str(u.Cli.toml_unwrap_item(backend_item))
        if current_backend != expected_backend:
            build_system["build-backend"] = expected_backend
            changes.append("build-system.build-backend set to hatchling.build")
        expected_requires = ["hatchling"]
        requires_item = u.Cli.toml_get_item(build_system, "requires")
        current_requires = sorted(
            u.Cli.toml_as_string_list(requires_item),
        )
        if current_requires != expected_requires:
            build_system["requires"] = u.Cli.toml_array(expected_requires)
            changes.append("build-system.requires set to ['hatchling']")
        # Backend is now guaranteed to be hatchling.build (set above or already correct)
        tool_table = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        hatch_table = u.Cli.toml_ensure_table(tool_table, "hatch")
        metadata_table = u.Cli.toml_ensure_table(hatch_table, "metadata")
        allow_value = u.Infra.get(metadata_table, "allow-direct-references")
        current_allow = u.norm_str(str(allow_value), case="lower") == "true"
        if not current_allow:
            metadata_table["allow-direct-references"] = True
            changes.append("tool.hatch.metadata.allow-direct-references set to true")
        return changes

    @staticmethod
    def _ordered_keys(
        keys: t.StrSequence,
        *,
        preferred_first: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Return keys with optional preferred-first order then alphabetical."""
        preferred = list(preferred_first or [])
        key_set = set(keys)
        ordered: MutableSequence[str] = [key for key in preferred if key in key_set]
        remaining = sorted(key for key in keys if key not in set(ordered))
        ordered.extend(remaining)
        return ordered

    @classmethod
    def _reorder_table_inplace(
        cls,
        table: t.Infra.TomlTable,
        *,
        preferred_first: t.StrSequence | None = None,
        table_key: str | None = None,
    ) -> None:
        """Reorder table keys in-place recursively (tables/AoT items)."""
        if table_key == "per-file-ignores":
            return
        original_keys = [str(key) for key in table]
        ordered_keys = cls._ordered_keys(
            original_keys,
            preferred_first=preferred_first,
        )
        if ordered_keys == original_keys:
            for key in ordered_keys:
                value = table[key]
                if isinstance(value, Table):
                    cls._reorder_table_inplace(value, table_key=key)
                elif isinstance(value, AoT):
                    for entry in value.body:
                        cls._reorder_table_inplace(entry, table_key=key)
            return
        items: MutableMapping[str, t.Infra.TomlItem] = {
            key: table[key] for key in original_keys
        }
        for key in original_keys:
            del table[key]
        for key in ordered_keys:
            value = items[key]
            if isinstance(value, Table):
                cls._reorder_table_inplace(value, table_key=key)
            elif isinstance(value, AoT):
                for entry in value.body:
                    cls._reorder_table_inplace(entry, table_key=key)
            table[key] = value

    @classmethod
    def _reorder_document_inplace(cls, doc: t.Infra.TomlDocument) -> None:
        """Apply deterministic ordering for top-level groups and nested tables."""
        root_keys = [str(key) for key in doc]
        ordered_root = cls._ordered_keys(
            root_keys,
            preferred_first=("build-system", "dependency-groups", "project", "tool"),
        )
        if ordered_root != root_keys:
            root_items: MutableMapping[
                str, t.Infra.TomlItem | t.Infra.TomlContainer
            ] = {key: doc[key] for key in root_keys}
            for key in root_keys:
                del doc[key]
            for key in ordered_root:
                doc[key] = root_items[key]
        tool_child = u.Cli.toml_get_table(doc, "tool")
        if tool_child is not None:
            cls._reorder_table_inplace(tool_child, table_key="tool")
        for key in ordered_root:
            if key == "tool":
                continue
            value = doc[key]
            if isinstance(value, Table):
                cls._reorder_table_inplace(value, table_key=key)
            elif isinstance(value, AoT):
                for entry in value.body:
                    cls._reorder_table_inplace(entry, table_key=key)

    def find_pyproject_files(
        self,
        *,
        project_paths: Sequence[Path] | None = None,
    ) -> Sequence[Path]:
        """Find all workspace pyproject.toml files."""
        result = u.Infra.find_all_pyproject_files(
            self.root,
            skip_dirs=c.Infra.SKIP_DIRS,
            project_paths=project_paths,
        )
        return result.fold(
            on_failure=lambda _: [],
            on_success=lambda v: sorted(v),
        )

    def process_file(
        self,
        path: Path,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
    ) -> t.StrSequence:
        """Process one pyproject.toml file and collect changes."""
        try:
            original_rendered = path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return ["invalid TOML"]
        doc = u.Cli.toml_read(path)
        if doc is None:
            return ["invalid TOML"]
        is_root = path.parent.resolve() == self.root.resolve()
        project_kind = "core"
        if not is_root:
            kind_result = self._classify_project(path.parent)
            if kind_result.is_success:
                project_kind = kind_result.value
        changes: MutableSequence[str] = []
        changes.extend(self._ensure_build_system(doc))
        tool_item = u.Cli.toml_get_table(doc, c.Infra.TOOL)
        if tool_item is None:
            tool_item = u.Cli.toml_table()
            doc[c.Infra.TOOL] = tool_item
        poetry_item = u.Cli.toml_get_table(tool_item, c.Infra.POETRY)
        if poetry_item is not None:
            group_item = u.Cli.toml_get_table(poetry_item, c.Infra.GROUP)
            if group_item is not None:
                empty_groups: MutableSequence[str] = []
                for name in u.Cli.toml_table_string_keys(group_item):
                    group_dep_item = u.Cli.toml_get_table(group_item, name)
                    if group_dep_item is None:
                        continue
                    deps_item = u.Cli.toml_get_table(
                        group_dep_item, c.Infra.DEPENDENCIES
                    )
                    if deps_item is not None and not deps_item:
                        empty_groups.append(name)
                for name in empty_groups:
                    del group_item[name]
                    changes.append(f"removed empty poetry group '{name}'")
                if not group_item:
                    del poetry_item[c.Infra.GROUP]
                    changes.append("removed empty poetry group container")
        changes.extend(FlextInfraConsolidateGroupsPhase().apply(doc, canonical_dev))
        changes.extend(FlextInfraEnsurePytestConfigPhase(self._tool_config).apply(doc))
        changes.extend(
            FlextInfraEnsurePyreflyConfigPhase(self._tool_config).apply(
                doc,
                is_root=is_root,
                project_dir=path.parent,
                paths_manager=self.paths_manager,
            ),
        )
        changes.extend(FlextInfraEnsureMypyConfigPhase(self._tool_config).apply(doc))
        changes.extend(
            FlextInfraEnsurePydanticMypyConfigPhase(self._tool_config).apply(doc),
        )
        changes.extend(
            FlextInfraEnsureFormattingToolingPhase(self._tool_config).apply(doc),
        )
        changes.extend(FlextInfraEnsureNamespaceToolingPhase().apply(doc, path=path))
        changes.extend(
            FlextInfraEnsureRuffConfigPhase(self._tool_config).apply(
                doc,
                path=path,
            ),
        )
        changes.extend(
            FlextInfraEnsurePyrightConfigPhase(self._tool_config).apply(
                doc,
                is_root=is_root,
                workspace_root=self.root,
                project_dir=path.parent,
                project_kind=project_kind,
                paths_manager=self.paths_manager,
            ),
        )
        changes.extend(
            FlextInfraEnsureCoverageConfigPhase(self._tool_config).apply(
                doc,
                project_kind=project_kind,
            ),
        )
        changes.extend(
            FlextInfraEnsureExtraPathsPhase().apply(
                doc,
                path=path,
                is_root=is_root,
                dry_run=dry_run,
                paths_manager=self.paths_manager,
            ),
        )
        self._reorder_document_inplace(doc)
        rendered = doc.as_string()
        if not skip_comments:
            rendered, comment_changes = FlextInfraInjectCommentsPhase().apply(rendered)
            changes.extend(comment_changes)
        normalized_original = original_rendered.rstrip() + "\n"
        normalized_rendered = rendered.rstrip() + "\n"
        if normalized_rendered == normalized_original:
            return []
        if not dry_run:
            u.write_file(path, rendered, encoding=c.Infra.Encoding.DEFAULT)
        return changes

    def run(self, args: t.Infra.CliNamespace, cli: u.Infra.CliArgs) -> int:
        """Run pyproject modernization for the workspace."""
        check_mode = bool(args.audit or cli.check)
        dry_run = bool(cli.dry_run or check_mode)
        project_names = cli.project_names() or []
        project_paths: Sequence[Path] | None = None
        if project_names:
            selected_projects = u.Infra.resolve_projects(self.root, project_names)
            if selected_projects.is_failure:
                u.Infra.error(
                    selected_projects.error or "failed to resolve selected projects",
                )
                return 2
            project_paths = [project.path for project in selected_projects.value]
        files = self.find_pyproject_files(project_paths=project_paths)
        root_doc: t.Cli.TomlDocument | None = u.Cli.toml_read(
            self.root / c.Infra.Files.PYPROJECT_FILENAME
        )
        if root_doc is None:
            return 2
        canonical_dev: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(
            FlextInfraUtilitiesTomlParse.canonical_dev_dependencies(root_doc),
        )
        violations: MutableMapping[str, t.StrSequence] = {}
        total = 0
        for file_path in files:
            changes = self.process_file(
                file_path,
                canonical_dev=canonical_dev,
                dry_run=dry_run,
                skip_comments=bool(args.skip_comments),
            )
            if not changes:
                continue
            rel = str(file_path.relative_to(self.root))
            violations[rel] = changes
            total += len(changes)
        if violations:
            for rel_path, changes in violations.items():
                u.Infra.info(f"{rel_path}:")
                for change in changes:
                    u.Infra.info(f"  - {change}")
            u.Infra.info(
                f"Total: {total} change(s) across {len(violations)} file(s)",
            )
            if dry_run:
                u.Infra.info("(dry-run — no files modified)")
        if check_mode and total > 0:
            return 1
        if not dry_run and (not bool(getattr(args, "skip_check", False))):
            return self._run_build_check(files)
        return 0

    def _run_build_check(self, files: Sequence[Path]) -> int:
        """Validate pyproject.toml files have hatchling build backend."""
        has_warning = False
        for path in files:
            doc = u.Cli.toml_read(path)
            if doc is None:
                has_warning = True
                continue
            build_sys = u.Cli.toml_get_table(doc, "build-system")
            if build_sys is None:
                u.Infra.info(f"{path}: missing [build-system]")
                has_warning = True
                continue
            backend_item = u.Cli.toml_get_item(build_sys, "build-backend")
            backend = u.norm_str(u.Cli.toml_unwrap_item(backend_item))
            if backend != "hatchling.build":
                u.Infra.info(f"{path}: expected hatchling.build, got {backend}")
                has_warning = True
        return 1 if has_warning else 0

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Run the pyproject modernizer CLI."""
        parser = u.Infra.create_parser(
            "flext-infra deps modernize",
            "Modernize workspace pyproject files",
            flags=u.Infra.SharedFlags(
                include_apply=True,
                include_check=True,
                include_project=True,
            ),
        )
        _ = parser.add_argument("--audit", action="store_true")
        _ = parser.add_argument(
            "--skip-check",
            action="store_true",
            help="Skip post-write build-system validation",
        )
        _ = parser.add_argument("--skip-comments", action="store_true")
        args = parser.parse_args(argv)
        if bool(args.dry_run or args.audit or args.check):
            args.skip_check = True
        cli = u.Infra.resolve(args)
        return FlextInfraPyprojectModernizer(workspace_root=cli.workspace).run(
            args,
            cli,
        )


if __name__ == "__main__":
    raise SystemExit(FlextInfraPyprojectModernizer.main())


__all__ = ["FlextInfraPyprojectModernizer"]
