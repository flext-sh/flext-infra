"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

import tomlkit
from tomlkit.items import Table

from flext_infra import (
    ConsolidateGroupsPhase,
    EnsureCoverageConfigPhase,
    EnsureExtraPathsPhase,
    EnsureFormattingToolingPhase,
    EnsureMypyConfigPhase,
    EnsureNamespaceToolingPhase,
    EnsurePydanticMypyConfigPhase,
    EnsurePyreflyConfigPhase,
    EnsurePyrightConfigPhase,
    EnsurePytestConfigPhase,
    EnsureRuffConfigPhase,
    InjectCommentsPhase,
    ProjectClassifier,
    c,
    r,
    t,
    u,
)


class FlextInfraPyprojectModernizer:
    """Modernize all workspace pyproject.toml files."""

    ROOT = u.Infra.resolve_workspace_root(__file__)

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize pyproject modernizer."""
        self.root = workspace_root or self.ROOT
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.is_failure:
            msg = tool_config_result.error or "failed to load deps tool config"
            raise ValueError(msg)
        self._tool_config = tool_config_result.value

    @staticmethod
    def _table_child(parent: tomlkit.TOMLDocument | Table, key: str) -> Table | None:
        if key not in parent:
            return None
        child_value = parent[key]
        if isinstance(child_value, Table):
            return child_value
        return None

    def _classify_project(self, project_dir: Path) -> r[str]:
        """Classify project kind for pyright/coverage config selection."""
        kind = ProjectClassifier(project_dir).classify().project_kind
        return r[str].ok(kind)

    def find_pyproject_files(self) -> Sequence[Path]:
        """Find all workspace pyproject.toml files."""
        result = u.Infra.find_all_pyproject_files(
            self.root,
            skip_dirs=c.Infra.SKIP_DIRS,
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
        doc = u.Infra.read(path)
        if doc is None:
            return ["invalid TOML"]
        is_root = path.parent.resolve() == self.root.resolve()
        project_kind = "core"
        if not is_root:
            kind_result = self._classify_project(path.parent)
            if kind_result.is_success:
                project_kind = kind_result.value
        changes: MutableSequence[str] = []
        tool_item = self._table_child(doc, c.Infra.Toml.TOOL)
        if tool_item is None:
            tool_item = tomlkit.table()
            doc[c.Infra.Toml.TOOL] = tool_item
        poetry_item = self._table_child(tool_item, c.Infra.Toml.POETRY)
        if poetry_item is not None:
            group_item = self._table_child(poetry_item, c.Infra.Toml.GROUP)
            if group_item is not None:
                empty_groups: MutableSequence[str] = []
                for name in u.Infra.table_string_keys(group_item):
                    group_dep_item = self._table_child(group_item, name)
                    if group_dep_item is None:
                        continue
                    deps_item = self._table_child(
                        group_dep_item,
                        c.Infra.Toml.DEPENDENCIES,
                    )
                    if deps_item is not None and not deps_item:
                        empty_groups.append(name)
                for name in empty_groups:
                    del group_item[name]
                    changes.append(f"removed empty poetry group '{name}'")
                if not group_item:
                    del poetry_item[c.Infra.Toml.GROUP]
                    changes.append("removed empty poetry group container")
        changes.extend(ConsolidateGroupsPhase().apply(doc, canonical_dev))
        changes.extend(EnsurePytestConfigPhase(self._tool_config).apply(doc))
        changes.extend(
            EnsurePyreflyConfigPhase(self._tool_config).apply(
                doc,
                is_root=is_root,
                project_dir=path.parent,
            ),
        )
        changes.extend(EnsureMypyConfigPhase(self._tool_config).apply(doc))
        changes.extend(EnsurePydanticMypyConfigPhase(self._tool_config).apply(doc))
        changes.extend(EnsureFormattingToolingPhase(self._tool_config).apply(doc))
        changes.extend(EnsureNamespaceToolingPhase().apply(doc, path=path))
        changes.extend(
            EnsureRuffConfigPhase(self._tool_config).apply(
                doc,
                path=path,
            ),
        )
        changes.extend(
            EnsurePyrightConfigPhase(self._tool_config).apply(
                doc,
                is_root=is_root,
                workspace_root=self.root,
                project_dir=path.parent,
                project_kind=project_kind,
            ),
        )
        changes.extend(
            EnsureCoverageConfigPhase(self._tool_config).apply(
                doc,
                project_kind=project_kind,
            ),
        )
        changes.extend(
            EnsureExtraPathsPhase().apply(
                doc,
                path=path,
                is_root=is_root,
                dry_run=dry_run,
            ),
        )
        rendered = doc.as_string()
        if not skip_comments:
            rendered, comment_changes = InjectCommentsPhase().apply(rendered)
            changes.extend(comment_changes)
        if changes and (not dry_run):
            u.write_file(path, rendered, encoding=c.Infra.Encoding.DEFAULT)
        return changes

    def run(self, args: Namespace, cli: u.Infra.CliArgs) -> int:
        """Run pyproject modernization for the workspace."""
        check_mode = bool(args.audit or cli.check)
        dry_run = bool(cli.dry_run or check_mode)
        files = self.find_pyproject_files()
        root_doc = u.Infra.read(self.root / c.Infra.Files.PYPROJECT_FILENAME)
        if root_doc is None:
            return 2
        canonical_dev = u.Infra.canonical_dev_dependencies(root_doc)
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
        if not dry_run and (not args.skip_check):
            return self._run_poetry_check(files)
        return 0

    def _run_poetry_check(self, files: Sequence[Path]) -> int:
        has_warning = False
        for path in files:
            project_dir = path.parent
            result = u.Infra.run_raw(
                [c.Infra.Cli.POETRY, c.Infra.Cli.PoetryCmd.CHECK],
                cwd=project_dir,
            )
            if result.is_failure:
                has_warning = True
                continue
            if result.value.exit_code != 0:
                has_warning = True
        return 1 if has_warning else 0

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Run the pyproject modernizer CLI."""
        parser = u.Infra.create_parser(
            "flext-infra deps modernize",
            "Modernize workspace pyproject files",
            include_apply=True,
            include_check=True,
        )
        _ = parser.add_argument("--audit", action="store_true")
        _ = parser.add_argument("--skip-comments", action="store_true")
        _ = parser.add_argument("--skip-check", action="store_true")
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        return FlextInfraPyprojectModernizer(workspace_root=cli.workspace).run(
            args,
            cli,
        )


main = FlextInfraPyprojectModernizer.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraPyprojectModernizer.main())


__all__ = ["FlextInfraPyprojectModernizer", "u"]
