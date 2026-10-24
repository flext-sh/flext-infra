"""Cold settings-input election for editable suppliers and hosted runners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import errno
import sys
from pathlib import Path

import pytest

from flext_infra import settings
from tests import c, m, t, tm, u


class TestsFlextInfraEditableSupplierInput:
    """Hosted execution ignores host-only paths before native path validation."""

    @staticmethod
    def _consumer(tmp_path: Path) -> Path:
        """Create a native repository without changing process-wide settings.

        Returns:
            The resulting ``Path``.

        """
        consumer = tmp_path / "consumer"
        u.Tests.WorktreeFixture.initialize_governed_project(
            consumer,
            "consumer",
            beads=u.Tests.BeadsIdentity(
                workspace="consumer", database="consumer", issue_prefix="consumer"
            ),
        )
        return consumer

    @staticmethod
    def _run_cold(tmp_path: Path, source: str, environment: t.StrMapping) -> None:
        """Execute the installed public consumer with only elected inputs."""
        output = tm.ok(
            u.Cli.run_raw(
                [sys.executable, "-I", "-c", source],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        "HOME": str(tmp_path),
                        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                        **environment,
                    },
                    inherit_environment=False,
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)

    @staticmethod
    @pytest.mark.parametrize(
        ("hosted", "supplier"),
        [
            (c.ParserBooleanToken.TRUE, "missing"),
            (c.ParserBooleanToken.TRUE, "relative"),
            (c.ParserBooleanToken.FALSE, "empty"),
        ],
    )
    def test_cold_import_ignores_unselected_supplier(
        tmp_path: Path, hosted: str, supplier: str
    ) -> None:
        """A runner never depends on an inherited local workspace directory."""
        selected = (
            str(tmp_path / "missing")
            if supplier == "missing"
            else "relative"
            if supplier == "relative"
            else ""
        )
        output = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "from flext_infra import settings; "
                        "print(settings.Infra.editable_supplier_root is None)"
                    ),
                ],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ENV_VAR_GITHUB_ACTIONS: hosted,
                        type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT: selected,
                        "HOME": str(tmp_path),
                        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                    },
                    inherit_environment=False,
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="True")
        tm.that(output.stderr, eq="")

    @staticmethod
    def test_local_cold_import_refuses_relative_supplier(tmp_path: Path) -> None:
        """Ignoring the host path is restricted to the actual hosted mode."""
        output = tm.ok(
            u.Cli.run_raw(
                [sys.executable, "-I", "-c", "from flext_infra import settings"],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ENV_VAR_GITHUB_ACTIONS: c.ParserBooleanToken.FALSE,
                        type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT: "relative",
                        "HOME": str(tmp_path),
                        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                    },
                    inherit_environment=False,
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=False)
        tm.that(output.stderr, has="editable supplier root must be an absolute path")

    @staticmethod
    @pytest.mark.parametrize(
        "receipt",
        [
            "empty-bytes",
            "missing-newline",
            "extra-line",
            "crlf",
            "nul",
            "invalid-utf8",
            "relative",
            "symlink",
            "dangling-receipt",
            "directory",
        ],
    )
    def test_invalid_persisted_selection_fails_without_fallback(
        tmp_path: Path,
        receipt: str,
    ) -> None:
        """A malformed receipt must not become a different or absent supplier."""
        consumer = TestsFlextInfraEditableSupplierInput._consumer(tmp_path)
        supplier = tmp_path / "supplier"
        supplier.mkdir()
        policy = tm.ok(u.Infra.load_codegen_inputs(consumer)).spec.make.uv_resolution
        selection = consumer / policy.supplier_selection_file
        selection.parent.mkdir(parents=True, exist_ok=True)
        target = tmp_path / "selection"
        payload: bytes | None = None
        if receipt in {"symlink", "dangling-receipt"}:
            if receipt == "symlink":
                target.write_text(f"{supplier}\n", encoding="utf-8")
            selection.symlink_to(target)
        elif receipt == "directory":
            selection.mkdir()
        else:
            payload = {
                "empty-bytes": b"",
                "missing-newline": str(supplier).encode(),
                "extra-line": f"{supplier}\n\n".encode(),
                "crlf": f"{supplier}\r\n".encode(),
                "nul": f"{supplier}\x00\n".encode(),
                "invalid-utf8": b"\xff\n",
                "relative": b"relative\n",
            }[receipt]
            selection.write_bytes(payload)
        declaration = consumer / c.PYPROJECT_FILENAME
        before = declaration.read_bytes()
        state = selection.lstat()
        TestsFlextInfraEditableSupplierInput._run_cold(
            tmp_path,
            "from pathlib import Path\n"
            "import errno\n"
            "from flext_infra import workspace\n"
            f"consumer = Path({str(consumer)!r})\n"
            "result = workspace.FlextInfraWorkspaceDetector."
            "resolution_context(consumer)\n"
            "assert result.failure, result\n"
            + (
                "assert isinstance(result.exception, OSError), result.exception\n"
                "assert result.exception.errno == errno.EINVAL, result.exception\n"
                f"assert str(result.exception.filename) == {str(selection)!r}\n"
                if receipt in {"symlink", "dangling-receipt", "directory"}
                else "assert isinstance(result.exception, UnicodeDecodeError), "
                "result.exception\n"
                if receipt == "invalid-utf8"
                else "assert 'absolute path' in result.error, result.error\n"
                if receipt == "relative"
                else "assert 'one UTF-8 line' in result.error, result.error\n"
            ),
            {policy.hosted_variable: c.ParserBooleanToken.FALSE},
        )
        tm.that(declaration.read_bytes(), eq=before)
        tm.that(selection.lstat().st_ino, eq=state.st_ino)
        if receipt in {"symlink", "dangling-receipt"}:
            tm.that(selection.readlink(), eq=target)
            if receipt == "symlink":
                tm.that(target.read_bytes(), eq=f"{supplier}\n".encode())
            else:
                tm.that(target.exists(), eq=False)
        elif receipt == "directory":
            tm.that(tuple(selection.iterdir()), eq=())
        else:
            tm.that(selection.read_bytes(), eq=payload)

    @staticmethod
    @pytest.mark.parametrize("mode", ["empty", "nonempty", "hosted", "hosted-explicit"])
    def test_explicit_or_hosted_mode_ignores_persisted_supplier(
        tmp_path: Path,
        mode: str,
    ) -> None:
        """A disabled selection or hosted isolation wins before receipt validation."""
        consumer = TestsFlextInfraEditableSupplierInput._consumer(tmp_path)
        policy = tm.ok(u.Infra.load_codegen_inputs(consumer)).spec.make.uv_resolution
        selection = consumer / policy.supplier_selection_file
        selection.parent.mkdir(parents=True, exist_ok=True)
        absent = tmp_path / "absent"
        selection.symlink_to(absent)
        supplier = tmp_path / "explicit supplier"
        supplier.mkdir()
        hosted = mode.startswith("hosted")
        environment = {
            policy.hosted_variable: policy.hosted_value
            if hosted
            else c.ParserBooleanToken.FALSE
        }
        if mode != "hosted":
            environment[type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT] = (
                str(supplier) if mode == "nonempty" else "relative" if hosted else ""
            )
        directory = (
            policy.standalone_directory
            if hosted
            else policy.editable_directory
            if mode == "nonempty"
            else policy.local_directory
        )
        expected = supplier.resolve() if mode == "nonempty" else None
        expected_source = f"Path({str(expected)!r})" if expected is not None else "None"
        declaration = consumer / c.PYPROJECT_FILENAME
        before = declaration.read_bytes()
        state = selection.lstat()
        TestsFlextInfraEditableSupplierInput._run_cold(
            tmp_path,
            "from pathlib import Path\n"
            "from flext_infra import workspace\n"
            f"consumer = Path({str(consumer)!r})\n"
            "result = workspace.FlextInfraWorkspaceDetector."
            "resolution_context(consumer)\n"
            "assert not result.failure, result.error\n"
            f"assert result.value.editable_supplier_root == {expected_source}\n"
            f"assert result.value.resolution_root == "
            f"Path({str(consumer / directory)!r})\n"
            f"assert result.value.environment_path == "
            f"Path({str(consumer / c.Infra.ENVIRONMENT_DIRECTORY)!r})\n",
            environment,
        )
        tm.that(declaration.read_bytes(), eq=before)
        tm.that(selection.lstat().st_ino, eq=state.st_ino)
        tm.that(selection.readlink(), eq=absent)
        tm.that(absent.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize("kind", ["missing", "dangling-supplier", "file"])
    def test_selected_supplier_retains_native_os_failure(
        tmp_path: Path, kind: str
    ) -> None:
        """Public failure preserves the native errno without changing its inputs."""
        consumer = TestsFlextInfraEditableSupplierInput._consumer(tmp_path)
        supplier = tmp_path / "supplier"
        if kind == "dangling-supplier":
            supplier.symlink_to(tmp_path / "missing", target_is_directory=True)
        elif kind == "file":
            supplier.write_bytes(b"not a directory\n")
        with pytest.raises(
            NotADirectoryError if kind == "file" else FileNotFoundError
        ) as native:
            (
                (supplier / "child").stat()
                if kind == "file"
                else supplier.resolve(strict=True)
            )
        expected_errno = native.value.errno
        tm.that(expected_errno, eq=errno.ENOTDIR if kind == "file" else errno.ENOENT)
        policy = tm.ok(u.Infra.load_codegen_inputs(consumer)).spec.make.uv_resolution
        selection = consumer / policy.supplier_selection_file
        selection.parent.mkdir(parents=True, exist_ok=True)
        payload = f"{supplier}\n".encode()
        selection.write_bytes(payload)
        declaration = consumer / c.PYPROJECT_FILENAME
        before = declaration.read_bytes()
        TestsFlextInfraEditableSupplierInput._run_cold(
            tmp_path,
            "from pathlib import Path\n"
            "from flext_infra import workspace\n"
            f"consumer = Path({str(consumer)!r})\n"
            "result = workspace.FlextInfraWorkspaceDetector."
            "resolution_context(consumer)\n"
            "assert result.failure, result\n"
            "assert isinstance(result.exception, OSError), result.exception\n"
            f"assert result.exception.errno == {expected_errno!r}, result.exception\n"
            "assert result.exception.__traceback__ is not None\n"
            + (
                "assert isinstance(result.exception, NotADirectoryError)\n"
                if kind == "file"
                else "assert isinstance(result.exception, FileNotFoundError)\n"
                "assert str(result.exception.filename) == "
                f"{str(native.value.filename)!r}\n"
            ),
            {policy.hosted_variable: c.ParserBooleanToken.FALSE},
        )
        tm.that(selection.read_bytes(), eq=payload)
        tm.that(declaration.read_bytes(), eq=before)
        if kind == "file":
            tm.that(supplier.read_bytes(), eq=b"not a directory\n")
        elif kind == "dangling-supplier":
            tm.that(supplier.readlink(), eq=tmp_path / "missing")
        else:
            tm.that(supplier.exists(), eq=False)
