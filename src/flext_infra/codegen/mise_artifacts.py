"""Offline validation for generated Mise launchers and lock metadata."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base import s

from .codegen_transaction import FlextInfraCodegenTransaction

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenMiseArtifacts(s[bool]):
    """Validate committed Mise artifacts entirely offline."""

    _PLATFORM_PREFIX: ClassVar[str] = "platforms."

    @staticmethod
    def _read_toml(path: Path) -> p.Result[t.JsonMapping]:
        source = u.Cli.files_read_text(path)
        if source.failure:
            return r[t.JsonMapping].from_failure(source)
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[t.JsonMapping].fail(f"invalid TOML in {path.name}")
        return r[t.JsonMapping].ok(payload)

    @staticmethod
    def _tool_version(raw_tool: t.JsonValue) -> str | None:
        """Return one exact version from either supported Mise tool shape."""
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
                    f".mise.toml tool lacks an exact version: {selector}"
                )
            specifiers[selector] = version
        if not specifiers:
            return r[t.StrMapping].fail(".mise.toml must declare at least one tool")
        return r[t.StrMapping].ok(specifiers)

    @classmethod
    def _normalize_lock_entry(
        cls, selector: str, raw_entry: t.JsonValue
    ) -> p.Result[t.JsonMapping]:
        """Normalize one Mise lock entry without weakening its typed boundary."""
        if not isinstance(raw_entry, Mapping):
            return r[t.JsonMapping].fail(
                f"mise.lock contains an invalid entry for {selector}"
            )
        normalized_entry: dict[str, t.JsonValue] = {}
        normalized_platforms: dict[str, t.JsonValue] = {}
        for raw_key, raw_value in raw_entry.items():
            if raw_key.startswith(cls._PLATFORM_PREFIX):
                platform = raw_key.removeprefix(cls._PLATFORM_PREFIX)
                normalized_platforms[platform] = raw_value
            else:
                normalized_entry[raw_key] = raw_value
        normalized_entry["platforms"] = normalized_platforms
        return r[t.JsonMapping].ok(normalized_entry)

    @classmethod
    def _normalize_lock_payload(cls, payload: t.JsonMapping) -> p.Result[t.JsonMapping]:
        """Expand Mise quoted platform keys for typed validation."""
        raw_tools = payload.get("tools")
        if not isinstance(raw_tools, Mapping):
            return r[t.JsonMapping].fail("mise.lock must declare [tools]")
        normalized_tools: dict[str, t.JsonValue] = {}
        for raw_selector, raw_entries in raw_tools.items():
            if not raw_selector.strip() or not isinstance(raw_entries, list):
                return r[t.JsonMapping].fail("mise.lock contains an invalid tool entry")
            normalized_entries: list[t.JsonValue] = []
            for raw_entry in raw_entries:
                normalized = cls._normalize_lock_entry(raw_selector, raw_entry)
                if normalized.failure:
                    return r[t.JsonMapping].from_failure(normalized)
                normalized_entries.append(dict(normalized.value))
            normalized_tools[raw_selector] = normalized_entries
        return r[t.JsonMapping].ok({
            "lockfile_version": payload.get("lockfile_version"),
            "tools": normalized_tools,
        })

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
        return len(value) == sha256().digest_size * 2 and all(
            character in "0123456789abcdef" for character in value
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
    def is_mise_release(value: str | None) -> bool:
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
        shell = cls.validate_seed(root / "bin" / "mise")
        windows = cls.validate_seed(root / "bin" / "mise.cmd")
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
            return r[str].from_failure(source)
        windows = path.name == "mise.cmd"
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
        raw_settings = config_result.value.get("settings")
        raw_tool_config = config_result.value.get("tool_config")
        if (
            not isinstance(raw_settings, Mapping)
            or raw_settings.get("lockfile") is not True
            or not isinstance(raw_tool_config, Mapping)
            or raw_tool_config.get("locked") is not True
        ):
            return r[bool].fail(".mise.toml must enable lockfile and locked mode")
        tools_result = self._tool_specifiers(config_result.value)
        if tools_result.failure:
            return r[bool].from_failure(tools_result)
        lock_result = self._read_toml(project_root / "mise.lock")
        if lock_result.failure:
            return r[bool].from_failure(lock_result)
        normalized_lock = self._normalize_lock_payload(lock_result.value)
        if normalized_lock.failure:
            return r[bool].from_failure(normalized_lock)
        try:
            lock = m.Infra.MiseLockSpec.model_validate(normalized_lock.value)
        except c.ValidationError as exc:
            return r[bool].fail(f"invalid mise.lock metadata: {exc}", exception=exc)
        launcher_result = self.validate_launchers(project_root)
        if launcher_result.failure:
            return launcher_result

        return self._validate_lock(lock, configured_tools=tools_result.value)

    @staticmethod
    def _validate_lock(
        lock: m.Infra.MiseLockSpec, *, configured_tools: t.StrMapping
    ) -> p.Result[bool]:
        expected_tools = sorted(configured_tools)
        actual_tools = sorted(lock.tools)
        if actual_tools != expected_tools:
            return r[bool].fail(
                "Mise lock tool set mismatch: "
                f"expected={expected_tools} actual={actual_tools}"
            )
        toolchain = config.Infra.codegen.toolchain
        declared_platforms = frozenset(toolchain.mise_lock_platforms)
        for selector in sorted(expected_tools):
            entries = lock.tools[selector]
            if len(entries) != 1:
                return r[bool].fail(f"Mise lock must contain one entry for {selector}")
            entry = entries[0]
            if configured_tools[selector] not in entry.specifiers:
                return r[bool].fail(f"Mise lock specifier drift for {selector}")
            if selector.startswith("github:") and entry.backend != selector:
                return r[bool].fail(f"Mise lock backend drift for {selector}")
            actual_platforms = frozenset(entry.platforms)
            if not actual_platforms <= declared_platforms:
                return r[bool].fail(
                    f"Mise lock platform metadata mismatch for {selector}: "
                    f"declared={sorted(declared_platforms)} "
                    f"actual={sorted(actual_platforms)}"
                )
        return r[bool].ok(True)

    @override
    def execute(self) -> p.Result[bool]:
        """Validate only; conform is the sole writable toolchain owner."""
        transaction = FlextInfraCodegenTransaction(self)
        if not self.effective_dry_run:
            return r[bool].fail("Mise artifact publication is owned by codegen conform")
        return transaction.validate()


__all__: list[str] = ["FlextInfraCodegenMiseArtifacts"]
