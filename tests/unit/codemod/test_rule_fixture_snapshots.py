"""Rule-test snapshots change only through their explicit refresh, never in mod.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import c, main
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from tests import t, tm, u


class TestsFlextInfraModRuleFixtureSnapshots:
    """Verification rejects snapshot drift; the refresh records it for review."""

    @pytest.mark.parametrize("collection", ["dict", "list"])
    def test_typing_collection_fixes_preserve_runtime_values(
        self,
        tmp_path: Path,
        collection: str,
    ) -> None:
        """Validate real fixes and execute concrete collection/Pydantic contracts."""
        owner = Path(__file__).resolve().parents[3]
        demo = self._owner(tmp_path)
        catalog = self._catalog(tmp_path)
        source_catalog = self._catalog(owner)
        tm.ok(u.Cli.ensure_dir(catalog / "utils"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.CODEMOD_CONFIG_RELPATH,
                "ruleDirs: [rules]\nutilDirs: [utils]\n"
                "testConfigs:\n  - testDir: tests\n",
            ),
        )
        for name in (
            "semantic-type-context",
            "typing-annotated-form",
            "typing-literal-form",
            "typing-module-binding",
            "t-locally-bound",
            f"typing-{collection}-generic",
            f"{collection}-imported-from-typing",
        ):
            relative = Path("utils") / f"{name}.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    catalog / relative,
                    (source_catalog / relative).read_text(encoding="utf-8"),
                ),
            )
        rule_id = (
            "typing-dict-to-mapping-kv"
            if collection == "dict"
            else "typing-list-to-sequence-of"
        )
        rule = catalog / "rules" / f"{rule_id}.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                (source_catalog / "rules" / rule.name).read_text(encoding="utf-8"),
            ),
        )
        for selected_id in (rule_id, f"typing-{collection}-missing-t-import"):
            relative = Path("tests") / f"{selected_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    catalog / relative,
                    (source_catalog / relative).read_text(encoding="utf-8"),
                ),
            )
        rules = (demo, rule)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                rules,
                apply=True,
            ),
        )
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, rules))
        snapshots = tm.ok(u.Cli.yaml_safe_load(self._snapshot(tmp_path, rule_id)))[
            "snapshots"
        ]
        assert isinstance(snapshots, Mapping)
        runtime_consumers = 0
        for snapshot in snapshots.values():
            assert isinstance(snapshot, Mapping)
            fixed = snapshot["fixed"]
            assert isinstance(fixed, str)
            _ = ast.parse(fixed)
            if "class Payload(m.ArbitraryTypesModel):" in fixed:
                outcome = tm.ok(u.Cli.run_raw((sys.executable, "-c", fixed)))
                tm.that(outcome.exit_code, eq=0)
                tm.that(outcome.stderr, eq="")
                runtime_consumers += 1
        tm.that(runtime_consumers, eq=1)

    @pytest.mark.parametrize("suffix", ["", "; value = 1", ";"])
    def test_managed_artifact_sequential_full_source_fixes_parse(
        self,
        tmp_path: Path,
        suffix: str,
    ) -> None:
        """Parse sequential pinned-engine outputs and prove both fixed points."""
        owner = Path(__file__).resolve().parents[3]
        private_import = (
            "from flext_infra._utilities.project_managed_artifacts import "
            "FlextInfraUtilitiesProjectManagedArtifacts"
        )
        source = (
            f"from flext_infra import u\n{private_import}{suffix}\n"
            "result = FlextInfraUtilitiesProjectManagedArtifacts."
            "snapshot_config_sources(root)\n"
        )
        _ = ast.parse(source)
        staged: list[tuple[Path, Path, Path, str]] = []
        for filename, rule_id, expect_fix in (
            (
                "rewire-project-managed-artifacts",
                "rewire-project-managed-artifacts-call",
                True,
            ),
            (
                "remove-project-managed-artifacts-private-import",
                "remove-project-managed-artifacts-private-import",
                not suffix,
            ),
        ):
            root = tmp_path / filename
            demo = self._owner(root)
            rule = self._catalog(root) / "rules" / f"{filename}.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rule,
                    (self._catalog(owner) / "rules" / rule.name).read_text(
                        encoding="utf-8",
                    ),
                ),
            )
            fixture = self._catalog(root) / "tests" / f"{rule_id}-test.yml"
            case = "  - |\n" + "".join(f"    {line}\n" for line in source.splitlines())
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    f"id: {rule_id}\nvalid: []\ninvalid:\n{case}"
                    if expect_fix
                    else f"id: {rule_id}\nvalid:\n{case}invalid: []\n",
                ),
            )
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    root,
                    (demo, rule),
                    apply=True,
                ),
            )
            if expect_fix:
                snapshots = tm.ok(
                    u.Cli.yaml_safe_load(self._snapshot(root, rule_id)),
                )["snapshots"]
                assert isinstance(snapshots, Mapping)
                tm.that(len(snapshots), eq=1)
                snapshot = next(iter(snapshots.values()))
                assert isinstance(snapshot, Mapping)
                fixed = snapshot["fixed"]
                assert isinstance(fixed, str)
                source = fixed
            _ = ast.parse(source)
            staged.append((root, demo, rule, rule_id))
        tm.that(source, has="result = u.Infra.snapshot_config_sources(root)")
        tm.that(private_import in source, eq=bool(suffix))
        for root, demo, rule, rule_id in staged:
            case = "  - |\n" + "".join(f"    {line}\n" for line in source.splitlines())
            fixture = self._catalog(root) / "tests" / f"{rule_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    f"id: {rule_id}\nvalid:\n{case}invalid: []\n",
                ),
            )
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    root,
                    (demo, rule),
                    apply=True,
                ),
            )
            tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(root, (demo, rule)))

    def test_managed_artifact_cutover_preserves_live_export_owner(
        self,
        tmp_path: Path,
    ) -> None:
        """Run the owned rules against the live initializer and consumer fixtures."""
        demo = self._owner(tmp_path)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (demo,),
                apply=True,
            ),
        )
        owner = Path(__file__).resolve().parents[3]
        catalog = self._catalog(owner)
        rules = [demo]
        for filename in (
            "remove-project-managed-artifacts-private-import",
            "rewire-project-managed-artifacts",
        ):
            source_rule = catalog / "rules" / f"{filename}.yml"
            rule = self._catalog(tmp_path) / "rules" / source_rule.name
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rule,
                    source_rule.read_text(encoding="utf-8"),
                ),
            )
            rules.append(rule)
            rule_id = (
                "rewire-project-managed-artifacts-call"
                if filename == "rewire-project-managed-artifacts"
                else filename
            )
            for relative in (
                Path("tests") / f"{rule_id}-test.yml",
                Path("tests")
                / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
                / f"{rule_id}{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}",
            ):
                source = (catalog / relative).read_text(encoding="utf-8")
                if relative.name == f"{filename}-test.yml":
                    initializer = (
                        owner / "src/flext_infra/_utilities/__init__.py"
                    ).read_text(encoding="utf-8")
                    live_case = "  - |\n" + "".join(
                        f"    {line}\n" for line in initializer.splitlines()
                    )
                    source = source.replace("invalid:\n", f"{live_case}invalid:\n")
                destination = self._catalog(tmp_path) / relative
                tm.ok(u.Cli.ensure_dir(destination.parent))
                tm.ok(u.Cli.atomic_write_text_file(destination, source))

        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, tuple(rules)))
        for rule in rules[1:]:
            rule_id = tm.ok(u.Cli.yaml_safe_load(rule))["id"]
            assert isinstance(rule_id, str)
            cases = tm.ok(
                u.Cli.yaml_safe_load(
                    self._catalog(tmp_path) / "tests" / f"{rule_id}-test.yml",
                ),
            )["valid"]
            assert isinstance(cases, list)
            for source in cases:
                assert isinstance(source, str)
                _ = ast.parse(source)
            snapshots = tm.ok(u.Cli.yaml_safe_load(self._snapshot(tmp_path, rule_id)))[
                "snapshots"
            ]
            assert isinstance(snapshots, Mapping)
            fixed_cases = ""
            for snapshot in snapshots.values():
                assert isinstance(snapshot, Mapping)
                fixed = snapshot["fixed"]
                assert isinstance(fixed, str)
                _ = ast.parse(fixed)
                fixed_cases += "  - |\n" + "".join(
                    f"    {line}\n" for line in fixed.splitlines()
                )
            fixture = self._catalog(tmp_path) / "tests" / f"{rule_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    fixture.read_text(encoding="utf-8").replace(
                        "invalid:\n",
                        f"{fixed_cases}invalid:\n",
                    ),
                ),
            )
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, tuple(rules)))

    @staticmethod
    def _catalog(root: Path) -> Path:
        """Return the project's own rule catalog directory under ``root``.

        Returns:
            The directory holding the local ``sgconfig.yml`` the plan reads.

        """
        return root / c.Infra.CODEMOD_CONFIG_RELPATH.parent

    @classmethod
    def _owner(
        cls,
        root: Path,
        *,
        fix: str = "bar($A)",
        invalid: t.StrSequence = ("foo(1)",),
    ) -> Path:
        """Declare one governed rule with its test in the local catalog.

        The catalog sits where the rule plan reads a project's own rules, and
        Git must track it: Git decides which provider a repository governs.

        Returns:
            The resulting ``Path``.

        """
        catalog = cls._catalog(root)
        for directory in (root / "src", catalog / "rules", catalog / "tests"):
            tm.ok(u.Cli.ensure_dir(directory))
        u.Tests.copy_tracked_mise_seeds(root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.CODEMOD_CONFIG_RELPATH,
                "ruleDirs: [rules]\ntestConfigs:\n  - testDir: tests\n",
            ),
        )
        rule = catalog / "rules" / "demo.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                "id: demo\nlanguage: python\nseverity: error\n"
                f"rule:\n  pattern: foo($A)\nfix: {fix}\n",
            ),
        )
        cases = "".join(f"  - {case}\n" for case in invalid)
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalog / "tests" / "demo-test.yml",
                f"id: demo\nvalid:\n  - baz(1)\ninvalid:\n{cases}",
            ),
        )
        # The rule engine runs ast-grep through the owner's pinned Mise lock,
        # which every governed repository carries; without it a host-global
        # binary (or none, on CI runners) answered instead.
        u.Tests.copy_tracked_mise_seeds(root)
        # A bare root becomes a checkout through its initial commit; an
        # existing checkout commits the catalog it now declares.
        if (root / c.Infra.GIT_DIR).exists():
            u.Tests.commit_git_changes(root, "Declare the demo rule catalog")
        else:
            u.Tests.initialize_git_repo(root)
        u.Tests.git_bootstrap(root, ("add", str(c.Infra.CODEMOD_CONFIG_RELPATH)))
        u.Tests.git_bootstrap(root, ("add", str(c.Infra.CODEMOD_CONFIG_RELPATH.parent)))
        return rule

    @classmethod
    def _snapshot(cls, root: Path, rule_id: str = "demo") -> Path:
        """Return the committed snapshot path of one rule under ``root``.

        Returns:
            The committed snapshot path of one rule under ``root``.

        """
        return (
            cls._catalog(root)
            / "tests"
            / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            / f"{rule_id}{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
        )

    def test_refresh_records_what_verification_then_accepts(
        self,
        tmp_path: Path,
    ) -> None:
        """A dry refresh writes nothing; the applied refresh makes mod verify."""
        rule = self._owner(tmp_path)

        preview = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=False,
            ),
        )
        tm.that(preview, eq=(f"created {self._snapshot(tmp_path)}",))
        tm.that(self._snapshot(tmp_path).exists(), eq=False)
        tm.fail(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

        applied = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )

        tm.that(applied, eq=preview)
        tm.that(self._snapshot(tmp_path).exists(), eq=True)
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))
        tm.that(
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    tmp_path,
                    (rule,),
                    apply=True,
                ),
            ),
            empty=True,
        )

    def test_changed_rule_output_fails_verification_without_rewriting(
        self,
        tmp_path: Path,
    ) -> None:
        """Mod never accepts a new fix output as its own expectation."""
        rule = self._owner(tmp_path)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        committed = self._snapshot(tmp_path).read_bytes()
        _ = self._owner(tmp_path, fix="qux($A)")

        failure = FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,))

        tm.fail(failure, has=c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT)
        tm.that(self._snapshot(tmp_path).read_bytes(), eq=committed)
        changes = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        tm.that(changes, eq=(f"updated {self._snapshot(tmp_path)}",))
        tm.that(self._snapshot(tmp_path).read_text(encoding="utf-8"), has="qux(1)")
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

    @pytest.mark.parametrize("residue", ["removed-rule", "deleted-case"])
    def test_snapshot_residue_fails_verification_until_refreshed(
        self,
        tmp_path: Path,
        residue: str,
    ) -> None:
        """A snapshot no rule test produces is reported, then removed by refresh."""
        rule = self._owner(tmp_path, invalid=("foo(1)", "foo(2)"))
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        if residue == "removed-rule":
            stale = self._snapshot(tmp_path, "retired")
            tm.ok(
                u.Cli.atomic_write_text_file(
                    stale,
                    self
                    ._snapshot(tmp_path)
                    .read_text(encoding="utf-8")
                    .replace("id: demo", "id: retired"),
                ),
            )
            expected = f"removed {stale}"
        else:
            _ = self._owner(tmp_path, invalid=("foo(1)",))
            expected = f"updated {self._snapshot(tmp_path)}"

        failure = FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,))

        tm.fail(failure, has=c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT)
        changes = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        tm.that(changes, eq=(expected,))
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

    @pytest.mark.slow
    def test_public_refresh_route_dry_run_fails_until_applied(
        self,
        mod_workspace: Path,
    ) -> None:
        """The public route previews pending snapshots as red and applies them."""
        _ = self._owner(mod_workspace)
        snapshot = self._snapshot(mod_workspace)
        route = ["refactor", "mod-snapshots", "--repository-root", str(mod_workspace)]

        tm.that(main(route), ne=0)
        tm.that(snapshot.exists(), eq=False)
        tm.that(main([*route, "--apply"]), eq=0)
        tm.that(snapshot.exists(), eq=True)
        tm.that(main(route), eq=0)
