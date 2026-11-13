# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Constants package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._constants.base import FlextInfraConstantsBase
    from flext_infra._constants.census import FlextInfraConstantsCensus
    from flext_infra._constants.check import FlextInfraConstantsCheck
    from flext_infra._constants.cli import FlextInfraConstantsCli
    from flext_infra._constants.codegen import FlextInfraConstantsCodegen
    from flext_infra._constants.codegen_detection import (
        FlextInfraConstantsCodegenDetection,
    )
    from flext_infra._constants.codegen_lazy import FlextInfraConstantsCodegenLazy
    from flext_infra._constants.codegen_project import FlextInfraConstantsCodegenProject
    from flext_infra._constants.codegen_render_names import (
        FlextInfraConstantsCodegenRenderNames,
    )
    from flext_infra._constants.config import FlextInfraConstantsConfig
    from flext_infra._constants.deps import FlextInfraConstantsDeps
    from flext_infra._constants.docs import FlextInfraConstantsDocs
    from flext_infra._constants.git import FlextInfraConstantsGit
    from flext_infra._constants.make import FlextInfraConstantsMake
    from flext_infra._constants.namespace import FlextInfraConstantsNamespace
    from flext_infra._constants.promoted import FlextInfraConstantsPromoted
    from flext_infra._constants.promoted_messages import (
        FlextInfraConstantsPromotedMessages,
    )
    from flext_infra._constants.pytest_surface import FlextInfraConstantsPytest
    from flext_infra._constants.refactor import FlextInfraConstantsRefactor
    from flext_infra._constants.release import FlextInfraConstantsRelease
    from flext_infra._constants.rope import FlextInfraConstantsRope
    from flext_infra._constants.source_code import FlextInfraConstantsSourceCode
    from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
    from flext_infra._constants.workspace import FlextInfraConstantsWorkspace


__all__: tuple[str, ...] = (
    "FlextInfraConstantsBase",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCheck",
    "FlextInfraConstantsCli",
    "FlextInfraConstantsCodegen",
    "FlextInfraConstantsCodegenDetection",
    "FlextInfraConstantsCodegenLazy",
    "FlextInfraConstantsCodegenProject",
    "FlextInfraConstantsCodegenRenderNames",
    "FlextInfraConstantsConfig",
    "FlextInfraConstantsDeps",
    "FlextInfraConstantsDocs",
    "FlextInfraConstantsGit",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsNamespace",
    "FlextInfraConstantsPromoted",
    "FlextInfraConstantsPromotedMessages",
    "FlextInfraConstantsPytest",
    "FlextInfraConstantsRefactor",
    "FlextInfraConstantsRelease",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSharedInfra",
    "FlextInfraConstantsSourceCode",
    "FlextInfraConstantsWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraConstantsBase": ".base",
        "FlextInfraConstantsCensus": ".census",
        "FlextInfraConstantsCheck": ".check",
        "FlextInfraConstantsCli": ".cli",
        "FlextInfraConstantsCodegen": ".codegen",
        "FlextInfraConstantsCodegenDetection": ".codegen_detection",
        "FlextInfraConstantsCodegenLazy": ".codegen_lazy",
        "FlextInfraConstantsCodegenProject": ".codegen_project",
        "FlextInfraConstantsCodegenRenderNames": ".codegen_render_names",
        "FlextInfraConstantsConfig": ".config",
        "FlextInfraConstantsDeps": ".deps",
        "FlextInfraConstantsDocs": ".docs",
        "FlextInfraConstantsGit": ".git",
        "FlextInfraConstantsMake": ".make",
        "FlextInfraConstantsNamespace": ".namespace",
        "FlextInfraConstantsPromoted": ".promoted",
        "FlextInfraConstantsPromotedMessages": ".promoted_messages",
        "FlextInfraConstantsPytest": ".pytest_surface",
        "FlextInfraConstantsRefactor": ".refactor",
        "FlextInfraConstantsRelease": ".release",
        "FlextInfraConstantsRope": ".rope",
        "FlextInfraConstantsSharedInfra": ".validate",
        "FlextInfraConstantsSourceCode": ".source_code",
        "FlextInfraConstantsWorkspace": ".workspace",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraConstantsPytest": ("Pytest",),
        "FlextInfraConstantsSourceCode": (
            "Cst",
            "MergeConflictControl",
            "MERGE_CONFLICT_CONTROLS",
            "MERGE_CONFLICT_BRANCH_BOUNDARIES",
            "MERGE_CONFLICT_ENCODING",
            "MERGE_CONFLICT_LINE_TERMINATORS",
            "TOML_MULTILINE_QUOTE_LENGTH",
            "TOML_SECTION_HEADER_RE",
            "TOML_BARE_KEY_RE",
            "SCRIPT_METADATA_BLOCK_RE",
            "SCRIPT_METADATA_TYPE",
            "SCRIPT_METADATA_START",
            "SCRIPT_METADATA_END",
            "SCRIPT_METADATA_COMMENT",
            "SCRIPT_METADATA_LINE_PREFIX",
            "GITHUB_DIRNAME",
            "GITHUB_AGENT_PROJECTION_DIRS",
            "TRANSIENT_PYTEST_SCRATCH_PART",
            "ENCODING_DEFAULT",
            "TOC_START",
            "TOC_END",
            "GENERATED_HEADER",
            "GENERATED_SHELL_HEADER",
            "FUTURE_ANNOTATIONS",
            "FUTURE_MODULE",
            "RUNTIME_MODEL_BASES",
            "PROTOCOL_BASE",
            "ENCODING_COOKIE_RE",
            "CLASS_WITH_BASES_RE",
            "FROM_IMPORT_RE",
            "FROM_IMPORT_BLOCK_RE",
            "REQUIRES_PYTHON_RE",
            "DEPENDENCY_VERSION_OP_RE",
            "REGEX_ERROR",
            "TOC_BLOCK_RE",
            "DUNDER_ALL_SINGLE_LINE_RE",
            "DUNDER_ALL_MULTI_LINE_RE",
            "BLANK_LINE_RUN_RE",
            "LEGACY_TYPEALIAS_RE",
            "compile_multiline",
            "compile",
            "compile_class_base_with_generic",
            "escape",
            "compile_from_module_paren_open",
            "compile_from_module_import_line",
            "GITHUB_REPO_URL",
            "GITHUB_REPO_NAME",
            "MIN_UNION_MEMBERS",
            "LINE_COL_RE",
            "CODE_FRAME_RE",
            "CODE_FRAME_BODY_RE",
            "UNUSED_IMPORT_RE",
            "LINT_SUMMARY_RE",
            "REPORTS_DIR_NAME",
            "AST_FUNCTION_TYPES",
            "AST_CALLABLE_TYPES",
            "AST_DEFINITION_TYPES",
            "AST_ASSIGNMENT_TYPES",
            "AST_IMPORT_TYPES",
            "AST_IMPORT_OR_CLASS_TYPES",
            "AST_NAME_REFERENCE_TYPES",
            "AST_SEQUENCE_DISPLAY_TYPES",
            "AST_TYPE_PARAM_TYPES",
            "AST_UNBINDING_CONTEXT_TYPES",
            "AST_WITH_TYPES",
            "AST_TRY_TYPES",
            "AST_SCOPE_OWNER_TYPES",
            "CST_IMPORT_TYPES",
            "CST_DEFINITION_TYPES",
        ),
    },
)
