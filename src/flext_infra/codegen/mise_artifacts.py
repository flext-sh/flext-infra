"""Offline validation for generated Mise declarations and launchers."""

from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatchcase
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, ClassVar, TypeIs, override
from urllib.parse import urlsplit

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenMiseArtifacts(s[bool]):
    """Validate unlocked latest-version Mise declarations and launchers."""
    config_only: Annotated[
        bool,
        m.Field(
            default=False,
            alias="config-only",
            description=(
                "Validate the generated Mise payload before any tool-owned effect"
            ),
        ),
    ] = False

    @staticmethod
    def _read_toml(path: Path) -> p.Result[t.JsonMapping]:
        source = u.Cli.files_read_text(path)
        if source.failure:
            return r[t.JsonMapping].fail(source.error or f"cannot read {path.name}")
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[t.JsonMapping].fail(f"invalid TOML in {path.name}")
        return r[t.JsonMapping].ok(payload)

    @staticmethod
    def _tool_version(raw_tool: t.JsonValue) -> str | None:
        """Return one version selector from either supported Mise tool shape."""
        candidate = (
            raw_tool.get("version") if isinstance(raw_tool, Mapping) else raw_tool
        )
        return candidate.strip() if isinstance(candidate, str) else None

    @classmethod
    def _tool_specifiers(cls, payload: t.JsonMapping) -> p.Result[t.StrMapping]:
        raw_tools = payload.get("tools")
        if not isinstance(raw_tools, Mapping):
            return r[t.StrMapping].fail(".mise.toml must declare [tools]")
        specifiers: dict[str, str] = {}
        for raw_selector, raw_tool in raw_tools.items():
            if not raw_selector.strip():
                return r[t.StrMapping].fail(".mise.toml contains an invalid tool name")
            selector = raw_selector.strip()
            version = cls._tool_version(raw_tool)
            if not version:
                return r[t.StrMapping].fail(
                    f".mise.toml tool lacks a version selector: {selector}"
                )
            specifiers[selector] = version
        if not specifiers:
            return r[t.StrMapping].fail(".mise.toml must declare at least one tool")
        return r[t.StrMapping].ok(specifiers)

    @staticmethod
    def _validate_suspended_selectors(configured_tools: t.StrMapping) -> p.Result[bool]:
        """Reject dormant capabilities before download or publication."""
        patterns = config.Infra.codegen.toolchain.suspended_mise_selector_patterns
        suspended = tuple(
            selector
            for selector in configured_tools
            if any(fnmatchcase(selector, pattern) for pattern in patterns)
        )
        if suspended:
            return r[bool].fail(
                "Mise payload selects a suspended toolchain: "
                f"{', '.join(sorted(suspended))}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _assignment(content: str, name: str) -> str | None:
        prefixes = (f'{name}="', f'set "{name}=')
        for raw_line in content.splitlines():
            line = raw_line.strip()
            for prefix in prefixes:
                if line.startswith(prefix) and line.endswith('"'):
                    return line.removeprefix(prefix).removesuffix('"')
        return None

    @staticmethod
    def _is_sha256(value: str | None) -> bool:
        if value is None:
            return False
        digest = value.split(maxsplit=1)[0]
        return len(digest) == sha256().digest_size * 2 and all(
            character in "0123456789abcdef" for character in digest
        )

    @staticmethod
    def _shell_launcher_version(content: str) -> str | None:
        prefix = 'local mise_version="${MISE_VERSION:-'
        suffix = '}"'
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.startswith(prefix) and line.endswith(suffix):
                return line.removeprefix(prefix).removesuffix(suffix)
        return None

    @staticmethod
    def is_mise_release(value: str | None) -> TypeIs[str]:
        """Return whether a runtime identity is an exact Mise release."""
        if value is None:
            return False
        parts = value.split(".")
        return len(parts) == c.Infra.MISE_RELEASE_COMPONENT_COUNT and all(
            part.isdecimal() for part in parts
        )

    @classmethod
    def launcher_release(cls, root: Path) -> p.Result[str]:
        """Return the one exact release embedded by both generated launchers."""
        shell = cls.validate_seed(
            root / c.Infra.MISE_LAUNCHER_DIRECTORY / c.Infra.MISE_UNIX_LAUNCHER_FILENAME
        )
        windows = cls.validate_seed(
            root
            / c.Infra.MISE_LAUNCHER_DIRECTORY
            / c.Infra.MISE_WINDOWS_LAUNCHER_FILENAME
        )
        if shell.failure or windows.failure:
            return r[str].fail(shell.error or windows.error or "invalid Mise launcher")
        if shell.value != windows.value:
            return r[str].fail("Mise launcher version drift")
        return r[str].ok(shell.value)

    @classmethod
    def validate_seed(cls, path: Path) -> p.Result[str]:
        """Validate one native staged bootstrap seed without executing live bytes."""
        source = u.Cli.files_read_text(path)
        if source.failure:
            return r[str].fail(source.error or f"missing generated Mise seed: {path}")
        windows = path.name == c.Infra.MISE_WINDOWS_LAUNCHER_FILENAME
        release = (
            cls._assignment(source.value, "pinned_version")
            if windows
            else cls._shell_launcher_version(source.value)
        )
        if release is None or not cls.is_mise_release(release):
            return r[str].fail(f"Mise seed has an invalid release: {path}")
        try:
            mode = path.stat().st_mode
        except OSError as exc:
            return r[str].fail(
                f"cannot inspect generated Mise seed: {exc}", exception=exc
            )
        if not windows and not mode & 0o100:
            return r[str].fail("generated Unix Mise seed is not executable")
        checksums = (
            ("sum_x64", "sum_arm64")
            if windows
            else (
                "checksum_linux_x86_64",
                "checksum_linux_x86_64_musl",
                "checksum_linux_arm64",
                "checksum_linux_arm64_musl",
                "checksum_linux_armv7",
                "checksum_linux_armv7_musl",
                "checksum_macos_x86_64",
                "checksum_macos_arm64",
                "checksum_linux_x86_64_zstd",
                "checksum_linux_x86_64_musl_zstd",
                "checksum_linux_arm64_zstd",
                "checksum_linux_arm64_musl_zstd",
                "checksum_linux_armv7_zstd",
                "checksum_linux_armv7_musl_zstd",
                "checksum_macos_x86_64_zstd",
                "checksum_macos_arm64_zstd",
            )
        )
        for checksum_name in checksums:
            assignment = cls._assignment(source.value, checksum_name)
            digest = (
                assignment if windows or assignment is None else assignment.split()[0]
            )
            if not cls._is_sha256(digest):
                return r[str].fail(
                    f"Mise seed checksum missing in {path.name}: {checksum_name}"
                )
        return r[str].ok(release)

    @classmethod
    def validate_launchers(cls, root: Path) -> p.Result[bool]:
        """Validate both generated launchers and their identical release."""
        release = cls.launcher_release(root)
        if release.failure:
            return r[bool].from_failure(release)
        return r[bool].ok(True)

    def validate_artifacts(self, project_root: Path) -> p.Result[bool]:
        """Validate one project's committed Mise artifacts entirely offline."""
        config_result = self._read_toml(project_root / ".mise.toml")
        if config_result.failure:
            return r[bool].from_failure(config_result)
        tools_result = self._tool_specifiers(config_result.value)
        if tools_result.failure:
            return r[bool].from_failure(tools_result)
        suspended = self._validate_suspended_selectors(tools_result.value)
        if suspended.failure:
            return suspended
        release = self.launcher_release(project_root)
        if release.failure:
            return r[bool].fail(release.error or "invalid committed Mise launchers")
        return r[bool].ok(True)

    @override
    def execute(self) -> p.Result[bool]:
        """Validate generated Mise declarations and launchers entirely offline."""
        config_result = self._read_toml(self.workspace_root / ".mise.toml")
        if config_result.failure:
            return r[bool].fail(config_result.error or "invalid .mise.toml")
        tools_result = self._tool_specifiers(config_result.value)
        if tools_result.failure:
            return r[bool].fail(tools_result.error or "invalid .mise.toml tools")
        suspended = self._validate_suspended_selectors(tools_result.value)
        if suspended.failure:
            return suspended
        if self.config_only:
            return r[bool].ok(True)
        release = self.launcher_release(self.workspace_root)
        if release.failure:
            return r[bool].fail(release.error or "invalid committed Mise launchers")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenMiseArtifacts"]
