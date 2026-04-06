# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Models package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._models.base as _flext_infra__models_base

    base = _flext_infra__models_base
    import flext_infra._models.basemk as _flext_infra__models_basemk
    from flext_infra._models.base import FlextInfraModelsBase

    basemk = _flext_infra__models_basemk
    import flext_infra._models.census as _flext_infra__models_census
    from flext_infra._models.basemk import FlextInfraBasemkModels

    census = _flext_infra__models_census
    import flext_infra._models.check as _flext_infra__models_check
    from flext_infra._models.census import FlextInfraModelsCensus

    check = _flext_infra__models_check
    import flext_infra._models.cli_inputs as _flext_infra__models_cli_inputs
    from flext_infra._models.check import FlextInfraCheckModels

    cli_inputs = _flext_infra__models_cli_inputs
    import flext_infra._models.cli_inputs_codegen as _flext_infra__models_cli_inputs_codegen
    from flext_infra._models.cli_inputs import FlextInfraModelsCliInputs

    cli_inputs_codegen = _flext_infra__models_cli_inputs_codegen
    import flext_infra._models.cli_inputs_ops as _flext_infra__models_cli_inputs_ops
    from flext_infra._models.cli_inputs_codegen import FlextInfraModelsCliInputsCodegen

    cli_inputs_ops = _flext_infra__models_cli_inputs_ops
    import flext_infra._models.codegen as _flext_infra__models_codegen
    from flext_infra._models.cli_inputs_ops import FlextInfraModelsCliInputsOps

    codegen = _flext_infra__models_codegen
    import flext_infra._models.codegen_deduplication as _flext_infra__models_codegen_deduplication
    from flext_infra._models.codegen import FlextInfraCodegenModels

    codegen_deduplication = _flext_infra__models_codegen_deduplication
    import flext_infra._models.deps as _flext_infra__models_deps
    from flext_infra._models.codegen_deduplication import (
        FlextInfraCodegenDeduplicationModels,
    )

    deps = _flext_infra__models_deps
    import flext_infra._models.deps_tool_config as _flext_infra__models_deps_tool_config
    from flext_infra._models.deps import FlextInfraDepsModels

    deps_tool_config = _flext_infra__models_deps_tool_config
    import flext_infra._models.deps_tool_config_linters as _flext_infra__models_deps_tool_config_linters
    from flext_infra._models.deps_tool_config import FlextInfraDepsModelsToolConfig

    deps_tool_config_linters = _flext_infra__models_deps_tool_config_linters
    import flext_infra._models.deps_tool_config_type_checkers as _flext_infra__models_deps_tool_config_type_checkers
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraDepsModelsToolConfigLinters,
    )

    deps_tool_config_type_checkers = _flext_infra__models_deps_tool_config_type_checkers
    import flext_infra._models.docs as _flext_infra__models_docs
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraDepsModelsToolConfigTypeCheckers,
    )

    docs = _flext_infra__models_docs
    import flext_infra._models.engine as _flext_infra__models_engine
    from flext_infra._models.docs import FlextInfraDocsModels

    engine = _flext_infra__models_engine
    import flext_infra._models.engine_ops as _flext_infra__models_engine_ops
    from flext_infra._models.engine import FlextInfraEngineModels

    engine_ops = _flext_infra__models_engine_ops
    import flext_infra._models.gates as _flext_infra__models_gates
    from flext_infra._models.engine_ops import FlextInfraEngineOperationModels

    gates = _flext_infra__models_gates
    import flext_infra._models.github as _flext_infra__models_github
    from flext_infra._models.gates import FlextInfraGatesModels

    github = _flext_infra__models_github
    import flext_infra._models.mixins as _flext_infra__models_mixins
    from flext_infra._models.github import FlextInfraGithubModels

    mixins = _flext_infra__models_mixins
    import flext_infra._models.refactor as _flext_infra__models_refactor
    from flext_infra._models.mixins import FlextInfraModelsMixins

    refactor = _flext_infra__models_refactor
    import flext_infra._models.refactor_ast_grep as _flext_infra__models_refactor_ast_grep
    from flext_infra._models.refactor import FlextInfraRefactorModels

    refactor_ast_grep = _flext_infra__models_refactor_ast_grep
    import flext_infra._models.refactor_census as _flext_infra__models_refactor_census
    from flext_infra._models.refactor_ast_grep import FlextInfraRefactorGrepModels

    refactor_census = _flext_infra__models_refactor_census
    import flext_infra._models.refactor_namespace_enforcer as _flext_infra__models_refactor_namespace_enforcer
    from flext_infra._models.refactor_census import FlextInfraRefactorModelsCensus

    refactor_namespace_enforcer = _flext_infra__models_refactor_namespace_enforcer
    import flext_infra._models.refactor_violations as _flext_infra__models_refactor_violations
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraNamespaceEnforcerModels,
    )

    refactor_violations = _flext_infra__models_refactor_violations
    import flext_infra._models.release as _flext_infra__models_release
    from flext_infra._models.refactor_violations import (
        FlextInfraRefactorModelsViolations,
    )

    release = _flext_infra__models_release
    import flext_infra._models.rope as _flext_infra__models_rope
    from flext_infra._models.release import FlextInfraReleaseModels

    rope = _flext_infra__models_rope
    import flext_infra._models.scan as _flext_infra__models_scan
    from flext_infra._models.rope import FlextInfraModelsRope

    scan = _flext_infra__models_scan
    import flext_infra._models.validate as _flext_infra__models_validate
    from flext_infra._models.scan import FlextInfraModelsScan

    validate = _flext_infra__models_validate
    import flext_infra._models.workspace as _flext_infra__models_workspace
    from flext_infra._models.validate import FlextInfraCoreModels

    workspace = _flext_infra__models_workspace
    from flext_infra._models.workspace import FlextInfraWorkspaceModels
