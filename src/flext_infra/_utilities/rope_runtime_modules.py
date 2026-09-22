"""Rope project, module and import factory boundary methods."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from flext_infra import p, t

from .rope_runtime_base import FlextInfraUtilitiesRopeRuntimeBase


class FlextInfraUtilitiesRopeRuntimeModules(FlextInfraUtilitiesRopeRuntimeBase):
    """Load Rope project/module/import objects behind protocols."""

    @classmethod
    def snapshot_project(
        cls, project: p.Infra.RopeProject, sources: t.MappingKV[Path, str]
    ) -> p.Infra.RopeProject:
        """Capture a complete identity graph with proposed sources authoritative.

        Unchanged dependencies are captured once before graph construction;
        subsequent imports and MRO resolution only read that closed inventory.
        """
        inventory = {
            Path(resource.real_path).resolve(): resource.read()
            for resource in project.get_python_files()
        }
        for path, source in sources.items():
            resolved = path.resolve()
            if resolved not in inventory:
                msg = f"Rope proposed source is outside its input inventory: {path}"
                raise ValueError(msg)
            inventory[resolved] = source
        owner = cls.runtime_type(
            "flext_infra._utilities._rope.project", "FlextInfraRopeProject"
        )
        factory = getattr(owner, "from_snapshot", None)
        if not callable(factory):
            msg = "Rope project owner does not expose snapshot construction"
            raise TypeError(msg)
        snapshot = factory(
            project.root.real_path,
            inventory,
            [folder.path for folder in project.get_source_folders()],
        )
        if not isinstance(snapshot, p.Infra.RopeProject):
            msg = "Rope snapshot does not satisfy its project contract"
            raise TypeError(msg)
        return snapshot

    @classmethod
    def imported_name_at(
        cls, pymodule: t.Infra.RopePyModule, offset: int
    ) -> p.Infra.RopeImportedName | None:
        """Resolve a lexical binding; local shadows are not imported names."""
        resolver = cls._runtime_callable("rope.base.evaluate", "eval_location")
        result = resolver(pymodule, offset)
        return result if isinstance(result, p.Infra.RopeImportedName) else None

    @staticmethod
    def imported_module_path(
        project: p.Infra.RopeProject, binding: p.Infra.RopeImportedName
    ) -> Path:
        """Resolve import provenance through Rope without evaluating its target.

        Generated initializers may still await publication. Their content is
        not required to identify which module an authored import names.
        """
        imported = binding.imported_module
        resource = imported.resource
        if resource is None:
            name = imported.module_name
            module = imported.importing_module.get_module()
            source = module.get_resource() if module is not None else None
            if name is None or source is None:
                message = (
                    f"import has no declared module location: {binding.imported_name}"
                )
                raise ValueError(message)
            resource = (
                project.find_module(name, source.parent)
                if imported.level == 0
                else project.find_relative_module(name, source.parent, imported.level)
            )
        if resource is None:
            message = f"unresolved imported module: {imported.module_name}"
            raise ValueError(message)
        return Path(resource.real_path).resolve()

    @classmethod
    def new_project(
        cls,
        root: str,
        *,
        ropefolder: str,
        save_objectdb: bool,
        ignored_resources: t.SequenceOf[str],
        source_folders: t.SequenceOf[str],
    ) -> t.Infra.RopeProject:
        project_factory = cls._runtime_callable(
            "flext_infra._utilities._rope.project", "FlextInfraRopeProject"
        )
        # flext-i6nq.10: FLEXT owns writes; disable Rope's leaking Git subprocess.
        fscommands_factory = cls._runtime_callable(
            "rope.base.fscommands", "FileSystemCommands"
        )
        project = project_factory(
            root,
            fscommands=fscommands_factory(),
            ropefolder=ropefolder,
            save_objectdb=save_objectdb,
            save_history=False,
            ignored_resources=list(ignored_resources),
            source_folders=list(source_folders),
        )
        if not isinstance(project, p.Infra.RopeProject):
            msg = "rope Project does not satisfy p.Infra.RopeProject"
            raise TypeError(msg)
        return project

    @classmethod
    def module_imports_for_pymodule(
        cls, rope_project: t.Infra.RopeProject, pymodule: t.Infra.RopePyModule
    ) -> t.Infra.RopeModuleImports:
        loader = cls._runtime_callable(
            "rope.refactor.importutils", "get_module_imports"
        )
        result = loader(rope_project, pymodule)
        if not isinstance(result, p.Infra.RopeModuleImports):
            msg = "rope get_module_imports returned invalid module imports"
            raise TypeError(msg)
        return result

    @classmethod
    def get_string_module(
        cls,
        rope_project: t.Infra.RopeProject,
        source: str,
        *,
        resource: t.Infra.RopeResource | None = None,
    ) -> t.Infra.RopePyModule:
        loader = cls._runtime_callable("rope.base.libutils", "get_string_module")
        pymodule = loader(rope_project, source, resource=resource, force_errors=True)
        if not isinstance(pymodule, p.Infra.RopePyModule):
            msg = "rope get_string_module returned non-PyModule"
            raise TypeError(msg)
        return pymodule

    @classmethod
    def import_organizer(
        cls, rope_project: t.Infra.RopeProject
    ) -> p.Infra.RopeImportOrganizer:
        organizer_factory = cls._runtime_callable(
            "rope.refactor.importutils", "ImportOrganizer"
        )
        organizer = organizer_factory(rope_project)
        if not isinstance(organizer, p.Infra.RopeImportOrganizer):
            msg = "rope ImportOrganizer does not satisfy p.Infra.RopeImportOrganizer"
            raise TypeError(msg)
        return organizer

    @classmethod
    def runtime_find_occurrences(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        resources: t.SequenceOf[t.Infra.RopeResource] | None,
        in_hierarchy: bool,
    ) -> t.SequenceOf[t.Infra.RopeLocation]:
        finder = cls._runtime_callable("rope.contrib.findit", "find_occurrences")
        raw_locations = finder(
            rope_project,
            resource,
            offset,
            resources=resources,
            in_hierarchy=in_hierarchy,
        )
        if not isinstance(raw_locations, Iterable):
            msg = "rope find_occurrences returned non-iterable locations"
            raise TypeError(msg)
        return tuple(
            location
            for location in raw_locations
            if isinstance(location, p.Infra.RopeLocation)
        )

    @classmethod
    def from_import(
        cls,
        module_name: str,
        level: int,
        names_and_aliases: t.SequenceOf[t.Pair[str, str | None]],
    ) -> t.Infra.RopeFromImport:
        from_import_factory = cls._runtime_callable(
            "rope.refactor.importutils.importinfo", "FromImport"
        )
        from_import = from_import_factory(module_name, level, list(names_and_aliases))
        if not isinstance(from_import, p.Infra.RopeFromImport):
            msg = "rope FromImport does not satisfy p.Infra.RopeFromImport"
            raise TypeError(msg)
        return from_import


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModules"]
