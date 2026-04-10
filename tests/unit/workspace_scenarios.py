from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Protocol

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceFactoryLike(Protocol):
    def create_minimal(self, tmp_path: Path, name: str = "test-proj") -> Path: ...

    def create_full(self, tmp_path: Path, name: str) -> Path: ...


class EmptyScenario(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    workspace_name: Annotated[str, Field(default="workspace")]

    def build(self, factory: WorkspaceFactoryLike, tmp_path: Path) -> Path:
        _ = factory
        root = tmp_path / self.workspace_name
        root.mkdir(parents=True, exist_ok=True)
        return root


class MinimalScenario(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    project_name: Annotated[str, Field(default="test-proj")]

    def build(self, factory: WorkspaceFactoryLike, tmp_path: Path) -> Path:
        return factory.create_minimal(tmp_path=tmp_path, name=self.project_name)


class FullScenario(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    project_name: Annotated[str, Field(default="full-proj")]

    def build(self, factory: WorkspaceFactoryLike, tmp_path: Path) -> Path:
        return factory.create_full(tmp_path=tmp_path, name=self.project_name)


class BrokenScenario(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    project_name: Annotated[str, Field(default="broken-proj")]

    def build(self, factory: WorkspaceFactoryLike, tmp_path: Path) -> Path:
        project_root = factory.create_minimal(tmp_path=tmp_path, name=self.project_name)
        (project_root / "Makefile").unlink(missing_ok=True)
        return project_root


__all__ = ["BrokenScenario", "EmptyScenario", "FullScenario", "MinimalScenario"]
