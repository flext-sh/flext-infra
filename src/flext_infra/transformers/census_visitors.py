"""CST visitors for census usage detection.

Contains import discovery and usage collection visitors used by
the census module to detect method access patterns across the codebase.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, m, t, u


class FlextInfraCensusImportDiscoveryVisitor(cst.CSTVisitor):
    """Discover family alias and direct class imports via LibCST.

    Parametrized by ``family_alias`` (e.g. ``"u"``) and
    ``facade_class_prefix`` (e.g. ``"FlextUtilities"``).
    """

    def __init__(
        self,
        *,
        family_alias: str,
        facade_class_prefix: str,
    ) -> None:
        """Initialize with family alias and facade class prefix."""
        super().__init__()
        self.family_alias = family_alias
        self.facade_class_prefix = facade_class_prefix
        self.alias_locals: t.Infra.StrSet = set()
        self.direct_imports: t.MutableStrMapping = {}

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        if node.module is None:
            return
        module_str = u.Infra.cst_module_name(node.module)
        if not module_str:
            return
        if isinstance(node.names, cst.ImportStar):
            return
        for alias in node.names:
            imported_name = alias.name.value if isinstance(alias.name, cst.Name) else ""
            local_name = (
                u.Infra.cst_asname_to_local(alias.asname)
                if alias.asname
                else imported_name
            )
            if not local_name:
                local_name = imported_name

            if imported_name in {self.family_alias, self.facade_class_prefix} and (
                "flext_core" in module_str or "flext_" in module_str
            ):
                self.alias_locals.add(local_name)

            if (
                imported_name.startswith(self.facade_class_prefix)
                and "flext_core" in module_str
            ):
                self.direct_imports[local_name] = imported_name


class FlextInfraCensusUsageCollector(cst.CSTVisitor):
    """Detect method accesses via LibCST attribute resolution.

    Detects three access modes:
    1. ``alias.method_name(...)`` — flat alias via facade
    2. ``alias.ClassName.method_name()`` — namespaced via inner class
    3. ``FlextXxxYyy.method_name()`` — direct class reference
    """

    def __init__(
        self,
        *,
        method_index: Mapping[str, t.Infra.StrSet],
        flat_aliases: Mapping[str, t.Infra.StrPair],
        inner_class_map: t.StrMapping,
        alias_locals: t.Infra.StrSet,
        direct_imports: t.StrMapping,
        file_path: Path,
        project_name: str,
    ) -> None:
        """Initialize with method index and import context."""
        super().__init__()
        self.method_index = method_index
        self.flat_aliases = flat_aliases
        self.inner_class_map = inner_class_map
        self.alias_locals = alias_locals
        self.direct_imports = direct_imports
        self.file_path = file_path
        self.project_name = project_name
        self.records: MutableSequence[m.Infra.CensusUsageRecord] = []

    @override
    def visit_Attribute(self, node: cst.Attribute) -> None:
        method_name = node.attr.value
        value = node.value

        if (
            isinstance(value, cst.Name)
            and value.value in self.alias_locals
            and method_name in self.flat_aliases
        ):
            cls, orig = self.flat_aliases[method_name]
            self._record(cls, orig, c.Infra.Census.MODE_ALIAS_FLAT)

        if (
            isinstance(value, cst.Attribute)
            and u.Infra.cst_root_name(value) in self.alias_locals
        ):
            inner_name = value.attr.value
            base_class = self.inner_class_map.get(inner_name, "")
            if (
                base_class in self.method_index
                and method_name in self.method_index[base_class]
            ):
                self._record(
                    base_class,
                    method_name,
                    c.Infra.Census.MODE_ALIAS_NS,
                )

        if isinstance(value, cst.Name):
            actual = self.direct_imports.get(value.value, value.value)
            if actual in self.method_index and method_name in self.method_index[actual]:
                self._record(actual, method_name, c.Infra.Census.MODE_DIRECT)

    def _record(self, class_name: str, method_name: str, mode: str) -> None:
        self.records.append(
            m.Infra.CensusUsageRecord(
                class_name=class_name,
                method_name=method_name,
                access_mode=mode,
                file_path=str(self.file_path),
                project=self.project_name,
            ),
        )


__all__ = ["FlextInfraCensusImportDiscoveryVisitor", "FlextInfraCensusUsageCollector"]