_LAZY_IMPORTS = {
    "FlextInfraBasemkModels": ("flext_infra._models.basemk", "FlextInfraBasemkModels"),
    "FlextInfraCheckModels": ("flext_infra._models.check", "FlextInfraCheckModels"),
    "FlextInfraCodegenDeduplicationModels": (
        "flext_infra._models.codegen_deduplication",
        "FlextInfraCodegenDeduplicationModels",
    ),
    "FlextInfraCodegenModels": (
        "flext_infra._models.codegen",
        "FlextInfraCodegenModels",
    ),
    "FlextInfraCoreModels": ("flext_infra._models.validate", "FlextInfraCoreModels"),
    "FlextInfraDepsModels": ("flext_infra._models.deps", "FlextInfraDepsModels"),
    "FlextInfraDepsModelsToolConfig": (
        "flext_infra._models.deps_tool_config",
        "FlextInfraDepsModelsToolConfig",
    ),
    "FlextInfraDepsModelsToolConfigLinters": (
        "flext_infra._models.deps_tool_config_linters",
        "FlextInfraDepsModelsToolConfigLinters",
    ),
    "FlextInfraDepsModelsToolConfigTypeCheckers": (
        "flext_infra._models.deps_tool_config_type_checkers",
        "FlextInfraDepsModelsToolConfigTypeCheckers",
    ),
    "FlextInfraDocsModels": ("flext_infra._models.docs", "FlextInfraDocsModels"),
    "FlextInfraEngineModels": ("flext_infra._models.engine", "FlextInfraEngineModels"),
    "FlextInfraEngineOperationModels": (
        "flext_infra._models.engine_ops",
        "FlextInfraEngineOperationModels",
    ),
    "FlextInfraGatesModels": ("flext_infra._models.gates", "FlextInfraGatesModels"),
    "FlextInfraGithubModels": ("flext_infra._models.github", "FlextInfraGithubModels"),
    "FlextInfraModelsBase": ("flext_infra._models.base", "FlextInfraModelsBase"),
    "FlextInfraModelsCensus": ("flext_infra._models.census", "FlextInfraModelsCensus"),
    "FlextInfraModelsCliInputs": (
        "flext_infra._models.cli_inputs",
        "FlextInfraModelsCliInputs",
    ),
    "FlextInfraModelsCliInputsCodegen": (
        "flext_infra._models.cli_inputs_codegen",
        "FlextInfraModelsCliInputsCodegen",
    ),
    "FlextInfraModelsCliInputsOps": (
        "flext_infra._models.cli_inputs_ops",
        "FlextInfraModelsCliInputsOps",
    ),
    "FlextInfraModelsMixins": ("flext_infra._models.mixins", "FlextInfraModelsMixins"),
    "FlextInfraModelsRope": ("flext_infra._models.rope", "FlextInfraModelsRope"),
    "FlextInfraModelsScan": ("flext_infra._models.scan", "FlextInfraModelsScan"),
    "FlextInfraNamespaceEnforcerModels": (
        "flext_infra._models.refactor_namespace_enforcer",
        "FlextInfraNamespaceEnforcerModels",
    ),
    "FlextInfraRefactorGrepModels": (
        "flext_infra._models.refactor_ast_grep",
        "FlextInfraRefactorGrepModels",
    ),
    "FlextInfraRefactorModels": (
        "flext_infra._models.refactor",
        "FlextInfraRefactorModels",
    ),
    "FlextInfraRefactorModelsCensus": (
        "flext_infra._models.refactor_census",
        "FlextInfraRefactorModelsCensus",
    ),
    "FlextInfraRefactorModelsViolations": (
        "flext_infra._models.refactor_violations",
        "FlextInfraRefactorModelsViolations",
    ),
    "FlextInfraReleaseModels": (
        "flext_infra._models.release",
        "FlextInfraReleaseModels",
    ),
    "FlextInfraWorkspaceModels": (
        "flext_infra._models.workspace",
        "FlextInfraWorkspaceModels",
    ),
    "base": "flext_infra._models.base",
    "basemk": "flext_infra._models.basemk",
    "census": "flext_infra._models.census",
    "check": "flext_infra._models.check",
    "cli_inputs": "flext_infra._models.cli_inputs",
    "cli_inputs_codegen": "flext_infra._models.cli_inputs_codegen",
    "cli_inputs_ops": "flext_infra._models.cli_inputs_ops",
    "codegen": "flext_infra._models.codegen",
    "codegen_deduplication": "flext_infra._models.codegen_deduplication",
    "deps": "flext_infra._models.deps",
    "deps_tool_config": "flext_infra._models.deps_tool_config",
    "deps_tool_config_linters": "flext_infra._models.deps_tool_config_linters",
    "deps_tool_config_type_checkers": "flext_infra._models.deps_tool_config_type_checkers",
    "docs": "flext_infra._models.docs",
    "engine": "flext_infra._models.engine",
    "engine_ops": "flext_infra._models.engine_ops",
    "gates": "flext_infra._models.gates",
    "github": "flext_infra._models.github",
    "mixins": "flext_infra._models.mixins",
    "refactor": "flext_infra._models.refactor",
    "refactor_ast_grep": "flext_infra._models.refactor_ast_grep",
    "refactor_census": "flext_infra._models.refactor_census",
    "refactor_namespace_enforcer": "flext_infra._models.refactor_namespace_enforcer",
    "refactor_violations": "flext_infra._models.refactor_violations",
    "release": "flext_infra._models.release",
    "rope": "flext_infra._models.rope",
    "scan": "flext_infra._models.scan",
    "validate": "flext_infra._models.validate",
    "workspace": "flext_infra._models.workspace",
}

