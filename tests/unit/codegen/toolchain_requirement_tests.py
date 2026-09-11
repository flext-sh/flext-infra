"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config, u
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

    def test_uv_cooldown_is_scoped_away_from_typed_tools(self) -> None:
        """Runtime libraries retain the window while typed tools are uncapped."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(
            toolchain.uv_exclude_newer, eq=f"{toolchain.dependency_cooldown_days} days"
        )
        tm.that(toolchain.dependency_cooldown_exclusions, has="cryptography")
        tm.that(
            config.Infra.codegen.python_tool_distributions,
            has=["hatchling", "ruff", "pytest", "rumdl"],
        )

    def test_every_owned_python_tool_projects_from_one_catalog(self) -> None:
        """Build, gates, docs, release, and scaffold requirements are uncapped."""
        codegen = config.Infra.codegen
        catalog = set(codegen.python_tool_distributions)
        scaffold_owned = {
            name
            for requirement in (
                *codegen.scaffold.build.requirements,
                *codegen.scaffold.project.dev,
            )
            if (name := u.Infra.dep_name(requirement)) is not None
        }
        executable_owners = {
            "actionlint-py",
            "bandit",
            "deptry",
            "hatchling",
            "mkdocs",
            "mypy",
            "pip-audit",
            "pre-commit",
            "pyrefly",
            "pyright",
            "pytest",
            codegen.release.tool,
            "ruff",
            "rumdl",
            "vulture",
            "yamlfix",
        }

        tm.that(scaffold_owned <= catalog, eq=True)
        tm.that(executable_owners <= catalog, eq=True)
        tm.that(len(catalog), eq=len(codegen.python_tool_distributions))

    def test_runtime_dependency_profiles_never_enter_tool_catalog(self) -> None:
        """Known runtime libraries remain governed by the seven-day window."""
        codegen = config.Infra.codegen
        runtime_libraries = {
            name
            for profile in codegen.scaffold.project.dependency_profiles
            for requirement in profile.runtime
            if (name := u.Infra.dep_name(requirement)) is not None
        }

        tm.that(
            runtime_libraries.isdisjoint(codegen.python_tool_distributions), eq=True
        )
        tm.that(
            set(codegen.python_tool_distributions).isdisjoint(
                {"requests", "jinja2", "pydantic", "setuptools-scm"}
            ),
            eq=True,
        )


__all__: tuple[str, ...] = ()
