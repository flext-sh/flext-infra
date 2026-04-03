"""Facade and dependency-chain helpers for namespace refactors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping, Sequence
from pathlib import Path
from typing import ClassVar

import tomlkit
from tomlkit.exceptions import TOMLKitError

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraNamespaceFacadeScanner,
    FlextInfraUtilitiesFormatting,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorNamespaceFacades:
    """Facade generation and dependency-chain helpers."""

    _base_chains_cache: ClassVar[MutableMapping[Path, t.StrSequenceMapping]] = {}

    @staticmethod
    def build_expected_base_chains(
        *,
        project_root: Path,
    ) -> t.StrSequenceMapping:
        resolved = project_root.resolve()
        cached = FlextInfraUtilitiesRefactorNamespaceFacades._base_chains_cache.get(
            resolved,
        )
        if cached is not None:
            return cached
        result = FlextInfraUtilitiesRefactorNamespaceFacades._compute_base_chains(
            project_root=resolved,
        )
        FlextInfraUtilitiesRefactorNamespaceFacades._base_chains_cache[resolved] = (
            result
        )
        return result

    @staticmethod
    def _compute_base_chains(
        *,
        project_root: Path,
    ) -> t.StrSequenceMapping:
        pyproject_path = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return {}
        try:
            doc = tomlkit.parse(
                pyproject_path.read_text(encoding=c.Infra.Encoding.DEFAULT),
            )
        except (OSError, TOMLKitError):
            return {}
        dep_names = (
            FlextInfraUtilitiesRefactorNamespaceFacades._extract_dep_names_from_doc(
                doc=doc,
            )
        )
        chains: t.MutableStrSequenceMapping = defaultdict(list)
        for dep_name in dep_names:
            if dep_name == c.Infra.Packages.CORE or not dep_name.startswith(
                c.Infra.Packages.PREFIX_HYPHEN
            ):
                continue
            stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
                project_name=dep_name,
            )
            if not stem:
                continue
            for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
                chains[family].append(f"{stem}{suffix}")
        return chains

    @staticmethod
    def _extract_dep_names_from_doc(
        *,
        doc: tomlkit.TOMLDocument,
    ) -> t.StrSequence:
        dep_names: t.Infra.StrSet = set()
        raw: t.Infra.TomlData = doc.unwrap()
        FlextInfraUtilitiesRefactorNamespaceFacades._collect_pep621_deps(
            raw=raw,
            dep_names=dep_names,
        )
        FlextInfraUtilitiesRefactorNamespaceFacades._collect_poetry_deps(
            raw=raw,
            dep_names=dep_names,
        )
        return sorted(dep_names)

    @staticmethod
    def _collect_pep621_deps(
        *,
        raw: t.Infra.TomlData,
        dep_names: t.Infra.StrSet,
    ) -> None:
        project_val: t.Infra.InfraValue = raw.get("project")
        if not FlextUtilities.is_mapping(project_val):
            return
        deps_val: t.Infra.InfraValue = project_val.get("dependencies")
        if not isinstance(deps_val, Sequence) or isinstance(deps_val, str):
            return
        for item_val in deps_val:
            if not isinstance(item_val, str) or " @ " not in item_val:
                continue
            _name, path_part = item_val.split(" @ ", 1)
            cleaned = path_part.strip().removeprefix("file:").removeprefix("./").strip()
            if cleaned:
                dep_names.add(Path(cleaned).name)

    @staticmethod
    def _collect_poetry_deps(
        *,
        raw: t.Infra.TomlData,
        dep_names: t.Infra.StrSet,
    ) -> None:
        tool_val: t.Infra.InfraValue = raw.get("tool")
        if not FlextUtilities.is_mapping(tool_val):
            return
        poetry_val: t.Infra.InfraValue = tool_val.get("poetry")
        if not FlextUtilities.is_mapping(poetry_val):
            return
        deps_val: t.Infra.InfraValue = poetry_val.get("dependencies")
        if not FlextUtilities.is_mapping(deps_val):
            return
        for dep_entry in deps_val.values():
            if not FlextUtilities.is_mapping(dep_entry):
                continue
            dep_path_val: t.Infra.InfraValue = dep_entry.get("path")
            dep_path = dep_path_val.strip() if isinstance(dep_path_val, str) else ""
            if dep_path:
                dep_names.add(Path(dep_path.removeprefix("./")).name)

    @staticmethod
    def _base_import_for_family(
        *,
        family: str,
        base_chains: t.StrSequenceMapping | None = None,
    ) -> str:
        if base_chains:
            chain = base_chains.get(family, [])
            if chain:
                return "\n".join(
                    f"from {FlextInfraUtilitiesFormatting.class_name_to_module(base)} import {base}"
                    for base in chain
                )
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "Utilities")
        return f"from flext_core import Flext{suffix}"

    @staticmethod
    def _base_class_for_family(
        *,
        family: str,
        base_chains: t.StrSequenceMapping | None = None,
    ) -> str:
        if base_chains:
            chain = base_chains.get(family, [])
            if chain:
                return ", ".join(chain)
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "Utilities")
        return f"Flext{suffix}"

    @staticmethod
    def _write_missing_facade_file(
        *,
        file_path: Path,
        family: str,
        class_name: str,
        base_chains: t.StrSequenceMapping | None = None,
    ) -> None:
        content = (
            '"""Auto-generated facade to enforce MRO namespace contracts."""\n\n'
            "from __future__ import annotations\n\n"
            f"{FlextInfraUtilitiesRefactorNamespaceFacades._base_import_for_family(family=family, base_chains=base_chains)}\n\n"
            f"class {class_name}({FlextInfraUtilitiesRefactorNamespaceFacades._base_class_for_family(family=family, base_chains=base_chains)}):\n"
            "    pass\n\n"
            f"{family} = {class_name}\n"
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _ = file_path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def ensure_missing_facades(
        *,
        project_root: Path,
        project_name: str,
        facade_statuses: Sequence[m.Infra.FacadeStatus],
        workspace_root: Path | None = None,
    ) -> None:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / c.Infra.Files.INIT_PY).is_file()
        ]
        if not package_dirs:
            return
        package_dir = package_dirs[0]
        stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        base_chains = (
            FlextInfraUtilitiesRefactorNamespaceFacades.build_expected_base_chains(
                project_root=project_root,
            )
            if workspace_root is not None
            else None
        )
        for status in facade_statuses:
            if status.exists:
                continue
            suffix = c.Infra.FAMILY_SUFFIXES[status.family]
            class_name = f"{stem}{suffix}"
            file_name = c.Infra.FAMILY_FILES.get(
                status.family, c.Infra.Files.UTILITIES_PY
            ).lstrip("*")
            target_path = package_dir / file_name
            if target_path.exists():
                FlextInfraUtilitiesRefactorNamespaceFacades._patch_existing_facade_file(
                    target_path=target_path,
                    family=status.family,
                    class_name=class_name,
                    base_chains=base_chains,
                )
                continue
            FlextInfraUtilitiesRefactorNamespaceFacades._write_missing_facade_file(
                file_path=target_path,
                family=status.family,
                class_name=class_name,
                base_chains=base_chains,
            )

    @staticmethod
    def _patch_existing_facade_file(
        *,
        target_path: Path,
        family: str,
        class_name: str,
        base_chains: t.StrSequenceMapping | None = None,
    ) -> None:
        content = target_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        mutated = False
        header = f"class {class_name}("
        if header not in content and f"class {class_name}:" not in content:
            base_class = (
                FlextInfraUtilitiesRefactorNamespaceFacades._base_class_for_family(
                    family=family,
                    base_chains=base_chains,
                )
            )
            content = (
                content.rstrip() + f"\n\nclass {class_name}({base_class}):\n    pass\n"
            )
            mutated = True
        alias_line = f"{family} = {class_name}"
        if alias_line not in content:
            content = content.rstrip() + f"\n\n{alias_line}\n"
            mutated = True
        if mutated:
            _ = target_path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)


__all__ = ["FlextInfraUtilitiesRefactorNamespaceFacades"]
