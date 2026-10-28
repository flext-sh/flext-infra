"""Integration tests for flext_infra cross-module flows.

Every test here exercises a real cross-module flow through the public
runtime surfaces: Rope census evidence, the markdown gate fix contract over the
filesystem, and the canonical CLI boundary driving real git and external commands.
Detector, discovery, and result-monad behavior keep their dedicated suites.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

import pytest

from flext_infra import infra, m
from flext_infra.gates import FlextInfraMarkdownGate
from flext_infra.refactor import FlextInfraRefactorCensus
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


class TestsFlextInfraIntegrationInfraIntegration:
    """Integration tests for the public FlextInfra surface."""

    @staticmethod
    @pytest.mark.parametrize(
        ("name", "declaration"),
        [("helper", "def"), ("_helper", "def"), ("helper", "async def")],
        ids=["function", "private-function", "async-function"],
    )
    def test_census_all_surface_evidence_preserves_reachability(
        tmp_path: Path,
        name: str,
        declaration: str,
    ) -> None:
        """Public read-only inventory retains qualified sites on every surface."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        definition = package / "helpers.py"
        definition.write_text(
            f"{declaration} {name}() -> int:\n    return 7\n",
            encoding="utf-8",
        )
        consumer_source = (
            f"from flext_evidence.helpers import {name}\n"
            f"uses = ({name}, {name})\n"
            f'label = "{name}"\n'
        )
        expected: set[tuple[str, int, int, str]] = set()
        for surface in (
            c.Infra.DEFAULT_SRC_DIR,
            c.Infra.DIR_SCRIPTS,
            c.Infra.DIR_TESTS,
            c.Infra.DIR_EXAMPLES,
        ):
            directory = (
                package if surface == c.Infra.DEFAULT_SRC_DIR else root / surface
            )
            directory.mkdir(parents=True, exist_ok=True)
            consumer = directory / "consumer.py"
            consumer.write_text(consumer_source, encoding="utf-8")
            start = consumer_source.index("import ") + len("import ")
            for line in (1, 2, 2):
                offset = consumer_source.index(name, start)
                expected.add((str(consumer.resolve()), line, offset, surface))
                start = offset + len(name)
            (directory / "homonym.py").write_text(
                f"def {name}() -> int:\n    return 8\nuses = ({name}, {name})\n",
                encoding="utf-8",
            )
        initializer = package / c.Infra.INIT_PY
        reexport_source = f"from flext_evidence.helpers import {name}\n"
        initializer.write_text(reexport_source, encoding="utf-8")
        expected.add((
            str(initializer.resolve()),
            1,
            reexport_source.index("import ") + len("import "),
            c.Infra.DEFAULT_SRC_DIR,
        ))

        with infra.rope_workspace(root) as rope:
            item = next(
                item
                for item in rope.objects(definition, include_local_scopes=False)
                if item.name == name
            )

        tm.ok(item.reference_evidence_collected)
        tm.that(
            {
                (site.file_path, site.line, site.offset, site.surface)
                for site in item.all_reference_sites
            },
            eq=expected,
        )
        tm.that(len(item.all_reference_sites), eq=len(expected))
        ordering = [
            (site.file_path, tm.not_none(site.offset))
            for site in item.all_reference_sites
        ]
        tm.that(ordering, eq=sorted(ordering))
        tm.that(item.runtime_references_count, eq=0 if name.startswith("_") else 2)
        tm.that(item.script_references_count, eq=0 if name.startswith("_") else 2)
        tm.that(item.references_count, eq=0 if name.startswith("_") else 4)
        tm.that(
            all(
                site.file_path != str(initializer.resolve())
                for site in item.runtime_reference_sites
            ),
            eq=True,
        )
        restored = m.Infra.Object.model_validate_json(item.model_dump_json())
        tm.that(restored, eq=item)
        with infra.rope_workspace(root) as rope:
            repeated = next(
                item for item in rope.objects(definition) if item.name == name
            )
        tm.that(repeated.all_reference_sites, eq=item.all_reference_sites)
        tm.that(initializer.read_text(encoding="utf-8"), eq=reexport_source)

    @staticmethod
    def test_census_test_only_evidence_does_not_block_unused_classification(
        tmp_path: Path,
    ) -> None:
        """An untracked test consumer supplies evidence, not runtime reachability."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        u.Tests.provision_checkout(root)
        definition = package / "helpers.py"
        definition.write_text("def helper() -> int:\n    return 7\n", encoding="utf-8")
        tests_dir = root / c.Infra.DIR_TESTS
        tests_dir.mkdir()
        consumer = tests_dir / "consumer.py"
        consumer.write_text(
            "from flext_evidence.helpers import helper\nuses = (helper, helper)\n",
            encoding="utf-8",
        )
        status = tm.ok(u.Cli.capture(["git", "status", "--porcelain"], cwd=root))
        tm.that(status, has=f"?? {c.Infra.DIR_TESTS}/")

        report = FlextInfraRefactorCensus(
            workspace_factory=infra.rope_workspace,
            source_preview=infra.source_preview(root),
            repository_root=root,
            apply_changes=False,
            dry_run=False,
            options=m.Infra.CensusOptions(
                kinds=("function",),
                rules=("unused",),
                include_local_scopes=False,
            ),
        ).build_report()
        item = next(
            item
            for project in report.projects
            for item in project.objects
            if item.file_path == str(definition.resolve()) and item.name == "helper"
        )
        tm.that(len(item.all_reference_sites), eq=3)
        tm.that(
            {site.file_path for site in item.all_reference_sites},
            eq={str(consumer.resolve())},
        )
        tm.ok(item.reference_evidence_collected)
        tm.that(item.references_count, eq=0)
        tm.that(item.runtime_reference_sites, eq=())
        tm.that(item.script_reference_sites, eq=())
        candidates = [
            candidate
            for candidate in report.removal_candidates
            if candidate.object_name == "helper"
        ]
        tm.that(len(candidates), eq=1)
        tm.that(candidates[0].reason, eq="unused")
        restored = m.Infra.WorkspaceReport.model_validate_json(report.model_dump_json())
        tm.that(restored.projects, eq=report.projects)

    @staticmethod
    @pytest.mark.parametrize("declaration", ["def", "async def"])
    def test_census_definition_only_and_disabled_evidence(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """No consumers differs from a disabled reference collection."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        definition = package / "helpers.py"
        definition.write_text(
            f"{declaration} helper() -> int:\n    return 7\n",
            encoding="utf-8",
        )
        with infra.rope_workspace(root) as rope:
            collected = next(
                item for item in rope.objects(definition) if item.name == "helper"
            )
            disabled = next(
                item
                for item in rope.objects(definition, include_references=False)
                if item.name == "helper"
            )
        tm.that(collected.all_reference_sites, eq=())
        tm.ok(collected.reference_evidence_collected)
        tm.that(collected.references_count, eq=0)
        tm.that(disabled.all_reference_sites, eq=())
        tm.fail(disabled.reference_evidence_collected)

    @staticmethod
    def test_census_facade_evidence_does_not_become_runtime_reachability(
        tmp_path: Path,
    ) -> None:
        """Policy-owned facade aliases retain evidence, not runtime reachability."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        family = next(iter(u.Infra.facade_families().values()))
        definition = package / f"{family.module}.py"
        definition.write_text("", encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            convention = rope.convention(definition)
        layout = tm.not_none(convention.project_layout)
        class_name = f"{layout.class_stem}{family.suffix}"
        u.Tests.write_lazy_init_namespace_module(
            definition,
            class_name=class_name,
            alias=family.letter,
        )
        with infra.rope_workspace(root) as rope:
            convention = rope.convention(definition)
        alias = tm.not_none(convention.module_policy.expected_alias)
        consumer = package / "consumer.py"
        consumer.write_text(
            f"from {convention.module_name} import {alias}\nuses = {alias}\n",
            encoding="utf-8",
        )
        with infra.rope_workspace(root) as rope:
            item = next(item for item in rope.objects(definition) if item.name == alias)
        tm.ok(item.is_facade_member)
        tm.ok(item.reference_evidence_collected)
        tm.that(
            {
                site.line
                for site in item.all_reference_sites
                if site.file_path == str(consumer.resolve())
            },
            eq={1, 2},
        )
        tm.that(item.references_count, eq=0)
        tm.that(item.runtime_reference_sites, eq=())
        tm.that(item.script_reference_sites, eq=())

    @staticmethod
    def test_census_multiline_parameters_keep_native_definition_positions(
        tmp_path: Path,
    ) -> None:
        """Native parameter bindings retain positional and keyword signature lines."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        definition = package / "helpers.py"
        definition.write_text(
            "def consume(\n"
            "    first,\n"
            "    /,\n"
            "    second=None,\n"
            "    *items,\n"
            "    named=None,\n"
            "    **options,\n"
            "):\n"
            "    return first, second, items, named, options\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as rope:
            parameters = {
                item.name: item.line
                for item in rope.objects(
                    definition,
                    include_local_scopes=True,
                    include_references=False,
                )
                if item.kind == "parameter"
            }
        tm.that(
            parameters,
            eq={"first": 2, "second": 4, "items": 5, "named": 6, "options": 7},
        )

    @staticmethod
    def test_census_same_line_function_and_parameter_bindings_are_separate(
        tmp_path: Path,
    ) -> None:
        """Repeated declaration spelling does not conflate distinct Rope bindings."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        definition = package / "helpers.py"
        source = "def _helper(_helper):\n    return _helper\n\nuse = _helper\n"
        definition.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            objects = rope.objects(definition, include_local_scopes=True)
        function = next(item for item in objects if item.scope_path == "_helper")
        parameter = next(
            item for item in objects if item.scope_path == "_helper._helper"
        )
        tm.that(function.kind, eq="function")
        tm.that(parameter.kind, eq="parameter")
        tm.ok(function.reference_evidence_collected)
        tm.ok(parameter.reference_evidence_collected)
        tm.that(
            [
                (site.file_path, site.line, site.offset)
                for site in function.all_reference_sites
            ],
            eq=[(str(definition.resolve()), 4, source.rindex("_helper"))],
        )
        tm.that(
            [
                (site.file_path, site.line, site.offset)
                for site in parameter.all_reference_sites
            ],
            eq=[
                (
                    str(definition.resolve()),
                    2,
                    source.index("_helper", source.index("return")),
                )
            ],
        )

    @staticmethod
    def test_census_same_line_binding_evidence_is_anchored_not_guessed(
        tmp_path: Path,
    ) -> None:
        """Same-line binding matches never acquire a guessed definition token."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-evidence",
            package_name="flext_evidence",
        )
        definition = package / "helpers.py"
        source = "def _helper(_helper): return _helper\nuse = _helper\n"
        definition.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            objects = rope.objects(definition, include_local_scopes=True)
        # The function record anchors its exact definition token (the line-2
        # module use is found); the parameter's same-line tokens stay
        # ambiguous and are reported uncollected instead of guessed.
        helper = next(item for item in objects if item.scope_path == "_helper")
        parameter = next(
            item for item in objects if item.scope_path == "_helper._helper"
        )
        tm.ok(helper.reference_evidence_collected)
        tm.that(
            [
                (site.file_path, site.line, site.offset)
                for site in helper.all_reference_sites
            ],
            eq=[
                (
                    str(definition.resolve()),
                    2,
                    source.index("_helper", source.index("use = _helper")),
                ),
            ],
        )
        tm.fail(parameter.reference_evidence_collected)
        tm.that(parameter.all_reference_sites, empty=True)
        tm.that(parameter.references_count, eq=0)

    @staticmethod
    @pytest.mark.integration
    def test_markdown_fix_reports_residual_after_repair(tmp_path: Path) -> None:
        """A valid repair survives while an unfixable finding fails the invocation."""
        project_dir = u.Tests.mk_project(
            tmp_path, "markdown-fmt-contract", markdown_config=""
        )
        document = project_dir / "README.md"
        document.write_text("not a heading   \n", encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path,
            apply_fixes=True,
        )

        execution = FlextInfraMarkdownGate(tmp_path).fix(project_dir, context)

        # Valid trailing-space repair remains published; MD041 still fails
        # this invocation with the same diagnostic as the read-only check.
        tm.fail(execution.result.passed)
        tm.that(document.read_text(encoding="utf-8"), eq="not a heading\n")
        tm.that(execution.issues[0].code, eq="MD041")
        tm.that(
            execution.issues,
            eq=FlextInfraMarkdownGate(tmp_path).check(project_dir, context).issues,
        )

    @staticmethod
    @pytest.mark.integration
    def test_markdown_check_retains_normalization_finding(tmp_path: Path) -> None:
        """A native MD013 normalization diagnostic remains visible to callers."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-normalization")
        (project_dir / c.Infra.MARKDOWN_CONFIG_FILENAME).write_text(
            u.Cli.toml_dumps(
                u.Cli.toml_document_from_mapping({
                    "global": {"enable": ["MD013"]},
                    "MD013": {
                        "line_length": 60,
                        "reflow": True,
                        "reflow-mode": "normalize",
                    },
                })
            ),
            encoding="utf-8",
        )
        (project_dir / "README.md").write_text(
            "# Title\n\nThis paragraph has\n"
            "several short lines that could be joined without\n"
            "changing the meaning of its content.\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)

        execution = FlextInfraMarkdownGate(tmp_path).check(
            project_dir,
            m.Infra.GateContext(repository_root=tmp_path, reports_dir=tmp_path),
        )

        tm.fail(execution.result.passed)
        tm.that(execution.issues[0].code, eq="MD013")

    @staticmethod
    @pytest.mark.integration
    def test_cli_capture_git_current_branch_in_real_repo(tmp_path: Path) -> None:
        """Test git branch detection through the canonical CLI runtime surface."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        init_result = u.Cli.run_checked(["git", "init"], cwd=repo_root)
        tm.ok(init_result)
        email_result = u.Cli.run_checked(
            ["git", "config", "user.email", "infra@example.com"],
            cwd=repo_root,
        )
        tm.ok(email_result)
        name_result = u.Cli.run_checked(
            ["git", "config", "user.name", "Infra Test"],
            cwd=repo_root,
        )
        tm.ok(name_result)
        sample_file = repo_root / "README.md"
        _ = sample_file.write_text("infra test\n", encoding="utf-8")
        add_result = u.Cli.run_checked(["git", "add", "README.md"], cwd=repo_root)
        tm.ok(add_result)
        commit_result = u.Cli.run_checked(
            ["git", "commit", "-m", "initial"],
            cwd=repo_root,
        )
        tm.ok(commit_result)
        branch_result = u.Cli.capture(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
        )
        tm.ok(branch_result)
        tm.that(branch_result.value, ne="")

    @staticmethod
    @pytest.mark.integration
    def test_command_runner_capture_executes_real_command() -> None:
        """Test u.Cli.capture with a real external command."""
        capture_result = u.Cli.capture(["python3", "-c", "print('infra-ok')"])
        tm.ok(capture_result, eq="infra-ok")
