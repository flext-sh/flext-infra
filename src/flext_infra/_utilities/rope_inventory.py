"""Rope-only object inventory helpers for workspace-wide census."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path

from rope.base.exceptions import RopeError
from rope.base.pynames import DefinedName, ImportedName
from rope.base.pynamesdef import AssignedName, ParameterName
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyFunction, PyModule

from flext_infra import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    c,
    m,
    p,
    t,
)


class FlextInfraUtilitiesRopeInventory:
    """Generic Rope-only inventory helpers for Python objects."""

    @classmethod
    def objects(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        module_entry: m.Infra.RopeModuleIndexEntry | None,
        convention: m.Infra.RopeModuleConvention,
        include_local_scopes: bool,
        rope_workspace: object | None = None,
    ) -> tuple[m.Infra.Census.Object, ...]:
        """Return all same-file defined objects for one Rope module."""
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return ()
        except (RecursionError, SyntaxError, ValueError, RopeError):
            return ()
        source = resource.read()
        items: MutableSequence[m.Infra.Census.Object] = []
        module_scope = pymodule.get_scope()
        if not isinstance(module_scope, p.Infra.RopeScopeDsl):
            return ()
        child_scopes = tuple(module_scope.get_scopes())
        for name, pyname in cls._sorted_module_names(pymodule, resource):
            record = cls._record(
                rope_project=rope_project,
                resource=resource,
                source=source,
                name=name,
                pyname=pyname,
                module_name=module_entry.module_name
                if module_entry is not None
                else "",
                project_name=convention.project_layout.project_name
                if convention.project_layout is not None
                else convention.file_path.parent.name,
                convention=convention,
                scope_chain=(),
                class_chain=(),
                child_scope=cls._child_scope_for(child_scopes, pyname),
                rope_workspace=rope_workspace,
            )
            if record is None:
                continue
            items.append(record)
            if include_local_scopes and record.kind in {"class", "function", "method"}:
                child_scope = cls._child_scope_for(child_scopes, pyname)
                if child_scope is not None:
                    items.extend(
                        cls._scope_objects(
                            rope_project=rope_project,
                            resource=resource,
                            source=source,
                            module_name=record.module_name,
                            project_name=record.project,
                            convention=convention,
                            scope=child_scope,
                            scope_chain=tuple(
                                part for part in record.scope_path.split(".") if part
                            ),
                            class_chain=tuple(
                                part for part in record.class_path.split(".") if part
                            ),
                            rope_workspace=rope_workspace,
                        )
                    )
        return tuple(items)

    @classmethod
    def _scope_objects(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        *,
        module_name: str,
        project_name: str,
        convention: m.Infra.RopeModuleConvention,
        scope: p.Infra.RopeScopeDsl,
        scope_chain: tuple[str, ...],
        class_chain: tuple[str, ...],
        rope_workspace: object | None = None,
    ) -> tuple[m.Infra.Census.Object, ...]:
        items: MutableSequence[m.Infra.Census.Object] = []
        child_scopes = tuple(scope.get_scopes())
        for name, pyname in cls._sorted_scope_names(scope, resource):
            child_scope = cls._child_scope_for(child_scopes, pyname)
            record = cls._record(
                rope_project=rope_project,
                resource=resource,
                source=source,
                name=name,
                pyname=pyname,
                module_name=module_name,
                project_name=project_name,
                convention=convention,
                scope_chain=scope_chain,
                class_chain=class_chain,
                child_scope=child_scope,
                rope_workspace=rope_workspace,
            )
            if record is None:
                continue
            items.append(record)
            if (
                record.kind not in {"class", "function", "method"}
                or child_scope is None
            ):
                continue
            next_class_chain = (
                (*class_chain, record.name) if record.kind == "class" else class_chain
            )
            items.extend(
                cls._scope_objects(
                    rope_project=rope_project,
                    resource=resource,
                    source=source,
                    module_name=module_name,
                    project_name=project_name,
                    convention=convention,
                    scope=child_scope,
                    scope_chain=(*scope_chain, record.name),
                    class_chain=next_class_chain,
                    rope_workspace=rope_workspace,
                )
            )
        return tuple(items)

    @staticmethod
    def _sorted_module_names(
        pymodule: PyModule,
        resource: t.Infra.RopeResource,
    ) -> tuple[tuple[str, t.Infra.RopePyName], ...]:
        return tuple(
            sorted(
                (
                    (name, pyname)
                    for name, pyname in pymodule.get_attributes().items()
                    if FlextInfraUtilitiesRopeInventory._definition_line(
                        pyname, resource
                    )
                    is not None
                    and not isinstance(pyname, ImportedName)
                ),
                key=lambda item: (
                    FlextInfraUtilitiesRopeInventory._definition_line(item[1], resource)
                    or 0
                ),
            )
        )

    @staticmethod
    def _sorted_scope_names(
        scope: p.Infra.RopeScopeDsl,
        resource: t.Infra.RopeResource,
    ) -> tuple[tuple[str, t.Infra.RopePyName], ...]:
        return tuple(
            sorted(
                (
                    (name, pyname)
                    for name, pyname in scope.get_names().items()
                    if FlextInfraUtilitiesRopeInventory._definition_line(
                        pyname, resource
                    )
                    is not None
                    and not isinstance(pyname, ImportedName)
                ),
                key=lambda item: (
                    FlextInfraUtilitiesRopeInventory._definition_line(item[1], resource)
                    or 0
                ),
            )
        )

    @classmethod
    def _record(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        *,
        name: str,
        pyname: t.Infra.RopePyName,
        module_name: str,
        project_name: str,
        convention: m.Infra.RopeModuleConvention,
        scope_chain: tuple[str, ...],
        class_chain: tuple[str, ...],
        child_scope: p.Infra.RopeScopeDsl | None,
        rope_workspace: object | None = None,
    ) -> m.Infra.Census.Object | None:
        line = cls._definition_line(pyname, resource)
        if line is None:
            return None
        (
            runtime_reference_sites,
            test_reference_sites,
            example_reference_sites,
            script_reference_sites,
        ) = cls._reference_sites(
            rope_project,
            resource,
            source=source,
            name=name,
            line=line,
            rope_workspace=rope_workspace,
        )
        references_count = sum(
            len(reference_sites)
            for reference_sites in (
                runtime_reference_sites,
                test_reference_sites,
                example_reference_sites,
                script_reference_sites,
            )
        )
        kind = cls._kind_for(
            pyname, class_chain=class_chain, scope_chain=scope_chain, name=name
        )
        if kind == "parameter" and name in {"self", "cls"}:
            return None
        scope_path = ".".join((*scope_chain, name))
        class_path = (
            ".".join((*class_chain, name)) if kind == "class" else ".".join(class_chain)
        )
        return m.Infra.Census.Object(
            name=name,
            kind=kind,
            file_path=str(convention.file_path),
            line=line,
            project=project_name,
            class_path=class_path,
            module_name=module_name,
            scope_path=scope_path,
            actual_tier=cls._actual_tier(convention),
            expected_tier=cls._expected_tier(convention, kind=kind),
            is_facade_member=cls._is_facade_member(
                convention, name=name, scope_chain=scope_chain
            ),
            references_count=references_count,
            runtime_references_count=len(runtime_reference_sites),
            test_references_count=len(test_reference_sites),
            example_references_count=len(example_reference_sites),
            script_references_count=len(script_reference_sites),
            runtime_reference_sites=runtime_reference_sites,
            test_reference_sites=test_reference_sites,
            example_reference_sites=example_reference_sites,
            script_reference_sites=script_reference_sites,
            fingerprint=cls._fingerprint(
                source, name=name, line=line, child_scope=child_scope
            ),
        )

    @staticmethod
    def _definition_line(
        pyname: t.Infra.RopePyName,
        resource: t.Infra.RopeResource,
    ) -> int | None:
        location = pyname.get_definition_location()
        if location is None:
            return None
        module, line = location
        origin = module.get_resource() if module is not None else None
        if line is None or origin is None or origin.path != resource.path:
            return None
        result: int = line
        return result

    @staticmethod
    def _child_scope_for(
        scopes: Sequence[p.Infra.RopeScopeDsl], pyname: t.Infra.RopePyName
    ) -> p.Infra.RopeScopeDsl | None:
        location = pyname.get_definition_location()
        if location is None:
            return None
        _, line = location
        if line is None:
            return None
        scope = next((scope for scope in scopes if scope.get_start() == line), None)
        if scope is not None:
            return scope
        getter = getattr(pyname.get_object(), "get_scope", None)
        candidate = getter() if callable(getter) else None
        return candidate if isinstance(candidate, p.Infra.RopeScopeDsl) else None

    @staticmethod
    def _kind_for(
        pyname: t.Infra.RopePyName,
        *,
        class_chain: tuple[str, ...],
        scope_chain: tuple[str, ...],
        name: str,
    ) -> str:
        obj = pyname.get_object()
        if isinstance(obj, AbstractClass):
            return "class"
        if isinstance(obj, PyFunction):
            return (
                "method"
                if class_chain and len(scope_chain) == len(class_chain)
                else "function"
            )
        if isinstance(pyname, ParameterName):
            return "parameter"
        if class_chain and len(scope_chain) == len(class_chain):
            return "attribute"
        if scope_chain:
            return "local" if not name.isupper() else "constant"
        if isinstance(pyname, (DefinedName, AssignedName)) and name.isupper():
            return "constant"
        return "assignment"

    @staticmethod
    def _reference_sites(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        source: str,
        name: str,
        line: int,
        rope_workspace: object | None = None,
    ) -> tuple[
        tuple[m.Infra.Census.ReferenceSite, ...],
        tuple[m.Infra.Census.ReferenceSite, ...],
        tuple[m.Infra.Census.ReferenceSite, ...],
        tuple[m.Infra.Census.ReferenceSite, ...],
    ]:
        lines = source.splitlines(keepends=True)
        if line < 1 or line > len(lines):
            return ((), (), (), ())
        column = lines[line - 1].find(name)
        if column < 0:
            return ((), (), (), ())
        offset = sum(len(item) for item in lines[: line - 1]) + column
        definition_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            rope_project,
            resource,
        )
        if rope_workspace is not None and definition_path is not None:
            fast_path = (
                FlextInfraUtilitiesRopeInventory._fast_reference_sites_from_index(
                    rope_workspace,
                    name=name,
                    definition_path=definition_path,
                )
            )
            if fast_path is not None:
                return fast_path
        hits = FlextInfraUtilitiesRopeImports.find_occurrences(
            rope_project,
            resource,
            offset,
        )
        runtime_reference_sites: list[m.Infra.Census.ReferenceSite] = []
        test_reference_sites: list[m.Infra.Census.ReferenceSite] = []
        example_reference_sites: list[m.Infra.Census.ReferenceSite] = []
        script_reference_sites: list[m.Infra.Census.ReferenceSite] = []
        seen_sites: set[tuple[str, int, str]] = set()
        skipped_definition = False
        for hit in hits:
            if (
                not skipped_definition
                and FlextInfraUtilitiesRopeInventory._is_definition_occurrence(
                    hit,
                    definition_path=definition_path,
                    line=line,
                    offset=offset,
                )
            ):
                skipped_definition = True
                continue
            reference_site = FlextInfraUtilitiesRopeInventory._reference_site(hit)
            if reference_site is None:
                continue
            if Path(reference_site.file_path).name == c.Infra.INIT_PY:
                continue
            site_key = (
                reference_site.file_path,
                reference_site.line,
                reference_site.surface,
            )
            if site_key in seen_sites:
                continue
            seen_sites.add(site_key)
            if reference_site.surface == c.Infra.DIR_TESTS:
                test_reference_sites.append(reference_site)
                continue
            if reference_site.surface == c.Infra.DIR_EXAMPLES:
                example_reference_sites.append(reference_site)
                continue
            if reference_site.surface == c.Infra.DIR_SCRIPTS:
                script_reference_sites.append(reference_site)
                continue
            runtime_reference_sites.append(reference_site)
        if not skipped_definition and definition_path is not None:
            surface = FlextInfraUtilitiesRopeInventory._reference_surface(
                definition_path
            )
            if surface == c.Infra.DIR_TESTS:
                FlextInfraUtilitiesRopeInventory._discard_definition_site(
                    test_reference_sites,
                    definition_path=definition_path,
                    line=line,
                )
            elif surface == c.Infra.DIR_EXAMPLES:
                FlextInfraUtilitiesRopeInventory._discard_definition_site(
                    example_reference_sites,
                    definition_path=definition_path,
                    line=line,
                )
            elif surface == c.Infra.DIR_SCRIPTS:
                FlextInfraUtilitiesRopeInventory._discard_definition_site(
                    script_reference_sites,
                    definition_path=definition_path,
                    line=line,
                )
            else:
                FlextInfraUtilitiesRopeInventory._discard_definition_site(
                    runtime_reference_sites,
                    definition_path=definition_path,
                    line=line,
                )
        return (
            tuple(runtime_reference_sites),
            tuple(test_reference_sites),
            tuple(example_reference_sites),
            tuple(script_reference_sites),
        )

    @staticmethod
    def _fast_reference_sites_from_index(
        rope_workspace: object,
        *,
        name: str,
        definition_path: Path,
    ) -> (
        tuple[
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
        ]
        | None
    ):
        """Fast-path reference classification from pre-scanned workspace text index.

        Only short-circuits rope when the index shows the symbol has ZERO
        external-file occurrences (truly unused candidate). For any symbol
        with external references the caller falls back to rope's semantic
        ``find_occurrences`` to correctly handle intra-module ``__all__``
        literals, decorator references, and same-name collisions.
        """
        name_index_getter = getattr(rope_workspace, "name_index", None)
        if name_index_getter is None:
            return None
        occurrences = name_index_getter().get(name, ())
        if not occurrences:
            return ((), (), (), ())
        resolved_definition = definition_path.resolve()
        has_external = any(
            path.resolve() != resolved_definition and path.name != c.Infra.INIT_PY
            for path, _surface, _lines in occurrences
        )
        if has_external:
            return None
        return ((), (), (), ())

    @staticmethod
    def _location_file_path(location: t.Infra.RopeLocation) -> Path | None:
        resource = getattr(location, "resource", None)
        real_path = getattr(resource, "real_path", None)
        if isinstance(real_path, str) and real_path:
            return Path(real_path).resolve()
        path = getattr(resource, "path", None)
        if isinstance(path, str) and path:
            return Path(path)
        return None

    @staticmethod
    def _location_line(location: t.Infra.RopeLocation) -> int:
        line = getattr(location, "lineno", None)
        return line if isinstance(line, int) and line >= 0 else 0

    @staticmethod
    def _reference_site(
        location: t.Infra.RopeLocation,
    ) -> m.Infra.Census.ReferenceSite | None:
        file_path = FlextInfraUtilitiesRopeInventory._location_file_path(location)
        if file_path is None:
            return None
        return m.Infra.Census.ReferenceSite(
            file_path=FlextInfraUtilitiesRopeInventory._normalize_file_path(file_path),
            line=FlextInfraUtilitiesRopeInventory._location_line(location),
            surface=FlextInfraUtilitiesRopeInventory._reference_surface(file_path),
        )

    @staticmethod
    def _discard_definition_site(
        sites: list[m.Infra.Census.ReferenceSite],
        *,
        definition_path: Path,
        line: int,
    ) -> None:
        definition_key = (
            FlextInfraUtilitiesRopeInventory._normalize_file_path(definition_path),
            line,
        )
        match_index = next(
            (
                index
                for index, site in enumerate(sites)
                if (site.file_path, site.line) == definition_key
            ),
            None,
        )
        if match_index is not None:
            sites.pop(match_index)

    @staticmethod
    def _normalize_file_path(file_path: Path) -> str:
        return str(file_path.resolve() if file_path.is_absolute() else file_path)

    @staticmethod
    def _is_definition_occurrence(
        location: t.Infra.RopeLocation,
        *,
        definition_path: Path | None,
        line: int,
        offset: int,
    ) -> bool:
        location_path = FlextInfraUtilitiesRopeInventory._location_file_path(location)
        if (
            definition_path is not None
            and location_path is not None
            and location_path != definition_path
        ):
            return False
        location_line = getattr(location, "lineno", None)
        if isinstance(location_line, int) and location_line != line:
            return False
        location_offset = getattr(location, "offset", None)
        if isinstance(location_offset, int):
            return location_offset == offset
        return bool(
            definition_path is not None
            and location_path == definition_path
            and location_line == line
        )

    @staticmethod
    def _reference_surface(file_path: Path | None) -> str:
        default_src: str = c.Infra.DEFAULT_SRC_DIR
        if file_path is None:
            return default_src
        parts = set(file_path.parts)
        tests_dir: str = c.Infra.DIR_TESTS
        if tests_dir in parts:
            return tests_dir
        examples_dir: str = c.Infra.DIR_EXAMPLES
        if examples_dir in parts:
            return examples_dir
        scripts_dir: str = c.Infra.DIR_SCRIPTS
        if scripts_dir in parts:
            return scripts_dir
        return default_src

    @staticmethod
    def _fingerprint(
        source: str,
        *,
        name: str,
        line: int,
        child_scope: p.Infra.RopeScopeDsl | None,
    ) -> str:
        start = max(1, line)
        end = child_scope.get_end() if child_scope is not None else start
        end = end if isinstance(end, int) and end >= start else start
        lines = source.splitlines()
        snippet = "\n".join(lines[start - 1 : end])
        return " ".join(snippet.replace(name, "<name>").split())

    @staticmethod
    def _actual_tier(convention: m.Infra.RopeModuleConvention) -> str:
        policy = convention.module_policy
        expected: str = policy.expected_family or ""
        if expected:
            return expected
        if "services" in convention.relative_path.parts:
            return "Services"
        stem: str = convention.file_path.stem
        return stem

    @staticmethod
    def _expected_tier(convention: m.Infra.RopeModuleConvention, *, kind: str) -> str:
        expected: str = convention.module_policy.expected_family or ""
        if expected:
            return expected
        if kind == "constant":
            constants: str = c.Infra.FAMILY_SUFFIXES.get("c", "Constants")
            return constants
        return FlextInfraUtilitiesRopeInventory._actual_tier(convention)

    @staticmethod
    def _is_facade_member(
        convention: m.Infra.RopeModuleConvention,
        *,
        name: str,
        scope_chain: tuple[str, ...],
    ) -> bool:
        if scope_chain:
            return False
        layout = convention.project_layout
        family = convention.module_policy.expected_family or ""
        alias = convention.module_policy.expected_alias or ""
        if name == alias:
            return True
        return bool(
            layout is not None and family and name == f"{layout.class_stem}{family}"
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeInventory"]
