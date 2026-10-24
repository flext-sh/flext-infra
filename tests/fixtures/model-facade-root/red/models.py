"""Fixture models for the red facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from pydantic import BaseModel


class FixtureModels(BaseModel):
    """Represents the fixture models."""

    class Entry(BaseModel):
        """Represents an entry in the fixture models."""

        label: str


m = FixtureModels

__all__ = ["FixtureModels", "m"]
