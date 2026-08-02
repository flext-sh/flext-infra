"""Domain models for the basemk subpackage."""

from __future__ import annotations

from typing import Annotated, Self

from flext_cli import m, u
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsBasemk:
    """Models for base.mk template rendering."""

    class BaseMkConfig(mm.ProjectNameFieldMixin, m.ArbitraryTypesModel):
        """Configuration model used to render base.mk templates."""

        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Target Python version")
        ]
        source_dir: Annotated[str, m.Field(description="Source directory path")] = (
            c.Infra.DEFAULT_SRC_DIR
        )
        tests_dir: Annotated[str, m.Field(description="Tests directory path")] = (
            c.Infra.DIR_TESTS
        )
        lint_gates: Annotated[
            t.StrSequence, m.Field(description="Enabled quality gates")
        ] = m.Field(default_factory=tuple)
        test_item_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Maximum wall time for one pytest item")
        ]
        test_session_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Maximum wall time for one test session")
        ]
        test_shard_count: Annotated[
            int, m.Field(gt=0, description="Deterministic full-suite shard count")
        ]
        test_shard_parallelism: Annotated[
            int, m.Field(gt=0, description="Concurrent full-suite shard limit")
        ]

        @u.model_validator(mode="after")
        def _validate_shard_parallelism(self) -> Self:
            """Keep bounded parallelism within the declared shard set."""
            if self.test_shard_parallelism > self.test_shard_count:
                msg = "test_shard_parallelism must not exceed test_shard_count"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsBasemk"]
