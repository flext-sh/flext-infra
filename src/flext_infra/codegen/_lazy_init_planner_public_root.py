"""Root public-export decisions for the lazy-init planner."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    if TYPE_CHECKING:
        lazy_init: m.Infra.LazyInitConfig
        rope_workspace: p.Infra.RopeWorkspaceDsl
        repository_root: Path

    def _load_exports_manifest(self) -> frozenset[str] | None:
        """Load declarative exports manifest if configured.

        Returns the set of declared public export names for the current package,
        or None if no manifest is configured or the package is not in the manifest.
        """
        manifest_path_str = getattr(self.lazy_init, "exports_manifest_path", None)
        if not manifest_path_str:
            return None
        manifest_path = self.repository_root / manifest_path_str
        if not manifest_path.is_file():
            u.Cli.info(f"lazy-init: manifest not found at {manifest_path}")
            return None
        try:
            import yaml

            manifest = yaml.safe_load(
                manifest_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            )
            if not isinstance(manifest, dict):
                return None
            package_exports = manifest.get(self._current_package_for_manifest())
            if not isinstance(package_exports, list):
                return None
            result = frozenset(str(name) for name in package_exports)
            u.Cli.info(
                f"lazy-init: loaded manifest for {self._current_package_for_manifest()} with {len(result)} exports"
            )
            return result
        except Exception as e:
            u.Cli.info(f"lazy-init: manifest load failed: {e}")
            return None

    def _current_package_for_manifest(self) -> str:
        """Return the package key used in the exports manifest.

        The manifest uses package names relative to the repository root
        (e.g., "flext_infra", "tests").
        """
        # This will be overridden by the planner context
        return getattr(self, "_manifest_package_key", "")

    def _filter_public_root_exports(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
    ) -> t.Pair[set[str], t.MutableLazyAliasMap]:
        # Set the manifest package key for this context
        self._manifest_package_key = context.current_pkg

        # Load declarative manifest if configured (RC-B: SSOT for public exports)
        manifest_contract = self._load_exports_manifest()

        # Use manifest as primary contract, fall back to scanned __init__.py
        declared_contract = manifest_contract
        if declared_contract is None:
            declared_contract = self._declared_root_contract(context)

        u.Cli.info(
            f"lazy-init: filtering exports for {context.current_pkg} ({context.pkg_dir}): export_names={len(export_names)}, lazy_map={len(lazy_map)}, eager_names={len(eager_names)}, declared_contract={len(declared_contract) if declared_contract else 0}"
        )

        governed_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if self._is_declared_root_export(
                name,
                target,
                root_pkg=context.current_pkg,
                declared_contract=declared_contract,
            )
        }
        u.Cli.info(
            f"lazy-init: governed_lazy_map={len(governed_lazy_map)} after filtering"
        )
        lazy_map.clear()
        lazy_map.update(governed_lazy_map)
        public_export_names = {
            name
            for name in export_names
            if name in eager_names
            or (name in governed_lazy_map and name not in c.Infra.PUBLISHED_ALL_EXCLUDE)
        }
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in public_export_names
        }
        u.Cli.info(f"lazy-init: public_export_names={len(public_export_names)}")

        # Validate scan against manifest (scan-as-validator)
        if manifest_contract is not None:
            self._validate_scan_against_manifest(
                context=context,
                manifest_contract=manifest_contract,
                scan_exports=public_export_names,
            )

        return public_export_names, filtered_lazy_map

    def _validate_scan_against_manifest(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        manifest_contract: frozenset[str],
        scan_exports: set[str],
    ) -> None:
        """Validate that scan matches manifest (RC-B: scan-as-validator).

        Divergence between scan and manifest = gen failure (never silent mutation).
        """
        u.Cli.info(
            f"lazy-init: validating manifest ({len(manifest_contract)} exports) against scan ({len(scan_exports)} exports)"
        )
        missing_in_scan = manifest_contract - scan_exports
        extra_in_scan = scan_exports - manifest_contract
        u.Cli.info(
            f"lazy-init: missing_in_scan={len(missing_in_scan)}, extra_in_scan={len(extra_in_scan)}"
        )
        if missing_in_scan:
            u.Cli.info(f"lazy-init: missing examples: {sorted(missing_in_scan)[:5]}")
        if extra_in_scan:
            u.Cli.info(f"lazy-init: extra examples: {sorted(extra_in_scan)[:5]}")
        if missing_in_scan or extra_in_scan:
            details = []
            if missing_in_scan:
                details.append(
                    f"missing in scan (orphaned in manifest): {sorted(missing_in_scan)}"
                )
            if extra_in_scan:
                details.append(
                    f"extra in scan (undeclared in manifest): {sorted(extra_in_scan)}"
                )
            u.Cli.info("lazy-init: RAISING ValueError for divergence")
            msg = (
                f"lazy-init public export contract divergence for {context.current_pkg}: "
                f"{'; '.join(details)}. Update config/exports.yaml or restore deleted modules."
            )
            raise ValueError(msg)
        u.Cli.info("lazy-init: validation passed")

    def _declared_root_contract(
        self, context: m.Infra.LazyInitPackageContext
    ) -> frozenset[str] | None:
        if context.generated_init or not context.init_path.is_file():
            return None
        # If the project declares subpackages (e.g. services/), root aggregates from sources;
        # only single-directory/flat projects can declare an ABI filter via manual __init__.py.
        entry = self.rope_workspace.package(context.pkg_dir)
        if entry is not None and entry.descendant_child_dirs:
            return None
        constants_path = context.pkg_dir / c.Infra.CONSTANTS_PY
        if self.rope_workspace.resource(constants_path) is not None:
            imports = self.rope_workspace.semantic(constants_path).declared_imports
            if any(
                name != "annotations" and not target.startswith("__future__")
                for name, target in imports.items()
            ):
                return None
        contract = frozenset(
            self.rope_workspace.exports(
                context.init_path,
                export_options=m.Infra.ExportOptions(allow_assignments=True),
            )
        )
        return contract or None

    @staticmethod
    def _is_declared_root_export(
        name: str,
        target: t.StrPair,
        *,
        root_pkg: str,
        declared_contract: frozenset[str] | None,
    ) -> bool:
        # Private names never widen the public root ABI.
        if name.startswith("_"):
            return False
        if declared_contract is not None and name not in declared_contract:
            return False
        module_path, _attr_name = target
        runtime_module = f"{module_path.rsplit('.', maxsplit=1)[-1]}.py"
        if u.Infra.runtime_singleton_export(runtime_module) == name:
            return True
        if (module_path == f"{root_pkg}._config" and name.endswith("Config")) or (
            module_path == f"{root_pkg}._settings" and name.endswith("Settings")
        ):
            return True
        if module_path == root_pkg:
            return True
        if module_path.startswith(f"{root_pkg}."):
            # Any underscore-prefixed source segment
            # marks the owner as private; the symbol stays behind its facade.
            tail = module_path[len(root_pkg) + 1 :].split(".")
            return not any(
                part.startswith("_") and not part.startswith("__") for part in tail
            )
        return True


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
