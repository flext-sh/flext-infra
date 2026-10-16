"""Native deptry capture authenticated against an unchanged production tree.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r, t


class FlextInfraUtilitiesDependencyDeptryMixin:
    """Run native deptry once and authenticate every state it consumed."""

    @staticmethod
    def capture_deptry_scan(
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[m.Infra.DeptryScan]:
        """Capture one native deptry report against an unchanged production tree.

        Callers elect the interpreter, configuration and fresh report destination.

        Returns:
            Complete native findings and the states authenticating their inputs.

        """
        result_type = r[m.Infra.DeptryScan]
        payload = FlextInfraUtilitiesDependencyDeptryMixin._captured_deptry_inputs(
            project_path,
            config_path=config_path,
        )
        if payload.failure:
            return result_type.from_failure(payload)
        settings, source = payload.value
        native = FlextInfraUtilitiesDependencyDeptryMixin._captured_deptry_native(
            venv_bin,
            project_path,
            config_path=config_path,
            json_output_path=json_output_path,
        )
        if native.failure:
            return result_type.from_failure(native)
        output, report_state, parsed = native.value
        rechecked = FlextInfraUtilitiesDependencyDeptryMixin._rechecked_deptry_states(
            settings,
            report_state,
            source,
        )
        if rechecked.failure:
            return result_type.from_failure(rechecked)
        coverage = FlextInfraUtilitiesDependencyDeptryMixin._validated_deptry_coverage(
            output,
            parsed,
        )
        if coverage.failure:
            return result_type.from_failure(coverage)
        if report_state.content is None:
            return result_type.fail(
                "deptry report state has no captured bytes to authenticate",
            )
        return result_type.ok(
            m.Infra.DeptryScan(
                scanned_files=coverage.value,
                venv_bin=venv_bin,
                source=source,
                native=output,
                settings=settings,
                report_state=report_state,
                report_sha256=u.Cli.sha256_bytes(report_state.content),
                report=parsed,
            )
        )

    @staticmethod
    def _validated_deptry_coverage(
        output: m.Cli.CommandOutput,
        parsed: m.Infra.DeptryNativeReport,
    ) -> p.Result[int]:
        """Authenticate the native exit status and its scan coverage line.

        Returns:
            The single positive coverage count reported by native deptry.

        """
        result_type = r[int]
        if output.outcome.raw_return_code != int(bool(parsed.root)):
            return result_type.fail("deptry exit status contradicts its native report")
        coverage = tuple(
            int(match.group("count"))
            for line in (*output.stdout.splitlines(), *output.stderr.splitlines())
            if (match := c.Infra.DEPTRY_SCAN_COVERAGE_RE.fullmatch(line)) is not None
        )
        if len(coverage) != 1 or coverage[0] < 1:
            return result_type.fail(
                "deptry lacks positive unambiguous native scan coverage\n"
                f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}",
            )
        return result_type.ok(coverage[0])

    @staticmethod
    def _authenticated_deptry_source(
        project_path: Path,
    ) -> p.Result[m.Cli.AtomicPhysicalTreeManifest]:
        """Inventory the production tree and authenticate its physical shape.

        Returns:
            The exact tree manifest, or the first authentication failure.

        """
        result_type = r[m.Cli.AtomicPhysicalTreeManifest]
        source = u.Cli.atomic_inventory_physical_tree(
            project_path / c.Infra.DEFAULT_SRC_DIR,
        )
        if source.failure:
            return result_type.from_failure(source)
        if any(entry.kind == "symlink" for entry in source.value.entries):
            return result_type.fail(
                "deptry production source contains unauthenticated symbolic links"
            )
        return result_type.ok(source.value)

    @staticmethod
    def _captured_deptry_inputs(
        project_path: Path,
        *,
        config_path: Path,
    ) -> p.Result[t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicPhysicalTreeManifest]]:
        """Read the deptry configuration and authenticate the production tree.

        Returns:
            The configuration state and the authenticated source manifest.

        """
        result_type = r[t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicPhysicalTreeManifest]]
        settings = u.Cli.atomic_read_binary_file_state(config_path, required=True)
        if settings.failure:
            return result_type.from_failure(settings)
        source = FlextInfraUtilitiesDependencyDeptryMixin._authenticated_deptry_source(
            project_path,
        )
        if source.failure:
            return result_type.from_failure(source)
        return result_type.ok((settings.value, source.value))

    @staticmethod
    def _run_deptry(
        venv_bin: Path,
        project_path: Path,
        *,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[m.Cli.CommandOutput]:
        """Run native deptry once against a fresh report destination.

        Returns:
            The validated native command output, or the first execution failure.

        """
        result_type = r[m.Cli.CommandOutput]
        before = u.Cli.atomic_read_binary_file_state(json_output_path, required=False)
        if before.failure:
            return result_type.from_failure(before)
        if before.value.content is not None:
            return result_type.fail(
                f"deptry report destination already exists: {json_output_path}"
            )
        completed = u.Cli.run_raw(
            (
                str(venv_bin / c.Infra.DEPTRY),
                c.Infra.DEFAULT_SRC_DIR,
                "--config",
                str(config_path),
                "--json-output",
                str(json_output_path),
                "--no-ansi",
            ),
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if completed.failure:
            return result_type.from_failure(completed)
        native = m.Cli.CommandOutput.model_validate(
            completed.value, from_attributes=True
        )
        if (
            native.outcome.timed_out
            or native.outcome.forwarded_signal is not None
            or native.outcome.raw_return_code not in {0, 1}
        ):
            return result_type.fail(
                f"deptry process failed: {native.outcome.model_dump_json()}\n"
                f"stdout:\n{native.stdout}\nstderr:\n{native.stderr}",
            )
        return result_type.ok(native)

    @staticmethod
    def _parsed_deptry_report(
        json_output_path: Path,
    ) -> p.Result[t.Pair[m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]]:
        """Read and strictly parse the fresh native deptry report.

        Returns:
            The report file state and its validated native payload.

        """
        result_type = r[t.Pair[m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]]
        report_state = u.Cli.atomic_read_binary_file_state(
            json_output_path, required=True
        )
        if report_state.failure:
            return result_type.from_failure(report_state)
        if report_state.value.content is None:
            return result_type.fail(
                f"deptry did not produce its native report: {json_output_path}"
            )
        parsed = r[m.Infra.DeptryNativeReport].create_from_callable(
            partial(
                m.Infra.DeptryNativeReport.model_validate_json,
                report_state.value.content,
                strict=True,
            ),
        )
        if parsed.failure:
            return result_type.from_failure(parsed)
        return result_type.ok((report_state.value, parsed.value))

    @staticmethod
    def _captured_deptry_native(
        venv_bin: Path,
        project_path: Path,
        *,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[
        t.Triple[m.Cli.CommandOutput, m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]
    ]:
        """Run deptry once and strictly parse its fresh native report.

        Returns:
            The validated command output, report state, and native report.

        """
        result_type = r[
            t.Triple[
                m.Cli.CommandOutput,
                m.Cli.AtomicFileState,
                m.Infra.DeptryNativeReport,
            ]
        ]
        native = FlextInfraUtilitiesDependencyDeptryMixin._run_deptry(
            venv_bin,
            project_path,
            config_path=config_path,
            json_output_path=json_output_path,
        )
        if native.failure:
            return result_type.from_failure(native)
        report = FlextInfraUtilitiesDependencyDeptryMixin._parsed_deptry_report(
            json_output_path,
        )
        if report.failure:
            return result_type.from_failure(report)
        report_state, parsed = report.value
        return result_type.ok((native.value, report_state, parsed))

    @staticmethod
    def _rechecked_deptry_states(
        settings: m.Cli.AtomicFileState,
        report_state: m.Cli.AtomicFileState,
        source: m.Cli.AtomicPhysicalTreeManifest,
    ) -> p.Result[bool]:
        """Re-verify the captured states and the unchanged production tree.

        Returns:
            Whether every captured state survived the scan unchanged.

        """
        result_type = r[bool]
        verified = u.Cli.atomic_verify_binary_file_states((settings, report_state))
        if verified.failure:
            return result_type.from_failure(verified)
        current_source = u.Cli.atomic_inventory_physical_tree(source.root.path)
        if current_source.failure:
            return result_type.from_failure(current_source)
        if current_source.value != source:
            return result_type.fail(
                f"deptry production source changed during scanning: {source.root.path}"
            )
        return result_type.ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesDependencyDeptryMixin"]
