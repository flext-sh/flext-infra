"""Transactional owner for newest Mise launchers and exact workspace locks."""

from __future__ import annotations

import os
import shutil
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from filelock import FileLock, Timeout
from flext_core import r
from flext_infra import c, config, m, settings, t, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenMiseArtifactTransaction:
    """Generate, validate, and transactionally publish a complete Mise set.

    The committed launcher is only the signed bootstrap seed. It invokes Mise's
    own ``generate install-script`` command without a version selector, so Mise
    resolves and verifies the newest release. Every project is then prepared in
    destination-filesystem staging. Live files remain unchanged until all
    launchers and locks validate. Publication uses exact byte preconditions and
    restores only writes attributable to this invocation on any normal failure.
    """

    _ARTIFACT_NAMES: ClassVar[tuple[str, ...]] = (
        "bin/mise",
        "bin/mise.cmd",
        "mise.lock",
    )
    _LOCK_NAME: ClassVar[str] = "mise-artifacts.lock"
    _JOURNAL_NAME: ClassVar[str] = "mise-artifacts.transaction.json"
    _TRANSACTION_DIR_NAME: ClassVar[str] = "mise-artifacts.transaction"
    _MISE_REMOVE_ENV_KEYS: ClassVar[t.StrSequence] = (
        "MISE_INSTALL_PATH",
        "MISE_VERSION",
        "MISE_INSTALLS_DIR",
        "MISE_SHIMS_DIR",
        "XDG_DATA_HOME",
        "MISE_ENV_FILE",
        "MISE_DEFAULT_CONFIG_FILENAME",
    )

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        """Bind the one public artifact owner used for validation and hydration."""
        self._owner = owner

    @staticmethod
    def _read_required_regular(path: Path) -> p.Result[bytes]:
        """Read one required regular artifact without following a symlink."""
        if path.is_symlink() or not path.is_file():
            return r[bytes].fail(f"required Mise artifact is not a regular file: {path}")
        read = u.Cli.files_read_binary(path)
        if read.failure:
            return r[bytes].fail(read.error or f"cannot read Mise artifact: {path}")
        return read

    def _project_states(self) -> p.Result[tuple[m.Infra.MiseToolchainProjectState, ...]]:
        """Discover and snapshot the governed workspace before any effect."""
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            self._owner.workspace_root
        )
        if workspace.failure:
            return r[tuple[m.Infra.MiseToolchainProjectState, ...]].fail(
                workspace.error or "cannot discover governed Mise workspace"
            )
        workspace_root = self._owner.workspace_root.resolve()
        selectors = (
            ".",
            *(project.path.as_posix() for project in workspace.value.subprojects),
        )
        states: list[m.Infra.MiseToolchainProjectState] = []
        for selector in selectors:
            relative = Path(selector)
            if selector != "." and (
                relative.is_absolute()
                or relative.as_posix() != selector
                or ".." in relative.parts
            ):
                return r[tuple[m.Infra.MiseToolchainProjectState, ...]].fail(
                    f"unsafe Mise project selector: {selector}"
                )
            unresolved_root = workspace_root / relative
            cursor = workspace_root
            for part in relative.parts:
                cursor /= part
                if cursor.is_symlink():
                    return r[
                        tuple[m.Infra.MiseToolchainProjectState, ...]
                    ].fail(
                        f"Mise project path contains a symlink: {selector}"
                    )
            project_root = unresolved_root.resolve()
            if (
                unresolved_root.is_symlink()
                or not project_root.is_dir()
                or not project_root.is_relative_to(workspace_root)
            ):
                return r[tuple[m.Infra.MiseToolchainProjectState, ...]].fail(
                    f"Mise project is not a physical workspace directory: {selector}"
                )
            sources: list[bytes] = []
            for name in (".mise.toml", *self._ARTIFACT_NAMES):
                source = self._read_required_regular(project_root / name)
                if source.failure:
                    return r[tuple[m.Infra.MiseToolchainProjectState, ...]].fail(
                        source.error or f"cannot snapshot {selector}/{name}"
                    )
                sources.append(source.value)
            states.append(
                m.Infra.MiseToolchainProjectState(
                    selector=selector,
                    root=project_root,
                    config_bytes=sources[0],
                    launcher_bytes=sources[1],
                    windows_launcher_bytes=sources[2],
                    lock_bytes=sources[3],
                )
            )
        return r[tuple[m.Infra.MiseToolchainProjectState, ...]].ok(tuple(states))

    @staticmethod
    def _mkdirs(*directories: Path) -> p.Result[bool]:
        """Create owned staging directories and retain the causal OS failure."""
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op("create Mise transaction staging", exc)
        return r[bool].ok(True)

    @classmethod
    def _run_mise(
        cls,
        command: t.StrSequence,
        *,
        cwd: Path,
        environment: t.StrMapping,
        operation: str,
    ) -> p.Result[str]:
        """Run one Mise command and reject its first error or warning."""
        executed = u.Cli.run_raw(
            command,
            cwd=cwd,
            env=environment,
            remove_env_keys=cls._MISE_REMOVE_ENV_KEYS,
        )
        if executed.failure:
            return r[str].fail(executed.error or f"{operation} failed to execute")
        output = executed.value.stdout + executed.value.stderr
        if executed.value.exit_code != 0:
            detail = output.strip() or f"exit {executed.value.exit_code}"
            return r[str].fail(f"{operation} failed: {detail}")
        if "mise WARN" in output:
            return r[str].fail(f"{operation} emitted a warning: {output.strip()}")
        return r[str].ok(executed.value.stdout.strip())

    @staticmethod
    def _isolated_environment(scratch: Path) -> dict[str, str]:
        """Build the single isolated environment shared by generation stages."""
        return {
            "MISE_SAFE": "1",
            "MISE_GLOBAL_CONFIG_FILE": str(scratch / "global-config.toml"),
            "MISE_CONFIG_DIR": str(scratch / "config"),
            "MISE_DATA_DIR": str(scratch / "data"),
            "MISE_CACHE_DIR": str(scratch / "cache"),
            "MISE_STATE_DIR": str(scratch / "state"),
            "MISE_TMP_DIR": str(scratch / "tmp"),
            "MISE_GLOBAL_CONFIG_ROOT": str(scratch),
            "MISE_SYSTEM_CONFIG_DIR": str(scratch / "system-config"),
            "MISE_SYSTEM_DIR": str(scratch / "system-config"),
            "TMPDIR": str(scratch / "tmp"),
        }

    def _latest_receipt(self, scratch: Path) -> p.Result[tuple[Path, str]]:
        """Use the committed seed to produce and identify the newest receipt."""
        receipt = scratch / "receipt"
        prepared = self._mkdirs(
            receipt / "bin",
            scratch / "config",
            scratch / "data",
            scratch / "cache",
            scratch / "state",
            scratch / "tmp",
            scratch / "system-config",
        )
        if prepared.failure:
            return r[tuple[Path, str]].from_failure(prepared)
        try:
            (scratch / "global-config.toml").write_bytes(b"")
        except OSError as exc:
            return r[tuple[Path, str]].fail_op("create isolated Mise config", exc)
        seed_name = "mise.cmd" if os.name == "nt" else "mise"
        seed = self._owner.workspace_root / "bin" / seed_name
        environment = self._isolated_environment(scratch)
        environment.update({
            "MISE_CEILING_PATHS": str(scratch.parent),
            "MISE_TRUSTED_CONFIG_PATHS": str(scratch),
        })
        generated = self._run_mise(
            (
                str(seed),
                "-C",
                str(scratch),
                "generate",
                "install-script",
                "--write",
                str(receipt / "bin" / "mise"),
                "--windows",
            ),
            cwd=scratch,
            environment=environment,
            operation="Mise newest launcher generation",
        )
        if generated.failure:
            return r[tuple[Path, str]].from_failure(generated)
        launcher = receipt / "bin" / ("mise.cmd" if os.name == "nt" else "mise")
        try:
            (receipt / "bin" / "mise").chmod(0o755)
        except OSError as exc:
            return r[tuple[Path, str]].fail_op("mark generated Mise launcher", exc)
        validation = self._owner._validate_launchers(receipt)
        if validation.failure:
            return r[tuple[Path, str]].fail(
                validation.error or "generated Mise receipt is invalid"
            )
        version = self._run_mise(
            (str(launcher), "--version"),
            cwd=scratch,
            environment=environment,
            operation="Mise newest runtime identity",
        )
        if version.failure:
            return r[tuple[Path, str]].from_failure(version)
        release = version.value.split(maxsplit=1)[0] if version.value else ""
        if not self._owner._is_mise_release(release):
            return r[tuple[Path, str]].fail(
                f"Mise newest runtime returned an invalid version: {version.value}"
            )
        embedded_release = self._owner._launcher_release(receipt)
        if embedded_release.failure:
            return r[tuple[Path, str]].from_failure(embedded_release)
        if release != embedded_release.value:
            return r[tuple[Path, str]].fail(
                "Mise generated launcher runtime differs from its receipt: "
                f"runtime={release} receipt={embedded_release.value}"
            )
        u.Cli.info(f"mise-toolchain: newest runtime={release}")
        return r[tuple[Path, str]].ok((launcher, release))

    @staticmethod
    def _copy_project_config(source_root: Path, stage_root: Path) -> p.Result[bool]:
        """Copy only regular YAML inputs consumed by Mise artifact validation."""
        source_config = source_root / "config"
        if not source_config.exists():
            return r[bool].ok(True)
        if source_config.is_symlink() or not source_config.is_dir():
            return r[bool].fail(
                f"project config is not a physical directory: {source_config}"
            )
        target_config = stage_root / "config"
        try:
            target_config.mkdir(parents=True, exist_ok=True)
            for source in sorted(source_config.glob("*.yaml")):
                if source.is_symlink() or not source.is_file():
                    return r[bool].fail(
                        f"project config is not a regular file: {source}"
                    )
                shutil.copy2(source, target_config / source.name)
        except OSError as exc:
            return r[bool].fail_op("copy project Mise configuration", exc)
        return r[bool].ok(True)

    def _stage_project(
        self,
        state: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        receipt_root: Path,
        scratch: Path,
        credential_command: str,
        root_stage: Path | None,
        root_config: bytes,
    ) -> p.Result[bool]:
        """Build and fully validate one project artifact set in staging."""
        prepared = self._mkdirs(stage_root / "bin")
        if prepared.failure:
            return prepared
        try:
            (stage_root / ".mise.toml").write_bytes(state.config_bytes)
            shutil.copy2(receipt_root / "bin" / "mise", stage_root / "bin" / "mise")
            shutil.copy2(
                receipt_root / "bin" / "mise.cmd", stage_root / "bin" / "mise.cmd"
            )
            (stage_root / "bin" / "mise").chmod(0o755)
        except OSError as exc:
            return r[bool].fail_op(f"stage Mise receipt for {state.selector}", exc)
        copied = self._copy_project_config(state.root, stage_root)
        if copied.failure:
            return copied
        if state.selector != "." and state.config_bytes == root_config:
            if root_stage is None:
                return r[bool].fail("root Mise artifacts must be staged first")
            try:
                shutil.copy2(root_stage / "mise.lock", stage_root / "mise.lock")
            except OSError as exc:
                return r[bool].fail_op(
                    f"propagate root Mise lock to {state.selector}", exc
                )
        else:
            try:
                (stage_root / "mise.lock").write_bytes(state.lock_bytes)
            except OSError as exc:
                return r[bool].fail_op(f"stage Mise lock for {state.selector}", exc)
            environment = self._isolated_environment(scratch)
            environment.update({
                "MISE_CEILING_PATHS": str(stage_root.parent),
                "MISE_TRUSTED_CONFIG_PATHS": str(stage_root),
                "MISE_GITHUB_CREDENTIAL_COMMAND": credential_command,
            })
            launcher = receipt_root / "bin" / (
                "mise.cmd" if os.name == "nt" else "mise"
            )
            locked = self._run_mise(
                (
                    str(launcher),
                    "-C",
                    str(stage_root),
                    "lock",
                    "--bump",
                    "--platform",
                    ",".join(config.Infra.codegen.toolchain.mise_lock_platforms),
                ),
                cwd=stage_root,
                environment=environment,
                operation=f"Mise lock generation for {state.selector}",
            )
            if locked.failure:
                return r[bool].from_failure(locked)
            hydrated = self._owner._hydrate_lock_checksums_at(stage_root)
            if hydrated.failure:
                return r[bool].fail(
                    hydrated.error or f"Mise checksum hydration failed for {state.selector}"
                )
        validated = self._owner._validate_artifacts(stage_root)
        if validated.failure:
            return r[bool].fail(
                validated.error or f"Mise artifact validation failed for {state.selector}"
            )
        return r[bool].ok(True)

    @classmethod
    def _publication_plan(
        cls,
        states: tuple[m.Infra.MiseToolchainProjectState, ...],
        stages: tuple[Path, ...],
    ) -> p.Result[tuple[m.Infra.MiseToolchainPublication, ...]]:
        """Create guarded replacements from already validated staged bytes."""
        planned: list[m.Infra.MiseToolchainPublication] = []
        for state, stage in zip(states, stages, strict=True):
            expected = (
                state.launcher_bytes,
                state.windows_launcher_bytes,
                state.lock_bytes,
            )
            for name, before in zip(cls._ARTIFACT_NAMES, expected, strict=True):
                replacement = cls._read_required_regular(stage / name)
                if replacement.failure:
                    return r[tuple[m.Infra.MiseToolchainPublication, ...]].fail(
                        replacement.error or f"cannot read staged artifact {stage / name}"
                    )
                planned.append(
                    m.Infra.MiseToolchainPublication(
                        path=state.root / name,
                        expected_bytes=before,
                        replacement_bytes=replacement.value,
                    )
                )
        return r[tuple[m.Infra.MiseToolchainPublication, ...]].ok(tuple(planned))

    @staticmethod
    def _guarded_write(publication: m.Infra.MiseToolchainPublication) -> p.Result[bool]:
        """Publish one UTF-8 artifact with an exact byte precondition."""
        try:
            replacement = publication.replacement_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return r[bool].fail_op(f"decode staged artifact {publication.path}", exc)
        return u.Cli.atomic_write_text_file_guarded(
            publication.path,
            replacement,
            expected_bytes=publication.expected_bytes,
        )

    @staticmethod
    def _digest(content: bytes) -> str:
        """Return the exact lowercase SHA-256 identity for journaled bytes."""
        return sha256(content).hexdigest()

    def _workspace_relative(self, path: Path) -> p.Result[str]:
        """Return one canonical workspace-relative physical artifact path."""
        workspace_root = self._owner.workspace_root.resolve()
        try:
            relative = path.resolve().relative_to(workspace_root)
        except (OSError, ValueError) as exc:
            return r[str].fail_op(f"resolve workspace artifact {path}", exc)
        selector = relative.as_posix()
        if not selector or selector == "." or ".." in relative.parts:
            return r[str].fail(f"invalid workspace artifact path: {path}")
        return r[str].ok(selector)

    @staticmethod
    def _resolve_relative(
        root: Path, selector: str, *, purpose: str
    ) -> p.Result[Path]:
        """Resolve one canonical relative path without allowing root escape."""
        relative = Path(selector)
        if (
            relative.is_absolute()
            or relative.as_posix() != selector
            or not relative.parts
            or ".." in relative.parts
        ):
            return r[Path].fail(f"unsafe {purpose} path: {selector}")
        try:
            resolved_root = root.resolve()
            resolved = (root / relative).resolve()
        except OSError as exc:
            return r[Path].fail_op(f"resolve {purpose} path {selector}", exc)
        if not resolved.is_relative_to(resolved_root):
            return r[Path].fail(f"{purpose} path escapes its root: {selector}")
        return r[Path].ok(resolved)

    @staticmethod
    def _journal_text(journal: m.Infra.MiseToolchainJournal) -> str:
        """Serialize one deterministic typed journal document."""
        return journal.model_dump_json(indent=2)

    @classmethod
    def _write_journal(
        cls,
        journal_path: Path,
        journal: m.Infra.MiseToolchainJournal,
        *,
        expected_bytes: bytes | None,
    ) -> p.Result[bytes]:
        """Atomically create or transition the journal under the process lock."""
        content = cls._journal_text(journal)
        written = u.Cli.atomic_write_text_file_guarded(
            journal_path, content, expected_bytes=expected_bytes
        )
        if written.failure:
            return r[bytes].fail(written.error or "cannot publish Mise journal")
        expected = content.encode(c.Cli.ENCODING_DEFAULT)
        published = cls._read_required_regular(journal_path)
        if published.failure:
            return r[bytes].fail(
                published.error or "cannot verify published Mise journal"
            )
        if published.value != expected:
            return r[bytes].fail("published Mise journal bytes differ from staging")
        return r[bytes].ok(published.value)

    @staticmethod
    def _read_journal(
        journal_path: Path,
    ) -> p.Result[tuple[m.Infra.MiseToolchainJournal, bytes]]:
        """Load one regular typed journal while preserving its exact bytes."""
        source = FlextInfraCodegenMiseArtifactTransaction._read_required_regular(
            journal_path
        )
        if source.failure:
            return r[tuple[m.Infra.MiseToolchainJournal, bytes]].fail(
                source.error or "cannot read Mise transaction journal"
            )
        try:
            journal = m.Infra.MiseToolchainJournal.model_validate_json(source.value)
        except c.ValidationError as exc:
            return r[tuple[m.Infra.MiseToolchainJournal, bytes]].fail_op(
                "validate Mise transaction journal", exc
            )
        return r[tuple[m.Infra.MiseToolchainJournal, bytes]].ok(
            (journal, source.value)
        )

    @classmethod
    def _remove_transaction_directory(cls, transaction_root: Path) -> p.Result[bool]:
        """Remove only this owner's exact disposable transaction directory."""
        if transaction_root.is_symlink():
            return r[bool].fail(
                f"refusing to remove symlinked Mise transaction path: {transaction_root}"
            )
        if not transaction_root.exists():
            return r[bool].ok(True)
        if transaction_root.name != cls._TRANSACTION_DIR_NAME or not transaction_root.is_dir():
            return r[bool].fail(
                f"refusing to remove invalid Mise transaction path: {transaction_root}"
            )
        try:
            shutil.rmtree(transaction_root)
        except OSError as exc:
            return r[bool].fail_op("remove Mise transaction staging", exc)
        return r[bool].ok(True)

    @classmethod
    def _remove_journal(
        cls, journal_path: Path, *, expected_journal_bytes: bytes
    ) -> p.Result[bool]:
        """Unlink only the exact journal bytes held under the process lock."""
        current = cls._read_required_regular(journal_path)
        if current.failure:
            return r[bool].fail(current.error or "cannot verify Mise journal cleanup")
        if current.value != expected_journal_bytes:
            return r[bool].fail("Mise transaction journal changed before cleanup")
        try:
            journal_path.unlink()
        except OSError as exc:
            return r[bool].fail_op("remove completed Mise transaction journal", exc)
        return r[bool].ok(True)

    @classmethod
    def _cleanup_transaction(
        cls,
        transaction_root: Path,
        journal_path: Path,
        *,
        expected_journal_bytes: bytes,
    ) -> p.Result[bool]:
        """Remove the exact journal first, then its now-disposable staged bytes."""
        removed_journal = cls._remove_journal(
            journal_path, expected_journal_bytes=expected_journal_bytes
        )
        if removed_journal.failure:
            return removed_journal
        return cls._remove_transaction_directory(transaction_root)

    def _prepared_journal(
        self,
        states: tuple[m.Infra.MiseToolchainProjectState, ...],
        publications: tuple[m.Infra.MiseToolchainPublication, ...],
        transaction_root: Path,
    ) -> p.Result[m.Infra.MiseToolchainJournal]:
        """Persist every original byte needed for guarded crash recovery."""
        recovery_root = transaction_root / "recovery"
        prepared = self._mkdirs(recovery_root)
        if prepared.failure:
            return r[m.Infra.MiseToolchainJournal].from_failure(prepared)
        sources: list[m.Infra.MiseToolchainJournalSource] = []
        for state in states:
            source_path = self._workspace_relative(state.root / ".mise.toml")
            if source_path.failure:
                return r[m.Infra.MiseToolchainJournal].from_failure(source_path)
            sources.append(
                m.Infra.MiseToolchainJournalSource(
                    path=source_path.value,
                    sha256=self._digest(state.config_bytes),
                )
            )
        entries: list[m.Infra.MiseToolchainJournalEntry] = []
        for index, publication in enumerate(publications):
            artifact_path = self._workspace_relative(publication.path)
            if artifact_path.failure:
                return r[m.Infra.MiseToolchainJournal].from_failure(artifact_path)
            backup_selector = f"recovery/{index:04d}.original"
            backup_path = transaction_root / backup_selector
            backup = u.Cli.files_write_binary(
                backup_path, publication.expected_bytes
            )
            if backup.failure:
                return r[m.Infra.MiseToolchainJournal].fail(
                    backup.error or f"cannot back up {publication.path}"
                )
            entries.append(
                m.Infra.MiseToolchainJournalEntry(
                    path=artifact_path.value,
                    original_backup=backup_selector,
                    original_sha256=self._digest(publication.expected_bytes),
                    replacement_sha256=self._digest(publication.replacement_bytes),
                )
            )
        return r[m.Infra.MiseToolchainJournal].ok(
            m.Infra.MiseToolchainJournal(
                state="prepared", sources=tuple(sources), entries=tuple(entries)
            )
        )

    def _validate_journal_topology(
        self,
        journal: m.Infra.MiseToolchainJournal,
        states: tuple[m.Infra.MiseToolchainProjectState, ...],
    ) -> p.Result[bool]:
        """Bind untrusted journal paths to the exact governed workspace graph."""
        expected_sources: list[str] = []
        expected_entries: list[str] = []
        for state in states:
            source_path = self._workspace_relative(state.root / ".mise.toml")
            if source_path.failure:
                return r[bool].from_failure(source_path)
            expected_sources.append(source_path.value)
            for artifact_name in self._ARTIFACT_NAMES:
                artifact_path = self._workspace_relative(state.root / artifact_name)
                if artifact_path.failure:
                    return r[bool].from_failure(artifact_path)
                expected_entries.append(artifact_path.value)
        actual_sources = [source.path for source in journal.sources]
        actual_entries = [entry.path for entry in journal.entries]
        actual_backups = [entry.original_backup for entry in journal.entries]
        expected_backups = [
            f"recovery/{index:04d}.original"
            for index in range(len(expected_entries))
        ]
        if actual_sources != expected_sources:
            return r[bool].fail("Mise journal source topology differs from workspace")
        if actual_entries != expected_entries:
            return r[bool].fail("Mise journal artifact topology differs from workspace")
        if actual_backups != expected_backups:
            return r[bool].fail("Mise journal backup topology is invalid")
        return r[bool].ok(True)

    def _verify_journal_sources(
        self, journal: m.Infra.MiseToolchainJournal
    ) -> p.Result[bool]:
        """Prove that no governed .mise.toml changed across a transaction."""
        workspace_root = self._owner.workspace_root.resolve()
        for source in journal.sources:
            source_path = self._resolve_relative(
                workspace_root, source.path, purpose="Mise source"
            )
            if source_path.failure:
                return r[bool].from_failure(source_path)
            current = self._read_required_regular(source_path.value)
            if current.failure:
                return r[bool].from_failure(current)
            if self._digest(current.value) != source.sha256:
                return r[bool].fail(
                    f"Mise source changed during transaction: {source.path}"
                )
        return r[bool].ok(True)

    def _recover_interrupted_transaction(
        self, transaction_root: Path, journal_path: Path
    ) -> p.Result[bool]:
        """Recover a journaled crash without overwriting unrelated bytes."""
        loaded = self._read_journal(journal_path)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        journal, journal_bytes = loaded.value
        if (
            journal.state == "prepared"
            and not journal.sources
            and not journal.entries
        ):
            return self._cleanup_transaction(
                transaction_root,
                journal_path,
                expected_journal_bytes=journal_bytes,
            )
        states = self._project_states()
        if states.failure:
            return r[bool].from_failure(states)
        topology = self._validate_journal_topology(journal, states.value)
        if topology.failure:
            return topology
        source_check = self._verify_journal_sources(journal)
        if source_check.failure:
            return source_check
        workspace_root = self._owner.workspace_root.resolve()
        restores: list[m.Infra.MiseToolchainPublication] = []
        for entry in journal.entries:
            target = self._resolve_relative(
                workspace_root, entry.path, purpose="Mise artifact"
            )
            if target.failure:
                return r[bool].from_failure(target)
            current = self._read_required_regular(target.value)
            if current.failure:
                return r[bool].from_failure(current)
            current_digest = self._digest(current.value)
            if journal.state == "committed":
                if current_digest != entry.replacement_sha256:
                    return r[bool].fail(
                        f"committed Mise artifact changed before cleanup: {entry.path}"
                    )
                continue
            if current_digest == entry.original_sha256:
                continue
            if current_digest != entry.replacement_sha256:
                return r[bool].fail(
                    f"Mise artifact has foreign bytes during recovery: {entry.path}"
                )
            backup_path = self._resolve_relative(
                transaction_root,
                entry.original_backup,
                purpose="Mise recovery backup",
            )
            if backup_path.failure:
                return r[bool].from_failure(backup_path)
            original = self._read_required_regular(backup_path.value)
            if original.failure:
                return r[bool].from_failure(original)
            if self._digest(original.value) != entry.original_sha256:
                return r[bool].fail(
                    f"Mise recovery backup identity mismatch: {entry.path}"
                )
            restores.append(
                m.Infra.MiseToolchainPublication(
                    path=target.value,
                    expected_bytes=current.value,
                    replacement_bytes=original.value,
                )
            )
        for publication in reversed(restores):
            restored = self._guarded_write(publication)
            if restored.failure:
                return r[bool].fail(
                    restored.error
                    or f"Mise crash recovery failed for {publication.path}"
                )
        if journal.state == "prepared":
            for entry in journal.entries:
                target = self._resolve_relative(
                    workspace_root, entry.path, purpose="Mise artifact"
                )
                if target.failure:
                    return r[bool].from_failure(target)
                current = self._read_required_regular(target.value)
                if current.failure:
                    return r[bool].from_failure(current)
                if self._digest(current.value) != entry.original_sha256:
                    return r[bool].fail(
                        f"Mise artifact was not restored exactly: {entry.path}"
                    )
        else:
            committed_states = self._project_states()
            if committed_states.failure:
                return r[bool].from_failure(committed_states)
            validated = self._validate_live(committed_states.value)
            if validated.failure:
                return validated
        cleaned = self._cleanup_transaction(
            transaction_root,
            journal_path,
            expected_journal_bytes=journal_bytes,
        )
        if cleaned.failure:
            return cleaned
        return r[bool].ok(True)

    def _validate_live(
        self, states: tuple[m.Infra.MiseToolchainProjectState, ...]
    ) -> p.Result[bool]:
        """Validate every published project and byte-identical launchers."""
        root_launchers: tuple[bytes, bytes] | None = None
        for state in states:
            validated = self._owner._validate_artifacts(state.root)
            if validated.failure:
                return r[bool].fail(
                    validated.error
                    or f"published Mise artifact validation failed for {state.selector}"
                )
            unix = self._read_required_regular(state.root / "bin" / "mise")
            windows = self._read_required_regular(state.root / "bin" / "mise.cmd")
            if unix.failure or windows.failure:
                return r[bool].fail(
                    unix.error or windows.error or "cannot read published Mise launchers"
                )
            if root_launchers is None:
                root_launchers = (unix.value, windows.value)
            elif (unix.value, windows.value) != root_launchers:
                return r[bool].fail(
                    f"published Mise launchers differ in {state.selector}"
                )
        return r[bool].ok(True)

    def _publish(
        self,
        states: tuple[m.Infra.MiseToolchainProjectState, ...],
        publications: tuple[m.Infra.MiseToolchainPublication, ...],
    ) -> p.Result[bool]:
        """CAS-publish changed artifacts; the persisted journal owns restoration."""
        for state in states:
            current = self._read_required_regular(state.root / ".mise.toml")
            if current.failure or current.value != state.config_bytes:
                return r[bool].fail(
                    current.error
                    or f"CAS failed: .mise.toml changed in {state.selector}"
                )
        applied: list[m.Infra.MiseToolchainPublication] = []
        for publication in publications:
            if publication.expected_bytes == publication.replacement_bytes:
                continue
            written = self._guarded_write(publication)
            if written.failure:
                return r[bool].fail(
                    written.error or f"publish failed for {publication.path}"
                )
            applied.append(publication)
        validated = self._validate_live(states)
        if validated.failure:
            return r[bool].fail(
                validated.error or "published Mise validation failed"
            )
        u.Cli.info(
            "mise-toolchain: published "
            f"{len(applied)} changed artifact(s) across {len(states)} project(s)"
        )
        return r[bool].ok(True)

    def _stage_publications(
        self,
        *,
        credential_command: str,
        transaction_root: Path,
        states: tuple[m.Infra.MiseToolchainProjectState, ...],
    ) -> p.Result[tuple[m.Infra.MiseToolchainPublication, ...]]:
        """Generate and validate every candidate without changing live artifacts."""
        try:
            staging_device = transaction_root.stat().st_dev
            foreign_devices = tuple(
                state.selector
                for state in states
                if state.root.stat().st_dev != staging_device
            )
        except OSError as exc:
            return r[tuple[m.Infra.MiseToolchainPublication, ...]].fail_op(
                "inspect Mise staging filesystem", exc
            )
        if foreign_devices:
            return r[tuple[m.Infra.MiseToolchainPublication, ...]].fail(
                "Mise staging must share every destination filesystem: "
                f"{', '.join(foreign_devices)}"
            )
        latest = self._latest_receipt(transaction_root)
        if latest.failure:
            return r[tuple[m.Infra.MiseToolchainPublication, ...]].from_failure(
                latest
            )
        launcher, _release = latest.value
        receipt_root = launcher.parents[1]
        stage_roots: list[Path] = []
        root_stage: Path | None = None
        root_config = states[0].config_bytes
        for index, state in enumerate(states):
            stage_root = transaction_root / "projects" / f"{index:04d}"
            staged = self._stage_project(
                state,
                stage_root=stage_root,
                receipt_root=receipt_root,
                scratch=transaction_root,
                credential_command=credential_command,
                root_stage=root_stage,
                root_config=root_config,
            )
            if staged.failure:
                return r[
                    tuple[m.Infra.MiseToolchainPublication, ...]
                ].from_failure(staged)
            stage_roots.append(stage_root)
            if index == 0:
                root_stage = stage_root
        return self._publication_plan(states, tuple(stage_roots))

    @classmethod
    def _fail_without_publication(
        cls, transaction_root: Path, message: str
    ) -> p.Result[bool]:
        """Discard unpublished staging once and retain any cleanup failure."""
        removed = cls._remove_transaction_directory(transaction_root)
        if removed.failure:
            return r[bool].fail(
                f"{message}; staging cleanup failed: "
                f"{removed.error or 'unknown cleanup failure'}"
            )
        return r[bool].fail(message)

    def _restore_failed_publication(
        self,
        *,
        transaction_root: Path,
        journal_path: Path,
        failure: str,
    ) -> p.Result[bool]:
        """Perform the journal's single normal-failure restoration attempt."""
        recovered = self._recover_interrupted_transaction(
            transaction_root, journal_path
        )
        if recovered.failure:
            return r[bool].fail(
                f"{failure}; recovery failed: "
                f"{recovered.error or 'unknown recovery failure'}"
            )
        return r[bool].fail(failure)

    def _execute_locked(
        self,
        *,
        credential_command: str,
        transaction_root: Path,
        journal_path: Path,
    ) -> p.Result[bool]:
        """Prepare and publish while the workspace-wide process lock is held."""
        if journal_path.exists() or journal_path.is_symlink():
            recovered = self._recover_interrupted_transaction(
                transaction_root, journal_path
            )
            if recovered.failure:
                return recovered
            return r[bool].fail(
                "recovered an interrupted Mise transaction; rerun the command"
            )
        if transaction_root.exists() or transaction_root.is_symlink():
            removed = self._remove_transaction_directory(transaction_root)
            if removed.failure:
                return removed
            return r[bool].fail(
                "removed unpublished Mise transaction staging; rerun the command"
            )
        try:
            transaction_root.mkdir(parents=False, exist_ok=False)
        except OSError as exc:
            return r[bool].fail_op("create Mise transaction root", exc)
        states = self._project_states()
        if states.failure:
            return self._fail_without_publication(
                transaction_root,
                states.error or "cannot snapshot the Mise workspace",
            )
        publications = self._stage_publications(
            credential_command=credential_command,
            transaction_root=transaction_root,
            states=states.value,
        )
        if publications.failure:
            return self._fail_without_publication(
                transaction_root,
                publications.error or "cannot stage Mise artifacts",
            )
        prepared_journal = self._prepared_journal(
            states.value, publications.value, transaction_root
        )
        if prepared_journal.failure:
            return self._fail_without_publication(
                transaction_root,
                prepared_journal.error or "cannot prepare Mise recovery journal",
            )
        prepared_bytes = self._write_journal(
            journal_path, prepared_journal.value, expected_bytes=None
        )
        if prepared_bytes.failure:
            if journal_path.exists() or journal_path.is_symlink():
                return r[bool].fail(
                    prepared_bytes.error
                    or "Mise journal publication failed with persistent state"
                )
            return self._fail_without_publication(
                transaction_root,
                prepared_bytes.error or "cannot publish Mise recovery journal",
            )
        published = self._publish(states.value, publications.value)
        if published.failure:
            return self._restore_failed_publication(
                transaction_root=transaction_root,
                journal_path=journal_path,
                failure=published.error or "Mise artifact publication failed",
            )
        committed = prepared_journal.value.model_copy(update={"state": "committed"})
        committed_bytes = self._write_journal(
            journal_path, committed, expected_bytes=prepared_bytes.value
        )
        if committed_bytes.failure:
            return self._restore_failed_publication(
                transaction_root=transaction_root,
                journal_path=journal_path,
                failure=committed_bytes.error or "cannot commit Mise journal",
            )
        cleaned = self._cleanup_transaction(
            transaction_root,
            journal_path,
            expected_journal_bytes=committed_bytes.value,
        )
        if cleaned.failure:
            return cleaned
        return r[bool].ok(True)

    @staticmethod
    def _physical_scratch_parent(root: Path) -> p.Result[Path]:
        """Create one physical scratch directory directly below its Git root."""
        try:
            resolved_root = root.resolve()
        except OSError as exc:
            return r[Path].fail_op("resolve Mise scratch owner", exc)
        scratch_parent = resolved_root / ".test-tmp"
        if scratch_parent.is_symlink():
            return r[Path].fail(
                f"Mise transaction root is a symlink: {scratch_parent}"
            )
        prepared = FlextInfraCodegenMiseArtifactTransaction._mkdirs(scratch_parent)
        if prepared.failure:
            return r[Path].from_failure(prepared)
        if not scratch_parent.is_dir():
            return r[Path].fail(
                f"Mise transaction root is not a directory: {scratch_parent}"
            )
        try:
            resolved_scratch = scratch_parent.resolve()
        except OSError as exc:
            return r[Path].fail_op(
                "resolve Mise transaction root", exc
            )
        if resolved_scratch.parent != resolved_root:
            return r[Path].fail(
                f"Mise staging is not on the workspace filesystem: {scratch_parent}"
            )
        return r[Path].ok(resolved_scratch)

    def _coordination_root(self) -> p.Result[Path]:
        """Use the Git umbrella as lock owner when this invocation is a member."""
        workspace_root = self._owner.workspace_root.resolve()
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=workspace_root)
        )
        if identity.failure:
            return r[Path].fail(
                identity.error or "cannot resolve Mise transaction Git identity"
            )
        if identity.value.is_submodule:
            superproject_root = identity.value.superproject_root
            if superproject_root is None:
                return r[Path].fail(
                    f"Git submodule has no coordination root: {workspace_root}"
                )
            try:
                return r[Path].ok(superproject_root.resolve())
            except OSError as exc:
                return r[Path].fail_op("resolve Mise coordination root", exc)
        return r[Path].ok(workspace_root)

    def _transaction_paths(self) -> p.Result[tuple[Path, Path, Path]]:
        """Resolve local staging/journal and the shared Git-umbrella lock."""
        workspace_scratch = self._physical_scratch_parent(
            self._owner.workspace_root
        )
        if workspace_scratch.failure:
            return r[tuple[Path, Path, Path]].from_failure(workspace_scratch)
        coordination_root = self._coordination_root()
        if coordination_root.failure:
            return r[tuple[Path, Path, Path]].from_failure(coordination_root)
        coordination_scratch = self._physical_scratch_parent(
            coordination_root.value
        )
        if coordination_scratch.failure:
            return r[tuple[Path, Path, Path]].from_failure(coordination_scratch)
        transaction_root = workspace_scratch.value / self._TRANSACTION_DIR_NAME
        journal_path = workspace_scratch.value / self._JOURNAL_NAME
        lock_path = coordination_scratch.value / self._LOCK_NAME
        if lock_path.is_symlink():
            return r[tuple[Path, Path, Path]].fail(
                f"Mise transaction lock is a symlink: {lock_path}"
            )
        return r[tuple[Path, Path, Path]].ok(
            (transaction_root, journal_path, lock_path)
        )

    def validate(self) -> p.Result[bool]:
        """Validate one stable workspace snapshot under the publication lock."""
        paths = self._transaction_paths()
        if paths.failure:
            return r[bool].from_failure(paths)
        transaction_root, journal_path, lock_path = paths.value
        try:
            with FileLock(str(lock_path), timeout=0):
                if journal_path.exists() or journal_path.is_symlink():
                    return r[bool].fail(
                        "pending Mise transaction requires apply-mode recovery"
                    )
                if transaction_root.exists() or transaction_root.is_symlink():
                    return r[bool].fail(
                        "unpublished Mise staging requires apply-mode cleanup"
                    )
                states = self._project_states()
                if states.failure:
                    return r[bool].from_failure(states)
                return self._validate_live(states.value)
        except Timeout:
            return r[bool].fail(
                f"another Mise artifact transaction owns the workspace: {lock_path}"
            )
        except OSError as exc:
            return r[bool].fail_op("validate Mise toolchain transaction", exc)

    def execute(self) -> p.Result[bool]:
        """Run one locked, journaled workspace-wide Mise publication."""
        credential_command = settings.Infra.mise_github_credential_command
        if credential_command is None or not credential_command.strip():
            return r[bool].fail(
                "MISE_GITHUB_CREDENTIAL_COMMAND is required for Mise lock publication"
            )
        paths = self._transaction_paths()
        if paths.failure:
            return r[bool].from_failure(paths)
        transaction_root, journal_path, lock_path = paths.value
        try:
            with FileLock(str(lock_path), timeout=0):
                return self._execute_locked(
                    credential_command=credential_command.strip(),
                    transaction_root=transaction_root,
                    journal_path=journal_path,
                )
        except Timeout:
            return r[bool].fail(
                f"another Mise artifact transaction owns the workspace: {lock_path}"
            )
        except OSError as exc:
            return r[bool].fail_op("execute Mise toolchain transaction", exc)


__all__: list[str] = ["FlextInfraCodegenMiseArtifactTransaction"]
