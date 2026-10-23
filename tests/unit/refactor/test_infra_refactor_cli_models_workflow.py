"""CLI workflow tests for refactor namespace automation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, m, main
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow:
    """Behavior contract for test_infra_refactor_cli_models_workflow."""

    @staticmethod
    def test_mod_cli_accepts_repeated_typed_consumer_roots_and_rejects_missing_scope(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Repeated run roots reach the canonical action without CSV or env inputs."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, _receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="native-receiver",
            package_name="native_receiver",
        )
        source = package / "consumer.py"
        source.write_text("VALUE = 'original'\n", encoding=c.DEFAULT_ENCODING)
        original = source.read_bytes()
        output = StringIO()
        with redirect_stdout(output):
            result = main([
                "refactor",
                "mod",
                f"--repository-root={root}",
                f"--consumer-roots={receiver}",
                f"--consumer-roots={tmp_path / 'absent-receiver'}",
                "--apply",
            ])
        tm.ok(result != 0)
        tm.that(
            capsys.readouterr().err,
            has="consumer roots must be existing absolute checkout roots",
        )
        tm.that(source.read_bytes(), eq=original)

    @staticmethod
    @pytest.mark.parametrize("kind", ["class", "module"])
    def test_native_rename_plan_captures_three_roots_before_any_effect(
        tmp_path: Path,
        kind: str,
    ) -> None:
        """The public action derives every reference without a consumer map."""
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declaration = package / "original.py"
        declaration.write_text(
            "class Original:\n"
            "    @staticmethod\n"
            "    def value() -> str:\n"
            "        return 'native'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        roots: list[Path] = []
        consumers: list[Path] = []
        for index in range(2):
            root, consumer_package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=f"native-consumer-{index}",
                package_name=f"native_consumer_{index}",
            )
            consumer = consumer_package / "consumer.py"
            consumer.write_text(
                f"from {package.name}.original import Original as Bound\n"
                "class Foreign:\n"
                "    class Original:\n"
                "        pass\n"
                "VALUE = Bound.value()\n",
                encoding=c.DEFAULT_ENCODING,
            )
            roots.append(root)
            consumers.append(consumer)
        unselected = tmp_path / "unselected.py"
        unselected.write_text("Original = 'unselected'\n", encoding=c.DEFAULT_ENCODING)
        originals = {
            path: path.read_bytes() for path in (declaration, *consumers, unselected)
        }
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.original"
                    + (".Original" if kind == "class" else ""),
                    replacement_name="Renamed" if kind == "class" else "renamed",
                    reason="Native identity propagation before the coordinated cut",
                ),
            ),
            consumer_roots=tuple(roots),
        )
        artifact_path = producer / "native.artifact"
        arguments = [
            "refactor",
            "rename-plan",
            f"--repository-root={producer}",
            f"--output={artifact_path.name}",
            f"--decisions={selections.model_dump_json()}",
        ]
        tm.that(main(arguments), eq=0)
        artifact = m.Infra.SemanticRenamePlan.model_validate_json(
            artifact_path.read_bytes()
        )
        tm.that(artifact.candidate.workspaces, eq=(producer, *roots))
        for consumer in consumers:
            proposed = tm.not_none(artifact.candidate.updates[consumer])
            tm.that(proposed, has="class Original:")
            tm.that(proposed, has="VALUE = Bound.value()")
            tm.that(
                proposed,
                has="import Renamed as Bound"
                if kind == "class"
                else ".renamed import Original as Bound",
            )
        if kind == "module":
            destination = declaration.with_name("renamed.py")
            tm.that(artifact.moves, eq=((declaration, destination),))
            tm.that(artifact.candidate.updates[declaration], eq=None)
            tm.that(artifact.candidate.updates[destination], eq=declaration.read_text())
            tm.fail(destination.exists())
        else:
            tm.that(
                tm.not_none(artifact.candidate.updates[declaration]),
                has="class Renamed:",
            )
        tm.that(main(arguments), eq=0)
        tm.that(
            m.Infra.SemanticRenamePlan.model_validate_json(
                artifact_path.read_bytes()
            ).model_dump(include={"edits", "decisions", "moves"}),
            eq=artifact.model_dump(include={"edits", "decisions", "moves"}),
        )
        for path, content in originals.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    def test_member_rename_plan_discovers_internal_consumers_from_composition(
        tmp_path: Path,
    ) -> None:
        """A member invocation elects the existing containing-workspace owner."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        producer, package = u.Tests.create_lazy_init_workspace(
            root,
            project_name="member-producer",
            package_name="member_producer",
        )
        consumer_root, consumer_package = u.Tests.create_lazy_init_workspace(
            root,
            project_name="member-consumer",
            package_name="member_consumer",
        )
        (root / c.Infra.GITMODULES).write_text(
            f'[submodule "{producer.name}"]\npath = {producer.name}\n'
            f"url = https://example.invalid/{producer.name}.git\n"
            f'[submodule "{consumer_root.name}"]\npath = {consumer_root.name}\n'
            f"url = https://example.invalid/{consumer_root.name}.git\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = consumer_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Original",
                    replacement_name="Renamed",
                    reason="Native containing-workspace cut",
                ),
            )
        )
        tm.that(
            main([
                "refactor",
                "rename-plan",
                f"--repository-root={producer}",
                "--output=native.artifact",
                f"--decisions={selections.model_dump_json()}",
            ]),
            eq=0,
        )
        artifact = m.Infra.SemanticRenamePlan.model_validate_json(
            (producer / "native.artifact").read_bytes()
        )
        tm.that(artifact.candidate.workspace, eq=root)
        tm.that(
            tm.not_none(artifact.candidate.updates[consumer]), has="VALUE = Renamed()"
        )
        tm.that(source.read_text(), has="class Original:")

    @staticmethod
    @pytest.mark.parametrize(
        "output_kind", ["artifact", "source", "config", "metadata", "symlink"]
    )
    def test_semantic_rename_cli_protects_governed_output_identities(
        tmp_path: Path, output_kind: str
    ) -> None:
        """Only a separate artifact may replace bytes after native planning."""
        workspace, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        source.write_text(
            "class Owner:\n"
            "    def predicate(self, value: str) -> bool:\n"
            "        return bool(value)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        policy = workspace / c.Infra.CODEGEN_CONFIG_DIR / "policy.data"
        policy.parent.mkdir(exist_ok=True)
        policy.write_text("governed policy\n", encoding=c.DEFAULT_ENCODING)
        alias = workspace / "source.alias"
        if output_kind == "symlink":
            alias.symlink_to(source)
        output = {
            "artifact": workspace / "rename.artifact",
            "source": source,
            "config": policy,
            "metadata": workspace / c.PYPROJECT_FILENAME,
            "symlink": alias,
        }[output_kind]
        originals = {
            path: path.read_bytes()
            for path in (source, policy, workspace / c.PYPROJECT_FILENAME)
        }
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Owner.predicate",
                    replacement_name="meaningful",
                    reason="Reviewed callable domain name",
                ),
            )
        )
        arguments = [
            "refactor",
            "rename-plan",
            f"--repository-root={workspace}",
            f"--output={output.relative_to(workspace)}",
            f"--decisions={selections.model_dump_json()}",
        ]
        result = main(arguments)
        if output_kind == "artifact":
            tm.that(result, eq=0)
            artifact = m.Infra.SemanticRenamePlan.model_validate_json(
                output.read_bytes()
            )
            tm.that(artifact.candidate.workspace, eq=workspace)
            tm.that(artifact.edits[0].updated_source, has="def meaningful(")
            tm.that(main(arguments), eq=0)
            repeated = m.Infra.SemanticRenamePlan.model_validate_json(
                output.read_bytes()
            )
            tm.that(repeated.edits, eq=artifact.edits)
            tm.that(repeated.decisions, eq=artifact.decisions)
            tm.that(repeated.moves, eq=artifact.moves)
        else:
            tm.that(result, ne=0)
        for path, content in originals.items():
            tm.that(path.read_bytes(), eq=content)
        if output_kind == "artifact":
            drifted = source.read_bytes() + b"\n# Independent shared source update\n"
            source.write_bytes(drifted)
            driver = output.read_bytes()
            tm.that(
                main([
                    "refactor",
                    "rename-preview",
                    f"--repository-root={workspace}",
                    f"--plan={output.relative_to(workspace)}",
                ]),
                ne=0,
            )
            tm.that(source.read_bytes(), eq=drifted)
            tm.that(output.read_bytes(), eq=driver)

    @staticmethod
    def test_namespace_enforce_cli_fails_on_manual_protocol_violation(
        tmp_path: Path,
    ) -> None:
        """Test namespace enforce cli fails on manual protocol violation."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "workspace",
            pyproject="[project]\nname='sample'\ndependencies = []\n",
            with_src=True,
        )
        module_dir = workspace / "src" / "sample_pkg"
        module_dir.mkdir(parents=True)
        (workspace / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        (module_dir / "service.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class External(Protocol):\n"
            "    def call(self) -> str:\n"
            "        ...\n",
            encoding="utf-8",
        )
        # The enforcer scans through the repository's pinned Mise lock, which
        # every governed repository carries; CI runners have no global tool.
        u.Tests.copy_tracked_mise_seeds(workspace)
        u.Tests.initialize_git_repo(workspace)
        buffer = StringIO()
        cli_args = [
            "namespace-enforce",
            f"--repository-root={workspace!s}",
            "--dry-run",
        ]
        with redirect_stdout(buffer):
            result = main(["refactor", *cli_args])
        tm.that(result, ne=0)

    @staticmethod
    def test_wrapper_root_namespace_cli_dry_run_succeeds(tmp_path: Path) -> None:
        """Test wrapper root namespace cli dry run succeeds."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "workspace",
            pyproject="[project]\nname='sample'\ndependencies = []\n",
            with_src=True,
        )
        scripts_dir = workspace / "scripts"
        scripts_dir.mkdir(parents=True)
        (workspace / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        source_file = scripts_dir / "sample.py"
        source_file.write_text(
            "from tests import c\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = c.Core.Tests.ERR_OK_FAILED\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(workspace)

        with redirect_stdout(StringIO()):
            result = main([
                "refactor",
                "wrapper-root-namespace",
                f"--repository-root={workspace!s}",
                "--dry-run",
            ])

        tm.that(result, eq=0)
        tm.that(source_file.read_text(encoding="utf-8"), has="c.Core.Tests")

    @staticmethod
    def test_wrapper_root_namespace_cli_check_fails_when_changes_are_needed(
        tmp_path: Path,
    ) -> None:
        """Test wrapper root namespace cli check fails when changes are needed."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "workspace",
            pyproject="[project]\nname='sample'\ndependencies = []\n",
            with_src=True,
        )
        scripts_dir = workspace / "scripts"
        scripts_dir.mkdir(parents=True)
        (workspace / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        (scripts_dir / "sample.py").write_text(
            "from tests import m\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = m.Core.Tests.Testobject\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(workspace)

        result = main([
            "refactor",
            "wrapper-root-namespace",
            f"--repository-root={workspace!s}",
            "--check",
        ])

        tm.that(result, ne=0)

    @staticmethod
    def test_wrapper_root_namespace_cli_apply_rewrites_file(
        tmp_path: Path,
    ) -> None:
        """Test wrapper root namespace cli apply rewrites file."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "workspace",
            pyproject="[project]\nname='sample'\ndependencies = []\n",
            with_src=True,
        )
        scripts_dir = workspace / "scripts"
        scripts_dir.mkdir(parents=True)
        (workspace / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        source_file = scripts_dir / "sample.py"
        source_file.write_text(
            "from tests import t\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = t.Core.Tests.Testobject\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        result = main([
            "refactor",
            "wrapper-root-namespace",
            f"--repository-root={workspace!s}",
            "--apply",
        ])

        tm.that(result, eq=0)
        updated = source_file.read_text(encoding="utf-8")
        tm.that(updated, has="from tests import t")
        tm.that(updated, has="t.Tests.Testobject")
        tm.that(updated, lacks="Core.Tests")
