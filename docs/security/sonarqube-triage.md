# Triagem SonarCloud — flext-sh/flext-infra

Gerado do dump da plataforma SonarCloud (2026-08-06).

Bead: `mro-2wjm.8`

## Resumo

**397 issues** — BLOCKER 24, CRITICAL 222, MAJOR 104, MINOR 47
Tipos: VULNERABILITY 57, BUG 4, CODE_SMELL 336 · **Debt total: 5399min**

| regra | issues |
|---|---|
| `python:S3776` | 180 |
| `python:S1192` | 37 |
| `python:S8786` | 23 |
| `docker:S6506` | 20 |
| `python:S3358` | 17 |
| `python:S5778` | 17 |
| `docker:S8482` | 15 |
| `python:S7504` | 7 |
| `python:S6353` | 7 |
| `pythonsecurity:S2083` | 5 |

## Como usar

Cada issue traz a **mensagem do SonarQube** (descreve o problema e o impacto), o **código real** (linha `>>>`), o tipo e o effort estimado.
**Decisão**: `corrigir` / `falso-positivo` (marcar na plataforma com justificativa) / `risco-aceito`. Ordem: BLOCKER → CRITICAL → VULNERABILITY → MAJOR. CODE_SMELL em volume pede correção de padrão.

## Issues

### 1 · 🔴 BLOCKER · VULNERABILITY · `pythonsecurity:S2083`
**Local**: `src/flext_infra/_utilities/namespace_analysis.py:161` · **Effort**: 30min

> Change this code to not construct the path from user-controlled data.

```python
      157                  continue
      158              rewritten = FlextInfraUtilitiesRefactorNamespaceMro.insert_import_lines(
      159                  lines=lines, imports=["", c.Infra.FUTURE_ANNOTATIONS, ""]
      160              )
>>>   161              _ = file_path.write_text(
      162                  "\n".join(rewritten).rstrip() + "\n", encoding=c.Cli.ENCODING_DEFAULT
      163              )
      164  
      165  
```

**Decisão**:

### 2 · 🔴 BLOCKER · VULNERABILITY · `pythonsecurity:S2083`
**Local**: `src/flext_infra/_utilities/namespace_facades.py:271` · **Effort**: 30min

> Change this code to not construct the path from user-controlled data.

```python
      267                  )
      268                  updated_lines[all_index : end_index + 1] = [all_line]
      269              updated_source = "\n".join(updated_lines).rstrip() + "\n"
      270          if updated_source != source:
>>>   271              _ = target_path.write_text(updated_source, encoding=c.Cli.ENCODING_DEFAULT)
      272  
      273  
      274  __all__: list[str] = ["FlextInfraUtilitiesRefactorNamespaceFacades"]
```

**Decisão**:

### 3 · 🔴 BLOCKER · VULNERABILITY · `pythonsecurity:S2083`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:937` · **Effort**: 30min

> Change this code to not construct the path from user-controlled data.

```python
      933                      backup_path = py_file.with_suffix(
      934                          py_file.suffix + c.Infra.SAFE_EXECUTION_BAK_SUFFIX
      935                      )
      936                      if not backup_path.exists():
>>>   937                          backup_path.write_text(
      938                              original_source, encoding=c.Cli.ENCODING_DEFAULT
      939                          )
      940  
      941  
```

**Decisão**:

### 4 · 🔴 BLOCKER · VULNERABILITY · `pythonsecurity:S2083`
**Local**: `src/flext_infra/_utilities/rope_source.py:448` · **Effort**: 30min

> Change this code to not construct the path from user-controlled data.

```python
      444              if (
      445                  file_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
      446                  != original_disk_source
      447              ):
>>>   448                  file_path.write_text(
      449                      original_disk_source, encoding=c.Cli.ENCODING_DEFAULT
      450                  )
      451  
      452  
```

**Decisão**:

### 5 · 🔴 BLOCKER · VULNERABILITY · `pythonsecurity:S2083`
**Local**: `src/flext_infra/release/orchestrator_phases.py:112` · **Effort**: 30min

> Change this code to not construct the path from user-controlled data.

```python
      108                      return r[str].fail(
      109                          f"immutable release policy collision: {destination}"
      110                      )
      111              else:
>>>   112                  destination.write_bytes(content)
      113              return r[str].ok(hashlib.sha256(content).hexdigest())
      114          except OSError as exc:
      115              return r[str].fail_op(f"persist release policy {destination}", exc)
      116  
```

**Decisão**:

### 6 · 🔴 BLOCKER · CODE_SMELL · `python:S1845`
**Local**: `src/flext_infra/transformers/cli_modernizer.py:76` · **Effort**: 10min

> Rename method "_banned_modules" to prevent any misunderstanding/clash with field "_BANNED_MODULES" defined on line 35

```python
       72  
       73          return updated, list(self.changes)
       74  
       75      @staticmethod
>>>    76      def _banned_modules() -> frozenset[str]:
       77          """Return the set of CLI helper modules whose imports are removed."""
       78          return FlextInfraRefactorCliModernizer._BANNED_MODULES
       79  
       80      @staticmethod
```

**Decisão**:

### 7 · 🔴 BLOCKER · CODE_SMELL · `python:S1845`
**Local**: `src/flext_infra/transformers/cli_modernizer.py:81` · **Effort**: 10min

> Rename method "_cli_pkg" to prevent any misunderstanding/clash with field "_CLI_PKG" defined on line 34

```python
       77          """Return the set of CLI helper modules whose imports are removed."""
       78          return FlextInfraRefactorCliModernizer._BANNED_MODULES
       79  
       80      @staticmethod
>>>    81      def _cli_pkg() -> str:
       82          """Return the canonical FLEXT CLI package name."""
       83          return FlextInfraRefactorCliModernizer._CLI_PKG
       84  
       85      @staticmethod
```

**Decisão**:

### 8 · 🔴 BLOCKER · CODE_SMELL · `python:S1845`
**Local**: `src/flext_infra/transformers/cli_modernizer.py:86` · **Effort**: 10min

> Rename method "_manual_attrs" to prevent any misunderstanding/clash with field "_MANUAL_ATTRS" defined on line 42

```python
       82          """Return the canonical FLEXT CLI package name."""
       83          return FlextInfraRefactorCliModernizer._CLI_PKG
       84  
       85      @staticmethod
>>>    86      def _manual_attrs() -> dict[str, frozenset[str]]:
       87          """Return banned-module attributes that require manual conversion."""
       88          return FlextInfraRefactorCliModernizer._MANUAL_ATTRS
       89  
       90      class _CliVisitor(FlextInfraSourceRewriter):
```

**Decisão**:

### 9 · 🔴 BLOCKER · CODE_SMELL · `python:S3516`
**Local**: `src/flext_infra/transformers/project_alias_migrator.py:153` · **Effort**: 2min

> Refactor this method to not always return the same value.

```python
      149      def leave_If(self, original_node: cst.If) -> None:
      150          self._leave_if()
      151  
      152      @override
>>>   153      def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
      154          if self._in_type_checking():
      155              return True
      156          module = _CstImportHelpers.dotted_name(node.module)
      157          if module is None or not module.startswith(f"{self.current_project}."):
```

**Decisão**:

### 10 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:20` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       16  # === SECTION: managed tool bootstrap (managed) ===
       17  # Source: config:python_version, template (installer URLs)
       18  # mise installs the supported Python 3.13 family.
       19  # uv is supplied by the managed environment without a project patch pin.
>>>    20  RUN curl -fsSL https://mise.run | sh
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
       23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 11 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:23` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       19  # uv is supplied by the managed environment without a project patch pin.
       20  RUN curl -fsSL https://mise.run | sh
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       25  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       26  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       27  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 12 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:25` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
       23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    25  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       26  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       27  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       28      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       29  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 13 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:22` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       18  # === SECTION: managed tool bootstrap (managed) ===
       19  # Source: config:python_version, template (installer URLs)
       20  # mise installs the supported Python 3.13 family.
       21  # uv is supplied by the managed environment without a project patch pin.
>>>    22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 14 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:25` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       21  # uv is supplied by the managed environment without a project patch pin.
       22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 15 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:27` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 16 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:23` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       19  # === SECTION: managed tool bootstrap (managed) ===
       20  # Source: config:python_version, template (installer URLs)
       21  # mise installs the supported Python 3.13 family.
       22  # uv is supplied by the managed environment without a project patch pin.
>>>    23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 17 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:26` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       22  # uv is supplied by the managed environment without a project patch pin.
       23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 18 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:28` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 19 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:22` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       18  # === SECTION: managed tool bootstrap (managed) ===
       19  # Source: config:python_version, template (installer URLs)
       20  # mise installs the supported Python 3.13 family.
       21  # uv is supplied by the managed environment without a project patch pin.
>>>    22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 20 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:25` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       21  # uv is supplied by the managed environment without a project patch pin.
       22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 21 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:27` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 22 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:23` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       19  # === SECTION: managed tool bootstrap (managed) ===
       20  # Source: config:python_version, template (installer URLs)
       21  # mise installs the supported Python 3.13 family.
       22  # uv is supplied by the managed environment without a project patch pin.
>>>    23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 23 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:26` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       22  # uv is supplied by the managed environment without a project patch pin.
       23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 24 · 🔴 BLOCKER · VULNERABILITY · `docker:S8482`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:28` · **Effort**: 15min

> Avoid executing downloaded artifacts directly without verification.

```Dockerfile
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 25 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_constants/check.py:114` · **Effort**: 6min

> Define a constant instead of duplicating this literal "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps" 3 times.

```python
      110          "colorama": "cli.print with c.Cli.MessageStyles",
      111          "prompt_toolkit": "cli.prompt / cli.confirm / cli.prompt_password",
      112          "tqdm": "cli.display_progress",
      113          "getpass": "cli.prompt_password",
>>>   114          "orjson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
      115          "ujson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
      116          "simplejson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
      117      })
      118      # Precompiled (lib, regex, replacement) rows — click is exempted at the call
```

**Decisão**:

### 26 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_constants/codegen_lazy.py:82` · **Effort**: 8min

> Define a constant instead of duplicating this literal "{file}" 4 times.

```python
       78      )
       79      "Regex: malformed ``from import`` statement (missing module name)."
       80  
       81      LINT_TOOLS: Final[t.StrSequencePairTuple] = (
>>>    82          ("ruff", ("ruff", "check", "{file}", "--no-fix", "--select", "E,F")),
       83          ("pyright", ("pyright", "{file}")),
       84          ("mypy", ("mypy", "{file}", "--no-error-summary")),
       85          ("pyrefly", ("pyrefly", "check", "{file}")),
       86      )
```

**Decisão**:

### 27 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_models/codegen.py:398` · **Effort**: 6min

> Define a constant instead of duplicating this literal "Config version" 3 times.

```python
      394  
      395      class ConstantsGovernanceConfig(m.ArbitraryTypesModel):
      396          """Constants governance config."""
      397  
>>>   398          version: str = m.Field(description="Config version")
      399          rules: list[FlextInfraModelsCodegen.NsRule] = m.Field(
      400              description="Governance rules"
      401          )
      402          canonical_values: list[FlextInfraModelsCodegen.CanonicalValueRule] = m.Field(
```

**Decisão**:

### 28 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_models/codegen_render.py:26` · **Effort**: 6min

> Define a constant instead of duplicating this literal "Generated module docstring." 3 times.

```python
       22  
       23          class_name: t.NonEmptyStr = m.Field(description="Generated class name.")
       24          base_class: t.NonEmptyStr = m.Field(description="Generated base class name.")
       25          base_import_block: str = m.Field(description="Rendered base import block.")
>>>    26          docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
       27  
       28      # NOTE (multi-agent, mro-p4s3.2 / agent: uv_overlay_owner): the docs
       29      # renderer sends one immutable model directly to the flext-cli boundary.
       30      class MkdocsRenderContext(m.ContractModel):
```

**Decisão**:

### 29 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_models/deps_toml.py:31` · **Effort**: 6min

> Define a constant instead of duplicating this literal "Operation kind" 3 times.

```python
       27                  """Set one TOML key to one JSON-compatible value."""
       28  
       29                  kind: Literal[c.Infra.TomlOperationKind.SET] = m.Field(
       30                      c.Infra.TomlOperationKind.SET,
>>>    31                      description="Operation kind",
       32                      validate_default=True,
       33                  )
       34                  key: str = m.Field(description="TOML key name")
       35                  value: t.JsonValue = m.Field(description="JSON-compatible value")
```

**Decisão**:

### 30 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_models/release.py:163` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      159              m.Field(description="Trusted Gitleaks policy SHA-256"),
      160          ]
      161  
      162          @u.model_validator(mode="after")
>>>   163          def validate_manifest(self) -> Self:
      164              """Require totals, project identity, outcomes, and artifacts to agree."""
      165              if self.total != len(self.records):
      166                  msg = "build report total does not match record count"
      167                  raise ValueError(msg)
```

**Decisão**:

### 31 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_git/semantic.py:68` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
       64          return component
       65      return urlencode(out)
       66  
       67  
>>>    68  def _redact_origin_remote(url: str) -> str:
       69      """Strip credential userinfo and sensitive query/fragment tokens."""
       70      value = url.strip()
       71      try:
       72          parsed = urlsplit(value)
```

**Decisão**:

### 32 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_git/worktree.py:145` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
      141              return r[Path].fail(str(exc))
      142          return r[Path].ok(Path(top_level).resolve())
      143  
      144      @classmethod
>>>   145      def _git_primary_worktree_root_path(cls, repository_path: Path) -> p.Result[Path]:
      146          """Private Path-based primary worktree resolver."""
      147          try:
      148              repo = cls._repo(repository_path)
      149              common_dir_text = repo.git.rev_parse(
```

**Decisão**:

### 33 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_git/worktree.py:435` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
      431          """Return whether a relative path belongs to an excluded subtree."""
      432          return any(path == prefix or prefix in path.parents for prefix in excluded)
      433  
      434      @classmethod
>>>   435      def _git_copy_untracked(
      436          cls, source_root: Path, worktree_root: Path, excluded: t.SequenceOf[Path]
      437      ) -> p.Result[bool]:
      438          """Copy non-ignored untracked files into an isolated worktree."""
      439          try:
```

**Decisão**:

### 34 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_git/worktree.py:727` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      723                  added.append(current)
      724          return tuple(added)
      725  
      726      @classmethod
>>>   727      def _git_apply_gitlinks(cls, repository_root: Path, patch: bytes) -> p.Result[bool]:
      728          """Apply submodule entries that have no working-tree file representation."""
      729          current: Path | None = None
      730          gitlink = False
      731          for raw_line in patch.splitlines():
```

**Decisão**:

### 35 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/_github_pr_execution.py:69` · **Effort**: 6min

> Define a constant instead of duplicating this literal "invalid pull-request create request" 3 times.

```python
       65          validation = FlextInfraUtilitiesGithubPrExecutionMixin._validate_github_pr_create_request(
       66              request
       67          )
       68          if validation.failure:
>>>    69              return r.fail(validation.error or "invalid pull-request create request")
       70          title, body = validation.value
       71          command: list[str] = [
       72              c.Infra.GH,
       73              c.Infra.PR,
```

**Decisão**:

### 36 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_project_discovery_candidates.py:31` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       27  ):
       28      """Private candidate enumeration for workspace project discovery."""
       29  
       30      @classmethod
>>>    31      def discover_external_workspace_roots(
       32          cls, workspace_root: Path, *, scan_dirs: frozenset[str] | None = None
       33      ) -> t.SequenceOf[Path]:
       34          """Return explicitly configured workspace roots outside ``workspace_root``.
       35  
```

**Decisão**:

### 37 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_project_discovery_candidates.py:121` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      117              seen.add(resolved_candidate)
      118          return tuple(roots)
      119  
      120      @classmethod
>>>   121      def discover_project_candidates(
      122          cls,
      123          workspace_root: Path,
      124          *,
      125          scan_dirs: frozenset[str] | None = None,
```

**Decisão**:

### 38 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_rope/pep695_patch.py:52` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
       48  
       49      _applied: ClassVar[bool] = False
       50  
       51      @classmethod
>>>    52      def apply(cls) -> None:
       53          """Install PEP 695 handlers on rope's ``_PatchingASTWalker`` once."""
       54          if cls._applied:
       55              return
       56          walker = FlextInfraUtilitiesRopeRuntime.patched_ast_walker()
```

**Decisão**:

### 39 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/_rope_bracket_balance.py:74` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
       70                  line
       71              )
       72  
       73      @staticmethod
>>>    74      def _fallback_bracket_balance_line(line: str) -> int:
       75          """Approximate bracket balance for incomplete lines that ``tokenize`` rejects."""
       76          balance = 0
       77          in_single_quote = False
       78          in_double_quote = False
```

**Decisão**:

### 40 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/census.py:181` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      177              planned_ranges.append(occurrence_range)
      178          return FlextInfraUtilitiesRefactorCensus.merge_line_ranges(planned_ranges)
      179  
      180      @staticmethod
>>>   181      def _aliased_import_occurrence_lines(
      182          rope: p.Infra.RopeWorkspaceDsl,
      183          file_path: Path,
      184          source: str,
      185          *,
```

**Decisão**:

### 41 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/census.py:329` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
      325              )
      326          return updates
      327  
      328      @staticmethod
>>>   329      def _removed_alias_names(
      330          rope: p.Infra.RopeWorkspaceDsl,
      331          file_path: Path,
      332          *,
      333          target_name: str,
```

**Decisão**:

### 42 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/census.py:398` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      394          """Return whether ``line`` falls inside any removed range."""
      395          return any(start <= line <= end for start, end in removed_ranges)
      396  
      397      @staticmethod
>>>   398      def build_facade_base_cascade_updates(
      399          rope: p.Infra.RopeWorkspaceDsl,
      400          candidate: m.Infra.Census.RemovalCandidate,
      401          *,
      402          source_cache: dict[Path, str] | None = None,
```

**Decisão**:

### 43 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/census.py:481` · **Effort**: 6min

> Define a constant instead of duplicating this literal "class " 3 times.

```python
      477          index = 0
      478          changed = False
      479          while index < len(rewritten_lines):
      480              line = rewritten_lines[index]
>>>   481              if not line.lstrip().startswith("class "):
      482                  index += 1
      483                  continue
      484              header_start = index
      485              header_lines = [rewritten_lines[index]]
```

**Decisão**:

### 44 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/census.py:559` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      555          ])
      556          return rewritten, True, False
      557  
      558      @staticmethod
>>>   559      def strip_module_all_entry(source: str, name: str) -> str:
      560          """Remove ``name`` from a module-level ``__all__`` list declaration.
      561  
      562          Handles both single-line and multi-line ``__all__`` forms. The list is
      563          normalised to single-line ``[...]`` when all remaining entries fit on
```

**Decisão**:

### 45 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/dependencies.py:51` · **Effort**: 42min

> Refactor this function to reduce its Cognitive Complexity from 52 to the 15 allowed.

```python
       47          normalized_version = version.strip()
       48          return f">={normalized_version}" if normalized_version else ""
       49  
       50      @classmethod
>>>    51      def locked_dependency_versions(cls, lock_path: Path) -> t.MappingKV[str, str]:
       52          """Return normalized registry package versions from one ``uv.lock`` file."""
       53          result: t.MappingKV[str, str] = {}
       54          if lock_path.is_file():
       55              try:
```

**Decisão**:

### 46 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/dependencies.py:92` · **Effort**: 19min

> Refactor this function to reduce its Cognitive Complexity from 29 to the 15 allowed.

```python
       88                              result = dict(versions)
       89          return result
       90  
       91      @classmethod
>>>    92      def rewrite_requirement_constraint(
       93          cls,
       94          requirement: str,
       95          *,
       96          locked_versions: t.MappingKV[str, str],
```

**Decisão**:

### 47 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/dependencies.py:128` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      124                              result = rewritten if rewritten != raw_text else None
      125          return result
      126  
      127      @classmethod
>>>   128      def rewrite_poetry_constraint(
      129          cls,
      130          dependency_name: str,
      131          raw_value: t.Infra.InfraValue,
      132          *,
```

**Decisão**:

### 48 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/discovery.py:276` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      272              return project_root
      273          return resolved_root
      274  
      275      @staticmethod
>>>   276      def find_all_pyproject_files(
      277          workspace_root: Path,
      278          *,
      279          skip_dirs: frozenset[str] | None = None,
      280          project_paths: t.SequenceOf[Path] | None = None,
```

**Decisão**:

### 49 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/docs_api.py:138` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      134              return f"{package_name}{module_name}"
      135          return module_name
      136  
      137      @classmethod
>>>   138      def _resolve_lazy_import_targets(
      139          cls,
      140          project_root: Path,
      141          *,
      142          root_package: str,
```

**Decisão**:

### 50 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/docs_audit.py:117` · **Effort**: 23min

> Refactor this function to reduce its Cognitive Complexity from 33 to the 15 allowed.

```python
      113              names.update(item for item in value if isinstance(item, str))
      114          return names
      115  
      116      @staticmethod
>>>   117      def docs_broken_link_issues(
      118          scope: m.Infra.DocScope,
      119      ) -> t.SequenceOf[m.Infra.AuditIssue]:
      120          """Collect broken internal link issues in one docs scope."""
      121          issues: t.MutableSequenceOf[m.Infra.AuditIssue] = []
```

**Decisão**:

### 51 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/docs_generate.py:60` · **Effort**: 8min

> Define a constant instead of duplicating this literal "docs/api-reference/generated/overview.md" 4 times.

```python
       56              scope.path, scope.package_name
       57          )
       58          module_names = FlextInfraUtilitiesDocsGenerate._module_names(contract)
       59          expected_generated: t.MutableSequenceOf[Path] = [
>>>    60              scope.path / "docs/api-reference/generated/overview.md",
       61              scope.path / "docs/api-reference/generated/public-api.md",
       62              scope.path / "docs/api-reference/generated/modules/index.md",
       63          ]
       64          files: t.MutableSequenceOf[m.Infra.GeneratedFile] = [
```

**Decisão**:

### 52 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/docs_generate.py:86` · **Effort**: 6min

> Define a constant instead of duplicating this literal "mkdocs.yml" 3 times.

```python
       82                  FlextInfraUtilitiesDocsRender.docs_api_readme(scope, contract),
       83                  apply=apply,
       84              ),
       85              FlextInfraUtilitiesDocsContract.docs_write_if_needed(
>>>    86                  scope.path / "mkdocs.yml",
       87                  FlextInfraUtilitiesDocsRender.docs_project_mkdocs(
       88                      scope, contract, module_names
       89                  ),
       90                  apply=apply,
```

**Decisão**:

### 53 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/docs_generate.py:130` · **Effort**: 8min

> Define a constant instead of duplicating this literal "docs/api-reference/generated" 4 times.

```python
      126                  )
      127              )
      128          files.extend(
      129              FlextInfraUtilitiesDocsGenerate._prune_generated_tree(
>>>   130                  scope.path / "docs/api-reference/generated",
      131                  expected_generated,
      132                  apply=apply,
      133              )
      134          )
```

**Decisão**:

### 54 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/docs_render.py:216` · **Effort**: 6min

> Define a constant instead of duplicating this literal "AGENTS.md" 3 times.

```python
      212          other boilerplate helpers but is intentionally unused.
      213          """
      214          _ = scope
      215          agents_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
>>>   216              link_prefix, "AGENTS.md"
      217          )
      218          return [
      219              "## Collection Rules",
      220              "",
```

**Decisão**:

### 55 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/docs_render.py:275` · **Effort**: 6min

> Define a constant instead of duplicating this literal "_not declared_" 3 times.

```python
      271      def docs_project_index(scope: m.Infra.DocScope, contract: t.JsonMapping) -> str:
      272          """Return the standard ``<project>/docs/index.md`` landing page."""
      273          data = contract
      274          version = str(data.get("version", "")).strip() or "unknown"
>>>   275          description = str(data.get("description", "")).strip() or "_not declared_"
      276          link_prefix = FlextInfraUtilitiesDocsRender._LINK_PREFIX_DOCS_INDEX
      277          return FlextInfraUtilitiesDocsRender._generated_page(
      278              f"{scope.name} Documentation",
      279              [
```

**Decisão**:

### 56 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/github_pr.py:101` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
       97          context.outcomes.append(outcome)
       98          return r[m.Infra.GithubPullRequestOutcome].ok(outcome)
       99  
      100      @classmethod
>>>   101      def _github_pr_checkpoint(cls, repo_root: Path, branch: str) -> p.Result[bool]:
      102          """Github pr checkpoint."""
      103          changes_capture = u.Cli.capture(
      104              [c.Infra.GIT, "status", "--porcelain"], cwd=repo_root
      105          )
```

**Decisão**:

### 57 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/mro_scan.py:21` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       17  class FlextInfraUtilitiesRefactorMroScan:
       18      """Scan project sources for declarations movable into MRO facade classes."""
       19  
       20      @classmethod
>>>    21      def scan_workspace(
       22          cls,
       23          *,
       24          workspace_root: Path,
       25          target: str,
```

**Decisão**:

### 58 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/namespace_analysis.py:25` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       21  ):
       22      """Helpers for MRO completeness and future-import rewrites."""
       23  
       24      @staticmethod
>>>    25      def rewrite_mro_completeness_violations(
       26          *,
       27          violations: t.SequenceOf[m.Infra.MROCompletenessViolation],
       28          parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation],
       29      ) -> None:
```

**Decisão**:

### 59 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:34` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       30  class FlextInfraUtilitiesRefactorNamespaceMoves:
       31      """Helpers for block moves and compatibility-alias rewrites."""
       32  
       33      @classmethod
>>>    34      def rewrite_import_violations(
       35          cls, *, py_files: t.SequenceOf[Path], project_package: str
       36      ) -> None:
       37          """Rewrite import violations."""
       38          if not py_files:
```

**Decisão**:

### 60 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:84` · **Effort**: 10min

> Define a constant instead of duplicating this literal "rope import cleanup failed" 5 times.

```python
       80                      file_paths=(file_path,),
       81                      preserve_canonical_aliases=True,
       82                  )
       83                  if cleanup_result.failure:
>>>    84                      msg = cleanup_result.error or "rope import cleanup failed"
       85                      raise RuntimeError(msg)
       86  
       87      @staticmethod
       88      def rewrite_namespace_source_violations(
```

**Decisão**:

### 61 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:535` · **Effort**: 20min

> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

```python
      531              raise RuntimeError(msg)
      532          return (source_file, target_file, tuple(moved))
      533  
      534      @staticmethod
>>>   535      def _collect_required_import_lines(
      536          *, source: str, blocks: t.StrSequence
      537      ) -> t.StrSequence:
      538          """Collect required import lines using rope-parsed module bodies."""
      539          source_pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
```

**Decisão**:

### 62 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:831` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      827              f"from {c.Infra.PKG_CORE_UNDERSCORE} import {', '.join(missing_aliases)}"
      828          ]
      829  
      830      @staticmethod
