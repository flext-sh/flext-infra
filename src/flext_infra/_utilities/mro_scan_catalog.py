"""Bootstrap-safe project and target catalog for MRO scans."""

from __future__ import annotations

from pathlib import Path

from flext_core import t
from flext_infra._constants.refactor import FlextInfraConstantsRefactor
from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
from flext_infra._models.mro_scan import FlextInfraModelsMroScan
from flext_infra._utilities.file_iteration import FlextInfraUtilitiesFileIteration
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesMroScanCatalog:
    """Resolve scan targets and Python files without importing flext_infra facade."""

    @classmethod
    def target_specs(
        cls,
        target: str,
    ) -> tuple[FlextInfraModelsMroScan.MROTargetSpec, ...]:
        """Return target specs for a normalized MRO scan target."""
        target_map: t.StrMapping = {
            "constants": "c",
            "typings": "t",
            "protocols": "p",
            "models": "m",
            "utilities": "u",
        }
        alias = target_map.get(target)
        specs = FlextInfraConstantsRefactor.MRO_TARGET_SPECS
        return (
            tuple(spec for spec in specs if spec.family_alias == alias)
            if alias
            else specs
        )

    @staticmethod
    def target_supported(target: str) -> bool:
        """Return whether ``target`` is a supported MRO scan target."""
        return target in FlextInfraConstantsRefactor.MRO_TARGETS

    @staticmethod
    def project_roots(
        workspace_root: Path,
        project_names: t.StrSequence | None,
    ) -> t.SequenceOf[Path]:
        """Discover governed project roots through the canonical workspace path."""
        selected = frozenset(project_names or ())
        return tuple(
            path
            for path in FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
                workspace_root=workspace_root,
            )
            if not selected or path.name in selected
        )

    @staticmethod
    def python_files(project_root: Path) -> t.SequenceOf[Path]:
        """Return Python files under configured namespace scan directories."""
        scan_dirs = FlextInfraUtilitiesNamespaceConfig.namespace_scan_dirs(project_root)
        result = FlextInfraUtilitiesFileIteration.iter_python_files(
            workspace_root=project_root,
            project_roots=[project_root],
            include_tests=FlextInfraConstantsSharedInfra.DIR_TESTS in scan_dirs,
            include_examples=FlextInfraConstantsSharedInfra.DIR_EXAMPLES in scan_dirs,
            include_scripts=FlextInfraConstantsSharedInfra.DIR_SCRIPTS in scan_dirs,
            include_dynamic_dirs=FlextInfraUtilitiesNamespaceConfig.namespace_include_dynamic_dirs(
                project_root,
            ),
            src_dirs=scan_dirs,
        )
        return () if result.failure else tuple(result.value)

    @staticmethod
    def module_name(file_path: Path, project_root: Path) -> str:
        """Return import-like module name for a source path."""
        relative_path = file_path.resolve().relative_to(project_root.resolve())
        return ".".join(
            part
            for part in relative_path.with_suffix("").parts
            if part != FlextInfraConstantsSharedInfra.DEFAULT_SRC_DIR
        )

    @staticmethod
    def matches_target(
        file_path: Path,
        spec: FlextInfraModelsMroScan.MROTargetSpec,
    ) -> bool:
        """Return whether a Python file belongs to the target family."""
        return (
            file_path.name in spec.file_names
            or spec.package_directory in file_path.parts
        )


__all__: list[str] = ["FlextInfraUtilitiesMroScanCatalog"]
