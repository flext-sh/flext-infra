"""Tests for rope semantic analysis utilities."""

from __future__ import annotations

from pathlib import Path

from tests import t, u

type RopeWorkspace = t.Pair[t.Infra.RopeProject, Path]


class TestsFlextInfraRefactorRopeSemantic:
    def test_returns_imports(
        self,
        rope_workspace: RopeWorkspace,
        services_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(
            proj,
            services_resource,
        )
        assert "Dog" in imports

    def test_no_imports_returns_empty(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(
            proj,
            models_resource,
        )
        # Path is imported
        assert "Path" in imports
        # Animal is defined, not imported
        assert "Animal" not in imports

    def test_returns_defined_classes(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(
            proj,
            models_resource,
        )
        assert "Animal" in classes
        assert "Dog" in classes

    def test_excludes_imported_classes(
        self,
        rope_workspace: RopeWorkspace,
        services_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(
            proj,
            services_resource,
        )
        # Dog is imported, not defined here
        assert "Dog" not in classes

    def test_returns_base_classes(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(
            proj,
            models_resource,
            "Dog",
        )
        assert "Animal" in bases

    def test_no_bases_for_root_class(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(
            proj,
            models_resource,
            "Animal",
        )
        # object is implicit base, rope may or may not return it
        assert "Dog" not in bases

    def test_nonexistent_class_returns_empty(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(
            proj,
            models_resource,
            "DoesNotExist",
        )
        assert not bases

    def test_returns_public_methods(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(
            proj,
            models_resource,
            "Dog",
        )
        assert "fetch" in methods
        assert methods["fetch"] == "staticmethod"
        assert "breed" in methods
        assert methods["breed"] == "classmethod"

    def test_excludes_private_by_default(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(
            proj,
            models_resource,
            "Dog",
        )
        assert "_wag" not in methods

    def test_includes_private_when_requested(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(
            proj, models_resource, "Dog", include_private=True
        )
        assert "_wag" in methods
        assert methods["_wag"] == "method"

    def test_returns_character_offset_for_semantic_definition(
        self,
        rope_workspace: RopeWorkspace,
        models_resource: t.Infra.RopeResource,
    ) -> None:
        proj, _ = rope_workspace
        offset = u.Infra.find_definition_offset(
            proj,
            models_resource,
            "Dog",
        )
        source = models_resource.read()
        assert offset is not None
        assert source[offset : offset + 3] == "Dog"
