"""FLEXT family-chain discovery + project-kind inference — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import TYPE_CHECKING

from flext_infra import c, u
from flext_infra.refactor._project import FlextInfraRefactorProjectClassifierDeps

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraRefactorProjectClassifierFamily(
    FlextInfraRefactorProjectClassifierDeps
):
    """Parse facade family files and confirm FLEXT family chains + project kind.

    Composed into FlextInfraProjectClassifier via inheritance; dependency
    normalization comes from its native base and source paths from the facade.
    """

    _CLASS_DEF_RE: t.RegexPattern = c.Infra.CLASS_WITH_BASES_RE

    if TYPE_CHECKING:
        _project_root: Path
        _src_path: Path

    def _discover_facade_inheritance(
        self,
    ) -> tuple[Mapping[str, t.Infra.StrSet], t.Infra.StrSet]:
        """Discover facade inheritance.

        Returns:
            The resulting ``tuple[Mapping[str, t.Infra.StrSet], t.Infra.StrSet]``.

        """
        families = u.Infra.facade_families()
        family_bases: Mapping[str, t.Infra.StrSet] = {
            family: set() for family in families
        }
        local_facade_classes: t.Infra.StrSet = set()
        if not self._src_path.is_dir():
            return (family_bases, local_facade_classes)
        for family, declared in families.items():
            for file_path in u.Infra.iter_matching_files(
                self._src_path,
                includes=[f"*{declared.module}{c.Infra.EXT_PYTHON}"],
            ):
                class_bases, class_names = self._parse_family_file(
                    file_path,
                    declared.suffix,
                )
                family_bases[family].update(class_bases)
                local_facade_classes.update(class_names)
        return (family_bases, local_facade_classes)

    def _parse_family_file(
        self,
        file_path: Path,
        suffix: str,
    ) -> tuple[t.Infra.StrSet, t.Infra.StrSet]:
        """Parse family file.

        Returns:
            The resulting ``tuple[t.Infra.StrSet, t.Infra.StrSet]``.

        """
        source = u.Cli.files_read_text(file_path).unwrap()
        base_names: t.Infra.StrSet = set()
        class_names: t.Infra.StrSet = set()
        for match in self._CLASS_DEF_RE.finditer(source):
            name = match.group(1)
            if not name.endswith(suffix):
                continue
            class_names.add(name)
            bases_str = match.group(2)
            for raw_base_part in bases_str.split(","):
                base_part = raw_base_part.strip()
                if not base_part:
                    continue
                base_name = base_part.split("[")[0].rsplit(".", maxsplit=1)[-1].strip()
                if base_name:
                    base_names.add(base_name)
        return (base_names, class_names)

    def _build_confirmed_family_chains(
        self,
        *,
        internal_dependencies: Sequence[str],
        family_bases: Mapping[str, t.Infra.StrSet],
    ) -> Mapping[str, Sequence[str]]:
        """Build confirmed family chains.

        Returns:
            The resulting ``Mapping[str, Sequence[str]]``.

        """
        family_chains: MutableMapping[str, Sequence[str]] = {}
        for family, declared in u.Infra.facade_families().items():
            expected_parents = self._expected_parents_for_family(
                family_suffix=declared.suffix,
                internal_dependencies=internal_dependencies,
            )
            confirmed_bases = family_bases.get(family, set())
            confirmed_expected = [
                parent for parent in expected_parents if parent in confirmed_bases
            ]
            extra_confirmed = sorted(
                base for base in confirmed_bases if base not in set(confirmed_expected)
            )
            family_chains[family] = [*confirmed_expected, *extra_confirmed]
        return family_chains

    def _expected_parents_for_family(
        self,
        *,
        family_suffix: str,
        internal_dependencies: Sequence[str],
    ) -> Sequence[str]:
        """Return the expected parents for a family.

        Returns:
            The expected parents for a family.

        """
        expected: MutableSequence[str] = []
        for dependency in internal_dependencies:
            stem = self._dependency_to_class_stem(dependency)
            if not stem:
                continue
            candidate = f"{stem}{family_suffix}"
            if candidate not in expected:
                expected.append(candidate)
        return expected

    def _dependency_to_class_stem(self, dependency: str) -> str:
        """Dependency to class stem.

        Returns:
            The resulting ``str``.

        """
        normalized = self._normalize_dependency_name(dependency)
        if normalized == c.Infra.PKG_CORE:
            return "Flext"
        if normalized.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            tail = normalized.removeprefix(c.Infra.PKG_PREFIX_HYPHEN)
            parts = [part for part in tail.split("-") if part]
            if not parts:
                return ""
            return "Flext" + "".join(part.capitalize() for part in parts)
        parts = [part for part in normalized.split("-") if part]
        if not parts:
            return ""
        return "".join(part.capitalize() for part in parts)

    def _infer_project_kind(
        self,
        *,
        internal_dependencies: Sequence[str],
        local_facade_classes: t.Infra.StrSet,
    ) -> str:
        """Infer project kind.

        Domain/platform member identity derives from the declared
        per-member ``flext-layer`` attributes in the containing workspace's
        ``.gitmodules``; a standalone checkout declares no members and
        classifies through dependencies alone.

        Returns:
            The resulting ``str``.

        """
        domain_members, platform_members = u.Infra.workspace_member_layer_names(
            self._project_root,
        )
        if not internal_dependencies:
            return "core"
        has_domain_dependency = any(
            dependency in domain_members for dependency in internal_dependencies
        )
        has_platform_dependency = any(
            dependency in platform_members for dependency in internal_dependencies
        )
        dependency_kind = "app"
        if has_domain_dependency and has_platform_dependency:
            dependency_kind = "integration"
        elif has_domain_dependency:
            dependency_kind = "domain"
        elif has_platform_dependency:
            dependency_kind = "platform"
        has_integration_facade = any(
            class_name.startswith(c.Infra.INTEGRATION_CLASS_PREFIXES)
            for class_name in local_facade_classes
        )
        if dependency_kind == "integration" and (not has_integration_facade):
            return "app"
        if (
            dependency_kind == "app"
            and has_domain_dependency
            and has_platform_dependency
            and has_integration_facade
        ):
            return "integration"
        return dependency_kind


__all__: list[str] = ["FlextInfraRefactorProjectClassifierFamily"]
