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
            tm.that(
                m.Infra.SemanticRenamePlan.model_validate_json(output.read_bytes()),
                eq=artifact,
            )
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
    @pytest.mark.parametrize(
        ("mode", "facade", "member", "succeeds"),
        [
            ("--dry-run", "c", "ERR_OK_FAILED", True),
            ("--check", "m", "Testobject", False),
            ("--apply", "t", "Testobject", True),
        ],
    )
    def test_wrapper_root_namespace_cli_modes(
        tmp_path: Path,
        mode: str,
        facade: str,
        member: str,
        succeeds: bool,
    ) -> None:
        """Dry-run keeps bytes, check flags needed changes, apply rewrites the file."""
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
            f"from tests import {facade}\n"
            "\n"
            "def test_contract() -> None:\n"
            f"    _ = {facade}.Core.Tests.{member}\n",
            encoding="utf-8",
        )
        if mode == "--apply":
            u.Tests.provision_checkout(workspace)
        else:
            u.Tests.initialize_git_repo(workspace)

        with redirect_stdout(StringIO()):
            result = main([
                "refactor",
                "wrapper-root-namespace",
                f"--repository-root={workspace!s}",
                mode,
            ])

        tm.that(result == 0, eq=succeeds)
        updated = source_file.read_text(encoding="utf-8")
        if mode == "--apply":
            tm.that(updated, has=f"from tests import {facade}")
            tm.that(updated, has=f"{facade}.Tests.{member}")
            tm.that(updated, lacks="Core.Tests")
        elif mode == "--dry-run":
            tm.that(updated, has=f"{facade}.Core.Tests")
