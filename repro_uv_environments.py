"""Diagnostic reproduction: build the ai-hub conform plan and inspect its Mise plans.

Run with the ai-hub venv interpreter and the worktree motor source:

    PYTHONPATH=/home/marlonsc/ai-hub-worktrees/flext-infra-automation/src \
        /home/marlonsc/ai-hub/.venv/bin/python repro_uv_environments.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import flext_infra

from flext_infra import c, m
from flext_infra.codegen._conform.file_plans import (
    FlextInfraCodegenConformFilePlans,
)
from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan

ROOT = Path("/home/marlonsc/ai-hub")


def main() -> int:
    print(f"motor: {flext_infra.__file__}")
    request = m.Infra.CodegenConformRequest(
        root=ROOT,
        what=c.Infra.CodegenConformSurface.ALL,
        scope=c.Infra.CodegenConformScope.ALL,
        mode=c.Infra.CodegenConformMode.APPLY,
    )
    planner = FlextInfraCodegenConformPlan()
    planned = planner.plan(request)
    if planned.failure:
        print(f"PLAN FAILURE: {planned.error}")
        return 1
    plan = planned.value
    print(f"repositories ({len(plan.repositories)}):")
    for repository in plan.repositories:
        print(
            f"  - name={repository.name} kind={repository.kind.value} "
            f"path={repository.path} read_only={repository.read_only}",
        )
    print(f"uv_environments ({len(plan.uv_environments)}):")
    for environment in plan.uv_environments:
        print(f"  - project_root={environment.project_root}")
    print(f"files ({len(plan.files)}):")
    for file in plan.files:
        print(f"  - {file.path}")
    print(f"issues ({len(plan.issues)}):")
    for issue in plan.issues[:25]:
        print(f"  - {issue.formatted}")
    print(f"planning_exception: {planner.planning_exception!r}")
    config_plans = FlextInfraCodegenConformFilePlans.mise_config_plans(plan)
    if config_plans.failure:
        print(f"mise_config_plans: FAIL — {config_plans.error}")
        return 1
    print(f"mise_config_plans: {len(config_plans.value)} plan(s)")
    for file in config_plans.value:
        print(f"  - {file.path}")
    if not config_plans.value:
        print("RED: config_plans is EMPTY — the Mise transaction would refuse")
        return 1
    print("GREEN: config_plans is populated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
