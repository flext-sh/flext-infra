"""Editable receipt, path-file and declared-package validation for provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.metadata import Distribution
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from flext_infra import FlextInfraUtilities, c, m, p, r, t, u
from flext_infra._utilities import FlextInfraUtilitiesDiscovery
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectDocument


class FlextInfraWorkspaceEnvironmentProvenanceEditable(
    FlextInfraUtilities,
):
    """Bind editable receipts and path files to declared package sources."""

    @staticmethod
    def distribution_installation(
        distribution_name: str,
        *,
        metadata_paths: t.StrSequence,
        environment_root: Path,
    ) -> p.Result[t.Triple[Distribution, str, m.Infra.DirectUrlReceipt]]:
        """Authenticate one installed distribution and its native PEP 610 record.

        Returns:
            The distribution, original receipt and validated source declaration.

        """
        result = r[t.Triple[Distribution, str, m.Infra.DirectUrlReceipt]]
        matches = u.installed_distributions(
            name=distribution_name,
            path=metadata_paths,
        )
        if len(matches) != 1:
            return result.fail(
                "member declaration needs one installed distribution: "
                f"{distribution_name}",
            )
        if (
            not Path(str(matches[0].locate_file("")))
            .resolve()
            .is_relative_to(
                environment_root.resolve(),
            )
        ):
            return result.fail(
                "member distribution is outside the owned environment: "
                f"{distribution_name}",
            )
        distribution = matches[0]
        raw = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        if raw is None:
            return result.fail(
                f"member declaration lacks PEP 610 provenance: {distribution_name}",
            )
        receipt = r[m.Infra.DirectUrlReceipt].create_from_callable(
            lambda: m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        return result.ok((distribution, raw, receipt.value))

    @classmethod
    def _validate_direct_url(
        cls,
        distribution: str,
        raw_payload: str | None,
        expected_root: Path,
    ) -> p.Result[int]:
        """Validate one PEP 610 payload against the declared member root.

        Returns:
            The resulting ``p.Result[int]``.

        """
        if raw_payload is None:
            return r[int].fail(
                "editable provenance missing direct_url.json: "
                f"distribution={distribution} expected={expected_root}",
            )
        try:
            payload = m.Infra.DirectUrlReceipt.model_validate_json(
                raw_payload,
                strict=True,
            )
        except ValueError as exc:
            return r[int].fail_op(
                f"editable provenance direct_url validation ({distribution})",
                exc,
            )
        return cls._editable_url_verdict(distribution, payload, expected_root)

    @staticmethod
    def _editable_url_verdict(
        distribution: str,
        payload: m.Infra.DirectUrlReceipt,
        expected_root: Path,
    ) -> p.Result[int]:
        """Bind one parsed editable receipt to its declared physical source.

        Returns:
            The resulting ``p.Result[int]``.

        """
        parsed = urlparse(payload.url)
        if (
            parsed.scheme != "file"
            or payload.dir_info is None
            or not payload.dir_info.editable
            or payload.vcs_info is not None
        ):
            revision = (
                payload.vcs_info.commit_id if payload.vcs_info is not None else None
            )
            return r[int].fail(
                "editable provenance is not an editable file URL: "
                f"distribution={distribution} expected={expected_root} "
                f"url={payload.url} installed_revision={revision}",
            )
        actual_root = Path(url2pathname(unquote(parsed.path))).resolve()
        if actual_root != expected_root:
            return r[int].fail(
                "editable provenance direct_url mismatch: "
                f"distribution={distribution} expected={expected_root} "
                f"actual={actual_root}",
            )
        return r[int].ok(1)

    @classmethod
    def _validate_pth(
        cls,
        distribution: str,
        pth_file: Path,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Validate the distribution-owned editable path file.

        Returns:
            Whether the distribution-owned editable paths are valid.

        """
        read_result = u.Cli.files_read_text(pth_file)
        if read_result.failure:
            return r[bool].from_failure(read_result)
        entries = tuple(
            line.strip()
            for line in read_result.value.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if not entries:
            return r[bool].fail(
                "editable provenance pth is empty: "
                f"distribution={distribution} path={pth_file}",
            )
        declared = cls.editable_declared_packages(distribution, expected_root)
        if declared.failure:
            return r[bool].from_failure(declared)
        exposed: set[t.Pair[str, Path | None]] = set()
        for entry in entries:
            elected = cls._editable_pth_source(
                distribution, entry, expected_root, declared.value
            )
            if elected.failure:
                return r[bool].from_failure(elected)
            exposed.update(elected.value)
        if exposed != set(declared.value):
            return r[bool].fail(
                "editable provenance pth omits declared package sources: "
                f"distribution={distribution}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def editable_declared_packages(
        cls,
        distribution: str,
        expected_root: Path,
    ) -> p.Result[tuple[t.Pair[str, Path | None]], ...]:
        """Elect the same package paths and Hatch source mappings as the producer.

        Returns:
            The complete deduplicated package declarations, including namespace roots.

        """
        result = (r[tuple[t.Pair[str, Path | None]], ...],)
        package_name = u.Infra.project_package_name(expected_root)
        payload = FlextInfraUtilitiesPyprojectDocument.pyproject_payload(
            expected_root / c.PYPROJECT_FILENAME,
        )
        wheel: t.JsonMapping = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            child = u.Cli.toml_mapping_child(wheel, key)
            if child is None:
                wheel = {}
                break
            wheel = child
        declared_paths = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            wheel.get("packages", ()),
            strict=True,
        )
        if declared_paths.failure:
            return result.from_failure(declared_paths)
        primary_parts = tuple(package_name.split("."))
        packages: list[t.Pair[str, Path | None]] = []
        for declared in declared_paths.value:
            relative = Path(declared)
            target = cls._editable_package_path(distribution, expected_root, declared)
            if target.failure:
                return result.from_failure(target)
            name = (
                package_name
                if relative.parts[-len(primary_parts) :] == primary_parts
                else relative.name
            )
            packages.append((name, target.value))
        sources = cls._editable_hatch_sources(distribution, expected_root, wheel)
        if sources.failure:
            return result.from_failure(sources)
        packages.extend(sources.value)
        packages = list(dict.fromkeys(packages))
        if not packages:
            packages.append((package_name, None))
        return result.ok(tuple(packages))

    @staticmethod
    def _editable_package_path(
        distribution: str,
        expected_root: Path,
        declared: str,
    ) -> p.Result[Path]:
        """Require a declared package path to remain live inside its source owner.

        Returns:
            The physical package directory or the original declaration failure.

        """
        relative = Path(declared)
        target = (expected_root / relative).resolve()
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not target.is_relative_to(expected_root)
            or not target.is_dir()
        ):
            return r[Path].fail(
                "editable provenance declared package path is invalid: "
                f"distribution={distribution} package={declared}",
            )
        return r[Path].ok(target)

    @classmethod
    def _editable_hatch_sources(
        cls,
        distribution: str,
        expected_root: Path,
        wheel: t.JsonMapping,
    ) -> p.Result[tuple[t.Pair[str, Path | None]], ...]:
        """Validate every importable Hatch source remapping in declaration order.

        Returns:
            Exact package identities bound to authenticated source directories.

        """
        result = (r[tuple[t.Pair[str, Path | None]], ...],)
        packages: list[t.Pair[str, Path | None]] = []
        source_mapping = u.Cli.toml_mapping_child(wheel, "sources")
        if source_mapping is not None:
            bindings = t.Infra.STR_MAPPING_ADAPTER.validate_python(
                source_mapping, strict=True
            )
            for source, destination in bindings.items():
                destination_path = Path(destination)
                if not destination or not all(
                    part.isidentifier() for part in destination_path.parts
                ):
                    continue
                target = cls._editable_package_path(distribution, expected_root, source)
                if target.failure:
                    return result.from_failure(target)
                packages.append((".".join(destination_path.parts), target.value))
        return result.ok(tuple(packages))

    @classmethod
    def _editable_pth_source(
        cls,
        distribution: str,
        entry: str,
        expected_root: Path,
        packages: t.SequenceOf[t.Pair[str, Path | None]],
    ) -> p.Result[frozenset[t.Pair[str, Path | None]]]:
        """Prove one absolute .pth entry exposes a real declared package owner.

        Returns:
            Every package exposed by this entry, preserving complete coverage checks.

        """
        result = r[frozenset[t.Pair[str, Path | None]]]
        if not Path(entry).is_absolute():
            return result.fail(
                "editable provenance pth entry is not an absolute source path: "
                f"distribution={distribution} entry={entry}",
            )
        actual_source = Path(entry).resolve()
        if not actual_source.is_relative_to(expected_root):
            return result.fail(
                "editable provenance pth mismatch: "
                f"distribution={distribution} expected_root={expected_root} "
                f"actual={actual_source}",
            )
        if not actual_source.is_dir():
            return result.fail(
                "editable provenance source directory is not live: "
                f"distribution={distribution} path={actual_source}",
            )
        elected = frozenset(
            (name, target)
            for name, target in packages
            if (
                (
                    package := FlextInfraUtilitiesDiscovery.declared_package_dir(
                        name,
                        search_paths=(str(actual_source),),
                    )
                )
                is not None
                and package.resolve().is_relative_to(expected_root)
                and (target is None or package.resolve() == target)
            )
        )
        if not elected:
            return result.fail(
                "editable provenance pth exposes no declared package: "
                f"distribution={distribution} path={actual_source}",
            )
        return result.ok(elected)


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentProvenanceEditable"]
