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


class ImportNormalizerVisitor(cst.CSTVisitor):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._file_path = file_path
        self._project_package = project_package
        self._alias_map = (
            alias_map
            if alias_map is not None
            else c.Infra.RUNTIME_ALIAS_NAMES_BY_PACKAGE
        )
        self._project_aliases = set(self._alias_map.get(project_package, ()))
        self._declared_alias = c.Infra.FACADE_FILE_DECLARES_ALIAS.get(
            file_path.name, ""
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
        if not module_name.startswith(f"{self._project_package}."):
            return False
        if self._is_private_submodule(module_name):
            return False
        aliases = self._alias_map.get(self._project_package, ())
        return imported_name in aliases

    def _is_wrong_source_violation(
        self, *, module_name: str, imported_name: str
    ) -> bool:
        if module_name == self._project_package:
            return False
        if module_name not in self._alias_map:
            return False
        if imported_name not in self._project_aliases:
            return False
        source_aliases = self._alias_map.get(module_name, ())
        return imported_name in source_aliases


class ImportNormalizerTransformer(cst.CSTTransformer):
    def __init__(
        self,
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._file_path = file_path
        self._project_package = project_package
        self._alias_map = (
            alias_map
            if alias_map is not None
            else c.Infra.RUNTIME_ALIAS_NAMES_BY_PACKAGE
        )
        self._project_aliases = set(self._alias_map.get(project_package, ()))
        self._declared_alias = c.Infra.FACADE_FILE_DECLARES_ALIAS.get(
            file_path.name, ""
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
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[ImportViolation]:
        if file_path.name == "__init__.py" or len(project_package) == 0:
            return []
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return []
        visitor = ImportNormalizerVisitor(
            file_path=file_path,
            project_package=project_package,
            alias_map=alias_map,
        )
        module.visit(visitor)
        return visitor.violations

    @staticmethod
    def normalize_file(
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[str]:
        if file_path.name == "__init__.py" or len(project_package) == 0:
            return []
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return []
        transformer = ImportNormalizerTransformer(
            file_path=file_path,
            project_package=project_package,
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
        if not module_name.startswith(f"{self._project_package}."):
            return False
        if self._is_private_submodule(module_name):
            return False
        aliases = self._alias_map.get(self._project_package, ())
        return imported_name in aliases

    def _is_wrong_source_violation(
        self, *, module_name: str, imported_name: str
    ) -> bool:
        if module_name == self._project_package:
            return False
        if module_name not in self._alias_map:
            return False
        if imported_name not in self._project_aliases:
            return False
        source_aliases = self._alias_map.get(module_name, ())
        return imported_name in source_aliases

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
