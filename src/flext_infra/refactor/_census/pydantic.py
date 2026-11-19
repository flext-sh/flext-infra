"""Pydantic census rows mounted over the existing authenticated inventory.

The part classifies facts its owners already computed: the census object
inventory, native Rope class bases, the live preset facade, the existing
duplicate payload groups and the canonical model projector. It adds no second
inventory, parse or projection route.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, u


class FlextInfraRefactorCensusPydantic:
    """Assemble the typed Pydantic section of the workspace census report."""

    @classmethod
    def pydantic_census(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        objects: Sequence[p.Infra.Object],
        duplicates: Sequence[p.Infra.DuplicateGroup],
    ) -> m.Infra.PydanticCensus:
        """Build the Pydantic census from the shared inventory.

        Returns:
            The complete Pydantic section.

        """
        presets = u.Infra.preset_names()
        bases = {path: u.Infra.class_bases(workspace, path) for path in sorted(sources)}
        classes = tuple(item for item in objects if item.kind == "class")
        models = tuple(
            m.Infra.PydanticModelCensus(
                package=cls._package(Path(item.file_path)),
                name=item.name,
                file_path=Path(item.file_path),
                line=item.line,
                base=base,
                preset=base if base in presets else "",
                raw=base == c.Infra.PYDANTIC_RAW_MODEL_NAME,
                generated=cls._generated(sources.get(Path(item.file_path), "")),
            )
            for item in classes
            if (base := bases.get(Path(item.file_path), {}).get(item.name, ""))
            and (base.endswith(c.Infra.PYDANTIC_MODEL_SUFFIX) or base in presets)
        )
        model_names = {model.name for model in models}
        return m.Infra.PydanticCensus(
            models=models,
            enums=tuple(
                m.Infra.PydanticEnumCensus(
                    package=cls._package(Path(item.file_path)),
                    name=item.name,
                    tier=item.actual_tier,
                    file_path=Path(item.file_path),
                    line=item.line,
                    generated=cls._generated(sources.get(Path(item.file_path), "")),
                )
                for item in classes
                if bases.get(Path(item.file_path), {}).get(item.name)
                == c.Infra.PYDANTIC_STR_ENUM_NAME
            ),
            literals=tuple(
                m.Infra.PydanticLiteralCensus(
                    package=cls._package(path),
                    owner=owner,
                    values=values,
                    kind=kind,
                    file_path=path,
                    line=line,
                    generated=cls._generated(sources[path]),
                )
                for path in sorted(sources)
                for owner, values, kind, line in u.Infra.literals(workspace, path)
            ),
            parity=cls._parity(workspace),
            duplicate_models=tuple(
                m.Infra.PydanticDuplicateModelCensus(
                    fingerprint=group.definitions[0].payload_fingerprint,
                    models=tuple(
                        f"{definition.project}.{Path(definition.file_path).stem}."
                        f"{definition.name}"
                        for definition in group.definitions
                    ),
                )
                for group in duplicates
                if group.definitions
                and group.definitions[0].kind == "class"
                and all(
                    definition.name in model_names for definition in group.definitions
                )
            ),
        )

    @staticmethod
    def _parity(
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> tuple[m.Infra.PydanticParityCensus, ...]:
        """Compare shipped protocol projections with their canonical render.

        Returns:
            One row per missing or drifted projection file.

        Raises:
            ValueError: If the canonical projector refuses the source.

        """
        root = workspace.repository_root
        rows: list[m.Infra.PydanticParityCensus] = []
        packages = u.Infra.protocol_model_package_names(root, workspace.rope_project)
        for package in packages:
            rendered = u.Infra.protocol_model_sources_from_source(
                root, workspace.rope_project, package_name=package
            )
            if rendered.failure:
                raise ValueError(rendered.error)
            for relative, expected in rendered.value.items():
                path = root / relative
                actual = (
                    path.read_text(encoding=c.DEFAULT_ENCODING)
                    if path.is_file()
                    else None
                )
                if actual != expected:
                    rows.append(
                        m.Infra.PydanticParityCensus(
                            package=package,
                            kind="projection-drift"
                            if actual is not None
                            else "missing-protocol",
                            protocol=path.stem,
                            file_path=path,
                            line=1,
                            detail="canonical projection differs from disk",
                        )
                    )
        return tuple(rows)

    @staticmethod
    def _generated(source: str) -> bool:
        """Whether the source is a generated projection.

        Returns:
            ``True`` for generated content.

        """
        return source.lstrip().startswith(c.Infra.AUTOGEN_HEADER)

    @staticmethod
    def _package(path: Path) -> str:
        """Resolve the owning package from the source layout.

        Returns:
            The package directory after ``src``, or an empty string.

        """
        parts = path.parts
        return parts[parts.index("src") + 1] if "src" in parts else ""


__all__: list[str] = ["FlextInfraRefactorCensusPydantic"]
