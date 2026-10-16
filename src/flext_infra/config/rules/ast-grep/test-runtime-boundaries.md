# Runtime assertions and source introspection

Tests exercise the real public owner and observe its returned value, failure, or
externally visible effect. Source spelling, private state, fabricated responses,
and cosmetic module structure do not prove that behavior.

`ban-test-source-introspection-assertion` selects calls to `inspect.getsource`
inside assertions, including generator expressions and `tm.that`. The existing
`resolved-symbol` context validates the captured function against the standard
library owner through Rope. Import aliases retain that identity; an unrelated or
shadowed function does not acquire it from its spelling.

The rule deliberately has no fixer. A replacement needs the scenario's public
behavior and preserves its failures. Assertions on generated files remain valid
when those bytes are the product's observable output, rather than the
implementation of the owner being tested.

The ast-grep fixtures prove candidate selection. Semantic integration cases must
also exercise the native codemod context with module and function aliases,
shadowed names, and an unchanged generated-artifact assertion. Source text stored
in an intermediate variable needs binding and dataflow proof before extending
this rule; an arbitrary `read_text` call is not evidence of a violation.
