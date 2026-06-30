# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".constants": ("TestsFlextInfraConstants",),
        ".unit.basemk.test_renderer": ("TestsFlextInfraBasemkRenderer",),
        ".unit.basemk.test_generator": ("TestsFlextInfraBasemkGenerator",),
        ".unit.basemk.test_generator_edge_cases": (
            "TestsFlextInfraBasemkGeneratorEdgeCases",
        ),
        ".unit.basemk.test_init": ("TestsFlextInfraBasemkInit",),
        ".unit.basemk.test_main": ("TestsFlextInfraBasemkMain",),
        ".unit.basemk.test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
        ".unit.check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
        ".unit.check.extended_models_tests": (
            "TestProjectResultProperties",
            "TestRunCommandGateParsing",
            "TestWorkspaceCheckerErrorSummary",
        ),
        ".unit.check.extended_project_runners_tests": ("TestsExtendedProjectRunners",),
        ".unit.check.extended_resolve_gates_tests": (
            "TestWorkspaceCheckerResolveGates",
        ),
        ".unit.check.extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
        ".unit.check.extended_runners_tests": ("TestRunnerPublicBehavior",),
        ".unit.check.tests_cli": ("TestWorkspaceCheckCli",),
        ".unit.cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
        ".unit.codegen.lazy_init_generation_tests": ("TestRunRuffFix",),
        ".unit.container.test_infra_container": (
            "TestsFlextInfraContainerInfraContainer",
        ),
        ".unit.deps.test_detection_classify": ("TestsFlextInfraDepsDetectionClassify",),
        ".unit.deps.test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
        ".unit.deps.test_detection_discover": ("TestsFlextInfraDepsDetectionDiscover",),
        ".unit.deps.test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
        ".unit.deps.test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
        ".unit.deps.test_detection_typings_flow": (
            "TestsFlextInfraDepsDetectionTypingsFlow",
        ),
        ".unit.deps.test_detection_uncovered": (
            "TestsFlextInfraDepsDetectionUncovered",
        ),
        ".unit.deps.test_detector_detect": ("TestsFlextInfraDepsDetectorDetect",),
        ".unit.deps.test_detector_detect_failures": (
            "TestsFlextInfraDepsDetectorDetectFailures",
        ),
        ".unit.deps.test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
        ".unit.docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
        ".unit.docs.shared_iter_tests": ("TestSelectedProjectNames",),
        ".unit.validate.main_cli_tests": ("TestValidateCli",),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_02"]
