# from flext-infra/docs/guides/using-flext-cli.md:112
from flext_cli import FlextCliCli, m


class GreetInput(m.BaseModel):
    name: str


def greet_handler(model: GreetInput) -> str:
    return f"Hello, {model.name}!"


def test_greet_command() -> None:
    cli = FlextCliCli()
    app = cli.create_app_with_common_params(
        name="greeting", help_text="Greeting commands"
    )
    command = cli.model_command(model_cls=GreetInput, handler=greet_handler)
    cli.register_command(
        app, name="greet", help_text="Build a greeting", command=command
    )
    invocation = cli.invoke_app(app, args=["greet", "--name", "Ada"])
    assert invocation.success
    assert invocation.value.exit_code == 0
    assert greet_handler(GreetInput(name="Ada")) == "Hello, Ada!"
