"""Optional complete checks preserve the mandatory CI approval contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, tm, u


class TestsFlextInfraCiCompleteCheck:
    """The manual port calls the existing complete native check."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "profile", [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE]
    )
    def test_complete_check_is_optional_and_keeps_required_steps(
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Render both profiles without changing required CI or gate selection."""
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist=config.Infra.name,
            make_profile=profile,
            repository_branch="0.12.0-dev",
            ci_trigger_branches=tuple(
                config.Infra.codegen.branch_policy.ci_trigger_branches
            ),
        )
        root = Path(__file__).resolve().parents[3]
        template = (
            root / "src/flext_infra/templates/project/base/.github/workflows/ci.yml.j2"
        )
        rendered = tm.ok(u.Cli.template_render(template, spec))
        artifact = (
            root
            / c.Infra.REPORTS_DIR_NAME
            / "ci-qualification"
            / f"{profile.value}.yml"
        )
        artifact.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(artifact, rendered))
        payload = u.json_mapping_adapter().validate_python(
            tm.ok(u.Cli.yaml_parse(rendered))
        )
        triggers = u.json_mapping_adapter().validate_python(payload["on"])
        for event in ("workflow_dispatch", "workflow_call"):
            event_spec = u.json_mapping_adapter().validate_python(triggers[event])
            inputs = u.json_mapping_adapter().validate_python(event_spec["inputs"])
            full_check = u.json_mapping_adapter().validate_python(inputs["full_check"])
            tm.that(full_check["default"], eq=False)
            tm.that(full_check["type"], eq="boolean")
            tm.that(full_check["required"], eq=False)
        steps = u.CodegenTestSupport.Ci.ci_job_steps(rendered)
        for step in (item for item in spec.make.workflow if "ci" in item.contexts):
            actual = next(
                item for item in steps if item.get("id") == f"approval-{step.identity}"
            )
            tm.that(
                actual["run"],
                eq=f"{spec.make.ci.variable}={spec.make.ci.value} {step.make_command}",
            )
        complete = next(
            step
            for step in spec.make.workflow
            if step.verb == "check" and step.phase != "primary"
        )
        optional = next(
            step for step in steps if step.get("id") == "qualification-check"
        )
        tm.that(
            optional["run"],
            eq=(
                f"{spec.make.ci.variable}={spec.make.ci.local_value} "
                f"{complete.make_command}"
            ),
        )
        tm.that(optional["if"], has="inputs.full_check == true")
        receipts = next(
            step
            for step in steps
            if step.get("name") == "Upload gate receipts on failure"
        )
        tm.that(receipts["if"], has="steps.qualification-check.outcome == 'failure'")
