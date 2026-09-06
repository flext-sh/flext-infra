"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainRequirement:
    """Toolchain requirements tolerate compatible Python patch drift."""

    def test_python_requirement_uses_declared_minor_as_floor(self) -> None:
        """The declared Python minor remains the lower compatibility bound."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(
            toolchain.python_required_version, has=f">={toolchain.python_version},<"
        )

    def test_python_requirement_rejects_the_next_minor(self) -> None:
        """Python minor upgrades remain an explicit SSOT migration."""
        toolchain = config.Infra.codegen.toolchain
        major, _, minor = toolchain.python_version.partition(".")

        tm.that(toolchain.python_required_version, has=f",<{major}.{int(minor) + 1}")

    def test_every_fleet_binary_uses_the_latest_selector(self) -> None:
        """Exact binary releases belong only to the generated mise.lock."""
        toolchain = config.Infra.codegen.toolchain
        fields = (
            "uv_version",
            "kubectl_version",
            "helm_version",
            "kind_version",
            "direnv_version",
            "taplo_version",
            "ast_grep_version",
            "gitleaks_version",
            "scc_version",
            "kubeconform_version",
            "qlty_version",
            "go_version",
        )

        tm.that({getattr(toolchain, field) for field in fields}, eq={"latest"})
        tm.that({toolchain.beads.version, toolchain.gascity.version}, eq={"latest"})
        for removed in (
            "dependency_cooldown_days",
            "dependency_cooldown_exclusions",
            "dependency_cooldown_overrides",
            "uv_exclude_newer",
        ):
            tm.that(type(toolchain).model_fields, lacks=removed)


__all__: tuple[str, ...] = ()
