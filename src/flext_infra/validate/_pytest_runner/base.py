"""Validated environment and filesystem boundary for pytest execution."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Self

from flext_infra import c, m, u
from flext_infra.base import s

type PytestPolicy = m.Infra.PytestConfig


class FlextInfraPytestRunnerBase(s[int]):
    """Own immutable inputs shared by all pytest runner phases."""

    started_at_monotonic: Annotated[
        float, m.Field(gt=0, description="Clock captured before FLEXT imports.")
    ]
    target: Annotated[Path, m.Field(description="Repository-relative test root.")]
    reports: Annotated[Path, m.Field(description="Repository-relative report root.")]
    testmon_db: Annotated[Path, m.Field(description="External persistent testmon DB.")]

    @staticmethod
    def _environment_value(name: str) -> str:
        """Read one Make-owned runner input."""
        return u.Cli.env_read(name, dict(os.environ)).unwrap().strip()

    @classmethod
    def from_environment(cls, *, started_at_monotonic: float) -> Self:
        """Create the runner exclusively from generated Make inputs."""
        return cls(
            repository_root=Path.cwd(),
            started_at_monotonic=started_at_monotonic,
            target=Path(cls._environment_value(c.Infra.PYTEST_ENV_TARGET)),
            reports=Path(cls._environment_value(c.Infra.PYTEST_ENV_REPORTS)),
            testmon_db=Path(
                cls._environment_value(c.Infra.PYTEST_ENV_TESTMON_DATAFILE)
            ),
        )

    @u.model_validator(mode="after")
    def _validate_paths(self) -> Self:
        """Require contained inputs and an external absolute cache path."""
        for name, path in (("target", self.target), ("reports", self.reports)):
            raw = str(path)
            if (
                path.is_absolute()
                or not path.parts
                or any(part in {"", ".", ".."} for part in path.parts)
                or any(character in raw for character in "\0\r\n\\")
            ):
                msg = f"{name} must be a normalized repository-relative path"
                raise ValueError(msg)
            resolved = (self.root / path).resolve()
            if not resolved.is_relative_to(self.root.resolve()):
                msg = f"{name} escapes the repository"
                raise ValueError(msg)
        target_path = self.root / self.target
        if not target_path.is_dir() or target_path.is_symlink():
            msg = f"test target must be an existing directory: {self.target}"
            raise ValueError(msg)
        if not self.testmon_db.is_absolute():
            msg = "TESTMON_DATAFILE must be absolute"
            raise ValueError(msg)
        if self.testmon_db.resolve().is_relative_to(self.root.resolve()):
            msg = "TESTMON_DATAFILE must be outside the repository checkout"
            raise ValueError(msg)
        return self

    @staticmethod
    def _memory_gb() -> int:
        """Read physical memory from the operating-system owner."""
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        if page_size <= 0 or pages <= 0:
            msg = "physical memory capacity is unavailable"
            raise ValueError(msg)
        memory_gb = (page_size * pages) // (1024**3)
        if memory_gb <= 0:
            msg = "physical memory is below one GiB"
            raise ValueError(msg)
        return memory_gb

    def parallel_worker_budget(self, policy: PytestPolicy) -> int:
        """Bound xdist by configuration, CPU, and physical memory."""
        cpu_count = os.cpu_count()
        if cpu_count is None or cpu_count <= 0:
            msg = "CPU capacity is unavailable"
            raise ValueError(msg)
        memory_workers = self._memory_gb() // policy.parallel_worker_memory_gb
        if memory_workers <= 0:
            msg = "physical memory cannot support one pytest worker"
            raise ValueError(msg)
        return min(policy.parallel_workers, cpu_count, memory_workers)

    def _report_directory(self) -> Path:
        """Create a collision-resistant report directory."""
        run_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S.%fZ") + f"-{os.getpid()}"
        report_dir: Path = self.root / self.reports / run_id
        u.Cli.ensure_dir(report_dir).unwrap()
        return report_dir


__all__: list[str] = ["FlextInfraPytestRunnerBase"]
