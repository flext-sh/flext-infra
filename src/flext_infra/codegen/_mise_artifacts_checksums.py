"""Checksum completion for newly generated Mise lock projections."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, t, u
from flext_infra.codegen import (
    _mise_artifacts_files as files,
    _mise_artifacts_process as process,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactChecksums:
    """Complete missing SHA-256 values from native immutable HTTPS metadata."""

    @classmethod
    def hydrate(cls, root: Path, *, environment: t.StrMapping) -> p.Result[bool]:
        """Hash every native platform URL that Mise left without a checksum."""
        lock_path = root / "mise.lock"
        before = files.read_state(lock_path, required=True)
        if before.failure:
            return r[bool].from_failure(before)
        if before.value.content is None:
            return r[bool].fail(f"generated Mise lock is absent: {lock_path}")
        try:
            source = before.value.content.decode(c.Cli.ENCODING_DEFAULT)
        except UnicodeDecodeError as exc:
            return r[bool].fail_op("decode generated mise.lock", exc)
        payload = u.Cli.toml_mapping_from_text(source)
        if payload is None:
            return r[bool].fail("invalid TOML in generated mise.lock")
        hydrated = cls._hydrate_payload(payload, root=root, environment=environment)
        if hydrated.failure:
            return r[bool].from_failure(hydrated)
        changed, replacement = hydrated.value
        if not changed:
            return r[bool].ok(True)
        rendered = u.Cli.toml_dumps(replacement)
        written = u.Cli.atomic_write_binary_file_guarded(
            before.value,
            rendered.encode(c.Cli.ENCODING_DEFAULT),
            permission_mode=files.ARTIFACT_SPECS[2][1],
        )
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(True)

    @classmethod
    def _hydrate_payload(
        cls, payload: t.JsonMapping, *, root: Path, environment: t.StrMapping
    ) -> p.Result[tuple[bool, t.JsonMapping]]:
        raw_tools = payload.get("tools")
        if not isinstance(raw_tools, Mapping):
            return r[tuple[bool, t.JsonMapping]].fail(
                "generated mise.lock must declare [tools]"
            )
        changed = False
        download_index = 0
        tools: dict[str, t.JsonValue] = {}
        for selector, raw_entries in raw_tools.items():
            if not isinstance(selector, str) or not isinstance(raw_entries, list):
                return r[tuple[bool, t.JsonMapping]].fail(
                    "generated mise.lock contains an invalid tool entry"
                )
            entries: list[t.JsonValue] = []
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    return r[tuple[bool, t.JsonMapping]].fail(
                        f"generated mise.lock contains an invalid entry for {selector}"
                    )
                entry: dict[str, t.JsonValue] = {}
                for key, value in raw_entry.items():
                    if not key.startswith("platforms.") or not isinstance(
                        value, Mapping
                    ):
                        entry[key] = value
                        continue
                    platform = dict(value)
                    if platform.get("checksum") is None:
                        url = platform.get("url")
                        if not isinstance(url, str) or not url.startswith("https://"):
                            return r[tuple[bool, t.JsonMapping]].fail(
                                "generated Mise checksum source is not safe: "
                                f"{selector} {key}"
                            )
                        checksum = cls._download_checksum(
                            url,
                            destination=root / f".mise-checksum-{download_index}",
                            environment=environment,
                        )
                        if checksum.failure:
                            return r[tuple[bool, t.JsonMapping]].from_failure(checksum)
                        platform["checksum"] = f"sha256:{checksum.value}"
                        changed = True
                        download_index += 1
                    entry[key] = platform
                entries.append(entry)
            tools[selector] = entries
        return r[tuple[bool, t.JsonMapping]].ok(
            changed,
            {"lockfile_version": payload.get("lockfile_version"), "tools": tools},
        )

    @staticmethod
    def _cleanup_download(destination: Path) -> p.Result[bool]:
        """Remove one download probe without masking the first failure."""
        state = files.read_state(destination, required=False)
        if state.failure:
            return r[bool].from_failure(state)
        if state.value.content is None:
            return r[bool].ok(True)
        removed = u.Cli.atomic_delete_binary_file_guarded(state.value)
        if removed.failure:
            return r[bool].from_failure(removed)
        return r[bool].ok(True)

    @classmethod
    def _download_checksum(
        cls, url: str, *, destination: Path, environment: t.StrMapping
    ) -> p.Result[str]:
        downloaded = process.run(
            (
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--output",
                str(destination),
                url,
            ),
            cwd=destination.parent,
            env=environment,
            operation=f"Mise checksum hydration for {url}",
        )
        if downloaded.failure:
            cleanup = cls._cleanup_download(destination)
            if cleanup.failure:
                return r[str].fail(
                    f"{downloaded.error}; checksum cleanup failed: {cleanup.error}"
                )
            return r[str].from_failure(downloaded)
        artifact = files.read_state(destination, required=True)
        if artifact.failure:
            cleanup = cls._cleanup_download(destination)
            if cleanup.failure:
                return r[str].fail(
                    f"{artifact.error}; checksum cleanup failed: {cleanup.error}"
                )
            return r[str].from_failure(artifact)
        if not artifact.value.content:
            cleanup = cls._cleanup_download(destination)
            if cleanup.failure:
                return r[str].fail(
                    f"Mise checksum source is empty: {url}; "
                    f"checksum cleanup failed: {cleanup.error}"
                )
            return r[str].fail(f"Mise checksum source is empty: {url}")
        digest = sha256(artifact.value.content).hexdigest()
        removed = u.Cli.atomic_delete_binary_file_guarded(artifact.value)
        if removed.failure:
            return r[str].from_failure(removed)
        return r[str].ok(digest)


__all__: list[str] = ["FlextInfraMiseArtifactChecksums"]
