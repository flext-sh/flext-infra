"""Declared costly distributions defer the facade-composed classes that import them.

The consumer's own provisioned environment maps each declared distribution to
the import packages it installs; the generated initializer gives a stand-in to
exactly the class exports of a module importing one of them at module scope that
a facade composes by MRO. Every other class export stays a plain lazy export.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodegenLazyInitDeferredCapability:
    """The initializer defers the composed export with its in-package members."""

    _DEFERRED_BLOCK = (
        "    deferred_members={\n"
        '        "FlextDemoCapabilityHeavy": (\n'
        '            "TIMEOUT_ERROR",\n'
        '            "heavy_value",\n'
        '            "base_value",\n'
        "        ),\n"
        "    },\n"
    )

    @staticmethod
    def _initializer(root: Path) -> str:
        """Read the capability family's generated initializer.

        Returns:
            The initializer source.

        """
        return (
            root
            / c.Infra.DEFAULT_SRC_DIR
            / "flext_demo"
            / "_capability"
            / c.Infra.INIT_PY
        ).read_text(encoding=c.DEFAULT_ENCODING)

    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_declared_distribution_defers_its_importing_export(
        self,
        deferred_capability_project: Path,
    ) -> None:
        """Only the facade-composed export of the importing module is deferred."""
        root = deferred_capability_project
        u.Tests.override_repository_declaration(
            root, {"deferred_distributions": ["requests"]}
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)
        tm.that(self._initializer(root), has=self._DEFERRED_BLOCK)

    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_class_outside_every_facade_stays_a_plain_lazy_export(
        self,
        deferred_capability_project: Path,
    ) -> None:
        """A third-party-based class of the heavy module gets no stand-in."""
        root = deferred_capability_project
        u.Tests.override_repository_declaration(
            root, {"deferred_distributions": ["requests"]}
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        initializer = self._initializer(root)
        tm.that(initializer, has="FlextDemoCapabilityClient")
        tm.that(initializer, lacks='"FlextDemoCapabilityClient": (')

    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_undeclared_project_defers_nothing(
        self,
        deferred_capability_project: Path,
    ) -> None:
        """Without a declaration the initializer keeps every export eager."""
        root = deferred_capability_project
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(self._initializer(root), lacks="deferred_members")

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_declared_distribution_without_import_package_fails(
        deferred_capability_project: Path,
    ) -> None:
        """A declared distribution the environment does not install fails loud."""
        root = deferred_capability_project
        u.Tests.override_repository_declaration(
            root, {"deferred_distributions": ["flext-absent-distribution"]}
        )
        with u.Tests.raises(ValueError, match="install no import package"):
            u.Tests.create_lazy_init_service(root).plan_files()
