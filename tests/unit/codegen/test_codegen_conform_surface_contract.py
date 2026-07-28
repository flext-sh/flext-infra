"""Typed conform surface dispatch contracts."""

from __future__ import annotations

from flext_infra import c
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestsCodegenConformSurfaceContract:
    """Each public surface selects a distinct conform plan shape."""

    def test_dependencies_selects_only_dependency_pyproject_work(self) -> None:
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.DEPENDENCIES
        )

        tm.that(contract.dependencies_only, eq=True)
        tm.that(contract.destinations, eq=frozenset({c.Infra.PYPROJECT_FILENAME}))
        tm.that(contract.templates, eq=False)

    def test_pyproject_selects_complete_pyproject_without_templates(self) -> None:
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.PYPROJECT
        )

        tm.that(contract.dependencies_only, eq=False)
        tm.that(contract.pyproject, eq=True)
        tm.that(contract.templates, eq=False)

    def test_makefile_selects_only_makefile_without_pyproject(self) -> None:
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.MAKEFILE
        )

        tm.that(contract.destinations, eq=frozenset({c.Infra.MAKEFILE_FILENAME}))
        tm.that(contract.pyproject, eq=False)
        tm.that(contract.templates, eq=True)

    def test_all_completes_every_governed_surface(self) -> None:
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.ALL
        )

        tm.that(contract.destinations, eq=None)
        tm.that(contract.complete_governed, eq=True)
        tm.that(contract.pyproject, eq=True)
        tm.that(contract.templates, eq=True)
