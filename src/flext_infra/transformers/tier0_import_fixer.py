"""Tier 0 import fixer -- rope-based implementation.

Detects and fixes circular self-imports in internal modules by redirecting
aliases to their correct sources (core, submodule, or TYPE_CHECKING block).
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from flext_infra import FlextInfraUtilitiesDiscovery, FlextInfraUtilitiesRope, c, t, u


class FlextInfraTransformerTier0ImportFixer:
    """Namespace for Tier 0 import fixing logic and classes."""

    @dataclass(frozen=True)
    class Analysis:
        """Detection results for a single Python file's self-import patterns."""

        package_name: str
        file_path: Path
        alias_to_module: t.MutableStrMapping = field(
            default_factory=lambda: dict[str, str](),
        )
        category_a: t.Infra.StrSet = field(default_factory=lambda: set[str]())
        category_b: t.Infra.StrSet = field(default_factory=lambda: set[str]())
        category_c: t.Infra.StrSet = field(default_factory=lambda: set[str]())
        category_d: t.Infra.StrSet = field(default_factory=lambda: set[str]())

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
            self._tier0_modules = {n.removesuffix(".py") for n in tier0_modules}
            self._core_aliases = set(core_aliases)
            self._self_import_aliases: t.Infra.StrSet = set()
            self._runtime_aliases: t.Infra.StrSet = set()

        def build_analysis(self) -> FlextInfraTransformerTier0ImportFixer.Analysis:
            """Parse file and build violation analysis."""
            pkg_dir, pkg_name = FlextInfraUtilitiesDiscovery.package_context(
                self._file_path,
            )
            if not pkg_name:
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    package_name="",
                    file_path=self._file_path,
                )
            source = self._file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            self._scan_self_imports(source, pkg_name)
            self._scan_runtime_usage(source)
            alias_map: t.MutableStrMapping = dict(
                FlextInfraUtilitiesDiscovery.discover_project_aliases(
                    pkg_dir.parent if pkg_dir.name == "src" else pkg_dir,
                ),
            )
            alias_map.update(
                FlextInfraUtilitiesDiscovery.extract_lazy_import_map(
                    pkg_dir / "__init__.py",
                ),
            )
            analysis = FlextInfraTransformerTier0ImportFixer.Analysis(
                package_name=pkg_name,
                file_path=self._file_path,
                alias_to_module=alias_map,
            )
            if u.Infra.is_module_toplevel(self._file_path):
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

        def _scan_self_imports(self, source: str, pkg_name: str) -> None:
            """Collect single-letter aliases from self-package imports."""
            for match in c.Infra.SourceCode.FROM_IMPORT_RE.finditer(source):
                module = match.group(1)
                if module != pkg_name:
                    continue
                names_str = match.group(2)
                for name_part in names_str.split(","):
                    name_part = name_part.strip()
                    if not name_part:
                        continue
                    bound = u.Infra.bound_name(name_part)
                    if len(bound) == 1 and bound.islower():
                        self._self_import_aliases.add(bound)

        def _scan_runtime_usage(self, source: str) -> None:
            """Detect aliases used at runtime (not just in annotations)."""
            for alias in self._self_import_aliases:
                pattern = u.Infra.word_boundary_re(alias)
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
            alias_to_submodule: t.StrMapping,
            core_package: str,
        ) -> None:
            """Initialize transformer with analysis and insertion config."""
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
        ) -> tuple[str, Sequence[str]]:
            """Apply tier 0 import fixes via rope."""
            source = FlextInfraUtilitiesRope.read_source(resource)
            self._detect_missing_classes(source)
            if self._root_remove:
                FlextInfraUtilitiesRope.remove_import_names(
                    rope_project,
                    resource,
                    self._package_name,
                    sorted(self._root_remove),
                    apply=True,
                )
            if self._core_pending:
                FlextInfraUtilitiesRope.add_import(
                    rope_project,
                    resource,
                    self._core_package,
                    sorted(self._core_pending),
                    apply=True,
                )
                self._core_pending.clear()
            for sub, aliases in sorted(self._direct_pending.items()):
                if aliases:
                    FlextInfraUtilitiesRope.add_import(
                        rope_project,
                        resource,
                        f"{self._package_name}.{sub}",
                        sorted(aliases),
                        apply=True,
                    )
            for name in sorted(self._missing_classes):
                mod = self._CLASS_IMPORTS_MAP[name]
                FlextInfraUtilitiesRope.add_import(
                    rope_project,
                    resource,
                    mod,
                    [name],
                    apply=True,
                )
            if self._type_checking_pending:
                self._add_type_checking_block(rope_project, resource)
            final = FlextInfraUtilitiesRope.read_source(resource)
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
            source = FlextInfraUtilitiesRope.read_source(resource)
            names = ", ".join(sorted(self._type_checking_pending))
            tc_import = f"from {self._package_name} import {names}"
            if "from typing import TYPE_CHECKING" not in source:
                FlextInfraUtilitiesRope.add_import(
                    rope_project,
                    resource,
                    "typing",
                    ["TYPE_CHECKING"],
                    apply=True,
                )
                self._changes.append("Added 'from typing import TYPE_CHECKING'")
                source = FlextInfraUtilitiesRope.read_source(resource)
            if "if TYPE_CHECKING:" not in source:
                block = f"\nif TYPE_CHECKING:\n    {tc_import}\n"
                lines = source.splitlines(keepends=True)
                idx = u.Infra.find_import_insert_position(lines)
                lines.insert(idx, block)
                new_source = "".join(lines)
                FlextInfraUtilitiesRope.write_source(
                    rope_project,
                    resource,
                    new_source,
                    description="add TYPE_CHECKING block",
                )
                self._changes.append(
                    f"Added TYPE_CHECKING block for {self._package_name}",
                )


__all__ = ["FlextInfraTransformerTier0ImportFixer"]