__all__ = [
    "FlextInfraBasemkModels",
    "FlextInfraCheckModels",
    "FlextInfraCodegenDeduplicationModels",
    "FlextInfraCodegenModels",
    "FlextInfraCoreModels",
    "FlextInfraDepsModels",
    "FlextInfraDepsModelsToolConfig",
    "FlextInfraDepsModelsToolConfigLinters",
    "FlextInfraDepsModelsToolConfigTypeCheckers",
    "FlextInfraDocsModels",
    "FlextInfraEngineModels",
    "FlextInfraEngineOperationModels",
    "FlextInfraGatesModels",
    "FlextInfraGithubModels",
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCliInputs",
    "FlextInfraModelsCliInputsCodegen",
    "FlextInfraModelsCliInputsOps",
    "FlextInfraModelsMixins",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "FlextInfraNamespaceEnforcerModels",
    "FlextInfraRefactorGrepModels",
    "FlextInfraRefactorModels",
    "FlextInfraRefactorModelsCensus",
    "FlextInfraRefactorModelsViolations",
    "FlextInfraReleaseModels",
    "FlextInfraWorkspaceModels",
    "base",
    "basemk",
    "census",
    "check",
    "cli_inputs",
    "cli_inputs_codegen",
    "cli_inputs_ops",
    "codegen",
    "codegen_deduplication",
    "deps",
    "deps_tool_config",
    "deps_tool_config_linters",
    "deps_tool_config_type_checkers",
    "docs",
    "engine",
    "engine_ops",
    "gates",
    "github",
    "mixins",
    "refactor",
    "refactor_ast_grep",
    "refactor_census",
    "refactor_namespace_enforcer",
    "refactor_violations",
    "release",
    "rope",
    "scan",
    "validate",
    "workspace",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