>>>   831      def _collect_orphaned_import_lines(
      832          *, source: str, kept_source: str, max_line: int
      833      ) -> t.StrSequence:
      834          """Collect orphaned import lines via rope-parsed bodies."""
      835          source_pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
```

**Decisão**:

### 63 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/namespace_moves.py:873` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      869              )
      870          return import_lines
      871  
      872      @staticmethod
>>>   873      def _rewrite_moved_imports(
      874          *,
      875          project_root: Path,
      876          py_files: t.SequenceOf[Path],
      877          moves: t.SequenceOf[t.Triple[Path, Path, t.VariadicTuple[str]]],
```

**Decisão**:

### 64 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/pyproject.py:143` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      139              raise ValueError(msg)
      140          return raw_name.strip()
      141  
      142      @staticmethod
>>>   143      def package_name_from_payload(
      144          project_root: Path, payload: t.JsonMapping, docs_meta: t.JsonMapping
      145      ) -> str:
      146          """Return the primary package name using pre-loaded pyproject payload."""
      147          configured = docs_meta.get("package_name")
```

**Decisão**:

### 65 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:43` · **Effort**: 6min

> Define a constant instead of duplicating this literal "pyproject content must define [project]" 3 times.

```python
       39          if source is None:
       40              return r[str].fail("pyproject content is not valid TOML")
       41          project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
       42          if project is None:
>>>    43              return r[str].fail("pyproject content must define [project]")
       44          project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
       45          if not isinstance(project_name_raw, str) or not project_name_raw.strip():
       46              return r[str].fail("[project].name must be a non-empty string")
       47          project_name = project_name_raw.strip()
```

**Decisão**:

### 66 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:82` · **Effort**: 6min

> Define a constant instead of duplicating this literal "uv source conformance failed" 3 times.

```python
       78              exclude_newer=toolchain.uv_exclude_newer,
       79              exclude_dependencies=uv_exclude_dependencies,
       80          )
       81          if sources_result.failure:
>>>    82              return r[str].fail(sources_result.error or "uv source conformance failed")
       83          provenance_result = cls._validate_dependency_provenance(
       84              source,
       85              project_name=project_name,
       86              workspace=workspace,
```

**Decisão**:

### 67 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:100` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       96              return r[str].fail("canonical pyproject rendering produced invalid TOML")
       97          return r[str].ok(rendered)
       98  
       99      @classmethod
>>>   100      def pyproject_dependencies_conform(
      101          cls,
      102          pyproject_content: str,
      103          *,
      104          providers: t.SequenceOf[m.Infra.ProviderSpec],
```

**Decisão**:

### 68 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:277` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      273          u.Cli.toml_sync_string_list(container, key, canonical)
      274          return r[bool].ok(True)
      275  
      276      @classmethod
>>>   277      def _canonical_requirement(
      278          cls,
      279          requirement: str,
      280          *,
      281          repositories: t.SequenceOf[p.Infra.RepositoryRef],
```

**Decisão**:

### 69 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:548` · **Effort**: 27min

> Refactor this function to reduce its Cognitive Complexity from 37 to the 15 allowed.

```python
      544              )
      545          return r[bool].ok(True)
      546  
      547      @classmethod
>>>   548      def _sync_uv_sources(
      549          cls,
      550          document: t.Cli.TomlDocument,
      551          *,
      552          project_name: str,
```

**Decisão**:

### 70 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/pyproject_conform.py:743` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      739                  )
      740          return r[bool].ok(True)
      741  
      742      @classmethod
>>>   743      def _validate_dependency_provenance(
      744          cls,
      745          document: t.Cli.TomlDocument,
      746          *,
      747          project_name: str,
```

**Decisão**:

### 71 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/release.py:115` · **Effort**: 6min

> Define a constant instead of duplicating this literal "# Changelog\n\n" 3 times.

```python
      111          notes_text = notes_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
      112          existing = (
      113              changelog_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
      114              if changelog_path.exists()
>>>   115              else "# Changelog\n\n"
      116          )
      117          updated = FlextInfraUtilitiesRelease._updated_changelog(
      118              existing=existing, version=version, tag=tag
      119          )
```

**Decisão**:

### 72 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:181` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      177          """Return a superclass name from Rope objects with uneven public APIs."""
      178          return FlextInfraUtilitiesRopeAnalysis._superclass_name(superclass)
      179  
      180      @staticmethod
>>>   181      def _superclass_name(
      182          superclass: p.AttributeProbe, *, visited: frozenset[int] | None = None
      183      ) -> str:
      184          """Return a superclass name from Rope objects with uneven public APIs."""
      185          visited_ids = visited or frozenset()
```

**Decisão**:

### 73 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:978` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      974                  break
      975          return "\n".join(collected)
      976  
      977      @staticmethod
>>>   978      def _bracket_depth_delta(source: str) -> int:
      979          """Return bracket nesting delta for one source line."""
      980          depth = 0
      981          quote = ""
      982          escaped = False
```

**Decisão**:

### 74 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1006` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
     1002                  depth -= 1
     1003          return depth
     1004  
     1005      @staticmethod
>>>  1006      def _split_top_level_commas(source: str) -> t.StrSequence:
     1007          """Split one source fragment on commas outside nested delimiters."""
     1008          parts: list[str] = []
     1009          start = 0
     1010          depth = 0
```

**Decisão**:

### 75 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1044` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
     1040              parts.append(tail)
     1041          return tuple(parts)
     1042  
     1043      @staticmethod
>>>  1044      def _top_level_partition(source: str, separator: str) -> tuple[str, str, str]:
     1045          """Partition one source fragment at a top-level separator."""
     1046          depth = 0
     1047          quote = ""
     1048          escaped = False
```

**Decisão**:

### 76 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1152` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
     1148                  source[open_index + 1 : close_index]
     1149              )
     1150  
     1151      @staticmethod
>>>  1152      def _matching_close_index(source: str, open_index: int) -> int:
     1153          """Return the index of the closing delimiter matching ``open_index``."""
     1154          open_char = source[open_index]
     1155          close_char = {"(": ")", "[": "]", "{": "}"}[open_char]
     1156          depth = 0
```

**Decisão**:

### 77 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1199` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
     1195                  return value
     1196          return ""
     1197  
     1198      @staticmethod
>>>  1199      def _mapping_entries_refs_source(
     1200          source: str,
     1201      ) -> tuple[tuple[tuple[str, t.StrSequence], ...], t.StrSequence]:
     1202          """Return lazy-map entries and referenced mapping symbols from source."""
     1203          text = source.strip()
```

**Decisão**:

### 78 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1286` · **Effort**: 6min

> Define a constant instead of duplicating this literal " import " 3 times.

```python
     1282          lines = source.splitlines()
     1283          bindings: list[tuple[str, int, str, str]] = []
     1284          for index, line in enumerate(lines):
     1285              stripped = line.strip()
>>>  1286              if not stripped.startswith("from ") or " import " not in stripped:
     1287                  continue
     1288              statement = FlextInfraUtilitiesRopeAnalysis._collect_statement(
     1289                  lines, index
     1290              ).strip()
```

**Decisão**:

### 79 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1356` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
     1352                  names.append(name)
     1353          return names
     1354  
     1355      @staticmethod
>>>  1356      def export_target_modules_source(
     1357          source: str, package_name: str, exports: t.StrSequence
     1358      ) -> dict[str, str]:
     1359          """Map exports → defining module via rope's parsed-source import table."""
     1360          export_names = {name for name in exports if name}
```

**Decisão**:

### 80 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1477` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
     1473                      stack.append(value)
     1474          return collected
     1475  
     1476      @staticmethod
>>>  1477      def ast_parent_map(root: object) -> dict[int, object]:
     1478          """Return a child-id -> parent map for the full AST reachable from ``root``.
     1479  
     1480          Uses only public ``_fields`` access (no ``import ast``); the shared SSOT
     1481          for parent lookups across every rope detector.
```

**Decisão**:

### 81 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1839` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
     1835              rope_project.close()
     1836          return target_map
     1837  
     1838      @classmethod
>>>  1839      def parent_constants_targets(
     1840          cls,
     1841          constants_file: Path,
     1842          project_root: Path,
     1843          *,
```

**Decisão**:

### 82 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis_workspace.py:99` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
       95              )
       96          )
       97  
       98      @classmethod
>>>    99      def _collect_modules(
      100          cls, rope_project: t.Infra.RopeProject, resolved_root: Path
      101      ) -> tuple[
      102          dict[str, m.Infra.RopeModuleIndexEntry],
      103          dict[Path, list[m.Infra.RopeModuleIndexEntry]],
```

**Decisão**:

### 83 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_analysis_workspace.py:171` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
      167              package_dirs,
      168          )
      169  
      170      @classmethod
>>>   171      def index_rope_workspace(
      172          cls, rope_project: t.Infra.RopeProject, workspace_root: Path
      173      ) -> m.Infra.RopeWorkspaceIndex:
      174          """Build a generic Rope workspace index for package-oriented planning."""
      175          resolved_root = workspace_root.resolve()
```

**Decisão**:

### 84 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_helpers.py:63` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
       59          if hook not in cls._post_hooks:
       60              cls._post_hooks.append(hook)
       61  
       62      @staticmethod
>>>    63      def get_module_level_assignments(source: str) -> t.StrPairSequence:
       64          """Return (name, value_str) for module-level simple assignments."""
       65          assignment_pattern = c.Infra.MODULE_ASSIGNMENT_RE
       66          results: list[t.StrPair] = []
       67          scope_depth = 0
```

**Decisão**:

### 85 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_helpers.py:155` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      151          updated_source: str = pattern.sub("", source, count=1)
      152          return updated_source
      153  
      154      @staticmethod
>>>   155      def append_to_class_body(source: str, class_name: str, block: str) -> str:
      156          """Append a block of code to an existing class body."""
      157          if not c.Infra.compile_class_header_search(class_name).search(source):
      158              return source.rstrip("\n") + f"\n\nclass {class_name}:\n{block}\n"
      159          lines = source.splitlines(keepends=True)
```

**Decisão**:

### 86 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:115` · **Effort**: 17min

> Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed.

```python
      111              return Path(path)
      112          return None
      113  
      114      @staticmethod
>>>   115      def indexed_search_resources(
      116          rope_workspace: p.AttributeProbe,
      117          *,
      118          resource: t.Infra.RopeResource,
      119          name: str,
```

**Decisão**:

### 87 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:224` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
      220              rope_project.do(changes)
      221          return r[bool].ok(changed)
      222  
      223      @classmethod
>>>   224      def normalize_imports(
      225          cls,
      226          rope_project: t.Infra.RopeProject,
      227          *,
      228          file_paths: t.SequenceOf[Path],
```

**Decisão**:

### 88 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:290` · **Effort**: 17min

> Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed.

```python
      286              return r[bool].fail(format_result.error or "ruff format failed")
      287          return r[bool].ok(rope_changed)
      288  
      289      @classmethod
>>>   290      def _collect_canonical_alias_imports(
      291          cls, rope_project: t.Infra.RopeProject, file_paths: t.SequenceOf[Path]
      292      ) -> dict[Path, list[tuple[str, tuple[str, ...]]]]:
      293          """Collect canonical runtime-alias imports eligible for semantic restore."""
      294          runtime_aliases = u.runtime_alias_names(c.Infra.PKG_INFRA_UNDERSCORE)
```

**Decisão**:

### 89 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:372` · **Effort**: 28min

> Refactor this function to reduce its Cognitive Complexity from 38 to the 15 allowed.

```python
      368                  )
      369          return r[frozenset[str]].ok(frozenset(referenced))
      370  
      371      @classmethod
>>>   372      def _ensure_canonical_alias_imports(
      373          cls,
      374          rope_project: t.Infra.RopeProject,
      375          collected: dict[Path, list[tuple[str, tuple[str, ...]]]],
      376      ) -> p.Result[bool]:
```

**Decisão**:

### 90 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:531` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      527              resource.write(updated_source)
      528          return updated_source
      529  
      530      @staticmethod
>>>   531      def _strip_aliases_from_source_imports(
      532          module_imports: t.Infra.RopeModuleImports,
      533          *,
      534          source_module: str,
      535          target_module: str,
```

**Decisão**:

### 91 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:642` · **Effort**: 34min

> Refactor this function to reduce its Cognitive Complexity from 44 to the 15 allowed.

```python
      638              return source
      639          return rewritten_source
      640  
      641      @classmethod
>>>   642      def collapse_submodule_alias_imports(
      643          cls,
      644          rope_project: t.Infra.RopeProject,
      645          resource: t.Infra.RopeResource,
      646          *,
```

**Decisão**:

### 92 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_imports.py:791` · **Effort**: 19min

> Refactor this function to reduce its Cognitive Complexity from 29 to the 15 allowed.

```python
      787              resource.write(updated)
      788          return updated
      789  
      790      @staticmethod
>>>   791      def rewrite_private_import_bypass_violations(
      792          rope_project: t.Infra.RopeProject,
      793          violations: t.SequenceOf[m.Infra.PrivateImportBypassViolation],
      794          parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation],
      795          *,
```

**Decisão**:

### 93 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_inventory.py:311` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
      307          validated_scope: p.Infra.RopeScopeDsl = candidate
      308          return validated_scope
      309  
      310      @staticmethod
>>>   311      def _kind_for(
      312          pyname: t.Infra.RopePyName,
      313          *,
      314          class_chain: t.StrSequence,
      315          scope_chain: t.StrSequence,
```

**Decisão**:

### 94 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_inventory.py:355` · **Effort**: 20min

> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

```python
      351                  result = "assignment"
      352          return result
      353  
      354      @staticmethod
>>>   355      def _reference_sites(
      356          rope_project: t.Infra.RopeProject,
      357          resource: t.Infra.RopeResource,
      358          *,
      359          source: str,
```

**Decisão**:

### 95 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_inventory.py:472` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
      468              script_reference_sites.extend(fallback_script_reference_sites)
      469          return (tuple(runtime_reference_sites), tuple(script_reference_sites))
      470  
      471      @staticmethod
>>>   472      def _fallback_reference_sites_from_index(
      473          rope_workspace: p.AttributeProbe,
      474          *,
      475          definition_path: Path,
      476          module_name: str,
```

**Decisão**:

### 96 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_mro_transform.py:23` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       19  class FlextInfraUtilitiesRopeMroTransform:
       20      """Move module-level constants into the constants facade class."""
       21  
       22      @staticmethod
>>>    23      def migrate_file(
       24          *, scan_result: m.Infra.MROScanReport
       25      ) -> tuple[str, m.Infra.MROFileMigration, t.StrMapping]:
       26          """Transform a candidate file and return code plus symbol map."""
       27          source = Path(scan_result.file).read_text(encoding=c.Cli.ENCODING_DEFAULT)
```

**Decisão**:

### 97 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/_utilities/rope_runtime_types.py:97` · **Effort**: 10min

> Define a constant instead of duplicating this literal "rope.base.exceptions" 5 times.

```python
       93      def rope_syntax_errors(cls) -> tuple[type[BaseException], ...]:
       94          """Return exceptions that signal unparseable Python source."""
       95          return (
       96              SyntaxError,
>>>    97              cls._exception_type("rope.base.exceptions", "ModuleSyntaxError"),
       98          )
       99  
      100      @classmethod
      101      def rope_runtime_errors(cls) -> tuple[type[BaseException], ...]:
```

**Decisão**:

### 98 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_source.py:54` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
       50              and "-" not in entry.name
       51          ]
       52  
       53      @staticmethod
>>>    54      def find_import_insert_position(
       55          lines: t.StrSequence, *, past_existing: bool = True
       56      ) -> int:
       57          """Find a line index for inserting imports, never inside a docstring.
       58  
```

**Decisão**:

### 99 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_structure.py:111` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      107              project_name=ctx.project_name,
      108          )
      109  
      110      @classmethod
>>>   111      def evaluate_static_rules(
      112          cls,
      113          *,
      114          source: str,
      115          module_imports: t.Infra.RopeModuleImports,
```

**Decisão**:

### 100 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_structure.py:169` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      165                          violations = (*violations, violation)
      166          return violations
      167  
      168      @classmethod
>>>   169      def _rule_matches(
      170          cls,
      171          *,
      172          rule: m.Infra.StaticRuleSpec,
      173          statement: m.Infra.LogicalStatement,
```

**Decisão**:

### 101 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/rope_structure.py:441` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      437              else c.Infra.StatementCategory.OTHER
      438          )
      439  
      440      @staticmethod
>>>   441      def _assignment_head(stripped: str) -> str | None:
      442          """Return the target side of a top-level assignment."""
      443          depth = 0
      444          quote = ""
      445          for index, char in enumerate(stripped):
```

**Decisão**:

### 102 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_common.py:36` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       32          if primary.failure:
       33              return r[Path].fail(primary.error or "failed to resolve primary worktree")
       34          return r[Path].ok(primary.value.primary_root)
       35  
>>>    36      def _resolve_integration_base(self, primary_root: Path) -> p.Result[str]:
       37          explicit = (self.base or "").strip()
       38          if explicit:
       39              return r.ok(explicit)
       40          cursor = primary_root.resolve()
```

**Decisão**:

### 103 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_common.py:98` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       94      @staticmethod
       95      def _branch_name(kind: c.Infra.WorkKind, slug: str) -> str:
       96          return f"{kind.value}/{slug}"
       97  
>>>    98      def _resolve_lane_branch(self) -> p.Result[str]:
       99          explicit = (self.branch or "").strip()
      100          if explicit:
      101              return r.ok(explicit)
      102          bead = (self.bead or "").strip()
```

**Decisão**:

### 104 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_finish.py:22` · **Effort**: 29min

> Refactor this function to reduce its Cognitive Complexity from 39 to the 15 allowed.

```python
       18      """Finish step for the public work saga."""
       19  
       20      apply_changes: bool
       21  
>>>    22      def _finish(self, primary_root: Path) -> p.Result[str]:
       23          if not self.apply_changes:
       24              return r.fail("work finish requires --apply")
       25          bead = (self.bead or "").strip()
       26          if not bead:
```

**Decisão**:

### 105 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_finish.py:122` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      118          )
      119          return r.ok(f"FINISHED BRANCH={branch} WORKTREE={worktree}\n{receipt}")
      120  
      121      @staticmethod
>>>   122      def _require_merged_pr(
      123          primary_root: Path, branch: str, pr_number: str
      124      ) -> p.Result[bool]:
      125          """Refuse to retire a lane whose pull request is not merged."""
      126          if not pr_number:
```

**Decisão**:

### 106 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_publish.py:46` · **Effort**: 43min

> Refactor this function to reduce its Cognitive Complexity from 53 to the 15 allowed.

```python
       42          if not rows:
       43              return r.fail(f"no open PR for head {branch}")
       44          return r.ok((str(rows[0].get("number", "")), str(rows[0].get("url", ""))))
       45  
>>>    46      def _land(self, primary_root: Path) -> p.Result[str]:
       47          if not self.apply_changes:
       48              return r.fail("work land requires --apply")
       49          bead = (self.bead or "").strip()
       50          if not bead:
```

**Decisão**:

### 107 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_start.py:57` · **Effort**: 20min

> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

```python
       53                  f"{removed.error or 'unknown worktree removal failure'}"
       54              )
       55          return f"{reason}; lane {branch} rolled back"
       56  
>>>    57      def _start(self, primary_root: Path) -> p.Result[str]:
       58          if not self.apply_changes:
       59              return r.fail("work start requires --apply")
       60          bead = (self.bead or "").strip()
       61          if not bead:
```

**Decisão**:

### 108 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/work_saga_start.py:160` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
      156              f"LANE_ID={bead} BRANCH={branch} WORKTREE={lane} "
      157              f"BASE={base.value} HEAD={head.value}\n{receipt}"
      158          )
      159  
>>>   160      def _status(self, primary_root: Path) -> p.Result[str]:
      161          bead = (self.bead or "").strip()
      162          branch_result = self._resolve_lane_branch()
      163          branch = branch_result.value if branch_result.success else (self.branch or "")
      164          lines: list[str] = ["work status"]
```

**Decisão**:

### 109 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/workspace_fingerprint.py:66` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
       62          except OSError as exc:
       63              return r[bytes].fail(f"workspace fingerprint read failed for {path}: {exc}")
       64  
       65      @classmethod
>>>    66      def workspace_fingerprint(
       67          cls, checkout: Path, *, excluded_paths: t.SequenceOf[Path] = ()
       68      ) -> p.Result[m.Infra.WorkspaceFingerprint]:
       69          """Capture a content-addressed snapshot of one Git checkout."""
       70          root = checkout.resolve()
```

**Decisão**:

### 110 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/worktree_transaction.py:85` · **Effort**: 27min

> Refactor this function to reduce its Cognitive Complexity from 37 to the 15 allowed.

```python
       81          )
       82          return r[t.SequenceOf[Path]].ok(paths)
       83  
       84      @classmethod
>>>    85      def _create_complete_worktree(
       86          cls,
       87          workspace_root: Path,
       88          worktree_root: Path,
       89          transaction_id: str,
```

**Decisão**:

### 111 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/_utilities/worktree_transaction.py:743` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
      739              )
      740          return report_result
      741  
      742      @classmethod
>>>   743      def _execute_isolated(
      744          cls,
      745          request: m.Infra.WorktreeTransactionRequest,
      746          *,
      747          transaction_id: str,
```

**Decisão**:

### 112 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/check/workspace_check_gates.py:230` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      226      # ------------------------------------------------------------------
      227      # Pipeline stage helpers
      228      # ------------------------------------------------------------------
      229  
>>>   230      def _make_gate_handler(
      231          self,
      232          gate_instance: FlextInfraGate,
      233          project_dir: Path,
      234          ctx: m.Infra.GateContext,
```

**Decisão**:

### 113 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/_lazy_init_generation.py:34` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
       30      if TYPE_CHECKING:
       31          workspace_root: Path
       32          _modified_files: t.Infra.StrSet
       33  
>>>    34      def _generate_all_inits(
       35          self,
       36          pkg_dirs: t.SequenceOf[Path],
       37          *,
       38          check_only: bool,
```

**Decisão**:

### 114 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/_lazy_init_generation_registry.py:38` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
       34              )
       35              return -1
       36          return 0
       37  
>>>    38      def _remove_obsolete_root_support(
       39          self, plan: m.Infra.LazyInitPlan, *, check_only: bool = False
       40      ) -> None:
       41          """Remove closed, preflighted root registries superseded by inline maps."""
       42          context = plan.context
```

**Decisão**:

### 115 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/_lazy_init_planner_aliases.py:107` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      103                  # mro-pulj (codex): the generated root TYPE_CHECKING contract
      104                  # makes the public package itself the single inherited owner.
      105                  lazy_map[alias_name] = (package_name, alias_name)
      106  
>>>   107      def _resolve_local_aliases(
      108          self, lazy_map: t.MutableLazyAliasMap, *, current_pkg: str, pkg_dir: Path
      109      ) -> None:
      110          """Inject public_file_aliases from the lazy-init config into the lazy map."""
      111          alias_to_files: dict[str, list[str]] = {}
```

**Decisão**:

### 116 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/_lazy_init_planner_children.py:30` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       26  
       27          @staticmethod
       28          def _publish(name: str, *, allow_main: bool) -> bool: ...
       29  
>>>    30      def _merge_children(
       31          self,
       32          pkg_dir: Path,
       33          lazy_map: t.MutableLazyAliasMap,
       34          dir_exports: t.MappingKV[str, t.LazyAliasMap],
```

**Decisão**:

### 117 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/_lazy_init_planner_exports.py:40` · **Effort**: 17min

> Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed.

```python
       36  
       37          @staticmethod
       38          def _publish(name: str, *, allow_main: bool) -> bool: ...
       39  
>>>    40      def _package_exports(
       41          self, context: m.Infra.LazyInitPackageContext
       42      ) -> t.MutableLazyAliasMap:
       43          """Return the lazy export map for a package (excluding child packages)."""
       44          if self._is_private_test_fixture_package(context.pkg_dir, context.surface):
```

**Decisão**:

### 118 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:96` · **Effort**: 25min

> Refactor this function to reduce its Cognitive Complexity from 35 to the 15 allowed.

```python
       92          )
       93          return service.execute()
       94  
       95      @override
>>>    96      def execute(self) -> p.Result[m.Infra.CodegenResult]:
       97          """Run check or apply and require a verified fixed point."""
       98          request = self.request or m.Infra.CodegenConformRequest(
       99              root=self.workspace_root
      100          )
```

**Decisão**:

### 119 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:202` · **Effort**: 48min

> Refactor this function to reduce its Cognitive Complexity from 58 to the 15 allowed.

```python
      198          return r[m.Infra.CodegenResult].ok(
      199              m.Infra.CodegenResult(plan=verified_plan, written_files=tuple(written))
      200          )
      201  
>>>   202      def plan(
      203          self, request: m.Infra.CodegenConformRequest
      204      ) -> p.Result[m.Infra.CodegenPlan]:
      205          """Build and validate the complete selection without writing."""
      206          config_spec = config.Infra.codegen
```

**Decisão**:

### 120 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:479` · **Effort**: 45min

> Refactor this function to reduce its Cognitive Complexity from 55 to the 15 allowed.

```python
      475              )
      476          )
      477  
      478      @staticmethod
>>>   479      def _complete_governed_plans(
      480          root: Path,
      481          planned: t.SequenceOf[m.Infra.CodegenFilePlan],
      482          codegen: m.Infra.CodegenConfigSpec,
      483          contract: m.Infra.CodegenConformSurfaceContract,
```

**Decisão**:

### 121 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:530` · **Effort**: 6min

> Define a constant instead of duplicating this literal ".github" 3 times.

```python
      526                  if profile not in allowed:
      527                      # Why: profile-excluded managed workflows must not survive as
      528                      # "keep current" ghosts (ci-matrix on workspace-member).
      529                      if (
>>>   530                          relative.parts[:2] == (".github", "workflows")
      531                          and path.is_file()
      532                      ):
      533                          orphan_read = u.Cli.files_read_text(path)
      534                          if orphan_read.failure:
```

**Decisão**:

### 122 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:653` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      649              codegen, profile=profile, project_name=project_name, workspace=workspace
      650          )
      651  
      652      @staticmethod
>>>   653      def _render_gitignore(
      654          codegen: m.Infra.CodegenConfigSpec,
      655          *,
      656          profile: c.Infra.MakeProfile,
      657          project_name: str | None = None,
```

**Decisão**:

### 123 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:788` · **Effort**: 1h15min

> Refactor this function to reduce its Cognitive Complexity from 85 to the 15 allowed.

```python
      784              for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
      785              if directory in generated_roots
      786          )
      787  
>>>   788      def _plan_scaffold_repository(
      789          self,
      790          *,
      791          root: Path,
      792          repository: m.Infra.RepositoryRef,
```

**Decisão**:

### 124 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:1039` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
     1035              )
     1036          planned.append(pyproject_plan.value)
     1037          return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
     1038  
>>>  1039      def _plan_existing_repository(
     1040          self,
     1041          *,
     1042          root: Path,
     1043          workspace_root: Path,
```

**Decisão**:

### 125 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:1196` · **Effort**: 57min

> Refactor this function to reduce its Cognitive Complexity from 67 to the 15 allowed.

```python
     1192                  )
     1193              planned.extend(custom_result.value)
     1194          return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
     1195  
>>>  1196      def _plan_existing_templates(
     1197          self,
     1198          *,
     1199          root: Path,
     1200          repository: m.Infra.RepositoryRef,
```

**Decisão**:

### 126 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:1367` · **Effort**: 20min

> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

```python
     1363              changed=True,
     1364              absent=True,
     1365          )
     1366  
>>>  1367      def _plan_ast_grep_surfaces(
     1368          self,
     1369          *,
     1370          root: Path,
     1371          codegen: m.Infra.CodegenConfigSpec,
```

**Decisão**:

### 127 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:1564` · **Effort**: 26min

> Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed.

```python
     1560          workspace_root_rel = FlextInfraCodegenConform._workspace_root_rel(workspace)
     1561          local_path: Path = local.path
     1562          return (Path(workspace_root_rel) / local_path).as_posix()
     1563  
>>>  1564      def _artifact_render_context(
     1565          self,
     1566          *,
     1567          dist: str,
     1568          repository: m.Infra.RepositoryRef,
```

**Decisão**:

### 128 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:1688` · **Effort**: 6min

> Define a constant instead of duplicating this literal "infrastructure CLI repository resolution failed" 3 times.

```python
     1684              infra_repository = self._infra_repository(workspace)
     1685              if infra_repository.failure:
     1686                  return r[p.Model].fail(
     1687                      infra_repository.error
>>>  1688                      or "infrastructure CLI repository resolution failed"
     1689                  )
     1690              infra_provider = self._repository_provider(infra_repository.value, codegen)
     1691              if infra_provider.failure:
     1692                  return r[p.Model].fail(
```

**Decisão**:

### 129 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:1693` · **Effort**: 6min

> Define a constant instead of duplicating this literal "infrastructure provider resolution failed" 3 times.

```python
     1689                  )
     1690              infra_provider = self._repository_provider(infra_repository.value, codegen)
     1691              if infra_provider.failure:
     1692                  return r[p.Model].fail(
>>>  1693                      infra_provider.error or "infrastructure provider resolution failed"
     1694                  )
     1695              gitlinks = self._managed_gitlinks(workspace, codegen)
     1696              if gitlinks.failure:
     1697                  return r[p.Model].fail(
```

**Decisão**:

### 130 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:1698` · **Effort**: 6min

> Define a constant instead of duplicating this literal "managed Gitlink resolution failed" 3 times.

```python
     1694                  )
     1695              gitlinks = self._managed_gitlinks(workspace, codegen)
     1696              if gitlinks.failure:
     1697                  return r[p.Model].fail(
>>>  1698                      gitlinks.error or "managed Gitlink resolution failed"
     1699                  )
     1700              return r[p.Model].ok(
     1701                  m.Infra.MakefileRenderSpec(
     1702                      pytest=config.Infra.tooling.tools.pytest,
```

**Decisão**:

### 131 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:1833` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
     1829              )
     1830          )
     1831  
     1832      @staticmethod
>>>  1833      def _project_render_context(
     1834          repository: m.Infra.RepositoryRef,
     1835          target: m.Infra.RepositoryConformTarget,
     1836          workspace: m.Infra.WorkspaceSpec,
     1837          codegen: m.Infra.CodegenConfigSpec,
```

**Decisão**:

### 132 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:2078` · **Effort**: 41min

> Refactor this function to reduce its Cognitive Complexity from 51 to the 15 allowed.

```python
     2074              ),
     2075          ))
     2076  
     2077      @staticmethod
>>>  2078      def validate_custom_make(
     2079          content: str, policy: m.Infra.CustomHandlerPolicy
     2080      ) -> p.Result[bool]:
     2081          """Reject public targets, aliases, includes, and toolchain declarations."""
     2082          target_re = re.compile(policy.target_pattern)
```

**Decisão**:

### 133 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:2207` · **Effort**: 59min

> Refactor this function to reduce its Cognitive Complexity from 69 to the 15 allowed.

```python
     2203              for pattern in patterns
     2204          )
     2205  
     2206      @classmethod
>>>  2207      def _branch_ancestry_plan(
     2208          cls, target: m.Infra.RepositoryConformTarget
     2209      ) -> p.Result[m.Infra.BranchAncestryPlan]:
     2210          """Inventory governed refs and prove descent from the provider baseline."""
     2211          root = target.root
```

**Decisão**:

### 134 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:2539` · **Effort**: 6min

> Define a constant instead of duplicating this literal "config.yaml" 3 times.

```python
     2535          rejecting the declared one inverted the SSOT. The file is parsed at
     2536          this boundary into a validated model — absence and an invalid payload
     2537          are failures the caller decides about, never a substituted string.
     2538          """
>>>  2539          config_path = repository_root / ".beads" / "config.yaml"
     2540          if not config_path.is_file():
     2541              return r[m.Infra.BeadsTrackerDeclaration].fail(
     2542                  f"repository declares no Beads tracker: {config_path}"
     2543              )
```

**Decisão**:

### 135 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/codegen/conform.py:2539` · **Effort**: 8min

> Define a constant instead of duplicating this literal ".beads" 4 times.

```python
     2535          rejecting the declared one inverted the SSOT. The file is parsed at
     2536          this boundary into a validated model — absence and an invalid payload
     2537          are failures the caller decides about, never a substituted string.
     2538          """
>>>  2539          config_path = repository_root / ".beads" / "config.yaml"
     2540          if not config_path.is_file():
     2541              return r[m.Infra.BeadsTrackerDeclaration].fail(
     2542                  f"repository declares no Beads tracker: {config_path}"
     2543              )
```

**Decisão**:

### 136 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/conform.py:2575` · **Effort**: 17min

> Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed.

```python
     2571              return prefix.strip()
     2572          return fallback
     2573  
     2574      @classmethod
>>>  2575      def _verify_beads_plan(
     2576          cls, plan: m.Infra.BeadsPlan, *, allow_missing: bool
     2577      ) -> p.Result[bool]:
     2578          """Validate the principal ledger route and fail closed on disagreement.
     2579  
```

**Decisão**:

### 137 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/consolidator.py:26` · **Effort**: 21min

> Refactor this function to reduce its Cognitive Complexity from 31 to the 15 allowed.

```python
       22          m.Field(alias="project", description="Single project to consolidate"),
       23      ] = None
       24  
       25      @override
>>>    26      def execute(self) -> p.Result[str]:
       27          """Execute constants consolidation with normalized command context."""
       28          output_lines: t.MutableSequenceOf[str] = (
       29              ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
       30          )
```

**Decisão**:

### 138 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/layout.py:33` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       29          str | None, m.Field(alias="project", description="Single project to conform")
       30      ] = None
       31  
       32      @override
>>>    33      def execute(self) -> p.Result[str]:
       34          """Run check (default) or apply across the selected projects."""
       35          selected = self._project_dirs()
       36          if selected.failure:
       37              return r[str].fail(selected.error or "project selection failed")
```

**Decisão**:

### 139 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/lazy_init.py:236` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
      232          )
      233          return 1
      234  
      235      @staticmethod
>>>   236      def _detect_duplicate_class_names(
      237          rope: FlextInfraRopeWorkspace, *, package_dirs: t.SequenceOf[Path]
      238      ) -> t.MappingKV[str, t.StrSequence]:
      239          """Return class-name collisions.
      240  
```

**Decisão**:

### 140 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/managed_conflicts.py:16` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       12  
       13      _TOML_SECTION_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
       14  
       15      @classmethod
>>>    16      def recover_toml(
       17          cls, content: str, *, conflict_sections: t.StrSequence
       18      ) -> p.Result[str]:
       19          """Choose the current projection inside configured TOML sections only."""
       20          if "<<<<<<< " not in content:
```

**Decisão**:

### 141 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/py_typed.py:37` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       33          """Execute ``py.typed`` synchronization from the validated CLI model."""
       34          self.run(check_only=self.check_only)
       35          return r[bool].ok(True)
       36  
>>>    37      def run(self, *, check_only: bool = False) -> int:
       38          """Ensure ``py.typed`` markers exist in every package directory.
       39  
       40          Args:
       41              check_only: If True, only report changes without writing.
```

**Decisão**:

### 142 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codegen/version_file.py:42` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
       38      workspace member list.  No manual directory iteration.
       39      """
       40  
       41      @override
>>>    42      def execute(self) -> p.Result[bool]:
       43          """Generate __version__.py for each discovered project."""
       44          # NOTE (multi-agent, mro-p4s3.2 / agent: uv_overlay_owner): the exact
       45          # source metadata model crosses the sole CLI rendering boundary.
       46          template_path = (
```

**Decisão**:

### 143 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/codemod/rules/refactor/apply_renames.py:136` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      132              tuple(lines),
      133          ))
      134  
      135      @staticmethod
>>>   136      def _apply(
      137          files: t.SequenceOf[Path],
      138          roots: t.SequenceOf[Path],
      139          pairs: t.SequenceOf[tuple[str, str]],
      140      ) -> p.Result[bool]:
```

**Decisão**:

### 144 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/_detection_runners.py:47` · **Effort**: 24min

> Refactor this function to reduce its Cognitive Complexity from 34 to the 15 allowed.

```python
       43          _ = cmd, cwd, timeout, env
       44          msg = "_run_raw must be implemented by the concrete analyzer"
       45          raise NotImplementedError(msg)
       46  
>>>    47      def run_deptry(
       48          self,
       49          project_path: Path,
       50          venv_bin: Path,
       51          *,
```

**Decisão**:

### 145 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/_extra_paths_sync.py:151` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
      147                      write_result.error or f"failed to write {pyproject_path}"
      148                  )
      149          return r[bool].ok(bool(changes))
      150  
>>>   151      def sync_extra_paths(
      152          self, *, dry_run: bool = False, project_dirs: t.SequenceOf[Path] | None = None
      153      ) -> p.Result[int]:
      154          """Synchronize extraPaths and mypy_path across projects."""
      155          if project_dirs:
```

**Decisão**:

### 146 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/_modernizer_constraints.py:73` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       69                  f"{location}.{dependency_name}: {current_value!r} -> {rewritten_value!r}"
       70              )
       71          return tuple(changes)
       72  
>>>    73      def _rewrite_dependency_constraints_payload(
       74          self,
       75          payload: t.MutableJsonMapping,
       76          *,
       77          locked_versions: t.MappingKV[str, str],
```

**Decisão**:

### 147 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/_modernizer_document.py:189` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      185                  value.strip() == c.Infra.MakeProfile.WORKSPACE_MEMBER.value
      186              )
      187          return r[bool].ok(False)
      188  
>>>   189      def _process_document_state(
      190          self,
      191          state: m.Infra.PyprojectDocumentState,
      192          *,
      193          canonical_dev: t.StrSequence,
```

**Decisão**:

### 148 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/_modernizer_run.py:76` · **Effort**: 1h18min

> Refactor this function to reduce its Cognitive Complexity from 88 to the 15 allowed.

```python
       72              skip_comments=skip_comments,
       73              rewrite_constraints=False,
       74          )
       75  
>>>    76      def run(self) -> int:
       77          """Run pyproject modernization for the workspace."""
       78          check_mode = self.audit or self.check_only
       79          dry_run = check_mode or self.effective_dry_run
       80          project_names = list(self.project_names or [])
```

**Decisão**:

### 149 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/detection.py:52` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
       48              return self.runner.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
       49          return u.Cli.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
       50  
       51      @staticmethod
>>>    52      def classify_issues(
       53          issues: t.SequenceOf[t.JsonMapping],
       54      ) -> m.Infra.DeptryIssueGroups:
       55          """Classify deptry issues by error code (DEP001-DEP004)."""
       56          groups = m.Infra.DeptryIssueGroups(dep001=[], dep002=[], dep003=[], dep004=[])
```

**Decisão**:

### 150 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/detection_analysis.py:36` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
       32              normalized[key] = converted
       33          return normalized
       34  
       35      @staticmethod
>>>    36      def to_infra_value(value: t.Infra.InfraValue | None) -> t.Infra.InfraValue | None:
       37          """Convert container value to namespaced infra value."""
       38          if value is None:
       39              return None
       40          if isinstance(value, t.PRIMITIVES_TYPES):
```

**Decisão**:

### 151 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/detector_runtime.py:36` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
       32          self._workspace_report_factory = workspace_report_factory
       33          self._dependency_limits_factory = dependency_limits_factory
       34          self._pip_check_factory = pip_check_factory
       35  
>>>    36      def run(self, params: m.Infra.DetectCommand) -> p.Result[bool]:
       37          """Execute dependency detection and generate workspace report (orchestrator)."""
       38          detector = self._detector
       39          root = params.workspace_path
       40          venv_bin = root / c.Infra.VENV_BIN_REL
```

**Decisão**:

### 152 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/fix_pyrefly_config.py:52` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
       48          if fix_result.failure:
       49              return r[bool].fail(fix_result.error or "pyrefly config fix failed")
       50          return r[bool].ok(True)
       51  
>>>    52      def process_file(
       53          self, path: Path, *, dry_run: bool = False
       54      ) -> p.Result[t.StrSequence]:
       55          """Process one pyproject.toml file and apply fixes."""
       56          document_result = u.Cli.toml_read_document(path)
```

**Decisão**:

### 153 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/fix_pyrefly_config.py:122` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      118                      write_result.error or f"failed to write {path}"
      119                  )
      120          return r[t.StrSequence].ok(all_fixes)
      121  
>>>   122      def run(
      123          self, projects: t.StrSequence, *, dry_run: bool = False, verbose: bool = False
      124      ) -> p.Result[t.StrSequence]:
      125          """Run pyrefly configuration fixes for selected projects."""
      126          project_paths = [
```

**Decisão**:

### 154 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/modernizer.py:101` · **Effort**: 26min

> Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed.

```python
       97                  changes[0] if changes else f"pyproject tooling render failed: {path}"
       98              )
       99          return r[str].ok(state.rendered)
      100  
>>>   101      def resolve_tooling_context(
      102          self,
      103          *,
      104          project_name: t.NonEmptyStr,
      105          package_name: t.NonEmptyStr,
```

**Decisão**:

### 155 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/phases/consolidate_groups.py:11` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
        7  
        8  class FlextInfraConsolidateGroupsPhase:
        9      """Consolidate optional-dependencies and Poetry groups into single dev group."""
       10  
>>>    11      def apply(
       12          self, doc: t.Cli.TomlDocument, canonical_dev: t.StrSequence
       13      ) -> t.StrSequence:
       14          """Merge all legacy optional groups into canonical ``project.optional-dependencies.dev``."""
       15          changes: t.MutableSequenceOf[str] = []
```

**Decisão**:

### 156 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/phases/consolidate_groups.py:75` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       71              deptry["pep621_dev_dependency_groups"] = u.Cli.toml_array([c.Infra.DEV])
       72              changes.append("tool.deptry.pep621_dev_dependency_groups set to ['dev']")
       73          return changes
       74  
>>>    75      def apply_payload(
       76          self, payload: t.MutableJsonMapping, canonical_dev: t.StrSequence
       77      ) -> t.StrSequence:
       78          """Merge legacy groups into one canonical dev group in one plain payload."""
       79          changes: t.MutableSequenceOf[str] = []
```

**Decisão**:

### 157 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/phases/ensure_pyright.py:378` · **Effort**: 22min

> Refactor this function to reduce its Cognitive Complexity from 32 to the 15 allowed.

```python
      374              for env_dir in u.Infra.discover_python_dirs(child_project):
      375                  includes.append((relative_root / env_dir).as_posix())
      376          return includes
      377  
>>>   378      def _phase(
      379          self,
      380          *,
      381          is_root: bool,
      382          workspace_root: Path | None = None,
```

**Decisão**:

### 158 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/deps/phases/inject_comments.py:89` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
       85                  return marker
       86          return None
       87  
       88      @classmethod
>>>    89      def _strip_managed_lines(
       90          cls, lines: t.StrSequence
       91      ) -> t.Pair[t.StrSequence, t.StrSequence]:
       92          """Strip managed lines."""
       93          changes: t.MutableSequenceOf[str] = []
```

**Decisão**:

### 159 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/class_placement_detector.py:321` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      317              name=target_name, line=line if isinstance(line, int) and line > 0 else 1
      318          )
      319  
      320      @staticmethod
>>>   321      def _type_aliases(
      322          rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
      323      ) -> t.SequenceOf[tuple[str, int]]:
      324          """Return module-level type aliases as (name, line) pairs."""
      325          try:
```

**Decisão**:

### 160 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/compatibility_alias_detector.py:42` · **Effort**: 26min

> Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed.

```python
       38              return "rewrite_foreign_canonical_alias"
       39          return "rewrite_compatibility_alias"
       40  
       41      @classmethod
>>>    42      def detect_file(
       43          cls, ctx: m.Infra.DetectorContext
       44      ) -> t.SequenceOf[m.Infra.CompatibilityAliasViolation]:
       45          """Detect compatibility aliases in a single file.
       46  
```

**Decisão**:

### 161 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/compatibility_alias_detector.py:141` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      137          )
      138          return violations
      139  
      140      @classmethod
