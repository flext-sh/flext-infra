"""Lazy-init planning and quality-gate models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Annotated, Literal

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsMixins


class FlextInfraModelsCodegenLazyInit:
    """Lazy-init planning and quality-gate models."""

    class PythonModuleFacts(m.ContractModel):
        """Static top-level facts of one module source, derived once per parse."""

        path: Annotated[Path, m.Field(description="Source file the facts describe")]
        declaration_only: bool = m.Field(
            description="Native syntax contains only documentation and future imports"
        )
        members: Annotated[
            t.MappingKV[str, t.Infra.PythonMemberKind],
            m.Field(description="Every bound top-level name, in declaration order"),
        ]
        imports: Annotated[
            t.MappingKV[str, str],
            m.Field(description="Dotted import target of each imported name"),
        ]
        exports: Annotated[
            t.StrSequence | None,
            m.Field(
                description=(
                    "Literal ``__all__`` names; empty when an entry is not a "
                    "string literal; ``None`` when the module declares none"
                ),
            ),
        ]
        classes: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(description="Base expressions as written, per defined class"),
        ]
        class_exports: Annotated[
            t.MappingKV[str, t.StrSequence | None],
            m.Field(description="Class-level ``__all__`` names per defined class"),
        ]
        values: Annotated[
            t.MappingKV[str, str],
            m.Field(description="Source text of each assigned top-level value"),
        ]

    class PythonModuleFactsDraft(m.ArbitraryTypesModel):
        """Facts of one module accumulated statement by statement, then frozen."""

        path: Annotated[Path, m.Field(description="Source file being read")]
        name: Annotated[str, m.Field(description="Dotted module name")]
        is_init: Annotated[bool, m.Field(description="Whether it is a package init")]
        members: Annotated[
            t.Port[dict[str, t.Infra.PythonMemberKind]],
            m.Field(exclude=True, description="Bound names so far, in order"),
        ]
        imports: Annotated[
            t.Port[dict[str, str]],
            m.Field(exclude=True, description="Import targets so far"),
        ]
        classes: Annotated[
            t.Port[dict[str, t.StrSequence]],
            m.Field(exclude=True, description="Class bases so far"),
        ]
        class_exports: Annotated[
            t.Port[dict[str, t.StrSequence | None]],
            m.Field(exclude=True, description="Class-level exports so far"),
        ]
        values: Annotated[
            t.Port[dict[str, str]],
            m.Field(exclude=True, description="Assigned value text so far"),
        ]
        exports: Annotated[
            t.Port[list[str | None]] | None,
            m.Field(exclude=True, description="``__all__`` entries so far"),
        ] = None

    class PythonModelRun(m.ArbitraryTypesModel):
        """One run of the shared static Python model: source view and parse caches."""

        source_project: Annotated[
            t.Port[p.Infra.RopeProject],
            m.Field(
                exclude=True, description="Source view every module is read through"
            ),
        ]
        module_files: Annotated[
            t.MappingKV[str, Path],
            m.Field(description="Indexed module names elected before installed ones"),
        ]
        modules: Annotated[
            t.Port[
                MutableMapping[
                    t.Infra.RopeNativeParsedModule,
                    FlextInfraModelsCodegenLazyInit.PythonModuleFacts,
                ]
            ],
            m.Field(
                exclude=True,
                description="Facts of each parsed module, keyed by the run's parse",
            ),
        ]
        ancestors: Annotated[
            t.Port[dict[str, frozenset[str]]],
            m.Field(exclude=True, description="Resolved class ancestry by path"),
        ]
        project_notices: Annotated[
            t.Port[dict[Path, t.Pair[t.Infra.DocumentationLanguage, str]]],
            m.Field(
                exclude=True,
                description=(
                    "Documentation language and copyright notice per owning "
                    "project root, read once per run"
                ),
            ),
        ]

    class LazyInitPackageContext(m.ContractModel):
        """Declarative package context for one lazy-init directory."""

        pkg_dir: Path = m.Field(description="Directory being processed.")
        init_path: Path = m.Field(description="Target __init__.py path.")
        current_pkg: str = m.Field(description="Importable package name.")
        surface: str = m.Field(description="Root surface for wrapper alias resolution.")
        generated_init: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the current __init__.py is generated by lazy-init."
                ),
            ),
        ] = False
        importable: Annotated[
            bool,
            m.Field(
                description="Whether the directory resolves to an importable package.",
            ),
        ] = False

    class LazyInitPlan(m.ContractModel):
        """Immutable resolved decision and its original source consumption."""

        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext = m.Field(
            description="Discovered package context.",
        )
        action: Annotated[
            c.Infra.LazyInitAction,
            m.Field(description="Action selected for this package."),
        ] = c.Infra.LazyInitAction.SKIP
        ownership: Literal["generator", "authored"] | None = m.Field(
            default=None,
            description="Content-elected initializer owner",
        )
        disposition: Literal["planned", "retained"] | None = m.Field(
            default=None,
            description="Actual ownership decision, never a failure suppression",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Public exports for generated __init__.py.",
        )
        lazy_map: t.LazyAliasMap = m.Field(
            description="Lazy import map: export name to module/attribute target.",
        )
        eager_dunders: t.LazyAliasMap = m.Field(
            description=(
                "Dunder exports bound eagerly right after the lazy installer. "
                "Required for the ``__version__.py`` submodule case where the "
                "submodule name collides with the dunder string it exports — "
                "the first submodule load rebinds the package attribute to the "
                "module, so only an eager binding pins the canonical string; "
                "running after the installer lets the submodule consume the "
                "package's own facades without an initialization cycle."
            ),
        )
        child_packages_for_lazy: t.StrSequence = m.Field(
            default_factory=tuple,
            description=(
                "Importable direct child packages recorded as metadata; "
                "their symbols are not reexported by an ancestor."
            ),
        )

    class QualityGateCheck(m.ArbitraryTypesModel):
        """A single quality gate check result entry."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Check identifier")]
        passed: Annotated[bool, m.Field(description="Whether check passed")]
        detail: Annotated[str, m.Field(description="Human-readable check detail")] = ""
        critical: Annotated[bool, m.Field(description="Whether failure is critical")]

    class QualityGateProjectFinding(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Per-project quality gate findings."""

        violations_total: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total violations"),
        ]
        validator_passed: Annotated[
            bool,
            m.Field(description="Whether validator passed"),
        ]


__all__: list[str] = ["FlextInfraModelsCodegenLazyInit"]
