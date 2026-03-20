"""Normalize project alias imports to canonical package-level imports."""

from __future__ import annotations

import importlib.util
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Annotated, override

import libcst as cst
from pydantic import ConfigDict, Field

from flext_infra import FlextInfraTransformerImportInsertion, c, t, u
from flext_infra.models import FlextModels

_UNKNOWN_TIER = 99


class ImportViolation(FlextModels.ArbitraryTypesModel):
    model_config = ConfigDict(frozen=True)

    file: Annotated[str, Field(min_length=1)]
    line: Annotated[int, Field(ge=1)]
    current_import: Annotated[str, Field(min_length=1)]
    suggested_import: Annotated[str, Field(min_length=1)]
    violation_type: Annotated[str, Field(pattern="^(deep|wrong_source)$")]


class _ImportNormalizationContext(FlextModels.ArbitraryTypesModel):
    file_path: Path
    file_module: str
    project_package: str
    project_aliases: frozenset[str]
    declared_alias: str
    alias_to_defining_module: Mapping[str, str]
    alias_tiers: Mapping[str, int]
    file_tier: int
    package_reachability: Mapping[str, frozenset[str]]
    wrong_source_enabled: bool
    universal_aliases: frozenset[str]
    workspace_packages: frozenset[str]


class FlextInfraTransformerImportNormalizerHelper:
    """Helper class for import normalization logic."""

    @staticmethod
    @lru_cache(maxsize=1)
    def load_import_normalization_config() -> Mapping[str, t.Infra.InfraValue]:
        rules_path = (
            Path(__file__).resolve().parent.parent
            / "rules"
            / "import-normalization.yml"
        )
        loaded = u.Infra.safe_load_yaml(rules_path)
        root = loaded.get("import_normalization")
        if isinstance(root, Mapping):
            normalized: dict[str, t.Infra.InfraValue] = dict(root.items())
            return normalized
        return {}

    @staticmethod
    @lru_cache(maxsize=1)
    def alias_tiers() -> Mapping[str, int]:
        config = FlextInfraTransformerImportNormalizerHelper.load_import_normalization_config().get(
            "alias_tiers",
        )
        if not isinstance(config, Mapping):
            return {}
        tiers: dict[str, int] = {}
        for alias_name, tier_value in config.items():
            if len(alias_name) != 1 or not alias_name.islower():
                continue
            if isinstance(tier_value, int):
                tiers[alias_name] = tier_value
        return tiers

    @staticmethod
    @lru_cache(maxsize=1)
    def facade_filenames() -> tuple[str, ...]:
        config = FlextInfraTransformerImportNormalizerHelper.load_import_normalization_config().get(
            "facade_filenames",
        )
        if not isinstance(config, list):
            return ()
        output: list[str] = [
            item for item in config if isinstance(item, str) and item.endswith(".py")
        ]
        return tuple(output)

    @staticmethod
    @lru_cache(maxsize=1)
    def wrong_source_config() -> tuple[bool, frozenset[str]]:
        config = FlextInfraTransformerImportNormalizerHelper.load_import_normalization_config().get(
            "wrong_source",
        )
        if not isinstance(config, Mapping):
            return False, frozenset()
        enabled_raw = config.get("enabled")
        enabled = isinstance(enabled_raw, bool) and enabled_raw
        universal_raw = config.get("universal_aliases")
        universal_aliases: set[str] = set()
        if isinstance(universal_raw, list):
            for item in universal_raw:
                if isinstance(item, str) and len(item) == 1 and item.islower():
                    universal_aliases.add(item)
        return enabled, frozenset(universal_aliases)

    @staticmethod
    def extract_declared_alias_from_facade(file_path: Path) -> str:
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return ""
        alias_name = ""
        for statement in module.body:
            if not isinstance(statement, cst.SimpleStatementLine):
                continue
            for expression in statement.body:
                if not isinstance(expression, cst.Assign):
                    continue
                if len(expression.targets) != 1:
                    continue
                target = expression.targets[0].target
                if not isinstance(target, cst.Name):
                    continue
                if len(target.value) != 1:
                    continue
                if not isinstance(expression.value, cst.Name):
                    continue
                alias_name = target.value
        return alias_name

    @staticmethod
    def discover_project_aliases(project_root: Path) -> dict[str, str]:
        src_package = u.Infra.discover_src_package_dir(project_root)
        if src_package is None:
            return {}
        _, package_dir = src_package
        alias_to_facade: dict[str, str] = {}
        for (
            facade_name
        ) in FlextInfraTransformerImportNormalizerHelper.facade_filenames():
            facade_path = package_dir / facade_name
            if not facade_path.is_file():
                continue
            alias_name = FlextInfraTransformerImportNormalizerHelper.extract_declared_alias_from_facade(
                facade_path,
            )
            if len(alias_name) != 1 or not alias_name.islower():
                continue
            alias_to_facade[alias_name] = facade_name
        return alias_to_facade

    @staticmethod
    def reverse_alias_map(alias_to_facade: Mapping[str, str]) -> dict[str, str]:
        return {
            file_name: alias_name for alias_name, file_name in alias_to_facade.items()
        }

    @staticmethod
    def find_lazy_imports_dict(module: cst.Module) -> cst.Dict | None:
        for statement in module.body:
            if not isinstance(statement, cst.SimpleStatementLine):
                continue
            for expression in statement.body:
                if isinstance(expression, cst.Assign):
                    if len(expression.targets) != 1:
                        continue
                    target = expression.targets[0].target
                    if (
                        isinstance(target, cst.Name)
                        and target.value == "_LAZY_IMPORTS"
                        and isinstance(expression.value, cst.Dict)
                    ):
                        return expression.value
                if isinstance(expression, cst.AnnAssign):
                    target = expression.target
                    if not isinstance(target, cst.Name):
                        continue
                    if target.value != "_LAZY_IMPORTS":
                        continue
                    if expression.value is None or not isinstance(
                        expression.value, cst.Dict
                    ):
                        continue
                    return expression.value
        return None

    @staticmethod
    def extract_string_literal(node: cst.BaseExpression) -> str:
        if not isinstance(node, cst.SimpleString):
            return ""
        value = node.evaluated_value
        return value if isinstance(value, str) else ""

    @staticmethod
    def extract_lazy_import_map(init_path: Path) -> dict[str, str]:
        if not init_path.is_file():
            return {}
        try:
            source = init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            module = cst.parse_module(source)
        except (OSError, cst.ParserSyntaxError):
            return {}
        lazy_imports = (
            FlextInfraTransformerImportNormalizerHelper.find_lazy_imports_dict(
                module,
            )
        )
        if lazy_imports is None:
            return {}
        lazy_import_map: dict[str, str] = {}
        for element in lazy_imports.elements:
            if not isinstance(element, cst.DictElement):
                continue
            key_text = (
                FlextInfraTransformerImportNormalizerHelper.extract_string_literal(
                    element.key,
                )
            )
            if len(key_text) == 0:
                continue
            if not isinstance(element.value, (cst.Tuple, cst.List)):
                continue
            if len(element.value.elements) == 0:
                continue
            module_spec = element.value.elements[0].value
            module_name = (
                FlextInfraTransformerImportNormalizerHelper.extract_string_literal(
                    module_spec,
                )
            )
            if len(module_name) == 0:
                continue
            lazy_import_map[key_text] = module_name
        return lazy_import_map

    @staticmethod
    @lru_cache(maxsize=128)
    def build_lazy_import_maps(
        package_dir: Path,
        package_name: str,
    ) -> dict[str, dict[str, str]]:
        lazy_import_maps: dict[str, dict[str, str]] = {}
        for init_path in sorted(package_dir.rglob("__init__.py")):
            module_name = FlextInfraTransformerImportNormalizerHelper.file_to_module(
                init_path,
                package_dir,
                package_name,
            )
            if len(module_name) == 0:
                module_name = package_name
            module_map = (
                FlextInfraTransformerImportNormalizerHelper.extract_lazy_import_map(
                    init_path,
                )
            )
            if len(module_map) == 0:
                continue
            lazy_import_maps[module_name] = module_map
        return lazy_import_maps

    @staticmethod
    def build_alias_to_defining_module(
        *,
        package_name: str,
        package_dir: Path,
        project_root: Path | None,
        alias_map: dict[str, tuple[str, ...]] | None,
    ) -> dict[str, str]:
        init_path = package_dir / "__init__.py"
        alias_to_module = dict(
            FlextInfraTransformerImportNormalizerHelper.extract_lazy_import_map(
                init_path,
            ),
        )
        if project_root is not None:
            alias_to_facade = (
                FlextInfraTransformerImportNormalizerHelper.discover_project_aliases(
                    project_root,
                )
            )
            for alias_name, facade_file in alias_to_facade.items():
                if alias_name in alias_to_module:
                    continue
                facade_module = f"{package_name}.{Path(facade_file).stem}"
                alias_to_module[alias_name] = facade_module
        if alias_map is not None:
            legacy_aliases = alias_map.get(package_name, ())
            for alias_name in legacy_aliases:
                if alias_name in alias_to_module:
                    continue
                guessed_module = f"{package_name}.{alias_name}"
                alias_to_module[alias_name] = guessed_module
        return alias_to_module

    @staticmethod
    def resolve_relative_module(
        *, current_module: str, level: int, module_name: str
    ) -> str:
        if len(current_module) == 0:
            return ""
        parts = current_module.split(".")
        package_parts = parts[:-1]
        hops = max(level - 1, 0)
        if hops > len(package_parts):
            return ""
        base_parts = package_parts[: len(package_parts) - hops]
        if len(module_name) > 0:
            base_parts.extend(module_name.split("."))
        return ".".join(base_parts)

    @staticmethod
    def file_to_module(file_path: Path, package_dir: Path, package_name: str) -> str:
        del package_name
        try:
            relative = file_path.relative_to(package_dir.parent)
        except ValueError:
            return ""
        parts = list(relative.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    @staticmethod
    @lru_cache(maxsize=128)
    def build_import_graph(
        package_dir: Path,
        package_name: str,
    ) -> dict[str, frozenset[str]]:
        python_files = sorted(
            path for path in package_dir.rglob("*.py") if path.name != "__init__.py"
        )
        module_names = {
            FlextInfraTransformerImportNormalizerHelper.file_to_module(
                path,
                package_dir,
                package_name,
            )
            for path in python_files
            if len(
                FlextInfraTransformerImportNormalizerHelper.file_to_module(
                    path,
                    package_dir,
                    package_name,
                ),
            )
            > 0
        }
        known_modules = frozenset(module_names)
        graph: dict[str, frozenset[str]] = {
            module_name: frozenset() for module_name in known_modules
        }
        lazy_import_maps = (
            FlextInfraTransformerImportNormalizerHelper.build_lazy_import_maps(
                package_dir,
                package_name,
            )
        )
        for file_path in python_files:
            current_module = FlextInfraTransformerImportNormalizerHelper.file_to_module(
                file_path,
                package_dir,
                package_name,
            )
            if current_module not in known_modules:
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                tree = cst.parse_module(source)
            except (OSError, cst.ParserSyntaxError):
                continue
            collector = _ImportEdgeCollector(
                current_module=current_module,
                package_name=package_name,
                known_modules=known_modules,
                lazy_import_maps=lazy_import_maps,
            )
            tree.visit(collector)
            edges = {
                imported_module
                for imported_module in collector.imported_modules
                if imported_module in known_modules
            }
            graph[current_module] = frozenset(edges)
        return graph

    @staticmethod
    @lru_cache(maxsize=128)
    def build_reachability(
        package_dir: Path,
        package_name: str,
    ) -> dict[str, frozenset[str]]:
        graph = FlextInfraTransformerImportNormalizerHelper.build_import_graph(
            package_dir,
            package_name,
        )
        reachability: dict[str, frozenset[str]] = {}
        for module_name in graph:
            visited: set[str] = set()
            queue: deque[str] = deque(graph.get(module_name, frozenset()))
            while len(queue) > 0:
                imported_module = queue.popleft()
                if imported_module in visited:
                    continue
                visited.add(imported_module)
                queue.extend(graph.get(imported_module, frozenset()))
            reachability[module_name] = frozenset(visited)
        return reachability

    @staticmethod
    def build_context(
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None,
    ) -> _ImportNormalizationContext:
        package_name = (
            project_package
            if len(project_package) > 0
            else u.Infra.discover_package_from_file(file_path)
        )
        project_root = u.Infra.discover_project_root_from_file(file_path)
        package_dir: Path | None = None
        if project_root is not None:
            candidate = project_root / "src" / package_name
            if candidate.is_dir() and (candidate / "__init__.py").is_file():
                package_dir = candidate
        if package_dir is None and len(package_name) > 0:
            spec = importlib.util.find_spec(package_name)
            if spec and spec.submodule_search_locations:
                locs = list(spec.submodule_search_locations)
                if locs:
                    cand = Path(locs[0])
                    if cand.is_dir() and (cand / "__init__.py").is_file():
                        package_dir = cand

        alias_to_module = (
            FlextInfraTransformerImportNormalizerHelper.build_alias_to_defining_module(
                package_name=package_name,
                package_dir=package_dir,
                project_root=project_root,
                alias_map=alias_map,
            )
            if package_dir is not None and len(package_name) > 0
            else {}
        )
        file_module = ""
        if package_dir is not None and len(package_name) > 0:
            try:
                file_module = (
                    FlextInfraTransformerImportNormalizerHelper.file_to_module(
                        file_path, package_dir, package_name
                    )
                )
            except ValueError:
                file_module = ""
        alias_to_facade = (
            FlextInfraTransformerImportNormalizerHelper.discover_project_aliases(
                project_root,
            )
            if project_root is not None
            else {}
        )
        facade_to_alias = FlextInfraTransformerImportNormalizerHelper.reverse_alias_map(
            alias_to_facade,
        )
        declared_alias = facade_to_alias.get(file_path.name, "")
        alias_tiers = FlextInfraTransformerImportNormalizerHelper.alias_tiers()
        file_tier = FlextInfraTransformerImportNormalizerHelper.file_tier(
            file_path=file_path,
            project_package=package_name,
            facade_to_alias=facade_to_alias,
            alias_tiers=alias_tiers,
        )
        reachability = (
            FlextInfraTransformerImportNormalizerHelper.build_reachability(
                package_dir,
                package_name,
            )
            if package_dir is not None and len(package_name) > 0
            else {}
        )
        workspace_root = u.Infra.discover_workspace_root_from_file(file_path)
        workspace_packages = u.Infra.discover_workspace_packages(workspace_root)
        wrong_source_enabled, universal_aliases = (
            FlextInfraTransformerImportNormalizerHelper.wrong_source_config()
        )
        project_aliases = set(alias_to_module)
        if alias_map is not None and len(package_name) > 0:
            project_aliases.update(alias_map.get(package_name, ()))
        return _ImportNormalizationContext(
            file_path=file_path,
            file_module=file_module,
            project_package=package_name,
            project_aliases=frozenset(project_aliases),
            declared_alias=declared_alias,
            alias_to_defining_module=alias_to_module,
            alias_tiers=alias_tiers,
            file_tier=file_tier,
            package_reachability=reachability,
            wrong_source_enabled=wrong_source_enabled,
            universal_aliases=universal_aliases,
            workspace_packages=workspace_packages,
        )

    @staticmethod
    def file_tier(
        *,
        file_path: Path,
        project_package: str,
        facade_to_alias: Mapping[str, str],
        alias_tiers: Mapping[str, int],
    ) -> int:
        declared_alias = facade_to_alias.get(file_path.name, "")
        if declared_alias in alias_tiers:
            return alias_tiers[declared_alias]
        if len(project_package) == 0:
            return _UNKNOWN_TIER
        marker = f"/src/{project_package}/"
        file_str = str(file_path.resolve())
        if marker not in file_str:
            return _UNKNOWN_TIER
        relative = file_str.split(marker, maxsplit=1)[1]
        parts = Path(relative).parts[:-1]
        if len(parts) == 0:
            return _UNKNOWN_TIER
        first = parts[0]
        if first.startswith("_"):
            normalized = first.lstrip("_")
            if normalized == "services":
                normalized = "service"
            alias = facade_to_alias.get(f"{normalized}.py", "")
            if alias in alias_tiers:
                return alias_tiers[alias]
            if normalized == "result" and "r" in alias_tiers:
                return alias_tiers["r"]
            return 4
        return 4

    @staticmethod
    def is_private_submodule(module_name: str) -> bool:
        return "._" in module_name

    @staticmethod
    def imported_name(imported_alias: cst.ImportAlias) -> str | None:
        if imported_alias.asname is not None:
            return None
        if not isinstance(imported_alias.name, cst.Name):
            return None
        return imported_alias.name.value

    @staticmethod
    def is_safe_to_normalize(context: _ImportNormalizationContext, alias: str) -> bool:
        defining_module = context.alias_to_defining_module.get(alias, "")
        if len(defining_module) > 0 and len(context.file_module) > 0:
            if defining_module == context.file_module:
                return False
            reachable = context.package_reachability.get(defining_module)
            if reachable is not None:
                return context.file_module not in reachable
        alias_tier = context.alias_tiers.get(alias, _UNKNOWN_TIER)
        if context.file_tier < _UNKNOWN_TIER:
            return alias_tier < context.file_tier
        return True

    @staticmethod
    def is_deep_violation(
        *,
        context: _ImportNormalizationContext,
        module_name: str,
        imported_name: str,
    ) -> bool:
        if module_name == context.project_package:
            return False
        if not module_name.startswith(f"{context.project_package}."):
            return False
        if (
            FlextInfraTransformerImportNormalizerHelper.is_private_submodule(
                module_name,
            )
            and imported_name not in context.project_aliases
        ):
            return False
        if not FlextInfraTransformerImportNormalizerHelper.is_safe_to_normalize(
            context,
            imported_name,
        ):
            return False
        return imported_name in context.project_aliases

    @staticmethod
    def is_wrong_source_violation(
        *,
        context: _ImportNormalizationContext,
        module_name: str,
        imported_name: str,
    ) -> bool:
        if not context.wrong_source_enabled:
            return False
        if module_name == context.project_package:
            return False
        if "." in module_name:
            return False
        if imported_name in context.universal_aliases:
            return False
        if imported_name not in context.project_aliases:
            return False
        if not FlextInfraTransformerImportNormalizerHelper.is_safe_to_normalize(
            context,
            imported_name,
        ):
            return False
        return module_name in context.workspace_packages

    @staticmethod
    def violation_type(
        *,
        context: _ImportNormalizationContext,
        module_name: str,
        imported_name: str,
    ) -> str | None:
        if imported_name not in context.project_aliases:
            return None
        if FlextInfraTransformerImportNormalizerHelper.is_deep_violation(
            context=context,
            module_name=module_name,
            imported_name=imported_name,
        ):
            return "deep"
        if FlextInfraTransformerImportNormalizerHelper.is_wrong_source_violation(
            context=context,
            module_name=module_name,
            imported_name=imported_name,
        ):
            return "wrong_source"
        return None

    @staticmethod
    def module_name(node: cst.ImportFrom) -> str:
        if node.module is None or len(node.relative) > 0:
            return ""
        return u.Infra.module_name_from_expr(node.module)


class _ImportEdgeCollector(cst.CSTVisitor):
    def __init__(
        self,
        *,
        current_module: str,
        package_name: str,
        known_modules: frozenset[str],
        lazy_import_maps: Mapping[str, Mapping[str, str]],
    ) -> None:
        """Initialize collector state used to build internal import edges."""
        self._current_module = current_module
        self._package_name = package_name
        self._known_modules = known_modules
        self._lazy_import_maps = lazy_import_maps
        self.imported_modules: set[str] = set()

    @override
    def visit_Import(self, node: cst.Import) -> None:
        for imported_alias in node.names:
            module_name = u.Infra.module_name_from_expr(imported_alias.name)
            if len(module_name) == 0:
                continue
            self._add_candidate(module_name)

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        base_module = self._resolve_import_from_module(node)
        if len(base_module) > 0:
            self._add_candidate(base_module)
        if isinstance(node.names, cst.ImportStar):
            return
        for imported_alias in node.names:
            imported_name = FlextInfraTransformerImportNormalizerHelper.imported_name(
                imported_alias,
            )
            if imported_name is None:
                continue
            if len(base_module) == 0:
                continue
            lazy_module = self._lazy_import_maps.get(base_module, {}).get(
                imported_name,
                "",
            )
            if len(lazy_module) > 0:
                self._add_candidate(lazy_module)
            self._add_candidate(f"{base_module}.{imported_name}")

    def _resolve_import_from_module(self, node: cst.ImportFrom) -> str:
        module_name = u.Infra.module_name_from_expr(node.module)
        if len(node.relative) == 0:
            return module_name
        return FlextInfraTransformerImportNormalizerHelper.resolve_relative_module(
            current_module=self._current_module,
            level=len(node.relative),
            module_name=module_name,
        )

    def _add_candidate(self, module_name: str) -> None:
        if module_name == self._package_name:
            self.imported_modules.add(module_name)
            return
        if not module_name.startswith(f"{self._package_name}."):
            return
        if module_name in self._known_modules:
            self.imported_modules.add(module_name)


class ImportNormalizerVisitor(cst.CSTVisitor):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        """Build visitor context for detecting non-canonical alias imports."""
        self._context = FlextInfraTransformerImportNormalizerHelper.build_context(
            file_path=file_path,
            project_package=project_package,
            alias_map=alias_map,
        )
        self.violations: list[ImportViolation] = []

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module_name = FlextInfraTransformerImportNormalizerHelper.module_name(node)
        if len(module_name) == 0:
            return
        if isinstance(node.names, cst.ImportStar):
            return
        for imported_alias in node.names:
            if imported_alias.asname is not None:
                continue
            if not isinstance(imported_alias.name, cst.Name):
                continue
            imported_name = imported_alias.name.value
            if imported_name == self._context.declared_alias:
                continue
            violation_type = FlextInfraTransformerImportNormalizerHelper.violation_type(
                context=self._context,
                module_name=module_name,
                imported_name=imported_name,
            )
            if violation_type is None:
                continue
            self.violations.append(
                ImportViolation(
                    file=str(self._context.file_path),
                    line=1,
                    current_import=f"from {module_name} import {imported_name}",
                    suggested_import=(
                        f"from {self._context.project_package} import {imported_name}"
                    ),
                    violation_type=violation_type,
                ),
            )


class ImportNormalizerTransformer(cst.CSTTransformer):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        """Prepare import normalization and change tracking for one file."""
        self._context = FlextInfraTransformerImportNormalizerHelper.build_context(
            file_path=file_path,
            project_package=project_package,
            alias_map=alias_map,
        )
        self._on_change = on_change
        self.modified_imports = False
        self.aliases_to_inject: set[str] = set()
        self.aliases_present: set[str] = set()
        self.changes: list[str] = []

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        module_name = FlextInfraTransformerImportNormalizerHelper.module_name(
            original_node,
        )
        if len(module_name) == 0:
            return updated_node
        if isinstance(updated_node.names, cst.ImportStar):
            return updated_node
        if module_name == self._context.project_package:
            self._track_present_aliases(updated_node.names)

        violating_names: set[str] = set()
        for imported_alias in updated_node.names:
            imported_name = FlextInfraTransformerImportNormalizerHelper.imported_name(
                imported_alias,
            )
            if imported_name is None or imported_name == self._context.declared_alias:
                continue
            violation_type = FlextInfraTransformerImportNormalizerHelper.violation_type(
                context=self._context,
                module_name=module_name,
                imported_name=imported_name,
            )
            if violation_type is None:
                continue
            violating_names.add(imported_name)
            self.aliases_to_inject.add(imported_name)
            self.modified_imports = True
            self._record_change(
                f"Removed {violation_type} alias import: from {module_name} import {imported_name}",
            )

        if len(violating_names) == 0:
            return updated_node

        kept_aliases = [
            imported_alias
            for imported_alias in updated_node.names
            if FlextInfraTransformerImportNormalizerHelper.imported_name(
                imported_alias,
            )
            not in violating_names
        ]
        if len(kept_aliases) == 0:
            return cst.RemovalSentinel.REMOVE
        kept_aliases[-1] = kept_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
        return updated_node.with_changes(names=tuple(kept_aliases))

    @override
    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        del original_node
        missing = sorted(self.aliases_to_inject - self.aliases_present)
        if len(missing) == 0:
            return updated_node

        body = list(updated_node.body)
        merge_index = self._find_project_import_index(body)
        if merge_index is not None:
            merged_body = self._merge_into_existing_import(
                body=body,
                index=merge_index,
                missing=missing,
            )
            if merged_body is not None:
                return updated_node.with_changes(body=merged_body)

        new_import = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=self._project_module_expr(self._context.project_package),
                    names=tuple(
                        cst.ImportAlias(name=cst.Name(alias_name))
                        for alias_name in missing
                    ),
                ),
            ],
        )
        insert_idx = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
            body,
        )
        self._record_change(
            "Added normalized alias import: "
            f"from {self._context.project_package} import {', '.join(missing)}",
        )
        return updated_node.with_changes(
            body=body[:insert_idx] + [new_import] + body[insert_idx:]
        )

    @staticmethod
    def detect_file(
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[ImportViolation]:
        """Return deep/wrong-source alias violations for a single file."""
        effective_package = (
            project_package
            if len(project_package) > 0
            else u.Infra.discover_package_from_file(file_path)
        )
        if file_path.name == "__init__.py" or len(effective_package) == 0:
            return []
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return []
        visitor = ImportNormalizerVisitor(
            file_path=file_path,
            project_package=effective_package,
            alias_map=alias_map,
        )
        module.visit(visitor)
        return visitor.violations

    @staticmethod
    def normalize_file(
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[str]:
        """Rewrite violating imports and return applied normalization messages."""
        effective_package = (
            project_package
            if len(project_package) > 0
            else u.Infra.discover_package_from_file(file_path)
        )
        if file_path.name == "__init__.py" or len(effective_package) == 0:
            return []
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return []
        transformer = ImportNormalizerTransformer(
            file_path=file_path,
            project_package=effective_package,
            alias_map=alias_map,
        )
        updated_module = module.visit(transformer)
        if updated_module.code != module.code:
            file_path.write_text(updated_module.code, encoding=c.Infra.Encoding.DEFAULT)
            u.Infra.run_ruff_fix(file_path, include_format=True, quiet=True)
        return transformer.changes

    def _track_present_aliases(self, aliases: Sequence[cst.ImportAlias]) -> None:
        for imported_alias in aliases:
            imported_name = FlextInfraTransformerImportNormalizerHelper.imported_name(
                imported_alias,
            )
            if imported_name is None:
                continue
            if imported_name == self._context.declared_alias:
                continue
            if imported_name not in self._context.project_aliases:
                continue
            self.aliases_present.add(imported_name)

    def _find_project_import_index(
        self,
        body: Sequence[cst.BaseStatement],
    ) -> int | None:
        for index, statement in enumerate(body):
            if not isinstance(statement, cst.SimpleStatementLine):
                continue
            if len(statement.body) != 1:
                continue
            only_stmt = statement.body[0]
            if not isinstance(only_stmt, cst.ImportFrom):
                continue
            module_name = FlextInfraTransformerImportNormalizerHelper.module_name(
                only_stmt,
            )
            if module_name != self._context.project_package:
                continue
            if isinstance(only_stmt.names, cst.ImportStar):
                continue
            return index
        return None

    def _merge_into_existing_import(
        self,
        *,
        body: Sequence[cst.BaseStatement],
        index: int,
        missing: list[str],
    ) -> list[cst.BaseStatement] | None:
        mutable_body = list(body)
        statement = mutable_body[index]
        if not isinstance(statement, cst.SimpleStatementLine):
            return None
        if len(statement.body) != 1:
            return None
        only_stmt = statement.body[0]
        if not isinstance(only_stmt, cst.ImportFrom):
            return None
        if isinstance(only_stmt.names, cst.ImportStar):
            return None

        existing = list(only_stmt.names)
        existing_names = {
            imported_name
            for imported_alias in existing
            if (
                imported_name
                := FlextInfraTransformerImportNormalizerHelper.imported_name(
                    imported_alias,
                )
            )
            is not None
        }
        new_aliases = [
            cst.ImportAlias(name=cst.Name(alias_name))
            for alias_name in missing
            if alias_name not in existing_names
        ]
        if len(new_aliases) == 0:
            return None

        mutable_body[index] = statement.with_changes(
            body=[only_stmt.with_changes(names=tuple(existing + new_aliases))],
        )
        self._record_change(
            "Merged normalized aliases into existing import: "
            f"from {self._context.project_package} import {', '.join(missing)}",
        )
        return mutable_body

    @staticmethod
    def _project_module_expr(project_package: str) -> cst.Name | cst.Attribute:
        parts = [part for part in project_package.split(".") if len(part) > 0]
        if len(parts) == 0:
            return cst.Name(project_package)
        expr: cst.Name | cst.Attribute = cst.Name(parts[0])
        for part in parts[1:]:
            expr = cst.Attribute(value=expr, attr=cst.Name(part))
        return expr

    def _record_change(self, message: str) -> None:
        self.changes.append(message)
        if self._on_change is not None:
            self._on_change(message)


__all__ = [
    "ImportNormalizerTransformer",
    "ImportNormalizerVisitor",
    "ImportViolation",
]
