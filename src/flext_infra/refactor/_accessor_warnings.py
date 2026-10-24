"""Declared accessor migration catalog shared by planning and review.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import c, config, m, u

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraAccessorMigrationWarningsMixin:
    """Load the configuration-owned accessor migrations once per request."""

    @staticmethod
    def migration_rules() -> t.SequenceOf[m.Infra.AccessorMigrationRule]:
        """Load and strictly validate the declared accessor migrations.

        Returns:
            The rename and field-normalization rules of the Rope catalog.

        """
        return u.type_adapter(Sequence[m.Infra.AccessorMigrationRule]).validate_python(
            u.Yaml.safe_load(
                (
                    type(config).ssot_config_dir().parent
                    / c.Infra.CODEMOD_ROPE_ACCESSOR_MIGRATIONS_RELPATH
                ).read_text(encoding=c.DEFAULT_ENCODING)
            ),
            strict=True,
        )

    @classmethod
    def automated_rules(cls) -> t.VariadicTuple[m.Infra.AccessorMigrationRule]:
        """Return the declared accessor renames.

        Returns:
            The rename rules of the declared accessor migrations.

        """
        return tuple(
            rule for rule in cls.migration_rules() if rule.operation == "rename"
        )


__all__: list[str] = ["FlextInfraAccessorMigrationWarningsMixin"]
