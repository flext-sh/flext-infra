"""Contract test for the release policy owner.

The Gitleaks policy is a codegen template projected into every repository.
Build constraints are rendered at release time from the typed config SSOT
(``config.Infra.release.build_constraints``) by the release policy phase —
no repository carries a ``config/build-constraints.txt`` projection
(flext-gufl8).
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config
from tests import u


class TestsReleasePolicyOwner:
    """Policy sources: one projected template, one config-rendered policy."""

    def test_policy_sources_resolve_from_the_checkout_in_use(self) -> None:
        """The Gitleaks template must exist for the current checkout.

        This holds in a plain clone and must equally hold in a linked worktree,
        where the repository sits deeper in the filesystem.
        """
        template_root = u.Tests.release_policy_root()

        tm.that(
            (template_root / f"{c.Infra.RELEASE_GITLEAKS_CONFIG_PATH}.j2").is_file(),
            eq=True,
        )

    def test_policy_root_is_the_packaged_template_root(self) -> None:
        """The owner is the packaged template tree, not an ambient parent."""
        expected = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
        )
        tm.that(u.Tests.release_policy_root(), eq=expected)

    def test_build_constraints_render_every_configured_pin(self) -> None:
        """The rendered constraints carry each pin exactly as config declares.

        Every pin appears as ``name==version`` with one ``--hash=sha256:`` line
        per digest, so ``uv build --require-hashes`` accepts precisely the
        declared backend and nothing else.
        """
        rendered = u.Tests.release_build_constraints_text()

        for pin in config.Infra.release.build_constraints:
            tm.that(rendered, has=f"{pin.name}=={pin.version} \\")
            for digest in pin.hashes:
                tm.that(rendered, has=f"--hash=sha256:{digest}")
        tm.that(
            rendered.count("--hash=sha256:"),
            eq=sum(len(pin.hashes) for pin in config.Infra.release.build_constraints),
        )
        tm.that(rendered.endswith("\n"), eq=True)
        tm.that(rendered, lacks="\\\n\n")

    def test_build_constraints_render_is_deterministic(self) -> None:
        """Identical config pins render byte-identical policy bytes.

        The release policy snapshot digest is stable across renders, so
        reports stay comparable across runs of the same config.
        """
        tm.that(
            u.Tests.release_build_constraints_text(),
            eq=u.Tests.release_build_constraints_text(),
        )

    def test_no_template_projects_build_constraints_into_repositories(self) -> None:
        """Extermination guard: the projection must never come back.

        ``config/build-constraints.txt`` in a repository is residue, not root
        source (operator law, flext-gufl8); the render path owns the bytes.
        """
        destinations = {
            entry.destination for entry in config.Infra.codegen.templates.entries
        }
        tm.that("config/build-constraints.txt" in destinations, eq=False)

    def test_every_repository_receives_the_gitleaks_policy(self) -> None:
        """The projected policy is fully generated in every profile.

        Codegen owns the bytes (``overwrite``), so no repository can drift
        from the fleet policy or lack it.
        """
        entries = {
            entry.destination: entry for entry in config.Infra.codegen.templates.entries
        }
        entry = entries[c.Infra.RELEASE_GITLEAKS_CONFIG_PATH]
        tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))
        tm.that(entry.overwrite, eq=True)
