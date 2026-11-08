"""Retire authored Protocols that a model-derived projection now owns.

The concrete model owns its structural contract. A same-named authored
Protocol elsewhere in the package's protocol family yields to the projected
contract in the same candidate that publishes and composes it. Spans,
consumers and source edits are read and planned through Rope; no list of
packages, protocols or members is kept here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import m, p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)


class FlextInfraUtilitiesModelsProtocolRetirement:
    """Plan the retirement of authored Protocols displaced by their projection."""

    @staticmethod
    def _identifier_offset(
        source: str,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.AnnAssign,
    ) -> int:
        """Locate the declared identifier of one native declaration.

        Returns:
            The source offset of the declaration's bound name.

        Raises:
            ValueError: The declaration has no native source extent.

        """
        target = node.target if isinstance(node, ast.AnnAssign) else node
        span = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_span_offsets(
            source, target
        )
        if span is None:
            message = "retired declaration has no native source extent"
            raise ValueError(message)
        if isinstance(node, ast.AnnAssign):
            return span[0]
        return source.index(node.name, span[0])

    @classmethod
    def _sites(
        cls, project: p.Infra.RopeProject, path: Path, offset: int
    ) -> tuple[tuple[Path, int, int], ...]:
        """Find every native occurrence of the declaration bound at ``offset``.

        Returns:
            Each occurrence's module path, source offset and line.

        Raises:
            ValueError: Rope reports an occurrence without a module resource.

        """
        sites: list[tuple[Path, int, int]] = []
        for location in FlextInfraUtilitiesRopeRuntimeModules.runtime_find_occurrences(
            project,
            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path),
            offset,
            resources=None,
            in_hierarchy=False,
        ):
            if location.resource is None:
                message = f"retired declaration occurrence has no module: {path}"
                raise ValueError(message)
            sites.append((
                Path(location.resource.real_path).resolve(),
                location.offset,
                location.lineno,
            ))
        return tuple(sites)

    @classmethod
    def member_consumers(
        cls,
        project: p.Infra.RopeProject,
        members: Mapping[str, tuple[t.Infra.AstStatement, Path]],
    ) -> tuple[str, ...]:
        """Report every consumer site of authored members the model lacks.

        Returns:
            ``path:line`` for each native use outside the member's declaration.

        Raises:
            TypeError: A member is not a native attribute or callable declaration.

        """
        reported: list[str] = []
        for node, path in members.values():
            if not isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.AnnAssign
            ):
                message = "authored member is not a native declaration"
                raise TypeError(message)
            offset = cls._identifier_offset(project.source_text(path), node)
            reported.extend(
                f"{site}:{line}"
                for site, position, line in cls._sites(project, path, offset)
                if (site, position) != (path.resolve(), offset)
            )
        return tuple(reported)

    @classmethod
    def _retired_declarations(
        cls,
        project: p.Infra.RopeProject,
        protocols: Sequence[p.Infra.RopeSourceClass],
        routes: Sequence[str],
    ) -> tuple[
        list[tuple[Path, int, int]],
        list[tuple[Path, int, p.Infra.RopeSourceClass, str]],
    ]:
        """Read the native source extent and identifier of each retired Protocol.

        Returns:
            The retired source spans and each declaration with its identifier
            offset and projected facade route.

        Raises:
            ValueError: A retired Protocol has no native source or extent.

        """
        spans: list[tuple[Path, int, int]] = []
        declarations: list[tuple[Path, int, p.Infra.RopeSourceClass, str]] = []
        for protocol, route in zip(protocols, routes, strict=True):
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                protocol.get_module()
            )
            resource = module.get_resource()
            node = protocol.get_ast()
            if resource is None or not isinstance(node, ast.ClassDef):
                message = (
                    f"retired Protocol has no native source: {protocol.get_name()}"
                )
                raise ValueError(message)
            path = Path(resource.real_path).resolve()
            source = project.source_text(path)
            span = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_span_offsets(
                source, node
            )
            if span is None:
                message = f"retired Protocol has no source extent: {node.name}"
                raise ValueError(message)
            spans.append((path, *span))
            declarations.append((
                path,
                cls._identifier_offset(source, node),
                protocol,
                route,
            ))
        return spans, declarations

    @classmethod
    def facade_rebinding(
        cls,
        project: p.Infra.RopeProject,
        protocols: Sequence[p.Infra.RopeSourceClass],
        routes: Sequence[str],
        owners: Sequence[p.Infra.RopePyObject],
    ) -> tuple[tuple[str, ...], dict[Path, tuple[p.Infra.SourceRewrite, ...]]]:
        """Plan how every use of a retired Protocol reaches its projected owner.

        A use through the public facade or its namespace already re-binds to
        the projected contract composed in the same candidate. A use inside a
        retired declaration leaves with it. A use that names the retired
        declaration itself, through its authored holder or a bare name, is
        rewritten to the projected facade route. Any other use would point to
        a retired identity.

        Returns:
            ``path:line`` for each use that would lose its declaration, and the
            planned rewrites of every module whose uses move to the facade.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        spans, declarations = cls._retired_declarations(project, protocols, routes)
        blocked: list[str] = []
        rewrites: dict[Path, dict[tuple[int, int], p.Infra.SourceRewrite]] = {}
        for path, offset, protocol, route in declarations:
            for site, position, line in cls._sites(project, path, offset):
                if any(
                    site == retired and start <= position <= end
                    for retired, start, end in spans
                ):
                    continue
                source = project.source_text(site)
                start, end = FlextInfraUtilitiesRopeRuntimeRefactors.word_primary_range(
                    source, position
                )
                expression = source[start:end]
                owner = expression.rpartition(".")[0]
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
                        project, site
                    ),
                )
                scope = runtime.scope_at(module, position)
                binding = runtime.expression_name(scope, owner) if owner else None
                if binding is not None and any(
                    binding.get_object() is facade for facade in owners
                ):
                    continue
                named = runtime.expression_name(scope, expression)
                if named is not None and named.get_object() is protocol:
                    rewrites.setdefault(site, {})[start, end] = m.Infra.SourceRewrite(
                        start=start, end=end, text=route
                    )
                    continue
                blocked.append(f"{site}:{line}")
        return tuple(blocked), {
            site: tuple(planned.values()) for site, planned in rewrites.items()
        }

    @classmethod
    def retired_sources(
        cls,
        project: p.Infra.RopeProject,
        repository_root: Path,
        retirements: Mapping[Path, Sequence[tuple[str, str]]],
        rendered: Mapping[Path, str],
    ) -> dict[Path, str]:
        """Remove retired nested Protocols from their authored holders.

        A module already planned by this candidate is edited in its planned
        form; otherwise its current source is edited. Imports that only the
        retired declarations used leave with them.

        Returns:
            Each repository-relative authored module with its retired source.

        Raises:
            ValueError: A retired holder or declaration has no native extent.

        """
        root = repository_root.resolve()
        updated: dict[Path, str] = {}
        for path, entries in retirements.items():
            relative = path.resolve().relative_to(root)
            original = rendered.get(relative, project.source_text(path))
            resource = FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
                project, path
            )
            tree = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, original, resource=resource
            ).get_ast()
            lines = original.splitlines(keepends=True)
            offsets = [0]
            for line in lines:
                offsets.append(offsets[-1] + len(line))
            rewrites: list[p.Infra.SourceRewrite] = []
            for holder in (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and any(name == node.name for name, _member in entries)
            ):
                retired = [
                    node
                    for node in holder.body
                    if isinstance(node, ast.ClassDef)
                    and (holder.name, node.name) in entries
                ]
                remaining = len(holder.body) - len(retired)
                for index, node in enumerate(retired):
                    if node.end_lineno is None:
                        message = f"retired Protocol has no extent: {path}:{node.name}"
                        raise ValueError(message)
                    first = min(
                        (node, *node.decorator_list), key=lambda item: item.lineno
                    )
                    rewrites.append(
                        m.Infra.SourceRewrite(
                            start=offsets[first.lineno - 1],
                            end=offsets[node.end_lineno],
                            text=f"{' ' * node.col_offset}pass\n"
                            if remaining == 0 and index == 0
                            else "",
                        )
                    )
            changed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                resource=resource, source=original, rewrites=rewrites
            ).new_contents
            updated[relative] = (
                FlextInfraUtilitiesSemanticDeclarationRelocation.remove_orphaned_imports(
                    project, resource, original, changed
                )
            )
        return updated


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolRetirement"]
