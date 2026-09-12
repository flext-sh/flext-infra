"""Contract test for the release policy owners.

The release build phase renders ``build-constraints.txt`` directly from the
checked-out flext-infra config SSOT into the release policy directory: no
repository ever carries that file. The ``config/gitleaks-release.toml`` policy
stays a codegen template projected into every governed repository; the release
workspace factory copies its exact bytes so a test workspace carries what a
generated repository carries.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config
from tests import u


class TestsReleasePolicyOwner:
    """Policies have exactly one owner and one transport each."""

    def test_build_constraints_template_resolves_from_the_checkout_in_use(self) -> None:
        """The release template must exist for the current checkout.

        This holds in a plain clone and must equally hold in a linked worktree,
        where the repository sits deeper in the filesystem.
        """
        template_root = u.Tests.release_policy_root()
        template = template_root / Path(c.Infra.RELEASE_BUILD_CONSTRAINTS_TEMPLATE).name
        tm.that(template.is_file(), eq=True)

    def test_release_template_root_is_the_release_owned_root(self) -> None:
        """The constraint policy owner is the release template tree."""
        expected_root = (
            Path(__file__).resolve().parents[3] / "src" / "flext_infra" / "release"
        )
        tm.that(u.Tests.release_policy_root(), eq=expected_root / "templates")

    def test_gitleaks_projection_stays_a_managed_repository_file(self) -> None:
        """The Gitleaks policy is a fleet policy projected into every repo.

        Every profile receives it and codegen owns the bytes (``overwrite``),
        so no repository can drift from the fleet policy or lack it.
        """
        entries = {
            entry.destination: entry for entry in config.Infra.codegen.templates.entries
        }
        entry = entries[c.Infra.RELEASE_GITLEAKS_CONFIG_PATH]
        tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))
        tm.that(entry.overwrite, eq=True)

    def test_build_constraints_are_never_a_managed_repository_file(self) -> None:
        """No repository ever carries ``config/build-constraints.txt``.

        The file is neither a managed artifact nor a template destination: the
        release phase owns its bytes, rendered from the config SSOT at snapshot
        time into the release policy directory.
        """
        managed = {
            entry.path.as_posix() for entry in config.Infra.codegen.managed_files
        }
        entries = {
            entry.destination for entry in config.Infra.codegen.templates.entries
        }
        banned = c.Infra.RELEASE_BUILD_CONSTRAINTS_BANNED_PATH
        tm.that(banned not in managed, eq=True)
        tm.that(banned not in entries, eq=True)
