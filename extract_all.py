"""Automatically extract method groups from conform.py to mixin modules."""
import ast
import pathlib
import re
import sys

CONFORM_PATH = "src/flext_infra/codegen/conform.py"
CODEGEN_DIR = "src/flext_infra/codegen"

# Groups to extract: (filename, class_name, method_names, header_docstring)
GROUPS = [
    (
        "_conform_gitignore.py",
        "FlextInfraCodegenConformGitignoreMixin",
        ["render_project_gitignore", "_gitignore_sections", "_render_gitignore"],
        '"""Gitignore rendering for conformed repositories."""',
    ),
    (
        "_conform_planning.py",
        "FlextInfraCodegenConformPlanningMixin",
        [
            "plan",
            "_complete_governed_plans",
            "_plan_scaffold_repository",
            "_plan_existing_repository",
            "_plan_existing_templates",
            "_plan_existing_custom",
        ],
        '"""Repository planning pipeline for conformed repositories."""',
    ),
    (
        "_conform_rendering.py",
        "FlextInfraCodegenConformRenderingMixin",
        [
            "compose_project_artifact",
            "_rendered_artifact_source",
            "_artifact_render_context",
            "make_render_context",
            "_project_render_context",
        ],
        '"""Artifact rendering and context for conformed repositories."""',
    ),
]


def find_method_ranges(source: str, method_names: list[str]) -> dict[str, tuple[int, int]]:
    tree = ast.parse(source)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in method_names:
                result[node.name] = (node.lineno, getattr(node, "end_lineno", node.lineno))
    return result


def convert_references(text: str, class_name: str) -> str:
    """Convert FlextInfraCodegenConform.method() to self.method()."""
    pattern = re.compile(
        rf"{re.escape(class_name)}\.(\w+)\("
    )
    return pattern.sub(r"self.\1(", text)


def create_mixin_module(
    source: str,
    method_names: list[str],
    class_name: str,
    header: str,
) -> str:
    ranges = find_method_ranges(source, method_names)
    sorted_methods = sorted(method_names, key=lambda n: ranges[n][0])

    lines = source.splitlines(keepends=True)

    module_lines = [header, "", "", f"class {class_name}:", ""]

    for name in sorted_methods:
        start, end = ranges[name]
        method_lines = lines[start - 1 : end]
        method_text = "".join(method_lines)
        method_text = re.sub(r"^    ", "", method_text, flags=re.MULTILINE)
        method_text = convert_references(method_text, "FlextInfraCodegenConform")
        module_lines.append(method_text.rstrip() + "\n\n")

    return "".join(module_lines)


def remove_methods_from_source(
    source: str, method_names: list[str]
) -> tuple[str, list[tuple[int, int]]]:
    ranges = find_method_ranges(source, method_names)
    sorted_methods = sorted(method_names, key=lambda n: ranges[n][0])

    all_ranges = [ranges[name] for name in sorted_methods]

    new_lines = []
    skip_until = 0
    removed_ranges = []

    for i, line in enumerate(source.splitlines(keepends=True)):
        line_no = i + 1
        if line_no <= skip_until:
            continue

        should_skip = False
        for start, end in all_ranges:
            if start <= line_no <= end:
                should_skip = True
                skip_until = end
                removed_ranges.append((start, end))
                break

        if not should_skip:
            new_lines.append(line)

    return "".join(new_lines), removed_ranges


def main() -> None:
    source = pathlib.Path(CONFORM_PATH).read_text(encoding="utf-8")

    len(source.splitlines())

    all_removed = []

    for filename, class_name, method_names, header in GROUPS:

        ranges = find_method_ranges(source, method_names)
        sum(end - start + 1 for start, end in ranges.values())

        module_content = create_mixin_module(source, method_names, class_name, header)
        filepath = f"{CODEGEN_DIR}/{filename}"
        pathlib.Path(filepath).write_text(module_content, encoding="utf-8")

        source, removed = remove_methods_from_source(source, method_names)
        all_removed.extend(removed)

    pathlib.Path(CONFORM_PATH).write_text(source, encoding="utf-8")

    len(source.splitlines())

    # Update class inheritance to include all mixins
    [g[1] for g in GROUPS]

    # Validate syntax
    try:
        ast.parse(source)
    except SyntaxError:
        sys.exit(1)


if __name__ == "__main__":
    main()
