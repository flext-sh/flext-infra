# Triagem Snyk Code (SAST) — flext-sh/flext-infra

Gerado do scan Snyk (dump 2026-08-06). Bead: `mro-32k4`

## Resumo

**2 achados** — critical 0, high 0, medium 1, low 1

| categoria | achados |
|---|---|
| Arbitrary File Write via Archive Extraction (Tar Slip) | 1 |
| Jinja auto-escape is set to false. | 1 |

## Como usar este documento

Cada achado traz o **código real** extraído da worktree (linha `>>>` = sink reportado), a regra completa e o CWE.
Preencha **Decisão**: `corrigir` / `falso-positivo` (registrar em `.snyk`) / `risco-aceito` (com prazo).

## Achados

### 1 · 🟡 MEDIUM · Arbitrary File Write via Archive Extraction (Tar Slip)
**Local**: `src/flext_infra/release/_release_artifact_source.py:212` · **CWE**: -

```python
      208              )
      209          try:
      210              stage_path.mkdir(parents=True, exist_ok=False)
      211              with tarfile.open(archive_path, "r") as archive:
>>>   212                  archive.extractall(stage_path, filter="data")
      213          except (OSError, tarfile.TarError) as exc:
      214              return r[m.Infra.SourceSnapshot].fail_op(
      215                  "extract committed release source", exc
      216              )
```

**Decisão**: 

### 2 · ⚪ LOW · Jinja auto-escape is set to false.
**Local**: `tests/unit/codegen/test_codegen_catalog_extensions.py:209` · **CWE**: -

```python
      205              / "gitmodules.j2"
      206          )
      207          import jinja2
      208  
>>>   209          rendered = jinja2.Template(template.read_text(encoding="utf-8")).render(
      210              workspace_gitlinks=[
      211                  {
      212                      "repository": {
      213                          "name": "demo-member",
```

**Decisão**: 

