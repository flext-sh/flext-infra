"""Public behavior tests for the Rope workspace DSL service."""

from __future__ import annotations

from pathlib import Path

import flext_infra
from tests import c, u


class TestFlextInfraRopeWorkspace:
    """Validate the public Rope workspace DSL through public methods only."""

    def test_open_workspace_materializes_snapshot(self, tmp_path: Path) -> None:
        """Public service class exposes one typed workspace snapshot."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        rope = flext_infra.FlextInfraRopeWorkspace.open_workspace(workspace_root)
        try:
            snapshot_result = rope.execute()
            assert snapshot_result.success
            snapshot = snapshot_result.value
            assert snapshot.workspace_root == workspace_root.resolve()
            assert package_root in snapshot.workspace_index.package_dirs
            assert rope.module_entry(module_path) is not None
            assert rope.package_entry(package_root) is not None
            exports = rope.module_export_names(module_path, allow_assignments=True)
            assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in exports
            assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS in exports
        finally:
            rope.close()

    def test_public_facade_opens_rope_workspace(self, tmp_path: Path) -> None:
        """Public facade returns the same ergonomic Rope workspace DSL."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            state = rope.module_semantic_state(module_path)
            assert any(
                class_info.name == c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS
                for class_info in state.class_infos
            )
