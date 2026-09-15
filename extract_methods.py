"""Extract methods from conform.py to a new module file."""
import ast
import pathlib
import re
import sys

SOURCE = "src/flext_infra/codegen/conform.py"


def find_method_lines(source: str, method_names: list[str]) -> dict[str, tuple[int, int]]:
    tree = ast.parse(source)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in method_names:
                result[node.name] = (node.lineno, getattr(node, "end_lineno", node.lineno))
    return result


def extract_group(
    source: str,
    method_names: list[str],
    new_file: str,
    new_class: str,
    new_file_header: str,
) -> tuple[str, str]:
    lines = source.splitlines(keepends=True)
    ranges = find_method_lines(source, method_names)

    if not ranges:
        return source, ""

    sorted_methods = sorted(method_names, key=lambda n: ranges[n][0])

    first_start = ranges[sorted_methods[0]][0]
    last_end = ranges[sorted_methods[-1]][1]

    method_text = "".join(lines[first_start - 1 : last_end])

    re.search(
        r"class\s+\w+\(.*?\):", method_text, re.DOTALL
    )

    body_lines = []
    for name in sorted_methods:
        start, end = ranges[name]
        method_lines = lines[start - 1 : end]
        for line in method_lines:
            if line.startswith("    "):
                body_lines.append(line[4:])
            else:
                body_lines.append(line)

    new_content = new_file_header + "\n\n" + "\n".join(body_lines) + "\n"

    new_content_lines = new_content.splitlines(keepends=True)

    new_lines = []
    for line in new_content_lines:
        if line.startswith(("    ", "\t")) or line.strip() == "":
            new_lines.append("    " + line if line.strip() else line)
        else:
            new_lines.append("    " + line)

    new_content = "".join(new_lines)

    new_lines = [
        l for l in new_content.splitlines(keepends=True) if l.strip() != "    "
    ]
    new_content = "".join(new_lines)

    new_module = f"{new_class}:\n"
    for name in sorted_methods:
        start, end = ranges[name]
        method_lines = lines[start - 1 : end]
        method_text = "".join(method_lines)
        dedented = re.sub(r"^    ", "", method_text, flags=re.MULTILINE)
        new_module += dedented + "\n\n"

    delegation_code = ""
    for name in sorted_methods:
        delegation_code += f"    def {name}(self, *args, **kwargs):\n"
        delegation_code += f"        return {name}(*args, **kwargs)\n\n"

    new_file_content = new_file_header + "\n\n" + new_module + "\n"

    keep_lines = []
    for i, line in enumerate(lines):
        line_no = i + 1
        should_skip = False
        for name in sorted_methods:
            start, end = ranges[name]
            if start <= line_no <= end:
                should_skip = True
                break
        if first_start <= line_no <= last_end and not any(
            start <= line_no <= end for name in sorted_methods for start, end in [ranges[name]]
        ):
            should_skip = False

        if should_skip:
            continue
        keep_lines.append(line)

    modified_source = "".join(keep_lines)

    return modified_source, new_file_content


if __name__ == "__main__":
    action = sys.argv[1]

    if action == "gitignore":
        source = pathlib.Path(SOURCE).read_text(encoding="utf-8")
        methods = ["render_project_gitignore", "_gitignore_sections", "_render_gitignore"]
        modified, new_mod = extract_group(
            source,
            methods,
            "_conform_gitignore.py",
            "FlextInfraCodegenConformGitignoreMixin",
            '"""Gitignore rendering for conformed repositories."""',
        )
        pathlib.Path(SOURCE).write_text(modified, encoding="utf-8")
        pathlib.Path("src/flext_infra/codegen/_conform_gitignore.py").write_text(new_mod, encoding="utf-8")
