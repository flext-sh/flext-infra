"""Every class a family facade composes by MRO is a lazy stand-in.

The generated initializer gives a stand-in to each facade-composed part with
its in-package members. A class no facade composes stays a plain lazy export,
and a composed part whose base is a third-party type fails generation by name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u


class TestsFlextInfraCodegenLazyInitDeferredCapability:
    """The initializer defers every composed part with its in-package members."""

    _DEFERRED_BLOCK = (
        "    deferred_members={\n"
        '        "FlextDemoCapabilityBase": ("base_value",),\n'
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
    def test_every_facade_part_is_deferred(
        self,
        deferred_capability_project: Path,
    ) -> None:
        """Each part the facade composes gets a stand-in, with no declaration."""
        root = deferred_capability_project
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)
        tm.that(self._initializer(root), has=self._DEFERRED_BLOCK)

    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_class_outside_every_facade_stays_a_plain_lazy_export(
        self,
        deferred_capability_project: Path,
    ) -> None:
        """A third-party-based class no facade composes gets no stand-in."""
        root = deferred_capability_project
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        initializer = self._initializer(root)
        tm.that(initializer, has="FlextDemoCapabilityClient")
        tm.that(initializer, lacks='"FlextDemoCapabilityClient": (')

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_composed_part_with_third_party_base_fails(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
    ) -> None:
        """A facade-composed part that cannot be deferred fails generation."""
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-foreign-base", destination=root)
        with u.Tests.raises(ValueError, match="not a class of its package"):
            u.Tests.create_lazy_init_service(root).plan_files()
