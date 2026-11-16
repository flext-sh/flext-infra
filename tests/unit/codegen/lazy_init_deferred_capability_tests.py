"""Observable outcomes of deferring every class a family facade composes.

A composed part whose base is a third-party or builtin type, that flattens a
base around a routed one, or that a stand-in cannot represent (root ADR-018
stand-in composition law, rule 5), fails generation by name. A base another
package publishes is shared by its import route: a fresh import gives the
stand-in the real class's base objects (rule 4), and a scoped run renders the
same bytes as the unscoped one.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u


class TestsFlextInfraCodegenLazyInitDeferredCapability:
    """Deferral reports unrepresentable parts and shares published bases."""

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
        ("kind", "defect"),
        [
            ("dunder", "dunder __repr__"),
            ("slots", "dunder __slots__"),
            ("field", "field-like annotated attribute base_limit"),
            ("decorator", "decorator computed_field on base_total"),
            ("super", "zero-argument super() in base_name"),
            ("isinstance", "isinstance(..., FlextDemoCapabilityBase) in base_is_self"),
            ("protocol", "base Protocol makes it a Protocol namespace"),
            ("metaclass", "metaclass ABCMeta"),
        ],
    )
    def test_part_a_stand_in_cannot_represent_fails(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
        kind: str,
        defect: str,
    ) -> None:
        """A part whose construct a stand-in would lose fails generation by name."""
        root = deferred_capability_project
        fixture_tree(
            f"lazy-deferred-capability-unrepresentable-{kind}", destination=root
        )
        tm.fail(
            u.Tests.create_lazy_init_service(root).plan_files(),
            has=(
                "facade part flext_demo._capability.base.FlextDemoCapabilityBase "
                f"cannot be a stand-in: {defect}; fix:"
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
        "fixture",
        [
            "lazy-deferred-capability-ancestor-base",
            "lazy-deferred-capability-ancestor-letter",
            "lazy-deferred-capability-installed-base",
        ],
    )
    def test_ancestor_package_base_is_shared_by_its_import_route(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
        fixture: str,
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
    def test_ancestor_attribute_base_is_shared_by_its_root_route(
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
    ) -> None:
        """An attribute of a published ancestor class is shared as named."""
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-examples-facade", destination=root)
        fixture_tree("lazy-deferred-capability-ancestor-dotted", destination=root)
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)
        source = (
            root / c.Infra.DIR_EXAMPLES / "_capability" / c.Infra.INIT_PY
        ).read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            source,
            has=(
                '"ExamplesFlextDemoCapabilityExtra": '
                '(("flext_demo", "FlextDemoUtilities.Demo"),),'
            ),
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
