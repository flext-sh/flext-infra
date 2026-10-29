"""Structural protocols for the external Rope runtime boundary.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence, Set as AbstractSet
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, ClassVar, Literal, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_core import p

    from flext_infra import m, t


@runtime_checkable
class FlextInfraProtocolsRopeRuntime(Protocol):
    """Rope object contracts used instead of importing untyped Rope classes."""

    @runtime_checkable
    class RopeProjectFiles(Protocol):
        """Filesystem observations consumed by native project construction."""

        def realpath(self, path: str) -> str: ...

        def exists(self, path: str) -> bool: ...

        def isfile(self, path: str) -> bool: ...

        def isdir(self, path: str) -> bool: ...

        def listdir(self, path: str) -> list[str]: ...

        def read(self, path: str) -> bytes: ...

    @runtime_checkable
    class RopeResourceOwner(Protocol):
        """External resource election used by the native project initializer."""

        def get_resource(
            self, name: str, /
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource: ...

    @runtime_checkable
    class RopeChangeObserver(Protocol):
        """Native resource notifications used by source candidate transitions."""

        def resource_changed(
            self, resource: FlextInfraProtocolsRopeRuntime.RopeResource
        ) -> None: ...

        def resource_created(
            self, resource: FlextInfraProtocolsRopeRuntime.RopeResource
        ) -> None: ...

        def resource_removed(
            self, resource: FlextInfraProtocolsRopeRuntime.RopeResource
        ) -> None: ...

    @runtime_checkable
    class RopeResourceObserver(Protocol):
        """Native observer registration without claiming a semantic payload read."""

        def add_resource(
            self, resource: FlextInfraProtocolsRopeRuntime.RopeResource
        ) -> None: ...

    @runtime_checkable
    class RopeProjectInitializer(Protocol):
        """Native initialization with its documented nullable state folder."""

        def __call__(
            self,
            project: t.Infra.RopeNativeProject,
            projectroot: str,
            *,
            fscommands: FlextInfraProtocolsRopeRuntime.RopeProjectFiles | None,
            ropefolder: str | None,
            external_project: FlextInfraProtocolsRopeRuntime.RopeResourceOwner | None,
            **prefs: bool | Sequence[str],
        ) -> None: ...

    @runtime_checkable
    class RopeProjectElection(Protocol):
        """Readonly native import roots and source-selection policy."""

        @property
        def source_folders(self) -> t.StrTuple: ...

        @property
        def ignored_resources(self) -> t.StrTuple: ...

        @property
        def extension_modules(self) -> t.StrTuple: ...

        @property
        def python_path_folders(self) -> t.StrTuple: ...

    @runtime_checkable
    class RopeResource(Protocol):
        """Rope project resource shape shared by files and folders."""

        def is_folder(self) -> bool: ...

        def exists(self) -> bool: ...

        @property
        def name(self) -> str: ...

        @property
        def path(self) -> str: ...

        @property
        def real_path(self) -> str: ...

        @property
        def parent(self) -> FlextInfraProtocolsRopeRuntime.RopeRoot: ...

    @runtime_checkable
    class RopeRoot(RopeResource, Protocol):
        """Folder resource with the SDK's child lookup contract."""

        def get_children(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeResource]: ...

        def get_child(
            self,
            name: str,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource: ...

        def has_child(self, name: str) -> bool: ...

    @runtime_checkable
    class RopeFile(RopeResource, Protocol):
        """Rope file resource with content access."""

        def read(self) -> str: ...

        def write(self, contents: str) -> None: ...

    @runtime_checkable
    class RopePyObject(Protocol):
        """Attributes, module identity and type provided by every native object."""

        def get_attribute(
            self,
            name: str,
        ) -> FlextInfraProtocolsRopeRuntime.RopePyName: ...

        def get_attributes(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_module(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeSemanticModule | None: ...

        def get_type(self) -> FlextInfraProtocolsRopeRuntime.RopePyObject: ...

    @runtime_checkable
    class RopeNamedObject(RopePyObject, Protocol):
        """Names and documentation owned by native classes, functions and modules."""

        def get_doc(self) -> str | None: ...

        def get_name(self) -> str: ...

    @runtime_checkable
    class RopeClassObject(RopeNamedObject, Protocol):
        """Superclass queries supplied by native abstract classes."""

        def get_mro(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopePyObject]: ...

        def get_superclasses(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopePyObject]: ...

    @runtime_checkable
    class RopeScopedObject(RopeNamedObject, Protocol):
        """Source-defined object retained by a native lexical scope."""

        def get_scope(self) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

        def get_module(self) -> FlextInfraProtocolsRopeRuntime.RopePyModule: ...

    @runtime_checkable
    class RopeSourceDefinition(Protocol):
        """Cached AST capability of native source-defined classes and functions."""

        def get_ast(self) -> FlextInfraProtocolsRopeRuntime.RopeAstNode: ...

    @runtime_checkable
    class RopeSourceObject(RopeScopedObject, RopeSourceDefinition, Protocol):
        """The source and scope capabilities of native Python definitions."""

    @runtime_checkable
    class RopeSourceClass(RopeSourceObject, RopeClassObject, Protocol):
        """A source-defined class retaining its native superclass graph."""

    @runtime_checkable
    class RopeSourceFunction(RopeSourceObject, Protocol):
        """A source-defined function retaining its native callable role."""

        def get_kind(self) -> str: ...

        def get_param_names(self, *, special_args: bool = True) -> Sequence[str]: ...

        def get_parameter_layout(self) -> tuple[tuple[str, str], ...]: ...

        def get_parameter_defaults(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopeAstNode]: ...

        def get_parameters(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

    @runtime_checkable
    class NativeClassMetadata(Protocol):
        """CPython class metadata published by Rope's builtin class object."""

        __module__: str
        __qualname__: str

        @property
        def __base__(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.NativeClassMetadata | None: ...

        @property
        def __bases__(
            self,
        ) -> tuple[FlextInfraProtocolsRopeRuntime.NativeClassMetadata, ...]: ...

    @runtime_checkable
    class RopeRuntimeSequence(Protocol):
        """Inspectable SDK tuple/list elements before boundary validation."""

        def __len__(self) -> int: ...

        def __getitem__(self, index: int, /) -> p.AttributeProbe: ...

        def __iter__(self) -> Iterator[p.AttributeProbe]: ...

    @runtime_checkable
    class RopeBuiltinClass(Protocol):
        """Rope's exact native class identity, not an inferred instance type."""

        builtin: FlextInfraProtocolsRopeRuntime.NativeClassMetadata

    @runtime_checkable
    class RopeAstNode(Protocol):
        """Raw AST node shape from ``RopePyModule.get_ast()``.

        Minimal contract for Python ``ast.AST`` nodes as exposed by Rope.
        Consumers access attributes via ``getattr``/``hasattr``; the protocol
        declares the common fields that appear across all node types.
        """

        _fields: ClassVar[tuple[str, ...]]

    @runtime_checkable
    class RopeSourceLines(Protocol):
        """Native source line text and character offsets used by refactors."""

        def get_line(self, lineno: int) -> str: ...

        def get_line_start(self, lineno: int) -> int: ...

        def get_line_end(self, lineno: int) -> int: ...

        def get_line_number(self, offset: int) -> int: ...

    @runtime_checkable
    class RopeLogicalLineFinder(Protocol):
        """Native logical-line regions produced by Rope's source analyzer."""

        def generate_regions(
            self,
            start_line: int = 1,
            end_line: int | None = None,
        ) -> Iterator[tuple[int, int]]: ...

    @runtime_checkable
    class RopeCachedLogicalLineFinder(Protocol):
        """Native cached lookup of the logical statement containing a line."""

        def logical_line_in(self, line_number: int) -> tuple[int, int]: ...

    @runtime_checkable
    class RopeAssignment(Protocol):
        """Rope assignment shape."""

        ast_node: FlextInfraProtocolsRopeRuntime.RopeAstNode | None
        type_hint: FlextInfraProtocolsRopeRuntime.RopeAstNode | None

        def get_lineno(self) -> int | None: ...

    @runtime_checkable
    class RopePyName(Protocol):
        """Rope semantic name shape."""

        def get_object(self) -> FlextInfraProtocolsRopeRuntime.RopePyObject: ...

        def get_definition_location(
            self,
        ) -> tuple[
            FlextInfraProtocolsRopeRuntime.RopeParsedModule | None, int | None
        ]: ...

    @runtime_checkable
    class RopeAssignedName(RopePyName, Protocol):
        """Rope assigned-name marker shape."""

        assignments: Sequence[FlextInfraProtocolsRopeRuntime.RopeAssignment]

    @runtime_checkable
    class RopeImportedModule(RopePyName, Protocol):
        """Declared import provenance, before its module is evaluated."""

        importing_module: FlextInfraProtocolsRopeRuntime.RopeSourceModule
        module_name: str | None
        level: int
        resource: FlextInfraProtocolsRopeRuntime.RopeResource | None

    @runtime_checkable
    class RopeImportedName(RopePyName, Protocol):
        """Import binding with its declaring module and original symbol."""

        imported_module: FlextInfraProtocolsRopeRuntime.RopeImportedModule
        imported_name: str

    @runtime_checkable
    class SourceConclusions(Protocol):
        """Native inferred facts, separate from retained parsed source modules."""

        def forget_all_data(self) -> None: ...

    @runtime_checkable
    class RopePyCore(Protocol):
        """Native graph owner retaining the original project of scopes and sources."""

        @property
        def project(self) -> FlextInfraProtocolsRopeRuntime.RopeProject: ...

        @property
        def extension_modules(self) -> AbstractSet[str]: ...

        @property
        def module_cache(self) -> FlextInfraProtocolsRopeRuntime.SourceConclusions: ...

    @runtime_checkable
    class RopeScope(Protocol):
        """Rope semantic scope shape."""

        @property
        def parent(self) -> FlextInfraProtocolsRopeRuntime.RopeScope | None: ...

        def get_scopes(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeScope]: ...

        def get_names(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_defined_names(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_kind(self) -> str | None: ...

        def get_start(self) -> int: ...

        def get_body_start(self) -> int: ...

        def get_end(self) -> int: ...

        def get_region(self) -> tuple[int, int]: ...

        def lookup(
            self, name: str
        ) -> FlextInfraProtocolsRopeRuntime.RopePyName | None: ...

        @property
        def pyobject(self) -> FlextInfraProtocolsRopeRuntime.RopeSourceObject: ...

        @property
        def pycore(self) -> FlextInfraProtocolsRopeRuntime.RopePyCore: ...

    @runtime_checkable
    class RopeModuleScope(RopeScope, Protocol):
        """Lexical lookup owned by the global scope of a parsed source module."""

        def get_inner_scope_for_line(
            self, lineno: int
        ) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

        def get_inner_scope_for_offset(
            self, offset: int
        ) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

    @runtime_checkable
    class RopeSourceBindingContext(Protocol):
        """Native binding environment recorded for one source position."""

        @property
        def environment(self) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

        @property
        def structural_scope(self) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

        @property
        def role(self) -> str: ...

    @runtime_checkable
    class RopeScopeNameFinder(Protocol):
        """Native lexical lookup through the source-binding index."""

        def get_pyname_at(
            self, offset: int
        ) -> FlextInfraProtocolsRopeRuntime.RopePyName | None: ...

    @runtime_checkable
    class RopeSourceFragment(Protocol):
        """Native cached source region, without exposing syntax nodes."""

        start: int
        end: int
        depth: int
        context: FlextInfraProtocolsRopeRuntime.RopeSourceBindingContext

    @runtime_checkable
    class RopeSourceDeclarationLines(Protocol):
        """Exact character regions elected by Rope for its opaque source nodes."""

        def __getitem__(
            self, node: FlextInfraProtocolsRopeRuntime.RopeAstNode
        ) -> tuple[int, int] | tuple[None, None]: ...

    @runtime_checkable
    class RopeSourceBindingIndex(Protocol):
        """Native source binding index, including PEP 695 type parameters."""

        def absolute_import_roots(self) -> frozenset[str]: ...

        def assignment_string_sequence(
            self,
            name: str,
            scope: FlextInfraProtocolsRopeRuntime.RopeScope | None = None,
            *,
            class_metadata: bool = False,
        ) -> tuple[str, ...] | None: ...

        def context_at(
            self, offset: int
        ) -> FlextInfraProtocolsRopeRuntime.RopeSourceBindingContext: ...

        @property
        def lines(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeSourceDeclarationLines: ...

        @property
        def fragments(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeSourceFragment]: ...

    @runtime_checkable
    class RopeSourceMemberResolver(Protocol):
        """Member lookup and class ordering bound to one captured source view."""

        def __call__(
            self, qualified: str | m.Infra.SourceClassReference, /
        ) -> FlextInfraProtocolsRopeRuntime.RopePyName: ...

        def class_order(
            self, declarations: Sequence[m.Infra.SourceClassReference]
        ) -> t.StrTuple: ...

        def class_reaches(
            self,
            declarations: Sequence[m.Infra.SourceClassReference],
            anchors: Sequence[m.Infra.SourceClassReference],
        ) -> tuple[frozenset[str], ...]: ...

        def class_defers_annotations(
            self, qualified: m.Infra.SourceClassReference
        ) -> bool: ...

    @runtime_checkable
    class RopeSemanticModule(RopeNamedObject, Protocol):
        """Module attributes shared by native builtins, packages, and source."""

        def get_resource(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource | None: ...

    @runtime_checkable
    class RopeParsedModule(RopeSemanticModule, Protocol):
        """AST and scope exposed by native Python modules and packages."""

        def get_module(self) -> FlextInfraProtocolsRopeRuntime.RopeParsedModule: ...

        # NOTE (multi-agent, flext-f8vk / kimi): rope returns None for
        # string-parsed modules (pycore.get_string_module(resource=None));
        # the widened contract keeps every consumer None guard live.
        def get_resource(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource | None: ...

        def get_ast(self) -> FlextInfraProtocolsRopeRuntime.RopeAstNode: ...

        def get_scope(self) -> FlextInfraProtocolsRopeRuntime.RopeModuleScope: ...

    @runtime_checkable
    class RopePyModule(RopeParsedModule, Protocol):
        """Native source text, including modules parsed from a string."""

        source_code: str

        @property
        def lines(self) -> FlextInfraProtocolsRopeRuntime.RopeSourceLines: ...

        @property
        def logical_lines(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeCachedLogicalLineFinder: ...

        def get_module(self) -> FlextInfraProtocolsRopeRuntime.RopePyModule: ...

        def get_resource(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeFile | None: ...

        def get_source_binding_index(
            self,
        ) -> FlextInfraProtocolsRopeRuntime.RopeSourceBindingIndex: ...

        @property
        def pycore(self) -> FlextInfraProtocolsRopeRuntime.RopePyCore: ...

    @runtime_checkable
    class RopeSourceModule(RopePyModule, Protocol):
        """Source-module capability retaining its native semantic graph."""

        def get_module(self) -> FlextInfraProtocolsRopeRuntime.RopeSourceModule: ...

        @property
        def pycore(self) -> FlextInfraProtocolsRopeRuntime.RopePyCore: ...

    @runtime_checkable
    class RopeModuleFinder(Protocol):
        """Native relative module lookup shared by every Rope project flavour."""

        def find_relative_module(
            self,
            modname: str,
            folder: FlextInfraProtocolsRopeRuntime.RopeRoot,
            level: int,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource | None: ...

    @runtime_checkable
    class RopePreferences(Protocol):
        """Native preference updates required by project source election."""

        def add(self, key: str, value: str) -> None: ...

    @runtime_checkable
    class RopeSourceAccess(Protocol):
        """Source reads through the project's overlaid filesystem view."""

        @property
        def source_plans(self) -> tuple[m.Infra.CodegenFilePlan, ...]: ...

        def source_view(
            self,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = (),
            additional_source_folders: tuple[str, ...] | None = (),
        ) -> AbstractContextManager[Self]: ...

        def source_state(
            self, path: Path, *, required: bool = True
        ) -> m.Cli.AtomicFileState: ...

        def source_query(
            self, path: Path, predicate: Literal["exists", "isfile", "isdir"]
        ) -> bool: ...

        def source_children(self, path: Path) -> tuple[Path, ...]: ...

        def source_text(self, path: Path) -> str: ...

        def source_bytes(self, path: Path) -> bytes: ...

        def source_walk(
            self,
            path: Path,
        ) -> Iterator[tuple[Path, list[str], list[str]]]: ...

    @runtime_checkable
    class RopeProject(RopeModuleFinder, RopeSourceAccess, Protocol):
        """Compose native project lifecycle with authenticated source access."""

        @property
        def root(self) -> FlextInfraProtocolsRopeRuntime.RopeRoot: ...

        @property
        def fscommands(self) -> FlextInfraProtocolsRopeRuntime.RopeProjectFiles: ...

        def get_resource(
            self,
            resource_name: str,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource: ...

        def get_file(
            self,
            path: str,
        ) -> FlextInfraProtocolsRopeRuntime.RopeFile: ...

        def get_folder(
            self,
            path: str,
        ) -> FlextInfraProtocolsRopeRuntime.RopeRoot: ...

        def get_pymodule(
            self,
            resource: t.Infra.RopeNativeResource
            | FlextInfraProtocolsRopeRuntime.RopeResource,
            *,
            force_errors: bool = False,
        ) -> t.Infra.RopeNativeParsedModule: ...

        def get_pycore(self) -> p.AttributeProbe: ...

        def get_source_folders(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeResource]: ...

        def get_python_path_folders(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeResource]: ...

        def find_module(
            self,
            modname: str,
            folder: FlextInfraProtocolsRopeRuntime.RopeRoot | None = None,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource | None: ...

        def get_module(
            self,
            name: str,
            folder: FlextInfraProtocolsRopeRuntime.RopeRoot | None = None,
        ) -> t.Infra.RopeNativeSemanticModule: ...

        def get_relative_module(
            self,
            name: str,
            folder: FlextInfraProtocolsRopeRuntime.RopeRoot,
            level: int,
        ) -> t.Infra.RopeNativeParsedModule: ...

        def get_python_files(
            self,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeFile]: ...

        def do(self, changes: FlextInfraProtocolsRopeRuntime.RopeChangeSet) -> None: ...

        def validate(
            self,
            folder: FlextInfraProtocolsRopeRuntime.RopeRoot | None = None,
        ) -> None: ...

        def close(self) -> None: ...

        def get_prefs(self) -> FlextInfraProtocolsRopeRuntime.RopePreferences: ...

        def frozen_layout(self) -> AbstractContextManager[Self]: ...

    @runtime_checkable
    class RopeLocation(Protocol):
        """Rope occurrence location shape."""

        # flext-j47u (codex): detectors consume Rope's semantic occurrence
        # coordinates directly instead of rediscovering references textually.
        resource: FlextInfraProtocolsRopeRuntime.RopeResource | None
        offset: int
        lineno: int

    @runtime_checkable
    class RopeImportInfo(Protocol):
        """Common Rope import-info shape."""

        names_and_aliases: Sequence[tuple[str, str | None]]

        def get_import_statement(self) -> str: ...

    @runtime_checkable
    class RopeFromImport(RopeImportInfo, Protocol):
        """Rope from-import marker shape."""

        module_name: str
        level: int

    @runtime_checkable
    class RopeNormalImport(RopeImportInfo, Protocol):
        """Rope normal-import marker shape."""

    @runtime_checkable
    class RopeImportStatement(Protocol):
        """Rope import statement shape."""

        import_info: FlextInfraProtocolsRopeRuntime.RopeImportInfo
        start_line: int
        end_line: int

    @runtime_checkable
    class RopeWordFinder(Protocol):
        """Native delimiter reader owned by Worder's code finder."""

        def get_word_parens_range(
            self,
            offset: int,
            opening: str = "(",
            closing: str = ")",
        ) -> tuple[int, int]: ...

    @runtime_checkable
    class RopeWorder(Protocol):
        """Rope word/call classifier consumed by the static fact engine."""

        code_finder: FlextInfraProtocolsRopeRuntime.RopeWordFinder

        def get_primary_at(self, offset: int) -> str: ...

        def get_word_at(self, offset: int) -> str: ...

        def is_a_name_after_from_import(self, offset: int) -> bool: ...

        def is_from_aliased(self, offset: int) -> bool: ...

        def get_from_aliased(self, offset: int) -> str | None: ...

        def get_from_module(self, offset: int) -> str | None: ...

        def get_primary_range(self, offset: int) -> tuple[int, int]: ...

        def get_splitted_primary_before(self, offset: int) -> tuple[str, str, int]: ...

        def is_a_function_being_called(self, offset: int) -> bool: ...

        def get_word_parens_range(self, offset: int) -> tuple[int, int]: ...

        def get_parameters(
            self, first: int, last: int
        ) -> tuple[Sequence[str], Sequence[tuple[str, str]]]: ...

        def get_word_range(self, offset: int) -> tuple[int, int]: ...

        def find_function_offset(self, offset: int) -> int: ...

        def get_function_and_args_in_header(self, offset: int) -> str: ...

    @runtime_checkable
    class RopeChangeSet(Protocol):
        """Rope change set shape."""

        changes: list[p.AttributeProbe]

    @runtime_checkable
    class RopeInlineVariable(Protocol):
        """Native assigned-name inlining without publishing its changes."""

        def get_changes(
            self,
            *,
            remove: bool,
            resources: list[FlextInfraProtocolsRopeRuntime.RopeResource],
            docs: bool,
        ) -> FlextInfraProtocolsRopeRuntime.RopeChangeSet: ...

    @runtime_checkable
    class RopeChangeContents(Protocol):
        """A planned Rope content replacement with no applied effect."""

        resource: FlextInfraProtocolsRopeRuntime.RopeResource
        new_contents: str

    @runtime_checkable
    class RopeMoveResource(Protocol):
        """Native observational relocation; publication remains infra-owned."""

        resource: FlextInfraProtocolsRopeRuntime.RopeResource
        new_resource: FlextInfraProtocolsRopeRuntime.RopeResource

    @runtime_checkable
    class RopeContractMatch(Protocol):
        """Native Rope match coordinates without exposing syntax trees."""

        def get_region(self) -> tuple[int, int]: ...

        def get_capture_region(self, name: str) -> tuple[int, int]: ...

        def get_ast(
            self, name: str
        ) -> FlextInfraProtocolsRopeRuntime.RopeAstNode | None: ...

    @runtime_checkable
    class RopeSimilarFinder(Protocol):
        """One native Rope matcher for identity-bound matches and source regions."""

        def get_matches(
            self,
            code: str,
            args: Mapping[str, str] | None = None,
            *,
            start: int = 0,
            end: int | None = None,
        ) -> Iterator[FlextInfraProtocolsRopeRuntime.RopeContractMatch]: ...

    @runtime_checkable
    class RopeWildcard[Argument](Protocol):
        """Native wildcard callback, parameterized by its argument grammar."""

        def get_name(self) -> str: ...

        def matches(self, suspect: p.AttributeProbe, arg: Argument) -> bool: ...

    @runtime_checkable
    class RopeDefaultWildcard(RopeWildcard[str], Protocol):
        """Native default wildcard consuming Rope's string constraint grammar."""

    @runtime_checkable
    class RopeChangeComputer(Protocol):
        """Native source computation consumed by the restructuring planner."""

        def get_changed(self) -> str | None: ...

    @runtime_checkable
    class RopeRestructure(Protocol):
        """Public semantic restructuring planner at the Rope runtime boundary."""

        matched_count: int
        admitted_count: int

        def get_changes(
            self,
            *,
            resources: list[FlextInfraProtocolsRopeRuntime.RopeResource],
        ) -> FlextInfraProtocolsRopeRuntime.RopeChangeSet: ...

    @runtime_checkable
    class RopeModuleImports(Protocol):
        """Rope mutable module-import collection shape."""

        imports: list[FlextInfraProtocolsRopeRuntime.RopeImportStatement]

        def get_used_imports(
            self, defined_pyobject: FlextInfraProtocolsRopeRuntime.RopeParsedModule
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeImportInfo]: ...

        def add_import(
            self,
            import_info: FlextInfraProtocolsRopeRuntime.RopeImportInfo,
        ) -> None: ...

        def remove_duplicates(self) -> None: ...

        def sort_imports(self) -> None: ...

        def get_changed_source(self) -> str: ...

    @runtime_checkable
    class RopeImportTools(Protocol):
        """Native import translation used by observational relocation plans."""

        def relatives_to_absolutes(
            self,
            module: FlextInfraProtocolsRopeRuntime.RopePyModule,
        ) -> str: ...

    @runtime_checkable
    class RopeImportOrganizer(Protocol):
        """Rope import organizer shape."""

        def organize_imports(
            self,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource,
        ) -> FlextInfraProtocolsRopeRuntime.RopeChangeSet | None: ...

    @runtime_checkable
    class RopeMoveGlobal(Protocol):
        """Rope MoveGlobal refactoring shape."""

        def get_changes(
            self,
            target: FlextInfraProtocolsRopeRuntime.RopeResource,
            resources: Sequence[FlextInfraProtocolsRopeRuntime.RopeResource,]
            | None = None,
        ) -> FlextInfraProtocolsRopeRuntime.RopeChangeSet: ...

    @runtime_checkable
    class RopeOccurrence(Protocol):
        """Rope occurrence shape."""

        offset: int

        lineno: int

        def get_word_range(self) -> tuple[int, int]: ...

        def get_primary_range(self) -> tuple[int, int]: ...

        def is_written(self) -> bool: ...

        def is_defined(self) -> bool: ...

    @runtime_checkable
    class RopeOccurrenceFinder(Protocol):
        """Rope occurrence finder shape."""

        def find_occurrences(
            self,
            *,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource | None = None,
            pymodule: FlextInfraProtocolsRopeRuntime.RopePyModule | None = None,
        ) -> Sequence[FlextInfraProtocolsRopeRuntime.RopeOccurrence]: ...


__all__: list[str] = ["FlextInfraProtocolsRopeRuntime"]
