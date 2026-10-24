"""Generated Make rejects credential-bearing Git rewrites without disclosure.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, m, tm, u
from tests.unit.codegen import TestsFlextInfraConformSupport

pytestmark = pytest.mark.slow


class TestsFlextInfraMakeCredentialRedaction:
    """Exercise native Git configuration and generated public Make targets."""

    @staticmethod
    @pytest.mark.parametrize("verb", ["setup", "upg", "status"])
    def test_credential_rewrite_is_rejected_before_effects_without_disclosure(
        tmp_path: Path,
        verb: str,
    ) -> None:
        """A fixture-owned global rewrite never reaches output or an installer."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        global_config = tmp_path / "fixture-global.gitconfig"
        credential = "fixture-only-password-for-redaction"
        username = "fixture-only-git-user"
        credential_url = f"https://{username}:{credential}@github.com/"
        environment = {
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_CONFIG_NOSYSTEM": c.ParserBooleanToken.ONE,
            "GITHUB_TOKEN": "fixture-only-explicit-token",
        }
        configured = tm.ok(
            u.Cli.run_raw(
                (
                    c.Infra.GIT,
                    "config",
                    "--global",
                    f"url.{credential_url}.insteadOf",
                    "https://github.com/",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )
        tm.ok(u.Cli.process_succeeded(configured.outcome))
        before = TestsFlextInfraConformSupport.project_tree(root)
        configured_bytes = global_config.read_bytes()

        rejected = tm.ok(
            u.Tests.run_isolated_make(
                ("--no-print-directory", verb),
                cwd=root,
                env=environment,
            ),
        )

        tm.that(rejected.outcome.raw_return_code, eq=2)
        diagnostic = rejected.stdout + rejected.stderr
        tm.that(
            diagnostic,
            has="embeds credentials in a GitHub URL rewrite",
            lacks=(
                credential,
                username,
                credential_url,
                environment["GITHUB_TOKEN"],
            ),
        )
        tm.that(
            TestsFlextInfraConformSupport.project_tree(root),
            eq=before,
        )
        tm.fail((root / c.Infra.ENVIRONMENT_DIRECTORY).exists())
        tm.that(global_config.read_bytes(), eq=configured_bytes)
