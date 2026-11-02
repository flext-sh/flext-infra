from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

"""Structural contracts for dependency-analysis collaborators.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""


if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


@runtime_checkable
class FlextInfraProtocolsDeps(Protocol):
    """Dependency-analysis protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class RuntimeDependencyCollector(Protocol):
        """Collect explicit target suppliers for one completed native scan."""

        def __call__(
            self,
            project_root: Path,
            scan: p.Infra.DeptryScan,
            /,
        ) -> p.Result[p.Infra.RuntimeDependencyInputs]:
            """Return the elected lock, supplier metadata and own applicability."""
            ...

    @runtime_checkable
    class TypeCheckerPathRules(Protocol):
        """Path-rule fields every type-checker configuration declares."""

        @property
        def source_dir(self) -> str:
            """Import root the generated search paths order first."""
            ...

        @property
        def project_root(self) -> str:
            """Project-root entry the generated search paths order last."""
            ...

    @runtime_checkable
    class DetectCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def output_format(self) -> str: ...

        @property
        def output(self) -> str | None: ...

        @property
        def quiet(self) -> bool: ...

        @property
        def no_fail(self) -> bool: ...

        @property
        def no_pip_check(self) -> bool: ...

    @runtime_checkable
    class GitSourceReferenceMigration(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url_prefix(self) -> t.NonEmptyStr: ...

        @property
        def source_ref(self) -> t.NonEmptyStr: ...

        @property
        def target_ref(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class PackagedDataSelection(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def files(self) -> t.StrTuple: ...

        @property
        def directories(self) -> t.StrTuple: ...

    @runtime_checkable
    class RuffProjectFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def first_party(self) -> Sequence[str]: ...

        @property
        def analysis_exclusions(self) -> Sequence[str] | None: ...

        @property
        def generated_python_roots(self) -> Sequence[str]: ...

        @property
        def repository_namespace_packages(self) -> t.StrTuple: ...

    @runtime_checkable
    class PyprojectDeclaredTopology(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root_modules(self) -> t.StrTuple: ...

        @property
        def root_packages(self) -> t.StrTuple: ...

        @property
        def repository_namespace_packages(self) -> t.StrTuple: ...

        @property
        def packaged_data_paths(self) -> t.StrTuple: ...

        @property
        def packaged_data_excludes(self) -> t.StrTuple: ...

        @property
        def hatch_build_hook_path(self) -> Path | None: ...

        @property
        def planned_data_files(self) -> t.StrTuple: ...

        @property
        def declared_python_dirs(self) -> t.StrTuple: ...

        @property
        def declared_python_dirs_are_complete(self) -> bool: ...

        @property
        def project_kind(self) -> str | None: ...

        @property
        def analysis_exclusions(self) -> t.StrTuple | None: ...

    @runtime_checkable
    class PyprojectAnalyzerContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def is_root(self) -> bool: ...

        @property
        def repository_root(self) -> Path | None: ...

        @property
        def project_dir(self) -> Path | None: ...

        @property
        def declared_python_dirs(self) -> t.StrTuple: ...

        @property
        def declared_python_dirs_are_complete(self) -> bool: ...


__all__: list[str] = ["FlextInfraProtocolsDeps"]
