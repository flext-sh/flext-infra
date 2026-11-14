"""Every class a family facade composes by MRO is a lazy stand-in.

The generated initializer gives a stand-in to each facade-composed part with
its in-package members. A base another package's generated initializer publishes
is shared by its import route (root ADR-018 stand-in composition law, rule 4), the
same in a scoped and an unscoped run, and the fresh stand-in's MRO names the real
class's base objects. A class no facade composes stays a plain lazy export, and a
composed part whose base is a third-party or builtin type, or that flattens a base
around a routed one, fails generation by name. A facade of one tier root
(``examples``) that another tier's facade composes stays real, like a public
``src`` facade.

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
        "        ),\n"
        "    },\n"
    )
    _BASES_CALL = (
        "defer_lazy_bases(\n"
        "    __name__,\n"
        "    {\n"
        '        "FlextDemoCapabilityHeavy": ((".", "FlextDemoCapabilityBase"),),\n'
        "    },\n"
        ")\n"
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
        initializer = self._initializer(root)
        tm.that(initializer, has=self._DEFERRED_BLOCK)
        tm.that(initializer, has=self._BASES_CALL)

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
    @c.Tests.MARK.parametrize(
        ("fixture", "base"),
        [
            ("lazy-deferred-capability-foreign-base", "Session"),
            ("lazy-deferred-capability-builtin-base", "type"),
        ],
    )
    def test_composed_part_with_third_party_or_builtin_base_fails(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
        fixture: str,
        base: str,
    ) -> None:
        """A facade-composed part that cannot be deferred fails generation."""
        root = deferred_capability_project
        fixture_tree(fixture, destination=root)
        tm.fail(
            u.Tests.create_lazy_init_service(root).plan_files(),
            has=(
                f"the base {base}, which is neither a class of its package nor "
                "published by a generated FLEXT initializer"
            ),
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    @c.Tests.MARK.parametrize(
        ("fixture", "relation"),
        [
            ("lazy-deferred-capability-flatten-after-route", "follows"),
            ("lazy-deferred-capability-flatten-derived-route", "derives from"),
        ],
    )
    def test_part_flattening_a_base_around_a_route_fails(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
        fixture: str,
        relation: str,
    ) -> None:
        """Flattened members could shadow a routed base, so generation fails."""
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-examples-facade", destination=root)
        fixture_tree(fixture, destination=root)
        tm.fail(
            u.Tests.create_lazy_init_service(root).plan_files(),
            has=(
                "flattens the base ExamplesFlextDemoCapabilityMixin, which "
                f"{relation} a base another package publishes"
            ),
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    @c.Tests.MARK.parametrize(
        ("fixture", "route"),
        [
            (
                "lazy-deferred-capability-ancestor-base",
                ("flext_demo", "FlextDemoUtilities"),
            ),
            ("lazy-deferred-capability-ancestor-letter", ("flext_demo", "u")),
            (
                "lazy-deferred-capability-installed-base",
                (c.Infra.PKG_CORE_UNDERSCORE, "FlextUtilities"),
            ),
        ],
    )
    def test_ancestor_package_base_is_shared_by_its_import_route(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
        fixture: str,
        route: tuple[str, str],
    ) -> None:
        """A base another package publishes is shared as the source imports it.

        The source reads it by class name or through the published letter, from
        a package of this run's plans or from an installed distribution. A
        scoped run renders the same bytes as the unscoped one, and a fresh
        import gives the stand-in the real class's base objects.
        """
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-examples-facade", destination=root)
        fixture_tree(fixture, destination=root)
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)
        initializer = root / c.Infra.DIR_EXAMPLES / "_capability" / c.Infra.INIT_PY
        generated = initializer.read_bytes()
        source = generated.decode(c.DEFAULT_ENCODING)
        tm.that(source, has='"ExamplesFlextDemoCapabilityExtra": ("EXTRA_VALUE",),')
        package, export = route
        tm.that(
            source,
            has=f'"ExamplesFlextDemoCapabilityExtra": (("{package}", "{export}"),),',
        )
        scoped = u.Tests.create_lazy_init_service(root)
        scoped.project_scope_roots = (root,)
        planned = {
            plan.path: plan.desired_content for plan in tm.ok(scoped.plan_files())
        }
        tm.that(planned.get(initializer), eq=generated)
        probe = fixture_tree("lazy-deferred-capability-mro-probe") / "mro_probe.py"
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe.read_text(encoding=c.DEFAULT_ENCODING),
                python_paths=(str(root), str(root / c.Infra.DEFAULT_SRC_DIR)),
            ),
            eq=["True"] * 3,
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_tier_root_facade_composed_by_another_tier_stays_real(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
    ) -> None:
        """An examples facade the tests facade composes is a root, not a part."""
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-tier-roots", destination=root)
        tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        initializer = (root / c.Infra.DIR_EXAMPLES / c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING
        )
        tm.that(initializer, has="ExamplesFlextDemoUtilities")
        tm.that(initializer, lacks='"ExamplesFlextDemoUtilities": (')
