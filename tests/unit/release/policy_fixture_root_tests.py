"""Contract test for the release policy owner.

The release build phase snapshots ``config/build-constraints.txt`` and
``config/gitleaks-release.toml`` from the repository before the first artifact
build. Both are fleet-wide policies owned by flext-infra as codegen templates
and projected into every generated repository; the release workspace factory
copies the same template bytes so a test workspace carries exactly what a
generated repository carries.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_tests import tm
from tests import u


class TestsReleasePolicyOwner:
    """Policy sources are the packaged templates, projected to every repository."""

    def test_policy_sources_resolve_from_the_checkout_in_use(self) -> None:
        """The templates must exist for the current checkout.

        This holds in a plain clone and must equally hold in a linked worktree,
        where the repository sits deeper in the filesystem.
        """
        template_root = u.Tests.release_policy_root()

        for policy_path in (
            c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH,
            c.Infra.RELEASE_GITLEAKS_CONFIG_PATH,
        ):
            tm.that((template_root / f"{policy_path}.j2").is_file(), eq=True)

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

    def test_build_constraints_render_every_configured_pin(
        self, tmp_path: Path
    ) -> None:
        """The projected constraints carry each pin exactly as config declares it.

        Every pin appears as ``name==version`` with one ``--hash=sha256:`` line
        per digest, so ``uv build --require-hashes`` accepts precisely the
        declared backend and nothing else.
        """
        workspace = u.Tests.create_release_workspace(tmp_path)
        rendered = (workspace / c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH).read_text(
            encoding="utf-8"
        )

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

    def test_every_repository_receives_both_policies(self) -> None:
        """Each policy the build phase reads is a fully generated projection.

        Every profile receives it and codegen owns the bytes (``overwrite``),
        so no repository can drift from the fleet policy or lack it.
        """
        entries = {
            entry.destination: entry for entry in config.Infra.codegen.templates.entries
        }
        for policy_path in (
            c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH,
            c.Infra.RELEASE_GITLEAKS_CONFIG_PATH,
        ):
            entry = entries[policy_path]
            tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))
            tm.that(entry.overwrite, eq=True)