>>>   141      def _detect_foreign_canonical_aliases(
      142          cls, *, ctx: m.Infra.DetectorContext, source: str, file_path: Path
      143      ) -> t.SequenceOf[m.Infra.CompatibilityAliasViolation]:
      144          """Detect runtime canonical aliases imported from ``flext_core``."""
      145          current_module = u.Infra.package_name(file_path)
```

**Decisão**:

### 162 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/cyclic_import_detector.py:23` · **Effort**: 13min

> Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed.

```python
       19  class FlextInfraCyclicImportDetector:
       20      """Detect cyclic imports at project level via rope semantic import resolution."""
       21  
       22      @staticmethod
>>>    23      def scan_project(
       24          *,
       25          project_root: Path,
       26          rope_project: t.Infra.RopeProject,
       27          _parse_failures: t.SequenceOf[m.Infra.ParseFailureViolation] | None = None,
```

**Decisão**:

### 163 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/inline_import_detector.py:34` · **Effort**: 47min

> Refactor this function to reduce its Cognitive Complexity from 57 to the 15 allowed.

```python
       30              return "rewrite_library_abstraction"
       31          return "manual"
       32  
       33      @classmethod
>>>    34      def detect_file(
       35          cls, ctx: m.Infra.DetectorContext
       36      ) -> t.SequenceOf[m.Infra.InlineImportViolation]:
       37          """Return Rope-resolved inline imports and dynamic import calls."""
       38          file_path = ctx.file_path
```

