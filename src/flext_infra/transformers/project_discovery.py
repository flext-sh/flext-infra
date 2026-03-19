from __future__ import annotations

from pathlib import Path

import libcst as cst


class ProjectAliasDiscovery:
    @staticmethod
    def discover_package_aliases(package_init: Path) -> tuple[str, ...]:
        if not package_init.exists():
            return ()
        try:
            tree = cst.parse_module(package_init.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return ()
        aliases: set[str] = set()
        for item in tree.body:
            if not isinstance(item, cst.SimpleStatementLine):
                continue
            for stmt in item.body:
                if not isinstance(stmt, cst.Assign):
                    continue
                ProjectAliasDiscovery._collect_single_letter_targets(
                    stmt,
                    aliases,
                )
                ProjectAliasDiscovery._collect_all_exports(stmt, aliases)
        return tuple(sorted(aliases))

    @staticmethod
    def _collect_single_letter_targets(
        stmt: cst.Assign,
        aliases: set[str],
    ) -> None:
        for target in stmt.targets:
            if not isinstance(target.target, cst.Name):
                continue
            name = target.target.value
            if len(name) == 1 and name.isalpha() and name.islower():
                aliases.add(name)

    @staticmethod
    def _collect_all_exports(
        stmt: cst.Assign,
        aliases: set[str],
    ) -> None:
        for target in stmt.targets:
            if not isinstance(target.target, cst.Name):
                continue
            if target.target.value != "__all__":
                continue
            if not isinstance(stmt.value, (cst.List, cst.Tuple)):
                continue
            for el in stmt.value.elements:
                if not isinstance(el.value, cst.SimpleString):
                    continue
                val = el.value.evaluated_value
                if (
                    isinstance(val, str)
                    and len(val) == 1
                    and val.isalpha()
                    and val.islower()
                ):
                    aliases.add(val)

    @staticmethod
    def discover_workspace_aliases(
        workspace_root: Path,
    ) -> dict[str, tuple[str, ...]]:
        result: dict[str, tuple[str, ...]] = {}
        for src_dir in sorted(workspace_root.glob("*/src/")):
            project_dir = src_dir.parent
            pkg_name = project_dir.name.replace("-", "_")
            pkg_dir = src_dir / pkg_name
            init_file = pkg_dir / "__init__.py"
            if not init_file.exists():
                continue
            aliases = ProjectAliasDiscovery.discover_package_aliases(init_file)
            if aliases:
                result[pkg_name] = aliases
        return result

    @staticmethod
    def discover_facade_alias_map(package_dir: Path) -> dict[str, str]:
        facade_map: dict[str, str] = {}
        facade_files = [
            "constants.py",
            "typings.py",
            "models.py",
            "protocols.py",
            "utilities.py",
            "exceptions.py",
            "decorators.py",
            "handlers.py",
            "service.py",
            "services.py",
            "mixins.py",
            "result.py",
        ]
        for filename in facade_files:
            filepath = package_dir / filename
            if not filepath.exists():
                continue
            try:
                tree = cst.parse_module(filepath.read_text())
            except cst.ParserSyntaxError:
                continue
            for item in tree.body:
                if not isinstance(item, cst.SimpleStatementLine):
                    continue
                for stmt in item.body:
                    if not isinstance(stmt, cst.Assign):
                        continue
                    for target in stmt.targets:
                        if not isinstance(target.target, cst.Name):
                            continue
                        name = target.target.value
                        if len(name) == 1 and name.isalpha() and name.islower():
                            facade_map[name] = filename
        return facade_map


__all__ = ["ProjectAliasDiscovery"]
