# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".basemk.test_renderer": ("TestsFlextInfraBasemkRenderer",),
        ".basemk.test_generator": ("TestsFlextInfraBasemkGenerator",),
        ".basemk.test_generator_edge_cases": (
            "TestsFlextInfraBasemkGeneratorEdgeCases",
        ),
        ".basemk.test_init": ("TestsFlextInfraBasemkInit",),
        ".basemk.test_main": ("TestsFlextInfraBasemkMain",),
        ".basemk.test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
        ".check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
        ".check.extended_models_tests": (
            "TestProjectResultProperties",
            "TestRunCommandGateParsing",
            "TestWorkspaceCheckerErrorSummary",
        ),
        ".check.extended_project_runners_tests": ("TestsExtendedProjectRunners",),
        ".check.extended_resolve_gates_tests": ("TestWorkspaceCheckerResolveGates",),
        ".check.extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
        ".check.extended_runners_tests": ("TestRunnerPublicBehavior",),
        ".check.tests_cli": ("TestWorkspaceCheckCli",),
        ".cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
        ".codegen.lazy_init_generation_tests": ("TestRunRuffFix",),
        ".container.test_infra_container": ("TestsFlextInfraContainerInfraContainer",),
        ".deps.test_detection_classify": ("TestsFlextInfraDepsDetectionClassify",),
        ".deps.test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
        ".deps.test_detection_discover": ("TestsFlextInfraDepsDetectionDiscover",),
        ".deps.test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
        ".deps.test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
        ".deps.test_detection_typings_flow": (
            "TestsFlextInfraDepsDetectionTypingsFlow",
        ),
        ".deps.test_detection_uncovered": ("TestsFlextInfraDepsDetectionUncovered",),
        ".deps.test_detector_detect": ("TestsFlextInfraDepsDetectorDetect",),
        ".deps.test_detector_detect_failures": (
            "TestsFlextInfraDepsDetectorDetectFailures",
        ),
        ".deps.test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
        ".deps.test_detector_main": ("TestsFlextInfraDepsDetectorMain",),
        ".docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
        ".docs.shared_iter_tests": ("TestSelectedProjectNames",),
        ".validate.main_cli_tests": ("TestValidateCli",),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02"]