**Decisão**:

### 164 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/loose_object_detector.py:22` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
       18  class FlextInfraLooseObjectDetector:
       19      """Detect loose top-level objects outside namespace classes via rope."""
       20  
       21      @classmethod
>>>    22      def detect_file(
       23          cls, ctx: m.Infra.DetectorContext
       24      ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
       25          """Detect loose top-level objects in a single file."""
       26          if ctx.project_root is not None and not cls._is_src_file(
```

**Decisão**:

### 165 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/mro_completeness_detector.py:21` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
       17  class FlextInfraMROCompletenessDetector:
       18      """Detect facade classes missing MRO bases via rope."""
       19  
       20      @staticmethod
>>>    21      def detect_file(
       22          ctx: m.Infra.DetectorContext,
       23      ) -> t.SequenceOf[m.Infra.MROCompletenessViolation]:
       24          """Detect missing MRO bases: expected - declared = violations."""
       25          file_path = ctx.file_path
```

**Decisão**:

### 166 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/mro_shape_detector.py:434` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      430              if (base_name := u.Infra.class_base_name(base))
      431          )
      432  
      433      @staticmethod
>>>   434      def _build_parent_map(tree: object) -> dict[int, object]:
      435          """Map child node id -> parent node for the full module AST."""
      436          parent_map: dict[int, object] = {}
      437          stack: list[object] = [tree]
      438          while stack:
```

**Decisão**:

### 167 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/mro_shape_detector.py:453` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      449                      stack.append(value)
      450          return parent_map
      451  
      452      @staticmethod
>>>   453      def _collect_class_nodes(
      454          tree: object, parent_map: dict[int, object]
      455      ) -> t.SequenceOf[tuple[object, str]]:
      456          """Return every ClassDef node with its dotted qualname."""
      457          result: list[tuple[object, str]] = []
```

**Decisão**:

### 168 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/mro_shape_detector.py:500` · **Effort**: 25min

> Refactor this function to reduce its Cognitive Complexity from 35 to the 15 allowed.

```python
      496                      return False
      497          return True
      498  
      499      @staticmethod
>>>   500      def _class_body_uses_name(node: object, name: str) -> bool:
      501          """Return True when a method body references ``name`` as a name/attribute."""
      502          body = getattr(node, "body", ())
      503          if not isinstance(body, (list, tuple)):
      504              return False
```

**Decisão**:

### 169 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/namespace_source_detector.py:21` · **Effort**: 35min

> Refactor this function to reduce its Cognitive Complexity from 45 to the 15 allowed.

```python
       17  class FlextInfraNamespaceSourceDetector:
       18      """Detect alias imports from wrong source packages."""
       19  
       20      @staticmethod
>>>    21      def detect_file(
       22          ctx: m.Infra.DetectorContext,
       23      ) -> t.SequenceOf[m.Infra.NamespaceSourceViolation]:
       24          """Detect runtime aliases imported from a different flext package root."""
       25          result: t.SequenceOf[m.Infra.NamespaceSourceViolation] = []
```

**Decisão**:

### 170 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/detectors/runtime_alias_detector.py:21` · **Effort**: 15min

> Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed.

```python
       17  class FlextInfraRuntimeAliasDetector:
       18      """Detect missing/duplicate runtime aliases (e.g. m = FlextFooModels) via rope."""
       19  
       20      @staticmethod
>>>    21      def detect_file(
       22          ctx: m.Infra.DetectorContext,
       23      ) -> t.SequenceOf[m.Infra.RuntimeAliasViolation]:
       24          """Detect missing/duplicate runtime alias assignments in a facade file."""
       25          file_path = ctx.file_path
```

**Decisão**:

### 171 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/fixers/orchestrator.py:156` · **Effort**: 13min

> Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed.

```python
      152              else discovered
      153          )
      154          return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(selected)
      155  
>>>   156      def _fix_project(
      157          self, project: p.Infra.ProjectInfo, rules: t.SequenceOf[me.EnforcementRuleSpec]
      158      ) -> t.SequenceOf[m.Infra.ProjectFixResult]:
      159          """Collect violations and apply fixes for one project."""
      160          project_dir = project.path
```

**Decisão**:

### 172 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/fixers/rope_fixer.py:164` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      160          module_path = Path(*module_name.split(".")).with_suffix(".py")
      161          return project_root / src_dir / module_path
      162  
      163      @staticmethod
>>>   164      def _constants_module_for_file(
      165          file_path: Path, *, module_name: str, project_root: Path
      166      ) -> str:
      167          """Return the canonical project constants module for a source file."""
      168          module_parts = tuple(module_name.split("."))
```

**Decisão**:

### 173 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/fixers/rope_fixer.py:258` · **Effort**: 6min

> Define a constant instead of duplicating this literal "no files in violation batch" 3 times.

```python
      254                  skipped=(
      255                      m.Infra.SkippedViolation(
      256                          rule_id=rule_id,
      257                          file_path=str(project_dir),
>>>   258                          reason="no files in violation batch",
      259                      ),
      260                  ),
      261              )
      262          with u.Infra.open_project(self._workspace_root) as rope_project:
```

**Decisão**:

### 174 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/fixers/rope_fixer.py:347` · **Effort**: 6min

> Define a constant instead of duplicating this literal "rope resource not found" 3 times.

```python
      343                      skipped.append(
      344                          m.Infra.SkippedViolation(
      345                              rule_id=rule_id,
      346                              file_path=str(file_path),
>>>   347                              reason="rope resource not found",
      348                          )
      349                      )
      350                      continue
      351                  try:
```

**Decisão**:

### 175 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/fixers/rope_fixer.py:634` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
      630              target_action="hoist_inline_import",
      631              empty_reason="no hoistable inline imports",
      632          )
      633  
