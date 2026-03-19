from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated, override

import libcst as cst
from pydantic import ConfigDict, Field

from flext_infra import c, u
from flext_infra.models import FlextModels
from flext_infra.transformers.import_insertion import (
    FlextInfraTransformerImportInsertion,
)


class ImportViolation(FlextModels.ArbitraryTypesModel):
    model_config = ConfigDict(frozen=True)

    file: Annotated[str, Field(min_length=1)]
    line: Annotated[int, Field(ge=1)]
    current_import: Annotated[str, Field(min_length=1)]
    suggested_import: Annotated[str, Field(min_length=1)]
    violation_type: Annotated[str, Field(pattern="^(deep|wrong_source)$")]


FACADE_TIER: dict[str, int] = {
    "c": 0,
    "t": 1,
    "p": 2,
    "m": 3,
    "u": 4,
    "e": 4,
    "r": 4,
    "s": 5,
    "d": 5,
    "h": 5,
    "x": 5,
}

FACADE_FILENAMES: tuple[str, ...] = (
    "constants.py",
    "typings.py",
    "protocols.py",
    "models.py",
    "utilities.py",
    "service.py",
    "exceptions.py",
    "decorators.py",
    "handlers.py",
    "mixins.py",
    "result.py",
)


def _discover_src_package_dir(project_root: Path) -> tuple[str, Path] | None:
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return None
    for child in sorted(src_dir.iterdir()):
        if child.is_dir() and (child / "__init__.py").is_file():
            return child.name, child
    return None


def _discover_project_root_from_file(file_path: Path) -> Path | None:
    resolved = file_path.resolve()
    candidate = resolved.parent if resolved.is_file() else resolved
    lineage = (candidate, *candidate.parents)
    for current in lineage:
        if current.name == "src":
            return current.parent
        src_dir = current / "src"
        if src_dir.is_dir():
            return current
    return None


def discover_package_from_file(file_path: Path) -> str:
    resolved = file_path.resolve()
    candidate = resolved.parent if resolved.is_file() else resolved
    lineage = (candidate, *candidate.parents)
    for current in lineage:
        if current.name != "src":
            continue
        try:
            rel = resolved.relative_to(current)
        except ValueError:
            continue
        if len(rel.parts) == 0:
            continue
        package_name = rel.parts[0]
        package_dir = current / package_name
        if (package_dir / "__init__.py").is_file():
            return package_name
    project_root = _discover_project_root_from_file(file_path)
    if project_root is None:
        return ""
    discovered = _discover_src_package_dir(project_root)
    if discovered is None:
        return ""
    package_name, _ = discovered
    return package_name


def _extract_declared_alias_from_facade(file_path: Path) -> str:
    module = u.Infra.parse_module_cst(file_path)
    if module is None:
        return ""
    alias_name = ""
    for statement in module.body:
        if not isinstance(statement, cst.SimpleStatementLine):
            continue
        for expr in statement.body:
            if not isinstance(expr, cst.Assign):
                continue
            if len(expr.targets) != 1:
                continue
            target = expr.targets[0].target
            if not isinstance(target, cst.Name):
                continue
            if len(target.value) != 1:
                continue
            if not isinstance(expr.value, cst.Name):
                continue
            alias_name = target.value
    return alias_name


def discover_project_aliases(project_root: Path) -> dict[str, str]:
    discovered = _discover_src_package_dir(project_root)
    if discovered is None:
        return {}
    _, package_dir = discovered
    alias_to_facade: dict[str, str] = {}
    for facade_name in FACADE_FILENAMES:
        facade_path = package_dir / facade_name
        if not facade_path.is_file():
            continue
        alias_name = _extract_declared_alias_from_facade(facade_path)
        if len(alias_name) != 1:
            continue
        alias_to_facade[alias_name] = facade_name
    return alias_to_facade


def _reverse_alias_map(alias_to_facade: dict[str, str]) -> dict[str, str]:
    return {file_name: alias_name for alias_name, file_name in alias_to_facade.items()}


def _is_file_in_private_subdirectory(file_path: Path, project_package: str) -> bool:
    pkg_dir = project_package.replace(".", "/")
    file_str = str(file_path)
    idx = file_str.find(f"{pkg_dir}/")
    if idx < 0:
        return False
    relative = file_str[idx + len(pkg_dir) + 1 :]
    return any(part.startswith("_") for part in Path(relative).parts[:-1])


