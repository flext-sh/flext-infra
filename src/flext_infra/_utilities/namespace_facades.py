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


class FlextInfraUtilitiesRefactorNamespaceFacades:
    """Facade generation and dependency-chain helpers."""

    _base_chains_cache: ClassVar[MutableMapping[Path, t.StrSequenceMapping]] = {}

    @staticmethod
    def _class_name_to_module(class_name: str) -> str:
        """Convert CamelCase class names to snake_case module names."""
        head = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", head).lower()

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
        dep_names = FlextInfraUtilitiesIteration.local_dependency_names_from_payload({
            str(key): value for key, value in payload.items()
        })
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
                    f"from {FlextInfraUtilitiesRefactorNamespaceFacades._class_name_to_module(base)} import {base}"
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
        lines = target_path.read_text(encoding=c.Cli.ENCODING_DEFAULT).splitlines()
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
        mutated = False
        if base_import not in lines:
            insert_idx = 0
            if c.Infra.FUTURE_ANNOTATIONS in lines:
                insert_idx = lines.index(c.Infra.FUTURE_ANNOTATIONS) + 1
                while insert_idx < len(lines) and not lines[insert_idx].strip():
                    insert_idx += 1
            lines.insert(insert_idx, "")
            lines.insert(insert_idx, base_import)
            mutated = True
        class_line_indices = [
            idx for idx, line in enumerate(lines) if re.match(r"^class\s+\w+", line)
        ]
        current_names: t.Infra.StrSet = set()
        for idx in class_line_indices:
            match = re.match(r"^class\s+(?P<name>\w+)", lines[idx])
            if match is not None:
                current_names.add(match.group("name"))
        if class_line_indices:
            if class_name not in current_names and len(class_line_indices) == 1:
                lines[class_line_indices[0]] = canonical_header
                mutated = True
            elif class_name in current_names:
                for idx in class_line_indices:
                    if re.match(rf"^class\s+{re.escape(class_name)}\b", lines[idx]):
                        if lines[idx] != canonical_header:
                            lines[idx] = canonical_header
                            mutated = True
                        break
            else:
                lines.extend(["", canonical_header, "    pass"])
                mutated = True
        else:
            lines.extend(["", canonical_header, "    pass"])
            mutated = True
        alias_line = f"{family} = {class_name}"
        alias_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if re.match(rf"^{re.escape(family)}\s*=", line)
            ),
            -1,
        )
        if alias_index < 0:
            lines.extend(["", alias_line])
            mutated = True
        elif lines[alias_index] != alias_line:
            lines[alias_index] = alias_line
            mutated = True
        all_line = f'__all__: list[str] = ["{class_name}", "{family}"]'
        all_index = next(
            (idx for idx, line in enumerate(lines) if re.match(r"^__all__\s*:", line)),
            -1,
        )
        if all_index < 0:
            lines.extend(["", all_line])
            mutated = True
        elif lines[all_index] != all_line:
            lines[all_index] = all_line
            mutated = True
        if mutated:
            _ = target_path.write_text(
                "\n".join(lines).rstrip() + "\n",
                encoding=c.Cli.ENCODING_DEFAULT,
            )


__all__: list[str] = ["FlextInfraUtilitiesRefactorNamespaceFacades"]
