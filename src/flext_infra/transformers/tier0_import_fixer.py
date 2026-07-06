"""Tier 0 import fixer -- rope-based implementation.

Detects and fixes circular self-imports in internal modules by redirecting
aliases to their correct sources (core, submodule, or TYPE_CHECKING block).
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.transformers._tier0_transformer import (
    FlextInfraTier0TransformerMixin,
)
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraTransformerTier0ImportFixer(FlextInfraTier0TransformerMixin):
    """Namespace for Tier 0 import fixing logic and classes."""

    class Analysis(m.Value):
        """Detection results for a single Python file's self-import patterns."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            arbitrary_types_allowed=True,
        )

        package_name: Annotated[
            str,
            m.Field(description="Resolved package name for the analyzed file"),
        ]
        file_path: Annotated[
            Path,
            m.Field(description="Python file analyzed for Tier 0 import violations"),
        ]
        alias_to_module: Annotated[
            t.StrMapping,
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

        @m.computed_field()
        @property
        def has_violations(self) -> bool:
            """True if any imports need redirecting or moving."""
            return bool(self.category_b or self.category_c or self.category_d)

    class Analyzer:
        """Analyze imports via regex to identify circular Tier 0 aliases."""

        def __init__(
            self,
            *,
            file_path: Path,
            tier0_modules: t.VariadicTuple[str],
            core_aliases: t.VariadicTuple[str],
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
            source = u.Cli.files_read_text(self._file_path).unwrap()
            self._scan_self_imports(source, pkg_name)
            self._scan_runtime_usage(source)
            alias_map: dict[str, str] = {
                alias_name: alias_name
                for alias_name in u.read_project_constants(
                    "flext-infra",
                ).RUNTIME_ALIAS_NAMES
            }
            if u.Infra.matches_module_toplevel(self._file_path):
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
                pattern = c.Infra.compile_word(alias)
                # Check for usage outside import lines and annotations
                for line in source.splitlines():
                    stripped = line.strip()
                    if stripped.startswith(("from ", "import ")):
                        continue
                    if pattern.search(line):
                        self._runtime_aliases.add(alias)
                        break


__all__: list[str] = ["FlextInfraTransformerTier0ImportFixer"]
