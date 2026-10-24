"""Settings/config import rebinding through identity-proven lazy exports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesSemanticDeclarationRelocationExports:
    """Bind layer-0 imports to external public exports by lazy-export identity."""

    @classmethod
    def _declaration_import_rewrites(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[
        t.MutableMappingKV[Path, str],
        t.VariadicTuple[m.Infra.DeclarationRelocationFinding],
    ]:
        """Rebind declarations only to identity-proven external public exports.

        An own-namespace provider has to relocate; importing its defining leaf
        does not repair the dependency. Unresolved identities remain typed red
        findings while the other safe semantic edits can proceed.

        Returns:
            Proposed sources and every dependency lacking a permitted owner.

        """
        layers = FlextInfraUtilitiesImportLaw
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        proposed = dict(sources)
        findings: list[m.Infra.DeclarationRelocationFinding] = []
        for path, source in sources.items():
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            located = layers.import_namespace(root, path)
            if located is None:
                continue
            namespace, module = located
            if layers.import_module_role(module) != "layer0":
                continue
            exports = cls._collect_settings_exports(
                (
                    project,
                    path,
                    source,
                    namespace,
                    runtime,
                    root,
                    sources,
                ),
                findings,
            )
            if exports:
                proposed[path] = cls._relocate_settings_exports(
                    project,
                    path,
                    source,
                    exports,
                )
        return proposed, tuple(findings)

    @classmethod
    def _collect_settings_exports(
        cls,
        context: tuple[
            p.Infra.RopeProject,
            Path,
            str,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
        findings: list[m.Infra.DeclarationRelocationFinding],
    ) -> t.MutableMappingKV[str, t.Pair[str, str]]:
        project, path, _source, namespace, runtime, root, sources = context
        exports: t.MutableMappingKV[str, t.Pair[str, str]] = {}
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(path.relative_to(root).as_posix()),
        )
        for statement in runtime.module_imports_for_pymodule(project, module).imports:
            information = statement.import_info
            if not isinstance(information, p.Infra.RopeFromImport) or information.level:
                continue
            module_name = information.module_name
            if module_name.split(".")[0] != namespace.name:
                continue
            for name, _alias in information.names_and_aliases:
                if name == "*":
                    continue
                alias_context = (
                    project,
                    module_name,
                    name,
                    namespace,
                    runtime,
                    root,
                    sources,
                )
                resolved = cls._resolve_settings_export(alias_context)
                if resolved is not None:
                    exports[resolved[0]] = resolved[1]
                else:
                    findings.append(
                        m.Infra.DeclarationRelocationFinding(
                            file_path=path,
                            declaration=f"{module_name}.{name}",
                            expected_owner="external public declaration",
                            reason=(
                                "own-namespace dependency has no "
                                "identity-proven external export"
                            ),
                        )
                    )
        return exports

    @classmethod
    def _resolve_settings_export(
        cls,
        context: tuple[
            p.Infra.RopeProject,
            str,
            str,
            Path,
            type[FlextInfraUtilitiesRopeRuntimeModules],
            Path,
            t.MappingKV[Path, str],
        ],
    ) -> t.Pair[str, t.Pair[str, str]] | None:
        project, module_name, name, namespace, runtime, root, sources = context
        binding = cls._resolve_binding(project, module_name, name, root, sources)
        if binding is None:
            return None
        owner = binding.get_definition_location()[0]
        resource = owner.get_resource() if owner is not None else None
        if resource is None:
            return None
        target = Path(resource.real_path).resolve()
        if target.is_relative_to(namespace):
            return None
        destination = project.get_pymodule(resource)
        destination_name = destination.get_name().split(".")[0]
        declared = cls._resolve_binding(project, destination_name, name, root, sources)
        if (
            declared is None
            or not runtime.same_name(binding, declared)
            or destination_name == module_name
        ):
            return None
        return (
            f"{module_name}.{name}",
            (destination_name, name),
        )

    @classmethod
    def _relocate_settings_exports(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        exports: t.MappingKV[str, t.Pair[str, str]],
    ) -> str:
        """Rebind native import records while retaining their lexical aliases.

        Returns:
            The rewritten source text with rebound import records.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        imports = runtime.module_imports_for_pymodule(
            project,
            FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource),
        )
        rewrites: list[m.Infra.SourceRewrite] = []
        lines = cls._source_lines(source)
        for statement in imports.imports:
            information = statement.import_info
            if not isinstance(information, p.Infra.RopeFromImport):
                continue
            grouped: t.MutableMappingKV[str, list[t.Pair[str, str | None]]] = {}
            changed = False
            for name, alias in information.names_and_aliases:
                destination = exports.get(f"{information.module_name}.{name}")
                bound_alias = alias
                if destination is None:
                    destination = (information.module_name, name)
                else:
                    changed = True
                    bound_alias = alias or (name if destination[1] != name else None)
                grouped.setdefault(destination[0], []).append((
                    destination[1],
                    bound_alias,
                ))
            if not changed:
                continue
            start = lines.get_line_start(statement.start_line)
            end = min(lines.get_line_start(statement.end_line), len(source))
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=start,
                    end=end,
                    text="\n".join(
                        runtime.from_import(
                            module, information.level, tuple(names)
                        ).get_import_statement()
                        for module, names in grouped.items()
                    )
                    + "\n",
                ),
            )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            tuple(rewrites),
        ).new_contents

    @staticmethod
    def _source_lines(source: str) -> p.Infra.RopeSourceLines:
        lines = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.base.codeanalyze",
            "SourceLinesAdapter",
        )(source)
        if not isinstance(lines, p.Infra.RopeSourceLines):
            msg = "declaration-relocation: missing native source lines"
            raise TypeError(msg)
        return lines

    @staticmethod
    def _provider_file(
        provider_resource: p.Infra.RopeResource,
    ) -> t.Pair[Path, t.Infra.RopeFile]:
        """Resolve a provider resource to its physical module file.

        A package resolves to its initializer.

        Returns:
            The provider module path and its file resource.

        Raises:
            TypeError: If a folder resource is not a Rope root.

        """
        provider_path = Path(provider_resource.real_path).resolve()
        file_resource: p.Infra.RopeResource = provider_resource
        if provider_resource.is_folder():
            if not isinstance(provider_resource, p.Infra.RopeRoot):
                msg = f"declaration-relocation: invalid folder resource {provider_path}"
                raise TypeError(msg)
            file_resource = provider_resource.get_child(c.Infra.INIT_PY)
            provider_path /= c.Infra.INIT_PY
        return provider_path, FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            file_resource,
            provider_path,
        )

    @classmethod
    def _resolve_binding(
        cls,
        project: p.Infra.RopeProject,
        module_name: str,
        alias_name: str,
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> p.Infra.RopePyName | None:
        provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
            project.get_module(module_name)
        )
        visited: set[str] = set()
        while True:
            provider_resource = provider.get_resource()
            if provider_resource is None:
                break
            provider_name = provider.get_name()
            if provider_name in visited:
                msg = f"declaration-relocation: cyclic lazy export {provider_name}"
                raise ValueError(msg)
            visited.add(provider_name)
            provider_path, provider_file = cls._provider_file(provider_resource)
            source = (
                sources[provider_path]
                if provider_path.is_relative_to(root) and provider_path in sources
                else provider_file.read()
            )
            aliases = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                provider_name,
                provider_path,
                source,
                project=project,
                pymodule=provider,
            )
            route = aliases.get(alias_name)
            if route is None:
                break
            provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module(route)
            )
        return provider.get_attributes().get(alias_name)


__all__: list[str] = ["FlextInfraUtilitiesSemanticDeclarationRelocationExports"]
