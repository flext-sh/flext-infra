# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/scaffold
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsConfigScaffold:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ScaffoldBuildSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def backend(self) -> t.NonEmptyStr:
            """PEP 517 backend."""
            ...

        @property
        def requirements(self) -> tuple[t.NonEmptyStr, ...]:
            """Build-system requirements."""
            ...

    @runtime_checkable
    class ScaffoldConfigBaseSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr:
            """Distribution owning the base."""
            ...

        @property
        def module(self) -> t.NonEmptyStr:
            """Import module exposing the base."""
            ...

        @property
        def class_name(self) -> t.NonEmptyStr:
            """Config base class name."""
            ...

    @runtime_checkable
    class ScaffoldProjectSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def readme(self) -> t.NonEmptyStr:
            """PEP 621 readme path."""
            ...

        @property
        def supported_licenses(self) -> tuple[t.NonEmptyStr, ...]:
            """Licenses with complete templates."""
            ...

        @property
        def classifiers(self) -> tuple[t.NonEmptyStr, ...]:
            """Default PyPI classifiers."""
            ...

        @property
        def keywords(self) -> tuple[t.NonEmptyStr, ...]:
            """Default project keywords."""
            ...

        @property
        def copyright_year(self) -> int:
            """Structural member projected from the owning model.

            LICENSE/NOTICE year for existing-tree ProjectSpec. Override
            scaffold.project.copyright_year; gen must not use the clock.
            """
            ...

        @property
        def dev(self) -> tuple[t.NonEmptyStr, ...]:
            """Canonical development and validation requirements."""
            ...

        @property
        def retired_dev(self) -> tuple[t.NonEmptyStr, ...]:
            """Development distributions retired from managed groups."""
            ...

        @property
        def required_flext_dev(self) -> tuple[t.NonEmptyStr, ...]:
            """Development suppliers required only by internal FLEXT projects."""
            ...

        @property
        def config_bases(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldConfigBaseSpec, ...]:
            """Structural member projected from the owning model.

            Config base classes in precedence order; a project composes the first
            one whose distribution it depends on.
            """
            ...

    @runtime_checkable
    class ScaffoldPingExampleSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def command_name(self) -> t.NonEmptyStr:
            """Public CLI command."""
            ...

        @property
        def help_text(self) -> t.NonEmptyStr:
            """Public CLI command help."""
            ...

        @property
        def success_message(self) -> t.NonEmptyStr:
            """CLI success message."""
            ...

        @property
        def enabled_default(self) -> bool:
            """Default runtime enablement."""
            ...

        @property
        def reply(self) -> t.NonEmptyStr:
            """Enabled ping response."""
            ...

        @property
        def disabled_reply(self) -> t.NonEmptyStr:
            """Disabled ping response."""
            ...

    @runtime_checkable
    class ScaffoldGitignoreSectionSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Section heading."""
            ...

        @property
        def patterns(self) -> tuple[t.NonEmptyStr, ...]:
            """Ignored path patterns."""
            ...

        @property
        def profiles(self) -> tuple[c.Infra.MakeProfile, ...]:
            """Structural member projected from the owning model.

            Make profiles this section applies to; empty means every profile
            (universal). Sections that only make sense at the superproject root
            (subproject-directory allowlists, workspace manifest, submodule/Beads
            coordination) declare [workspace] so subprojects and standalone projects
            never receive the phantom entries.
            """
            ...

    @runtime_checkable
    class ScaffoldDependencyProfileSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def upstream(self) -> t.NonEmptyStr:
            """Supported upstream facade package."""
            ...

        @property
        def project(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Distribution receiving additional requirements; unset selects the shared
            upstream profile.
            """
            ...

        @property
        def runtime(self) -> tuple[t.NonEmptyStr, ...]:
            """Runtime requirements."""
            ...

        @property
        def codegen(self) -> tuple[t.NonEmptyStr, ...]:
            """Code-generation requirements."""
            ...

    @runtime_checkable
    class ScaffoldSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_stems(self) -> tuple[t.NonEmptyStr, ...]:
            """Required component stems in every production facade family."""
            ...

        @property
        def auxiliary_stems(self) -> tuple[t.NonEmptyStr, ...]:
            """Required component stems in every auxiliary facade family."""
            ...

        @property
        def build(self) -> FlextInfraProtocolsConfigScaffold.ScaffoldBuildSpec:
            """Build-system policy."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsConfigScaffold.ScaffoldProjectSpec:
            """Project metadata and dependency policy."""
            ...

        @property
        def ping_example(
            self,
        ) -> FlextInfraProtocolsConfigScaffold.ScaffoldPingExampleSpec:
            """Functional scaffold example."""
            ...

        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldGitignoreSectionSpec, ...]:
            """Generated Git ignore sections."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigScaffold",
]
