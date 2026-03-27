"""CST protocols — accessed via p.Infra.Cst.*."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_core import r

from flext_infra import m


class FlextInfraProtocolsCst:
    """Structural contracts for CST-based analysis — accessed via p.Infra.Cst.*."""

    class Cst:
        """CST-specific protocols."""

        @runtime_checkable
        class FileExtractor(Protocol):
            """Contract for CST-based file object extractors.

            Implementations parse a single Python file and return
            extracted objects without cross-file resolution.
            """

            def extract(
                self,
                file_path: Path,
                project_name: str,
            ) -> r[m.Infra.Cst.FileResult]:
                """Extract all objects from a single Python file.

                Args:
                    file_path: Absolute path to the Python file.
                    project_name: Name of the containing project.

                Returns:
                    Result containing extracted objects or failure.

                """
                ...

        @runtime_checkable
        class ObjectClassifier(Protocol):
            """Contract for object kind classification.

            Implementations determine the expected tier (constant/type/
            protocol/model/utility) for an extracted object based on its
            structural characteristics.
            """

            def classify(
                self,
                obj: m.Infra.Cst.ExtractedObject,
            ) -> str:
                """Return the expected object kind string.

                Args:
                    obj: The extracted object to classify.

                Returns:
                    Object kind string matching c.Infra.CensusObjectKind values.

                """
                ...

        @runtime_checkable
        class WorkspaceScanner(Protocol):
            """Contract for workspace-wide CST scanning."""

            def scan(
                self,
                workspace_root: Path,
                *,
                project_names: Sequence[str] | None = None,
            ) -> r[Sequence[m.Infra.Cst.FileResult]]:
                """Scan workspace and return extraction results per file.

                Args:
                    workspace_root: Root of the workspace.
                    project_names: Optional filter for specific projects.

                Returns:
                    Result containing file results or failure.

                """
                ...


__all__ = ["FlextInfraProtocolsCst"]
