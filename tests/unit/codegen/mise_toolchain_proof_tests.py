"""Npm-free toolchain contract and the setup reality proof.

The toolchain model refuses an npm-backed tool at load, and the reality proof
runs real executables on the real filesystem: a binary escaping its install
root or reporting another version fails, and the defects surface in proof
order (lock identity, then containment, then version).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from flext_infra import config, m, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.mise_toolchain_proof import FlextInfraCodegenMiseToolchainProof
from tests import c, tm


class TestsFlextInfraMiseToolchainProof:
    """Public behavior of the npm-free toolchain and its reality proof."""

    TOOL = "probe-tool"
    CHECKSUM = "sha256:00"

    @staticmethod
    def _repository_root() -> Path:
        """Resolve the real checkout supplying the managed tool and lock.

        Returns:
            The native repository root.

        """
        return tm.ok(
            u.Infra.git_repository_root(
                m.Infra.GitRepoRequest(repo_root=Path(__file__).parent)
            )
        ).repository_root

    @staticmethod
    def _native_entry() -> m.Infra.MiseToolEntry:
        """Read the declared UV probe from the production configuration.

        Returns:
            The configured native tool entry.

        """
        return next(
            tool
            for tool in config.Infra.codegen.toolchain.tools
            if tool.name == c.Infra.UV
        )

    @classmethod
    def _native_version(cls) -> str:
        """Read the UV version through the public lock-identity boundary.

        Returns:
            The version authenticated against the current tool declaration.

        """
        lock = tm.ok(
            u.Cli.toml_read_json(cls._repository_root() / c.Infra.MISE_LOCK_FILENAME),
        )
        version, _ = tm.ok(
            FlextInfraCodegenMiseToolchainProof.lock_identity(
                cls._native_entry(),
                lock,
                tm.ok(FlextInfraCodegenMiseToolchainProof.current_platform()),
            ),
        )
        return version

    @classmethod
    def test_setup_proof_requires_the_declared_runtime_lint_tools(cls) -> None:
        """The real setup proof validates the lint inventory in its own runtime."""
        root = cls._repository_root()
        uv = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        tm.ok(
            FlextInfraCodegenMiseToolchainProof(
                repository_root=root, uv_executable=uv
            ).execute()
        )

    @classmethod
    def test_uv_binary_belongs_to_its_declared_mise_installation(cls) -> None:
        """A bundled executable from another tool cannot own UV resolution."""
        root = cls._repository_root()
        entry = cls._native_entry()
        reader = tm.ok(u.Infra.managed_mise_self(root))
        installation = tm.ok(
            u.Cli.run_raw(
                (
                    str(reader),
                    "-C",
                    str(root),
                    "where",
                    entry.selector or entry.name,
                ),
                cwd=root,
                timeout=c.Infra.TIMEOUT_SHORT,
            )
        )
        tm.that(u.Cli.process_succeeded(installation.outcome), eq=True)
        tm.that(installation.stderr, eq="")
        binary = tm.ok(u.Infra.managed_mise_binary(entry.name, root))
        tm.that(
            binary.is_relative_to(Path(installation.stdout.strip()).resolve()),
            eq=True,
        )

    @classmethod
    def _entry(cls) -> m.Infra.MiseToolEntry:
        """Bind the scenario identity to the real configured UV probe.

        Returns:
            The scenario tool entry.

        """
        return m.Infra.MiseToolEntry.model_validate(
            cls._native_entry().model_dump(round_trip=True)
            | {
                "name": cls.TOOL,
                "selector": None,
                "version": c.Infra.MISE_MOVING_SELECTOR,
            },
        )

    @classmethod
    def _lock(
        cls,
        *,
        checksum: bool = True,
        version: str | None = None,
    ) -> t.JsonMapping:
        """Build the scenario mise.lock mapping of the tool.

        Returns:
            The scenario lock mapping.

        """
        platform = tm.ok(FlextInfraCodegenMiseToolchainProof.current_platform())
        platform_key = c.Infra.MISE_LOCK_PLATFORM_KEY.format(platform=platform)
        section: t.JsonDict = (
            {"checksum": cls.CHECKSUM} if checksum else {"url": platform}
        )
        locked: t.JsonDict = {
            "version": cls._native_version() if version is None else version,
            platform_key: section,
        }
        versions: list[t.JsonValue] = [locked]
        tools: t.JsonDict = {cls.TOOL: versions}
        return {"tools": tools}

    @classmethod
    def _executable(cls, path: Path) -> Path:
        """Copy the managed native UV binary into an isolated scenario root.

        Returns:
            The executable path.

        """
        path.parent.mkdir(parents=True, exist_ok=True)
        source = tm.ok(
            u.Infra.managed_mise_binary(c.Infra.UV, cls._repository_root()),
        )
        _ = shutil.copy2(source, path)
        return path

    @classmethod
    def _prove(
        cls,
        root: Path,
        binary: Path,
        *,
        checksum: bool = True,
        version: str | None = None,
    ) -> str | None:
        """Run the public proof and return its first defect, if any.

        Returns:
            The failure message, or None when the tool is proven.

        """
        result = FlextInfraCodegenMiseToolchainProof.prove(
            cls._entry(),
            cls._lock(checksum=checksum, version=version),
            tm.ok(FlextInfraCodegenMiseToolchainProof.current_platform()),
            (root, binary),
        )
        return result.error if result.failure else None

    def test_contained_binary_reporting_the_lock_version_is_proven(
        self,
        tmp_path: Path,
    ) -> None:
        """A self-contained binary that reports the locked version passes."""
        root = tmp_path / "installs" / self.TOOL / self._native_version()
        self._executable(root / "libexec" / self.TOOL)
        link = root / "bin" / self.TOOL
        link.parent.mkdir(parents=True)
        link.symlink_to(Path("..") / "libexec" / self.TOOL)

        result = FlextInfraCodegenMiseToolchainProof.prove(
            self._entry(),
            self._lock(),
            tm.ok(FlextInfraCodegenMiseToolchainProof.current_platform()),
            (root, link),
        )

        tm.that(tm.ok(result), has=self.CHECKSUM)

    def test_binary_escaping_its_install_root_fails(self, tmp_path: Path) -> None:
        """A bin link into a foreign tree (the bun walk-up shape) fails."""
        root = tmp_path / "installs" / self.TOOL / self._native_version()
        foreign = self._executable(tmp_path / "outside" / self.TOOL)
        link = root / "bin" / self.TOOL
        link.parent.mkdir(parents=True)
        link.symlink_to(foreign)

        tm.that(self._prove(root, link) or "", has="outside its install root")

    def test_version_mismatch_fails(self, tmp_path: Path) -> None:
        """A contained binary reporting another release fails."""
        root = tmp_path / "installs" / self.TOOL / self._native_version()
        binary = self._executable(root / "bin" / self.TOOL)

        tm.that(
            self._prove(root, binary, version=f"{self._native_version()}.mismatch")
            or "",
            has="does not report the locked",
        )

    def test_proof_reports_defects_in_order(self, tmp_path: Path) -> None:
        """Lock identity precedes containment, which precedes the version."""
        version = self._native_version()
        root = tmp_path / "installs" / self.TOOL / version
        foreign = self._executable(tmp_path / "outside" / self.TOOL)
        escaping = root / "bin" / self.TOOL
        escaping.parent.mkdir(parents=True)
        escaping.symlink_to(foreign)
        contained = self._executable(root / "libexec" / self.TOOL)
        unexpected = f"{version}.mismatch"

        tm.that(
            self._prove(root, escaping, checksum=False, version=unexpected) or "",
            has="checksum",
        )
        tm.that(
            self._prove(root, escaping, version=unexpected) or "",
            has="outside its install root",
        )
        tm.that(
            self._prove(root, contained, version=unexpected) or "",
            has="does not report the locked",
        )

    @staticmethod
    def test_toolchain_rejects_an_npm_selector_at_load() -> None:
        """The fleet toolchain has no npm backend: an npm: tool is refused."""
        toolchain = config.Infra.codegen.toolchain
        declared = {
            name: value
            for name, value in toolchain.model_dump().items()
            if name in m.Infra.ToolchainSpec.model_fields
        }
        npm_tool = {
            "name": "npm-tool",
            "selector": "npm:some-cli",
            "version": "latest",
            "version_probe": {
                "binary": "some-cli",
                "arguments": ["--version"],
                "pattern": "{version}",
            },
        }

        with pytest.raises(ValueError, match="no npm backend"):
            m.Infra.ToolchainSpec.model_validate({
                **declared,
                "tools": [*declared["tools"], npm_tool],
            })

    @staticmethod
    def test_declared_toolchain_carries_no_npm_tool() -> None:
        """Every loaded tool key is a native, checksum-locked selector."""
        keys = config.Infra.codegen.toolchain.tool_keys.values()

        tm.that([key for key in keys if key.startswith("npm:")], eq=[])

    @staticmethod
    def test_generation_retires_the_prettier_projections(tmp_path: Path) -> None:
        """Generated .prettierrc/.prettierignore retire; a hand-owned one stays."""
        evidence = {
            retired.path: retired.evidence
            for retired in config.Infra.codegen.retired_projections
            if not isinstance(retired, str)
        }
        generated = tmp_path / "generated"
        hand_owned = tmp_path / "hand-owned"
        for name in (".prettierrc", ".prettierignore"):
            generated.mkdir(exist_ok=True)
            hand_owned.mkdir(exist_ok=True)
            (generated / name).write_text(f"{evidence[name]}\n", encoding="utf-8")
            (hand_owned / name).write_text("{}\n", encoding="utf-8")

        retired = {
            plan.path.name
            for plan in tm.ok(
                FlextInfraCodegenConform.retired_projection_plans(
                    generated,
                    c.Infra.MakeProfile.STANDALONE,
                ),
            )
            if plan.desired_content is None
        }
        preserved = {
            plan.path.name
            for plan in tm.ok(
                FlextInfraCodegenConform.retired_projection_plans(
                    hand_owned,
                    c.Infra.MakeProfile.STANDALONE,
                ),
            )
            if plan.desired_content is None
        }

        tm.that(retired >= {".prettierrc", ".prettierignore"}, eq=True)
        tm.that(preserved & {".prettierrc", ".prettierignore"}, eq=set[str]())
