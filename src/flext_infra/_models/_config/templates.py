"""Managed file and template entry specification models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import cached_property
from keyword import iskeyword
from pathlib import Path
from typing import Annotated, Literal, Self

import flext_core
from flext_cli import m, u

from flext_infra import c, t
from flext_infra._models._config.contract import FlextInfraModelsConfigContract
from flext_infra._models._config.scaffold import FlextInfraModelsConfigScaffold


class FlextInfraModelsConfigTemplates:
    """Managed file and template entry specification models."""

    class CodegenVscodeSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Typed editor declarations shared by target and artifact planning."""

        model_config = m.ConfigDict(extra="forbid")

        settings: Annotated[
            t.Infra.SettingsPairs,
            m.Field(description="Ordered VS Code key/value pairs; the last key wins"),
        ] = ()
        runtime_environment_token: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Declared generation token replaced by the topology-owned "
                    "environment path, relative to the opened workspace folder"
                ),
            ),
        ] = None
        map_union_settings: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(description="VS Code objects union-merged over project settings"),
        ] = m.Field(
            default_factory=flext_core.u.empty(Mapping[str, t.JsonMapping]),
            validate_default=True,
        )

        stripped_keys: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "VS Code keys actively stripped from the settings projection "
                    "because they conflict with a pyrightconfig.json/pyproject.toml "
                    "owner (Pylance settingsNotOverridable)."
                ),
            ),
        ] = ()

        stripped_map_keys: Annotated[
            Mapping[str, tuple[str, ...]],
            m.Field(description="Retired keys inside language-specific setting maps"),
        ] = m.Field(
            default_factory=flext_core.u.empty(Mapping[str, tuple[str, ...]]),
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
        FlextInfraModelsConfigContract.ConfigContract,
    ):
        """Portable editor overrides extracted from one captured document."""

        values: Annotated[
            t.JsonMapping,
            m.Field(
                description="Minimal typed codegen.vscode declaration overrides",
            ),
        ]

    class CodegenLayerProjection(FlextInfraModelsConfigContract.ConfigContract):
        """An owned declaration delta projected into one elected config layer."""

        path: Annotated[Path, m.Field(description="Exact target config layer")]
        values: Annotated[
            t.JsonMapping,
            m.Field(description="JSON-compatible declaration fragment"),
        ]

    class ConfigDocumentInputs(FlextInfraModelsConfigContract.ConfigContract):
        """One composed F.yaml document with its consulted physical sources."""

        values: Annotated[
            t.JsonMapping,
            m.Field(description="Strictly parsed and ordered configuration document"),
        ]
        sources: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Exact physical files consulted by this document",
            ),
        ] = ()

    class ManagedFileOwnership(FlextInfraModelsConfigContract.ConfigContract):
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
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Dotted sections rendered by the canonical owner"),
        ] = ()
        preserve_project_keys: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Authored PEP 621 project keys retained on merge"),
        ] = ()
        overwrite_project_keys: Annotated[
            tuple[t.NonEmptyStr, ...],
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
                msg = (
                    "project keys have competing owners: "
                    f"{', '.join(sorted(competing))}"
                )
                raise ValueError(msg)
            return self

        @m.computed_field
        @property
        def managed_tool_tables(self) -> tuple[str, ...]:
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

    class TemplateDeclarationSpec(FlextInfraModelsConfigContract.ConfigContract):
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
        source_package: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Explicit original package owner of a resource declaration"
                ),
            ),
        ] = None
        source_closure: Annotated[
            tuple[Path, ...],
            m.Field(description="Complete package-relative resource source closure"),
        ] = ()
        enforce: Annotated[
            t.Infra.EnforcementIds,
            m.Field(
                description=(
                    "Enforcement law ids the generated projection itself enforces"
                ),
            ),
        ] = ()
        requires_artifacts: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Catalog destination keys required by this artifact"),
        ] = ()
        profiles: Annotated[
            tuple[c.Infra.MakeProfile, ...],
            m.Field(min_length=1, description="Profiles that consume the artifact"),
        ]
        ownership: Annotated[
            FlextInfraModelsConfigTemplates.ManagedFileOwnership | None,
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
        bootstrap_distribution: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Executor whose local dependency closure this artifact binds"
                )
            ),
        ] = None

        @m.field_validator("bootstrap_distribution")
        @classmethod
        def validate_bootstrap_distribution(cls, value: str | None) -> str | None:
            """Validate the declared executor's canonical distribution identity.

            Returns:
                The canonical distribution identity, or None when undeclared.

            """
            return (
                None
                if value is None
                else t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(value)
            )

        @m.field_validator("source_package")
        @classmethod
        def validate_source_package(cls, value: str | None) -> str | None:
            """Require a qualified Python package identity without importing it.

            Returns:
                The explicit package identity, or the own-package selection.

            Raises:
                ValueError: If the identity contains an invalid package component.

            """
            if value is not None and any(
                not part.isidentifier() or iskeyword(part) for part in value.split(".")
            ):
                msg = f"resource source_package must be a qualified package: {value}"
                raise ValueError(msg)
            return value

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
            if (
                self.source_package is not None or self.source_closure
            ) and self.source_kind != "resource":
                msg = "source_package and source_closure require a resource declaration"
                raise ValueError(msg)
            full_ownership = (
                self.ownership is not None and self.ownership.policy == "full"
            )
            if self.bootstrap_distribution is not None and (
                self.source_kind != "template"
                or self.source is None
                or not full_ownership
                or self.profiles != (c.Infra.MakeProfile.WORKSPACE,)
            ):
                msg = "bootstrap requires a full-owned workspace template"
                raise ValueError(msg)
            if self.source_kind == "resource" and (
                self.source is None
                or self.source_package is None
                or self.source not in self.source_closure
                or not full_ownership
            ):
                msg = (
                    "resource requires an explicit package, source closure and "
                    "full managed ownership"
                )
                raise ValueError(msg)
            if len(set(self.source_closure)) != len(self.source_closure) or any(
                path.is_absolute() or ".." in path.parts or path == Path()
                for path in self.source_closure
            ):
                msg = (
                    "resource source closure must contain unique package-relative paths"
                )
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
            """Confine the destination supplied by its catalog key.

            Returns:
                The entry with a repository-relative destination.

            Raises:
                ValueError: If the destination escapes the repository root.

            """
            path = Path(self.destination)
            if path.is_absolute() or ".." in path.parts or path == Path():
                msg = f"artifact destination must be root-relative: {path}"
                raise ValueError(msg)
            return self

    class TemplatesSpec(FlextInfraModelsConfigContract.ConfigContract):
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
                FlextInfraModelsConfigTemplates.TemplateDeclarationSpec,
            ],
            m.Field(
                alias="entries",
                description="Ordered template bodies keyed by destination",
            ),
        ]

        @cached_property
        def entries(
            self,
        ) -> tuple[FlextInfraModelsConfigTemplates.TemplateEntrySpec, ...]:
            """Expose the typed consumer view, validated once per catalog instance."""
            return tuple(
                FlextInfraModelsConfigTemplates.TemplateEntrySpec.model_validate({
                    **dict(declaration),
                    "destination": destination,
                })
                for destination, declaration in self.catalog.items()
            )

        @property
        def artifact_requirements(self) -> Mapping[str, Sequence[str]]:
            """Expose each catalog key's declared artifact dependencies."""
            return {
                destination: declaration.requires_artifacts
                for destination, declaration in self.catalog.items()
            }

        @property
        def bootstrap_entry(self) -> FlextInfraModelsConfigTemplates.TemplateEntrySpec:
            """Require the single declared executor bootstrap artifact.

            Returns:
                The single bootstrap artifact entry.

            Raises:
                ValueError: If zero or multiple bootstrap artifacts are declared.

            """
            entries = tuple(
                entry
                for entry in self.entries
                if entry.bootstrap_distribution is not None
            )
            if len(entries) != 1:
                msg = "setup requires exactly one bootstrap artifact declaration"
                raise ValueError(msg)
            return entries[0]

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
            waves = u.Cli.dag_waves(self.artifact_requirements)
            if waves.failure:
                msg = f"artifact dependencies are invalid: {waves.error}"
                raise ValueError(msg)
            for declaration in self.catalog.values():
                for dependency in declaration.requires_artifacts:
                    required = self.catalog[dependency]
                    unavailable_capability = (
                        required.requires_beads and not declaration.requires_beads
                    ) or (
                        required.requires_release_protocol
                        and not declaration.requires_release_protocol
                    )
                    if (
                        not set(declaration.profiles) <= set(required.profiles)
                        or required.ownership is None
                        or unavailable_capability
                    ):
                        msg = (
                            f"artifact dependency is not always available: {dependency}"
                        )
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

    class GitignoreRenderContext(FlextInfraModelsConfigContract.ConfigContract):
        """Profile-filtered input consumed by the Git ignore template."""

        ignore_sections: Annotated[
            tuple[FlextInfraModelsConfigScaffold.ScaffoldGitignoreSectionSpec, ...],
            m.Field(min_length=1, description="Applicable Git ignore sections"),
        ]

    class GitignoreRenderSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Typed, profile-filtered input for the generated Git ignore file."""

        ignore_sections: Annotated[
            tuple[FlextInfraModelsConfigScaffold.ScaffoldGitignoreSectionSpec, ...],
            m.Field(
                min_length=1,
                description="Canonical ignore sections applicable to one profile",
            ),
        ]

    class StaticTextRenderSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Empty typed context for a variable-free governed text template."""


__all__: list[str] = ["FlextInfraModelsConfigTemplates"]
