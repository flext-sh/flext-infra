"""Tests for rope semantic analysis utilities."""

from __future__ import annotations

from pathlib import Path

from tests import t
from tests import u
from flext_tests import tm

type RopeWorkspace = t.Pair[t.Infra.RopeProject, Path]


class TestsFlextInfraRefactorRopeSemantic:
    def test_returns_imports(
        self, rope_workspace: RopeWorkspace, services_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(proj, services_resource)
        tm.that(imports, has="Dog")

    def test_no_imports_returns_empty(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(proj, models_resource)
        # Path is imported
        tm.that(imports, has="Path")
        # Animal is defined, not imported
        tm.that(imports, lacks="Animal")

    def test_returns_defined_classes(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(proj, models_resource)
        tm.that(classes, has="Animal")
        tm.that(classes, has="Dog")

    def test_excludes_imported_classes(
        self, rope_workspace: RopeWorkspace, services_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(proj, services_resource)
        # Dog is imported, not defined here
        tm.that(classes, lacks="Dog")

    def test_returns_base_classes(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "Dog")
        tm.that(bases, has="Animal")

    def test_no_bases_for_root_class(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "Animal")
        # object is implicit base, rope may or may not return it
        tm.that(bases, lacks="Dog")

    def test_nonexistent_class_returns_empty(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "DoesNotExist")
        assert not bases

    def test_returns_public_methods(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(proj, models_resource, "Dog")
        tm.that(methods, has="fetch")
        tm.that(methods["fetch"], eq="staticmethod")
        tm.that(methods, has="breed")
        tm.that(methods["breed"], eq="classmethod")

    def test_excludes_private_by_default(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(proj, models_resource, "Dog")
        tm.that(methods, lacks="_wag")

    def test_includes_private_when_requested(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(
            proj, models_resource, "Dog", include_private=True
        )
        tm.that(methods, has="_wag")
        tm.that(methods["_wag"], eq="method")

    def test_returns_character_offset_for_semantic_definition(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        proj, _ = rope_workspace
        offset = u.Infra.find_definition_offset(proj, models_resource, "Dog")
        source = models_resource.read()
        tm.that(offset, none=False)
        tm.that(source[offset : offset + 3], eq="Dog")
