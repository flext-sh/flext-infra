"""Canonical loader for the codegen ``.gen`` requirements contract.

Single owner for locating, loading, and validating ``codegen.gen.yaml``;
``codegen.conform`` and the release artifact archive both consume this
helper so the resolution and validation rules cannot drift apart.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from flext_core import r
from flext_infra import c, m, u

if TYPE_CHECKING:
    from flext_infra import p


@final
class GenRequirementsLoader:
    """Load and validate the ``.gen`` requirements contract exactly once."""

    @classmethod
    def _contract_path(cls, anchor: Path) -> Path:
        """Resolve the contract path from one in-package anchor module.

        Installed (wheel) layout ships config inside the package; the source
        checkout keeps it at the repository root next to ``src/``.
        """
        package_root = anchor.resolve().parent.parent
        gen_path = (
            package_root / c.Infra.CODEGEN_CONFIG_DIR / c.Infra.CODEGEN_GEN_FILENAME
        )
        if not gen_path.is_file():
            gen_path = (
                package_root.parent.parent
                / c.Infra.CODEGEN_CONFIG_DIR
                / c.Infra.CODEGEN_GEN_FILENAME
            )
        return gen_path

    @classmethod
    def load(cls, anchor: Path) -> p.Result[m.Infra.GenRequirementsSpec]:
        """Locate, load, and validate the contract relative to ``anchor``."""
        gen_path = cls._contract_path(anchor)
        if not gen_path.is_file():
            return r[m.Infra.GenRequirementsSpec].fail(
                f"generation requirements contract is absent: {gen_path}; "
                f"{c.Infra.CODEGEN_GEN_FILENAME} is the mandatory conformance gate"
            )
        loaded = u.Cli.config_load(gen_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.GenRequirementsSpec].fail(
                f"failed to load generation requirements: {loaded.error or gen_path}"
            )
        try:
            requirements = m.Infra.GenRequirementsSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.GenRequirementsSpec].fail(
                f"invalid .gen requirements contract at {gen_path}: {exc}",
                exception=exc,
            )
        return r[m.Infra.GenRequirementsSpec].ok(requirements)


__all__: list[str] = ["GenRequirementsLoader"]
