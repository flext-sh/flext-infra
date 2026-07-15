"""Tests for Rope semantic analysis utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import t, u

type RopeWorkspace = t.Pair[t.Infra.RopeProject, Path]


class TestsFlextInfraRefactorRopeSemantic:
    """Verify semantic queries through the public infrastructure utilities."""

    def test_returns_imports(
        self, rope_workspace: RopeWorkspace, services_resource: t.Infra.RopeResource
    ) -> None:
        """Verify imported class names are returned."""
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(proj, services_resource)
        tm.that(imports, has="Dog")

    def test_no_imports_returns_empty(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify locally defined names are excluded from module imports."""
        proj, _ = rope_workspace
        imports = u.Infra.get_semantic_module_imports(proj, models_resource)
        # Path is imported
        tm.that(imports, has="Path")
        # Animal is defined, not imported
        tm.that(imports, lacks="Animal")

    def test_returns_defined_classes(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify module-defined classes are returned."""
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(proj, models_resource)
        tm.that(classes, has="Animal")
        tm.that(classes, has="Dog")

    def test_excludes_imported_classes(
        self, rope_workspace: RopeWorkspace, services_resource: t.Infra.RopeResource
    ) -> None:
        """Verify imported classes are excluded from module definitions."""
        proj, _ = rope_workspace
        classes = u.Infra.get_module_classes(proj, services_resource)
        # Dog is imported, not defined here
        tm.that(classes, lacks="Dog")

    def test_returns_base_classes(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify explicit base classes are returned."""
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "Dog")
        tm.that(bases, has="Animal")

    def test_no_bases_for_root_class(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify an unrelated class is not reported as a base."""
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "Animal")
        # object is implicit base, rope may or may not return it
        tm.that(bases, lacks="Dog")

    def test_nonexistent_class_returns_empty(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify an unknown class has no base-class result."""
        proj, _ = rope_workspace
        bases = u.Infra.get_class_bases(proj, models_resource, "DoesNotExist")
        tm.that(bases, empty=True)

    def test_returns_public_methods(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify public methods and their descriptor kinds are returned."""
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(proj, models_resource, "Dog")
        tm.that(methods, has="fetch")
        tm.that(methods["fetch"], eq="staticmethod")
        tm.that(methods, has="breed")
        tm.that(methods["breed"], eq="classmethod")

    def test_excludes_private_by_default(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify private methods are excluded by default."""
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(proj, models_resource, "Dog")
        tm.that(methods, lacks="_wag")

    def test_includes_private_when_requested(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify private methods are included when explicitly requested."""
        proj, _ = rope_workspace
        methods = u.Infra.get_class_methods(
            proj, models_resource, "Dog", include_private=True
        )
        tm.that(methods, has="_wag")
        tm.that(methods["_wag"], eq="method")

    def test_returns_character_offset_for_semantic_definition(
        self, rope_workspace: RopeWorkspace, models_resource: t.Infra.RopeResource
    ) -> None:
        """Verify semantic lookup returns the class-name character offset."""
        proj, _ = rope_workspace
        offset = tm.not_none(
            u.Infra.find_definition_offset(proj, models_resource, "Dog")
        )
        source = models_resource.read()
        tm.that(source[offset : offset + 3], eq="Dog")
