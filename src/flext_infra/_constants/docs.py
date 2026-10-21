"""Centralized constants for the docs subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsDocs:
    """Docs infrastructure constants."""

    class DocumentationText(Enum):
        """Finite presentation messages, English baseline and Brazilian Portuguese."""

        DOCUMENTATION = ("Documentation", "Documentação")
        VERSION = ("Version", "Versão")
        PROJECT_CLASS = ("Project class", "Classe do projeto")
        PACKAGE = ("Package", "Pacote")
        DESCRIPTION = ("Description", "Descrição")
        UNKNOWN = ("unknown", "desconhecida")
        NOT_DECLARED = ("_not declared_", "_não declarado_")
        NONE = ("_none_", "_nenhum_")
        MORE = ("more", "a mais")
        COLLECTION_RULES = ("Collection Rules", "Regras da coleção")
        COLLECTION_BODY = (
            (
                "Read [`/flext/AGENTS.md`]({agents_link}) and this project's "
                "`AGENTS.md` for the current authority chain, execution "
                "boundaries and required validation."
            ),
            (
                "Leia [`/flext/AGENTS.md`]({agents_link}) e o `AGENTS.md` deste "
                "projeto para conhecer a cadeia de autoridade atual, os limites "
                "de execução e a validação exigida."
            ),
        )
        QUALITY_GATES = ("Quality Gates", "Verificações de qualidade")
        QUALITY_BODY = (
            (
                "Canonical `make` verbs (`gen`, `check`, `test`, `fmt`, "
                "`docs`) execute their declared operations directly."
            ),
            (
                "Os verbos canônicos do `make` (`gen`, `check`, `test`, `fmt`, "
                "`docs`) executam diretamente as operações declaradas."
            ),
        )
        QUALITY_LINK = (
            (
                "See [`/flext/AGENTS.md`]({agents_link}) for the build, test, "
                "and Python quality gates."
            ),
            (
                "Consulte [`/flext/AGENTS.md`]({agents_link}) para as verificações "
                "de compilação, testes e qualidade de Python."
            ),
        )
        GOVERNANCE = ("Governance Pointer", "Referências de governança")
        ENGINEERING_LAW = ("Engineering law", "Regras de engenharia")
        GOVERNANCE_ADRS = ("Governance + ADRs", "Governança e ADRs")
        SKILLS_INDEX = ("Skills index", "Índice de habilidades")
        ONBOARDING = ("Onboarding", "Integração inicial")
        PORTAL_BODY = (
            (
                "This project portal is generated from `pyproject.toml`, "
                "package exports, and real docstrings."
            ),
            (
                "Este portal do projeto é gerado a partir de `pyproject.toml`, "
                "das exportações do pacote e das docstrings reais."
            ),
        )
        START_HERE = ("Start Here", "Comece aqui")
        GUIDES = ("Guides", "Guias")
        API_REFERENCE = ("API Reference", "Referência da API")
        GENERATED_OVERVIEW = ("Generated API Overview", "Visão geral gerada da API")
        GENERATED_MODULE_INDEX = ("Generated Module Index", "Índice gerado de módulos")
        PUBLIC_SURFACE_SUMMARY = (
            "Public Surface Summary",
            "Resumo da interface pública",
        )
        README_METADATA = (
            (
                "**Version**: `{version}` | **Python**: see `pyproject.toml` "
                "`requires-python` | **Project class**: `{project_class}`"
            ),
            (
                "**Versão**: `{version}` | **Python**: consulte `requires-python` "
                "em `pyproject.toml` | **Classe do projeto**: `{project_class}`"
            ),
        )
        ALPHA_NOTE = (
            (
                "> **Alpha (0.12.0).** This package is alpha quality. Every "
                "package in the workspace must be re-checked and re-validated "
                "at 0.12.0 before any promotion beyond alpha; treat interfaces "
                "as unstable."
            ),
            (
                "> **Alfa (0.12.0).** Este pacote está em estágio alfa. Cada "
                "pacote do workspace deve ser verificado e validado novamente "
                "na versão 0.12.0 antes de qualquer promoção além de alfa; "
                "considere as interfaces instáveis."
            ),
        )
        PURPOSE = ("Purpose", "Finalidade")
        MODULE_MAP = ("Module Map", "Mapa de módulos")
        OPERATION_FLOW = ("Operation Flow", "Fluxo de operação")
        PUBLIC_SURFACE_LINK = (
            (
                "- Public surface: see [`docs/index.md`](docs/index.md) and "
                "[`docs/api-reference/README.md`](docs/api-reference/README.md)."
            ),
            (
                "- Interface pública: consulte [`docs/index.md`](docs/index.md) e "
                "[`docs/api-reference/README.md`](docs/api-reference/README.md)."
            ),
        )
        GENERATED_MODULE_LINK = (
            (
                "- Generated module overview: "
                "[`docs/api-reference/generated/overview.md`]"
                "(docs/api-reference/generated/overview.md)."
            ),
            (
                "- Visão geral gerada dos módulos: "
                "[`docs/api-reference/generated/overview.md`]"
                "(docs/api-reference/generated/overview.md)."
            ),
        )
        SETTINGS_PREFIX = (
            (
                "- Settings env prefix: see project `pyproject.toml` "
                "`[tool.flext]` and `FlextSettings` ConfigDict."
            ),
            (
                "- Prefixo das variáveis de ambiente: consulte `[tool.flext]` no "
                "`pyproject.toml` do projeto e o ConfigDict de `FlextSettings`."
            ),
        )
        INTEGRATION_POINTS = ("Integration Points", "Pontos de integração")
        PARENT_CHAIN = (
            (
                "- Parent FLEXT chain: read this project's `pyproject.toml` "
                "`dependencies` array filtered by `flext-*`. The FLEXT cascade "
                "is encoded in the inheritance lists of the facade classes "
                "listed under Module Map above."
            ),
            (
                "- Cadeia de dependências FLEXT: leia a lista `dependencies` do "
                "`pyproject.toml` deste projeto, filtrando por `flext-*`. A cascata "
                "FLEXT está codificada nas listas de herança das classes de "
                "fachada relacionadas no Mapa de módulos acima."
            ),
        )
        PUBLIC_EXTENSIONS = (
            "- Public extensions exposed by this project: {facades}.",
            "- Extensões públicas expostas por este projeto: {facades}.",
        )
        LIBRARY_BOUNDARIES = (
            (
                "- Library abstraction boundaries: see the project `AGENTS.md` "
                "and the referenced parent architecture rules."
            ),
            (
                "- Limites de abstração da biblioteca: consulte o `AGENTS.md` do "
                "projeto e as regras de arquitetura do proprietário referenciadas "
                "nele."
            ),
        )
        FULL_PORTAL = (
            "- Full project portal: [`docs/index.md`](docs/index.md).",
            "- Portal completo do projeto: [`docs/index.md`](docs/index.md).",
        )
        GUIDES_BODY = (
            (
                "Curated operational guides live here. Keep API behavior in "
                "generated reference pages sourced from code and docstrings."
            ),
            (
                "Os guias operacionais mantidos ficam aqui. Mantenha o "
                "comportamento da API nas páginas de referência geradas a partir "
                "do código e das docstrings."
            ),
        )
        BACK_TO_DOCS = ("Back to project docs", "Voltar à documentação do projeto")
        API_BODY = (
            "This section is generated from public exports and real docstrings.",
            (
                "Esta seção é gerada a partir das exportações públicas e das "
                "docstrings reais."
            ),
        )
        SOURCE_OF_TRUTH = ("Source of Truth", "Fonte de verdade")
        METADATA = ("metadata", "metadados")
        EXPORTS = ("exports", "exportações")
        MODULE_DOCSTRINGS = ("Module docstrings", "Docstrings dos módulos")
        CLASS_DOCSTRINGS = (
            "Class and function docstrings",
            "Docstrings das classes e funções",
        )
        GENERATED_PAGES = ("Generated Pages", "Páginas geradas")
        OVERVIEW = ("Overview", "Visão geral")
        PUBLIC_API = ("Public API", "API pública")
        MODULE_INDEX = ("Module Index", "Índice de módulos")
        SURFACE_SUMMARY = ("Surface Summary", "Resumo da interface")
        PRIMARY_FACADES = ("Primary facades", "Fachadas principais")
        GENERATED_MODULE_PAGES = (
            "Generated module pages",
            "Páginas de módulos geradas",
        )
        BACK_LINK = (
            "Back to [project docs](../index.md).",
            "Voltar à [documentação do projeto](../index.md).",
        )
        API_OVERVIEW = ("API Overview", "Visão geral da API")
        DOC_SUMMARY = ("Doc summary", "Resumo da documentação")
        CLASSIFIERS = ("Classifiers", "Classificadores")
        KEYWORDS = ("Keywords", "Palavras-chave")
        MAIN_FACADES = ("Main facades", "Fachadas principais")
        ALIAS_EXPORTS = ("Alias exports", "Exportações de aliases")
        PUBLIC_SYMBOL_EXPORTS = (
            "Public symbol exports",
            "Exportações de símbolos públicos",
        )
        MODULE_SHORTCUTS = (
            "Exported module shortcuts",
            "Atalhos de módulos exportados",
        )
        NEXT_PAGES = ("Next Pages", "Próximas páginas")
        MODULES_BODY = (
            "These pages are generated from public modules and their docstrings.",
            (
                "Estas páginas são geradas a partir dos módulos públicos e de "
                "suas docstrings."
            ),
        )
        NO_MODULES = (
            "_No public modules discovered._",
            "_Nenhum módulo público encontrado._",
        )
        DARK_MODE = ("Switch to dark mode", "Alternar para o modo escuro")
        LIGHT_MODE = ("Switch to light mode", "Alternar para o modo claro")
        ROOT_SITE_DESCRIPTION = (
            "Workspace documentation generated from code and curated root docs",
            (
                "Documentação do workspace gerada a partir do código e da "
                "documentação mantida na raiz"
            ),
        )
        PROJECT_SITE_DESCRIPTION = (
            "Generated documentation for",
            "Documentação gerada de",
        )

        def localized(self, language: t.Infra.DocumentationLanguage) -> str:
            """Return one message in the supported presentation language.

            Returns:
                The selected immutable message.

            """
            return self.value[1 if language == "pt-BR" else 0]

    DEFAULT_DOCS_OUTPUT_DIR: ClassVar[str] = ".reports/docs"
    # Registered docs CLI action names; make.docs.actions must stay inside this
    # surface so the generated Makefile loop can never dispatch a missing verb.
    DOCS_ACTION_IDS: ClassVar[frozenset[str]] = frozenset({
        "audit",
        "build",
        "collect",
        "fix",
        "fmt",
        "generate",
        "serve",
        "validate",
    })
    DOCS_CONFIG_FILENAME: ClassVar[str] = "docs_config.json"
    # Structured docs reports: the only report files the audit and validate
    # phases publish, and the only ones generated CI dumps and uploads.
    DOCS_AUDIT_SUMMARY_FILENAME: ClassVar[str] = "audit-summary.json"
    DOCS_AUDIT_REPORT_FILENAME: ClassVar[str] = "audit-report.md"
    DOCS_VALIDATE_SUMMARY_FILENAME: ClassVar[str] = "validate-summary.json"
    DOCS_VALIDATE_REPORT_FILENAME: ClassVar[str] = "validate-report.md"
    DOCS_STRUCTURED_REPORT_FILENAMES: ClassVar[t.VariadicTuple[str]] = (
        DOCS_AUDIT_SUMMARY_FILENAME,
        DOCS_AUDIT_REPORT_FILENAME,
        DOCS_VALIDATE_SUMMARY_FILENAME,
        DOCS_VALIDATE_REPORT_FILENAME,
    )
    DOCS_INSECURE_WEB_SCHEME: ClassVar[str] = "http"
    DOCS_SECURE_WEB_SCHEME: ClassVar[str] = "https"
    # A generated document may point outward, never carry a payload: a `data:`
    # target embeds its content in the link and can execute in a rendered page,
    # which is why the sanitizer has always stripped it. Declaring it here as a
    # preserved scheme made the catalog disagree with the only consumer.
    DOCS_EXTERNAL_SCHEMES: ClassVar[frozenset[str]] = frozenset({
        DOCS_SECURE_WEB_SCHEME,
        "mailto",
        "tel",
    })
    DOCS_FRAGMENT_PREFIX: ClassVar[str] = "#"
    PYTHON_FENCE_RUFF_EXTEND_IGNORE: ClassVar[t.StrSequence] = (
        "undocumented-public-module",
        "undocumented-public-function",
        "undocumented-public-class",
        "undocumented-public-method",
        "undocumented-public-init",
        "missing-copyright-notice",
        "implicit-namespace-package",
        "print",
        "assert",
        "boolean-positional-value-in-call",
        "no-self-use",
        "pytest-assert-in-except",
        "magic-value-comparison",
        "docstring-missing-returns",
        "docstring-missing-exception",
    )
    """Only module-header (docstring, copyright notice) and package rules are
    inapplicable to a standalone Markdown fence, which is not a module file;
    the pydocstyle public-surface family is inapplicable for the same reason
    (the surrounding prose is the fence's documentation), as is the
    docstring-completeness contract (example helpers keep their one-line
    docstrings; full Args/Returns sections are authored-source law),
    ``print`` is the fence demonstrating its output, ``assert`` and the
    pytest-idiom rules are the test-idiom contract of executable fences,
    which the pytest markdown-docs plugin runs as tests during ``make test``
    (the fleet's justified per-rule S101/PT test-idiom exception) — fences
    teaching exception semantics show real ``except`` blocks, the
    boolean-trap call-site rule is inapplicable because a fence must
    faithfully demonstrate the owning API's declared call signature;
    ``no-self-use`` is inapplicable for the same reason on adapter fences,
    where ``self`` is the port protocol's interface contract rather than an
    unused receiver, and magic-value-comparison is inapplicable because a
    fence's concrete
    literals are narrative data illustrating one scenario, never
    config-owned values. All names, behavior, types, and security rules
    remain active and require correction in the authored source."""
    MACHINE_PATH_RE: ClassVar[t.RegexPattern] = re.compile(
        r"(?<![\w./-])/(?:home|Users)/(?P<user>[A-Za-z0-9_.-]+)(?=/|\b)",
    )
    """Regex matching a per-user absolute root (``/home/<user>``, ``/Users/<user>``)."""
    # NOTE: MACHINE_PATH_CONTAINER_USERS was removed: container/CI home
    # identities are declared documentation-audit contract
    # (config/codegen.yaml repository.docs_audit.container_home_identities,
    # rendered into docs_config.json and validated by DocsAuditPolicySpec),
    # and the detector flags per-user absolute paths outside the checkout
    # root instead of allowlisting names.
    PYTHON_FENCE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^```python\s*\n(?P<body>.*?)^```\s*$",
        re.MULTILINE | re.DOTALL,
    )
    """Regex matching ``python`` fenced blocks; ``body`` group yields contents."""

    PYTHON_FENCE_FIX_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?P<indent>[ \t]*)(?P<open>```python[ \t]*\n)(?P<body>.*?)^```[ \t]*$",
        re.MULTILINE | re.DOTALL,
    )
    """Regex matching ``python`` fenced blocks for fix-in-place replacement."""

    WELDED_FENCE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?P<indent>[ \t]*)(?P<body>.*[^\s`])```[ \t]*$",
        re.MULTILINE,
    )
    """Match a closing fence welded to the final code line by an older fixer.

    The body must end in a non-whitespace, non-backtick character so that a
    legitimately indented closing fence (``   ``` ``) and an existing
    four-backtick fence are never rewritten; only a code line with the fence
    welded onto it matches, and its indentation is preserved on repair.
    """

    FENCE_NOTEST_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^```(\S+)\s+notest\s*$",
        re.MULTILINE,
    )
    """Regex matching fenced code blocks with a ``notest`` info qualifier."""

    FENCE_NOTEST_ATTR_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^```([A-Za-z0-9_+-]+)\s+notest\s*$",
        re.MULTILINE,
    )
    """Regex matching a bare ``notest`` qualifier for the buildable rewrite.

    ``pymdownx.superfences`` rejects an info string whose second token is not a
    known option, so a bare ``python notest`` fence is not rendered as code and
    its contents leak into the page as prose, swallowing the headings that
    follow. The fix phase rewrites it to the ``attr_list`` form
    ``{.python .notest}``, which superfences renders and whose info string still
    carries the marker the code gates skip. The language token excludes ``{``
    so an already-rewritten fence never matches again.
    """

    # --- Markdown link/heading patterns ---
    MARKDOWN_LINK_RE: ClassVar[t.RegexPattern] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    """Match markdown links capturing text (group 1) and URL (group 2)."""
    DOCS_GITHUB_BLOB_TREE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^https://github\.com/"
        r"(?P<org>[^/]+)/(?P<repo>[^/]+)/"
        r"(?P<kind>blob|tree)/"
        r"(?P<refpath>[^/?#]+/[^?#]*)"
        r"(?P<suffix>[?#].*)?$",
    )
    """Match a github.com blob/tree documentation URL by its named parts.

    ``refpath`` is the whole ``<ref>/<path>`` remainder: Git refs may contain
    ``/``, so the ref/path boundary is only decidable against the governed
    branch a consumer knows. ``suffix`` keeps a ``?query`` or ``#fragment``
    (for example ``#L10``) out of the filesystem path.
    """
    DOCS_ARTIFACT_MODE: ClassVar[Literal[0o644]] = 0o644
    """File mode every rendered documentation artifact is published with."""
    DOCS_OWNED_HEADER_LINES: ClassVar[int] = 2
    """Lines an owned member guide carries before its body: marker + source."""
    HEADING_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^#{1,6}\s+(.+?)\s*$",
        re.MULTILINE,
    )
    """Match any markdown heading (h1-h6), capturing the text."""
    INLINE_CODE_RE: ClassVar[t.RegexPattern] = re.compile(r"`[^`]*`")
    """Match inline code spans for stripping before analysis."""
    DOCS_INLINE_COMMAND_DIRECTIVE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"\b(?:run|execute|invoke|try|use)(?:\s+the\s+command)?\s*$",
        re.IGNORECASE,
    )
    """Recognize an instruction preceding a shell command in inline code."""
    STRING_LITERAL_RE: ClassVar[t.RegexPattern] = re.compile(
        r"""["']([a-zA-Z0-9_\.]+)["']""",
    )
    """Match quoted string literals, capturing the content."""

    DOCS_MAKE_COMMAND_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?make\s+(?P<verb>[a-z][a-z0-9_-]*)(?P<args>.*)$",
        re.IGNORECASE,
    )
    """Match an executable Make command and capture its verb and arguments."""
    DOCS_SHELL_FENCE_LANGUAGES: ClassVar[frozenset[str]] = frozenset({
        "",
        "bash",
        "console",
        "fish",
        "sh",
        "shell",
        "zsh",
    })
    """Markdown fence languages whose lines are executable shell commands."""
    DOCS_APPLY_RE: ClassVar[t.RegexPattern] = re.compile(r"\bAPPLY\s*=")
    """Reject the removed mutation selector for every supplied value."""
    DOCS_COMMAND_CONTRACT_DIRNAMES: ClassVar[frozenset[str]] = frozenset({
        "guides",
        "standards",
    })
    """Live documentation trees governed by the command contract."""
    DOCS_RAW_PYTEST_COMMAND_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S+)\s+)*"
        r"(?:(?:uv|poetry|pdm)\s+run\s+|"
        r"python(?:3(?:\.\d+)?)?\s+-m\s+)?pytest(?:\s|$)",
        re.IGNORECASE,
    )
    """Match direct pytest execution that bypasses the root Testmon verb."""
    DOCS_RAW_TOOL_COMMAND_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S+)\s+)*"
        r"(?:(?:ruff|pyrefly|mypy|pyright|mkdocs|uv|poetry|pdm|tox|nox|pre-commit)(?=\s|$)|"
        r"python(?:3(?:\.\d+)?)?(?:\s+-m|\s+[^\s]+\.py\b))",
        re.IGNORECASE,
    )
    """Match tool and script commands that bypass the root Make dispatcher."""
    ISO_DATE_STRING_LENGTH: ClassVar[int] = 10
    """Length of an ISO date string ``YYYY-MM-DD``."""
    DOCS_TEST_DOUBLE_CODE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"(?:from\s+unittest(?:\.mock)?\s+import|import\s+unittest\.mock|"
        r"(?:^|\W)(?:MagicMock|Mock|patch)\s*\(|mock\.patch\s*\(|"
        r"monkeypatch\.[A-Za-z_]|class\s+(?:Fake|Stub)[A-Za-z0-9_]*|"
        r"(?:^|\W)(?:fake|stub)_[A-Za-z0-9_]+)",
        re.IGNORECASE,
    )
    """Match test-double construction inside executable Python examples."""
    DOCS_TEST_DOUBLE_HEADING_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*#{1,6}\s+.*\b(?:mock(?:ing|s)?|fake(?:s)?|stub(?:bing|s)?|"
        r"patch(?:ing)?)\b",
        re.IGNORECASE,
    )
    """Match headings that introduce test-double guidance."""


__all__: list[str] = ["FlextInfraConstantsDocs"]
