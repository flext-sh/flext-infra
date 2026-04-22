"""Tier 0 import fixer -- rope-based implementation.

Detects and fixes circular self-imports in internal modules by redirecting
aliases to their correct sources (core, submodule, or TYPE_CHECKING block).
"""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
)
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar

from flext_infra import c, m, t, u


class FlextInfraTransformerTier0ImportFixer:
    """Namespace for Tier 0 import fixing logic and classes."""

    class Analysis(m.Value):
        """Detection results for a single Python file's self-import patterns."""

        model_config = m.ConfigDict(frozen=True, arbitrary_types_allowed=True)

        package_name: Annotated[
            str,
            m.Field(description="Resolved package name for the analyzed file"),
        ]
        file_path: Annotated[
            Path,
            m.Field(description="Python file analyzed for Tier 0 import violations"),
        ]
        alias_to_module: Annotated[
            Mapping[str, str],
            m.Field(description="Alias names mapped to their source modules"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        category_a: Annotated[
            frozenset[str],
            m.Field(description="Top-level aliases that are informational only"),
        ] = m.Field(default_factory=frozenset)
        category_b: Annotated[
            frozenset[str],
            m.Field(description="Core aliases to redirect to the core package"),
        ] = m.Field(default_factory=frozenset)
        category_c: Annotated[
            frozenset[str],
            m.Field(description="Aliases to move into a TYPE_CHECKING block"),
        ] = m.Field(default_factory=frozenset)
        category_d: Annotated[
            frozenset[str],
            m.Field(
                description="Runtime-used aliases requiring direct import handling",
            ),
        ] = m.Field(default_factory=frozenset)

        @u.computed_field()
        @property
        def has_violations(self) -> bool:
            """Return True if any imports need redirecting or moving."""
            return bool(self.category_b or self.category_c or self.category_d)

    class Analyzer:
        """Analyze imports via regex to identify circular Tier 0 aliases."""

        def __init__(
            self,
            *,
            file_path: Path,
            tier0_modules: t.Infra.VariadicTuple[str],
            core_aliases: t.Infra.VariadicTuple[str],
        ) -> None:
            """Initialize analyzer state for Tier 0 import scanning."""
            self._file_path = file_path
            self._tier0_modules = {
                n.removesuffix(c.Infra.EXT_PYTHON) for n in tier0_modules
            }
            self._core_aliases = set(core_aliases)
            self._self_import_aliases: t.Infra.StrSet = set()
            self._runtime_aliases: t.Infra.StrSet = set()

        def build_analysis(self) -> FlextInfraTransformerTier0ImportFixer.Analysis:
            """Parse file and build violation analysis."""
            pkg_name = u.Infra.package_name(self._file_path)
            project_root = u.Infra.project_root(self._file_path)
            package_root = pkg_name.split(".", maxsplit=1)[0]
            pkg_dir = (
                project_root / c.Infra.DEFAULT_SRC_DIR / package_root
                if project_root is not None and package_root
                else Path()
            )
            if not pkg_name or project_root is None or not pkg_dir.is_dir():
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    package_name="",
                    file_path=self._file_path,
                )
            source = self._file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            self._scan_self_imports(source, pkg_name)
            self._scan_runtime_usage(source)
            alias_map: dict[str, str] = {
                alias_name: alias_name for alias_name in c.Infra.RUNTIME_ALIAS_NAMES
            }
            if u.Infra.is_module_toplevel(self._file_path):
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    package_name=pkg_name,
                    file_path=self._file_path,
                    alias_to_module=MappingProxyType(alias_map),
                    category_a=frozenset(self._self_import_aliases),
                )
            category_b: set[str] = set()
            category_c: set[str] = set()
            category_d: set[str] = set()
            for alias in sorted(self._self_import_aliases):
                if alias in self._core_aliases:
                    category_b.add(alias)
                elif alias in self._runtime_aliases:
                    category_d.add(alias)
                else:
                    category_c.add(alias)
            return FlextInfraTransformerTier0ImportFixer.Analysis(
                package_name=pkg_name,
                file_path=self._file_path,
                alias_to_module=MappingProxyType(alias_map),
                category_b=frozenset(category_b),
                category_c=frozenset(category_c),
                category_d=frozenset(category_d),
            )

        def _scan_self_imports(self, source: str, pkg_name: str) -> None:
            """Collect single-letter aliases from self-package imports."""
            for match in c.Infra.FROM_IMPORT_RE.finditer(source):
                module = match.group(1)
                if module != pkg_name:
                    continue
                names_str = match.group(2)
                for name_part in names_str.split(","):
                    name_part = name_part.strip()
                    if not name_part:
                        continue
                    bound = (
                        name_part.split(" as ", maxsplit=1)[1].strip()
                        if " as " in name_part
                        else name_part
                    )
                    if len(bound) == 1 and bound.islower():
                        self._self_import_aliases.add(bound)

        def _scan_runtime_usage(self, source: str) -> None:
            """Detect aliases used at runtime (not just in annotations)."""
            for alias in self._self_import_aliases:
                pattern = re.compile(rf"\b{re.escape(alias)}\b")
                # Check for usage outside import lines and annotations
                for line in source.splitlines():
                    stripped = line.strip()
                    if stripped.startswith(("from ", "import ")):
                        continue
                    if pattern.search(line):
                        self._runtime_aliases.add(alias)
                        break

    class Transformer:
        """Rewrite Tier 0 imports via rope to remove circularity."""

        _CLASS_IMPORTS_MAP: ClassVar[t.StrMapping] = {
            "u": "flext_core",
            "FlextUtilitiesGuardsTypeCore": "flext_core_type_core",
            "FlextUtilitiesGuards": "flext_core",
            "FlextUtilitiesGuardsType": "flext_core_type",
            "FlextUtilitiesCache": "flext_core",
            "FlextUtilitiesMapper": "flext_core",
            "FlextUtilitiesModel": "flext_core",
            "EnumT": "flext_core",
            "T": "flext_core",
            "U": "flext_core",
            "T_Model": "flext_core",
        }

        def __init__(
            self,
            *,
            analysis: FlextInfraTransformerTier0ImportFixer.Analysis,
            alias_to_submodule: t.StrMapping,
            core_package: str,
        ) -> None:
            """Initialize transformer with analysis and insertion settings."""
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
            self._direct_pending: MutableMapping[str, t.Infra.StrSet] = {}
            for a in sorted(analysis.category_d):
                sub = alias_to_submodule.get(
                    a,
                    analysis.alias_to_module.get(a, ""),
                )
                if sub:
                    self._direct_pending.setdefault(sub, set()).add(a)
            self._missing_classes: t.Infra.StrSet = set()
            self._changes: MutableSequence[str] = []

        @property
        def changes(self) -> t.StrSequence:
            """Return recorded transformation changes."""
            return self._changes

        def transform(
            self,
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
        ) -> t.Infra.TransformResult:
            """Apply tier 0 import fixes via rope."""
            source = resource.read()
            self._detect_missing_classes(source)
            if self._root_remove:
                u.Infra.remove_import_names(
                    rope_project,
                    resource,
                    self._package_name,
                    sorted(self._root_remove),
                    apply=True,
                )
            if self._core_pending:
                u.Infra.add_import(
                    rope_project,
                    resource,
                    self._core_package,
                    sorted(self._core_pending),
                    apply=True,
                )
                self._core_pending.clear()
            for sub, aliases in sorted(self._direct_pending.items()):
                if aliases:
                    u.Infra.add_import(
                        rope_project,
                        resource,
                        f"{self._package_name}.{sub}",
                        sorted(aliases),
                        apply=True,
                    )
            for name in sorted(self._missing_classes):
                mod = self._CLASS_IMPORTS_MAP[name]
                u.Infra.add_import(
                    rope_project,
                    resource,
                    mod,
                    [name],
                    apply=True,
                )
            if self._type_checking_pending:
                self._add_type_checking_block(rope_project, resource)
            final = resource.read()
            return final, list(self._changes)

        def _detect_missing_classes(self, source: str) -> None:
            """Find class names used but not imported."""
            self._missing_classes.clear()
            for name in self._CLASS_IMPORTS_MAP:
                if name in source and f"import {name}" not in source:
                    self._missing_classes.add(name)

        def _add_type_checking_block(
            self,
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
        ) -> None:
            """Add TYPE_CHECKING block with pending type-only imports."""
            source = resource.read()
            names = ", ".join(sorted(self._type_checking_pending))
            tc_import = f"from {self._package_name} import {names}"
            if "from typing import TYPE_CHECKING" not in source:
                u.Infra.add_import(
                    rope_project,
                    resource,
                    "typing",
                    ["TYPE_CHECKING"],
                    apply=True,
                )
                self._changes.append("Added 'from typing import TYPE_CHECKING'")
                source = resource.read()
            if "if TYPE_CHECKING:" not in source:
                block = f"\nif TYPE_CHECKING:\n    {tc_import}\n"
                lines = source.splitlines(keepends=True)
                idx = u.Infra.find_import_insert_position(lines)
                lines.insert(idx, block)
                new_source = "".join(lines)
                resource.write(new_source)
                self._changes.append(
                    f"Added TYPE_CHECKING block for {self._package_name}",
                )


__all__: list[str] = ["FlextInfraTransformerTier0ImportFixer"]
