# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/scaffold
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigScaffold:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ScaffoldBuildSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def backend(self) -> t.NonEmptyStr: ...
        @property
        def requirements(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class ScaffoldConfigBaseSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr: ...
        @property
        def module(self) -> t.NonEmptyStr: ...
        @property
        def class_name(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class ScaffoldProjectSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def readme(self) -> t.NonEmptyStr: ...
        @property
        def supported_licenses(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def classifiers(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def keywords(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def copyright_year(self) -> int: ...
        @property
        def dev(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def retired_dev(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def required_flext_dev(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def config_bases(self) -> tuple[p.Infra.ScaffoldConfigBaseSpec, ...]: ...

    @runtime_checkable
    class ScaffoldPingExampleSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def command_name(self) -> t.NonEmptyStr: ...
        @property
        def help_text(self) -> t.NonEmptyStr: ...
        @property
        def success_message(self) -> t.NonEmptyStr: ...
        @property
        def enabled_default(self) -> bool: ...
        @property
        def reply(self) -> t.NonEmptyStr: ...
        @property
        def disabled_reply(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class ScaffoldGitignoreSectionSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def patterns(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def profiles(self) -> tuple[c.Infra.MakeProfile, ...]: ...

    @runtime_checkable
    class ScaffoldDependencyProfileSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def upstream(self) -> t.NonEmptyStr: ...
        @property
        def project(self) -> t.NonEmptyStr | None: ...
        @property
        def runtime(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def codegen(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class ScaffoldSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def build(self) -> p.Infra.ScaffoldBuildSpec: ...
        @property
        def project(self) -> p.Infra.ScaffoldProjectSpec: ...
        @property
        def ping_example(self) -> p.Infra.ScaffoldPingExampleSpec: ...
        @property
        def gitignore_sections(
            self,
        ) -> tuple[p.Infra.ScaffoldGitignoreSectionSpec, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigScaffold",
]
