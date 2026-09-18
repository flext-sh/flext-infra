# from flext-infra_docs/guides/using-flext-cli.md:152
from flext_cli import m


class GreetInput(m.BaseModel):
    name: str


def greet_handler(model: GreetInput) -> str:
    return f"Hello, {model.name}!"


assert greet_handler(GreetInput(name="Ada")) == "Hello, Ada!"
