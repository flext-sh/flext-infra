"""CST transformer for fixing circular Tier 0 self-imports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra.transformers.import_insertion import (
    FlextInfraTransformerImportInsertion,
)
from flext_infra.utilities import u


class FlextInfraTransformerTier0ImportFixer:
    """Namespace for Tier 0 import fixing logic."""

    @dataclass(frozen=True)
    class Analysis:
        """Detection results for self-import patterns."""

        package_name: str
        file_path: Path
        alias_to_module: dict[str, str] = field(default_factory=dict)
        category_a: set[str] = field(default_factory=set)
        category_b: set[str] = field(default_factory=set)
        category_c: set[str] = field(default_factory=set)
        category_d: set[str] = field(default_factory=set)

        @property
        def has_violations(self) -> bool:
            return bool(self.category_b or self.category_c or self.category_d)

    class ImportEdgeCollector(cst.CSTVisitor):
        """Build internal import edges."""

        def __init__(
            self,
            *,
            current_module: str,
            package_name: str,
            known_modules: frozenset[str],
            lazy_import_maps: Mapping[str, Mapping[str, str]],
        ) -> None:
            self._current_module, self._package_name = current_module, package_name
            self._known_modules, self._lazy_import_maps = (
                known_modules,
                lazy_import_maps,
            )
            self.imported_modules: set[str] = set()

        @override
        def visit_Import(self, node: cst.Import) -> None:
            for i in node.names:
                n = u.Infra.cst_module_name(i.name)
                if n:
                    self._add(n)

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
            base = self._res(node)
            if base:
                self._add(base)
            if isinstance(node.names, cst.ImportStar):
                return
            for i in node.names:
                n = u.Infra.cst_imported_name(i)
                if not n or not base:
                    continue
                lzy = self._lazy_import_maps.get(base, {}).get(n, "")
                if lzy:
                    self._add(lzy)
                self._add(f"{base}.{n}")

        def _res(self, node: cst.ImportFrom) -> str:
            n = u.Infra.cst_module_name(node.module)
            return (
                n
                if not node.relative
                else u.Infra.resolve_relative_module(
                    current_module=self._current_module,
                    level=len(node.relative),
                    module_name=n,
                )
            )

        def _add(self, n: str) -> None:
            if n == self._package_name or n.startswith(f"{self._package_name}."):
                if n in self._known_modules or n == self._package_name:
                    self.imported_modules.add(n)

    class Analyzer(cst.CSTVisitor):
        """Identify circular Tier 0 aliases."""

        def __init__(
            self,
            *,
            file_path: Path,
            tier0_modules: tuple[str, ...],
            core_aliases: tuple[str, ...],
        ) -> None:
            self._file_path = file_path
            self._tier0_modules = {n.removesuffix(".py") for n in tier0_modules}
            self._core_aliases = set(core_aliases)
            self._pkg_name, self._alias_map = "", {}
            self._import_depth = self._annot_depth = self._alias_depth = (
                self._tc_depth
            ) = 0
            self._self_aliases, self._runtime_aliases = set(), set()

        def build_analysis(self) -> FlextInfraTransformerTier0ImportFixer.Analysis:
            pkg_dir, self._pkg_name = u.Infra.package_context(self._file_path)
            if not self._pkg_name:
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    "", self._file_path
                )
            self._alias_map = u.Infra.discover_project_aliases(
                pkg_dir.parent if pkg_dir.name == "src" else pkg_dir
            )
            self._alias_map.update(
                u.Infra.extract_lazy_import_map(pkg_dir / "__init__.py")
            )
            ans = FlextInfraTransformerTier0ImportFixer.Analysis(
                self._pkg_name, self._file_path, self._alias_map
            )
            if u.Infra.cst_is_module_toplevel(self._file_path):
                ans.category_a.update(self._self_aliases)
                return ans
            agg = self._detect_aggregator()
            for a in sorted(self._self_aliases):
                mod = self._alias_map.get(a, "")
                if a in self._core_aliases or (agg and mod == agg):
                    ans.category_b.add(a)
                elif mod in self._tier0_modules:
                    ans.category_a.add(a)
                elif a in self._runtime_aliases:
                    ans.category_d.add(a)
                else:
                    ans.category_c.add(a)
            return ans

        def _detect_aggregator(self) -> str:
            for p in self._file_path.parts:
                if p.startswith("_") and not p.startswith("__"):
                    return p.lstrip("_")
            return ""

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
            self._import_depth += 1
            _, pkg = u.Infra.package_context(self._file_path)
            if (
                not pkg
                or not node.module
                or node.relative
                or u.Infra.cst_module_name(node.module) != pkg
            ):
                return
            if isinstance(node.names, cst.ImportStar):
                return
            for i in node.names:
                b = u.Infra.cst_asname_to_local(i.asname) or (
                    i.name.value if isinstance(i.name, cst.Name) else ""
                )
                if len(b) == 1 and b.islower():
                    self._self_aliases.add(b)

        @override
        def leave_ImportFrom(self, node: cst.ImportFrom) -> None:
            self._import_depth = max(0, self._import_depth - 1)

        @override
        def visit_Annotation(self, node: cst.Annotation) -> None:
            self._annot_depth += 1

        @override
        def leave_Annotation(self, node: cst.Annotation) -> None:
            self._annot_depth = max(0, self._annot_depth - 1)

        @override
        def visit_TypeAlias(self, node: cst.TypeAlias) -> None:
            self._alias_depth += 1

        @override
        def leave_TypeAlias(self, node: cst.TypeAlias) -> None:
            self._alias_depth = max(0, self._alias_depth - 1)

        @override
        def visit_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._tc_depth += 1

        @override
        def leave_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._tc_depth = max(0, self._tc_depth - 1)

        @override
        def visit_Name(self, node: cst.Name) -> None:
            if node.value in self._self_aliases and self._import_depth == 0:
                if self._alias_depth > 0 or not (
                    self._annot_depth > 0 or self._tc_depth > 0
                ):
                    self._runtime_aliases.add(node.value)

    class Transformer(cst.CSTTransformer):
        """Rewrite Tier 0 imports."""

        _CLS_MAP = {
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
            self.ans, self._pkg, self._core = (
                analysis,
                analysis.package_name,
                core_package,
            )
            self._rem = (
                set(analysis.category_b)
                | set(analysis.category_c)
                | set(analysis.category_d)
            )
            self._core_pnd, self._tc_pnd, self._dir_pnd = (
                set(analysis.category_b),
                set(analysis.category_c),
                {},
            )
            for a in sorted(analysis.category_d):
                s = alias_to_submodule.get(a, analysis.alias_to_module.get(a, ""))
                if s:
                    self._dir_pnd.setdefault(s, set()).add(a)
            self.changes, self._tc_present, self._miss_cls = [], False, set()

        @override
        def visit_Module(self, node: cst.Module) -> None:
            cde = node.code
            for n in self._CLS_MAP:
                if n in cde and f"import {n}" not in cde:
                    self._miss_cls.add(n)

        @override
        def leave_ImportFrom(
            self, orig: cst.ImportFrom, updated: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            mod = u.Infra.cst_module_name(updated.module)
            if mod == "typing" and "TYPE_CHECKING" in u.Infra.cst_collect_bound_names(
                updated
            ):
                self._tc_present = True
            if mod == self._pkg:
                return self._rw_root(updated)
            if mod == self._core:
                return self._mrg(updated, self._core_pnd)
            for s, p in self._dir_pnd.items():
                if mod == f"{self._pkg}.{s}":
                    return self._mrg(updated, p)
            return updated

        @override
        def leave_Module(self, orig: cst.Module, updated: cst.Module) -> cst.Module:
            bdy = list(updated.body)
            if not self._tc_present and self._tc_pnd:
                bdy.insert(
                    self._idx(bdy), u.Infra.cst_import_line("typing", ["TYPE_CHECKING"])
                )
                self._tc_present = True
                self.changes.append("Added TYPE_CHECKING import")
            adds = self._build_adds()
            if adds:
                bdy[self._idx(bdy) : self._idx(bdy)] = adds
            if self._tc_pnd:
                bdy.insert(
                    self._idx(bdy),
                    cst.If(
                        test=cst.Name("TYPE_CHECKING"),
                        body=cst.IndentedBlock(
                            body=[
                                u.Infra.cst_import_line(self._pkg, list(self._tc_pnd))
                            ]
                        ),
                    ),
                )
                self.changes.append(f"Added TYPE_CHECKING block for {self._pkg}")
            return updated.with_changes(body=tuple(bdy))

        def _rw_root(
            self, node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            if isinstance(node.names, cst.ImportStar):
                return node
            rem = [
                i
                for i in node.names
                if (
                    u.Infra.cst_asname_to_local(i.asname)
                    or (i.name.value if isinstance(i.name, cst.Name) else "")
                )
                not in self._rem
            ]
            return (
                node.with_changes(names=tuple(rem))
                if rem
                else cst.RemovalSentinel.REMOVE
            )

        def _mrg(self, node: cst.ImportFrom, p: set[str]) -> cst.ImportFrom:
            if isinstance(node.names, cst.ImportStar):
                return node
            ext = u.Infra.cst_collect_bound_names(node)
            add = [cst.ImportAlias(name=cst.Name(a)) for a in sorted(p - ext)]
            if not add:
                return node
            p.clear()
            return node.with_changes(names=tuple(list(node.names) + add))

        def _build_adds(self) -> list[cst.BaseStatement]:
            res: list[cst.BaseStatement] = []
            if self._core_pnd:
                res.append(u.Infra.cst_import_line(self._core, sorted(self._core_pnd)))
                self._core_pnd.clear()
            res.extend(
                u.Infra.cst_import_line(f"{self._pkg}.{s}", sorted(self._dir_pnd[s]))
                for s in sorted(self._dir_pnd)
                if self._dir_pnd[s]
            )
            res.extend(
                u.Infra.cst_import_line(self._CLS_MAP[n], [n])
                for n in sorted(self._miss_cls)
            )
            return res

        def _idx(
            self, bdy: Sequence[cst.BaseStatement | cst.BaseCompoundStatement]
        ) -> int:
            i = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
                bdy
            )
            while (
                i < len(bdy)
                and isinstance(bdy[i], cst.SimpleStatementLine)
                and isinstance(bdy[i].body[0], (cst.Import, cst.ImportFrom))
            ):
                i += 1
            return i


__all__ = ["FlextInfraTransformerTier0ImportFixer"]
