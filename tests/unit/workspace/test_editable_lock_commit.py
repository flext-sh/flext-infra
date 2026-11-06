"""Editable sources must sit at the commit their target lock pins (flext-92rpb).

Operator decision recorded on flext-92rpb: "Require tip = lock". An editable
tree at another commit renders projections, or installs code, that the
locked environment lacks; both the rendering-engine precondition and the
``make setup FLEXT=<path>`` binding refuse it, naming both commits.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, workspace
from flext_infra.codegen import FlextInfraCodegenPreconditions
from tests import c, m, tm, u


class TestsEditableLockCommit:
    """Public verdicts bind an editable tree's HEAD to the locked commit."""

    @staticmethod
    def _head(repo_root: Path) -> str:
        return tm.ok(
            u.Infra.git_resolve_commit(
                m.Infra.GitCommitishRequest(
                    repo_root=repo_root, commitish=c.Infra.GIT_HEAD
                ),
            ),
        ).oid

    @staticmethod
    def _write_lock(root: Path, name: str, version: str, source: str) -> Path:
        lock = root / c.Infra.UV_LOCK_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                lock,
                (
                    "version = 1\n\n[[package]]\n"
                    f'name = "{name}"\nversion = "{version}"\n'
                    f'source = {{ git = "{source}" }}\n'
                ),
            ),
        )
        return lock

    def test_editable_source_must_be_the_locked_commit(self, tmp_path: Path) -> None:
        """A real Git tree ahead of its pin fails naming both SHAs, at it passes."""
        source = u.Tests.git_repository(tmp_path, "member")
        locked = self._head(source)
        u.Tests.git_run(source, "commit", "--allow-empty", "-qm", "ahead of lock")
        head = self._head(source)
        lock = self._write_lock(
            tmp_path, "fixture-member", "1.0.0", f"git+{source.as_uri()}#{locked}"
        )
        environment = workspace.FlextInfraWorkspaceEnvironment
        verdict = environment.editable_sources_at_lock(lock, {"Fixture_Member": source})
        tm.fail(verdict, has=head)
        tm.fail(verdict, has=locked)
        tm.fail(verdict, has="make upg")
        self._write_lock(
            tmp_path, "fixture-member", "1.0.0", f"git+{source.as_uri()}#{head}"
        )
        tm.ok(environment.editable_sources_at_lock(lock, {"fixture-member": source}))

    def test_rendering_engine_refuses_an_editable_engine_off_the_lock(
        self, tmp_path: Path
    ) -> None:
        """The executing editable engine renders only for the commit the target pins.

        Premise: the test runtime installs this repository editable, as
        ``make setup`` does, so the running engine is an editable tree.
        """
        name = config.Infra.codegen.infra_repository.distribution
        matches = u.installed_distributions(name=name)
        tm.that(len(matches), eq=1)
        raw = matches[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        tm.that(raw is not None, eq=True)
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(str(raw))
        tm.that(receipt.dir_info is not None and receipt.dir_info.editable, eq=True)
        engine = workspace.FlextInfraWorkspaceEnvironment.editable_root(receipt)
        head = self._head(engine)
        target = u.Tests.git_repository(tmp_path, "consumer")
        tm.ok(
            u.Cli.atomic_write_text_file(
                target / c.PYPROJECT_FILENAME,
                '[project]\nname = "consumer"\nversion = "1.0.0"\n',
            ),
        )
        version = matches[0].version
        foreign = self._head(target)
        self._write_lock(target, name, version, f"git+{engine.as_uri()}#{foreign}")
        refused = FlextInfraCodegenPreconditions.rendering_engine(target)
        tm.fail(refused, has=head)
        tm.fail(refused, has=foreign)
        self._write_lock(target, name, version, f"git+{engine.as_uri()}#{head}")
        tm.ok(FlextInfraCodegenPreconditions.rendering_engine(target))
