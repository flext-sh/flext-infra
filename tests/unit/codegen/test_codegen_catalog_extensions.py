"""Repository catalog identity contracts for consumer-owned Make extensions."""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsCodegenCatalogExtensions:
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
