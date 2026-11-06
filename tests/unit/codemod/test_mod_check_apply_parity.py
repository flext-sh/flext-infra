"""Check, dry-run and apply of ``refactor mod`` agree on rule validity and naming.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraCli
from tests import c, t, tm, u


class TestsFlextInfraModCheckApplyParity:
    """Drive the public ``refactor mod`` route in inspection and apply modes."""

    _RULE_ID = "parity-demo"

    @classmethod
    def _declare_catalog(cls, root: Path, *, invalid_fixture: bool) -> None:
        """Declare one local rule, optionally with a fixture its rule cannot satisfy."""
        u.Tests.declare_rules(
            root,
            {
                cls._RULE_ID: (
                    f"id: {cls._RULE_ID}\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: parity_call($A)\nfix: parity_done($A)\n"
                )
            },
        )
        if not invalid_fixture:
            return
        config_path = root / c.Infra.CODEMOD_CONFIG_RELPATH
        tests = config_path.parent / "tests"
        tm.ok(u.Cli.ensure_dir(tests))
        tm.ok(
            u.Cli.atomic_write_text_file(
                config_path,
                f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
                f"ruleDirs:\n  - {c.Cli.RULES_DIR_NAME}\n"
                "testConfigs:\n  - testDir: tests\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tests / f"{cls._RULE_ID}-test.yml",
                f"id: {cls._RULE_ID}\nvalid:\n  - other(1)\n"
                "invalid:\n  - unrelated(1)\n",
            )
        )

    @staticmethod
    def _run(
        root: Path,
        capsys: t.Tests.CaptureFixture[str],
        *options: str,
    ) -> tuple[int, str]:
        """Invoke the public application route and capture its console.

        Returns:
            The exit code and the combined console text.

        """
        exit_code = FlextInfraCli.infra_main([
            "refactor",
            "mod",
            "--repository-root",
            str(root),
            *options,
        ])
        capture = capsys.readouterr()
        return exit_code, capture.out + capture.err

    @staticmethod
    def _split_module_workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Provision a project owning one mechanically split numbered module.

        Returns:
            The repository root and the split module the naming campaign elects.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = "ExampleModelsProjectMetadata"
        source = package / f"{owner.lower()}_part_01.py"
        tm.ok(
            u.Cli.atomic_write_text_file(source, f"class {owner}Contract:\n    pass\n")
        )
        return root, source

    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize("mode", ["--check", "--apply"])
    def test_invalid_rule_fixture_stops_every_mode_before_the_scan(
        self,
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
        mode: str,
    ) -> None:
        """Inspection fails on a rule whose fixture fails, exactly like apply."""
        self._declare_catalog(mod_workspace, invalid_fixture=True)
        sample = mod_workspace / "sample.py"
        before = sample.read_bytes()
        exit_code, console = self._run(mod_workspace, capsys, mode)
        tm.that(exit_code, ne=0, msg=console)
        tm.that(console, has="mod: validate ast-grep rule fixtures")
        tm.that(console, lacks="mod: ast-grep scan providers")
        tm.that(sample.read_bytes(), eq=before)

    @c.Tests.MARK.slow
    def test_check_plans_and_lists_the_module_naming_campaign(
        self,
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """Inspection reports each planned module rename and publishes nothing."""
        root, source = self._split_module_workspace(tmp_path)
        self._declare_catalog(root, invalid_fixture=False)
        original = source.read_bytes()
        exit_code, console = self._run(root, capsys, "--check")
        tm.that(exit_code, ne=0, msg=console)
        tm.that(console, has="mod: rename module")
        tm.that(console, has=source.name)
        tm.that(console, has="1 pending module rename(s)")
        tm.that(source.read_bytes(), eq=original)

    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize("mode", ["--check", "--apply"])
    def test_rule_selection_does_not_plan_module_naming(
        self,
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
        mode: str,
    ) -> None:
        """One selected rule runs alone: the unselected naming campaign stays out."""
        root, source = self._split_module_workspace(tmp_path)
        self._declare_catalog(root, invalid_fixture=False)
        original = source.read_bytes()
        exit_code, console = self._run(root, capsys, mode, "--rule-ids", self._RULE_ID)
        tm.that(console, lacks="mod: rename module", msg=console)
        tm.that(console, lacks="pending module rename(s)")
        tm.that(source.read_bytes(), eq=original)
        if mode == "--check":
            tm.that(exit_code, eq=0, msg=console)