class ImportNormalizerVisitor(cst.CSTVisitor):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._file_path = file_path
        self._project_package = (
            project_package
            if len(project_package) > 0
            else discover_package_from_file(file_path)
        )
        project_root = _discover_project_root_from_file(file_path)
        alias_to_facade = (
            discover_project_aliases(project_root) if project_root is not None else {}
        )
        facade_to_alias = _reverse_alias_map(alias_to_facade)
        if alias_map is not None and len(self._project_package) > 0:
            self._project_aliases = set(alias_map.get(self._project_package, ()))
        else:
            self._project_aliases = set(alias_to_facade)
        self._facade_to_alias = facade_to_alias
        self._declared_alias = facade_to_alias.get(file_path.name, "")
        self._file_tier = self._get_file_tier()
        self._is_internal_module = _is_file_in_private_subdirectory(
            file_path, self._project_package
        )
        self.violations: list[ImportViolation] = []

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module_name = self._module_name(node)
        if len(module_name) == 0 or self._is_private_submodule(module_name):
            return
        if isinstance(node.names, cst.ImportStar):
            return
        for imported_alias in node.names:
            if imported_alias.asname is not None:
                continue
            if not isinstance(imported_alias.name, cst.Name):
                continue
            imported_name = imported_alias.name.value
            if imported_name == self._declared_alias:
                continue
            violation_type = self._violation_type(
                module_name=module_name,
                imported_name=imported_name,
            )
            if violation_type is None:
                continue
            line = 1
            self.violations.append(
                ImportViolation(
                    file=str(self._file_path),
                    line=line,
                    current_import=f"from {module_name} import {imported_name}",
                    suggested_import=(
                        f"from {self._project_package} import {imported_name}"
                    ),
                    violation_type=violation_type,
                ),
            )

    def _module_name(self, node: cst.ImportFrom) -> str:
        if node.module is None or len(node.relative) > 0:
            return ""
        return u.Infra.module_name_from_expr(node.module)

    @staticmethod
    def _is_private_submodule(module_name: str) -> bool:
        return "._" in module_name

    def _violation_type(self, *, module_name: str, imported_name: str) -> str | None:
        if imported_name not in self._project_aliases:
            return None
        if self._is_deep_violation(
            module_name=module_name, imported_name=imported_name
        ):
            return "deep"
        if self._is_wrong_source_violation(
            module_name=module_name,
            imported_name=imported_name,
        ):
            return "wrong_source"
        return None

    def _is_deep_violation(self, *, module_name: str, imported_name: str) -> bool:
        if module_name == self._project_package:
            if imported_name not in self._project_aliases:
                return False
            return not self._is_safe_to_normalize(imported_name)
        if not module_name.startswith(f"{self._project_package}."):
            return False
        if self._is_private_submodule(module_name):
            return False
        if not self._is_safe_to_normalize(imported_name):
            return False
        return imported_name in self._project_aliases

    def _is_wrong_source_violation(
        self, *, module_name: str, imported_name: str
    ) -> bool:
        if module_name == self._project_package:
            return False
        if "." in module_name:
            return False
        if imported_name not in self._project_aliases:
            return False
        if not self._is_safe_to_normalize(imported_name):
            return False
        return (
            module_name.startswith("flext_") or module_name == "gruponos_meltano_native"
        )

    def _get_file_tier(self) -> int:
        declared_alias = self._facade_to_alias.get(self._file_path.name, "")
        if declared_alias in FACADE_TIER:
            return FACADE_TIER[declared_alias]
        package_name = self._project_package
        if len(package_name) == 0:
            return 99
        marker = f"/src/{package_name}/"
        file_str = str(self._file_path.resolve())
        if marker not in file_str:
            return 99
        relative = file_str.split(marker, maxsplit=1)[1]
        parts = Path(relative).parts[:-1]
        if len(parts) == 0:
            return 99
        first = parts[0]
        if first.startswith("_"):
            normalized = first.lstrip("_")
            if normalized == "services":
                normalized = "service"
            alias = self._facade_to_alias.get(f"{normalized}.py", "")
            if alias in FACADE_TIER:
                return FACADE_TIER[alias]
            if normalized == "result":
                return FACADE_TIER["r"]
            return 4
        return 4

    def _is_safe_to_normalize(self, alias: str) -> bool:
        file_tier = self._file_tier
        alias_tier = FACADE_TIER.get(alias, 99)
        if file_tier < 99:
            return alias_tier < file_tier
        return True


