"""Typed conform surface dispatch contracts."""

from __future__ import annotations

from flext_infra import c
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsCodegenConformSurfaceContract:
    """Each public surface selects a distinct conform plan shape."""

    def test_dependencies_selects_only_dependency_pyproject_work(self) -> None:
        contract = FlextInfraCodegenConform._surface_contract(
            c.Infra.CodegenConformSurface.DEPENDENCIES
        )

        assert contract.dependencies_only
        assert contract.destinations == frozenset({c.Infra.PYPROJECT_FILENAME})
        assert not contract.templates

    def test_pyproject_selects_complete_pyproject_without_templates(self) -> None:
        contract = FlextInfraCodegenConform._surface_contract(
            c.Infra.CodegenConformSurface.PYPROJECT
        )

        assert not contract.dependencies_only
        assert contract.pyproject
        assert not contract.templates

    def test_makefile_selects_only_makefile_without_pyproject(self) -> None:
        contract = FlextInfraCodegenConform._surface_contract(
            c.Infra.CodegenConformSurface.MAKEFILE
        )

        assert contract.destinations == frozenset({c.Infra.MAKEFILE_FILENAME})
        assert not contract.pyproject
        assert contract.templates

    def test_all_completes_every_governed_surface(self) -> None:
        contract = FlextInfraCodegenConform._surface_contract(
            c.Infra.CodegenConformSurface.ALL
        )

        assert contract.destinations is None
        assert contract.complete_governed
        assert contract.pyproject
        assert contract.templates
