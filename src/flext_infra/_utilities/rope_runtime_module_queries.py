"""Rope project, module and import factory boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import sysconfig
from importlib.machinery import BuiltinImporter, FrozenImporter, ModuleSpec, PathFinder
from inspect import getsourcefile
from pathlib import Path

from flext_cli import u
from typing_extensions import TypeForm

from flext_infra import config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeBase,
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesRopeRuntimeModuleQueries(FlextInfraUtilitiesRopeRuntimeBase):
    """Authenticate native suppliers and construct Rope source snapshots."""

    @classmethod
    def new_project(
        cls,
        root: str,
        *,
        ropefolder: str,
        save_objectdb: bool,
        filter_lists: t.Pair[t.SequenceOf[str], t.SequenceOf[str]],
    ) -> t.Infra.RopeProject:
        """Create one Rope project.

        ``filter_lists`` carries the Rope filter sequences in order:
        ignored resources, source folders. The project itself declares the
        interpreter's sourceless stdlib modules.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        Raises:
            TypeError: If Rope project does not satisfy its project contract.

        """
        ignored_resources, source_folders = filter_lists
        project_factory = cls.runtime_callable(
            "flext_infra._utilities._rope.project",
            "FlextInfraRopeProject",
        )
        # FLEXT owns writes; disable Rope's leaking Git subprocess.
        fscommands_factory = cls.runtime_callable(
            "rope.base.fscommands",
            "FileSystemCommands",
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

    @staticmethod
    def extension_module_names(project: p.Infra.RopeProject) -> t.StrTuple:
        """Read native extension names through their validated structural boundary.

        Returns:
            The exact elected extension names in deterministic order.

        """
        core = u.type_adapter(
            TypeForm(t.InstanceOf[p.Infra.RopePyCore])
        ).validate_python(project.get_pycore(), strict=True)
        return tuple(
            sorted(
                u.type_adapter(set[str]).validate_python(
                    core.extension_modules, strict=True
                )
            )
        )

    @staticmethod
    def native_election(project: p.Infra.RopeProject) -> p.Infra.RopeProjectElection:
        """Capture the installed native resolver's elected source identities.

        Returns:
            The original source, extension and interpreter search election.

        """
        return m.Infra.RopeProjectElection(
            source_folders=tuple(
                folder.path for folder in project.get_source_folders()
            ),
            ignored_resources=tuple(sorted(config.Infra.codegen.source_scan_ignored)),
            extension_modules=FlextInfraUtilitiesRopeRuntimeModuleQueries.extension_module_names(
                project
            ),
            python_path_folders=tuple(
                folder.real_path
                for folder in project.get_python_path_folders()
                if folder.is_folder()
            ),
        )

    @classmethod
    def from_import(
        cls,
        module_name: str,
        level: int,
        names_and_aliases: t.SequenceOf[t.Pair[str, str | None]],
    ) -> t.Infra.RopeFromImport:
        """Build the native relative or absolute from-import record.

        Returns:
            The native import record for the supplied module and bindings.

        Raises:
            TypeError: If the native factory does not satisfy its import protocol.

        """
        from_import_factory = cls.runtime_callable(
            "rope.refactor.importutils.importinfo",
            "FromImport",
        )
        from_import = from_import_factory(module_name, level, list(names_and_aliases))
        if not isinstance(from_import, p.Infra.RopeFromImport):
            msg = "rope FromImport does not satisfy p.Infra.RopeFromImport"
            raise TypeError(msg)
        return from_import

    @classmethod
    def normal_import(
        cls,
        names_and_aliases: t.SequenceOf[t.Pair[str, str | None]],
    ) -> t.Infra.RopeNormalImport:
        """Build Rope's native plain ``import`` record.

        Returns:
            The native ``NormalImport`` for the given names.

        Raises:
            TypeError: If Rope's record does not satisfy its protocol.

        """
        normal_import = cls.runtime_callable(
            "rope.refactor.importutils.importinfo",
            "NormalImport",
        )(list(names_and_aliases))
        if not isinstance(normal_import, p.Infra.RopeNormalImport):
            msg = "rope NormalImport does not satisfy p.Infra.RopeNormalImport"
            raise TypeError(msg)
        return normal_import

    @classmethod
    def import_statement(
        cls,
        import_info: p.Infra.RopeImportInfo,
        start_line: int,
        end_line: int,
        source: str,
    ) -> p.Infra.RopeImportStatement:
        """Construct a native statement from an authenticated Rope AST span.

        Returns:
            The native import statement with its original source coordinates.

        Raises:
            TypeError: If Rope returns a record outside its statement contract.

        """
        statement = cls.runtime_callable(
            "rope.refactor.importutils.importinfo", "ImportStatement"
        )(import_info, start_line, end_line, source)
        if not isinstance(statement, p.Infra.RopeImportStatement):
            msg = "rope ImportStatement does not satisfy p.Infra.RopeImportStatement"
            raise TypeError(msg)
        return statement

    @classmethod
    def native_module_source(cls, module_name: str) -> p.Result[Path]:
        """Authenticate native module election without calling an upper service.

        Returns:
            The physical supplier source, or the authenticated native interpreter.

        """
        module = sys.modules[module_name]
        native = module.__spec__
        if (
            native is None
            or sys.modules.get(native.name) is not module
            or (
                native.name != module_name
                and (
                    native.origin not in {"built-in", "frozen"}
                    or module_name.partition(".")[0] not in sys.stdlib_module_names
                )
            )
        ):
            return r[Path].fail(f"producer module lacks its native spec: {module_name}")
        elected = cls._native_elected_spec(module_name, native)
        if elected.failure:
            return r[Path].from_failure(elected)
        spec = elected.value
        if (
            spec.origin != native.origin
            or type(spec.loader) is not type(native.loader)
            or module.__loader__ is not native.loader
        ):
            return r[Path].fail(
                f"producer module election differs from loaded spec: {module_name}; "
                f"loaded_origin={native.origin!r}; "
                f"cold_origin={spec.origin!r}; "
                f"loaded_loader={type(native.loader).__module__}."
                f"{type(native.loader).__qualname__}; "
                f"cold_loader={type(spec.loader).__module__}."
                f"{type(spec.loader).__qualname__}"
            )
        if spec.origin == "frozen" and (
            (
                native.loader is not spec.loader
                or native.loader_state.origname != spec.loader_state.origname
            )
            or any(
                observed is not None and observed != expected
                for observed, expected in (
                    (native.loader_state.filename, spec.loader_state.filename),
                    (spec.loader_state.filename, getsourcefile(module)),
                )
            )
        ):
            return r[Path].fail(
                f"producer frozen declaration source differs from native loader: "
                f"{module_name}; loaded_state={native.loader_state!r}; "
                f"cold_state={spec.loader_state!r}; source={getsourcefile(module)!r}"
            )
        if spec.origin is None or (
            spec.origin not in {"built-in", "frozen"}
            and getattr(module, "__file__", None) != spec.origin
        ):
            return r[Path].fail(
                f"producer loaded module differs from cold origin: {module_name}"
            )
        return r[Path].ok(
            Path(sys.executable).resolve()
            if spec.origin in {"built-in", "frozen"}
            else Path(spec.origin).absolute()
        )

    @classmethod
    def _native_elected_spec(
        cls,
        module_name: str,
        native: ModuleSpec,
    ) -> p.Result[ModuleSpec]:
        """Compare registered importers with the complete physical module election.

        Returns:
            The elected leaf spec, or the first physical/importer discrepancy.

        """
        elected = cls._native_root_spec(module_name, native)
        if elected.failure or native.origin in {"built-in", "frozen"}:
            return elected
        spec: ModuleSpec | None = elected.value
        components = module_name.split(".")
        parent_path = None
        for index in range(1, len(components)):
            if spec is None or not spec.submodule_search_locations:
                return r[ModuleSpec].fail(
                    f"producer module has no cold parent: {module_name}"
                )
            parent_path = spec.submodule_search_locations
            spec = PathFinder.find_spec(".".join(components[: index + 1]), parent_path)
        registered = cls.runtime_callable("importlib._bootstrap", "_find_spec")(
            module_name, parent_path
        )
        if (
            not isinstance(registered, ModuleSpec)
            or spec is None
            or registered.origin != spec.origin
            or registered.submodule_search_locations != spec.submodule_search_locations
        ):
            return r[ModuleSpec].fail(
                f"registered producer importer disagrees with physical election: "
                f"{module_name}"
            )
        return r[ModuleSpec].ok(registered)

    @staticmethod
    def _native_root_spec(
        module_name: str,
        native: ModuleSpec,
    ) -> p.Result[ModuleSpec]:
        """Elect the native root using the interpreter's physical search paths.

        Returns:
            The elected root spec, or the original physical authority failure.

        """
        namespace = module_name.partition(".")[0]
        search: list[str] | None = None
        if namespace in sys.stdlib_module_names:
            base = Path(sys.base_prefix).resolve()
            standard = Path(
                sysconfig.get_path(
                    "stdlib",
                    vars={"base": sys.base_prefix, "platbase": sys.base_exec_prefix},
                )
            ).resolve()
            extension = sysconfig.get_config_var("DESTSHARED")
            if not isinstance(extension, str):
                return r[ModuleSpec].fail(
                    "producer Python base lacks its native extension directory"
                )
            extension_root = Path(extension).resolve()
            if any(
                not path.is_relative_to(base)
                for path in (Path(sys.executable).resolve(), standard, extension_root)
            ):
                return r[ModuleSpec].fail(
                    "producer standard library differs from native Python base"
                )
            physical = u.Cli.atomic_plan_directory_chain(standard)
            if physical.failure:
                return r[ModuleSpec].from_failure(physical)
            search = [str(standard), str(extension_root)]
        if native.origin == "built-in":
            spec = BuiltinImporter.find_spec(native.name)
        elif native.origin == "frozen":
            spec = FrozenImporter.find_spec(native.name)
        else:
            spec = PathFinder.find_spec(namespace, search)
        if spec is None:
            return r[ModuleSpec].fail(
                f"producer module has no cold root: {module_name}"
            )
        return r[ModuleSpec].ok(spec)

    @classmethod
    def native_class(
        cls,
        native: p.Infra.NativeClassMetadata,
    ) -> t.Infra.RopePyObject:
        """Wrap an observed native class without requiring a module export.

        Returns:
            Rope's class object retaining the exact native identity.

        Raises:
            TypeError: If the input is not a class or Rope changes its identity.

        """
        if not isinstance(native, type):
            msg = "Rope native class input is not a class"
            raise TypeError(msg)
        wrapped = cls.runtime_callable("rope.base.builtins", "BuiltinClass")(
            native,
            {},
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(wrapped):
            msg = "Rope native class factory did not return a class"
            raise TypeError(msg)
        if (
            not isinstance(wrapped, p.Infra.RopeBuiltinClass)
            or wrapped.builtin is not native
        ):
            msg = "Rope native class factory did not preserve native identity"
            raise TypeError(msg)
        return wrapped

    @classmethod
    def native_class_primary_base(
        cls,
        native: p.Infra.NativeClassMetadata,
    ) -> t.Infra.RopePyObject:
        """Resolve the native type descriptor, not an inherited class member.

        Returns:
            Rope's wrapper retaining the observed primary base identity.

        Raises:
            TypeError: If the primary base is None rather than a class.

        """
        base = native.__base__
        if base is None:
            msg = "Rope native primary base is not a class"
            raise TypeError(msg)
        return cls.native_class(base)

    @classmethod
    def parse_rope_module(cls, source: str, *, filename: str) -> t.Infra.RopeAstNode:
        """Parse one source snapshot through Rope's canonical syntax boundary.

        Returns:
            The resulting ``t.Infra.RopeAstNode``.

        Raises:
            TypeError: If rope parser returned an invalid module node.

        """
        parsed = cls.runtime_callable("rope.base.ast", "parse")(
            source,
            filename=filename,
        )
        if not isinstance(parsed, p.Infra.RopeAstNode):
            msg = "rope parser returned an invalid module node"
            raise TypeError(msg)
        return parsed

    @classmethod
    def snapshot_project(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Infra.RopeProject:
        """Open a Rope view of the live tree with proposed sources overlaid.

        ``sources`` are authoritative; ``declared_files`` contribute only the
        paths ``sources`` does not name.

        Returns:
            The overlaid project; the caller owns closing it.

        Raises:
            ValueError: If a proposed source escapes the project.

        """
        root = Path(project.root.real_path).resolve()
        declared = {plan.path.resolve(): plan for plan in declared_files}
        for path, source in sources.items():
            resolved = path.resolve()
            content = source.encode("utf-8")
            declared.pop(resolved, None)
            before = project.source_state(resolved, required=False)
            if before.content == content:
                continue
            if not resolved.is_relative_to(root):
                msg = f"Rope proposed source is outside its project: {path}"
                raise ValueError(msg)
            declared[resolved] = m.Infra.CodegenFilePlan(
                project=root,
                path=resolved,
                before=before,
                desired_content=content,
                desired_mode=(
                    before.mode
                    if before.mode is not None
                    else config.Infra.codegen.modes.file_default
                ),
            )
        return cls.planned_project(
            project,
            election=cls.native_election(project),
            declared_files=tuple(declared.values()),
        )

    @classmethod
    def planned_project(
        cls,
        live: p.Infra.RopeProject,
        *,
        election: p.Infra.RopeProjectElection,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
        additional_source_folders: tuple[str, ...] = (),
    ) -> p.Infra.RopeProject:
        """Open the overlay project owner over ``live`` with planned file effects.

        Returns:
            The overlaid project admitted at its project contract; the caller
            owns closing it.

        Raises:
            TypeError: If the Rope project owner violates its contract.

        """
        owner = cls.runtime_type(
            "flext_infra._utilities._rope.project",
            "FlextInfraRopeProject",
        )
        factory = getattr(owner, "from_atomic_reads", None)
        if not callable(factory):
            msg = "Rope project owner does not expose overlay construction"
            raise TypeError(msg)
        snapshot = factory(
            live,
            election=election,
            declared_files=declared_files,
            additional_source_folders=additional_source_folders,
        )
        if not isinstance(snapshot, p.Infra.RopeProject):
            msg = "Rope snapshot does not satisfy its project contract"
            raise TypeError(msg)
        return snapshot


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModuleQueries"]