class ImportNormalizerTransformer(cst.CSTTransformer):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._file_path = file_path
        self._project_package = (
            project_package
            if len(project_package) > 0
            else discover_package_from_file(file_path)
        )
        project_root = _discover_project_root_from_file(file_path)
        alias_to_facade = (
            discover_project_aliases(project_root) if project_root is not None else {}
        )
        facade_to_alias = _reverse_alias_map(alias_to_facade)
        if alias_map is not None and len(self._project_package) > 0:
            self._project_aliases = set(alias_map.get(self._project_package, ()))
        else:
            self._project_aliases = set(alias_to_facade)
        self._facade_to_alias = facade_to_alias
        self._declared_alias = facade_to_alias.get(file_path.name, "")
        self._file_tier = self._get_file_tier()
        self._is_internal_module = _is_file_in_private_subdirectory(
            file_path, self._project_package
        )
        self._on_change: Callable[[str], None] | None = on_change
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
        module_name = self._module_name(original_node)
        if len(module_name) == 0:
            return updated_node
        if isinstance(updated_node.names, cst.ImportStar):
            return updated_node
        if module_name == self._project_package:
            self._track_present_aliases(updated_node.names)
        if self._is_private_submodule(module_name):
            return updated_node

        violating_names: set[str] = set()
        for imported_alias in updated_node.names:
            imported_name = self._imported_name(imported_alias)
            if imported_name is None or imported_name == self._declared_alias:
                continue
            violation_type = self._violation_type(
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
            if self._imported_name(imported_alias) not in violating_names
        ]
        if len(kept_aliases) == 0:
            return cst.RemovalSentinel.REMOVE
        kept_aliases[-1] = kept_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT,
        )
        return updated_node.with_changes(names=tuple(kept_aliases))

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
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
                    module=self._project_module_expr(self._project_package),
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
            f"Added normalized alias import: from {self._project_package} import {', '.join(missing)}",
        )
        new_body = body[:insert_idx] + [new_import] + body[insert_idx:]
        return updated_node.with_changes(body=new_body)

    @staticmethod
    def detect_file(
        *,
        file_path: Path,
        project_package: str = "",
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[ImportViolation]:
        effective_package = (
            project_package
            if len(project_package) > 0
            else discover_package_from_file(file_path)
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
        effective_package = (
            project_package
            if len(project_package) > 0
            else discover_package_from_file(file_path)
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

    def _module_name(self, node: cst.ImportFrom) -> str:
        if node.module is None or len(node.relative) > 0:
            return ""
        return u.Infra.module_name_from_expr(node.module)

    @staticmethod
    def _is_private_submodule(module_name: str) -> bool:
        return "._" in module_name

    @staticmethod
    def _imported_name(imported_alias: cst.ImportAlias) -> str | None:
        if imported_alias.asname is not None:
            return None
        if not isinstance(imported_alias.name, cst.Name):
            return None
        return imported_alias.name.value

    def _violation_type(self, *, module_name: str, imported_name: str) -> str | None:
        if imported_name not in self._project_aliases:
            return None
        if self._is_deep_violation(
            module_name=module_name, imported_name=imported_name
        ):
            return "deep"
        if self._is_wrong_source_violation(
            module_name=module_name,
            imported_name=imported_name,
        ):
            return "wrong_source"
        return None

    def _is_deep_violation(self, *, module_name: str, imported_name: str) -> bool:
        if module_name == self._project_package:
            if imported_name not in self._project_aliases:
                return False
            return not self._is_safe_to_normalize(imported_name)
        if not module_name.startswith(f"{self._project_package}."):
            return False
        if self._is_private_submodule(module_name):
            return False
        if not self._is_safe_to_normalize(imported_name):
            return False
        return imported_name in self._project_aliases

    def _is_wrong_source_violation(
        self, *, module_name: str, imported_name: str
    ) -> bool:
        if module_name == self._project_package:
            return False
        if "." in module_name:
            return False
        if imported_name not in self._project_aliases:
            return False
        if not self._is_safe_to_normalize(imported_name):
            return False
        return (
            module_name.startswith("flext_") or module_name == "gruponos_meltano_native"
        )

    def _get_file_tier(self) -> int:
        declared_alias = self._facade_to_alias.get(self._file_path.name, "")
        if declared_alias in FACADE_TIER:
            return FACADE_TIER[declared_alias]
        package_name = self._project_package
        if len(package_name) == 0:
            return 99
        marker = f"/src/{package_name}/"
        file_str = str(self._file_path.resolve())
        if marker not in file_str:
            return 99
        relative = file_str.split(marker, maxsplit=1)[1]
        parts = Path(relative).parts[:-1]
        if len(parts) == 0:
            return 99
        first = parts[0]
        if first.startswith("_"):
            normalized = first.lstrip("_")
            if normalized == "services":
                normalized = "service"
            alias = self._facade_to_alias.get(f"{normalized}.py", "")
            if alias in FACADE_TIER:
                return FACADE_TIER[alias]
            if normalized == "result":
                return FACADE_TIER["r"]
            return 4
        return 4

    def _is_safe_to_normalize(self, alias: str) -> bool:
        file_tier = self._file_tier
        alias_tier = FACADE_TIER.get(alias, 99)
        if file_tier < 99:
            return alias_tier < file_tier
        return True

    def _track_present_aliases(
        self,
        aliases: Sequence[cst.ImportAlias],
    ) -> None:
        for imported_alias in aliases:
            imported_name = self._imported_name(imported_alias)
            if imported_name is None:
                continue
            if imported_name == self._declared_alias:
                continue
            if imported_name not in self._project_aliases:
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
            module_name = self._module_name(only_stmt)
            if module_name != self._project_package:
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
            if (imported_name := self._imported_name(imported_alias)) is not None
        }
        new_aliases = [
            cst.ImportAlias(name=cst.Name(alias_name))
            for alias_name in missing
            if alias_name not in existing_names
        ]
        if len(new_aliases) == 0:
            return None

        merged_names = tuple(existing + new_aliases)
        mutable_body[index] = statement.with_changes(
            body=[only_stmt.with_changes(names=merged_names)],
        )
        self._record_change(
            f"Merged normalized aliases into existing import: from {self._project_package} import {', '.join(missing)}",
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
