"""Qualify installed native process inputs during setup.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import base64
import platform
import shutil
import socket
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

from flext_cli import config as cli_config

from flext_infra import c, codegen, config, m, p, r, u

_PRIVATE_EXECUTABLE_MODE = 0o500


class FlextInfraNativeSetup:
    """Produce original setup observations using the installed native tools."""

    @staticmethod
    def _resource(
        distribution_name: str,
        parts: tuple[str, ...],
    ) -> p.Cli.AtomicFileReceipt:
        owner = distribution(distribution_name)
        matches = tuple(
            entry for entry in owner.files or () if entry.parts[-len(parts) :] == parts
        )
        if len(matches) != 1 or matches[0].hash is None:
            msg = f"{distribution_name} RECORD does not own one resource: {parts}"
            raise ValueError(msg)
        entry = matches[0]
        entry_hash = entry.hash
        if entry_hash is None or entry_hash.mode != "sha256":
            msg = f"{distribution_name} RECORD lacks SHA-256 for {entry.as_posix()}"
            raise ValueError(msg)
        path = Path(str(entry.locate())).resolve(strict=True)
        root = Path(str(owner.locate_file(""))).resolve(strict=True)
        if not path.is_relative_to(root):
            msg = f"installed resource escapes its distribution: {path}"
            raise ValueError(msg)
        state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        payload = state.content
        if payload is None:
            msg = f"installed resource has no authenticated content: {path}"
            raise ValueError(msg)
        digest = (
            base64
            .urlsafe_b64encode(bytes.fromhex(u.Cli.sha256_bytes(payload)))
            .decode("ascii")
            .rstrip("=")
        )
        if digest != entry_hash.value or entry.size != len(payload):
            msg = f"installed resource differs from its RECORD entry: {path}"
            raise ValueError(msg)
        return FlextInfraNativeSetup._receipt_for_state(state)

    @staticmethod
    def _provider(
        repository_root: Path,
        mise: Path,
        provider: p.Infra.NativeIsolationProvider,
        toolchain: p.Infra.ToolchainSpec,
    ) -> p.Cli.AtomicFileReceipt:
        manifest = repository_root / c.Infra.MISE_TOML_FILENAME
        lock = u.Cli.toml_mapping_from_text_result(
            (repository_root / c.Infra.MISE_LOCK_FILENAME).read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
        ).unwrap()
        entry = next(
            item
            for item in toolchain.tools
            if (item.selector or item.name) == provider.tool
        )
        proof = codegen.FlextInfraCodegenMiseToolchainProof
        version, _ = proof.lock_identity(
            entry,
            lock,
            proof.current_platform().unwrap(),
        ).unwrap()
        query = [str(mise), "-C", str(repository_root)]
        options = m.Cli.ProcessOptions(env={"MISE_LOCKED": "1"})
        selected = FlextInfraNativeSetup._query(
            [*query, "tool", provider.tool, "--config-source"],
            repository_root,
            options,
        )
        if Path(selected).expanduser().resolve(strict=True) != manifest:
            msg = (
                f"native resource is not requested by the workspace manifest: "
                f"{provider.tool}"
            )
            raise ValueError(msg)
        located = FlextInfraNativeSetup._query(
            [*query, "where", f"{provider.tool}@{version}"],
            repository_root,
            options,
        )
        base = Path(located).resolve(strict=True)
        path = (base / provider.relative_path).resolve(strict=True)
        if path == base or not path.is_relative_to(base):
            msg = f"native resource escapes locked installation: {provider.tool}"
            raise ValueError(msg)
        receipt = FlextInfraNativeSetup._receipt(path)
        if receipt.sha256 != provider.sha256:
            msg = f"native installation differs from its producer digest: {path}"
            raise ValueError(msg)
        return receipt

    @staticmethod
    def _query(
        argv: list[str],
        cwd: Path,
        options: p.Cli.ProcessOptions,
    ) -> str:
        result = u.Cli.run_raw(
            argv,
            cwd=cwd,
            options=options,
            timeout=c.Infra.TIMEOUT_SHORT,
        ).unwrap()
        if (
            not u.Cli.process_succeeded(result.outcome)
            or result.stderr.strip()
            or not result.stdout.strip()
        ):
            msg = f"Mise did not resolve the original locked tool: {result.stderr}"
            raise ValueError(msg)
        return result.stdout.strip()

    @staticmethod
    def _run(
        argv: list[str],
        cwd: Path,
        *,
        pass_fds: tuple[int, ...] = (),
    ) -> p.Cli.CommandBytesOutput:
        result = u.Cli.run_bytes(
            argv,
            cwd=cwd,
            options=m.Cli.ProcessOptions(
                pass_fds=pass_fds,
                env={"HOME": str(cwd), "TMPDIR": str(cwd)},
                inherit_environment=False,
            ),
            timeout=c.Infra.TIMEOUT_DEFAULT,
        ).unwrap()
        if not u.Cli.process_succeeded(result.outcome):
            error = result.stderr.decode(c.DEFAULT_ENCODING, errors="replace")
            msg = f"{argv[0]} exited {result.outcome.raw_return_code}: {error}"
            raise ValueError(msg)
        return result

    @staticmethod
    def _namespace(launcher: Path) -> list[str]:
        return [
            str(launcher),
            "--unshare-user",
            "--unshare-ipc",
            "--unshare-pid",
            "--unshare-net",
            "--unshare-uts",
            "--unshare-cgroup",
            "--disable-userns",
            "--assert-userns-disabled",
            "--new-session",
            "--die-with-parent",
            "--cap-drop",
            "ALL",
            "--clearenv",
        ]

    @classmethod
    def _observe(
        cls,
        root: Path,
        launcher: Path,
        compiler: Path,
        probe: Path,
        *,
        fixture: bool,
    ) -> tuple[
        p.Cli.ProcessOutcome,
        tuple[p.Cli.ProcessNativePolicyProbe, ...],
    ]:
        args = u.Cli.native_process_policy_arguments(fixture=fixture)
        policy = cls._run([str(compiler), *args], root).stdout
        profile = "fixture" if fixture else "read-only"
        writable = root / profile
        writable.mkdir()
        with (
            tempfile.TemporaryFile(dir=root) as descriptor,
            socket.socket(socket.AF_UNIX) as listener,
        ):
            descriptor.write(policy)
            descriptor.seek(0)
            listener.bind(str(writable / "outside.sock"))
            listener.listen(1)
            launcher_argv = [
                *cls._namespace(launcher),
                "--bind",
                str(writable),
                "/probe",
                "--ro-bind",
                str(probe),
                "/native-probe",
                "--ro-bind",
                str(compiler),
                "/native-policy",
                "--remount-ro",
                "/",
                "--seccomp",
                str(descriptor.fileno()),
                "--",
            ]
            command = ["/native-probe", profile]
            if fixture:
                command[:0] = ["/native-policy", "--fixture-exec"]
            result = cls._run(
                [*launcher_argv, *command],
                root,
                pass_fds=(descriptor.fileno(),),
            )
        observed = tuple(
            m.Cli.ProcessNativePolicyProbe(syscall=name, observed_errno=int(value))
            for line in result.stdout.decode("ascii").splitlines()
            for name, _, value in (line.partition("="),)
        )
        expected = u.Cli.native_process_policy_observations(fixture=fixture)
        if (
            len(observed) != len(expected)
            or {item.syscall: item.observed_errno for item in observed} != expected
        ):
            msg = f"native {profile} observations differ from the elected policy"
            raise ValueError(msg)
        return result.outcome, observed

    @staticmethod
    def _receipt(path: Path) -> p.Cli.AtomicFileReceipt:
        return u.Cli.atomic_read_binary_file_receipt(
            path,
            required=True,
        ).unwrap()

    @classmethod
    def _receipt_for_state(
        cls,
        state: p.Cli.AtomicFileState,
    ) -> p.Cli.AtomicFileReceipt:
        receipt = cls._receipt(state.path)
        content = state.content
        if (
            content is None
            or receipt.sha256 != u.Cli.sha256_bytes(content)
            or (receipt.device, receipt.inode, receipt.mode)
            != (state.device, state.inode, state.mode)
        ):
            msg = f"native setup input changed after selection: {state.path}"
            raise ValueError(msg)
        return receipt

    @staticmethod
    def _publish_compiler(build: Path, repository_root: Path) -> Path:
        content = build.read_bytes()
        directory = (
            repository_root / c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH.parent
        )
        if directory.resolve(strict=True) != directory:
            msg = "native setup compiler artifact root must stay physical"
            raise ValueError(msg)
        destination = directory / f"{build.name}-{u.Cli.sha256_bytes(content)}"
        before = u.Cli.atomic_read_binary_file_state(
            destination,
            required=False,
        ).unwrap()
        if before.content is None:
            u.Cli.atomic_write_binary_file_guarded(
                before,
                content,
                permission_mode=_PRIVATE_EXECUTABLE_MODE,
            ).unwrap()
        elif before.content != content or before.mode != _PRIVATE_EXECUTABLE_MODE:
            msg = f"native compiler content-addressed artifact drift: {destination}"
            raise ValueError(msg)
        return destination

    @classmethod
    def _elected_inputs(
        cls,
        repository_root: Path,
    ) -> m.Infra.NativeSetupInputs:
        if sys.platform != "linux":
            msg = "the elected native process setup requires Linux"
            raise ValueError(msg)
        codegen_inputs = u.Infra.load_codegen_inputs(repository_root).unwrap()
        toolchain = codegen_inputs.spec.toolchain
        declared = toolchain.native_isolation
        if not isinstance(declared, m.Infra.NativeIsolationSetup):
            msg = "the workspace has not elected native isolation setup"
            raise TypeError(msg)
        mise = u.Infra.managed_mise_self(repository_root).unwrap()
        installed = tuple(
            cls._provider(repository_root, mise, entry, toolchain)
            for entry in (
                declared.launcher,
                declared.compiler,
                declared.extractor,
                declared.seccomp_header,
                declared.seccomp_syscalls,
                declared.seccomp_archive,
            )
        )
        launcher, compiler, extractor, header, syscalls, archive = installed
        if (
            header.path.parent != syscalls.path.parent
            or header.path.name != "seccomp.h"
            or syscalls.path.name != "seccomp-syscalls.h"
        ):
            msg = "elected libseccomp headers must share the SDK include directory"
            raise ValueError(msg)
        return m.Infra.NativeSetupInputs(
            launcher=launcher,
            extractor=extractor,
            extractor_arguments=declared.extractor_arguments,
            compiler_archive=compiler,
            compiler_member=declared.compiler_member,
            compiler_arguments=declared.compiler_arguments,
            archive=archive.path,
            headers=(header.path, syscalls.path),
            sources=(
                cls._resource(
                    cli_config.Cli.name,
                    cli_config.ProcessIsolation.compiler_resource_parts,
                ),
                cls._resource(
                    config.Infra.name,
                    ("workspace", "resources", "native_isolation_probe.c"),
                ),
            ),
            declaration=(
                cls._receipt(repository_root / c.Infra.MISE_TOML_FILENAME),
                *(
                    cls._receipt_for_state(state)
                    for state in codegen_inputs.sources
                    if state.content is not None
                ),
            ),
            installation=(
                cls._receipt(repository_root / c.Infra.MISE_LOCK_FILENAME),
                cls._receipt(mise),
                *installed,
            ),
            abi_reference=cls._receipt(Path(sys.executable).resolve(strict=True)),
            profiles=declared.profiles,
        )

    @classmethod
    def _materialize_sdk(
        cls,
        private: Path,
        inputs: m.Infra.NativeSetupInputs,
    ) -> Path:
        archive = private / "sdk-archive"
        shutil.copyfile(inputs.compiler_archive.path, archive)
        if cls._receipt(archive).sha256 != inputs.compiler_archive.sha256:
            msg = "native compiler SDK changed during materialization"
            raise ValueError(msg)
        sdk = private / "sdk"
        sdk.mkdir()
        extractor = str(inputs.extractor.path)
        cls._run(
            [
                *cls._namespace(inputs.launcher.path),
                "--ro-bind",
                extractor,
                extractor,
                "--ro-bind",
                str(archive),
                str(archive),
                "--bind",
                str(sdk),
                str(sdk),
                "--remount-ro",
                "/",
                "--",
                extractor,
                *inputs.extractor_arguments,
                str(archive),
                "-C",
                str(sdk),
            ],
            private,
        )
        compiler = (sdk / inputs.compiler_member).resolve(strict=True)
        if not compiler.is_relative_to(sdk):
            msg = "native compiler member escapes the authenticated SDK"
            raise ValueError(msg)
        return compiler

    @classmethod
    def _build(
        cls,
        scratch: Path,
        inputs: m.Infra.NativeSetupInputs,
        compiler: Path,
    ) -> p.Cli.ProcessOutcome:
        policy_source, probe_source = (receipt.path for receipt in inputs.sources)
        command = cls._namespace(inputs.launcher.path)
        for path in (
            compiler.parent,
            *inputs.headers,
            inputs.archive,
            policy_source,
            probe_source,
        ):
            command.extend(("--ro-bind", str(path), str(path)))
        command.extend((
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--bind",
            str(scratch),
            str(scratch),
            "--chdir",
            str(scratch),
            "--setenv",
            "HOME",
            str(scratch),
            "--setenv",
            "TMPDIR",
            str(scratch),
            "--setenv",
            "PATH",
            str(compiler.parent),
            "--remount-ro",
            "/",
            "--",
            str(compiler),
            *inputs.compiler_arguments,
            "-std=c17",
            "-static",
            "-Wall",
            "-Wextra",
            "-Werror",
        ))
        built = cls._run(
            [
                *command,
                "-I",
                str(inputs.headers[0].parent),
                str(policy_source),
                str(inputs.archive),
                "-o",
                str(scratch / "policy-compiler"),
            ],
            scratch,
        )
        cls._run(
            [
                *command,
                str(probe_source),
                "-o",
                str(scratch / "policy-probe"),
            ],
            scratch,
        )
        return built.outcome

    @classmethod
    def _qualify(
        cls,
        repository_root: Path,
    ) -> tuple[p.Cli.ProcessNativeToolEvidence, ...]:
        inputs = cls._elected_inputs(repository_root)
        abi = u.Cli.native_binary_identity(
            inputs.abi_reference.path.read_bytes(),
            require_static=False,
        )
        cls._validate_tool_abi(inputs.launcher.path, abi)
        cls._validate_tool_abi(inputs.extractor.path, abi)
        with tempfile.TemporaryDirectory(prefix="flext-native-setup-") as private:
            root = Path(private)
            compiler = cls._materialize_sdk(root, inputs)
            cls._validate_tool_abi(compiler, abi)
            scratch = root / "run"
            scratch.mkdir()
            policy = scratch / "policy-compiler"
            probe = scratch / "policy-probe"
            built = cls._build(scratch, inputs, compiler)
            cls._validate_tool_abi(policy, abi)
            abi_probe = cls._run([str(policy)], scratch)
            seccomp_token = abi_probe.stdout.decode("ascii").strip()
            if not seccomp_token.isdecimal():
                msg = "native setup compiler did not provide its numeric ABI"
                raise ValueError(msg)
            qualified = tuple(
                (
                    profile,
                    *cls._observe(
                        scratch,
                        inputs.launcher.path,
                        policy,
                        probe,
                        fixture=profile == "fixture",
                    ),
                )
                for profile in inputs.profiles
            )
            for receipt in (
                *inputs.declaration,
                *inputs.sources,
                *inputs.installation,
                inputs.abi_reference,
            ):
                if cls._receipt(receipt.path) != receipt:
                    msg = (
                        f"native setup input changed before publication: {receipt.path}"
                    )
                    raise ValueError(msg)
            artifact = cls._receipt(cls._publish_compiler(policy, repository_root))
        architecture = platform.machine()
        return tuple(
            m.Cli.ProcessNativeToolEvidence.model_validate({
                "role": role,
                "artifact_receipt": (
                    artifact if role == "policy-compiler" else inputs.launcher
                ),
                "declaration_inputs": inputs.declaration,
                "installation_inputs": inputs.installation,
                "source_inputs": inputs.sources,
                "native_build_outcome": built,
                "native_abi_probe_outcome": abi_probe.outcome,
                "native_policy_probe_outcome": outcome,
                "policy_sha256": u.Cli.native_process_policy_identity(
                    fixture=profile == "fixture"
                ),
                "native_policy_probes": observations,
                "probe_compiler_receipt": artifact,
                "abi_reference": inputs.abi_reference,
                "architecture": architecture,
            })
            for profile, outcome, observations in qualified
            for role in ("isolation-launcher", "policy-compiler")
        )

    @staticmethod
    def _validate_tool_abi(candidate: Path, expected: tuple[int, int, int]) -> None:
        observed = u.Cli.native_binary_identity(
            candidate.read_bytes(), require_static=True
        )
        if observed != expected:
            msg = f"native tool ABI differs from the installed runtime: {candidate}"
            raise ValueError(msg)

    @staticmethod
    def _read_pending(
        root: Path,
        pending: Path,
    ) -> tuple[m.Infra.WorkspaceOperationReport, p.Cli.AtomicFileState]:
        destination = root / c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH
        if (
            pending.parent != destination.parent
            or not pending.name.startswith(destination.name + ".")
            or pending.resolve(strict=True) != pending
        ):
            msg = "pending setup receipt is outside the original report authority"
            raise ValueError(msg)
        source = u.Cli.atomic_read_binary_file_state(pending, required=True).unwrap()
        if source.content is None:
            msg = "native qualification requires the pending setup receipt"
            raise ValueError(msg)
        report = m.Infra.WorkspaceOperationReport.model_validate_json(source.content)
        if (
            report.operation != "tool-bootstrap"
            or len(report.receipts) != 1
            or not report.receipts[0].completed
            or report.receipts[0].native_exit_code != 0
            or report.receipts[0].native_tool_qualifications
        ):
            msg = "native qualification requires one original completed setup receipt"
            raise ValueError(msg)
        return report, source

    @classmethod
    def _attach_pending(
        cls,
        repository_root: Path,
        pending: Path,
    ) -> int:
        root = repository_root.resolve(strict=True)
        report, source = cls._read_pending(root, pending)
        identity_request = m.Infra.GitRepoRequest(repo_root=root)
        identity = u.Infra.git_identity(identity_request, include_status=False).unwrap()
        if (
            identity.repo_root != root
            or not identity.head_oid
            or report.candidate_sha != identity.head_oid
        ):
            msg = "pending setup receipt belongs to a different Git candidate"
            raise ValueError(msg)
        qualifications = cls._qualify(root)
        current = u.Infra.git_identity(identity_request, include_status=False).unwrap()
        if current != identity:
            msg = "native setup candidate changed before evidence publication"
            raise ValueError(msg)
        receipt = report.receipts[0].model_copy(
            update={"native_tool_qualifications": qualifications},
        )
        completed = report.model_copy(update={"receipts": (receipt,)})
        u.Cli.atomic_write_binary_file_guarded(
            source,
            completed.model_dump_json(round_trip=True).encode(c.DEFAULT_ENCODING),
            permission_mode=source.mode,
        ).unwrap()
        return len(qualifications)

    @classmethod
    def qualify_pending(
        cls,
        repository_root: Path,
        pending: Path,
    ) -> p.Result[int]:
        """Attach native observations to this setup's pending typed receipt.

        Returns:
            The count of original native qualifications, or the producer failure.

        """
        try:
            count = cls._attach_pending(repository_root, pending)
        except (OSError, TypeError, ValueError) as error:
            return r[int].fail(f"native setup qualification failed: {error}")
        return r[int].ok(count)


__all__ = ["FlextInfraNativeSetup"]
