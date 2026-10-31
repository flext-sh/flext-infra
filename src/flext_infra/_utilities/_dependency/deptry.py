"""Native deptry capture authenticated against an unchanged production tree.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path, PurePosixPath

from flext_cli import u

from flext_infra import c, m, p, r, t


class FlextInfraUtilitiesDependencyDeptry:
    """Run native deptry once and authenticate every state it consumed."""

    @classmethod
    def capture_deptry_scan(
        cls,
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[m.Infra.DeptryScan]:
        """Capture one native deptry report against unchanged production trees.

        Callers elect the interpreter, configuration and fresh report destination;
        the wheel target the configuration declares elects the scanned roots.

        Returns:
            Complete native findings and the states authenticating their inputs.

        """
        result_type = r[m.Infra.DeptryScan]
        payload = cls._captured_deptry_inputs(
            project_path,
            config_path=config_path,
        )
        if payload.failure:
            return result_type.from_failure(payload)
        settings, roots, sources = payload.value
        native = cls._captured_deptry_native(
            venv_bin,
            project_path,
            roots=roots,
            config_path=config_path,
            json_output_path=json_output_path,
        )
        if native.failure:
            return result_type.from_failure(native)
        output, report_state, parsed = native.value
        rechecked = cls._rechecked_deptry_states(
            settings,
            report_state,
            sources,
        )
        if rechecked.failure:
            return result_type.from_failure(rechecked)
        coverage = cls._validated_deptry_coverage(
            output,
            parsed,
            roots,
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
                source=sources,
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
        roots: t.StrTuple,
    ) -> p.Result[int]:
        """Authenticate the native exit status and its scan coverage line.

        Native deptry reports one coverage count over every root it scanned.

        Returns:
            The single positive coverage count reported by native deptry.

        """
        result_type = r[int]
        if output.outcome.raw_return_code != int(bool(parsed.root)):
            return result_type.fail("deptry exit status contradicts its native report")
        coverage = tuple(
            int(match.group(c.Aggregation.COUNT))
            for line in (*output.stdout.splitlines(), *output.stderr.splitlines())
            if (match := c.Infra.DEPTRY_SCAN_COVERAGE_RE.fullmatch(line)) is not None
        )
        if len(coverage) != 1 or coverage[0] < 1:
            return result_type.fail(
                "deptry lacks positive unambiguous native scan coverage over roots "
                f"{', '.join(roots)}\n"
                f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}",
            )
        return result_type.ok(coverage[0])

    @staticmethod
    def _declared_wheel_target(
        settings: m.Cli.AtomicFileState,
    ) -> p.Result[t.JsonMapping]:
        """Read the wheel target table from the captured settings bytes.

        Returns:
            The declared wheel target, empty when the settings declare none.

        """
        result_type = r[t.JsonMapping]
        if settings.content is None:
            return result_type.fail(f"deptry configuration is absent: {settings.path}")
        document = u.Cli.toml_parse_text(settings.content.decode(c.DEFAULT_ENCODING))
        if document is None:
            return result_type.fail(f"invalid deptry configuration: {settings.path}")
        wheel: t.JsonMapping | None = u.Cli.toml_as_mapping(document)
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            wheel = None if wheel is None else u.Cli.toml_mapping_child(wheel, key)
        return result_type.ok(dict[str, t.JsonValue]() if wheel is None else wheel)

    @staticmethod
    def _shipped_import_base(
        shipped: PurePosixPath,
        target: PurePosixPath,
    ) -> PurePosixPath:
        """Return the directory whose children a shipped directory's imports are.

        A source remapped to its own trailing components (``src/pkg`` shipped as
        ``pkg``) roots at the remaining prefix; a directory shipped verbatim or
        relocated under the package roots at itself.

        Returns:
            The deptry root covering exactly the shipped directory.

        """
        cut = len(shipped.parts) - len(target.parts)
        if cut > 0 and shipped.parts[cut:] == target.parts:
            return PurePosixPath(*shipped.parts[:cut])
        return shipped

    @classmethod
    def _declared_deptry_roots(
        cls,
        settings: m.Cli.AtomicFileState,
    ) -> p.Result[t.StrTuple]:
        """Elect deptry's roots from the wheel target the settings declare.

        Every directory the wheel ships — through its ``packages`` entries, its
        ``only-include`` entries, or its ``sources`` prefixes — contributes its
        import base; a root nested in another root is already covered. Hatch
        ships a ``packages`` entry at its trailing components (``src/pkg`` lands
        as ``pkg``), so a flat entry roots at itself and a ``src/``-prefixed one
        at its remaining prefix. A wheel target declaring none of the three
        keeps the native src layout root.

        Returns:
            The sorted roots, or the first declaration failure.

        """
        result_type = r[t.StrTuple]
        wheel = cls._declared_wheel_target(settings)
        if wheel.failure:
            return result_type.from_failure(wheel)
        shipped: p.Result[Sequence[str]] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            wheel.value.get("only-include", ()),
            strict=True,
        )
        if shipped.failure:
            return result_type.from_failure(shipped)
        sources: p.Result[Mapping[str, str]] = u.validate_value(
            t.Infra.STR_MAPPING_ADAPTER,
            wheel.value.get("sources", dict[str, str]()),
            strict=True,
        )
        if sources.failure:
            return result_type.from_failure(sources)
        packages: p.Result[Sequence[str]] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            wheel.value.get("packages", ()),
            strict=True,
        )
        if packages.failure:
            return result_type.from_failure(packages)
        roots: set[PurePosixPath] = set()
        for declaration in packages.value:
            path = PurePosixPath(declaration)
            if path.is_absolute() or not path.parts or ".." in path.parts:
                return result_type.fail(
                    "deptry root is outside the declared wheel boundary: "
                    f"{declaration!r} in {settings.path}",
                )
            roots.add(
                cls._shipped_import_base(path, PurePosixPath(path.parts[-1])),
            )
        for declaration in (*shipped.value, *sources.value):
            path = PurePosixPath(declaration)
            if path.is_absolute() or not path.parts or ".." in path.parts:
                return result_type.fail(
                    "deptry root is outside the declared wheel boundary: "
                    f"{declaration!r} in {settings.path}",
                )
            roots.add(
                cls._shipped_import_base(
                    path,
                    PurePosixPath(sources.value.get(declaration, declaration)),
                ),
            )
        return result_type.ok(
            tuple(
                sorted(
                    root.as_posix()
                    for root in roots
                    if not any(
                        root != other and root.is_relative_to(other) for other in roots
                    )
                )
            )
            or (c.Infra.DEFAULT_SRC_DIR,),
        )

    @staticmethod
    def _authenticated_deptry_sources(
        project_path: Path,
        roots: t.StrTuple,
    ) -> p.Result[tuple[m.Cli.AtomicPhysicalTreeManifest, ...]]:
        """Inventory every production root and authenticate its physical shape.

        Returns:
            One exact tree manifest per root, or the first authentication failure.

        """
        result_type = r[tuple[m.Cli.AtomicPhysicalTreeManifest, ...]]
        manifests: list[m.Cli.AtomicPhysicalTreeManifest] = []
        for root in roots:
            source = u.Cli.atomic_inventory_physical_tree(project_path / root)
            if source.failure:
                return result_type.from_failure(source)
            if any(entry.kind == "symlink" for entry in source.value.entries):
                return result_type.fail(
                    "deptry production source contains unauthenticated symbolic "
                    f"links: {source.value.root.path}"
                )
            manifests.append(source.value)
        return result_type.ok(tuple(manifests))

    @staticmethod
    def _verified_deptry_sources(
        sources: Sequence[m.Cli.AtomicPhysicalTreeManifest],
        *,
        moment: str,
    ) -> p.Result[bool]:
        """Re-inventory every production root against its captured manifest.

        Returns:
            Whether every root survived unchanged, or the first changed root.

        """
        result_type = r[bool]
        for source in sources:
            current = u.Cli.atomic_inventory_physical_tree(source.root.path)
            if current.failure:
                return result_type.from_failure(current)
            if current.value != source:
                return result_type.fail(
                    f"deptry production source changed {moment}: {source.root.path}"
                )
        return result_type.ok(value=True)

    @classmethod
    def _captured_deptry_inputs(
        cls,
        project_path: Path,
        *,
        config_path: Path,
    ) -> p.Result[
        tuple[
            m.Cli.AtomicFileState,
            t.StrTuple,
            tuple[m.Cli.AtomicPhysicalTreeManifest, ...],
        ]
    ]:
        """Read the deptry configuration and authenticate its declared roots.

        Returns:
            The configuration state, its roots and their authenticated manifests.

        """
        result_type = r[
            tuple[
                m.Cli.AtomicFileState,
                t.StrTuple,
                tuple[m.Cli.AtomicPhysicalTreeManifest, ...],
            ]
        ]
        settings = u.Cli.atomic_read_binary_file_state(config_path, required=True)
        if settings.failure:
            return result_type.from_failure(settings)
        roots = cls._declared_deptry_roots(settings.value)
        if roots.failure:
            return result_type.from_failure(roots)
        sources = cls._authenticated_deptry_sources(
            project_path,
            roots.value,
        )
        if sources.failure:
            return result_type.from_failure(sources)
        return result_type.ok((settings.value, roots.value, sources.value))

    @staticmethod
    def _run_deptry(
        venv_bin: Path,
        project_path: Path,
        *,
        roots: t.StrTuple,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[m.Cli.CommandOutput]:
        """Run native deptry once over the elected roots into a fresh report.

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
                "--config",
                str(config_path),
                "--json-output",
                str(json_output_path),
                "--no-ansi",
                "--",
                *roots,
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
    ) -> p.Result[tuple[m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]]:
        """Read and strictly parse the fresh native deptry report.

        Returns:
            The report file state and its validated native payload.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]]
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

    @classmethod
    def _captured_deptry_native(
        cls,
        venv_bin: Path,
        project_path: Path,
        *,
        roots: t.StrTuple,
        config_path: Path,
        json_output_path: Path,
    ) -> p.Result[
        tuple[m.Cli.CommandOutput, m.Cli.AtomicFileState, m.Infra.DeptryNativeReport]
    ]:
        """Run deptry once and strictly parse its fresh native report.

        Returns:
            The validated command output, report state, and native report.

        """
        result_type = r[
            tuple[
                m.Cli.CommandOutput,
                m.Cli.AtomicFileState,
                m.Infra.DeptryNativeReport,
            ]
        ]
        native = cls._run_deptry(
            venv_bin,
            project_path,
            roots=roots,
            config_path=config_path,
            json_output_path=json_output_path,
        )
        if native.failure:
            return result_type.from_failure(native)
        report = cls._parsed_deptry_report(
            json_output_path,
        )
        if report.failure:
            return result_type.from_failure(report)
        report_state, parsed = report.value
        return result_type.ok((native.value, report_state, parsed))

    @classmethod
    def _rechecked_deptry_states(
        cls,
        settings: m.Cli.AtomicFileState,
        report_state: m.Cli.AtomicFileState,
        sources: Sequence[m.Cli.AtomicPhysicalTreeManifest],
    ) -> p.Result[bool]:
        """Re-verify the captured states and the unchanged production trees.

        Returns:
            Whether every captured state survived the scan unchanged.

        """
        verified = u.Cli.atomic_verify_binary_file_states((settings, report_state))
        if verified.failure:
            return r[bool].from_failure(verified)
        return cls._verified_deptry_sources(
            sources,
            moment="during scanning",
        )


__all__: list[str] = ["FlextInfraUtilitiesDependencyDeptry"]
