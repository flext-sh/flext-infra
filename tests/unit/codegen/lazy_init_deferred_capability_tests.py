"""Every class a family facade composes by MRO is a lazy stand-in.

The generated initializer names each facade-composed part a stand-in and lists
no member and no base: the runtime resolves both from the code (root ADR-018
stand-in composition law, rules 2 and 4). The output is the same in a scoped and
an unscoped run, and the fresh stand-in's MRO names the real class's base
objects. A class no facade composes stays a plain lazy export, and a part that
a stand-in cannot represent (rule 5) fails generation by name. A facade of one
tier root
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
        "    deferred_members=(\n"
        '        "FlextDemoCapabilityBase",\n'
        '        "FlextDemoCapabilityHeavy",\n'
        "    ),\n"
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
        tm.that(initializer, lacks="defer_lazy_bases")

    @c.Tests.MARK.slow
    @c.Tests.MARK.remote
    def test_part_binding_no_member_is_not_deferred(
        self,
        deferred_capability_project: Path,
        fixture_tree: p.Tests.FixtureTree,
    ) -> None:
        """A composed class that binds no member stays a plain lazy export."""
        root = deferred_capability_project
        fixture_tree("lazy-deferred-capability-empty-part", destination=root)
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        initializer = self._initializer(root)
        tm.that(initializer, has="FlextDemoCapabilityNamespace")
        tm.that(initializer, has=self._DEFERRED_BLOCK)

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
        tm.that(initializer, has=self._DEFERRED_BLOCK)

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
        source = generated.decode(c.DEFAULT_ENCODING)
        tm.that(source, has='        "ExamplesFlextDemoCapabilityExtra",\n')
        tm.that(source, lacks="defer_lazy_bases")
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
