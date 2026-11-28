"""Conformance preserves authored Git refs; only ``make upg`` writes uv.lock.

An explicit requirement retains its declared URL and ref, including a commit.
Detecting an integration line is a separate operation: a commit supplies no
branch, and a hand-authored ``project.flext_source`` must declare that line.
Generation removes obsolete projected overrides without inventing a new ref.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsFlextInfraUpgOwnedDependencyPin:
    """Conformance preserves sources while upgrade owns lock resolution."""

    PROVIDER = "https://example.org/flext"
    LINE = "0.12.0-dev"
    COMMIT = "b" * 40

    @classmethod
    def _requirement(cls, name: str, ref: str) -> str:
        return f"{name} @ git+{cls.PROVIDER}/{name}.git@{ref}"

    @classmethod
    def _consumer(
        cls,
        root: Path,
        core_ref: str,
        infra_ref: str = LINE,
        flext_source: str = "",
    ) -> str:
        """Write one standalone consumer declaring the family on the given refs.

        Returns:
            The resulting ``str``.

        """
        config_dir = root / c.CONFIG_DIR_NAME
        config_dir.mkdir(parents=True)
        repository: t.JsonDict = {}
        if flext_source:
            repository["project"] = {
                **u.Tests.project_spec("consumer").model_dump(mode="json"),
                "flext_source": flext_source,
            }
        tm.ok(
            u.Cli.yaml_dump(
                config_dir / c.Infra.CODEGEN_CONFIG_FILENAME,
                {"Infra": {"codegen": {"repository": repository}}},
            )
        )
        source = (
            '[project]\nname = "consumer"\nversion = "0.1.0"\n'
            f'dependencies = ["{cls._requirement("flext-core", core_ref)}"]\n'
            "[dependency-groups]\n"
            f'codegen = ["{cls._requirement("flext-infra", infra_ref)}"]\n'
            f'dev = ["{cls._requirement("flext-core", core_ref)}"]\n'
            "[tool.uv]\n"
            "override-dependencies = "
            f'["{cls._requirement("flext-core", cls.COMMIT)}"]\n'
        )
        (root / c.PYPROJECT_FILENAME).write_text(source, encoding="utf-8")
        return source

    @staticmethod
    def _conform(
        source: str,
        flext_line: p.Infra.WorkspaceIntegrationSpec | None = None,
    ) -> p.Result[str]:
        toolchain = config.Infra.codegen.toolchain
        workspace = u.Tests.workspace_spec(u.Tests.repository_ref("consumer"))
        return u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=m.Infra.UvResolutionSpec(
                link_mode=toolchain.uv_link_mode,
                cooldown_days=toolchain.dependency_cooldown_days,
                constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                environments=tuple(toolchain.uv_environments),
            ),
            options=u.Infra.PyprojectConformOptions(
                flext_line=flext_line,
            ),
        )

    def test_generation_keeps_the_line_and_drops_override_pins(
        self,
        tmp_path: Path,
    ) -> None:
        """Every internal requirement stays on its line; no override survives."""
        source = self._consumer(tmp_path, self.LINE)
        rendered = tm.ok(self._conform(source))
        for section, key in (
            ("project", "dependencies"),
            ("dependency-groups", "dev"),
            ("dependency-groups", "codegen"),
        ):
            for requirement in u.Tests.toml_strings_at(rendered, section, key):
                tm.ok(requirement.endswith(f".git@{self.LINE}"))
        tm.that(rendered, lacks=self.COMMIT)
        tm.that(rendered, lacks="override-dependencies")
        tm.that(tm.ok(self._conform(rendered)), eq=rendered)
        line = tm.ok(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=tmp_path,
            ),
        )
        tm.that((line.base_url, line.branch), eq=(self.PROVIDER, self.LINE))

    def test_explicit_commit_is_preserved_with_a_detected_line(
        self,
        tmp_path: Path,
    ) -> None:
        """A detected branch never replaces an explicitly declared commit."""
        source = self._consumer(tmp_path, self.COMMIT, self.COMMIT)
        line = m.Infra.WorkspaceIntegrationSpec(
            provider=u.Tests.provider().name,
            branch=self.LINE,
            base_url=self.PROVIDER,
        )
        rendered = tm.ok(self._conform(source, line))
        for section, key, distribution in (
            ("project", "dependencies", "flext-core"),
            ("dependency-groups", "dev", "flext-core"),
            ("dependency-groups", "codegen", "flext-infra"),
        ):
            tm.that(
                u.Tests.toml_strings_at(rendered, section, key),
                eq=(self._requirement(distribution, self.COMMIT),),
            )
        tm.that(rendered, lacks="override-dependencies")
        tm.that(tm.ok(self._conform(rendered, line)), eq=rendered)
        tm.that(tm.ok(self._conform(source)), eq=rendered)

    def test_a_fully_pinned_projection_takes_the_line_from_the_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """Commit residue declares no line: the hand-authored source does."""
        pinned = tmp_path / "pinned"
        self._consumer(pinned, self.COMMIT, self.COMMIT)
        tm.fail(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=pinned,
            ),
            has="no manifest flext_source",
        )
        declared = tmp_path / "declared"
        self._consumer(
            declared,
            self.COMMIT,
            self.COMMIT,
            flext_source=self._requirement("flext-infra", self.LINE),
        )
        line = tm.ok(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=declared,
            ),
        )
        tm.that((line.base_url, line.branch), eq=(self.PROVIDER, self.LINE))

    def test_a_hand_authored_commit_fails_loudly(self, tmp_path: Path) -> None:
        """A commit in the manifest's flext_source is a pin beside uv.lock."""
        self._consumer(
            tmp_path,
            self.COMMIT,
            self.COMMIT,
            flext_source=self._requirement("flext-infra", self.COMMIT),
        )
        tm.fail(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=tmp_path,
            ),
            has="never a commit",
        )

    def test_mixed_providers_remain_ambiguous(self, tmp_path: Path) -> None:
        """One family line: two providers on the same line still fail loudly."""
        source = self._consumer(tmp_path, self.LINE)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            source.replace(self.PROVIDER, "https://other.example.org/flext", 1),
            encoding="utf-8",
        )
        tm.fail(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=tmp_path,
            ),
            has="conflicting flext-* line sources",
        )

    def test_the_manifest_carries_no_revision_pins(self) -> None:
        """The retired manifest pin is rejected, never silently ignored."""
        retired = {
            **u.Tests.project_spec("consumer").model_dump(),
            "dependency_revisions": {"flext-core": self.COMMIT},
        }
        with u.Tests.raises(ValueError, match="dependency_revisions"):
            m.Infra.ProjectSpec.model_validate(retired)
