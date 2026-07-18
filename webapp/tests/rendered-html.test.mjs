import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the HyperMix Observatory", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>HyperMix Observatory<\/title>/i);
  assert.match(html, /Detection without/);
  assert.match(html, /AUDITED LEADERBOARD/);
  assert.match(html, /READ BEFORE CLAIMING/);
  assert.match(html, /The original gain mixed spectral information/);
  assert.match(html, /aria-label="English"/);
  assert.match(html, /aria-label="Português"/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|Codex is working/i);
});

test("keeps the dashboard interactive and free of starter assets", async () => {
  const [page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /useState/);
  assert.match(page, /useState<Language>\("en"\)/);
  assert.match(page, /setLanguage\("pt"\)/);
  assert.match(page, /🇺🇸/);
  assert.match(page, /🇧🇷/);
  assert.match(page, /aria-label="Target SNR"/);
  assert.match(page, /role="tablist"/);
  assert.match(page, /TARGET VARIABILITY/);
  assert.match(layout, /lang="en"/);
  assert.match(layout, /title: "HyperMix Observatory"/);
  assert.doesNotMatch(page, /_sites-preview|SkeletonPreview/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});
