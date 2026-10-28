"""Per-identity authentication of operator-decided lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, p, u
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraReadonlyNamespace:
    """Authenticate exempt findings from source and native Rope identity.

    Identities are derived from the reported findings, never from a hand
    registry; nothing is exempt by rule name or by file. Ruff remains the
    diagnostic authority.
    """

    @classmethod
    def exempt_identities(
        cls,
        project_dir: Path,
        findings: Sequence[p.Infra.Issue],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> frozenset[tuple[tuple[Path, int, int], str]]:
        """Authenticate the findings an operator-decided exemption names.

        The publication policy is authenticated per identity from source,
        never by name or file:

        - ``non-pep695-type-alias`` ("Exceção UP040 por identidade"): a PEP 613
          facade class publication, authenticated by the facade owner;

        Returns:
            ``((path, row, column), rule)`` for each authenticated finding.

        """
        alias_rule = c.Infra.RUFF_NON_PEP695_TYPE_ALIAS
        rows: MutableMapping[str, MutableMapping[Path, set[int]]] = {
            alias_rule: {},
        }
        naming_rule = "invalid-function-name"
        if not any(finding.code in {alias_rule, naming_rule} for finding in findings):
            return frozenset()
        for finding in findings:
            if finding.code in rows:
                rows[finding.code].setdefault(Path(finding.file).resolve(), set()).add(
                    finding.line
                )
        exempt: set[tuple[tuple[Path, int, int], str]] = set()
        # N802 on a protocol property mirrors a published settings branch
        # field (ADR-005: ``settings.<Namespace>.*`` carries the namespace's
        # capitalized name); the structural contract must repeat that exact
        # spelling, authenticated against the member's settings model.
        with u.Infra.facade_source_project(
            project_dir, source_project=source_project
        ) as (project, sources):
            if rows[alias_rule]:
                exempt.update(
                    (identity, alias_rule)
                    for identity in u.Infra.facade_class_publications(
                        project_dir,
                        {
                            path: frozenset(lines)
                            for path, lines in rows[alias_rule].items()
                        },
                        source_project=project,
                    )
                )
            exempt.update(
                (identity, naming_rule)
                for identity in cls._settings_branch_properties(
                    project, tuple(sources), findings
                )
            )
        return frozenset(exempt)

    @staticmethod
    def _settings_branch_properties(
        source_project: p.Infra.RopeProject,
        source_files: Sequence[Path],
        findings: Sequence[p.Infra.Issue],
    ) -> tuple[tuple[Path, int, int], ...]:
        """Authenticate capitalized protocol properties against settings fields.

        Returns:
            The findings whose flagged name is a field on the member's
            settings model, proven from native source.

        Raises:
            TypeError: If Protocol property requires a native source module.

        """
        selected = tuple(
            finding for finding in findings if finding.code == "invalid-function-name"
        )
        if not selected:
            return ()
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol = (
            source_project
            .get_module("typing")
            .get_attributes()["Protocol"]
            .get_object()
        )
        modules: dict[Path, p.Infra.RopeSourceModule] = {}
        wanted: dict[str, list[tuple[Path, int, int]]] = {}
        for finding in selected:
            path = Path(finding.file).resolve()
            if path not in modules:
                module = source_project.get_pymodule(
                    runtime.file_resource_at(source_project, path), force_errors=True
                )
                if not runtime.source_module(module):
                    msg = f"Protocol property requires a native source module: {path}"
                    raise TypeError(msg)
                modules[path] = module
            name = FlextInfraReadonlyNamespace._protocol_property(
                modules[path], finding.line, finding.column, protocol
            )
            if name is None:
                continue
            wanted.setdefault(name, []).append((
                path,
                finding.line,
                finding.column,
            ))
        if not wanted:
            return ()
        names = u.Infra.settings_branch_fields(
            source_project, source_files, frozenset(wanted)
        )
        return tuple(identity for name in names for identity in wanted[name])

    @staticmethod
    def _protocol_property(
        module: p.Infra.RopeSourceModule,
        line: int,
        column: int,
        protocol: p.Infra.RopePyObject,
    ) -> str | None:
        """Authenticate the reported own declaration and its native decorator.

        Returns:
            The resulting ``str | None``.

        Raises:
            TypeError: If Protocol property requires the native word finder contract.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        offset = module.lines.get_line_start(line) + column - 1
        scope = module.get_scope().get_inner_scope_for_offset(offset)
        function = scope.pyobject
        owner = scope.parent
        if (
            scope.get_kind() != "Function"
            or scope.get_start() != line
            or not runtime.py_function(function)
            or owner is None
            or owner.get_kind() != "Class"
            or function.get_scope().parent is None
            or function.get_scope().parent.pyobject is not owner.pyobject
        ):
            return None
        finder = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(finder, p.Infra.RopeWorder):
            msg = "Protocol property requires the native word finder contract"
            raise TypeError(msg)
        name = function.get_name()
        if finder.get_word_at(offset) != name:
            return None
        binding = owner.get_defined_names().get(name)
        if binding is None or binding.get_object() is not function:
            return None
        pending = [owner.pyobject]
        visited: set[int] = set()
        while pending:
            ancestor = pending.pop()
            if ancestor is protocol:
                break
            if id(ancestor) in visited:
                continue
            visited.add(id(ancestor))
            if runtime.abstract_class(ancestor):
                pending.extend(ancestor.get_superclasses())
        else:
            return None
        start = scope.get_region()[0]
        end = module.lines.get_line_start(scope.get_start())
        decorators = runtime.semantic_regions(
            module,
            "${own_property}",
            arguments={"own_property": "name=__builtin__.property"},
            start=start,
            end=end,
        )
        index = module.get_source_binding_index()
        fragments = tuple(
            fragment
            for fragment in index.fragments
            if start <= fragment.start < fragment.end <= end
            and index.context_at(fragment.start).role == "decorator"
        )
        shallowest = min((fragment.depth for fragment in fragments), default=None)
        if any(
            (fragment.start, fragment.end) in decorators
            and fragment.depth == shallowest
            for fragment in fragments
        ):
            return name
        return None


__all__ = ["FlextInfraReadonlyNamespace"]
