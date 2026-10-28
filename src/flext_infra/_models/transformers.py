"""Domain models for the transformers subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import p, t
from flext_infra._models import FlextInfraModelsBase


class FlextInfraModelsTransformers:
    """Models for source transformers — exposed through the ``m.Infra`` facade."""

    class SemanticPublicationOptions(m.FrozenModel):
        """Caller-controlled gates and scope roots for one joint publication."""

        validator: Callable[[Path], p.Result[bool]] | None = m.Field(
            default=None,
            description="Consumer acceptance gate over the previewed view root",
        )
        plan_validator: (
            Callable[[tuple[m.Cli.FileChange, ...]], p.Result[bool]] | None
        ) = m.Field(
            default=None,
            description=(
                "Consumer acceptance gate over the normalized candidate changes, "
                "for a consumer that reads its own snapshot instead of a view root"
            ),
        )
        projection_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Generated projection roots composed into the publication",
        )

    class AliasMigrationContext(m.ContractModel):
        """Resolved ownership and import-root context for one alias migration."""

        policy_owner: Annotated[
            str,
            m.Field(description="Project package that owns the canonical alias policy"),
        ]
        import_root: Annotated[
            str,
            m.Field(description="Public facade root from which consumers import"),
        ]

    class SemanticFilePlan(m.ContractModel):
        """Exact before state and desired state for one semantic migration file."""

        project: Annotated[Path, m.Field(description="Physical owning project root")]
        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        before: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Descriptor-authenticated file state before migration"),
        ]
        desired_content: Annotated[
            bytes | None,
            m.Field(
                strict=True,
                description=(
                    "Exact desired bytes after migration, or None for no change"
                ),
            ),
        ]
        desired_mode: Annotated[
            int | None,
            m.Field(
                ge=0,
                le=0o7777,
                strict=True,
                description="Exact desired mode, or None for no change",
            ),
        ]
        changes: Annotated[
            tuple[str, ...],
            m.Field(description="Recorded migration operations"),
        ] = m.Field(default_factory=tuple)

    class SemanticMigrationEdit(m.ContractModel):
        """One validated in-memory semantic source rewrite."""

        # Why: source bytes must survive validation byte-exact;
        # the strict base strips whitespace, which corrupts CAS comparisons.
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            str_strip_whitespace=False, arbitrary_types_allowed=True
        )

        file_path: Annotated[Path, m.Field(description="Source file to rewrite")]
        original_source: Annotated[
            str | None,
            m.Field(
                description=(
                    "Source bytes before migration; None declares a creation "
                    "whose destination must not exist when published"
                ),
            ),
        ]
        updated_source: Annotated[
            str,
            m.Field(description="Prospective source bytes after migration"),
        ]
        retire_file: bool = m.Field(
            default=False,
            description="Explicit source retirement, not empty-file output",
        )
        changes: Annotated[
            tuple[str, ...],
            m.Field(description="Recorded migration operations"),
        ] = ()

    class SemanticBehaviorRewriteRequest(m.ArbitraryTypesModel):
        """One consumer rewrite over its declared behavior owner facts."""

        path: Annotated[Path, m.Field(description="Consumer source identity")]
        source: Annotated[str, m.Field(description="Consumer source text")]
        modules: Annotated[
            Mapping[str, tuple[str, bool]],
            m.Field(description="Qualified source text and package identities"),
        ]
        ownership: Annotated[
            tuple[
                Mapping[tuple[str, str], Sequence[tuple[str, str]]],
                frozenset[tuple[str, str, str, str]],
            ],
            m.Field(description="Declared utility owners and facade dispatch needs"),
        ]
        utility_imports: Annotated[
            frozenset[tuple[str, str]],
            m.Field(description="Elected self-facade import identities"),
        ] = m.Field(default_factory=frozenset[tuple[str, str]])
        declaration_imports: Annotated[
            frozenset[tuple[str, str]],
            m.Field(
                description="External declaration receivers eligible for proven lower "
                "binding"
            ),
        ] = m.Field(default_factory=frozenset[tuple[str, str]])

    class DeclarationRelocationFinding(m.ContractModel):
        """One payload declaration whose relocation owner cannot be resolved."""

        file_path: Annotated[
            Path,
            m.Field(description="Source file declaring the unrelocated payload"),
        ]
        declaration: Annotated[
            t.NonEmptyStr,
            m.Field(description="Qualified ``Outer.Payload`` declaration name"),
        ]
        expected_owner: Annotated[
            t.NonEmptyStr,
            m.Field(description="Owner the relocation expected to resolve"),
        ]
        reason: Annotated[
            t.NonEmptyStr,
            m.Field(description="Why that owner did not resolve"),
        ]

    class CompatibilityAliasRewritePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Binding-proven rewrites planned for one compatibility-alias cutover file."""

        local_aliases: Annotated[
            Mapping[str, str],
            m.Field(description="Aliases the file declares, mapped to their targets"),
        ]
        import_aliases: Annotated[
            Mapping[str, Mapping[str, str]],
            m.Field(description="Imported aliases per source module and their targets"),
        ]
        attribute_aliases: Annotated[
            Mapping[tuple[str, str], str],
            m.Field(description="Module attribute alias accesses and their targets"),
        ]
        qualified_aliases: Annotated[
            Mapping[str, str],
            m.Field(description="Qualified alias identities mapped to their targets"),
        ]
        target_bindings: Annotated[
            frozenset[str],
            m.Field(description="Module-level names the file already binds"),
        ]
        preserved_reads: Annotated[
            frozenset[tuple[int, int]],
            m.Field(description="Eager upstream reads before a local alias rebind"),
        ] = frozenset()
        upstream_aliases: Annotated[
            Mapping[str, str],
            m.Field(description="Proven upstream identities preceding local aliases"),
        ] = m.Field(default_factory=u.empty(TypeForm(Mapping[str, str])))

    class PrivateImportRewritePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Binding-proven import rewrites planned for one private-import file."""

        removals: Annotated[
            Mapping[str, frozenset[str]],
            m.Field(description="Private symbols removed per source module"),
        ]
        obsolete_imports: Annotated[
            Mapping[str, frozenset[str]],
            m.Field(description="Public roots superseded by their facade alias"),
        ]
        replacements: Annotated[
            Mapping[str, str],
            m.Field(description="Private qualified identities and public references"),
        ]
        public_imports: Annotated[
            Mapping[str, str],
            m.Field(description="Facade aliases mapped to their publishing package"),
        ]

    class Tier0ImportAnalysis(m.Value):
        """Detection results for a single Python file self-import patterns."""

        # Why: value contract owned by m.Infra transformers facet, not nested
        # in the fixer service.
        package_name: Annotated[
            str,
            m.Field(description="Resolved package name for the analyzed file"),
        ]
        file_path: Annotated[
            Path,
            m.Field(description="Python file analyzed for Tier 0 import violations"),
        ]
        alias_to_module: Annotated[
            Mapping[str, str],
            m.Field(description="Alias names mapped to their source modules"),
        ]
        category_a: Annotated[
            frozenset[str],
            m.Field(description="Top-level aliases that are informational only"),
        ] = m.Field(default_factory=frozenset[str])
        category_b: Annotated[
            frozenset[str],
            m.Field(description="Core aliases to redirect to the core package"),
        ] = m.Field(default_factory=frozenset[str])
        category_c: Annotated[
            frozenset[str],
            m.Field(description="Aliases to move into a TYPE_CHECKING block"),
        ] = m.Field(default_factory=frozenset[str])
        category_d: Annotated[
            frozenset[str],
            m.Field(
                description="Runtime-used aliases requiring direct import handling",
            ),
        ] = m.Field(default_factory=frozenset[str])

        @m.computed_field
        @property
        def has_violations(self) -> bool:
            """True if any imports need redirecting or moving.

            Returns:
                The resulting ``bool``.

            """
            return bool(self.category_b or self.category_c or self.category_d)

    class SourceRewrite(FlextInfraModelsBase.FrozenArbitrary):
        """One source rewrite: replace ``source[start:end]`` with ``text``."""

        start: Annotated[int, m.Field(description="Start byte offset in the source")]
        end: Annotated[int, m.Field(description="End byte offset in the source")]
        text: Annotated[str, m.Field(description="Replacement text")]

    class HeaderSpan(m.ArbitraryTypesModel):
        """Byte offsets for the logical sections of a Python module header.

        Mutable accumulator populated incrementally by the header tokenizer
        (``_utilities/transformer_header_parser.py``); never frozen while a
        parse is open.
        """

        shebang_end: Annotated[
            int,
            m.Field(description="Byte offset just after the shebang line"),
        ] = 0
        encoding_end: Annotated[
            int,
            m.Field(description="Byte offset just after the encoding cookie"),
        ] = 0
        comments_end: Annotated[
            int,
            m.Field(description="Byte offset after the leading comment block"),
        ] = 0
        docstring_end: Annotated[
            int,
            m.Field(description="Byte offset after the module docstring"),
        ] = 0
        last_import_end: Annotated[
            int,
            m.Field(description="Byte offset after the last import statement"),
        ] = 0

    class ClassBlockLayout(m.ArbitraryTypesModel):
        """Measured layout of one wrapper class block to unwrap.

        Line coordinates are Rope's one-based lines; ``indentation`` is the
        body column width to strip, and ``docstring_span`` excludes the
        wrapper's own docstring lines from the strip when present.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        header_start: Annotated[int, m.Field(description="First header line")]
        header_end: Annotated[int, m.Field(description="Last header line")]
        body_end: Annotated[int, m.Field(description="Last body line")]
        indentation: Annotated[
            int,
            m.Field(description="Body indent width stripped per line"),
        ]
        docstring_span: Annotated[
            tuple[int, int] | None,
            m.Field(description="Wrapper docstring line span"),
        ] = None

    class HeaderInfo(FlextInfraModelsBase.FrozenArbitrary):
        """Structural summary of a module header."""

        has_future_annotations: Annotated[
            bool,
            m.Field(description="Whether the module already imports annotations"),
        ]
        aliases: Annotated[
            frozenset[str],
            m.Field(description="Local names bound by from-import statements"),
        ]
        span: Annotated[
            FlextInfraModelsTransformers.HeaderSpan,
            m.Field(description="Byte offsets for the header sections"),
        ]

    class FacadeNamespaceCutover(m.ArbitraryTypesModel):
        """Shared planning state for one duplicate facade-namespace cutover.

        Replaces the untyped parameter bundle the nesting planner threaded
        through its helpers: the Rope project, the physical root, the editable
        sources, the prospective bytes and the accumulated consumer rewrites
        travel as one resolved contract.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        project: Annotated[
            t.Port[t.Infra.RopeProject],
            m.Field(description="Rope project snapshot holding the editable sources"),
        ]
        root: Annotated[Path, m.Field(description="Physical project root")]
        sources: Annotated[
            Mapping[Path, str],
            m.Field(description="Editable source bytes per path"),
        ]
        working: Annotated[
            MutableMapping[Path, str],
            m.Field(description="Prospective source bytes per path"),
        ]

    class FacadeNamespaceSite(FlextInfraModelsBase.FrozenArbitrary):
        """Resolved duplicate-facade site for one editable source module."""

        path: Annotated[Path, m.Field(description="Source path holding the facade")]
        source: Annotated[str, m.Field(description="Source bytes holding the facade")]
        facade: Annotated[
            t.Port[ast.ClassDef], m.Field(description="Facade composition class")
        ]
        namespace: Annotated[
            t.Port[ast.ClassDef],
            m.Field(description="Single composed namespace class"),
        ]
        children: Annotated[
            tuple[t.Port[ast.ClassDef], ...],
            m.Field(description="Facade body classes"),
        ]
        tree: Annotated[t.Port[ast.Module], m.Field(description="Parsed source module")]


__all__: list[str] = ["FlextInfraModelsTransformers"]
