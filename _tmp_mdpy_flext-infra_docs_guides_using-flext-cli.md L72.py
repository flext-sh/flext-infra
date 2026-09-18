# from flext-infra/docs/guides/using-flext-cli.md:72
from __future__ import annotations

from flext_cli import FlextCliCli, FlextCliSettings, m, t

settings = FlextCliSettings.fetch_global()


class GreetInput(m.BaseModel):
    name: str
    shout: bool = False


def greet_handler(model: GreetInput) -> t.JsonValue:
    message = f"Hello, {model.name}!"
    if model.shout:
        message = message.upper()
    return {"message": message}


command = FlextCliCli.model_command(
    model_cls=GreetInput, handler=greet_handler, settings=settings
)
cli = FlextCliCli()
app = cli.create_app_with_common_params(name="greeting", help_text="Greeting commands")
cli.register_command(app, name="greet", help_text="Build a greeting", command=command)
