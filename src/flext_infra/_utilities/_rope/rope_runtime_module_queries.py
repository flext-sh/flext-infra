"""Rope project, module and import factory boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import config, m, p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeBase,
    FlextInfraUtilitiesTypesRopeRuntime,
)


class FlextInfraUtilitiesRopeRuntimeModuleQueries(FlextInfraUtilitiesRopeRuntimeBase):
    """Authenticate native suppliers and construct Rope source snapshots."""

    @staticmethod
    def definition_location(
        binding: t.Infra.RopePyName,
    ) -> tuple[t.Infra.RopeParsedModule | None, int | None]:
        """Read native definition metadata, including annotation-only bindings.

        Returns:
            The original supplier and first assignment's logical declaration line.

        Raises:
            TypeError: The native annotation is not an expression node.

        """
        module, line = binding.get_definition_location()
        if (
            line is not None
            or not FlextInfraUtilitiesTypesRopeRuntime.source_module(module)
            or not FlextInfraUtilitiesTypesRopeRuntime.assigned_name(binding)
            or not binding.assignments
        ):
            return module, line
        assignment = binding.assignments[0]
        annotation = assignment.type_hint
        if assignment.ast_node is not None or annotation is None:
            return module, line
        if not isinstance(annotation, ast.expr):
            message = "native Rope assignment annotation is not an expression"
            raise TypeError(message)
        return module, module.logical_lines.logical_line_in(annotation.lineno)[0]

    @staticmethod
    def concrete_data_class(candidate: p.Infra.RopePyObject | None) -> bool:
        """Distinguish a native concrete data constraint from a class constraint.

        Returns:
            Whether native class metadata excludes universal and metaclass types.

        """
        if not (
            FlextInfraUtilitiesTypesRopeRuntime.abstract_class(candidate)
            and isinstance(candidate, p.Infra.RopeBuiltinClass)
        ):
            return False
        native = candidate.builtin
        # A metaclass or its universal ancestor can describe class objects.
        return (
            isinstance(native, type)
            and type(native) is type
            and not issubclass(native, type)
            and not issubclass(type, native)
        )

    @staticmethod
    def source_import_binding(
        binding: p.Infra.RopePyName,
    ) -> p.Infra.RopePyName | None:
        """Follow native imported names to their declaring source binding.

        Returns:
            The declared binding, or None for an unresolved or cyclic import.

        """
        imported: set[int] = set()
        while isinstance(binding, p.Infra.RopeImportedName):
            if id(binding) in imported:
                return None
            imported.add(id(binding))
            supplier = (
                binding.imported_module
                .get_object()
                .get_attributes()
                .get(binding.imported_name)
            )
            if supplier is None:
                return None
            binding = supplier
        return binding

    @staticmethod
    def imported_module_resource(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopeImportedName,
    ) -> p.Infra.RopeResource:
        """Resolve a declared import through its native Rope resource identity.

        Returns:
            The exact file or package resource declared by the import.

        Raises:
            ValueError: If the declared import has no resolvable source resource.

        """
        imported = binding.imported_module
        resource = imported.resource
        if resource is None:
            name = imported.module_name
            module = imported.importing_module.get_module()
            source = module.get_resource()
            if source is None or (name is None and imported.level == 0):
                message = (
                    f"import has no declared module location: {binding.imported_name}"
                )
                raise ValueError(message)
            if imported.level == 0 and name is not None:
                resource = project.find_module(name, source.parent)
            else:
                resource = project.find_relative_module(
                    name if name is not None else "", source.parent, imported.level
                )
        if resource is None:
            message = f"unresolved imported module: {imported.module_name}"
            raise ValueError(message)
        return resource

    @staticmethod
    def source_offset(source: str, node: p.Infra.RopeAstNode) -> int:
        """Resolve Rope AST byte coordinates to a Python source offset.

        Returns:
            The source offset.

        Raises:
            TypeError: If the native AST node has no source position.
            ValueError: If the node line is outside its source.

        """
        line = getattr(node, "lineno", None)
        column = getattr(node, "col_offset", None)
        lines = source.splitlines(keepends=True)
        if not isinstance(line, int) or not isinstance(column, int):
            msg = "Rope AST node has no source position"
            raise TypeError(msg)
        if line < 1 or line > len(lines):
            msg = f"Rope AST node line is outside its source: {line}"
            raise ValueError(msg)
        encoded_prefix = lines[line - 1].encode("utf-8")[:column]
        prefix = encoded_prefix.decode("utf-8")
        return sum(map(len, lines[: line - 1])) + len(prefix)

    @classmethod
    def new_project(
        cls,
        root: str,
        *,
        ropefolder: str,
        save_objectdb: bool,
        filter_lists: tuple[Sequence[str], Sequence[str]],
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
    def project_core(project: p.Infra.RopeProject) -> t.Infra.RopeNativeCore:
        """Admit the original untyped SDK result at the native boundary.

        Returns:
            The native core retained by the project.

        """
        return u.type_adapter(
            t.TypeForm(t.Port[t.Infra.RopeNativeCore])
        ).validate_python(project.get_pycore(), strict=True)

    @classmethod
    def extension_module_names(cls, project: p.Infra.RopeProject) -> t.StrTuple:
        """Read native extension names through their validated structural boundary.

        Returns:
            The exact elected extension names in deterministic order.

        """
        core = cls.project_core(project)
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
        names_and_aliases: Sequence[tuple[str, str | None]],
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
        names_and_aliases: Sequence[tuple[str, str | None]],
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
        if not FlextInfraUtilitiesTypesRopeRuntime.abstract_class(wrapped):
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
        sources: Mapping[Path, str],
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
        observations: tuple[m.Cli.AtomicFileState, ...] | None = None,
        additional_source_folders: tuple[str, ...] = (),
    ) -> p.Infra.RopeProject:
        """Open the overlay owner with captured reads and declared file effects.

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
            observations=observations,
            additional_source_folders=additional_source_folders,
        )
        if not isinstance(snapshot, p.Infra.RopeProject):
            msg = "Rope snapshot does not satisfy its project contract"
            raise TypeError(msg)
        return snapshot


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeModuleQueries"]