>>>   634      def _fix_inline_import_action(
      635          self,
      636          project_dir: Path,
      637          violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
      638          ctx: m.Infra.FixEnforcementCommand,
```

**Decisão**:

### 176 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/fixers/rope_fixer.py:822` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
      818                  continue
      819              unique.append(import_line)
      820          return unique
      821  
>>>   822      def _fix_classvar_relocation(
      823          self,
      824          project_dir: Path,
      825          violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
      826          ctx: m.Infra.FixEnforcementCommand,
```

**Decisão**:

### 177 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/fixers/rope_fixer.py:953` · **Effort**: 23min

> Refactor this function to reduce its Cognitive Complexity from 33 to the 15 allowed.

```python
      949              failed=tuple(failed),
      950              files_modified=tuple(files_modified),
      951          )
      952  
>>>   953      def _fix_one_class_per_module(
      954          self,
      955          project_dir: Path,
      956          violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
      957          ctx: m.Infra.FixEnforcementCommand,
```

**Decisão**:

### 178 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/gates/canonical_alias.py:132` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      128              ctx=ctx,
      129          )
      130  
      131      @override
>>>   132      def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
      133          """Apply ENFORCE-080 rewrites for the selected project."""
      134          if ctx.check_only or not ctx.apply_fixes:
      135              return self._check_only_fix_result(project_dir)
      136          started = time.monotonic()
```

**Decisão**:

### 179 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/gates/loc_cap.py:63` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
       59          issues = self._files_over_cap(result.stdout or "{}", c.Infra.LOC_CAP_MAX)
       60          return len(issues) == 0, issues
       61  
       62      @classmethod
>>>    63      def _files_over_cap(cls, tokei_json: str, cap: int) -> tuple[m.Infra.Issue, ...]:
       64          """Extract over-cap modules from a tokei `--output json` payload.
       65  
       66          Pure function (no subprocess) so the cap logic is unit-testable against
       67          a literal tokei fixture.
```

**Decisão**:

### 180 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/gates/mypy.py:130` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      126          mypy_path = str(typings_generated) + (f":{existing}" if existing else "")
      127          return u.Cli.process_env(overrides={"MYPYPATH": mypy_path})
      128  
      129      @override
>>>   130      def _parse_check_output(
      131          self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
      132      ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
      133          """Parse check output."""
      134          _ = project_dir, ctx
```

**Decisão**:

### 181 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/gates/pyrefly.py:79` · **Effort**: 6min

> Define a constant instead of duplicating this literal `<pyrefly-output>` 3 times.

```python
       75              read = u.Cli.files_read_json(json_file)
       76              if read.failure:
       77                  issues.append(
       78                      m.Infra.Issue(
>>>    79                          file="<pyrefly-output>",
       80                          line=0,
       81                          column=0,
       82                          code="PARSE_ERROR",
       83                          message=f"pyrefly output unreadable/invalid: {read.error}",
```

**Decisão**:

### 182 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/gates/ruff_format.py:44` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       40              c.Infra.RUFF, c.Infra.FORMAT, "--check", *check_dirs, "--quiet"
       41          )
       42  
       43      @override
>>>    44      def _parse_check_output(
       45          self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
       46      ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
       47          """Parse check output."""
       48          _ = project_dir, ctx
```

**Decisão**:

### 183 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_accessor_report.py:42` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
       38          """Accumulate lint totals."""
       39          for tool, lines in snapshot.items():
       40              totals[tool] = totals.get(tool, 0) + len(tuple(lines))
       41  
>>>    42      def _process_file(
       43          self,
       44          py_file: Path,
       45          *,
       46          source: str,
```

**Decisão**:

### 184 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_accessor_report.py:144` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      140          )
      141          return "".join(diff_lines[:80])
      142  
      143      @staticmethod
>>>   144      def render_text(report: m.Infra.AccessorMigrationReport) -> str:
      145          """Render an accessor migration report as CLI text."""
      146          lines: t.MutableSequenceOf[str] = [
      147              "Accessor Migration",
      148              f"workspace: {report.workspace}",
```

**Decisão**:

### 185 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_accessor_rewrite.py:118` · **Effort**: 13min

> Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed.

```python
      114          source_lines = source.splitlines(keepends=True)
      115          line_offset = sum(len(item) for item in source_lines[: line - 1])
      116          return line_offset + column
      117  
>>>   118      def _collect_manual_warnings(
      119          self, py_file: Path, source: str
      120      ) -> t.SequenceOf[m.Infra.AccessorMigrationChange]:
      121          """Collect manual warnings."""
      122          lines = source.splitlines()
```

**Decisão**:

### 186 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_apply.py:73` · **Effort**: 1h

> Refactor this function to reduce its Cognitive Complexity from 70 to the 15 allowed.

```python
       69          def _rewrite_runtime_alias_source(
       70              source: str, *, alias: str, target_name: str
       71          ) -> str: ...
       72  
>>>    73      def _apply_supported_fixes(
       74          self, rope: p.Infra.RopeWorkspaceDsl, report: m.Infra.Census.WorkspaceReport
       75      ) -> frozenset[str]:
       76          """Apply supported fixes."""
       77          applied: set[str] = set()
```

**Decisão**:

### 187 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_apply.py:272` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      268                  self._regenerate_inits_via_codegen()
      269              rope.reload()
      270          return frozenset(applied)
      271  
>>>   272      def _apply_hoist_inline_imports(
      273          self,
      274          *,
      275          rope: p.Infra.RopeWorkspaceDsl,
      276          file_path: Path,
```

**Decisão**:

### 188 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_inventory.py:29` · **Effort**: 18min

> Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed.

```python
       25          @staticmethod
       26          def _is_flext_owned(value: p.ModuleOwned) -> bool: ...
       27  
       28      @classmethod
>>>    29      def _build_parent_inventory(
       30          cls, workspace_root: Path
       31      ) -> t.MappingKV[str, t.StrSequence]:
       32          """Inventory governed-package alias top-level facade names.
       33  
```

**Decisão**:

### 189 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_rules_alias.py:66` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
       62          def _runtime_alias_target_name(
       63              convention: m.Infra.RopeModuleConvention,
       64          ) -> str: ...
       65  
>>>    66      def _rule_runtime_alias(
       67          self,
       68          rope: p.Infra.RopeWorkspaceDsl,
       69          file_path: Path,
       70          *,
```

**Decisão**:

### 190 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_rules_dispatch.py:334` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      330      def _declarative_catalog_rules() -> tuple[me.EnforcementRuleSpec, ...]:
      331          """Return enabled catalog rules handled by the declarative engine."""
      332          return FlextInfraEnforcementEngine.declarative_rules()
      333  
>>>   334      def _rule_declarative(
      335          self,
      336          rope: p.Infra.RopeWorkspaceDsl,
      337          file_path: Path,
      338          *,
```

**Decisão**:

### 191 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_census_validate.py:47` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       43              fixable: bool = False,
       44              fix_action: str = "",
       45          ) -> m.Infra.Census.Violation: ...
       46  
>>>    47      def _validated_project_reports(
       48          self,
       49          rope: p.Infra.RopeWorkspaceDsl,
       50          project_reports: tuple[m.Infra.Census.ProjectReport, ...],
       51      ) -> tuple[m.Infra.Census.ProjectReport, ...]:
```

**Decisão**:

### 192 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/_orchestrator_dispatch.py:165` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      161          else:
      162              result = []
      163          return result
      164  
>>>   165      def run_refactor(self, args: p.Infra.RefactorCliArgs) -> int:
      166          """Run refactor CLI dispatch for the selected scope."""
      167          if args.project:
      168              results = list(
      169                  self.refactor_project(
```

**Decisão**:

### 193 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/accessor_migration.py:45` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
       41          """Selected lint tool names resolved from gate names."""
       42          return u.Infra.selected_lint_tool_names(self.gate_names)
       43  
       44      @override
>>>    45      def execute(self) -> p.Result[m.Infra.AccessorMigrationReport]:
       46          """Execute."""
       47          selected_projects: t.StrSequence = (
       48              self.project_names if self.project_names is not None else ()
       49          )
```

**Decisão**:

### 194 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/class_nesting_analyzer.py:23` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
       19  class FlextInfraRefactorClassNestingAnalyzer:
       20      """Detect class nesting violations and report MRO hierarchy issues."""
       21  
       22      @classmethod
>>>    23      def analyze_files(cls, files: t.SequenceOf[Path]) -> m.Infra.ClassNestingReport:
       24          """Analyze files and return aggregated class-nesting violations."""
       25          if not files:
       26              return m.Infra.ClassNestingReport(
       27                  violations_count=0,
```

**Decisão**:

### 195 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/classvar_constant_autofix.py:122` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      118                  project, plan, dry_run=dry_run
      119              )
      120  
      121      @staticmethod
>>>   122      def _apply_with_project(
      123          project: t.Infra.RopeProject,
      124          plan: ClassvarConstantAutofixPlan,
      125          *,
      126          dry_run: bool,
```

**Decisão**:

### 196 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/classvar_constant_autofix.py:292` · **Effort**: 14min

> Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed.

```python
      288      resource: t.Infra.RopeResource = target_resource
      289      return resource
      290  
      291  
>>>   292  def _extract_declaration_line(
      293      source: str, class_name: str, constant_name: str, class_lineno: int
      294  ) -> str:
      295      """Return the exact source line that declares the class-level constant."""
      296      try:
```

**Decisão**:

### 197 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/classvar_constant_autofix.py:567` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      563      """Return whether an attribute prefix should be rewritten to _constants."""
      564      return prefix in {class_name, "cls"} or prefix.endswith(".__class__")
      565  
      566  
>>>   567  def _ensure_constants_import(
      568      source: str, constants_alias: str, class_module: str, constants_module: str
      569  ) -> str:
      570      """Add an import for the canonical _constants module if absent.
      571  
```

**Decisão**:

### 198 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/classvar_constant_autofix.py:653` · **Effort**: 13min

> Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed.

```python
      649          break
      650      return last_import
      651  
      652  
>>>   653  def _module_import_insert_after(lines: t.StrSequence) -> int:
      654      """Return index after module docstring and future imports only."""
      655      idx = 0
      656      while idx < len(lines) and not lines[idx].strip():
      657          idx += 1
```

**Decisão**:

### 199 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/declarative_enforcement.py:325` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      321              file_path=str(file_path), line=line, rule_id=rule_id, **kwargs
      322          )
      323  
      324      @staticmethod
>>>   325      def _rope_parent_map(root: p.AttributeProbe) -> dict[int, p.AttributeProbe]:
      326          """Build a child-id -> parent map for the full rope AST."""
      327          parent_map: dict[int, p.AttributeProbe] = {}
      328          stack: list[p.AttributeProbe] = [root]
      329          while stack:
```

**Decisão**:

### 200 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/legacy_text_ops.py:94` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       90              else (source, list[str]())
       91          )
       92  
       93      @classmethod
>>>    94      def _remove_wrappers(cls, source: str) -> t.Infra.TransformResult:
       95          """Inline passthrough function wrappers via rope-located ranges."""
       96          pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
       97          if pymodule is None:
       98              return (source, list[str]())
```

**Decisão**:

### 201 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/legacy_text_ops.py:138` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      134              return (source, list[str]())
      135          return ("".join(lines).rstrip("\n") + "\n", changes)
      136  
      137      @staticmethod
>>>   138      def _is_passthrough_wrapper(func: object, call: object) -> bool:
      139          """Whether ``func``'s body is exactly ``return call(*args, **kwargs)`` over its params."""
      140          args_obj = getattr(func, "args", None)
      141          if args_obj is None:
      142              return False
```

**Decisão**:

### 202 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/refactor/migrate_to_class_mro.py:36` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       32      def __init__(self, *, workspace_root: Path) -> None:
       33          """Create migration service bound to a workspace root."""
       34          self._workspace_root = workspace_root.resolve()
       35  
>>>    36      def run(
       37          self,
       38          *,
       39          target: str,
       40          apply: bool,
```

**Decisão**:

### 203 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/release/_release_artifact_archive.py:189` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      185          except (OSError, tarfile.TarError) as exc:
      186              return r[bool].fail_op(f"validate sdist archive {path}", exc)
      187  
      188      @classmethod
>>>   189      def _validate_open_sdist(
      190          cls, archive: tarfile.TarFile, path: Path, project: str, license_sha256: str
      191      ) -> p.Result[bool]:
      192          """Validate one already-open source-distribution archive."""
      193          expected_roots = (project.casefold(), project.replace("-", "_").casefold())
```

**Decisão**:

### 204 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/release/_release_artifact_metadata.py:75` · **Effort**: 19min

> Refactor this function to reduce its Cognitive Complexity from 29 to the 15 allowed.

```python
       71          u.Cli.toml_sync_string_list(container, key, rewritten)
       72          return r[bool].ok(True)
       73  
       74      @classmethod
>>>    75      def _release_pyproject(cls, source: str, version: str) -> p.Result[str]:
       76          """Render a pyproject suitable for a public package registry."""
       77          document = u.Cli.toml_parse_text(source)
       78          if document is None:
       79              return r[str].fail("release pyproject is not valid TOML")
```

**Decisão**:

### 205 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/release/orchestrator_phases.py:217` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      213          if report_result.value:
      214              return r[bool].fail(f"build failed: {report_result.value} project(s)")
      215          return r[bool].ok(True)
      216  
>>>   217      def phase_version(self, ctx: m.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
      218          """Execute versioning phase across workspace and selected projects."""
      219          target = f"{ctx.version}.dev0" if ctx.dev_suffix else ctx.version
      220          parse_result = u.Infra.parse_semver(target)
      221          if parse_result.failure:
```

**Decisão**:

### 206 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/release/orchestrator_phases.py:367` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
      363          return r[t.SequenceOf[t.Triple[Path, str, str]]].ok((
      364              (manifest_path, current_result.value, rendered.value),
      365          ))
      366  
>>>   367      def _version_update_files(
      368          self, files: t.SequenceOf[Path], target: str, *, dry_run: bool
      369      ) -> p.Result[int]:
      370          """Update version in each file, returning count of changed files."""
      371          updates: t.MutableSequenceOf[t.Triple[Path, str, str]] = []
```

**Decisão**:

### 207 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/services/_codegen/vscode.py:76` · **Effort**: 19min

> Refactor this function to reduce its Cognitive Complexity from 29 to the 15 allowed.

```python
       72          """Return strict JSON text from VS Code JSONC content."""
       73          return cls._remove_trailing_commas(cls._remove_jsonc_comments(content))
       74  
       75      @staticmethod
>>>    76      def _remove_jsonc_comments(content: str) -> str:
       77          """Remove JSONC comments while preserving comment markers in strings."""
       78          output: list[str] = []
       79          in_string = False
       80          escaped = False
```

**Decisão**:

### 208 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/services/_codegen/vscode.py:128` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
      124              index += 1
      125          return "".join(output)
      126  
      127      @staticmethod
>>>   128      def _remove_trailing_commas(content: str) -> str:
      129          """Remove commas before object or array closers outside strings."""
      130          output: list[str] = []
      131          in_string = False
      132          escaped = False
```

**Decisão**:

### 209 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/services/_codegen/vscode.py:243` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      239              changed = True
      240          return changed
      241  
      242      @staticmethod
>>>   243      def _resolve_list_setting(
      244          key: str, base_entries: tuple[str, ...], *, workspace_root: Path
      245      ) -> tuple[str, ...]:
      246          """Resolve one canonical list, deriving extra globs from the topology."""
      247          if key != c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY:
```

**Decisão**:

### 211 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/services/cli_routes.py:45` · **Effort**: 8min

> Define a constant instead of duplicating this literal "flext_infra.services.cli_routes_validate" 4 times.

```python
       41          "CodegenRoutes",
       42          "codegen_routes",
       43      ),
       44      c.Infra.CLI_GROUP_DOCS: (
>>>    45          "flext_infra.services.cli_routes_validate",
       46          "ValidationRoutes",
       47          "validation_routes",
       48      ),
       49      c.Infra.CLI_GROUP_GITHUB: (
```

**Decisão**:

### 212 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/services/cli_routes.py:65` · **Effort**: 6min

> Define a constant instead of duplicating this literal "flext_infra.services.cli_routes_workspace" 3 times.

```python
       61          "ValidationRoutes",
       62          "validation_routes",
       63      ),
       64      c.Infra.CLI_GROUP_REFACTOR: (
>>>    65          "flext_infra.services.cli_routes_workspace",
       66          "WorkspaceRoutes",
       67          "workspace_routes",
       68      ),
       69      c.Infra.CLI_GROUP_RELEASE: (
```

**Decisão**:

### 213 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/services/cli_transaction.py:129` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
      125                  members.append(member_path)
      126          return tuple(members)
      127  
      128      @classmethod
>>>   129      def transaction_scoped_paths(
      130          cls, args: t.StrSequence, workspace_root: Path
      131      ) -> tuple[Path, ...]:
      132          """Derive workspace-relative paths the command can touch.
      133  
```

**Decisão**:

### 214 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/_header.py:143` · **Effort**: 13min

> Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed.

```python
      139          lines.append(line)
      140      return "".join(lines)
      141  
      142  
>>>   143  def _parse_header(source: str) -> _HeaderInfo:
      144      """Parse the module header using the stdlib ``tokenize`` module."""
      145      aliases: set[str] = set()
      146      span = _HeaderSpan()
      147  
```

**Decisão**:

### 215 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/transformers/_typing_rewrite.py:48` · **Effort**: 8min

> Define a constant instead of duplicating this literal "tuple[" 4 times.

```python
       44              content, end_index = self._extract_square_bracket_content(
       45                  text, index + len(prefix) - 1
       46              )
       47              rewritten_content, nested_changes = self._rewrite_type_expression(content)
>>>    48              if prefix.lower().startswith("tuple["):
       49                  replacement = self._rewrite_tuple_annotation(
       50                      original_prefix=prefix, rewritten_content=rewritten_content
       51                  )
       52              else:
```

**Decisão**:

### 216 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/transformers/_typing_rewrite.py:117` · **Effort**: 6min

> Define a constant instead of duplicating this literal "Tuple[" 3 times.

```python
      113              if cls._matches_type_token(text, index, prefix):
      114                  return prefix, alias_name
      115          if cls._matches_type_token(text, index, "tuple["):
      116              return "tuple[", ""
>>>   117          if cls._matches_type_token(text, index, "Tuple["):
      118              return "Tuple[", ""
      119          return None
      120  
      121      @staticmethod
```

**Decisão**:

### 217 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/census_visitors.py:33` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       29          self.facade_class_prefix = facade_class_prefix
       30          self.alias_locals: t.Infra.StrSet = set()
       31          self.direct_imports: dict[str, str] = {}
       32  
>>>    33      def scan_source(self, source: str) -> None:
       34          """Scan source text to discover imports matching family/facade patterns."""
       35          for match in c.Infra.FROM_IMPORT_SIMPLE_RE.finditer(source):
       36              module_str = match.group(1)
       37              if (
```

**Decisão**:

### 218 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/compatibility_alias.py:75` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
       71                  f"Removed compatibility alias: {alias_name} = {alias_map[alias_name]}"
       72              )
       73          return updated
       74  
>>>    75      def _rewrite_compat_imports(self, source: str) -> str:
       76          """Rewrite ``from <pkg> import LongFacadeName`` to canonical aliases."""
       77          try:
       78              tree = ast.parse(source)
       79          except SyntaxError:
```

**Decisão**:

### 219 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/project_alias_migrator.py:70` · **Effort**: 10min

> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

```python
       66              expression = cst.Attribute(value=expression, attr=cst.Name(part))
       67          return expression
       68  
       69      @classmethod
>>>    70      def insert_local_imports(
       71          cls, tree: cst.Module, imports_to_add: dict[str, dict[str, str]]
       72      ) -> cst.Module:
       73          """Prepend newly required local alias imports after __future__/docstring."""
       74          if not imports_to_add:
```

**Decisão**:

### 220 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/transformers/pydantic_modernizer.py:209` · **Effort**: 8min

> Define a constant instead of duplicating this literal "mode=" 4 times.

```python
      205              dec_text = self.node_text(decorator)
      206              new_text = dec_text.replace("validator(", "field_validator(", 1)
      207  
      208              # Add mode="before" if pre=True is present, otherwise mode="after".
>>>   209              if "pre=True" in new_text and "mode=" not in new_text:
      210                  new_text = new_text.replace(")", ', mode="before")', 1)
      211              elif "mode=" not in new_text:
      212                  new_text = new_text.replace(")", ', mode="after")', 1)
      213  
```

**Decisão**:

### 221 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/signature_propagator.py:112` · **Effort**: 16min

> Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed.

```python
      108              updated = updated[:start] + replacement + updated[end:]
      109          return updated
      110  
      111      @staticmethod
>>>   112      def _rewrite_call_text(
      113          call_text: str,
      114          *,
      115          keyword_renames: t.MutableStrMapping,
      116          remove_keywords: t.Infra.StrSet,
```

**Decisão**:

### 222 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/transformers/signature_propagator.py:163` · **Effort**: 12min

> Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed.

```python
      159                      changed = True
      160          return result, changed
      161  
      162      @staticmethod
>>>   163      def _drop_keyword(text: str, pattern: t.Infra.RegexPattern) -> tuple[str, int]:
      164          """Remove ``<name>=<value>[,]?`` occurrences from a call slice."""
      165          result = text
      166          drops = 0
      167          match = pattern.search(result)
```

**Decisão**:

### 223 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/_skill_rule_runner.py:56` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       52                  "ast-grep matches" if rule_type == "ast-grep" else "custom violations"
       53              )
       54              violations.append(f"[{rule_id}] {count} {label}")
       55  
>>>    56      def _run_ast_grep_count(
       57          self,
       58          rule: t.MappingKV[str, t.Infra.InfraValue],
       59          skill_dir: Path,
       60          project_path: Path,
```

**Decisão**:

### 224 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/import_cycles.py:164` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
      160          resolves relative imports to absolute module names.
      161          """
      162          return u.Infra.imported_module_paths(module_imports)
      163  
>>>   164      def _tarjan(
      165          self, graph: MutableMapping[str, set[str]]
      166      ) -> t.SequenceOf[t.StrSequence]:
      167          """Tarjan's SCC over ``graph``; returns each SCC as a list of module names."""
      168          index_counter = [0]
```

**Decisão**:

### 225 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/validate/inventory.py:87` · **Effort**: 6min

> Define a constant instead of duplicating this literal "t.JsonMapping" 3 times.

```python
       83              "generated_at": now,
       84              "candidates": [],
       85          })
       86          return (
>>>    87              cast("t.JsonMapping", inventory_payload),
       88              cast("t.JsonMapping", wiring_payload),
       89              cast("t.JsonMapping", external_payload),
       90          )
       91  
```

**Decisão**:

### 226 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/namespace_rules.py:118` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      114              for node in body
      115              if FlextInfraUtilitiesRopeAnalysis.node_kind(node) == "ClassDef"
      116          ]
      117  
>>>   118      def check_rule_0(
      119          self,
      120          tree: object,
      121          filepath: Path,
      122          prefix: str,
```

**Decisão**:

### 227 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/namespace_rules.py:367` · **Effort**: 31min

> Refactor this function to reduce its Cognitive Complexity from 41 to the 15 allowed.

```python
      363                  f"{name_str!r} belongs in typings.py"
      364              )
      365          ]
      366  
>>>   367      def check_rule_3(
      368          self, tree: object, filepath: Path, *, class_stem: str, package_name: str
      369      ) -> t.StrSequence:
      370          """Rule 3 — Runtime modules use namespaced MRO aliases (c/m/p/t/u)."""
      371          owner_rules = self._owner_direct_facade_rules(class_stem)
```

**Decisão**:

### 228 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/validate/pytest_runner.py:276` · **Effort**: 6min

> Define a constant instead of duplicating this literal "pytest.log" 3 times.

```python
      272          """Compose the existing JUnit/log diagnostic owner in-process."""
      273          extractor = FlextInfraPytestDiagExtractor(
      274              workspace_root=self.root,
      275              junit=report_dir / "junit.xml",
>>>   276              log_path=report_dir / "pytest.log",
      277          )
      278          return extractor.extract(extractor.junit, extractor.log_path)
      279  
      280      def _execute_cache_maintenance(self) -> p.Result[int]:
```

**Decisão**:

### 229 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/pytest_runner.py:280` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      276              log_path=report_dir / "pytest.log",
      277          )
      278          return extractor.extract(extractor.junit, extractor.log_path)
      279  
>>>   280      def _execute_cache_maintenance(self) -> p.Result[int]:
      281          """Run one typed testmon DB maintenance WHAT without invoking pytest."""
      282          db = self._testmon_db_path()
      283          if self.what == "cache-clear":
      284              apply = (
```

**Decisão**:

### 230 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/pytest_runner.py:329` · **Effort**: 23min

> Refactor this function to reduce its Cognitive Complexity from 33 to the 15 allowed.

```python
      325          )
      326          return r[int].ok(0 if value.reason != "testmon db missing or empty" else 1)
      327  
      328      @override
>>>   329      def execute(self) -> p.Result[int]:
      330          """Execute pytest, profile it, and preserve reports under one deadline."""
      331          if self._is_cache_maintenance():
      332              return self._execute_cache_maintenance()
      333          # Why (mro-v4p5): CI workflows must not run pytest. Fail loud if invoked
```

**Decisão**:

### 231 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/runtime_census.py:83` · **Effort**: 8min

> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

```python
       79          except Exception as exc:
       80              modules.append(f"{package_name}: walk_packages failed: {exc}")
       81          return modules
       82  
>>>    83      def _check_module(self, module_name: str) -> t.SequenceOf[m.Infra.ValidationReport]:
       84          """Import one module and run runtime enforcement on its local classes."""
       85          try:
       86              module = importlib.import_module(module_name)
       87          except Exception as exc:
```

**Decisão**:

### 232 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/validate/testmon_db.py:102` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       98                  self._reject("testmon schema empty", seed_needed=True)
       99              )
      100          return None
      101  
>>>   102      def _inspect_existing(self) -> p.Result[FlextInfraTestmonCacheState]:
      103          """Validate one on-disk DB after pytest has closed it."""
      104          path = self.db_path
      105          if path.is_symlink():
      106              return r[FlextInfraTestmonCacheState].ok(
```

**Decisão**:

### 233 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/workspace/detector.py:250` · **Effort**: 9min

> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

```python
      246          """Resolve the declared provider owning ``url``, else the default one."""
      247          return cls._declared_provider_for_url(url) or config.Infra.codegen.providers[0]
      248  
      249      @classmethod
>>>   250      def _validate_observed_dependencies(
      251          cls, repository_root: Path, workspace: m.Infra.WorkspaceSpec
      252      ) -> p.Result[tuple[Path, ...]]:
      253          """Match governed members and external dependencies to live Git topology."""
      254          declared = u.Infra.git_declared_submodule_paths(repository_root)
```

**Decisão**:

### 234 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/workspace/detector.py:257` · **Effort**: 6min

> Define a constant instead of duplicating this literal "unable to read Git submodule topology" 3 times.

```python
      253          """Match governed members and external dependencies to live Git topology."""
      254          declared = u.Infra.git_declared_submodule_paths(repository_root)
      255          if declared.failure:
      256              return r[tuple[Path, ...]].fail(
>>>   257                  declared.error or "unable to read Git submodule topology"
      258              )
      259          declared_set = frozenset(declared.value)
      260          providers = {item.name: item for item in config.Infra.codegen.providers}
      261          governed_paths: set[Path] = set()
```

**Decisão**:

### 235 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/workspace/detector.py:419` · **Effort**: 17min

> Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed.

```python
      415              return r[bool].fail("local repository cannot be read-only")
      416          return r[bool].ok(True)
      417  
      418      @classmethod
>>>   419      def _unattached_mode(
      420          cls, repository_root: Path, workspace_spec: m.Infra.WorkspaceSpec | None
      421      ) -> p.Result[c.Infra.WorkspaceMode]:
      422          """Infer root from actual first-party governed submodule declarations."""
      423          attached_marker = cls._declares_attached_standalone(repository_root)
```

**Decisão**:

### 236 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/workspace/detector.py:486` · **Effort**: 20min

> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

```python
      482              else c.Infra.WorkspaceMode.STANDALONE
      483          )
      484  
      485      @classmethod
>>>   486      def conform_target(
      487          cls, repository_root: Path, workspace_spec: m.Infra.WorkspaceSpec | None = None
      488      ) -> p.Result[m.Infra.RepositoryConformTarget]:
      489          """Derive the sole conformance target from live Git and typed identity."""
      490          resolved_root = repository_root.expanduser().resolve()
```

**Decisão**:

### 237 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/workspace/detector.py:663` · **Effort**: 25min

> Refactor this function to reduce its Cognitive Complexity from 35 to the 15 allowed.

```python
      659              return r[tuple[str, str]].fail(contract.error)
      660          return r[tuple[str, str]].ok((contract.value.url, contract.value.branch))
      661  
      662      @classmethod
>>>   663      def _detect_attached(
      664          cls,
      665          project_root: Path,
      666          superproject_root: Path,
      667          workspace_spec: m.Infra.WorkspaceSpec | None,
```

**Decisão**:

### 238 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/workspace/environment_provenance.py:31` · **Effort**: 6min

> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

```python
       27          """Validate one CLI request without mutating the environment."""
       28          return cls.validate(request.workspace_root)
       29  
       30      @classmethod
>>>    31      def validate(
       32          cls, workspace_root: Path, *, metadata_paths: t.StrSequence | None = None
       33      ) -> p.Result[int]:
       34          """Validate PEP 610 and editable path metadata for active members."""
       35          resolved_root = workspace_root.resolve()
```

**Decisão**:

### 239 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/worktree.py:187` · **Effort**: 11min

> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

```python
      183                      f"{branch_cleanup.error or 'unknown branch cleanup failure'}"
      184                  )
      185          return r.fail(f"worktree setup failed: {setup_error}; clean lane rolled back")
      186  
>>>   187      def _add(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
      188          """Create and set up one branch worktree transactionally."""
      189          if not self.apply_changes:
      190              return r.fail("worktree add requires --apply")
      191          lane_result = self._lane_path(primary_root, branch)
```

**Decisão**:

### 240 · 🟠 CRITICAL · CODE_SMELL · `python:S1192`
**Local**: `src/flext_infra/worktree.py:193` · **Effort**: 6min

> Define a constant instead of duplicating this literal "invalid worktree lane path" 3 times.

```python
      189          if not self.apply_changes:
      190              return r.fail("worktree add requires --apply")
      191          lane_result = self._lane_path(primary_root, branch)
      192          if lane_result.failure:
>>>   193              return r.fail(lane_result.error or "invalid worktree lane path")
      194          lane = lane_result.value
      195          if lane.exists():
      196              return r.fail(f"worktree lane already exists: {lane}")
      197          ensured = u.Cli.ensure_dir(lane.parent)
```

**Decisão**:

### 241 · 🟠 CRITICAL · CODE_SMELL · `python:S3776`
**Local**: `src/flext_infra/worktree.py:265` · **Effort**: 7min

> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

```python
      261          if removed.failure:
      262              return r.fail(removed.error or f"failed to remove worktree for {branch}")
      263          return r.ok(str(lane))
      264  
>>>   265      def _update(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
      266          """Merge-forward one clean canonical lane to the requested base."""
      267          if not self.apply_changes:
      268              return r.fail("worktree update requires --apply")
      269          lane_result = self.registered_lane(primary_root, branch)
```

**Decisão**:

### 242 · 🟠 CRITICAL · VULNERABILITY · `docker:S6470`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:33` · **Effort**: 20min

> Copying recursively might inadvertently add sensitive data to the container. Make sure it is safe here.

```Dockerfile
       29  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       30  # End SECTION: managed tool bootstrap
       31  
       32  WORKDIR /workspace
>>>    33  COPY . .
       34  
       35  # === SECTION: mise install (managed) ===
       36  # Source: computed (reads .mise.toml from copied workspace)
       37  RUN mise trust .mise.toml && mise install --yes
```

**Decisão**:

### 243 · 🟠 CRITICAL · VULNERABILITY · `docker:S6470`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:35` · **Effort**: 20min

> Copying recursively might inadvertently add sensitive data to the container. Make sure it is safe here.

```Dockerfile
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       32  # End SECTION: managed tool bootstrap
       33  
       34  WORKDIR /workspace
>>>    35  COPY . .
       36  
       37  # === SECTION: mise install (managed) ===
       38  # Source: computed (reads .mise.toml from copied workspace)
       39  RUN mise trust .mise.toml && mise install --yes
```

**Decisão**:

### 244 · 🟠 CRITICAL · VULNERABILITY · `docker:S6470`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:36` · **Effort**: 20min

> Copying recursively might inadvertently add sensitive data to the container. Make sure it is safe here.

```Dockerfile
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       33  # End SECTION: managed tool bootstrap
       34  
       35  WORKDIR /workspace
>>>    36  COPY . .
       37  
       38  # === SECTION: mise install (managed) ===
       39  # Source: computed (reads .mise.toml from copied workspace)
       40  RUN mise trust .mise.toml && mise install --yes
```

**Decisão**:

### 245 · 🟠 CRITICAL · VULNERABILITY · `docker:S6470`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:35` · **Effort**: 20min

> Copying recursively might inadvertently add sensitive data to the container. Make sure it is safe here.

```Dockerfile
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       32  # End SECTION: managed tool bootstrap
       33  
       34  WORKDIR /workspace
>>>    35  COPY . .
       36  
       37  # === SECTION: mise install (managed) ===
       38  # Source: computed (reads .mise.toml from copied workspace)
       39  RUN mise trust .mise.toml && mise install --yes
```

**Decisão**:

### 246 · 🟠 CRITICAL · VULNERABILITY · `docker:S6470`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:36` · **Effort**: 20min

> Copying recursively might inadvertently add sensitive data to the container. Make sure it is safe here.

```Dockerfile
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       33  # End SECTION: managed tool bootstrap
       34  
       35  WORKDIR /workspace
>>>    36  COPY . .
       37  
       38  # === SECTION: mise install (managed) ===
       39  # Source: computed (reads .mise.toml from copied workspace)
       40  RUN mise trust .mise.toml && mise install --yes
```

**Decisão**:

### 247 · 🟡 MAJOR · VULNERABILITY · `githubactions:S8264`
**Local**: `.github/workflows/docs.yml:18` · **Effort**: 5min

> Move this read permission from workflow level to job level.

```yaml
       14        - ".github/workflows/docs.yml"
       15    workflow_dispatch:
       16  
       17  permissions:
>>>    18    contents: read
       19    pages: write
       20    id-token: write
       21  
       22  concurrency:
```

**Decisão**:

### 248 · 🟡 MAJOR · VULNERABILITY · `githubactions:S8233`
**Local**: `.github/workflows/docs.yml:19` · **Effort**: 5min

> Move this write permission from workflow level to job level.

```yaml
       15    workflow_dispatch:
       16  
       17  permissions:
       18    contents: read
>>>    19    pages: write
       20    id-token: write
       21  
       22  concurrency:
       23    group: pages
```

**Decisão**:

### 249 · 🟡 MAJOR · VULNERABILITY · `githubactions:S8233`
**Local**: `.github/workflows/docs.yml:20` · **Effort**: 5min

> Move this write permission from workflow level to job level.

```yaml
       16  
       17  permissions:
       18    contents: read
       19    pages: write
>>>    20    id-token: write
       21  
       22  concurrency:
       23    group: pages
       24    cancel-in-progress: false
```

**Decisão**:

### 250 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/census.py:31` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       27              r"^from\s+flext_core\.\S+\s+import\s+", re.MULTILINE
       28          )
       29          "Detect direct flext_core submodule imports."
       30          LEGACY_MAPPING_RE: Final[t.RegexPattern] = re.compile(
>>>    31              r"^from\s+typing\s+import\s+.*\bMapping\b", re.MULTILINE
       32          )
       33          "Detect legacy ``from typing import Mapping``."
       34          FLEXT_CORE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
       35              r"^from\s+flext_core\s+import\s+(.+?)$", re.MULTILINE
```

**Decisão**:

### 251 · 🟡 MAJOR · CODE_SMELL · `python:S6019`
**Local**: `src/flext_infra/_constants/census.py:35` · **Effort**: 10min

> Remove the '?' from this unnecessarily reluctant quantifier.

```python
       31              r"^from\s+typing\s+import\s+.*\bMapping\b", re.MULTILINE
       32          )
       33          "Detect legacy ``from typing import Mapping``."
       34          FLEXT_CORE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>    35              r"^from\s+flext_core\s+import\s+(.+?)$", re.MULTILINE
       36          )
       37          "Detect ``from flext_core import ...``."
       38          STRENUM_RE: Final[t.RegexPattern] = re.compile(
       39              r"class\s+(\w+)\s*\([^)]*\bStrEnum\b"
```

**Decisão**:

### 252 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/census.py:35` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       31              r"^from\s+typing\s+import\s+.*\bMapping\b", re.MULTILINE
       32          )
       33          "Detect legacy ``from typing import Mapping``."
       34          FLEXT_CORE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>    35              r"^from\s+flext_core\s+import\s+(.+?)$", re.MULTILINE
       36          )
       37          "Detect ``from flext_core import ...``."
       38          STRENUM_RE: Final[t.RegexPattern] = re.compile(
       39              r"class\s+(\w+)\s*\([^)]*\bStrEnum\b"
```

**Decisão**:

### 253 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/check.py:68` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       64      })
       65      ALLOWED_GATES: Final[frozenset[str]] = frozenset(SARIF_TOOL_INFO)
       66      "Gate identifiers — derived from SARIF_TOOL_INFO keys (single SSOT)."
       67      RUFF_FORMAT_FILE_RE: Final[t.RegexPattern] = re.compile(
>>>    68          r"^\s*-->\s*(.+?):\d+:\d+\s*$"
       69      )
       70      MARKDOWN_RE: Final[t.RegexPattern] = re.compile(
       71          r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s+\[(?P<code>MD\d+)\]\s+(?P<msg>.*)$"
       72      )
```

**Decisão**:

### 254 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/check.py:71` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       67      RUFF_FORMAT_FILE_RE: Final[t.RegexPattern] = re.compile(
       68          r"^\s*-->\s*(.+?):\d+:\d+\s*$"
       69      )
       70      MARKDOWN_RE: Final[t.RegexPattern] = re.compile(
>>>    71          r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s+\[(?P<code>MD\d+)\]\s+(?P<msg>.*)$"
       72      )
       73      VALID_GATE_SEVERITIES: Final[frozenset[str]] = frozenset(GateSeverity)
       74      "Severity levels accepted by gate output parsers — derived from GateSeverity."
       75      GATE_ERROR_OUTPUT_LIMIT: Final[int] = 20
```

**Decisão**:

### 255 · 🟡 MAJOR · CODE_SMELL · `python:S6019`
**Local**: `src/flext_infra/_constants/check.py:164` · **Effort**: 10min

> Remove the '?' from this unnecessarily reluctant quantifier.

```python
      160      BOUNDARY_TOML_RE: Final[t.RegexPattern] = re.compile(
      161          r"^\s*(import|from)\s+(tomllib|tomlkit)(\s|$|\.)", re.MULTILINE
      162      )
      163      BOUNDARY_CONCRETE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   164          r"^from\s+flext_cli\s+import\s+(?P<imports>.+?)$", re.MULTILINE
      165      )
      166      BOUNDARY_FLEXT_CLI_CONCRETE_RE: Final[t.RegexPattern] = re.compile(
      167          r"\bFlextCli[A-Z]\w*"
      168      )
```

**Decisão**:

### 256 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/check.py:164` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      160      BOUNDARY_TOML_RE: Final[t.RegexPattern] = re.compile(
      161          r"^\s*(import|from)\s+(tomllib|tomlkit)(\s|$|\.)", re.MULTILINE
      162      )
      163      BOUNDARY_CONCRETE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   164          r"^from\s+flext_cli\s+import\s+(?P<imports>.+?)$", re.MULTILINE
      165      )
      166      BOUNDARY_FLEXT_CLI_CONCRETE_RE: Final[t.RegexPattern] = re.compile(
      167          r"\bFlextCli[A-Z]\w*"
      168      )
```

**Decisão**:

### 257 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/codegen.py:58` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       54          ("_settings.py", "Settings", "FlextSettings", "Runtime settings"),
       55      )
       56      "Runtime singleton modules for src/: (filename, class_suffix, base_class, docstring)."
       57      VIOLATION_PATTERN: Final[t.RegexPattern] = re.compile(
>>>    58          r"\[(?P<rule>NS-\d{3})-\d{3}\]\s+(?P<module>[^:]+):(?P<line>\d+)\s+\u2014\s+(?P<message>.+)"
       59      )
       60      "Regex to parse violation strings: [NS-00X-NNN] path:line — message."
       61  
       62      # --- Pipeline stage StrEnum (was: class Pipeline plain strings) ---
```

**Decisão**:

### 258 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/docs.py:38` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       34          "PLC0415",
       35      )
       36      """Rules ignored for executable docs snippets that are not full modules/tests."""
       37      PYTHON_FENCE_RE: Final[t.RegexPattern] = re.compile(
>>>    38          r"^```python\s*\n(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL
       39      )
       40      """Regex matching ``python`` fenced blocks; ``body`` group yields contents."""
       41  
       42      PYTHON_FENCE_FIX_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 259 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/docs.py:43` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       39      )
       40      """Regex matching ``python`` fenced blocks; ``body`` group yields contents."""
       41  
       42      PYTHON_FENCE_FIX_RE: Final[t.RegexPattern] = re.compile(
>>>    43          r"^(?P<open>```python\s*\n)(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL
       44      )
       45      """Regex matching ``python`` fenced blocks for fix-in-place replacement."""
       46  
       47      FENCE_NOTEST_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 260 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/docs.py:62` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       58      MARKDOWN_LINK_RE: Final[t.RegexPattern] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
       59      """Match markdown links capturing text (group 1) and URL (group 2)."""
       60      MARKDOWN_LINK_URL_RE: Final[t.RegexPattern] = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
       61      """Match markdown links capturing only the URL (group 1)."""
>>>    62      HEADING_RE: Final[t.RegexPattern] = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
       63      """Match any markdown heading (h1-h6), capturing the text."""
       64      HEADING_H2_H3_RE: Final[t.RegexPattern] = re.compile(
       65          r"^(##|###)\s+(.+?)\s*$", re.MULTILINE
       66      )
```

