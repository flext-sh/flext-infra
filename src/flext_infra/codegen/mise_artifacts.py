"""Offline validation for generated Mise launchers and lock metadata."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar, override
from urllib.parse import urlsplit

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenMiseArtifacts(s[bool]):
    """Hydrate generated lock checksums or validate committed Mise artifacts."""

    _PLATFORM_PREFIX: ClassVar[str] = "platforms."

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
                    return r[t.JsonMapping].fail(
                        normalized.error
                        or f"mise.lock contains an invalid entry for {raw_selector}"
                    )
                normalized_entries.append(dict(normalized.value))
            normalized_tools[raw_selector] = normalized_entries
        return r[t.JsonMapping].ok({
            "lockfile_version": payload.get("lockfile_version"),
            "tools": normalized_tools,
        })

    @classmethod
    def _missing_checksums(
        cls, payload: t.JsonMapping
    ) -> p.Result[tuple[tuple[str, str, str], ...]]:
        """Return typed selector/platform/URL triples lacking a checksum."""
        raw_tools = payload.get("tools")
        if not isinstance(raw_tools, Mapping):
            return r[tuple[tuple[str, str, str], ...]].fail(
                "mise.lock must declare [tools]"
            )
        missing: list[tuple[str, str, str]] = []
        for raw_selector, raw_entries in raw_tools.items():
            if not isinstance(raw_entries, list):
                return r[tuple[tuple[str, str, str], ...]].fail(
                    "mise.lock contains an invalid tool entry"
                )
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    return r[tuple[tuple[str, str, str], ...]].fail(
                        f"mise.lock contains an invalid entry for {raw_selector}"
                    )
                for raw_key, raw_metadata in raw_entry.items():
                    if not raw_key.startswith(cls._PLATFORM_PREFIX):
                        continue
                    platform = raw_key.removeprefix(cls._PLATFORM_PREFIX)
                    if not platform or not isinstance(raw_metadata, Mapping):
                        return r[tuple[tuple[str, str, str], ...]].fail(
                            "mise.lock contains invalid platform metadata for "
                            f"{raw_selector}"
                        )
                    if raw_metadata.get("checksum") is not None:
                        continue
                    raw_url = raw_metadata.get("url")
                    if not isinstance(raw_url, str):
                        return r[tuple[tuple[str, str, str], ...]].fail(
                            "mise.lock checksum source missing for "
                            f"{raw_selector}/{platform}"
                        )
                    parsed_url = urlsplit(raw_url)
                    if (
                        parsed_url.scheme != "https"
                        or parsed_url.hostname is None
                        or parsed_url.username is not None
                        or parsed_url.password is not None
                    ):
                        return r[tuple[tuple[str, str, str], ...]].fail(
                            "mise.lock checksum source is not safe for "
                            f"{raw_selector}/{platform}"
                        )
                    missing.append((raw_selector, platform, raw_url))
        return r[tuple[tuple[str, str, str], ...]].ok(tuple(missing))

    @staticmethod
    def _platform_header(selector: str, platform: str) -> p.Result[str]:
        """Render the exact platform header emitted by Mise."""
        safe_characters = frozenset(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:/.-"
        )
        if (
            not selector
            or any(character not in safe_characters for character in selector)
            or not platform
            or any(character not in safe_characters for character in platform)
        ):
            return r[str].fail("mise.lock contains an unsupported TOML key")
        selector_key = (
            selector
            if all(character.isalnum() or character in "_-" for character in selector)
            else f'"{selector}"'
        )
        return r[str].ok(f'[tools.{selector_key}."platforms.{platform}"]')

    @classmethod
    def _download_checksum(
        cls, selector: str, platform: str, url: str, artifact: Path
    ) -> p.Result[str]:
        """Download and hash one validated HTTPS artifact."""
        download = u.Cli.run_raw(
            (
                "curl",
                "--fail",
                "--location",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--silent",
                "--show-error",
                "--output",
                str(artifact),
                url,
            ),
            cwd=artifact.parent,
        )
        if download.failure:
            return r[str].fail(
                download.error or f"checksum download failed for {selector}/{platform}"
            )
        if download.value.exit_code != 0:
            cause = download.value.stderr.strip() or "curl exited non-zero"
            return r[str].fail(
                f"checksum download failed for {selector}/{platform}: {cause}"
            )
        digest = u.Cli.sha256_file(artifact)
        if not cls._is_sha256(digest):
            return r[str].fail(f"invalid downloaded checksum for {selector}/{platform}")
        return r[str].ok(digest)

    def _hydrate_source(
        self, source: str, missing: tuple[tuple[str, str, str], ...], scratch: Path
    ) -> p.Result[str]:
        """Download each unique URL and return lock text with complete checksums."""
        hydrated = source
        digests: dict[str, str] = {}
        for index, (selector, platform, url) in enumerate(missing):
            digest = digests.get(url)
            if digest is None:
                downloaded = self._download_checksum(
                    selector, platform, url, scratch / f"artifact-{index}"
                )
                if downloaded.failure:
                    return r[str].fail(downloaded.error)
                digest = downloaded.value
                digests[url] = digest
            header = self._platform_header(selector, platform)
            if header.failure:
                return r[str].fail(header.error or "invalid mise.lock header")
            marker = f"{header.value}\n"
            if hydrated.count(marker) != 1:
                return r[str].fail(
                    "mise.lock platform section is not unique for "
                    f"{selector}/{platform}"
                )
            hydrated = hydrated.replace(
                marker, f'{marker}checksum = "sha256:{digest}"\n', 1
            )
        return r[str].ok(hydrated)

    def _hydrate_lock_checksums(self) -> p.Result[bool]:
        """Download exact resolved artifacts and atomically add missing SHA-256 values."""
        lock_path = self.workspace_root / "mise.lock"
        source = u.Cli.files_read_text(lock_path)
        if source.failure:
            return r[bool].fail(source.error or "cannot read mise.lock")
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[bool].fail("invalid TOML in mise.lock")
        missing = self._missing_checksums(payload)
        if missing.failure:
            return r[bool].fail(missing.error or "invalid mise.lock checksum metadata")
        if not missing.value:
            return r[bool].ok(True)
        try:
            with TemporaryDirectory(
                prefix=".mise-checksum.", dir=self.workspace_root
            ) as raw_scratch:
                hydrated = self._hydrate_source(
                    source.value, missing.value, Path(raw_scratch)
                )
        except OSError as exc:
            return r[bool].fail(f"cannot hydrate mise.lock checksums: {exc}")
        if hydrated.failure:
            return r[bool].fail(hydrated.error or "cannot hydrate mise.lock checksums")
        write = u.Cli.atomic_write_text_file(lock_path, hydrated.value)
        if write.failure:
            return r[bool].fail(write.error or "cannot publish hydrated mise.lock")
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

    @classmethod
    def _validate_launchers(cls, root: Path) -> p.Result[bool]:
        shell_path = root / "bin" / "mise"
        windows_path = root / "bin" / "mise.cmd"
        shell_source = u.Cli.files_read_text(shell_path)
        windows_source = u.Cli.files_read_text(windows_path)
        if shell_source.failure or windows_source.failure:
            return r[bool].fail("missing generated Mise launcher")
        version = config.Infra.codegen.toolchain.mise_version
        shell_marker = f'local mise_version="${{MISE_VERSION:-{version}}}"'
        windows_marker = f'set "pinned_version={version}"'
        if (
            shell_marker not in shell_source.value
            or windows_marker not in windows_source.value
        ):
            return r[bool].fail("Mise launcher version drift")
        try:
            shell_mode = shell_path.stat().st_mode
        except OSError as exc:
            return r[bool].fail(f"cannot inspect generated Mise launcher: {exc}")
        if not shell_mode & 0o100:
            return r[bool].fail("generated Unix Mise launcher is not executable")
        shell_checksums = (
            "checksum_linux_x86_64",
            "checksum_linux_x86_64_musl",
            "checksum_linux_arm64",
            "checksum_linux_arm64_musl",
            "checksum_macos_x86_64",
            "checksum_macos_arm64",
        )
        for checksum_name in shell_checksums:
            if not cls._is_sha256(cls._assignment(shell_source.value, checksum_name)):
                return r[bool].fail(f"Mise launcher checksum missing: {checksum_name}")
        if not cls._is_sha256(cls._assignment(windows_source.value, "sum_x64")):
            return r[bool].fail("Mise launcher checksum missing: windows-x64")
        return r[bool].ok(True)

    @staticmethod
    def _validate_lock(
        lock: m.Infra.MiseLockSpec, *, configured_tools: t.StrMapping
    ) -> p.Result[bool]:
        expected_tools = frozenset(configured_tools)
        actual_tools = frozenset(lock.tools)
        if actual_tools != expected_tools:
            return r[bool].fail(
                "Mise lock tool set mismatch: "
                f"expected={sorted(expected_tools)} actual={sorted(actual_tools)}"
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
            excluded = frozenset(
                toolchain.mise_lock_platform_exclusions.get(selector, ())
            )
            expected_platforms = declared_platforms - excluded
            actual_platforms = frozenset(entry.platforms)
            if actual_platforms != expected_platforms:
                return r[bool].fail(
                    f"Mise lock platform metadata mismatch for {selector}: "
                    f"expected={sorted(expected_platforms)} "
                    f"actual={sorted(actual_platforms)}"
                )
        return r[bool].ok(True)

    @override
    def execute(self) -> p.Result[bool]:
        """Hydrate in explicit apply mode; otherwise validate entirely offline."""
        if not self.effective_dry_run:
            return self._hydrate_lock_checksums()
        config_result = self._read_toml(self.workspace_root / ".mise.toml")
        if config_result.failure:
            return r[bool].fail(config_result.error or "invalid .mise.toml")
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
            return r[bool].fail(tools_result.error or "invalid .mise.toml tools")
        lock_result = self._read_toml(self.workspace_root / "mise.lock")
        if lock_result.failure:
            return r[bool].fail(lock_result.error or "invalid mise.lock")
        normalized_lock = self._normalize_lock_payload(lock_result.value)
        if normalized_lock.failure:
            return r[bool].fail(normalized_lock.error or "invalid mise.lock")
        try:
            lock = m.Infra.MiseLockSpec.model_validate(normalized_lock.value)
        except c.ValidationError as exc:
            return r[bool].fail(f"invalid mise.lock metadata: {exc}")
        launcher_result = self._validate_launchers(self.workspace_root)
        if launcher_result.failure:
            return launcher_result
        return self._validate_lock(lock, configured_tools=tools_result.value)


__all__: list[str] = ["FlextInfraCodegenMiseArtifacts"]
