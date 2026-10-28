"""Verify generated release jobs retain the credential required by Git pushes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import t
from tests import c, tm, u


class TestsFlextInfraReleaseCheckoutCredentials:
    """Release jobs push branches and tags through the checkout credential."""

    release_template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows/release.yml.j2"
    )

    @classmethod
    def render_release(cls, *, publish_index: bool = False) -> t.JsonMapping:
        """Provide ``render_release``.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        repository_branch = "develop"
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-workspace",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch=repository_branch,
            ci_trigger_branches=u.CodegenTestSupport.Ci.ci_trigger_branches(
                repository_branch,
            ),
        ).model_copy(
            update={
                "publish_index": publish_index,
                "private_submodules": (
                    u.CodegenTestSupport.Ci.synthetic_private_submodules()
                ),
            },
        )
        rendered = tm.ok(u.Cli.template_render(cls.release_template, spec))
        return u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.yaml_parse(rendered)),
        )

    @staticmethod
    def checkout_credentials(job: t.JsonValue) -> bool:
        """Provide ``checkout_credentials``.

        Returns:
            The resulting ``bool``.

        Raises:
            TypeError: If workflow job steps must be a sequence; or if
                persist-credentials must render as a YAML boolean.

        """
        mapping = u.Cli.JSON_MAPPING_ADAPTER.validate_python(job)
        steps = mapping["steps"]
        if not isinstance(steps, list):
            msg = "workflow job steps must be a sequence"
            raise TypeError(msg)
        checkout = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[0])
        inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(checkout["with"])
        value = inputs["persist-credentials"]
        if not isinstance(value, bool):
            msg = "persist-credentials must render as a YAML boolean"
            raise TypeError(msg)
        return value

    def test_release_push_jobs_persist_declared_checkout_token(self) -> None:
        """Test release push jobs persist declared checkout token."""
        document = self.render_release()
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])

        tm.fail(self.checkout_credentials(jobs["identity"]))
        tm.ok(self.checkout_credentials(jobs["version"]))
        tm.ok(self.checkout_credentials(jobs["publish"]))

    def test_release_effects_require_exact_candidate_ci(self) -> None:
        """Dispatch and release commits share one immutable, blocking CI input."""
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(self.render_release()["jobs"])
        candidate = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["candidate-ci"])
        tm.that(candidate["needs"], eq="identity")
        tm.that(candidate["uses"], eq="./.github/workflows/ci.yml")
        tm.that(candidate["secrets"], eq="inherit")
        inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(candidate["with"])
        tm.that(inputs["ref"], eq="${{ needs.identity.outputs.ref }}")
        for name in ("version", "publish"):
            job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs[name])
            tm.that(job["needs"], eq=["identity", "candidate-ci"])
            steps = u.json_list_adapter().validate_python(job["steps"])
            checkout = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[0])
            checkout_inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                checkout["with"]
            )
            tm.that(checkout_inputs["ref"], eq=inputs["ref"])
        publish = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["publish"])
        tm.that(
            publish["if"],
            eq=(
                "github.event_name == 'workflow_dispatch' && "
                "needs.identity.outputs.release_commit == 'true' && "
                "needs.candidate-ci.result == 'success'"
            ),
        )
        identity = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["identity"])
        steps = u.json_list_adapter().validate_python(identity["steps"])
        checkout = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[0])
        checkout_inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(checkout["with"])
        tm.that(
            checkout_inputs["ref"],
            eq=(
                "${{ github.event_name == 'workflow_dispatch' && inputs.tag != '' && "
                "format('refs/tags/{0}', inputs.tag) || github.sha }}"
            ),
        )
        head = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[1])
        tm.that(str(head["run"]), has="ref=$(git rev-parse HEAD^{commit})")

    def test_dispatch_checkpoint_is_version_only_environment_data(self) -> None:
        """Both dispatch choices are explicit; only version consumes ownership."""
        document = self.render_release()
        triggers = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            document[c.ParserBooleanToken.ON]
        )
        dispatch = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            triggers["workflow_dispatch"]
        )
        inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(dispatch["inputs"])
        tm.that(set(inputs), eq={"tag", "checkpoint_ref"})
        for name in ("tag", "checkpoint_ref"):
            option = u.Cli.JSON_MAPPING_ADAPTER.validate_python(inputs[name])
            tm.that(option["required"], eq=False)
            tm.that(option["type"], eq="string")
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
        version = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["version"])
        environment = u.Cli.JSON_MAPPING_ADAPTER.validate_python(version["env"])
        tm.that(
            environment["LANE_CHECKPOINT_REF"],
            eq=(
                "${{ github.event_name == 'workflow_dispatch' && "
                "inputs.checkpoint_ref || vars.LANE_CHECKPOINT_REF }}"
            ),
        )
        tm.that(version["if"], eq="needs.identity.outputs.release_commit == 'false'")
        publish = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["publish"])
        publish_env = u.Cli.JSON_MAPPING_ADAPTER.validate_python(publish["env"])
        tm.that("LANE_CHECKPOINT_REF" in publish_env, eq=False)

    @pytest.mark.parametrize(
        (c.HandlerType.EVENT, "selection", "succeeds", "release"),
        [
            ("push", ("", ""), True, False),
            ("workflow_dispatch", ("fixture-release", ""), True, True),
            ("workflow_dispatch", ("", "refs/checkpoints/owned"), True, False),
            (
                "workflow_dispatch",
                ("fixture-release", "refs/checkpoints/owned"),
                False,
                False,
            ),
            ("workflow_dispatch", ("", ""), False, False),
            ("workflow_dispatch", ("$(touch injected)", ""), False, False),
            (
                "workflow_dispatch",
                ("", "refs/checkpoints/x; touch injected"),
                False,
                False,
            ),
        ],
    )
    def test_dispatch_identity_preserves_native_candidate(
        self,
        tmp_path: Path,
        event: str,
        selection: tuple[str, str],
        *,
        succeeds: bool,
        release: bool,
    ) -> None:
        """Real Git classifies XOR inputs without executing data or moving HEAD."""
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(self.render_release()["jobs"])
        identity = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["identity"])
        steps = u.json_list_adapter().validate_python(identity["steps"])
        classify = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[1])
        tm.that("${{" in str(classify["run"]), eq=False)
        root = u.Tests.git_repository(tmp_path / "repo")
        u.Tests.git_run(root, "tag", "fixture-release")
        candidate = u.Tests.git_capture(root, "rev-parse", "HEAD").strip()
        index = (root / c.GIT_DIR_NAME / "index").read_bytes()
        output = tmp_path / "github-output"
        tag, checkpoint = selection
        with u.Tests.env_vars_context({
            "EVENT_NAME": event,
            "RELEASE_TAG": tag,
            "LANE_CHECKPOINT_REF": checkpoint,
            "GITHUB_OUTPUT": str(output),
        }):
            process = tm.ok(
                u.Cli.run_raw(["bash", "-eu", "-c", str(classify["run"])], cwd=root)
            )
        tm.that(u.Cli.process_succeeded(process.outcome), eq=succeeds)
        if succeeds:
            lines = output.read_text(encoding=c.DEFAULT_ENCODING).splitlines()
            tm.that(f"ref={candidate}" in lines, eq=True)
            tm.that(f"release_commit={str(release).lower()}" in lines, eq=True)
        tm.that(u.Tests.git_capture(root, "rev-parse", "HEAD").strip(), eq=candidate)
        tm.that((root / c.GIT_DIR_NAME / "index").read_bytes(), eq=index)
        tm.that((root / "injected").exists(), eq=False)

    def test_generated_version_head_gets_direct_ci_without_publication(self) -> None:
        """The token-created PR receives CI without becoming a publication path."""
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(self.render_release()["jobs"])
        version_ci = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["version-ci"])
        tm.that(version_ci["needs"], eq="version")
        tm.that(version_ci["uses"], eq="./.github/workflows/ci.yml")
        inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(version_ci["with"])
        tm.that(inputs["ref"], eq="${{ needs.version.outputs.ref }}")
        tm.that("steps" not in version_ci)
        version = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["version"])
        outputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(version["outputs"])
        tm.that(outputs["ref"], eq="${{ steps.version.outputs.ref }}")

    def test_reusable_ci_checks_requested_commit_with_canonical_gates(self) -> None:
        """The called workflow validates the supplied SHA, not its event SHA."""
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-workspace",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="candidate-line",
            ci_trigger_branches=u.CodegenTestSupport.Ci.ci_trigger_branches(
                "candidate-line",
            ),
        )
        rendered = tm.ok(
            u.Cli.template_render(self.release_template.with_name("ci.yml.j2"), spec),
        )
        document = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.yaml_parse(rendered)),
        )
        triggers = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            document[c.ParserBooleanToken.ON]
        )
        call = u.Cli.JSON_MAPPING_ADAPTER.validate_python(triggers["workflow_call"])
        inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(call["inputs"])
        ref = u.Cli.JSON_MAPPING_ADAPTER.validate_python(inputs["ref"])
        tm.that(ref["type"], eq="string")
        tm.that(ref["default"], eq="")
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
        ci = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["ci"])
        steps = u.json_list_adapter().validate_python(ci["steps"])
        checkout = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[0])
        checkout_inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(checkout["with"])
        tm.that(checkout_inputs["ref"], eq="${{ inputs.ref || github.sha }}")
        commands = [
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(step).get("run")
            for step in steps
        ]
        for step in spec.make.workflow:
            if "ci" not in step.contexts:
                continue
            tm.that(
                f"{spec.make.ci.variable}={spec.make.ci.value} {step.make_command}"
                in commands
            )

    def test_version_admits_detached_candidate_without_moving_its_sha(
        self,
        tmp_path: Path,
    ) -> None:
        """The rendered admission enters the required branch at the validated SHA."""
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(self.render_release()["jobs"])
        version = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["version"])
        steps = u.json_list_adapter().validate_python(version["steps"])
        admission = next(
            mapping
            for step in steps
            if (mapping := u.Cli.JSON_MAPPING_ADAPTER.validate_python(step)).get("name")
            == "Admit validated integration commit"
        )
        environment = u.Cli.JSON_MAPPING_ADAPTER.validate_python(admission["env"])
        branch = str(environment["INTEGRATION_BRANCH"])
        for command in (
            ["git", "init", "--initial-branch", branch],
            [
                "git",
                "-c",
                "user.name=Release test",
                "-c",
                "user.email=release@example.invalid",
                "commit",
                "--allow-empty",
                "-m",
                "candidate",
            ],
            ["git", "checkout", "--detach", "HEAD"],
        ):
            tm.ok(u.Cli.run_checked(command, cwd=tmp_path))
        candidate = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=tmp_path))
        tm.ok(
            u.Cli.run_checked(
                [
                    "env",
                    f"INTEGRATION_BRANCH={branch}",
                    "bash",
                    "-eu",
                    "-c",
                    str(admission["run"]),
                ],
                cwd=tmp_path,
            ),
        )
        tm.that(
            tm.ok(u.Cli.capture(["git", "branch", "--show-current"], cwd=tmp_path)),
            eq=branch,
        )
        tm.that(
            tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=tmp_path)),
            eq=candidate,
        )

    @pytest.mark.parametrize("publish_index", [False, True])
    def test_index_policy_controls_publication_and_oidc(
        self,
        *,
        publish_index: bool,
    ) -> None:
        """Only explicitly permitted index publication requests an OIDC token."""
        document = self.render_release(publish_index=publish_index)
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
        publish = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["publish"])
        permissions = u.Cli.JSON_MAPPING_ADAPTER.validate_python(publish["permissions"])
        tm.that("id-token" in permissions, eq=publish_index)
        steps = u.json_list_adapter().validate_python(publish["steps"])
        publication = u.Cli.JSON_MAPPING_ADAPTER.validate_python(steps[-1])
        tm.that(
            publication["run"],
            eq="make publication INDEX=Y" if publish_index else "make publication",
        )
