"""CST transformer for fixing circular Tier 0 self-imports in internal modules.

Distinguishes between package facades (Básicas) and internal submodules (Módulos Internos)
using directory depth and naming conventions across flext, algar, and gruponos.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, override

import libcst as cst

from flext_infra.transformers.import_insertion import (
    FlextInfraTransformerImportInsertion,
)
from flext_infra.utilities import u


class FlextInfraTransformerTier0ImportFixer:
    """Namespace for Tier 0 import fixing logic and classes."""

    @dataclass(frozen=True)
    class Analysis:
        """Detection results for a single Python file's self-import patterns."""

        package_name: str
        file_path: Path
        alias_to_module: dict[str, str] = field(default_factory=dict)
        category_a: set[str] = field(default_factory=set)
        category_b: set[str] = field(default_factory=set)
        category_c: set[str] = field(default_factory=set)
        category_d: set[str] = field(default_factory=set)

        @property
        def has_violations(self) -> bool:
            """Return True if any imports need redirecting or moving."""
            return bool(self.category_b or self.category_c or self.category_d)

    class Analyzer(cst.CSTVisitor):
        """Analyze imports and names to identify circular Tier 0 aliases."""

        def __init__(
            self,
            *,
            file_path: Path,
            tier0_modules: tuple[str, ...],
            core_aliases: tuple[str, ...],
        ) -> None:
            """Initialize analyzer state for Tier 0 import scanning."""
            self._file_path = file_path
            self._tier0_modules = {n.removesuffix(".py") for n in tier0_modules}
            self._core_aliases = set(core_aliases)
            self._import_depth = 0
            self._annotation_depth = 0
            self._type_alias_depth = 0
            self._type_checking_depth = 0
            self._self_import_aliases: set[str] = set()
            self._runtime_aliases: set[str] = set()

        def build_analysis(self) -> FlextInfraTransformerTier0ImportFixer.Analysis:
            """Process visited nodes and build violation analysis."""
            pkg_dir, pkg_name = u.Infra.package_context(self._file_path)
            if not pkg_name:
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    package_name="", file_path=self._file_path
                )

            alias_map = u.Infra.discover_project_aliases(
                pkg_dir.parent if pkg_dir.name == "src" else pkg_dir
            )
            alias_map.update(u.Infra.extract_lazy_import_map(pkg_dir / "__init__.py"))

            analysis = FlextInfraTransformerTier0ImportFixer.Analysis(
                package_name=pkg_name,
                file_path=self._file_path,
                alias_to_module=alias_map,
            )

            if u.Infra.cst_is_module_toplevel(self._file_path):
                analysis.category_a.update(self._self_import_aliases)
                return analysis

            for alias in sorted(self._self_import_aliases):
                if alias in self._core_aliases:
                    analysis.category_b.add(alias)
                elif alias in self._runtime_aliases:
                    analysis.category_d.add(alias)
                else:
                    analysis.category_c.add(alias)
            return analysis

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
            self._import_depth += 1
            _, pkg_name = u.Infra.package_context(self._file_path)
            if (
                not pkg_name
                or not node.module
                or node.relative
                or u.Infra.cst_module_name(node.module) != pkg_name
            ):
                return
            if isinstance(node.names, cst.ImportStar):
                return
            for item in node.names:
                bound = u.Infra.cst_asname_to_local(item.asname) or (
                    item.name.value if isinstance(item.name, cst.Name) else ""
                )
                if len(bound) == 1 and bound.islower():
                    self._self_import_aliases.add(bound)

        @override
        def leave_ImportFrom(self, node: cst.ImportFrom) -> None:
            self._import_depth = max(0, self._import_depth - 1)

        @override
        def visit_Annotation(self, node: cst.Annotation) -> None:
            self._annotation_depth += 1

        @override
        def leave_Annotation(self, node: cst.Annotation) -> None:
            self._annotation_depth = max(0, self._annotation_depth - 1)

        @override
        def visit_TypeAlias(self, node: cst.TypeAlias) -> None:
            self._type_alias_depth += 1

        @override
        def leave_TypeAlias(self, node: cst.TypeAlias) -> None:
            self._type_alias_depth = max(0, self._type_alias_depth - 1)

        @override
        def visit_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._type_checking_depth += 1

        @override
        def leave_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._type_checking_depth = max(0, self._type_checking_depth - 1)

        @override
        def visit_Name(self, node: cst.Name) -> None:
            if node.value not in self._self_import_aliases or self._import_depth > 0:
                return
            if self._type_alias_depth > 0 or not (
                self._annotation_depth > 0 or self._type_checking_depth > 0
            ):
                self._runtime_aliases.add(node.value)

    class Transformer(cst.CSTTransformer):
        """Rewrite Tier 0 imports to remove circularity and enforce order."""

        _CLASS_IMPORTS_MAP: ClassVar[dict[str, str]] = {
            "FlextRuntime": "flext_core.runtime",
            "FlextUtilitiesGuardsTypeCore": "flext_core._utilities.guards_type_core",
            "FlextUtilitiesGuards": "flext_core._utilities.guards",
            "FlextUtilitiesGuardsType": "flext_core._utilities.guards_type",
            "FlextUtilitiesCache": "flext_core._utilities.cache",
            "FlextUtilitiesMapper": "flext_core._utilities.mapper",
            "FlextUtilitiesModel": "flext_core._utilities.model",
            "EnumT": "flext_core._typings.generics",
            "T": "flext_core._typings.generics",
            "U": "flext_core._typings.generics",
            "T_Model": "flext_core._typings.generics",
        }

        def __init__(
            self,
            *,
            analysis: FlextInfraTransformerTier0ImportFixer.Analysis,
            alias_to_submodule: dict[str, str],
            core_package: str,
        ) -> None:
            """Initialize transformer with analysis and insertion configuration."""
            self.analysis = analysis
            self._package_name = analysis.package_name
            self._core_package = core_package
            self._root_remove = (
                set(analysis.category_b)
                | set(analysis.category_c)
                | set(analysis.category_d)
            )
            self._core_pending = set(analysis.category_b)
            self._type_checking_pending = set(analysis.category_c)
            self._direct_pending: dict[str, set[str]] = {}
            for a in sorted(analysis.category_d):
                sub = alias_to_submodule.get(a, analysis.alias_to_module.get(a, ""))
                if sub:
                    self._direct_pending.setdefault(sub, set()).add(a)
            self._changes: list[str] = []
            self._type_checking_import_present = False
            self._missing_classes: set[str] = set()

        @property
        def changes(self) -> list[str]:
            """Return recorded transformation changes."""
            return self._changes

        @override
        def visit_Module(self, node: cst.Module) -> None:
            src = node.code
            for n in self._CLASS_IMPORTS_MAP:
                if n in src and f"import {n}" not in src:
                    self._missing_classes.add(n)

        @override
        def leave_ImportFrom(
            self, orig: cst.ImportFrom, updated: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            mod = u.Infra.cst_module_name(updated.module)
            if mod == "typing" and "TYPE_CHECKING" in u.Infra.cst_collect_bound_names(
                updated
            ):
                self._type_checking_import_present = True
            if mod == self._package_name:
                return self._rewrite_root_self_import(updated)
            if mod == self._core_package:
                return self._merge_into_import(updated, self._core_pending)
            for sub, pnd in self._direct_pending.items():
                if mod == f"{self._package_name}.{sub}":
                    return self._merge_into_import(updated, pnd)
            return updated

        @override
        def leave_Module(self, orig: cst.Module, updated: cst.Module) -> cst.Module:
            stmts = list(updated.body)
            if not self._type_checking_import_present and self._type_checking_pending:
                stmts.insert(
                    self._idx(stmts),
                    u.Infra.cst_import_line("typing", ["TYPE_CHECKING"]),
                )
                self._type_checking_import_present = True
                self._changes.append("Added 'from typing import TYPE_CHECKING'")

            additions = self._build_additions()
            if additions:
                stmts[self._idx(stmts) : self._idx(stmts)] = additions

            if self._type_checking_pending:
                stmts.insert(
                    self._idx(stmts),
                    cst.If(
                        test=cst.Name("TYPE_CHECKING"),
                        body=cst.IndentedBlock(
                            body=[
                                u.Infra.cst_import_line(
                                    self._package_name,
                                    list(self._type_checking_pending),
                                )
                            ]
                        ),
                    ),
                )
                self._changes.append(
                    f"Added TYPE_CHECKING block for {self._package_name}"
                )
            return updated.with_changes(body=tuple(stmts))

        def _rewrite_root_self_import(
            self, node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            rem = [
                i
                for i in node.names
                if (
                    u.Infra.cst_asname_to_local(i.asname)
                    or (i.name.value if isinstance(i.name, cst.Name) else "")
                )
                not in self._root_remove
            ]
            if not rem:
                return cst.RemovalSentinel.REMOVE
            return node.with_changes(names=tuple(rem))

        def _merge_into_import(
            self, node: cst.ImportFrom, pnd: set[str]
        ) -> cst.ImportFrom:
            ext = u.Infra.cst_collect_bound_names(node)
            add = [cst.ImportAlias(name=cst.Name(a)) for a in sorted(pnd - ext)]
            if not add:
                return node
            pnd.clear()
            return node.with_changes(names=tuple(list(node.names) + add))

        def _build_additions(self) -> list[cst.BaseStatement]:
            res: list[cst.BaseStatement] = []
            if self._core_pending:
                res.append(
                    u.Infra.cst_import_line(
                        self._core_package, sorted(self._core_pending)
                    )
                )
                self._core_pending.clear()
            res.extend(
                u.Infra.cst_import_line(
                    f"{self._package_name}.{sub}", sorted(self._direct_pending[sub])
                )
                for sub in sorted(self._direct_pending)
                if self._direct_pending[sub]
            )
            res.extend(
                u.Infra.cst_import_line(self._CLASS_IMPORTS_MAP[n], [n])
                for n in sorted(self._missing_classes)
            )
            return res

        def _idx(self, body: Sequence[cst.BaseStatement]) -> int:
            i = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
                body
            )
            while (
                i < len(body)
                and isinstance(body[i], cst.SimpleStatementLine)
                and isinstance(body[i].body[0], (cst.Import, cst.ImportFrom))
            ):
                i += 1
            return i


Tier0ImportAnalysis = FlextInfraTransformerTier0ImportFixer.Analysis
Tier0ImportAnalyzer = FlextInfraTransformerTier0ImportFixer.Analyzer
Tier0ImportContextDiscovery = FlextInfraTransformerTier0ImportFixer.Analyzer
Tier0ImportFixer = FlextInfraTransformerTier0ImportFixer.Transformer

__all__ = [
    "FlextInfraTransformerTier0ImportFixer",
    "Tier0ImportAnalysis",
    "Tier0ImportAnalyzer",
    "Tier0ImportContextDiscovery",
    "Tier0ImportFixer",
]
