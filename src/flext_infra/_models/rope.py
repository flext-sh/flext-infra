"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsBase, FlextInfraModelsMixins
from flext_infra._models._codegen import (
    FlextInfraModelsCodegenFix,
    FlextInfraModelsCodegenLazyInit,
)


class FlextInfraModelsRope(FlextInfraModelsCodegenLazyInit):
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class RopeProjectElection(m.FrozenModel, str_strip_whitespace=False):
        """Exact ordered native import roots and source-selection policy."""

        source_folders: t.StrTuple = m.Field(
            description="Ordered project-relative importable source folders",
        )
        ignored_resources: t.StrTuple = m.Field(
            description="Source-scan ignore patterns elected by the caller",
        )
        extension_modules: t.StrTuple = m.Field(
            description="Native extension modules elected by the original project",
        )
        python_path_folders: t.StrTuple = m.Field(
            description="Ordered physical native import roots sharing the read owner",
        )

    class RopeRestructureRequest(FlextInfraModelsBase.FrozenArbitrary):
        """One complete native restructuring operation and its admitted inputs."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(str_strip_whitespace=False)

        pattern: t.NonEmptyStr = m.Field(description="Native Rope match template")
        goal: str = m.Field(
            description="Native Rope replacement template; empty removes the match"
        )
        arguments: Mapping[str, str | Sequence[str]] = m.Field(
            description="Native wildcard constraints and exact identity alternatives",
        )
        resources: Sequence[t.Port[p.Infra.RopeResource]] = m.Field(
            description="The complete resource inventory selected for this operation",
        )
        imports: Sequence[str] | Mapping[str, str] = m.Field(
            default=(),
            description="Native imports, optionally keyed by reusable lexical bindings",
        )
        match_filter: t.Infra.RopeMatchFilter | None = m.Field(
            default=None,
            description="Domain proof admitting each native source occurrence",
        )

    class RopeSourceImport(FlextInfraModelsBase.FrozenArbitrary):
        """One native import declaration and its original logical source region."""

        import_info: Annotated[
            t.Port[p.Infra.RopeFromImport],
            m.Field(exclude=True, description="Native Rope from-import identity"),
        ]
        start_line: Annotated[
            int, m.Field(ge=1, description="Original one-based declaration line")
        ]
        start_offset: Annotated[
            int, m.Field(ge=0, description="Original inclusive source character offset")
        ]
        end_offset: Annotated[
            int, m.Field(ge=0, description="Original exclusive source character offset")
        ]
        source: Annotated[
            str, m.Field(description="Complete Rope logical import statement")
        ]
        type_checking_guarded: Annotated[
            bool, m.Field(description="Import belongs to a TYPE_CHECKING suite")
        ]

    # Callers resolve project
    # selection once; source iteration has one exact, branch-free request shape.
    class SourceScanRequest(m.ContractModel):
        """Exact project roots selected for one production-source scan."""

        project_roots: Annotated[
            tuple[Path, ...],
            m.Field(
                min_length=1,
                description="Non-empty ordered project roots to scan",
            ),
        ]

    class SubscriptRebind(m.ContractModel):
        """Typed rule for one subscript-assignment rebind target.

        External runtimes legitimately re-register aliases through the
        interpreter's module table (CPython's ``collections`` publishes
        ``sys.modules['collections.abc'] = _collections_abc``). The rule owns
        the decision: such a rebind never redefines a class binding.
        """

        root_name: Annotated[
            str,
            m.Field(
                description="Root name of the subscript's value expression.",
            ),
        ]
        attribute: Annotated[
            str | None,
            m.Field(
                description=(
                    "Dotted attribute path between the root and the subscript "
                    "when the subscript applies to an attribute expression "
                    "(for example ``modules`` in ``sys.modules[...]``)."
                ),
            ),
        ] = None

        @m.computed_field
        @property
        def is_module_table_mutation(self) -> bool:
            """Whether the rebind mutates an interpreter module table.

            ``<alias>.modules[...] = ...`` only ever writes the interpreter's
            module registry (``sys`` aliases included), never a class binding
            of the indexed module.
            """
            if self.attribute == "modules":
                return True
            return self.root_name.lstrip("_") == "sys"

    class ExportOptions(m.ContractModel):
        """Canonical options for Rope module export discovery."""

        include_dunder: Annotated[
            bool,
            m.Field(description="Whether dunder exports should be returned."),
        ] = False
        allow_main: Annotated[
            bool,
            m.Field(description="Whether a module-level main() may be exported."),
        ] = False
        allow_assignments: Annotated[
            bool,
            m.Field(description="Whether assignment-backed names may be exported."),
        ] = False
        allow_functions: Annotated[
            bool,
            m.Field(description="Whether module functions may be exported."),
        ] = False
        require_explicit_all: Annotated[
            bool,
            m.Field(
                description="Whether __all__ must exist for exports to be returned.",
            ),
        ] = False

    class ClassInfo(FlextInfraModelsMixins.PositiveLineMixin, m.ContractModel):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, m.Field(description="Class name")]
        bases: Annotated[Sequence[str], m.Field(description="Base class names")] = ()

    class SourceClassReference(m.ContractModel):
        """A lexical binding and its attribute path, distinct from Ruff's spelling."""

        target: Annotated[str, m.Field(description="Dotted target the binding names")]
        attributes: Annotated[
            tuple[str, ...],
            m.Field(description="Attribute path read off the binding target"),
        ] = ()
        qualified_base: Annotated[
            str,
            m.Field(description="Fully qualified base spelling when resolved"),
        ] = ""

    class SourceClassDefinition(m.ContractModel):
        """One source declaration, preserving ordered bases and member shadowing."""

        identity: Annotated[
            str,
            m.Field(description="Qualified identity of the declared class"),
        ]
        bases: Annotated[
            tuple[FlextInfraModelsRope.SourceClassReference, ...],
            m.Field(description="Ordered base references of the declaration"),
        ]
        members: Annotated[
            Mapping[str, FlextInfraModelsRope.SourceClassReference | None],
            m.Field(description="Member name to shadowing reference mapping"),
        ]

    class SourceBindingCollectorSpec(m.ContractModel):
        """Execution context one lexical-binding collector pass consumes.

        The scalar fields describe the module under inventory. The two
        injected maps are shared execution state the caller owns: they
        travel unvalidated by reference so every pass accumulates directly
        into the caller's inventories instead of pydantic copies.
        """

        module: Annotated[
            t.NonEmptyStr,
            m.Field(description="Qualified module name under inventory"),
        ]
        provider: Annotated[
            m.InstanceOf[p.Infra.RopeSourceModule],
            m.Field(description="Native provider elected for the captured source"),
        ]
        package: Annotated[
            str,
            m.Field(description="Enclosing package name of the module"),
        ]
        required_line: Annotated[
            int | None,
            m.Field(
                ge=1,
                description="Index only bindings visible at this line when set",
            ),
        ] = None
        allow_conditional: Annotated[
            bool,
            m.Field(
                description="Whether conditional bindings may degrade to unknown",
            ),
        ] = False
        definitions: Annotated[
            m.InstanceOf[
                MutableMapping[str, FlextInfraModelsRope.SourceClassDefinition]
            ],
            m.Field(
                description="Cross-module definition inventory the walk extends",
            ),
        ]
        lexical: Annotated[
            m.InstanceOf[
                MutableMapping[str, FlextInfraModelsRope.SourceClassReference | None]
            ],
            m.Field(
                description="Module-scope bindings visible to every nested base",
            ),
        ]

    class SourceBindingInventoryRequest(m.ContractModel):
        """One captured module's request for a lexical-binding inventory."""

        project: Annotated[
            t.Port[t.Infra.RopeProject],
            m.Field(description="Open Rope project scoped to the analysis roots"),
        ]
        module: Annotated[
            t.NonEmptyStr,
            m.Field(description="Qualified module name under inventory"),
        ]
        path: Annotated[Path, m.Field(description="Captured module path")]
        # Why: the family contract strips field whitespace, which would shift
        # every parsed line number of captured source; the inventory indexes
        # declarations by their exact 1-based lines, so the text must survive
        # byte-for-byte. An empty module (a bare package __init__.py) is valid
        # captured source, so the text is not required to be non-empty.
        source: Annotated[
            str,
            t.StringConstraints(strip_whitespace=False),
            m.Field(description="Captured module source text"),
        ]
        required_line: Annotated[
            int | None,
            m.Field(
                ge=1,
                description="Index only bindings visible at this line when set",
            ),
        ] = None
        allow_conditional: Annotated[
            bool,
            m.Field(
                description="Whether conditional bindings may degrade to unknown",
            ),
        ] = False

    class ScopeDefinition(FlextInfraModelsMixins.PositiveLineMixin, m.ContractModel):
        """One semantic scope (def/class) discovered via rope's scope tree.

        Built from ``PyScope.get_kind()``/``get_scopes()`` and the scope's
        ``pyobject.get_name()`` — no ``ast`` walking. ``is_module_level`` is True
        when the scope is a direct child of the module (global) scope.
        """

        name: Annotated[str, m.Field(description="Definition name")]
        kind: Annotated[
            c.Infra.RopeScopeKind,
            m.Field(description="Rope scope kind (Module/Function/Class/Unknown)"),
        ]
        is_module_level: Annotated[
            bool,
            m.Field(description="Whether the scope is a direct child of the module"),
        ]

    class LogicalStatement(FlextInfraModelsMixins.PositiveLineMixin, m.ContractModel):
        """One logical statement from the rope structure boundary (no ``ast``).

        Built from a rope ``LogicalLineFinder`` region plus an indent stack over
        the rope-owned source; carries the lexical category, indentation, the
        enclosing def/class scope, and the rope source slice for lexical probes.
        """

        indent: Annotated[
            int,
            m.Field(ge=0, description="Leading-whitespace column of the statement"),
        ]
        # Rope owns both boundaries so multiline consumers
        # never reconstruct statement ranges from source text.
        end_line: Annotated[
            int,
            m.Field(ge=1, description="Final line in the Rope logical region"),
        ]
        start_offset: Annotated[
            int,
            m.Field(ge=0, description="Source offset where the region starts"),
        ]
        end_offset: Annotated[
            int,
            m.Field(ge=0, description="Source offset where the region ends"),
        ]
        category: Annotated[
            c.Infra.StatementCategory,
            m.Field(description="Lexical category of the leading token"),
        ]
        enclosing_kind: Annotated[
            c.Infra.RopeScopeKind,
            m.Field(description="Kind of the nearest enclosing def/class scope"),
        ] = c.Infra.RopeScopeKind.MODULE
        enclosing_name: Annotated[
            str,
            m.Field(description="Name of the nearest enclosing def/class, or empty"),
        ] = ""
        # Consumers share this Rope-derived guard fact instead
        # of rebuilding TYPE_CHECKING control flow with stdlib AST visitors.
        type_checking_guarded: Annotated[
            bool,
            m.Field(description="Whether the statement is inside TYPE_CHECKING"),
        ] = False
        # Why: the slice is rope-owned line/offset-aligned source text; the
        # family whitespace strip would detach it from its declared offsets.
        text: Annotated[
            str,
            t.StringConstraints(strip_whitespace=False),
            m.Field(description="Rope-owned source slice for the statement"),
        ] = ""

    class FamilyWrapperFlatten(FlextInfraModelsBase.FrozenArbitrary):
        """Rope identity of one namespace wrapper flattened into its family owner."""

        project: Annotated[
            t.Port[t.Infra.RopeProject],
            m.Field(description="Rope snapshot project resolving every consumer"),
        ]
        owner_name: Annotated[
            str,
            m.Field(description="Family owner class receiving promoted members"),
        ]
        wrapper_name: Annotated[
            str,
            m.Field(description="Declared name of the flattened namespace wrapper"),
        ]
        wrapper: Annotated[
            t.Port[t.Infra.RopePyName],
            m.Field(description="Rope identity of the flattened namespace wrapper"),
        ]
        names: Annotated[
            Mapping[str, str],
            m.Field(description="Wrapper member names mapped to promoted names"),
        ]

    class ConstantInfo(
        FlextInfraModelsMixins.NonNegativeLineMixin,
        FlextInfraModelsMixins.NestedClassPathMixin,
        m.ContractModel,
    ):
        """Final-annotated constant definition from rope semantic analysis."""

        name: Annotated[str, m.Field(description="Constant name")]
        annotation: Annotated[str, m.Field(description="Type annotation text")] = ""
        value: Annotated[str, m.Field(description="Value representation")] = ""

    class SymbolInfo(FlextInfraModelsMixins.NonNegativeLineMixin, m.ContractModel):
        """Top-level symbol metadata from rope semantic analysis."""

        name: Annotated[str, m.Field(description="Symbol name")]
        kind: Annotated[
            str,
            m.Field(description="Symbol kind: class, function, assignment"),
        ]

    class ConsolidatorScannedFile(FlextInfraModelsBase.FrozenArbitrary):
        """One scanned module whose assignments match canonical constants."""

        resource: Annotated[
            t.Port[t.Infra.RopeResource],
            m.Field(description="Rope resource of the scanned module"),
        ]
        source: Annotated[
            str,
            m.Field(description="Source captured at scan; restored on failed gates"),
        ]
        matches: Annotated[
            Sequence[tuple[FlextInfraModelsRope.SymbolInfo, str, str]],
            m.Field(description="Matched symbol, canonical reference, and raw value"),
        ]

    class ModuleSemanticState(m.ContractModel):
        """Unified semantic snapshot for one Rope module analysis pass."""

        class_infos: Annotated[
            tuple[FlextInfraModelsRope.ClassInfo, ...],
            m.Field(description="Local classes discovered in the module"),
        ] = ()
        declared_imports: Annotated[
            Mapping[str, str],
            m.Field(description="Declared import targets by name"),
        ]
        semantic_imports: Annotated[
            Mapping[str, str],
            m.Field(description="Resolved import targets by name"),
        ]

    class RopeModuleConvention(m.ContractModel):
        """Unified module naming and namespace convention for one file."""

        file_path: Annotated[Path, m.Field(description="Resolved Python module path")]
        relative_path: Annotated[
            Path,
            m.Field(description="Module path relative to its package directory"),
        ]
        module_name: Annotated[str, m.Field(description="Fully-qualified module name")]
        package_name: Annotated[
            str,
            m.Field(description="Importable package name for the module"),
        ]
        package_dir: Annotated[
            Path,
            m.Field(description="Resolved package directory containing the module"),
        ]
        package_context: Annotated[
            FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
            m.Field(description="Resolved lazy-init package context for the module"),
        ]
        module_policy: Annotated[
            FlextInfraModelsCodegenFix.NamespaceModulePolicy,
            m.Field(description="Canonical module policy derived for the module"),
        ]
        project_layout: Annotated[
            FlextInfraModelsRope.RopeProjectLayout | None,
            m.Field(
                description="Resolved project layout, when the module belongs to one",
            ),
        ] = None

    class RopeInventoryRecordInput(m.ArbitraryTypesModel):
        """Validated payload for building one rope inventory census object."""

        rope_project: Annotated[
            t.Port[t.Infra.RopeProject],
            m.Field(description="Rope project used for reference discovery"),
        ]
        resource: Annotated[
            t.Port[t.Infra.RopeResource],
            m.Field(description="Rope resource containing the symbol definition"),
        ]
        source: Annotated[
            str,
            m.Field(description="Full source text used to compute fingerprints"),
        ]
        parameter_lines: Annotated[
            Mapping[tuple[int, str], int],
            m.Field(description="Parameter positions from the module snapshot"),
        ]
        constant_bindings: Annotated[
            frozenset[tuple[int, str]],
            m.Field(
                description="Identity-proven immutable declarations in the snapshot"
            ),
        ] = frozenset()
        name: Annotated[str, m.Field(description="Resolved symbol name being recorded")]
        pyname: Annotated[
            t.Port[t.Infra.RopePyName],
            m.Field(description="Rope pyname node for the symbol"),
        ]
        module_name: Annotated[
            str,
            m.Field(description="Resolved module name for the symbol"),
        ]
        project_name: Annotated[
            str,
            m.Field(description="Resolved project name for census attribution"),
        ]
        convention: Annotated[
            FlextInfraModelsRope.RopeModuleConvention,
            m.Field(description="Module convention metadata for tier/facade checks"),
        ]
        scope_chain: Annotated[
            Sequence[str],
            m.Field(description="Nested scope path leading to the symbol"),
        ] = ()
        class_chain: Annotated[
            Sequence[str],
            m.Field(description="Nested class path leading to the symbol"),
        ] = ()
        child_scope: Annotated[
            t.Port[p.Infra.RopeScopeDsl] | None,
            m.Field(description="Optional child scope object from rope"),
        ] = None
        rope_workspace: Annotated[
            t.Port[p.Infra.RopeWorkspaceDsl],
            m.Field(description="Shared rope workspace/session owning the resource"),
        ]

    class RopeWorkspaceSession(m.ContractModel):
        """Public Rope workspace snapshot used by the service DSL."""

        repository_root: Annotated[
            Path,
            m.Field(description="Resolved repository root requested by the caller"),
        ]
        rope_repository_root: Annotated[
            Path,
            m.Field(description="Canonical root used to open the shared Rope project"),
        ]
        # Policy stays in config.Infra;
        # this field-only model retains only materialized session state.
        workspace_index: Annotated[
            FlextInfraModelsRope.RopeWorkspaceIndex,
            m.Field(description="Materialized workspace index for the open session"),
        ]


__all__: list[str] = ["FlextInfraModelsRope"]