**Decisão**:

### 261 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/docs.py:65` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       61      """Match markdown links capturing only the URL (group 1)."""
       62      HEADING_RE: Final[t.RegexPattern] = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
       63      """Match any markdown heading (h1-h6), capturing the text."""
       64      HEADING_H2_H3_RE: Final[t.RegexPattern] = re.compile(
>>>    65          r"^(##|###)\s+(.+?)\s*$", re.MULTILINE
       66      )
       67      """Match h2/h3 headings, capturing level (group 1) and text (group 2)."""
       68      ANCHOR_LINK_RE: Final[t.RegexPattern] = re.compile(r"\[([^\]]+)\]\(#([^)]+)\)")
       69      """Match internal anchor links, capturing text and anchor."""
```

**Decisão**:

### 262 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:122` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      118          r"^\s*from\s+__future__\s+import\s"
      119      )
      120      "Regex: future import line."
      121      FROM_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   122          r"^\s*from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$", re.MULTILINE
      123      )
      124      "Regex: from-import with optional trailing comment."
      125      FROM_IMPORT_BLOCK_RE: Final[t.RegexPattern] = re.compile(
      126          r"^\s*from\s+([\w.]+)\s+import\s*\((.*?)\)", re.MULTILINE | re.DOTALL
```

**Decisão**:

### 263 · 🟡 MAJOR · CODE_SMELL · `python:S6019`
**Local**: `src/flext_infra/_constants/source_code.py:139` · **Effort**: 10min

> Fix this reluctant quantifier that will only ever match 0 repetitions.

```python
      135          re.MULTILINE,
      136      )
      137      "Regex: Final-annotated assignment (captures constant name)."
      138      DEPRECATED_RE: Final[t.RegexPattern] = re.compile(
>>>   139          r"^@deprecated.*\n(?:class|def)\s+(\w+).*?(?=\n(?:class |def |@|\Z))",
      140          re.MULTILINE | re.DOTALL,
      141      )
      142      "Regex: @deprecated decorated class/function block."
      143      REQUIRES_PYTHON_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 264 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:174` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      170          r"<!-- TOC START -->.*?<!-- TOC END -->", re.DOTALL
      171      )
      172      "Regex: TOC marker block (start..end), DOTALL."
      173      DUNDER_ALL_SINGLE_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   174          r"^(?P<prefix>__all__(?:\s*:\s*[^\n=]+)?\s*=\s*)\[(?P<body>[^\[\]\n]*)\]",
      175          re.MULTILINE,
      176      )
      177      "Regex: single-line ``__all__ = [...]`` declaration."
      178      DUNDER_ALL_MULTI_LINE_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 265 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:179` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      175          re.MULTILINE,
      176      )
      177      "Regex: single-line ``__all__ = [...]`` declaration."
      178      DUNDER_ALL_MULTI_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   179          r"^(?P<prefix>__all__(?:\s*:\s*[^\n=]+)?\s*=\s*)\[(?P<body>[^\[\]]*?)\]",
      180          re.MULTILINE | re.DOTALL,
      181      )
      182      "Regex: multi-line ``__all__ = [...]`` declaration (DOTALL body)."
      183      BLANK_LINE_RUN_RE: Final[t.RegexPattern] = re.compile(r"\n{4,}")
```

**Decisão**:

### 266 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:186` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      182      "Regex: multi-line ``__all__ = [...]`` declaration (DOTALL body)."
      183      BLANK_LINE_RUN_RE: Final[t.RegexPattern] = re.compile(r"\n{4,}")
      184      "Regex: 4+ consecutive newlines — collapsed to triple newline."
      185      LEGACY_TYPEALIAS_RE: Final[t.RegexPattern] = re.compile(
>>>   186          r"^(\w+)\s*:\s*TypeAlias\s*=\s*(.+)$", re.MULTILINE
      187      )
      188      "Regex: legacy ``X: TypeAlias = expr`` (rewritten to PEP 695 ``type X = ...``)."
      189      T_IMPORT_RE: Final[t.RegexPattern] = re.compile(
      190          r"^from\s+\S+\s+import\s+.*\bt\b", re.MULTILINE
```

**Decisão**:

### 267 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:190` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      186          r"^(\w+)\s*:\s*TypeAlias\s*=\s*(.+)$", re.MULTILINE
      187      )
      188      "Regex: legacy ``X: TypeAlias = expr`` (rewritten to PEP 695 ``type X = ...``)."
      189      T_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   190          r"^from\s+\S+\s+import\s+.*\bt\b", re.MULTILINE
      191      )
      192      "Regex: any ``from X import ... t ...`` line (canonical t import detector)."
      193      IMPORT_LINE_ANCHORED_RE: Final[t.RegexPattern] = re.compile(
      194          r"^(?:from\s+\S+\s+import\s+.+|import\s+.+)$", re.MULTILINE
```

**Decisão**:

### 268 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:194` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      190          r"^from\s+\S+\s+import\s+.*\bt\b", re.MULTILINE
      191      )
      192      "Regex: any ``from X import ... t ...`` line (canonical t import detector)."
      193      IMPORT_LINE_ANCHORED_RE: Final[t.RegexPattern] = re.compile(
>>>   194          r"^(?:from\s+\S+\s+import\s+.+|import\s+.+)$", re.MULTILINE
      195      )
      196      "Regex: any anchored import line (used to find the insertion offset)."
      197      IMPORT_PAREN_CLOSE_RE: Final[t.RegexPattern] = re.compile(r"^\)\s*$", re.MULTILINE)
      198      "Regex: closing ``)`` of a parenthesized import block, anchored at line start."
```

**Decisão**:

### 269 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:468` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      464          r"^([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*$"
      465      )
      466      "Regex: module-level ``X = Y`` identity-alias line."
      467      MODULE_ASSIGNMENT_RE: Final[t.RegexPattern] = re.compile(
>>>   468          r"^([A-Za-z_]\w*)\s*(?::\s*[^=]+)?=\s*(.+)$"
      469      )
      470      "Regex: module-level ``X [: T] = value`` assignment (captures name, value)."
      471      CAST_CALL_RE: Final[t.RegexPattern] = re.compile(
      472          r"\bcast\s*\(\s*[^,]+\s*,\s*([^)]+)\s*\)"
```

**Decisão**:

### 270 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:472` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      468          r"^([A-Za-z_]\w*)\s*(?::\s*[^=]+)?=\s*(.+)$"
      469      )
      470      "Regex: module-level ``X [: T] = value`` assignment (captures name, value)."
      471      CAST_CALL_RE: Final[t.RegexPattern] = re.compile(
>>>   472          r"\bcast\s*\(\s*[^,]+\s*,\s*([^)]+)\s*\)"
      473      )
      474      "Regex: ``cast(Type, value)`` call — captures the value to retain."
      475      AS_KEYWORD_RE: Final[t.RegexPattern] = re.compile(r"\s+as\s+")
      476      "Regex: ``<sp>as<sp>`` keyword for splitting import-as forms."
```

**Decisão**:

### 271 · 🟡 MAJOR · CODE_SMELL · `python:S6019`
**Local**: `src/flext_infra/_constants/source_code.py:478` · **Effort**: 10min

> Remove the '?' from this unnecessarily reluctant quantifier.

```python
      474      "Regex: ``cast(Type, value)`` call — captures the value to retain."
      475      AS_KEYWORD_RE: Final[t.RegexPattern] = re.compile(r"\s+as\s+")
      476      "Regex: ``<sp>as<sp>`` keyword for splitting import-as forms."
      477      FROM_IMPORT_SIMPLE_RE: Final[t.RegexPattern] = re.compile(
>>>   478          r"^from\s+([\w.]+)\s+import\s+(.+?)$", re.MULTILINE
      479      )
      480      "Regex: simple from-import line (no trailing-comment strip)."
      481      FROM_IMPORT_LINE_TRIM_RE: Final[t.RegexPattern] = re.compile(
      482          r"from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$"
```

**Decisão**:

### 272 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:478` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      474      "Regex: ``cast(Type, value)`` call — captures the value to retain."
      475      AS_KEYWORD_RE: Final[t.RegexPattern] = re.compile(r"\s+as\s+")
      476      "Regex: ``<sp>as<sp>`` keyword for splitting import-as forms."
      477      FROM_IMPORT_SIMPLE_RE: Final[t.RegexPattern] = re.compile(
>>>   478          r"^from\s+([\w.]+)\s+import\s+(.+?)$", re.MULTILINE
      479      )
      480      "Regex: simple from-import line (no trailing-comment strip)."
      481      FROM_IMPORT_LINE_TRIM_RE: Final[t.RegexPattern] = re.compile(
      482          r"from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$"
```

**Decisão**:

### 273 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:482` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      478          r"^from\s+([\w.]+)\s+import\s+(.+?)$", re.MULTILINE
      479      )
      480      "Regex: simple from-import line (no trailing-comment strip)."
      481      FROM_IMPORT_LINE_TRIM_RE: Final[t.RegexPattern] = re.compile(
>>>   482          r"from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$"
      483      )
      484      "Regex: from-import line with optional trailing comment (no anchor)."
      485  
      486      # --- Pytest log parsing patterns ---
```

**Decisão**:

### 274 · 🟡 MAJOR · BUG · `python:S5850`
**Local**: `src/flext_infra/_constants/source_code.py:502` · **Effort**: 10min

> Group parts of the regex together to make the intended operator precedence explicit.

```python
      498          r"^-- Docs: https://docs.pytest.org/"
      499      )
      500      "Regex: pytest warnings-section docs footer."
      501      PYTEST_FAILED_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   502          r"(^FAILED |::.* FAILED( |$))"
      503      )
      504      "Regex: pytest FAILED status line."
      505      PYTEST_ERROR_LINE_RE: Final[t.RegexPattern] = re.compile(
      506          r"(^ERROR |::.* ERROR( |$))"
```

**Decisão**:

### 275 · 🟡 MAJOR · BUG · `python:S5850`
**Local**: `src/flext_infra/_constants/source_code.py:506` · **Effort**: 10min

> Group parts of the regex together to make the intended operator precedence explicit.

```python
      502          r"(^FAILED |::.* FAILED( |$))"
      503      )
      504      "Regex: pytest FAILED status line."
      505      PYTEST_ERROR_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   506          r"(^ERROR |::.* ERROR( |$))"
      507      )
      508      "Regex: pytest ERROR status line."
      509      PYTEST_SKIPPED_LINE_RE: Final[t.RegexPattern] = re.compile(
      510          r"(^SKIPPED |::.* SKIPPED( |$))"
```

**Decisão**:

### 276 · 🟡 MAJOR · BUG · `python:S5850`
**Local**: `src/flext_infra/_constants/source_code.py:510` · **Effort**: 10min

> Group parts of the regex together to make the intended operator precedence explicit.

```python
      506          r"(^ERROR |::.* ERROR( |$))"
      507      )
      508      "Regex: pytest ERROR status line."
      509      PYTEST_SKIPPED_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   510          r"(^SKIPPED |::.* SKIPPED( |$))"
      511      )
      512      "Regex: pytest SKIPPED status line."
      513      PYTEST_WARNING_LINE_RE: Final[t.RegexPattern] = re.compile(
      514          r"\b[A-Za-z_][A-Za-z0-9_]*Warning\b"
```

**Decisão**:

### 277 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/source_code.py:623` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      619      "Minimum members for a union type to be normalizable."
      620  
      621      # --- Combined import detection (from + bare import) ---
      622      COMBINED_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   623          r"^(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+([\w.]+)(?:\s+as\s+(\w+))?)$",
      624          re.MULTILINE,
      625      )
      626      "Regex: matches both 'from X import Y' and 'import X [as Z]' forms."
      627      FUNCTION_DEF_SIMPLE_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 278 · 🟡 MAJOR · CODE_SMELL · `python:S5843`
**Local**: `src/flext_infra/_constants/source_code.py:623` · **Effort**: 10min

> Simplify this regular expression to reduce its complexity from 28 to the 20 allowed.

```python
      619      "Minimum members for a union type to be normalizable."
      620  
      621      # --- Combined import detection (from + bare import) ---
      622      COMBINED_IMPORT_RE: Final[t.RegexPattern] = re.compile(
>>>   623          r"^(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+([\w.]+)(?:\s+as\s+(\w+))?)$",
      624          re.MULTILINE,
      625      )
      626      "Regex: matches both 'from X import Y' and 'import X [as Z]' forms."
      627      FUNCTION_DEF_SIMPLE_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 279 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/validate.py:83` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
       79      SKILL_OWNER_MARKER_RE: Final[t.RegexPattern] = re.compile(
       80          r"^# Owner-Skill:\s+(.agents/skills/([a-z0-9][-a-z0-9]*)/SKILL\.md)\s*$"
       81      )
       82      SKILL_REPORT_ARTIFACT_NAME_RE: Final[t.RegexPattern] = re.compile(
>>>    83          r"^[a-z][-a-z0-9]*--[a-z]+--[a-z][-a-z0-9]*\.[a-z]+$"
       84      )
       85      SKILL_REPORT_ARTIFACT_SKILL_RE: Final[t.RegexPattern] = re.compile(
       86          r"^[a-z][-a-z0-9]*$"
       87      )
```

**Decisão**:

### 280 · 🟡 MAJOR · CODE_SMELL · `python:S8786`
**Local**: `src/flext_infra/_constants/validate.py:150` · **Effort**: 20min

> Simplify this regular expression to reduce its runtime, as it has super-linear performance due to backtracking.

```python
      146          r'(?m)^\[submodule "[^"]+"\]\s*$'
      147      )
      148      "``.gitmodules`` submodule section header at line start."
      149      GITMODULE_PATH_RE: Final[t.RegexPattern] = re.compile(
>>>   150          r"(?m)^[ \t]*path[ \t]*=[ \t]*(.+?)[ \t]*$"
      151      )
      152      "``.gitmodules`` path assignment value inside a submodule section."
      153      FOLLOW_SUPERPROJECT_BRANCH: Final[str] = "."
      154      GITIGNORE: Final[str] = ".gitignore"
```

**Decisão**:

### 281 · 🟡 MAJOR · CODE_SMELL · `python:S108`
**Local**: `src/flext_infra/_utilities/_git/worktree.py:578` · **Effort**: 5min

> Either remove or fill this block of code.

```python
      574          match identity:
      575              case [author_name, author_email] if (
      576                  author_name.strip() and author_email.strip()
      577              ):
>>>   578                  pass
      579              case _:
      580                  detail = "checkpoint parent has invalid author identity"
      581                  raise OSError(detail)
      582          commit_sha = str(
```

**Decisão**:

### 282 · 🟡 MAJOR · CODE_SMELL · `python:S108`
**Local**: `src/flext_infra/_utilities/discovery.py:139` · **Effort**: 5min

> Either remove or fill this block of code.

```python
      135                  case (_, package_name):
      136                      resolved_package: str = package_name
      137                      return resolved_package
      138                  case _:
>>>   139                      pass
      140          if project_root is None:
      141              return ""
      142  
      143          return FlextInfraUtilitiesPyproject.project_package_name(project_root)
```

**Decisão**:

### 283 · 🟡 MAJOR · CODE_SMELL · `pythonbugs:S2589`
**Local**: `src/flext_infra/_utilities/docs_fix.py:120` · **Effort**: 10min

> Fix this condition that always evaluates to false.

```python
      116              return f"[{text}]({fixed})"
      117  
      118          updated = c.Infra.MARKDOWN_LINK_RE.sub(replace_link, original)
      119          updated, toc_changed = FlextInfraUtilitiesDocs.update_toc(updated)
>>>   120          if apply and (link_count > 0 or toc_changed > 0) and updated != original:
      121              _ = md_file.write_text(updated, encoding=c.Cli.ENCODING_DEFAULT)
      122          return m.Infra.DocsPhaseItemModel(
      123              phase="fix", file=md_file.as_posix(), links=link_count, toc=toc_changed
      124          )
```

**Decisão**:

### 284 · 🟡 MAJOR · CODE_SMELL · `python:S108`
**Local**: `src/flext_infra/_utilities/docs_validate.py:45` · **Effort**: 5min

> Either remove or fill this block of code.

```python
       41          absence as "no override" can collapse with ``unwrap_or(())``.
       42          """
       43          match payload:
       44              case Mapping() as outer:
>>>    45                  pass
       46              case _:
       47                  return r[t.Infra.InfraSequence].fail("payload is not a mapping")
       48          match outer.get("docs_validation"):
       49              case Mapping() as inner:
```

**Decisão**:

### 285 · 🟡 MAJOR · CODE_SMELL · `python:S108`
**Local**: `src/flext_infra/_utilities/docs_validate.py:50` · **Effort**: 5min

> Either remove or fill this block of code.

```python
       46              case _:
       47                  return r[t.Infra.InfraSequence].fail("payload is not a mapping")
       48          match outer.get("docs_validation"):
       49              case Mapping() as inner:
>>>    50                  pass
       51              case _:
       52                  return r[t.Infra.InfraSequence].fail(
       53                      "docs_validation block missing or not a mapping"
       54                  )
```

**Decisão**:

### 286 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/_utilities/namespace.py:168` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      164              return None
      165          project_name = (
      166              project.name
      167              if project is not None and project.name
>>>   168              else FlextInfraUtilitiesDocsScope.project_name_from_payload(
      169                  resolved_root,
      170                  FlextInfraUtilitiesDocsScope.project_payload(resolved_root),
      171              )
      172              if (resolved_root / c.Infra.PYPROJECT_FILENAME).is_file()
```

**Decisão**:

### 287 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/_utilities/namespace.py:220` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      216          )
      217          family_tokens: t.StrSequence = (
      218              tuple(settings.private_family_tokens.get(family_alias, ()))
      219              if family_alias is not None
>>>   220              else (expected_family,)
      221              if expected_family
      222              else ()
      223          )
      224          return family_alias, expected_family, expected_alias, family_tokens
```

**Decisão**:

### 288 · 🟡 MAJOR · BUG · `pythonbugs:S2259`
**Local**: `src/flext_infra/_utilities/pyproject.py:169` · **Effort**: 10min

> Fix this call that leads to a attribute access on a value that can be 'None'.

```python
      165              for child in sorted(src_dir.iterdir()):
      166                  if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
      167                      child_path: Path = child
      168                      return child_path.name
>>>   169          project_name = FlextInfraUtilitiesPyproject.project_name_from_payload(
      170              project_root, payload
      171          )
      172          if project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN):
      173              msg = (
```

**Decisão**:

### 289 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/_utilities/rope_analysis_workspace.py:136` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      132              )
      133              package_name = (
      134                  cls._package_name_for_dir(package_dir, project_root=project_root)
      135                  if project_root is not None
>>>   136                  else module_name
      137                  if is_package_init
      138                  else module_name.rsplit(".", maxsplit=1)[0]
      139                  if "." in module_name
      140                  else ""
```

**Decisão**:

### 290 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/_utilities/rope_analysis_workspace.py:138` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      134                  cls._package_name_for_dir(package_dir, project_root=project_root)
      135                  if project_root is not None
      136                  else module_name
      137                  if is_package_init
>>>   138                  else module_name.rsplit(".", maxsplit=1)[0]
      139                  if "." in module_name
      140                  else ""
      141              )
      142              entry = m.Infra.RopeModuleIndexEntry(
```

**Decisão**:

### 291 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/_utilities/rope_analysis_workspace.py:225` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      221              )
      222              package_name = (
      223                  cls._package_name_for_dir(package_dir, project_root=project_root)
      224                  if project_root is not None
>>>   225                  else init_entry.package_name
      226                  if init_entry is not None
      227                  else ""
      228              )
      229              if package_name and package_name not in package_dir_by_name:
```

**Decisão**:

### 292 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/codegen/_codegen_generation_lazy_entries.py:101` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
       97  
       98      @staticmethod
       99      def _public_export_order_key(export_name: str) -> tuple[int, str]:
      100          """Classify one export using Ruff's canonical ``RUF022`` order."""
>>>   101          category = 0 if export_name.isupper() else 1 if export_name[:1].isupper() else 2
      102          # mro-wkii.17 (Codex): dependency order belongs to facade imports;
      103          # published __all__ values follow Ruff RUF022 (case-sensitive ASCII
      104          # secondary sort) so the two contracts never fight.
      105          return (category, export_name)
```

**Decisão**:

### 293 · 🟡 MAJOR · CODE_SMELL · `python:S8495`
**Local**: `src/flext_infra/codegen/_codegen_generation_type_checking.py:143` · **Effort**: 10min

> Refactor this function to always return tuples of the same length.

```python
      139                  )
      140              )
      141  
      142      @staticmethod
