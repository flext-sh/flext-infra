"""Facade and dependency-chain helpers for namespace refactors."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import (
    MutableMapping,
    Sequence,
)
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesIteration,
    c,
    m,
    t,
)
from flext_infra._utilities.namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra._utilities.rope_module_patch import (
    FlextInfraUtilitiesRopeModulePatch,
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
        pyproject_path = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return {}
        try:
            raw = pyproject_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        except OSError:
            return {}
        payload = u.Cli.toml_mapping_from_text(raw)
        if payload is None:
            return {}
        dep_names = FlextInfraUtilitiesIteration.local_dependency_names_from_payload(
            dict(payload.items())
        )
        chains: t.MutableStrSequenceMapping = defaultdict(list)
        for dep_name in dep_names:
            if dep_name == c.Infra.PKG_CORE or not dep_name.startswith(
                c.Infra.PKG_PREFIX_HYPHEN
            ):
                continue
            stem = u.derive_class_stem(dep_name)
            for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
                chains[family].append(f"{stem}{suffix}")
        return chains

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
                    f"from {FlextInfraUtilitiesRefactorNamespaceCommon.class_name_to_module(base)} import {base}"
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
            f"{family} = {class_name}\n\n"
            f'__all__: list[str] = ["{class_name}", "{family}"]\n'
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _ = file_path.write_text(content, encoding=c.Cli.ENCODING_DEFAULT)

    @staticmethod
    def ensure_missing_facades(
        *,
        project_root: Path,
        project_name: str,
        facade_statuses: Sequence[m.Infra.FacadeStatus],
        workspace_root: Path | None = None,
    ) -> None:
        del project_name
        src_dir = project_root / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / c.Infra.INIT_PY).is_file()
        ]
        layout = FlextInfraUtilitiesCodegenNamespace.layout(project_root)
        if layout is None:
            return
        package_dir = (
            layout.package_dir if layout.package_dir.is_dir() else package_dirs[0]
        )
        stem = layout.class_stem
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
                status.family, c.Infra.UTILITIES_PY
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
        source = target_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        lines = source.splitlines()
        base_class = FlextInfraUtilitiesRefactorNamespaceFacades._base_class_for_family(
            family=family,
            base_chains=base_chains,
        )
        base_import = (
            FlextInfraUtilitiesRefactorNamespaceFacades._base_import_for_family(
                family=family,
                base_chains=base_chains,
            )
        )
        canonical_header = f"class {class_name}({base_class}):"
        if base_import not in lines:
            lines = list(
                FlextInfraUtilitiesRefactorNamespaceCommon.insert_import_lines(
                    lines=lines,
                    imports=[base_import, ""],
                )
            )
        class_line_indices = [
            idx for idx, line in enumerate(lines) if re.match(r"^class\s+\w+", line)
        ]
        existing_class_index = next(
            (
                idx
                for idx in class_line_indices
                if re.match(rf"^class\s+{re.escape(class_name)}\b", lines[idx])
            ),
            -1,
        )
        if existing_class_index >= 0:
            if lines[existing_class_index] != canonical_header:
                lines[existing_class_index] = canonical_header
        elif len(class_line_indices) == 1:
            if lines[class_line_indices[0]] != canonical_header:
                lines[class_line_indices[0]] = canonical_header
        else:
            lines.extend(["", canonical_header, "    pass"])
        updated_source = "\n".join(lines).rstrip() + "\n"
        updated_source = FlextInfraUtilitiesRopeModulePatch.ensure_runtime_alias(
            updated_source,
            alias=family,
            target_name=class_name,
        )
        all_line = f'__all__: list[str] = ["{class_name}", "{family}"]'
        if all_line not in updated_source:
            updated_lines = updated_source.splitlines()
            all_index = next(
                (
                    idx
                    for idx, line in enumerate(updated_lines)
                    if re.match(r"^__all__\s*:", line)
                ),
                -1,
            )
            if all_index < 0:
                updated_lines.extend(["", all_line])
            else:
                updated_lines[all_index] = all_line
            updated_source = "\n".join(updated_lines).rstrip() + "\n"
        if updated_source != source:
            _ = target_path.write_text(
                updated_source,
                encoding=c.Cli.ENCODING_DEFAULT,
            )


__all__: list[str] = ["FlextInfraUtilitiesRefactorNamespaceFacades"]
