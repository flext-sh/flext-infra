"""Repository catalog identity contracts for consumer-owned Make extensions."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsCodegenCatalogExtensions:
    def test_cosmos_consumer_manifest_matches_typed_catalog(self) -> None:
        consumer_manifest = Path(
            "/home/marlonsc/cosmos-main/.worktrees/qpsq-8-argo-cutover/config/workspace.yaml"
        )
        codegen_manifest = Path(__file__).parents[3] / "config" / "codegen.yaml"
        workspace_document = tm.ok(
            u.Cli.yaml_parse(consumer_manifest.read_text(encoding="utf-8"))
        )
        codegen_document = tm.ok(
            u.Cli.yaml_parse(codegen_manifest.read_text(encoding="utf-8"))
        )
        workspace = m.Infra.WorkspaceSpec.model_validate(workspace_document)
        codegen = m.Infra.CodegenConfigSpec.model_validate(
            codegen_document["Infra"]["codegen"]
        )

        result = FlextInfraCodegenConform._validate_workspace_catalog(  # ruff:ignore[private-member-access]
            codegen, workspace
        )

        tm.ok(result)

    def test_consumer_make_extensions_do_not_change_catalog_identity(self) -> None:
        known = config.Infra.codegen.repositories[0]
        local = known.model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(name="audit", default_what="all"),
                ),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher="scripts/dispatch.py", roots=("scripts",)
                ),
            }
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=known.name,
            repository=local,
        )

        result = FlextInfraCodegenConform._validate_workspace_catalog(  # ruff:ignore[private-member-access]
            config.Infra.codegen, workspace
        )

        tm.ok(result)

    def test_catalog_identity_difference_remains_rejected(self) -> None:
        known = config.Infra.codegen.repositories[0]
        local = known.model_copy(update={"branch": "different-branch"})
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=known.name,
            repository=local,
        )

        result = FlextInfraCodegenConform._validate_workspace_catalog(  # ruff:ignore[private-member-access]
            config.Infra.codegen, workspace
        )

        tm.fail(result)
        tm.that(
            result.error, eq=f"workspace repository differs from catalog: {known.name}"
        )


__all__: list[str] = []
