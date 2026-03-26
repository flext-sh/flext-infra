"""Tests for rope semantic analysis utilities (get_module_imports, get_module_classes, etc.)."""
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportArgumentType=false

from __future__ import annotations

from pathlib import Path

import pytest
from rope.base.project import Project as RopeProject
from rope.base.resources import File as RopeFile

from flext_infra._utilities.rope import FlextInfraUtilitiesRope as R


@pytest.fixture
def rope_workspace(tmp_path: Path) -> tuple[RopeProject, Path]:
    """Create a temp workspace with a rope project and sample modules."""
    pkg = tmp_path / "example"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    (pkg / "models.py").write_text(
        """\
from pathlib import Path


class Animal:
    \"\"\"Base class.\"\"\"

    def speak(self) -> str:
        return ""


class Dog(Animal):
    @staticmethod
    def fetch(item: str) -> str:
        return item

    @classmethod
    def breed(cls) -> "Dog":
        return cls()

    def _wag(self) -> None:
        pass


SPECIES_COUNT = 42
""",
    )

    (pkg / "services.py").write_text(
        """\
from example.models import Dog

active_dog = Dog()
""",
    )

    proj = RopeProject(str(tmp_path), ropefolder=None, save_objectdb=False)
    return proj, tmp_path


@pytest.fixture
def models_resource(rope_workspace: tuple[RopeProject, Path]) -> RopeFile:
    proj, _ = rope_workspace
    res = proj.get_resource("example/models.py")
    assert isinstance(res, RopeFile)
    return res


@pytest.fixture
def services_resource(rope_workspace: tuple[RopeProject, Path]) -> RopeFile:
    proj, _ = rope_workspace
    res = proj.get_resource("example/services.py")
    assert isinstance(res, RopeFile)
    return res


class TestGetModuleImports:
    def test_returns_imports(
        self,
        rope_workspace: tuple[RopeProject, Path],
        services_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        imports = R.get_module_imports(proj, services_resource)
        assert "Dog" in imports

    def test_no_imports_returns_empty(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        imports = R.get_module_imports(proj, models_resource)
        # Path is imported
        assert "Path" in imports
        # Animal is defined, not imported
        assert "Animal" not in imports


class TestGetModuleClasses:
    def test_returns_defined_classes(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        classes = R.get_module_classes(proj, models_resource)
        assert "Animal" in classes
        assert "Dog" in classes

    def test_excludes_imported_classes(
        self,
        rope_workspace: tuple[RopeProject, Path],
        services_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        classes = R.get_module_classes(proj, services_resource)
        # Dog is imported, not defined here
        assert "Dog" not in classes


class TestGetClassBases:
    def test_returns_base_classes(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        bases = R.get_class_bases(proj, models_resource, "Dog")
        assert "Animal" in bases

    def test_no_bases_for_root_class(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        bases = R.get_class_bases(proj, models_resource, "Animal")
        # object is implicit base, rope may or may not return it
        assert "Dog" not in bases

    def test_nonexistent_class_returns_empty(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        bases = R.get_class_bases(proj, models_resource, "DoesNotExist")
        assert bases == []


class TestGetClassMethods:
    def test_returns_public_methods(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        methods = R.get_class_methods(proj, models_resource, "Dog")
        assert "fetch" in methods
        assert methods["fetch"] == "staticmethod"
        assert "breed" in methods
        assert methods["breed"] == "classmethod"

    def test_excludes_private_by_default(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        methods = R.get_class_methods(proj, models_resource, "Dog")
        assert "_wag" not in methods

    def test_includes_private_when_requested(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        methods = R.get_class_methods(
            proj, models_resource, "Dog", include_private=True
        )
        assert "_wag" in methods
        assert methods["_wag"] == "method"

    def test_nonexistent_class_returns_empty(
        self,
        rope_workspace: tuple[RopeProject, Path],
        models_resource: RopeFile,
    ) -> None:
        proj, _ = rope_workspace
        methods = R.get_class_methods(proj, models_resource, "DoesNotExist")
        assert methods == {}
