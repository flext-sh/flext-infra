from pydantic import BaseModel


class FixtureModels:
    class Entry(BaseModel):
        label: str


m = FixtureModels

__all__ = ["FixtureModels", "m"]
