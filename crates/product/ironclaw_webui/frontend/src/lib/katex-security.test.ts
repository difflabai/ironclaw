import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "vitest";

// Resolve the actual Mermaid dependency used by the streaming renderer.
const fromStreamdown = createRequire(import.meta.resolve("streamdown"));
const fromMermaid = createRequire(fromStreamdown.resolve("mermaid"));
const katex = fromMermaid("katex") as {
  renderToString: (expression: string, options?: Record<string, unknown>) => string;
};

test("Mermaid's KaTeX ignores inherited trust while preserving ordinary math", () => {
  const safe = katex.renderToString("x^2 + y^2 = z^2");
  assert.match(safe, /class="katex"/);

  // GHSA-238p-pmpm-9mq7: a separately polluted options prototype must not
  // turn the renderer's default trust=false into trusted executable links.
  const inheritedTrust = Object.create({ trust: true });
  const html = katex.renderToString("\\href{javascript:alert(1)}{click}", inheritedTrust);
  assert.doesNotMatch(html, /href=["']javascript:/i);
  assert.match(html, /katex/);
});
