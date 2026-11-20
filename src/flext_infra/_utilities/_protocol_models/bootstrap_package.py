"""Plan, normalize and install one declared package's bootstrap protocol sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ast
import importlib
from pathlib import Path

from flext_cli import u

from flext_infra import c, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
from flext_infra.protocols_bootstrap import (
    normalize_protocol_source,
    plan_protocol_facades,
)

if TYPE_CHECKING:
    from flext_infra._utilities.protocol_models import (
        FlextInfraUtilitiesModelsProtocol,
    )


class FlextInfraUtilitiesModelsProtocolBootstrapPackage:
    """Own one declared package's prepared and installed bootstrap sources."""

    @classmethod
    def _bootstrap_package_sources(
        cls: "FlextInfraUtilitiesModelsProtocol",
        root: Path,
        project: p.Infra.RopeProject,
        *,
        package_name: str,
        namespace_package: bool,
    ) -> p.Result[t.Infra.BootstrapProtocolPackage | None]:
        """Plan and normalize one package's bootstrap sources without publishing.

        A declared namespace package owning models receives its first protocol
        sources even before its ``_protocols`` directory exists; the primary
        package opts in by declaring that directory.

        Returns:
            The package's planned, normalized sources, or ``None`` when it
            declares no protocol projection.

        """
        projection = cls._ModelProtocolProjection(
            root, project, package_name=package_name
        )
        layout = projection.source_layout()
        if layout is None:
            return r[t.Infra.BootstrapProtocolPackage | None].ok(None)
        package, _stem, package_name = layout
        protocol_root = package / "_protocols"
        protocols_declared = project.source_query(protocol_root, "isdir")
        if not namespace_package and not protocols_declared:
            return r[t.Infra.BootstrapProtocolPackage | None].ok(None)
        originals = {
            directory / name: project.source_state(directory / name)
            for directory, _children, files in (
                project.source_walk(protocol_root) if protocols_declared else ()
            )
            for name in files
            if name.endswith(c.Infra.EXT_PYTHON)
        }
        normalized = {
            path: normalize_protocol_source(
                project.source_text(path),
                package_name=package_name,
                filename=str(path),
            )
            for path in originals
        }
        declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            root, (), normalized, source_project=project
        )
        with project.source_view(
            declared_files=declared, additional_source_folders=None
        ):
            planned = cls.protocol_model_sources_from_source(
                root, project, package_name=package_name
            )
        if planned.failure:
            return r[
                t.Infra.BootstrapProtocolPackage | None
            ].from_failure(planned)
        updates = {
            **normalized,
            **{root / path: text for path, text in planned.value.items()},
        }
        for path in updates:
            if path not in originals:
                originals[path] = project.source_state(path, required=False)
        inputs = dict(originals)
        for directory, _children, files in project.source_walk(package / "_models"):
            for name in files:
                if name.endswith(c.Infra.EXT_PYTHON):
                    path = directory / name
                    inputs[path] = project.source_state(path)
        manifest = root / c.PYPROJECT_FILENAME
        for path in (
            manifest,
            package / "models.py",
            Path(__file__).resolve().parent.parent / "protocol_models.py",
        ):
            inputs[path] = project.source_state(path)
        members = [
            (
                cls._ModelProtocolProjection.module_name_for(relative),
                holder.name,
                tuple(
                    node.name for node in holder.body if isinstance(node, ast.ClassDef)
                ),
            )
            for relative, text in planned.value.items()
            for holder in ast.parse(text).body
            if isinstance(holder, ast.ClassDef)
        ]

        return r[t.Infra.BootstrapProtocolPackage | None].ok(
            (package, planned.value, updates, originals, inputs, members)
        )

    @classmethod
    def _publish_bootstrap_protocol_facades(
        cls: "FlextInfraUtilitiesModelsProtocol",
        repository_root: Path,
        _members: list[tuple[str, str, tuple[str, ...]]],
    ) -> p.Result[bool]:
        """Materialize the canonical facade plan in the staged source candidate.

        Returns:
            Whether composing the candidate changed a facade source.

        The public generation transaction owns the later guarded publication.
        This nested source-preview callback only materializes its admitted
        candidate so its validation sees the canonical facade MRO.

        """
        changed = False
        for path, raw_source in plan_protocol_facades(repository_root).items():
            source = raw_source
            if source.startswith("# AUTO-GENERATED FILE"):
                source = c.Infra.AUTOGEN_HEADER + "\n" + source.partition("\n")[2]
            if not path.is_file() or path.read_text(encoding="utf-8") != source:
                path.write_text(source, encoding="utf-8")
                changed = True
        return r.ok(value=changed)

    @staticmethod
    def _install_bootstrap_facade_members(
        members: list[tuple[str, str, tuple[str, ...]]], repository_root: Path
    ) -> None:
        """Bind published protocol members on the already-loaded public facade.

        This is the live equivalent of lazy facade export wiring. It is confined
        to the invocation that published the source contracts; ordinary codegen
        regenerates the durable facade projection immediately afterwards.
        """
        package = repository_root / "src"
        package_name = next(
            path.name for path in package.iterdir() if (path / "protocols.py").is_file()
        )
        facade_module = importlib.import_module(f"{package_name}.protocols")
        package_stem = u.derive_class_stem(package_name.replace("_", "-"))
        family = package_stem.removeprefix("Flext")
        # flext-core is the root facade: source contracts belong on ``p`` itself,
        # not on a synthetic ``p.Core`` namespace.
        facade = (
            facade_module.p
            if package_name == "flext_core"
            else getattr(facade_module.p, family, None)
        )
        holder_prefix = f"{package_stem}Protocols"
        if not isinstance(facade, type):
            return
        for module_name, holder_name, names in members:
            if not module_name.startswith(
                f"{package_name}._protocols."
            ) or not holder_name.startswith(holder_prefix):
                continue
            module = importlib.import_module(module_name)
            holder = vars(module).get(holder_name)
            if not isinstance(holder, type) or holder.__module__ != module_name:
                continue
            for name in names:
                member = vars(holder).get(name)
                if isinstance(member, type):
                    setattr(facade, name, member)


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolBootstrapPackage"]
