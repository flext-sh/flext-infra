"""Managed file and template entry specification models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, Self

import flext_core
from flext_cli import m
from typing_extensions import TypeForm

from flext_infra import c, t
from flext_infra._models._config.contract import FlextInfraConfigModelsContract
from flext_infra._models._config.scaffold import FlextInfraConfigModelsScaffold


class FlextInfraConfigModelsTemplates:
    """Managed file and template entry specification models."""

    class CodegenVscodeSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed editor declarations shared by target and artifact planning."""

        model_config = m.ConfigDict(extra="forbid")

        settings: Annotated[
            t.Infra.SettingsPairs,
            m.Field(description="Ordered VS Code key/value pairs; the last key wins"),
        ] = ()
        map_union_settings: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(description="VS Code objects union-merged over project settings"),
        ] = m.Field(
            default_factory=flext_core.u.empty(TypeForm(Mapping[str, t.JsonMapping])),
            validate_default=True,
        )

        stripped_keys: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "VS Code keys actively stripped from the settings projection "
                    "because they conflict with a pyrightconfig.json/pyproject.toml "
                    "owner (Pylance settingsNotOverridable)."
                ),
            ),
        ] = ()

        stripped_map_keys: Annotated[
            Mapping[str, t.VariadicTuple[str]],
            m.Field(description="Retired keys inside language-specific setting maps"),
        ] = m.Field(
            default_factory=flext_core.u.empty(
                TypeForm(Mapping[str, t.VariadicTuple[str]])
            ),
            validate_default=True,
        )

        @m.model_validator(mode="after")
        def _validate_setting_keys(self) -> Self:
            """Validate setting-key grammar without an extension-option registry.

            Returns:
                The declaration with valid ordinary or language-override keys.

            Raises:
                ValueError: If a declared key contains invalid setting syntax.

            """
            keys = (
                *(key for key, _value in self.settings),
                *self.map_union_settings,
                *self.stripped_keys,
                *self.stripped_map_keys,
            )
            for key in keys:
                ordinary = key.split(".")
                languages = key.removeprefix("[").removesuffix("]").split("][")
                segments = (
                    languages if key.startswith("[") and key.endswith("]") else ordinary
                )
                if not all(
                    segment and all(char.isalnum() or char in "_-+" for char in segment)
                    for segment in segments
                ):
                    msg = f"invalid VS Code setting key: {key}"
                    raise ValueError(msg)
            return self

    class CodegenVscodeDeclarationDelta(
        FlextInfraConfigModelsContract.ConfigContract,
    ):
        """Portable editor overrides extracted from one captured document."""

        values: Annotated[
            t.JsonMapping,
            m.Field(
                description="Minimal typed codegen.vscode declaration overrides",
            ),
        ]

    class CodegenLayerProjection(FlextInfraConfigModelsContract.ConfigContract):
        """An owned declaration delta projected into one elected config layer."""

        path: Annotated[Path, m.Field(description="Exact target config layer")]
        values: Annotated[
            t.JsonMapping,
            m.Field(description="JSON-compatible declaration fragment"),
        ]

    class ConfigDocumentInputs(FlextInfraConfigModelsContract.ConfigContract):
        """One composed F.yaml document with its consulted physical sources."""

        values: Annotated[
            t.JsonMapping,
            m.Field(description="Strictly parsed and ordered configuration document"),
        ]
        sources: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                exclude=True,
                description="Exact physical files consulted by this document",
            ),
        ] = ()

    class ManagedFileOwnership(FlextInfraConfigModelsContract.ConfigContract):
        """Path-independent ownership shared by declarations and planned views."""

        model_config = m.ConfigDict(extra="forbid")

        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        tracking: Annotated[
            Literal["versioned", "runtime-local"],
            m.Field(description="Versioned declaration or checkout-local projection"),
        ] = "versioned"
        policy: Annotated[
            Literal["full", "merge"],
            m.Field(
                description=(
                    "Full renders the whole file; merge keeps content outside "
                    "the owner's declared sections"
                ),
            ),
        ]
        mode: Annotated[
            int,
            m.Field(
                ge=0,
                le=0o7777,
                strict=True,
                description="Exact permission bits owned by generated publication",
            ),
        ] = 0o644
        conflict_sections: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Dotted sections rendered by the canonical owner"),
        ] = ()
        preserve_project_keys: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Authored PEP 621 project keys retained on merge"),
        ] = ()
        overwrite_project_keys: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="PEP 621 project keys replaced by generation"),
        ] = ()

        @m.model_validator(mode="after")
        def validate_project_key_ownership(self) -> Self:
            """Reject keys assigned to both the author and the generator.

            Returns:
                The declaration with disjoint project-key ownership.

            Raises:
                ValueError: If project keys have competing owners.

            """
            competing = set(self.preserve_project_keys).intersection(
                self.overwrite_project_keys,
            )
            if competing:
                msg = f"project keys have competing owners: {', '.join(sorted(competing))}"
                raise ValueError(msg)
            return self

        @m.computed_field
        @property
        def managed_tool_tables(self) -> t.VariadicTuple[str]:
            """Derive tool-relative table paths from the owner's sections.

            Returns:
                The tool-relative table paths without duplicates.

            """
            return tuple(
                dict.fromkeys(
                    table
                    for section in self.conflict_sections
                    for root, _separator, table in (section.partition("."),)
                    if root == c.Infra.TOOL and table
                ),
            )

    class TemplateDeclarationSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Path-independent template body stored under one destination key."""

        model_config = m.ConfigDict(extra="forbid")

        source: Annotated[
            Path | None,
            m.Field(
                description="Source relative to the selected template or package root",
            ),
        ] = None
        source_kind: Annotated[
            Literal["template", "resource"],
            m.Field(
                description="Render a template or project the original package asset",
            ),
        ] = "template"
        requires_artifacts: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Catalog destination keys required by this artifact"),
        ] = ()
        profiles: Annotated[
            t.VariadicTuple[c.Infra.MakeProfile],
            m.Field(min_length=1, description="Profiles that consume the artifact"),
        ]
        ownership: Annotated[
            FlextInfraConfigModelsTemplates.ManagedFileOwnership | None,
            m.Field(
                description=(
                    "Explicit generated-file ownership, or null for an authored "
                    "project-creation seed"
                ),
            ),
        ]
        requires_release_protocol: Annotated[
            bool,
            m.Field(
                default=False,
                description=(
                    "Whether this projection requires the repository's explicit "
                    "release-protocol opt-in"
                ),
            ),
        ] = False
        requires_beads: Annotated[
            bool,
            m.Field(description="Whether the projection requires Beads participation"),
        ] = False

        @m.model_validator(mode="after")
        def validate_artifact_declaration(self) -> Self:
            """Confine paths and require an explicit render or specialized owner.

            Returns:
                The confined declaration without an ambiguous rendering route.

            Raises:
                ValueError: If an artifact escapes its root, repeats a profile,
                    or has neither a template nor specialized merge ownership.

            """
            if self.source is not None and (
                self.source.is_absolute()
                or ".." in self.source.parts
                or self.source == Path()
            ):
                msg = f"artifact source must be root-relative: {self.source}"
                raise ValueError(msg)
            if len(set(self.profiles)) != len(self.profiles):
                msg = "artifact profiles must not repeat"
                raise ValueError(msg)
            if self.source_kind == "resource" and (
                self.source is None
                or self.ownership is None
                or self.ownership.policy != "full"
            ):
                msg = "resource requires an explicit source and full managed ownership"
                raise ValueError(msg)
            if self.source is None and (
                self.ownership is None or self.ownership.policy != "merge"
            ):
                msg = "artifact without a template requires specialized merge ownership"
                raise ValueError(msg)
            return self

    class TemplateEntrySpec(TemplateDeclarationSpec):
        """One validated template body with its derived destination."""

        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]

        @m.model_validator(mode="after")
        def validate_destination(self) -> Self:
            """Confine the destination supplied by its catalog key."""
            path = Path(self.destination)
            if path.is_absolute() or ".." in path.parts or path == Path():
                msg = f"artifact destination must be root-relative: {path}"
                raise ValueError(msg)
            return self

    class TemplatesSpec(FlextInfraConfigModelsContract.ConfigContract):
        """The single ordered catalog of generated artifacts and authored seeds."""

        model_config = m.ConfigDict(
            extra="forbid",
            serialize_by_alias=True,
            validate_by_alias=True,
            validate_by_name=False,
        )

        root: Annotated[Path, m.Field(description="Package-relative template root")]
        catalog: Annotated[
            Mapping[
                t.NonEmptyStr,
                FlextInfraConfigModelsTemplates.TemplateDeclarationSpec,
            ],
            m.Field(
                alias="entries",
                description="Ordered template bodies keyed by destination",
            ),
        ]

        @property
        def entries(
            self,
        ) -> t.VariadicTuple[FlextInfraConfigModelsTemplates.TemplateEntrySpec]:
            """Expose the existing typed consumer view without a second wire field."""
            return tuple(
                FlextInfraConfigModelsTemplates.TemplateEntrySpec(
                    destination=destination,
                    source=declaration.source,
                    source_kind=declaration.source_kind,
                    requires_artifacts=declaration.requires_artifacts,
                    profiles=declaration.profiles,
                    ownership=declaration.ownership,
                    requires_release_protocol=declaration.requires_release_protocol,
                    requires_beads=declaration.requires_beads,
                )
                for destination, declaration in self.catalog.items()
            )

        def required_destinations(self, destinations: frozenset[str]) -> frozenset[str]:
            """Expand selected catalog keys through their explicit dependencies."""
            selected = set(destinations)
            pending = list(destinations)
            while pending:
                destination = pending.pop()
                declaration = self.catalog.get(destination)
                if declaration is None:
                    continue
                for dependency in declaration.requires_artifacts:
                    if dependency not in selected:
                        selected.add(dependency)
                        pending.append(dependency)
            return frozenset(selected)

        @m.model_validator(mode="after")
        def validate_unique_destinations(self) -> Self:
            """Require exactly one authoring declaration per destination.

            Returns:
                The catalog with unique destination paths.

            Raises:
                ValueError: If two declarations address the same artifact.

            """
            if self.root.is_absolute() or ".." in self.root.parts:
                msg = f"template root must be package-relative: {self.root}"
                raise ValueError(msg)
            paths = tuple(Path(entry.destination) for entry in self.entries)
            if len(set(paths)) != len(paths):
                msg = "artifact destinations must have exactly one declaration"
                raise ValueError(msg)
            for destination, declaration in self.catalog.items():
                for dependency in declaration.requires_artifacts:
                    required = self.catalog.get(dependency)
                    if required is None:
                        msg = f"artifact dependency is not declared: {dependency}"
                        raise ValueError(msg)
                    if (
                        not set(declaration.profiles) <= set(required.profiles)
                        or required.ownership is None
                        or (required.requires_beads and not declaration.requires_beads)
                        or (
                            required.requires_release_protocol
                            and not declaration.requires_release_protocol
                        )
                    ):
                        msg = (
                            f"artifact dependency is not always available: {dependency}"
                        )
                        raise ValueError(msg)
                    if destination in self.required_destinations(
                        frozenset({dependency}),
                    ):
                        msg = f"artifact dependency cycle: {destination}"
                        raise ValueError(msg)
            return self

    class ManagedFileSpec(ManagedFileOwnership):
        """One declared file governed by generation and tracking policy."""

        path: Annotated[Path, m.Field(description="Repository-relative file path")]

        @m.model_validator(mode="after")
        def _validate_runtime_tracking(self) -> Self:
            """Confine a derived managed destination to its repository.

            Returns:
                The validated artifact declaration.

            Raises:
                ValueError: If a path escapes its repository.

            """
            if (
                self.path.is_absolute()
                or ".." in self.path.parts
                or self.path == Path()
            ):
                msg = f"managed artifact path must be repository-relative: {self.path}"
                raise ValueError(msg)
            return self

    class GitignoreRenderContext(FlextInfraConfigModelsContract.ConfigContract):
        """Profile-filtered input consumed by the Git ignore template."""

        gitignore_sections: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec
            ],
            m.Field(min_length=1, description="Applicable Git ignore sections"),
        ]

    class GitignoreRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed, profile-filtered input for the generated Git ignore file."""

        gitignore_sections: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec
            ],
            m.Field(
                min_length=1,
                description="Canonical ignore sections applicable to one profile",
            ),
        ]

    class StaticTextRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Empty typed context for a variable-free governed text template."""


__all__: list[str] = ["FlextInfraConfigModelsTemplates"]
