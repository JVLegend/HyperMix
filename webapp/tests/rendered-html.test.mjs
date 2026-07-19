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
  assert.match(html, /THE CASE FILE/);
  assert.match(html, /Seven ways to test it/);
  assert.match(html, /LATEST AUDIT/);
  assert.match(html, /Classical wins/);
  assert.match(html, /BAND ELBOW/);
  assert.match(html, /class="scroll-progress"/);
  assert.match(html, /aria-label="Story progress"/);
  assert.match(html, /data-reveal="scale"/);
  assert.match(html, /AUDITED LEADERBOARD/);
  assert.match(html, /No causal advantage/);
  assert.match(html, /Both 95% confidence intervals are below zero/);
  assert.match(html, /No uncertainty advantage/);
  assert.match(html, /Both 95% intervals are above zero/);
  assert.match(html, /How sparse is/);
  assert.match(html, /Three bands are not enough/);
  assert.match(html, /READ BEFORE CLAIMING/);
  assert.match(html, /The original gain mixed spectral information/);
  assert.match(html, /aria-label="English"/);
  assert.match(html, /aria-label="Português"/);
  assert.match(html, /Bring your own/);
  assert.match(html, /Visualization only/);
  assert.match(html, /type="file"/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|Codex is working/i);
});

test("keeps the dashboard interactive and free of starter assets", async () => {
  const [page, styles, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
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
  assert.match(page, /CHAPTER 03 · VARIATION/);
  assert.match(page, /BACKGROUND =/);
  assert.match(page, /auc: 0\.987, pd: 0\.650/);
  assert.match(page, /CHAPTER 04 · BACKGROUND/);
  assert.match(page, /function StoryBridge/);
  assert.match(page, />33</);
  assert.match(page, /UNCERTAINTY =/);
  assert.match(page, /nll: 0\.05766, brier: 0\.01540, ece: 0\.00896/);
  assert.match(page, /BAND_SPARSITY =/);
  assert.match(page, /className="latest-audit"/);
  assert.match(page, /item\.k === "20" \? "elbow"/);
  assert.match(page, /differenceValue: "−0\.036 AUC \[−0\.092, −0\.000\]"/);
  assert.match(page, /IntersectionObserver/);
  assert.match(page, /requestAnimationFrame/);
  assert.match(page, /prefers-reduced-motion: reduce/);
  assert.match(styles, /\.chapter-rail/);
  assert.match(styles, /Editorial dossier refresh/);
  assert.match(styles, /\.latest-audit/);
  assert.match(styles, /\.band-column\.elbow/);
  assert.match(styles, /\.story-chapter\.latest:hover,[\s\S]*background: var\(--lime\); color: var\(--ink\)/);
  assert.match(styles, /safe-area-inset-bottom/);
  assert.match(styles, /@media \(max-width: 370px\)/);
  assert.match(styles, /@media \(hover: none\) and \(pointer: coarse\)/);
  assert.match(styles, /\.unmix-table \{ overflow-x: auto/);
  assert.match(styles, /html\.motion-ready \[data-reveal\]/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(page, /function ScoreMapStudio/);
  assert.match(page, /image\/png,image\/jpeg,image\/webp/);
  assert.match(page, /getImageData/);
  assert.match(page, /This does not run HyperMix inference/);
  assert.match(layout, /lang="en"/);
  assert.match(layout, /viewportFit: "cover"/);
  assert.match(layout, /og-v2\.png/);
  assert.match(layout, /title: "HyperMix Observatory"/);
  assert.doesNotMatch(page, /_sites-preview|SkeletonPreview/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});
