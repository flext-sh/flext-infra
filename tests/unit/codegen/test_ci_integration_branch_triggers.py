"""Verify ci.yml branch-trigger generation matches the declared baseline.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import c, config, m
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, t, tm, u


class TestsFlextInfraCiIntegrationBranchTriggers:
    """Keep integration triggers on one typed owner."""

    ci_template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows/ci.yml.j2"
    )
    baseline_branches = tuple(config.Infra.codegen.branch_policy.ci_trigger_branches)

    @classmethod
    def _render_workflow(
        cls,
        *,
        dist: str,
        make_profile: c.Infra.MakeProfile,
        repository_branch: str,
        ci_trigger_branches: t.VariadicTuple[t.NonEmptyStr],
    ) -> tuple[m.Infra.GithubWorkflowRenderSpec, str]:
        """Render one CI workflow and return its typed spec and rendered text.

        Returns:
            The render spec and its rendered workflow.

        """
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist=dist,
            make_profile=make_profile,
            repository_branch=repository_branch,
            ci_trigger_branches=ci_trigger_branches,
        )
        return spec, tm.ok(u.Cli.template_render(cls.ci_template, spec))

    @classmethod
    def render_ci(cls, *, repository_branch: str) -> str:
        """Provide ``render_ci``.

        Returns:
            The resulting ``str``.

        """
        _, rendered = cls._render_workflow(
            dist="mcb",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch=repository_branch,
            # The repository's own integration branch joins the SSOT baselines;
            # no positional or named assumption about the baseline contents.
            ci_trigger_branches=tuple(
                dict.fromkeys((*cls.baseline_branches, repository_branch)),
            ),
        )
        return rendered

    @staticmethod
    def _trigger_section(rendered: str) -> str:
        return rendered.split("c.ParserBooleanToken.ON:", maxsplit=1)[1].split(
            "# End SECTION: triggers",
            maxsplit=1,
        )[0]

    @staticmethod
    def _branch_count(triggers: str, branch: str) -> int:
        return triggers.splitlines().count(f"      - {branch}")

    def test_ci_triggers_include_custom_workspace_integration_branch(self) -> None:
        """Test ci triggers include custom workspace integration branch."""
        custom_branch = "feature/v0-4-0-multitenant-weaviate"
        triggers = self._trigger_section(
            self.render_ci(repository_branch=custom_branch),
        )

        tm.that(self._branch_count(triggers, custom_branch), eq=2)
        for baseline in self.baseline_branches:
            tm.that(self._branch_count(triggers, baseline), eq=2)

    def test_ci_triggers_deduplicate_integration_branch_against_baselines(self) -> None:
        """Test ci triggers deduplicate integration branch against baselines."""
        triggers = self._trigger_section(self.render_ci(repository_branch="develop"))

        for branch in self.baseline_branches:
            tm.that(self._branch_count(triggers, branch), eq=2)

    def test_pull_request_title_edits_revalidate_release_metadata(self) -> None:
        """GitHub dispatches the workflow when release-plan's PR title changes."""
        workflow = tm.ok(u.Cli.yaml_parse(self.render_ci(repository_branch="develop")))
        events = workflow[c.ParserBooleanToken.ON]
        tm.that(isinstance(events, Mapping), truth=True)
        pull_request = events["pull_request"]
        tm.that(isinstance(pull_request, Mapping), truth=True)
        activities = pull_request["types"]
        tm.that(isinstance(activities, list), truth=True)

        tm.that(activities, has="edited")

    @staticmethod
    @pytest.mark.parametrize(
        "template_source",
        [
            entry.source
            for entry in config.Infra.codegen.templates.entries
            if entry.source is not None
            and not entry.requires_release_protocol
            and Path(entry.destination).is_relative_to(
                c.Infra.GITHUB_WORKFLOWS_RELATIVE_PATH,
            )
        ],
    )
    def test_event_context_matches_the_rendered_workflow_triggers(
        template_source: Path,
    ) -> None:
        """Only workflows declaring PR events may reference their payload."""
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="event-context-consumer",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="integration/event-context-consumer",
            ci_trigger_branches=(),
        )
        template_root = u.Infra.codegen_templates_root(config.Infra.codegen)
        template = template_root / template_source
        rendered = tm.ok(u.Cli.template_render(template, spec))
        document = tm.ok(u.Cli.yaml_parse(rendered))
        events = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            document[c.ParserBooleanToken.ON]
        )

        tm.that(
            "github.event.pull_request" in rendered and "pull_request" not in events,
            eq=False,
        )

    @staticmethod
    def test_workflow_projection_uses_only_manifest_workflows() -> None:
        """Scoped recovery retains every non-workflow destination."""
        codegen = config.Infra.codegen
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.WORKFLOWS,
            codegen=codegen,
        )
        expected = frozenset(
            entry.destination
            for entry in codegen.templates.entries
            if Path(entry.destination).is_relative_to(
                c.Infra.GITHUB_WORKFLOWS_RELATIVE_PATH,
            )
        )

        tm.that(expected, empty=False)
        tm.that(contract.destinations, eq=expected)
        tm.fail(contract.pyproject)
        tm.fail(contract.tooling)
        tm.fail(contract.custom)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_ci_and_hook_share_the_check_and_test_workflow(
        profile: c.Infra.MakeProfile,
    ) -> None:
        """CI approval and the commit hook share their check and test operations."""
        codegen = config.Infra.codegen
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="approval-consumer",
            make_profile=profile,
            repository_branch="integration/approval-consumer",
            ci_trigger_branches=(),
        )
        root = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base"
        )
        rendered = tm.ok(
            u.Cli.template_render(
                root / ".github/workflows/ci.yml.j2",
                spec,
            ),
        )
        steps = u.CodegenTestSupport.Ci.ci_job_steps(rendered)
        approval = tuple(
            step for step in steps if str(step.get("id", "")).startswith("approval-")
        )
        tm.that(
            tuple(step["run"] for step in approval),
            eq=tuple(
                f"{codegen.make.ci.variable}={codegen.make.ci.value} make {verb}"
                for verb in codegen.make.approval_verbs
            ),
        )
        # Quoted diagnostics may recommend a local resolver without executing it.
        for step in steps:
            for line in str(step.get("run", "")).splitlines():
                command = c.Infra.DOCS_MAKE_COMMAND_RE.match(line)
                if command is not None:
                    tm.that(
                        command.group("verb") in {"gen", "upg", "dep"},
                        eq=False,
                    )
        tm.that(rendered, lacks=["continue-on-error", "make pre-commit"])
        hook = tm.ok(
            u.Cli.template_render(
                root / ".pre-commit-config.yaml.j2",
                m.Infra.MakeWorkflowRenderSpec(dist=spec.dist, make=codegen.make),
            ),
        )
        tm.that(hook, has="make pre-commit")
        tm.that(hook, lacks=["make fmt", "make fix"])
        tm.that(
            tuple(
                step.verb
                for step in codegen.make.workflow
                if "pre_commit" in step.contexts
            ),
            eq=(c.Infra.VERB_CHECK, c.Infra.VERB_TEST),
        )

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_ci_preserves_original_execution_receipts_on_every_outcome(
        profile: c.Infra.MakeProfile,
    ) -> None:
        """The rendered Actions upload preserves causal evidence without logs."""
        spec, rendered = TestsFlextInfraCiIntegrationBranchTriggers._render_workflow(
            dist="receipt-consumer",
            make_profile=profile,
            repository_branch="integration/receipt-consumer",
            ci_trigger_branches=(),
        )
        steps = u.CodegenTestSupport.Ci.ci_job_steps(rendered)
        upload = next(
            step
            for step in steps
            if step.get("uses")
            == (
                f"{spec.github_actions['upload-artifact'].repository}"
                f"@{spec.github_actions['upload-artifact'].version}"
            )
        )
        tm.that(upload["if"], eq="${{ always() }}")
        inputs = u.Cli.json_as_mapping(upload["with"])
        tm.that(inputs["if-no-files-found"], eq="error")
        tm.ok(inputs["include-hidden-files"])
        paths = str(inputs["path"]).splitlines()
        for filename in (
            "suite-outcome.json",
            "selection-outcome.json",
            "inventory-outcome.json",
            "run-context.json",
            "selection-plan.json",
            "testmon-selection.json",
            "testmon-inventory.json",
            "run-accounting.json",
            "diagnostics.json",
            "cache-before.json",
            "cache-after.json",
            "cache-policy.json",
            "markdown-reconciliation.json",
        ):
            tm.that(paths, has=f".reports/tests/**/{filename}")
        tm.that(
            paths,
            has=[".reports/check/**/*.sarif", ".reports/check/**/*.md"],
        )
        tm.that(
            paths,
            has=[
                f"{spec.make.gate_receipts_directory}/**/{spec.gate_original_receipt_filename}",
                f"{spec.make.gate_receipts_directory}/**/check/**/*.sarif",
                f"{spec.make.gate_receipts_directory}/**/check/**/*.md",
                f".reports/tests/**/{spec.gate_original_receipt_filename}",
            ],
        )
        for private_name in (
            c.Infra.GATE_CAPTURE_START_FILENAME,
            c.Infra.GATE_CAPTURE_RESULT_FILENAME,
            "command.txt",
        ):
            tm.fail(any(path.endswith(private_name) for path in paths))
        publication = c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        tm.that(
            paths,
            has=[
                c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH.as_posix(),
                publication.as_posix(),
                f"{c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH.as_posix()}/**/*.json",
                f"{c.Infra.WORKSPACE_OPERATION_REPORT_DIRECTORY.as_posix()}/*.json",
            ],
        )
        tm.fail(any(path.endswith(".log") for path in paths))
        tm.that(rendered, lacks=["continue-on-error"])

    @staticmethod
    def test_tool_cache_keeps_new_generations_after_completed_failures() -> None:
        """A rendered cache contract restores progress and never overwrites it."""
        spec, rendered = TestsFlextInfraCiIntegrationBranchTriggers._render_workflow(
            dist="cache-consumer",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="integration/cache-consumer",
            ci_trigger_branches=(),
        )
        steps = u.CodegenTestSupport.Ci.ci_job_steps(rendered)
        restore = next(step for step in steps if step.get("id") == "tool-cache")
        save = next(step for step in steps if step.get("name") == "Save tool caches")
        restore_inputs = u.Cli.json_as_mapping(restore["with"])
        save_inputs = u.Cli.json_as_mapping(save["with"])
        primary_key = restore_inputs["key"]
        prefixes_text = restore_inputs["restore-keys"]
        tm.that(isinstance(primary_key, str), truth=True)
        tm.that(isinstance(prefixes_text, str), truth=True)
        prefixes = prefixes_text.splitlines()
        tm.that(len(prefixes), eq=2)
        tm.ok(primary_key.startswith(prefixes[0]))
        tm.ok(prefixes[0].startswith(prefixes[1]))
        tm.ok(prefixes[0] != prefixes[1])
        tm.that(prefixes[1], has=spec.python_version)
        tm.that(
            primary_key,
            has=["${{ github.run_id }}", "${{ github.run_attempt }}"],
        )
        tm.that(
            save_inputs["key"],
            eq="${{ steps.tool-cache.outputs.cache-primary-key }}",
        )
        tm.that(
            save["if"],
            has=[
                "always()",
                "!cancelled()",
                "steps.tool-cache.outcome == 'success'",
                "steps.tool-cache.outputs.cache-primary-key != ''",
                "github.event_name == 'workflow_dispatch'",
                "github.event.pull_request.head.repo.full_name == github.repository",
            ],
        )
        tm.that(save["if"], lacks=["cache-hit", "success()"])
        tm.that(save_inputs["path"], eq=restore_inputs["path"])
        cache_action = spec.github_actions["cache"]
        tm.that(
            save["uses"],
            eq=f"{cache_action.repository}/save@{cache_action.version}",
        )

    @staticmethod
    def test_testmon_save_requires_a_trusted_fresh_project_receipt() -> None:
        """Actions archives only the typed project database, never a cache tree."""
        spec, rendered = TestsFlextInfraCiIntegrationBranchTriggers._render_workflow(
            dist="cache-consumer",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="integration/cache-consumer",
            ci_trigger_branches=(),
        )
        steps = u.CodegenTestSupport.Ci.ci_job_steps(rendered)
        saves = tuple(
            step for step in steps if step.get("name") == "Save testmon database"
        )
        tm.that(bool(saves), eq=spec.make.testmon_cache_policy.save_enabled)
        if saves:
            resolver = next(step for step in steps if step.get("id") == "testmon_path")
            resolver_environment = u.Cli.json_as_mapping(resolver["env"])
            tm.that(
                saves[0]["if"],
                has=[
                    "always()",
                    "!cancelled()",
                    "steps.testmon_path.outputs.save_allowed == 'true'",
                    "testmon_saveable",
                    "testmon_digest",
                ],
            )
            tm.that(
                resolver_environment["CACHE_WRITE_ALLOWED"],
                has=[
                    "github.event_name == 'push'",
                    "startsWith(github.ref, 'refs/heads/')",
                    "github.event_name == 'pull_request'",
                    (
                        "github.event.pull_request.head.repo.full_name "
                        "== github.repository"
                    ),
                ],
            )
            tm.that(
                resolver_environment["CACHE_BRANCH"],
                eq="${{ github.head_ref || github.ref_name }}",
            )
            cache_input = u.Cli.json_as_mapping(saves[0]["with"])
            restore = next(
                step for step in steps if step.get("name") == "Restore testmon database"
            )
            test_step = next(
                step
                for step in steps
                if step.get("run")
                == (
                    f"{spec.make.ci.variable}={spec.make.ci.value} "
                    f"make {c.Infra.VERB_TEST}"
                )
            )
            tm.that(
                cache_input["path"],
                eq=f"${{{{ steps.{test_step['id']}.outputs.testmon_database }}}}",
            )
            tm.that(
                cache_input["key"],
                eq=u.Cli.json_as_mapping(restore["with"])["key"],
            )
            restore_inputs = u.Cli.json_as_mapping(restore["with"])
            tm.that(
                str(restore_inputs["restore-keys"]).splitlines(),
                eq=[
                    (
                        "${{ steps.testmon_path.outputs.namespace }}"
                        "${{ hashFiles('uv.lock', 'mise.lock', "
                        "'pyproject.toml', 'config/**') }}-"
                    ),
                    "${{ steps.testmon_path.outputs.namespace }}",
                    "${{ steps.testmon_path.outputs.seed_namespace }}",
                ],
            )

    @staticmethod
    def test_testmon_resolver_keeps_branch_and_generation_identity(
        tmp_path: Path,
    ) -> None:
        """Run the rendered cache resolver with distinct inputs and branches."""
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="cache-consumer",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="integration/cache-consumer",
            ci_trigger_branches=(),
        )
        rendered = tm.ok(
            u.Cli.template_render(
                TestsFlextInfraCiIntegrationBranchTriggers.ci_template,
                spec,
            ),
        )
        resolver = next(
            step
            for step in u.CodegenTestSupport.Ci.ci_job_steps(rendered)
            if step.get("id") == "testmon_path"
        )
        receipts: list[str] = []
        for index, (branch, inputs) in enumerate((
            ("feature/cache", "before"),
            ("feature/cache", "after"),
            ("feature/other-cache", "after"),
        )):
            output = tmp_path / f"output-{index}"
            outcome = tm.ok(
                u.Cli.run(
                    ["bash", "-c", str(resolver["run"])],
                    options=m.Cli.ProcessOptions(
                        env={
                            "CACHE_BRANCH": branch,
                            "CACHE_SEED_BRANCH": spec.repository_branch,
                            "CACHE_WRITE_ALLOWED": c.ParserBooleanToken.TRUE,
                            "CACHE_INPUTS": inputs,
                            "CACHE_PLATFORM": "fixture-platform",
                            "CACHE_GENERATION": str(index),
                            "GITHUB_OUTPUT": str(output),
                            spec.make.testmon_cache.data_home_environment_variable: str(
                                tmp_path,
                            ),
                        },
                    ),
                ),
            )
            tm.ok(u.Cli.process_succeeded(outcome.outcome))
            receipts.append(output.read_text(encoding="utf-8"))
        namespaces = tuple(
            next(line for line in receipt.splitlines() if line.startswith("namespace="))
            for receipt in receipts
        )
        seeds = tuple(
            next(
                line
                for line in receipt.splitlines()
                if line.startswith("seed_namespace=")
            )
            for receipt in receipts
        )
        tm.that(namespaces[0], eq=namespaces[1])
        tm.ok(namespaces[1] != namespaces[2])
        tm.that(len(set(seeds)), eq=1)
        tm.that(len(set(receipts)), eq=len(receipts))

    @staticmethod
    @pytest.mark.parametrize("missing", ["setup", "audit", "check", "test"])
    def test_typed_approval_rejects_missing_stages(missing: str) -> None:
        """A truncated workflow cannot become an approval contract."""
        owner = config.Infra.codegen.make
        payload = owner.model_dump(exclude=set(type(owner).model_computed_fields))
        payload["workflow"] = [
            step.model_dump() for step in owner.workflow if step.verb != missing
        ]
        with pytest.raises(ValueError, match="workflow"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    def test_typed_approval_cannot_disable_pre_commit() -> None:
        """Projection enablement is mandatory rather than a per-project option."""
        owner = config.Infra.codegen.make
        payload = owner.model_dump(exclude=set(type(owner).model_computed_fields))
        payload["pre_commit"] = False
        with pytest.raises(ValueError, match="pre_commit"):
            m.Infra.MakeSpec.model_validate(payload)