>>>   143      def generate_type_checking(
      144          groups: t.MappingKV[str, t.StrPairSequence],
      145          *,
      146          include_flext_types: bool = True,
      147          child_packages: t.StrSequence | None = None,
```

**Decisão**:

### 294 · 🟡 MAJOR · CODE_SMELL · `python:S108`
**Local**: `src/flext_infra/codegen/conform.py:2622` · **Effort**: 5min

> Either remove or fill this block of code.

```python
     2618              return r[bool].fail(f"mise-managed Beads CLI is unavailable: {ledger_root}")
     2619          version_parts = version.value.stdout.strip().split()
     2620          match version_parts:
     2621              case ["bd", "version", actual_version, *_]:
>>>  2622                  pass
     2623              case _:
     2624                  actual_version = ""
     2625          if actual_version != plan.expected_version:
     2626              return r[bool].fail(
```

**Decisão**:

### 295 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/codegen/lazy_init_planner.py:97` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
       93          empty_action: c.Infra.LazyInitAction = (
       94              c.Infra.LazyInitAction.WRITE
       95              if is_test_child_package
       96              else (
>>>    97                  c.Infra.LazyInitAction.REMOVE
       98                  if context.generated_init
       99                  else c.Infra.LazyInitAction.SKIP
      100              )
      101          )
```

**Decisão**:

### 296 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/deps/phases/ensure_pyright.py:405` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      401          expected_stub_path: str | None = (
      402              stub_rules.root_typings_paths[0]
      403              if is_root and stub_rules.root_typings_paths
      404              else (
>>>   405                  stub_rules.project_typings_paths[0]
      406                  if stub_rules.project_typings_paths
      407                  else None
      408              )
      409          )
```

**Decisão**:

### 297 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/docs/_auditor_report.py:52` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
       48          )
       49          result = (
       50              c.Infra.ResultStatus.OK
       51              if passed and issue_count == 0
>>>    52              else c.Infra.ResultStatus.WARN
       53              if passed
       54              else c.Infra.ResultStatus.FAIL
       55          )
       56          message = (
```

**Decisão**:

### 298 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/docs/_auditor_report.py:60` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
       56          message = (
       57              f"docstring coverage {docstring_coverage.percent}% below minimum "
       58              f"{params.docstring_min}%"
       59              if coverage_breached and docstring_coverage is not None
>>>    60              else "audit passed"
       61              if issue_count == 0
       62              else f"found {issue_count} issue(s)"
       63          )
       64          return m.Infra.DocsPhaseReport(
```

**Decisão**:

### 299 · 🟡 MAJOR · CODE_SMELL · `python:S1172`
**Local**: `src/flext_infra/fixers/base.py:36` · **Effort**: 5min

> Remove the unused function parameter "project_dir".

```python
       32          return fix_action.kind == self.kind
       33  
       34      def fix_project(
       35          self,
>>>    36          project_dir: Path,
       37          violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
       38          ctx: m.Infra.FixEnforcementCommand,
       39      ) -> m.Infra.ProjectFixResult:
       40          """Apply fixes for the given violations in ``project_dir``."""
```

**Decisão**:

### 300 · 🟡 MAJOR · CODE_SMELL · `python:S1172`
**Local**: `src/flext_infra/fixers/base.py:38` · **Effort**: 5min

> Remove the unused function parameter "ctx".

```python
       34      def fix_project(
       35          self,
       36          project_dir: Path,
       37          violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
>>>    38          ctx: m.Infra.FixEnforcementCommand,
       39      ) -> m.Infra.ProjectFixResult:
       40          """Apply fixes for the given violations in ``project_dir``."""
       41          msg = f"{self.__class__.__name__}.fix_project must be implemented"
       42          raise NotImplementedError(msg)
```

**Decisão**:

### 301 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/_census_filters.py:75` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
       71          """
       72          kinds = (
       73              selected_kinds
       74              if selected_kinds is not None
>>>    75              else (frozenset(kind_names) if kind_names else None)
       76          )
       77          if kinds and item.kind not in kinds:
       78              return False
       79          if not selected_families:
```

**Decisão**:

### 302 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/_census_rules_dispatch.py:188` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      184          resolved_convention = convention or rope.convention(file_path)
      185          resolved_kinds = (
      186              selected_kinds
      187              if selected_kinds is not None
>>>   188              else (frozenset(kind_names) if kind_names else frozenset())
      189          )
      190          symbol_index = self._lightweight_symbol_index(rope, file_path)
      191          violations: list[m.Infra.Census.Violation] = []
      192          fixes: list[m.Infra.Census.Fix] = []
```

**Decisão**:

### 303 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/_census_rules_struct.py:283` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      279                      file_path=file_path,
      280                      line=(
      281                          matched.line
      282                          if matched is not None
>>>   283                          else symbol[1]
      284                          if symbol is not None
      285                          else detector_violation.line
      286                      ),
      287                      description=detector_violation.suggestion,
```

**Decisão**:

### 304 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/_census_symbols.py:108` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      104          module_entry = rope.module(file_path)
      105          project_root = (
      106              layout.project_root
      107              if layout is not None
>>>   108              else module_entry.project_root
      109              if module_entry is not None
      110              else None
      111          )
      112          project_name = (
```

**Decisão**:

### 305 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/_census_symbols.py:115` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      111          )
      112          project_name = (
      113              layout.project_name
      114              if layout is not None
>>>   115              else project_root.name
      116              if project_root is not None
      117              else ""
      118          )
      119          return m.Infra.DetectorContext(
```

**Decisão**:

### 306 · 🟡 MAJOR · CODE_SMELL · `python:S8495`
**Local**: `src/flext_infra/refactor/declarative_enforcement.py:106` · **Effort**: 10min

> Refactor this function to always return tuples of the same length.

```python
      102          )
      103          raise ValueError(msg)
      104  
      105      @classmethod
>>>   106      def _detect_stub_files(
      107          cls, ctx: m.Infra.DetectorContext, *, rule_id: str
      108      ) -> t.SequenceOf[p.AttributeProbe]:
      109          """Return a probe for ``ctx.file_path`` when it is a prohibited ``.pyi``."""
      110          file_path = ctx.file_path
```

**Decisão**:

### 307 · 🟡 MAJOR · CODE_SMELL · `python:S1172`
**Local**: `src/flext_infra/refactor/namespace_enforcer_phases.py:24` · **Effort**: 5min

> Remove the unused function parameter "project_names".

```python
       20      _workspace_root: Path
       21      _rope_project: t.Infra.RopeProject
       22  
       23      def _resolve_project_roots(
>>>    24          self, *, project_names: t.StrSequence | None = None
       25      ) -> t.SequenceOf[Path]:
       26          """Resolve project roots."""
       27          msg = "_resolve_project_roots must be provided by the concrete enforcer"
       28          raise NotImplementedError(msg)
```

**Decisão**:

### 308 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/refactor/wrapper_root_namespace.py:126` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      122          """Build the canonical JSON payload from the accumulated wrapper run state."""
      123          mode_value = (
      124              "check"
      125              if self.check_only
>>>   126              else "dry-run"
      127              if self.effective_dry_run
      128              else "apply"
      129          )
      130          per_project_changes_payload: t.JsonDict = dict(
```

**Decisão**:

### 309 · 🟡 MAJOR · CODE_SMELL · `python:S8500`
**Local**: `src/flext_infra/transformers/_rewrite.py:15` · **Effort**: 5min

> Add the missing comparison methods or use "functools.total_ordering".

```python
       11  from dataclasses import dataclass
       12  
       13  
       14  @dataclass(frozen=True, slots=True)
>>>    15  class FlextInfraSourceRewrite:
       16      """One source rewrite: replace ``source[start:end]`` with ``text``."""
       17  
       18      start: int
       19      end: int
```

**Decisão**:

### 310 · 🟡 MAJOR · CODE_SMELL · `python:S1854`
**Local**: `src/flext_infra/transformers/signature_propagator.py:187` · **Effort**: 1min

> Remove this assignment to local variable 'joiner'; the value is never used.

```python
      183                  cursor += 1
      184              tail = result[cursor:].lstrip()
      185              head = result[:start].rstrip()
      186              head = head.removesuffix(",")
>>>   187              joiner = "" if not head.endswith("(") and tail.startswith(")") else " "
      188              if head.endswith("(") or tail.startswith(")"):
      189                  joiner = ""
      190              elif tail and not tail.startswith(","):
      191                  joiner = ", "
```

**Decisão**:

### 311 · 🟡 MAJOR · CODE_SMELL · `python:S107`
**Local**: `src/flext_infra/validate/stub_chain.py:38` · **Effort**: 20min

> Method "**init**" has 18 parameters, which is greater than the 13 authorized.

```python
       34      ] = False
       35      _runner: p.Cli.CommandRunner | None = m.PrivateAttr(default_factory=lambda: None)
       36  
       37      def __init__(
>>>    38          self,
       39          *,
       40          workspace_root: Path | None = None,
       41          apply_changes: bool = False,
       42          check_only: bool = False,
```

**Decisão**:

### 312 · 🟡 MAJOR · CODE_SMELL · `python:S3358`
**Local**: `src/flext_infra/workspace/rope.py:404` · **Effort**: 5min

> Extract this nested conditional expression into an independent statement.

```python
      400          )
      401          resolved_rel_path = (
      402              rel_path
      403              if rel_path is not None
>>>   404              else resolved_file.relative_to(package_dir)
      405              if resolved_file.is_relative_to(package_dir)
      406              else Path(resolved_file.name)
      407          )
      408          package_context = self.package_context(package_dir)
```

**Decisão**:

### 313 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:20` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       16  # === SECTION: managed tool bootstrap (managed) ===
       17  # Source: config:python_version, template (installer URLs)
       18  # mise installs the supported Python 3.13 family.
       19  # uv is supplied by the managed environment without a project patch pin.
>>>    20  RUN curl -fsSL https://mise.run | sh
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
       23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 314 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:23` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       19  # uv is supplied by the managed environment without a project patch pin.
       20  RUN curl -fsSL https://mise.run | sh
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       25  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       26  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       27  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 315 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:25` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       21  # uv is intentionally supplied by the caller environment; install it explicitly
       22  # in clean-machine images so the project bootstrap can resolve dependencies.
       23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    25  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       26  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       27  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       28      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       29  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 316 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:27` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       23  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       24  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       25  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       26  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
>>>    27  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       28      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       29  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       30  # End SECTION: managed tool bootstrap
       31  
```

**Decisão**:

### 317 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:22` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       18  # === SECTION: managed tool bootstrap (managed) ===
       19  # Source: config:python_version, template (installer URLs)
       20  # mise installs the supported Python 3.13 family.
       21  # uv is supplied by the managed environment without a project patch pin.
>>>    22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 318 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:25` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       21  # uv is supplied by the managed environment without a project patch pin.
       22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 319 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:27` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 320 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:29` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
>>>    29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       32  # End SECTION: managed tool bootstrap
       33  
```

**Decisão**:

### 321 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:23` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       19  # === SECTION: managed tool bootstrap (managed) ===
       20  # Source: config:python_version, template (installer URLs)
       21  # mise installs the supported Python 3.13 family.
       22  # uv is supplied by the managed environment without a project patch pin.
>>>    23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 322 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:26` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       22  # uv is supplied by the managed environment without a project patch pin.
       23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 323 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:28` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 324 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:30` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
>>>    30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       33  # End SECTION: managed tool bootstrap
       34  
```

**Decisão**:

### 325 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:22` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       18  # === SECTION: managed tool bootstrap (managed) ===
       19  # Source: config:python_version, template (installer URLs)
       20  # mise installs the supported Python 3.13 family.
       21  # uv is supplied by the managed environment without a project patch pin.
>>>    22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 326 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:25` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       21  # uv is supplied by the managed environment without a project patch pin.
       22  RUN curl -fsSL https://mise.run | sh
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 327 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:27` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       23  # uv is intentionally supplied by the caller environment; install it explicitly
       24  # in clean-machine images so the project bootstrap can resolve dependencies.
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 328 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:29` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       25  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       26  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       27  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       28  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
>>>    29  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       30      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       31  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       32  # End SECTION: managed tool bootstrap
       33  
```

**Decisão**:

### 329 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:23` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       19  # === SECTION: managed tool bootstrap (managed) ===
       20  # Source: config:python_version, template (installer URLs)
       21  # mise installs the supported Python 3.13 family.
       22  # uv is supplied by the managed environment without a project patch pin.
>>>    23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
```

**Decisão**:

### 330 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:26` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       22  # uv is supplied by the managed environment without a project patch pin.
       23  RUN curl -fsSL https://mise.run | sh
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
>>>    26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
```

**Decisão**:

### 331 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:28` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       24  # uv is intentionally supplied by the caller environment; install it explicitly
       25  # in clean-machine images so the project bootstrap can resolve dependencies.
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
>>>    28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
       30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
```

**Decisão**:

### 332 · 🟡 MAJOR · VULNERABILITY · `docker:S6506`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:30` · **Effort**: 30min

> Not enforcing HTTPS here might allow for redirections to insecure websites. Make sure it is safe here.

```Dockerfile
       26  RUN curl -fsSL https://astral.sh/uv/install.sh | sh
       27  # tokei (and any future cargo-backed mise tool) needs a Rust toolchain.
       28  RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
       29  # go is required for mise-managed beads (go:github.com/steveyegge/beads/cmd/bd).
>>>    30  RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
       31      && ln -sf /usr/local/go/bin/go /usr/local/bin/go
       32  ENV PATH="/usr/local/go/bin:/root/.local/bin:/root/.cargo/bin:/root/.local/share/mise/shims:${PATH}"
       33  # End SECTION: managed tool bootstrap
       34  
```

**Decisão**:

### 333 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/codegen/test_root_artifact_ownership.py:86` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       82                  )
       83              }
       84          )
       85  
>>>    86          with pytest.raises(ValueError, match="ownership mismatch"):
       87              type(spec).model_validate(mutated)
       88  
       89      def test_github_managed_owner_must_be_full(self) -> None:
       90          """Reject weaker policies for every config-declared GitHub artifact."""
```

**Decisão**:

### 334 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/codegen/test_root_artifact_ownership.py:106` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      102                  )
      103              }
      104          )
      105  
>>>   106          with pytest.raises(ValueError, match="must be full-managed"):
      107              type(spec).model_validate(mutated)
      108  
      109      def test_conform_uses_one_fixed_point_plan(self, tmp_path: Path) -> None:
      110          root = tmp_path / "flext-demo"
```

**Decisão**:

### 335 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:62` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       58          policy = config.Infra.tooling.tools.pytest
       59          payload = policy.model_dump(by_alias=True)
       60          payload[field] = 0
       61  
>>>    62          with pytest.raises(c.ValidationError, match="greater than"):
       63              type(policy).model_validate(payload)
       64  
       65      @pytest.mark.parametrize(
       66          "override", ["-o", "-o=addopts=", "--override-ini", "--override-ini=addopts="]
```

**Decisão**:

### 336 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:73` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       69          policy = config.Infra.tooling.tools.pytest
       70          payload = policy.model_dump(by_alias=True)
       71          payload["standard-addopts"] = [override]
       72  
>>>    73          with pytest.raises(
       74              c.ValidationError,
       75              match="pytest runtime policy options are derived from typed fields",
       76          ):
       77              type(policy).model_validate(payload)
```

**Decisão**:

### 337 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:86` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       82          payload["run-timeout-seconds"] = (
       83              policy.case_timeout_seconds + policy.termination_grace_seconds - 1
       84          )
       85  
>>>    86          with pytest.raises(
       87              c.ValidationError,
       88              match="pytest run timeout must include item and termination budgets",
       89          ):
       90              type(policy).model_validate(payload)
```

**Decisão**:

### 338 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:99` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       95          payload["process-timeout-seconds"] = (
       96              policy.run_timeout_seconds + policy.termination_grace_seconds
       97          )
       98  
>>>    99          with pytest.raises(
      100              c.ValidationError,
      101              match="pytest process timeout must exceed run and termination budgets",
      102          ):
      103              type(policy).model_validate(payload)
```

**Decisão**:

### 339 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:110` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      106          policy = config.Infra.tooling.tools.pytest
      107          payload = policy.model_dump(by_alias=True)
      108          payload["progress-args"] = ["-q"]
      109  
>>>   110          with pytest.raises(
      111              c.ValidationError,
      112              match="pytest progress args must expose verbose item progress",
      113          ):
      114              type(policy).model_validate(payload)
```

**Decisão**:

### 340 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/deps/test_pytest_timeout_config.py:138` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      134          policy = config.Infra.tooling.tools.pytest
      135          payload = policy.model_dump(by_alias=True)
      136          payload["report-args"] = [argument]
      137  
>>>   138          with pytest.raises(
      139              c.ValidationError,
      140              match="pytest reporting args must not override runner-owned policy",
      141          ):
      142              type(policy).model_validate(payload)
```

**Decisão**:

### 341 · 🟡 MAJOR · CODE_SMELL · `python:S8997`
**Local**: `tests/unit/io/test_infra_terminal_detection.py:51` · **Effort**: 5min

> Use the "monkeypatch" fixture for temporary modifications instead of manually modifying global state.

```python
       47          tm.that(_Stream(tty=True).isatty(), eq=True)
       48          tm.that(_Stream(tty=False).isatty(), eq=False)
       49  
       50      def test_env_applies_and_restores_environment(self) -> None:
>>>    51          os.environ["FLEXT_KEEP"] = "yes"
       52          with _env(FLEXT_KEEP=None, FLEXT_TEST="1"):
       53              tm.that(os.environ.get("FLEXT_TEST"), eq="1")
       54              tm.that(os.environ, lacks="FLEXT_KEEP")
       55          tm.that(os.environ.get("FLEXT_KEEP"), eq="yes")
```

**Decisão**:

### 342 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/refactor/test_declarative_enforcement.py:151` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      147  
      148      def test_missing_rope_resource_fails_loud(self, tmp_path: Path) -> None:
      149          """Missing source resources are detector failures, not clean scans."""
      150          missing = tmp_path / "missing.py"
>>>   151          with (
      152              u.Infra.open_project(tmp_path) as rope_project,
      153              pytest.raises(RuntimeError, match="unable to resolve rope resource"),
      154          ):
      155              FlextInfraRefactorDeclarativeEnforcement.detect(
```

**Decisão**:

### 343 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/refactor/test_declarative_enforcement.py:174` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      170              msg = "class placement exploded"
      171              raise RuntimeError(msg)
      172  
      173          monkeypatch.setattr(FlextInfraClassPlacementDetector, "detect_file", _fail)
>>>   174          with (
      175              u.Infra.open_project(tmp_path) as rope_project,
      176              pytest.raises(RuntimeError, match="class placement detector failed"),
      177          ):
      178              FlextInfraRefactorDeclarativeEnforcement.detect(
```

**Decisão**:

### 344 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/refactor/test_declarative_enforcement.py:220` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      216          )
      217          source = tmp_path / "consumer.py"
      218          source.write_text("", encoding="utf-8")
      219          tm.that(FlextInfraRefactorDeclarativeEnforcement.supports(rule), eq=False)
>>>   220          with (
      221              u.Infra.open_project(tmp_path) as rope_project,
      222              pytest.raises(ValueError, match="unsupported declarative"),
      223          ):
      224              FlextInfraRefactorDeclarativeEnforcement.detect(
```

**Decisão**:

### 345 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/release/orchestrator_helpers_tests.py:271` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      267                  artifacts=(),
      268              )
      269  
      270              tm.that(record.exit_code, eq=-9)
>>>   271              with pytest.raises(c.ValidationError):
      272                  m.Infra.BuildRecord.model_validate({
      273                      "project": "flext-a",
      274                      "path": str(tmp_path.resolve()),
      275                      "exit_code": "-9",
```

**Decisão**:

### 346 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/test_infra_rope_service.py:477` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
      473                  def import_dependents(self, import_target: str) -> str:
      474                      del import_target
      475                      return "invalid"
      476  
>>>   477              with pytest.raises(
      478                  TypeError, match=r"rope import_dependents returned non-tuple for demo"
      479              ):
      480                  u.Infra.indexed_search_resources(
      481                      _BrokenWorkspace(),
```

**Decisão**:

### 347 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/validate/pytest_selector_tests.py:48` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       44              "tests/test_sample.py\n--maxfail=0",
       45          ],
       46      )
       47      def test_file_rejects_non_normalized_or_control_text(self, file: str) -> None:
>>>    48          with pytest.raises(c.ValidationError, match="file must"):
       49              FlextInfraPytestSelectorValidator(workspace_root=Path.cwd(), file=file)
       50  
       51      def test_what_accepts_only_canonical_test_modes(self) -> None:
       52          validator = FlextInfraPytestSelectorValidator(
```

**Decisão**:

### 348 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/validate/pytest_selector_tests.py:62` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       58                  FlextInfraPytestSelectorValidator(
       59                      workspace_root=Path.cwd(), what=what
       60                  ).execute()
       61              )
>>>    62          with pytest.raises(c.ValidationError, match="what must be"):
       63              FlextInfraPytestSelectorValidator(
       64                  workspace_root=Path.cwd(), what="$(shell touch marker)"
       65              )
       66          with pytest.raises(c.ValidationError, match="what must be"):
```

**Decisão**:

### 349 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/validate/pytest_selector_tests.py:66` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       62          with pytest.raises(c.ValidationError, match="what must be"):
       63              FlextInfraPytestSelectorValidator(
       64                  workspace_root=Path.cwd(), what="$(shell touch marker)"
       65              )
>>>    66          with pytest.raises(c.ValidationError, match="what must be"):
       67              FlextInfraPytestSelectorValidator(workspace_root=Path.cwd(), what="cov")
       68          with pytest.raises(
       69              c.ValidationError, match="cache-status rejects FILE and MATCH"
       70          ):
```

**Decisão**:

### 350 · 🟡 MAJOR · CODE_SMELL · `python:S5778`
**Local**: `tests/unit/validate/pytest_selector_tests.py:68` · **Effort**: 5min

> Refactor this exception test to have only one invocation possibly throwing an exception.

```python
       64                  workspace_root=Path.cwd(), what="$(shell touch marker)"
       65              )
       66          with pytest.raises(c.ValidationError, match="what must be"):
       67              FlextInfraPytestSelectorValidator(workspace_root=Path.cwd(), what="cov")
>>>    68          with pytest.raises(
       69              c.ValidationError, match="cache-status rejects FILE and MATCH"
       70          ):
       71              FlextInfraPytestSelectorValidator(
       72                  workspace_root=Path.cwd(), what="cache-status", match="x"
```

**Decisão**:

### 351 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `conftest.py:20` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
       16      if (
       17          existing_package is None
       18          or Path(getattr(existing_package, "__file__", "")).resolve() != init_file
       19      ):
>>>    20          for module_name in list(sys.modules):
       21              if module_name == package_name or module_name.startswith(
       22                  f"{package_name}."
       23              ):
       24                  sys.modules.pop(module_name, None)
```

**Decisão**:

### 352 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/codegen_lazy.py:25` · **Effort**: 5min

> Use concise character class syntax '\d' instead of '[0-9]'.

```python
       21      "Root public ABI contract module consumed by lazy-init planning."
       22      ROOT_EXPORTS_DIR: Final[str] = "_constants"
       23      "Directory under each package where lazy-init registries must live."
       24      GENERATED_EXPORT_SIDECAR_RE: Final[t.RegexPattern] = re.compile(
>>>    25          r"^(?:_exports(?:_lazy(?:_part_[0-9]+)?)?|_lazy_exports)\.py$"
       26      )
       27      "Regex matching every generated lazy-export sidecar filename "
       28      "(``_exports.py``, ``_exports_lazy.py``, ``_exports_lazy_part_N.py``, "
       29      "``_lazy_exports.py``); these reserved names are superseded by the inline "
```

**Decisão**:

### 353 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/codegen_lazy.py:46` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
       42          "install_lazy_exports",
       43      })
       44      "Names bound eagerly by the canonical root initializer template."
       45      TEST_ONLY_SOURCE_MODULE_RE: Final[t.RegexPattern] = re.compile(
>>>    46          r"^(?:_?test(?:_[A-Za-z0-9_]+)?|[A-Za-z0-9_]+_tests?)\.py$"
       47      )
       48      "Test-module filenames forbidden from installable package export maps."
       49      INIT_PY: Final[str] = "__init__.py"
       50      "Standard Python package initializer filename."
```

**Decisão**:

### 354 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/codegen_lazy.py:46` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
       42          "install_lazy_exports",
       43      })
       44      "Names bound eagerly by the canonical root initializer template."
       45      TEST_ONLY_SOURCE_MODULE_RE: Final[t.RegexPattern] = re.compile(
>>>    46          r"^(?:_?test(?:_[A-Za-z0-9_]+)?|[A-Za-z0-9_]+_tests?)\.py$"
       47      )
       48      "Test-module filenames forbidden from installable package export maps."
       49      INIT_PY: Final[str] = "__init__.py"
       50      "Standard Python package initializer filename."
```

**Decisão**:

### 355 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/make.py:23` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
       19  
       20      # Why: conform Makefile policy classifies declarations via these patterns;
       21      # they belong on c.Infra, not as leaf module re.compile copies.
       22      MAKE_ASSIGNMENT_RE: Final[t.RegexPattern] = re.compile(
>>>    23          r"^[A-Za-z_][A-Za-z0-9_]*\s*(?::?:|\?|\+)?="
       24      )
       25      "GNU Make variable assignment at column 0 (``=``, ``:=``, ``::=``, ``?=``, ``+=``)."
       26      MAKE_DIRECTIVE_RE: Final[t.RegexPattern] = re.compile(
       27          r"^(?:export|unexport|override|include|-include|sinclude|vpath)\b"
```

**Decisão**:

### 356 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/refactor.py:666` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
      662      "Public accessor name prefixes that should be renamed (drop the prefix or use a canonical verb)."
      663  
      664      # --- MRO scan patterns ---
      665      MRO_SCAN_TYPE_PATTERN: Final[t.RegexPattern] = re.compile(
>>>   666          r"^_?[A-Za-z][A-Za-z0-9_]*$"
      667      )
      668      "Regex: valid Python identifier (used for MRO type/class name validation)."
      669      MRO_SCAN_PROTOCOL_BASE_PATTERN: Final[t.RegexPattern] = re.compile(
      670          r"(^|[\s,(])(?:[A-Za-z_]\w*\.)?Protocol(?:\[[^\]]+\])?(?=$|[\s,)])"
```

**Decisão**:

### 357 · ⚪ MINOR · CODE_SMELL · `python:S5857`
**Local**: `src/flext_infra/_constants/source_code.py:134` · **Effort**: 3min

> Replace this use of a reluctant quantifier with `[^\]]*`.

```python
      130      "Regex: docstring opening (single/triple quote)."
      131      CONSTANT_NAME_RE: Final[t.RegexPattern] = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
      132      "Regex: constant name pattern (UPPER_CASE with optional leading underscore)."
      133      FINAL_ASSIGN_RE: Final[t.RegexPattern] = re.compile(
>>>   134          r"^(_?[A-Z][A-Z0-9_]*)\s*:\s*(?:Final|typing\.Final)(?:\[.*?\])?\s*=",
      135          re.MULTILINE,
      136      )
      137      "Regex: Final-annotated assignment (captures constant name)."
      138      DEPRECATED_RE: Final[t.RegexPattern] = re.compile(
```

**Decisão**:

### 358 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_constants/source_code.py:514` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
      510          r"(^SKIPPED |::.* SKIPPED( |$))"
      511      )
      512      "Regex: pytest SKIPPED status line."
      513      PYTEST_WARNING_LINE_RE: Final[t.RegexPattern] = re.compile(
>>>   514          r"\b[A-Za-z_][A-Za-z0-9_]*Warning\b"
      515      )
      516      "Regex: concrete Python warning class in pytest output."
      517      PYTEST_FAILURES_OR_ERRORS_RE: Final[t.RegexPattern] = re.compile(
      518          r"^=+ (FAILURES|ERRORS) =+"
```

**Decisão**:

### 359 · ⚪ MINOR · CODE_SMELL · `python:S7500`
**Local**: `src/flext_infra/_models/refactor_namespace_enforcer.py:467` · **Effort**: 5min

> Replace this comprehension with passing the iterable to the collection constructor call

```python
      463                  self.inline_import_violations,
      464                  self.silent_failure_violations,
      465                  self.parse_failures,
      466              )
>>>   467              return missing_facades or any(v for v in violation_fields)
      468  
      469      class WorkspaceEnforcementReport(m.ArbitraryTypesModel):
      470          """Workspace enforcement report."""
      471  
```

**Decisão**:

### 360 · ⚪ MINOR · CODE_SMELL · `python:S5713`
**Local**: `src/flext_infra/_utilities/_git/repo.py:38` · **Effort**: 1min

> Remove this redundant Exception class; it derives from another which is already caught.

```python
       34      if resolved is None:
       35          return r[bool].fail(f"git executable not found on PATH: {c.Infra.GIT}")
       36      try:
       37          Git.refresh(resolved)
>>>    38      except (FileNotFoundError, OSError) as exc:
       39          return r[bool].fail(f"git binary refresh failed: {exc}")
       40      return r[bool].ok(True)
       41  
       42  
```

**Decisão**:

### 361 · ⚪ MINOR · CODE_SMELL · `python:S5685`
**Local**: `src/flext_infra/_utilities/_rope_core_resources.py:124` · **Effort**: 10min

> Move this assignment out of the argument list; ":=" operator is confusing in this context.

```python
      120                  (
      121                      file_path
      122                      for resource in resources
      123                      if (
>>>   124                          file_path
      125                          := FlextInfraUtilitiesRopeCoreResourcesMixin.resource_file_path(
      126                              rope_project, resource
      127                          )
      128                      )
```

**Decisão**:

### 362 · ⚪ MINOR · CODE_SMELL · `python:S7498`
**Local**: `src/flext_infra/_utilities/dependencies.py:314` · **Effort**: 5min

> Replace this constructor call with a literal.

```python
      310          """Collect optional dependency groups from one TOML document."""
      311          normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
      312          if not normalized:
      313              # mro-j47u (codex): keep the empty mapping immutable and fully typed.
>>>   314              return MappingProxyType(dict[str, tuple[str, ...]]())
      315          return cls.project_dev_groups_from_payload(normalized)
      316  
      317      @classmethod
      318      def canonical_dev_dependencies(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
```

**Decisão**:

### 363 · ⚪ MINOR · VULNERABILITY · `python:S5332`
**Local**: `src/flext_infra/_utilities/docs_audit.py:29` · **Effort**: 30min

> Using HTTP protocol is insecure. Use HTTPS instead.

```python
       25      @staticmethod
       26      def docs_is_external(target: str) -> bool:
       27          """Return whether a docs link target points outside the repository."""
       28          lower: str = u.norm_str(target, case="lower").lstrip("<")
>>>    29          return lower.startswith(("http://", "https://", "mailto:", "tel:", "data:"))
       30  
       31      @staticmethod
       32      def docs_normalize_link(target: str) -> str:
       33          """Strip fragments and query strings from a markdown link target."""
```

**Decisão**:

### 364 · ⚪ MINOR · VULNERABILITY · `python:S5332`
**Local**: `src/flext_infra/_utilities/docs_fix.py:27` · **Effort**: 30min

> Using HTTP protocol is insecure. Use HTTPS instead.

```python
       23  
       24      @staticmethod
       25      def docs_maybe_fix_link(md_file: Path, raw_link: str) -> str | None:
       26          """Return a corrected link target when a simple fix is possible."""
>>>    27          if raw_link.startswith(("http://", "https://")):
       28              return FlextInfraUtilitiesDocsGithubLinks.docs_rewrite_github_url(raw_link)
       29          result: str | None = None
       30          if not raw_link.startswith(("mailto:", "tel:", "#")):
       31              base = raw_link.split("#", maxsplit=1)[0]
```

**Decisão**:

### 365 · ⚪ MINOR · VULNERABILITY · `python:S5332`
**Local**: `src/flext_infra/_utilities/docs_generate.py:460` · **Effort**: 30min

> Using HTTP protocol is insecure. Use HTTPS instead.

```python
      456          """Replace local markdown links with plain text while preserving externals."""
      457          sanitized: str = c.Infra.MARKDOWN_LINK_RE.sub(
      458              lambda match: (
      459                  match.group(0)
>>>   460                  if match.group(2).startswith(("http://", "https://", "#", "mailto:"))
      461                  else match.group(1)
      462              ),
      463              content,
      464          )
```

**Decisão**:

### 366 · ⚪ MINOR · VULNERABILITY · `python:S5332`
**Local**: `src/flext_infra/_utilities/docs_render.py:114` · **Effort**: 30min

> Using HTTP protocol is insecure. Use HTTPS instead.

```python
      110          READMEs render on GitHub and can use relative paths; generated
      111          ``docs/index.md`` pages are built by MkDocs with ``docs_dir`` isolation,
      112          so governance pointers must be absolute GitHub URLs.
      113          """
>>>   114          if prefix.startswith(("http://", "https://")):
      115              kind = "tree" if is_dir else "blob"
      116              branch = "0.12.0-dev"
      117              for repo in config.Infra.codegen.make.docs.github_repos:
      118                  if repo.organization == "flext-sh" and repo.repository == "flext":
```

**Decisão**:

### 367 · ⚪ MINOR · CODE_SMELL · `python:S6353`
**Local**: `src/flext_infra/_utilities/mro_scan_source.py:20` · **Effort**: 5min

> Use concise character class syntax '\w' instead of '[A-Za-z0-9_]'.

```python
       16      """Find facade aliases and movable top-level symbols using Python AST."""
       17  
       18      _CONSTANT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
       19      _IDENTIFIER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
>>>    20          r"^_?[A-Za-z][A-Za-z0-9_]*$"
       21      )
       22      _FACADE_ALIAS_TEMPLATE: ClassVar[str] = r"(?m)^\s*{alias}\s*=\s*(\w+{suffix})\s*$"
       23      _CLASS_SUFFIX_TEMPLATE: ClassVar[str] = r"(?m)^class\s+(\w+{suffix})\b"
       24  
```

**Decisão**:

### 368 · ⚪ MINOR · CODE_SMELL · `python:S7498`
**Local**: `src/flext_infra/_utilities/namespace_facades.py:53` · **Effort**: 5min

> Replace this constructor call with a literal.

```python
       49      def _compute_base_chains(*, project_root: Path) -> t.StrSequenceMapping:
       50          """Compute base chains."""
       51          pyproject_path = project_root / c.Infra.PYPROJECT_FILENAME
       52          if not pyproject_path.exists():
>>>    53              return MappingProxyType(dict[str, tuple[str, ...]]())
       54          try:
       55              raw = pyproject_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
       56          except OSError:
       57              return MappingProxyType(dict[str, tuple[str, ...]]())
```

**Decisão**:

### 369 · ⚪ MINOR · CODE_SMELL · `python:S7498`
**Local**: `src/flext_infra/_utilities/namespace_facades.py:57` · **Effort**: 5min

> Replace this constructor call with a literal.

```python
       53              return MappingProxyType(dict[str, tuple[str, ...]]())
       54          try:
       55              raw = pyproject_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
       56          except OSError:
>>>    57              return MappingProxyType(dict[str, tuple[str, ...]]())
       58          payload = u.Cli.toml_mapping_from_text(raw)
       59          if payload is None:
       60              return MappingProxyType(dict[str, tuple[str, ...]]())
       61          dep_names = (
```

**Decisão**:

### 370 · ⚪ MINOR · CODE_SMELL · `python:S7498`
**Local**: `src/flext_infra/_utilities/namespace_facades.py:60` · **Effort**: 5min

> Replace this constructor call with a literal.

```python
       56          except OSError:
       57              return MappingProxyType(dict[str, tuple[str, ...]]())
       58          payload = u.Cli.toml_mapping_from_text(raw)
       59          if payload is None:
>>>    60              return MappingProxyType(dict[str, tuple[str, ...]]())
       61          dep_names = (
       62              FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
       63                  t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
       64              )
```

**Decisão**:

### 371 · ⚪ MINOR · CODE_SMELL · `python:S5685`
**Local**: `src/flext_infra/_utilities/rope_analysis.py:1658` · **Effort**: 10min

> Move this assignment out of the argument list; ":=" operator is confusing in this context.

```python
     1654              line=line if isinstance(line, int) and line > 0 else 1,
     1655              bases=tuple(
     1656                  base_name
     1657                  for base in raw_bases
>>>  1658                  if (base_name := FlextInfraUtilitiesRopeAnalysis._class_base_name(base))
     1659              ),
     1660          )
     1661  
     1662      @staticmethod
```

**Decisão**:

### 372 · ⚪ MINOR · CODE_SMELL · `python:S7498`
**Local**: `src/flext_infra/_utilities/work_saga_start.py:171` · **Effort**: 5min

> Replace this constructor call with a literal.

```python
      167              if shown.failure:
      168                  lines.append(f"bead: error={shown.error}")
      169              else:
      170                  meta = shown.value.get("metadata")
>>>   171                  meta_obj = meta if isinstance(meta, dict) else dict[str, object]()
      172                  lines.extend((
      173                      f"bead: {bead}",
      174                      f"bead_status: {shown.value.get('status')}",
      175                      f"assignee: {shown.value.get('assignee')}",
```

**Decisão**:

### 373 · ⚪ MINOR · CODE_SMELL · `python:S7508`
**Local**: `src/flext_infra/codegen/_codegen_generation_lazy_entries.py:90` · **Effort**: 5min

> Remove this redundant call.

```python
       86          """Build root public exports in Ruff's canonical isort-style order."""
       87          # mro-wkii.17.26 (codex): the planner is the sole ABI filter; rendering
       88          # only orders its validated contract and must not reinterpret target paths.
       89          _ = lazy_filtered
>>>    90          export_candidates = tuple(dict.fromkeys(exports))
       91          return tuple(
       92              sorted(
       93                  export_candidates,
       94                  key=FlextInfraCodegenGenerationLazyEntriesMixin._public_export_order_key,
```

**Decisão**:

### 374 · ⚪ MINOR · CODE_SMELL · `python:S5685`
**Local**: `src/flext_infra/codegen/constants_quality_gate.py:265` · **Effort**: 10min

> Move this assignment out of the argument list; ":=" operator is confusing in this context.

```python
      261          )
      262          metric_checks = tuple(
      263              m.Infra.QualityGateCheck(
      264                  name=name,
>>>   265                  passed=(value := u.Cli.json_nested_int(after_metrics, metric)) == 0,
      266                  detail=f"{label}={value}",
      267                  critical=True,
      268              )
      269              for name, metric, label in metric_check_rows
```

**Decisão**:

### 375 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/deps/_modernizer_constraints.py:57` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
       53          location: str,
       54      ) -> t.StrSequence:
       55          """Rewrite one Poetry dependency table using the locked version policy."""
       56          changes: t.MutableSequenceOf[str] = []
>>>    57          for dependency_name in list(dependencies):
       58              current_value = dependencies.get(dependency_name)
       59              rewritten_value = u.Infra.rewrite_poetry_constraint(
       60                  dependency_name,
       61                  current_value,
```

**Decisão**:

### 376 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/deps/_modernizer_constraints.py:101` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
       97              if optional_dependencies is not None:
       98                  optional_dependencies = u.Cli.toml_mapping_ensure_table(
       99                      project, c.Infra.OPTIONAL_DEPENDENCIES
      100                  )
>>>   101                  for group_name in list(optional_dependencies):
      102                      group_deps, group_changes = self._rewrite_requirement_group(
      103                          optional_dependencies.get(group_name),
      104                          locked_versions=locked_versions,
      105                          internal_names=internal_names,
```

**Decisão**:

### 377 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/deps/_modernizer_constraints.py:119` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
      115          if dependency_groups_view is not None:
      116              dependency_groups = u.Cli.toml_mapping_ensure_table(
      117                  payload, c.Infra.DEPENDENCY_GROUPS
      118              )
>>>   119              for group_name in list(dependency_groups):
      120                  group_deps, group_changes = self._rewrite_requirement_group(
      121                      dependency_groups.get(group_name),
      122                      locked_versions=locked_versions,
      123                      internal_names=internal_names,
```

**Decisão**:

### 378 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/deps/_modernizer_constraints.py:146` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
      142          poetry_groups = u.Cli.toml_mapping_path(
      143              payload, (c.Infra.TOOL, c.Infra.POETRY, c.Infra.GROUP)
      144          )
      145          if poetry_groups is not None:
>>>   146              for group_name in list(poetry_groups):
      147                  group_dependencies = u.Cli.toml_mapping_path(
      148                      payload,
      149                      (
      150                          c.Infra.TOOL,
```

**Decisão**:

### 379 · ⚪ MINOR · CODE_SMELL · `python:S7500`
**Local**: `src/flext_infra/deps/detection_analysis.py:94` · **Effort**: 5min

> Replace this comprehension with passing the iterable to the collection constructor call

```python
       90          poetry = self._mapping_from_value(tool.get(c.Infra.POETRY))
       91          group = self._mapping_from_value(poetry.get(c.Infra.GROUP))
       92          typings_group = self._mapping_from_value(group.get(c.Infra.TYPINGS))
       93          deps = self._mapping_from_value(typings_group.get(c.Infra.DEPENDENCIES))
>>>    94          names.update(key for key in deps)
       95          project = self._mapping_from_value(data.get(c.Infra.PROJECT))
       96          optional = self._mapping_from_value(project.get(c.Infra.OPTIONAL_DEPENDENCIES))
       97          typings = optional.get(c.Infra.TYPINGS)
       98          if isinstance(typings, list):
```

**Decisão**:

### 380 · ⚪ MINOR · CODE_SMELL · `python:S7500`
**Local**: `src/flext_infra/deps/detection_analysis.py:109` · **Effort**: 5min

> Replace this comprehension with passing the iterable to the collection constructor call

```python
      105                      .split("==", maxsplit=1)[0]
      106                      .strip()
      107                  )
      108          elif isinstance(typings, Mapping):
>>>   109              names.update(key for key in typings)
      110          return sorted(names)
      111  
      112      def get_required_typings(
      113          self,
```

**Decisão**:

### 381 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/deps/phases/ensure_ruff.py:258` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
      254          )
      255          stale_patterns = (
      256              [
      257                  pattern
>>>   258                  for pattern in list(per_file_ignores)
      259                  if pattern not in effective_ignores
      260              ]
      261              if per_file_ignores is not None
      262              else ()
```

**Decisão**:

### 382 · ⚪ MINOR · CODE_SMELL · `python:S1940`
**Local**: `src/flext_infra/refactor/_census_collect_helpers.py:92` · **Effort**: 2min

> Use the opposite operator (">") instead.

```python
       88          declarative_rules = cls._declarative_rules_for_selection(rule_names)
       89          declarative_rule_ids = frozenset(rule.id for rule in declarative_rules)
       90          if declarative_rule_ids and selected_rules <= declarative_rule_ids:
       91              return False
>>>    92          return not selected_rules <= cls._LIGHTWEIGHT_MODULE_RULES
       93  
       94      @staticmethod
       95      def _declarative_rules_for_selection(
       96          rule_names: t.StrSequence | None,
```

**Decisão**:

### 383 · ⚪ MINOR · CODE_SMELL · `python:S6659`
**Local**: `src/flext_infra/transformers/signature_propagator.py:152` · **Effort**: 5min

> Use `not` and `endswith` here.

```python
      148                      if key not in existing
      149                  ]
      150                  if additions:
      151                      inner = result[:close].rstrip()
>>>   152                      inner_has_args = inner.endswith(",") or inner[-1:] != "("
      153                      sep = ", " if inner_has_args and not inner.endswith(",") else ""
      154                      if inner.endswith(","):
      155                          sep = " "
      156                      if inner.endswith("("):
```

**Decisão**:

### 384 · ⚪ MINOR · CODE_SMELL · `python:S7504`
**Local**: `src/flext_infra/validate/import_cycles.py:198` · **Effort**: 5min

> Remove this unnecessary `list()` call on an already iterable object.

```python
      194                      if top == node:
      195                          break
      196                  result.append(scc)
      197  
>>>   198          for node in list(graph):
      199              if node not in index:
      200                  strongconnect(node)
      201          return result
      202  
```

**Decisão**:

### 385 · ⚪ MINOR · VULNERABILITY · `docker:S6471`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:8` · **Effort**: 15min

> The "alpine" image runs with "root" as the default user. Make sure it is safe here.

```Dockerfile
        4  # Free: no
        5  # End SECTION: header
        6  # Clean-machine proof: project bootstrap + canonical make verbs on Alpine
        7  # (musl, POSIX /bin/sh at runtime; bash installed for the project scripts).
>>>     8  FROM alpine:3.21
        9  
       10  # === SECTION: base packages (managed) ===
       11  # Source: template (distro-specific package list)
       12  RUN apk add --no-cache \
```

**Decisão**:

### 386 · ⚪ MINOR · CODE_SMELL · `docker:S7031`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:12` · **Effort**: 5min

> Merge this RUN instruction with the consecutive ones.

```Dockerfile
        8  FROM alpine:3.21
        9  
       10  # === SECTION: base packages (managed) ===
       11  # Source: template (distro-specific package list)
>>>    12  RUN apk add --no-cache \
       13        bash ca-certificates curl git make build-base icu-dev icu-libs
       14  # End SECTION: base packages
       15  
       16  # === SECTION: managed tool bootstrap (managed) ===
```

**Decisão**:

### 387 · ⚪ MINOR · CODE_SMELL · `docker:S7018`
**Local**: `tests/fixtures/ci/docker/alpine.Dockerfile:12` · **Effort**: 5min

> Sort these package names alphanumerically.

```Dockerfile
        8  FROM alpine:3.21
        9  
       10  # === SECTION: base packages (managed) ===
       11  # Source: template (distro-specific package list)
>>>    12  RUN apk add --no-cache \
       13        bash ca-certificates curl git make build-base icu-dev icu-libs
       14  # End SECTION: base packages
       15  
       16  # === SECTION: managed tool bootstrap (managed) ===
```

**Decisão**:

### 388 · ⚪ MINOR · VULNERABILITY · `docker:S6471`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:7` · **Effort**: 15min

> The "archlinux" image runs with "root" as the default user. Make sure it is safe here.

```Dockerfile
        3  # Source: template (base/tests/fixtures/ci/docker/arch.Dockerfile.j2)
        4  # Free: no
        5  # End SECTION: header
        6  # Clean-machine proof: project bootstrap + canonical make verbs on Arch Linux.
>>>     7  FROM archlinux:base
        8  
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
```

**Decisão**:

### 389 · ⚪ MINOR · CODE_SMELL · `docker:S7031`
**Local**: `tests/fixtures/ci/docker/arch.Dockerfile:13` · **Effort**: 5min

> Merge this RUN instruction with the consecutive ones.

```Dockerfile
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
>>>    13  RUN pacman -Syu --noconfirm --needed \
       14        bash ca-certificates curl git make base-devel icu \
       15      && pacman -Scc --noconfirm
       16  # End SECTION: base packages
       17  
```

**Decisão**:

### 390 · ⚪ MINOR · VULNERABILITY · `docker:S6471`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:7` · **Effort**: 15min

> The "debian" image runs with "root" as the default user. Make sure it is safe here.

```Dockerfile
        3  # Source: template (base/tests/fixtures/ci/docker/debian.Dockerfile.j2)
        4  # Free: no
        5  # End SECTION: header
        6  # Clean-machine proof: project bootstrap + canonical make verbs on Debian.
>>>     7  FROM debian:bookworm-slim
        8  
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
```

**Decisão**:

### 391 · ⚪ MINOR · CODE_SMELL · `docker:S7031`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:13` · **Effort**: 5min

> Merge this RUN instruction with the consecutive ones.

```Dockerfile
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
>>>    13  RUN apt-get update \
       14      && apt-get install -y --no-install-recommends \
       15         bash ca-certificates curl git make build-essential libicu-dev \
       16      && rm -rf /var/lib/apt/lists/*
       17  # End SECTION: base packages
```

**Decisão**:

### 392 · ⚪ MINOR · CODE_SMELL · `docker:S7018`
**Local**: `tests/fixtures/ci/docker/debian.Dockerfile:14` · **Effort**: 5min

> Sort these package names alphanumerically.

```Dockerfile
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
       13  RUN apt-get update \
>>>    14      && apt-get install -y --no-install-recommends \
       15         bash ca-certificates curl git make build-essential libicu-dev \
       16      && rm -rf /var/lib/apt/lists/*
       17  # End SECTION: base packages
       18  
```

**Decisão**:

### 393 · ⚪ MINOR · VULNERABILITY · `docker:S6471`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:7` · **Effort**: 15min

> The "fedora" image runs with "root" as the default user. Make sure it is safe here.

```Dockerfile
        3  # Source: template (base/tests/fixtures/ci/docker/fedora.Dockerfile.j2)
        4  # Free: no
        5  # End SECTION: header
        6  # Clean-machine proof: project bootstrap + canonical make verbs on Fedora.
>>>     7  FROM fedora:41
        8  
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
```

**Decisão**:

### 394 · ⚪ MINOR · CODE_SMELL · `docker:S7031`
**Local**: `tests/fixtures/ci/docker/fedora.Dockerfile:13` · **Effort**: 5min

> Merge this RUN instruction with the consecutive ones.

```Dockerfile
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
>>>    13  RUN dnf install -y \
       14        bash ca-certificates curl git make gcc gcc-c++ libatomic libicu-devel \
       15      && dnf clean all
       16  # End SECTION: base packages
       17  
```

**Decisão**:

### 395 · ⚪ MINOR · VULNERABILITY · `docker:S6471`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:7` · **Effort**: 15min

> The "ubuntu" image runs with "root" as the default user. Make sure it is safe here.

```Dockerfile
        3  # Source: template (base/tests/fixtures/ci/docker/ubuntu.Dockerfile.j2)
        4  # Free: no
        5  # End SECTION: header
        6  # Clean-machine proof: project bootstrap + canonical make verbs on Ubuntu.
>>>     7  FROM ubuntu:24.04
        8  
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
```

**Decisão**:

### 396 · ⚪ MINOR · CODE_SMELL · `docker:S7031`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:13` · **Effort**: 5min

> Merge this RUN instruction with the consecutive ones.

```Dockerfile
        9  SHELL ["/bin/bash", "-o", "pipefail", "-c"]
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
>>>    13  RUN apt-get update \
       14      && apt-get install -y --no-install-recommends \
       15         bash ca-certificates curl git make build-essential libicu-dev \
       16      && rm -rf /var/lib/apt/lists/*
       17  # End SECTION: base packages
```

**Decisão**:

### 397 · ⚪ MINOR · CODE_SMELL · `docker:S7018`
**Local**: `tests/fixtures/ci/docker/ubuntu.Dockerfile:14` · **Effort**: 5min

> Sort these package names alphanumerically.

```Dockerfile
       10  
       11  # === SECTION: base packages (managed) ===
       12  # Source: template (distro-specific package list)
       13  RUN apt-get update \
>>>    14      && apt-get install -y --no-install-recommends \
       15         bash ca-certificates curl git make build-essential libicu-dev \
       16      && rm -rf /var/lib/apt/lists/*
       17  # End SECTION: base packages
       18  
```

**Decisão**:
