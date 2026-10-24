from pydantic import BaseModel


class FixtureModels(BaseModel):
    class Entry(BaseModel):
        label: str


m = FixtureModels

__all__ = ["FixtureModels", "m"]
