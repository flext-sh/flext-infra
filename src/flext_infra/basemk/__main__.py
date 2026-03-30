"""CLI entry point for base.mk generation utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    m,
    t,
    u,
)


def _build_config(project_name: str | None) -> m.Infra.BaseMkConfig | None:
    if project_name is None:
        return None
    return FlextInfraBaseMkTemplateEngine.default_config().model_copy(
        update={"project_name": project_name},
    )


def run(argv: t.StrSequence | None = None) -> int:
    """Run the base.mk CLI command dispatcher."""
    parser = u.Infra.create_parser(
        "basemk",
        "base.mk generation utilities",
        include_apply=False,
        include_diff=False,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate base.mk content from templates",
    )
    _ = generate_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root directory (default: cwd)",
    )
    _ = generate_parser.add_argument(
        "--output",
        type=Path,
        help="Write generated content to file path (defaults to stdout)",
    )
    _ = generate_parser.add_argument(
        "--project-name",
        type=str,
        help="Override project name in generated base.mk",
    )
    args = parser.parse_args(argv)
    if args.command != "generate":
        parser.print_help()
        return 1
    generator = FlextInfraBaseMkGenerator()
    config = _build_config(args.project_name)
    generated_result = generator.generate_basemk(config)
    if generated_result.is_failure:
        return u.Infra.exit_code(
            generated_result,
            failure_msg="base.mk generation failed",
        )
    write_result = generator.write(
        generated_result.value,
        output=args.output,
        stream=sys.stdout,
    )
    return u.Infra.exit_code(write_result, failure_msg="base.mk write failed")


def main(argv: t.StrSequence | None = None) -> int:
    """Run the base.mk CLI entrypoint."""
    return u.Infra.run_cli(run, argv)


if __name__ == "__main__":
    sys.exit(main())
