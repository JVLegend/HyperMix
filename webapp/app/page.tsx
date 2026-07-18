"use client";

/* User-selected blob URLs cannot be optimized by next/image. */
/* eslint-disable @next/next/no-img-element */

import { useEffect, useMemo, useRef, useState } from "react";

type Language = "en" | "pt";

const SNR_LEVELS = [20, 10, 5, 0] as const;
const DETECTION = {
  20: [0.995, 0.995, 0.968, 0.896],
  10: [0.993, 0.993, 0.957, 0.879],
  5: [0.990, 0.987, 0.940, 0.855],
  0: [0.982, 0.972, 0.908, 0.811],
} as const;

const METHOD_TONES = ["teal", "ice", "amber", "muted"];
const MISMATCH = [
  { mf: 0.940, spatial: 0.990, learned: 0.987 },
  { mf: 0.899, spatial: 0.983, learned: 0.973 },
  { mf: 0.781, spatial: 0.920, learned: 0.907 },
  { mf: 0.647, spatial: 0.730, learned: 0.710 },
];

const REALISM_VALUES = [
  { oracle: 0.983, lab: 0.983 },
  { oracle: 0.995, lab: 0.995 },
  { oracle: 0.994, lab: 0.995 },
  { oracle: 0.994, lab: 0.913 },
  { oracle: 0.983, lab: 0.906 },
];

const TRACK_VALUES = {
  host: [0.996, 0.967, 0.997, 0.997],
  sensor: [0.993, 0.910, 0.996, 0.995],
  family: [0.907, 0.948, 0.928, 0.996],
} as const;

const UNMIXING = [
  { scene: "Indian Pines", mf: 0.0142, model: 0.0081, winner: "HyperMix" },
  { scene: "Salinas", mf: 0.0073, model: 0.0237, winner: "MF" },
  { scene: "Pavia University", mf: 0.0177, model: 0.0093, winner: "HyperMix" },
];

const COPY = {
  en: {
    documentLanguage: "en",
    languageLabel: "Switch language",
    navLabel: "Primary navigation",
    nav: ["Map Studio", "Benchmark", "Physics", "Variability", "Limits"],
    brandLabel: "HyperMix, home",
    hero: {
      eyebrow: "OPEN BENCHMARK · AUDITED 18 JUL 2026",
      lead: "An interactive observatory for testing what HyperMix actually demonstrates: in this benchmark, a well-calibrated spatial matched filter leads or ties the learned detector.",
      explore: "Open Map Studio",
      status: "Explore the benchmark",
      proof: ["passing tests", "real backgrounds", "seeds in T1", "open source"],
    },
    studio: {
      overline: "LOCAL RESULT VIEWER",
      title: <>Bring your own<br /><em>score map.</em></>,
      intro: "Drop a detector score map and inspect candidate pixels at different thresholds. Processing stays entirely in your browser.",
      uploadTitle: "Drop an image here",
      uploadText: "PNG, JPEG, or WebP · up to 12 MB",
      choose: "Choose image",
      source: "SOURCE MAP",
      result: "THRESHOLDED VIEW",
      empty: "Awaiting a score map",
      threshold: "DISPLAY THRESHOLD",
      local: "Local only",
      localText: "Your image never leaves this device.",
      disclaimer: "Visualization only. Pixel brightness is treated as detector score. This does not run HyperMix inference on an RGB image.",
      invalid: "Choose a PNG, JPEG, or WebP image up to 12 MB.",
    },
    leaderboard: {
      aria: "Audited leaderboard",
      kicker: "AUDITED LEADERBOARD",
      mean: "Mean AUC",
      scope: "3 scenes · 4 SNRs",
      methods: ["Spatial matched filter", "Learned detector", "Matched filter", "ACE", "SAM"],
      conclusion: "CONCLUSION",
      verdict: "The original gain mixed spectral information with the spatial prior of the target blobs.",
    },
    benchmark: {
      title: <>Turn down the signal.<br />See what holds.</>,
      intro: "Target SNR measures the target contribution against noise, not the energy of the entire scene. Move the control to inspect the low-signal regime.",
      definition: "DEFINITION",
      formula: "20 log₁₀(target RMS / noise RMS)",
      aggregate: "AGGREGATED AUC",
      axis: ["0.50 chance", "1.00 perfect"],
      methods: ["Spatial MF", "Learned detector", "Pixel MF", "ACE"],
      mismatchTitle: "When the signature is wrong",
      mismatchText: "The implanted target does not change. Only the signature supplied to the detector is shifted along the spectral index.",
      mismatchLabel: "Spectral shift",
      mismatchShifts: ["0%", "1%", "2.5%", "5%"],
      spatial: "SPATIAL MF",
      learned: "LEARNED",
    },
    physics: {
      title: <>From the lab<br />to the sensor.</>,
      intro: "Measured spectra, spectral response, atmosphere, and bilinear mixing are opt-in controls. The oracle target already knows the transformation; the lab target does not.",
      cards: [
        ["Stylized control", "Linear mixing"],
        ["Measured spectra", "USGS + bioHSI"],
        ["10 nm SRF", "Gaussian response"],
        ["SRF + atmosphere", "Mismatch appears"],
        ["Bilinear scenario", "Full forward model"],
      ],
      oracle: "ORACLE",
      lab: "LAB TARGET",
      evidence: "Key Phase B evidence",
      insight: <>With SRF + atmosphere, knowing the target at the sensor is worth <b>0.081 AUC</b>. Physical mismatch matters more than swapping the detector.</>,
    },
    variability: {
      title: <>The final<br />MLP-friendly test.</>,
      intro: "The detector is trained over measured variation, but its features still come from the nominal target. The classical subspace receives the library of plausible signatures.",
      tabLabel: "Variability tracks",
      selected: "SELECTED TRACK",
      methods: ["Nominal spatial MF", "Spatial subspace", "Learned", "Oracle"],
      tracks: {
        host: { name: "Host", detail: "SmURFP/biliverdin in E. coli and P. putida", verdict: "Practical tie" },
        sensor: { name: "Host + sensor", detail: "FWHM 6-14 nm and atmosphere 0.7-1.3", verdict: "Practical tie" },
        family: { name: "Any reporter", detail: "Bacteriochlorophyll a or SmURFP/biliverdin", verdict: "Classical subspace wins" },
      },
      honesty: <><strong>Correct reading:</strong> the “any reporter” track combines chemical classes. It is not intra-molecule variability. Spatial subspace beats the MLP by 0.020 AUC.</>,
    },
    unmixing: {
      title: <>Detection is not enough.<br />How much is there?</>,
      intro: "Target MAE uses only pixels with abundance above 0.02. In Salinas, correlation concealed a relevant scale bias.",
      columns: ["SCENE", "MF MAE", "UNMIXER MAE", "LOWER ERROR"],
    },
    limits: {
      title: <>What this project<br /><em>does not</em> demonstrate.</>,
      items: [
        ["There is no naturally occurring remote biological target.", "Backgrounds can be real or measured, but targets are implanted."],
        ["Pellets are not remote surfaces.", "Beer-Lambert converts absorbance into a reflectance-like target."],
        ["The MLP does not see the raw cube.", "It recombines MF, ACE, and smoothed versions built from the nominal target."],
        ["AUC is not enough.", "Confidence intervals, Pd@FAR, and uncertainty calibration remain on the roadmap."],
      ],
    },
    footer: {
      tagline: "Open detection of engineered biosignatures.",
      links: ["Source", "Results", "Data card"],
      note: "MIT · Developed by João Victor, statistician · Funded by the Experiment Foundation",
    },
  },
  pt: {
    documentLanguage: "pt-BR",
    languageLabel: "Mudar idioma",
    navLabel: "Navegação principal",
    nav: ["Map Studio", "Benchmark", "Física", "Variabilidade", "Limites"],
    brandLabel: "HyperMix, início",
    hero: {
      eyebrow: "BENCHMARK ABERTO · AUDITADO EM 18 JUL 2026",
      lead: "Um observatório interativo para testar o que o HyperMix realmente demonstra: neste benchmark, um matched filter espacial bem calibrado lidera ou empata com o detector aprendido.",
      explore: "Abrir Map Studio",
      status: "Explorar o benchmark",
      proof: ["testes verdes", "fundos reais", "seeds em T1", "código aberto"],
    },
    studio: {
      overline: "VISUALIZADOR LOCAL DE RESULTADOS",
      title: <>Traga seu próprio<br /><em>mapa de scores.</em></>,
      intro: "Envie um mapa de scores do detector e inspecione pixels candidatos em diferentes limiares. O processamento acontece inteiramente no navegador.",
      uploadTitle: "Solte uma imagem aqui",
      uploadText: "PNG, JPEG ou WebP · até 12 MB",
      choose: "Escolher imagem",
      source: "MAPA ORIGINAL",
      result: "VISÃO LIMIARIZADA",
      empty: "Aguardando um mapa de scores",
      threshold: "LIMIAR DE EXIBIÇÃO",
      local: "Somente local",
      localText: "Sua imagem nunca sai deste dispositivo.",
      disclaimer: "Apenas visualização. O brilho do pixel é tratado como score do detector. Isto não executa inferência HyperMix em uma imagem RGB.",
      invalid: "Escolha uma imagem PNG, JPEG ou WebP de até 12 MB.",
    },
    leaderboard: {
      aria: "Leaderboard auditado",
      kicker: "LEADERBOARD AUDITADO",
      mean: "AUC média",
      scope: "3 cenas · 4 SNRs",
      methods: ["Matched filter espacial", "Detector aprendido", "Matched filter", "ACE", "SAM"],
      conclusion: "CONCLUSÃO",
      verdict: "O ganho original confundia informação espectral com o prior espacial dos blobs.",
    },
    benchmark: {
      title: <>Baixe o sinal.<br />Veja quem resiste.</>,
      intro: "Target SNR mede a contribuição do alvo contra o ruído, não a energia da cena inteira. Arraste o controle para observar o regime de baixo sinal.",
      definition: "DEFINIÇÃO",
      formula: "20 log₁₀(RMS alvo / RMS ruído)",
      aggregate: "AUC AGREGADA",
      axis: ["0,50 chance", "1,00 perfeito"],
      methods: ["MF espacial", "Detector aprendido", "MF por pixel", "ACE"],
      mismatchTitle: "Quando a assinatura está errada",
      mismatchText: "O alvo implantado não muda. Apenas a assinatura entregue ao detector é deslocada no índice espectral.",
      mismatchLabel: "Deslocamento espectral",
      mismatchShifts: ["0%", "1%", "2,5%", "5%"],
      spatial: "MF ESPACIAL",
      learned: "APRENDIDO",
    },
    physics: {
      title: <>Do laboratório<br />ao sensor.</>,
      intro: "Espectros medidos, resposta espectral, atmosfera e mistura bilinear entram como controles opt-in. O alvo oráculo já conhece a transformação; o alvo lab não.",
      cards: [
        ["Controle estilizado", "Mistura linear"],
        ["Espectros medidos", "USGS + bioHSI"],
        ["SRF 10 nm", "Resposta gaussiana"],
        ["SRF + atmosfera", "Mismatch aparece"],
        ["Cenário bilinear", "Forward model completo"],
      ],
      oracle: "ORÁCULO",
      lab: "ALVO LAB",
      evidence: "Principal evidência da Fase B",
      insight: <>Com SRF + atmosfera, conhecer o alvo no sensor vale <b>0,081 AUC</b>. O mismatch físico pesa mais que trocar o detector.</>,
    },
    variability: {
      title: <>O último teste<br />favorável ao MLP.</>,
      intro: "O detector é treinado sobre variação medida, mas suas features continuam derivadas do alvo nominal. O subespaço clássico recebe a biblioteca de assinaturas plausíveis.",
      tabLabel: "Tracks de variabilidade",
      selected: "TRACK SELECIONADO",
      methods: ["MF espacial nominal", "Subespaço espacial", "Aprendido", "Oráculo"],
      tracks: {
        host: { name: "Hospedeiro", detail: "SmURFP/biliverdina em E. coli e P. putida", verdict: "Empate prático" },
        sensor: { name: "Hospedeiro + sensor", detail: "FWHM 6-14 nm e atmosfera 0,7-1,3", verdict: "Empate prático" },
        family: { name: "Qualquer repórter", detail: "Bacterioclorofila a ou SmURFP/biliverdina", verdict: "Subespaço clássico vence" },
      },
      honesty: <><strong>Leitura correta:</strong> o track “qualquer repórter” combina classes químicas. Não é variabilidade intra-molécula. Nele, o subespaço espacial supera o MLP por 0,020 AUC.</>,
    },
    unmixing: {
      title: <>Detectar é pouco.<br />Quanto existe?</>,
      intro: "Target MAE usa apenas pixels com abundância maior que 0,02. Em Salinas, a correlação escondia um viés de escala relevante.",
      columns: ["CENA", "MF MAE", "UNMIXER MAE", "MENOR ERRO"],
    },
    limits: {
      title: <>O que este projeto<br /><em>não</em> demonstra.</>,
      items: [
        ["Não há alvo biológico remoto natural.", "Os fundos podem ser reais ou medidos, mas os alvos são implantados."],
        ["Pellet não é superfície remota.", "Beer-Lambert converte absorbância em um alvo semelhante a reflectância."],
        ["O MLP não vê o cubo bruto.", "Ele recombina MF, ACE e versões suavizadas com alvo nominal."],
        ["AUC não basta.", "Intervalos de confiança, Pd@FAR e calibração de incerteza ainda estão no roadmap."],
      ],
    },
    footer: {
      tagline: "Detecção aberta de biossinais engenheirados.",
      links: ["Código", "Resultados", "Data card"],
      note: "MIT · Desenvolvido por João Victor, estatístico · Financiado pela Experiment Foundation",
    },
  },
} as const;

function EvidenceBar({ label, value, tone = "teal" }: { label: string; value: number; tone?: string }) {
  const visualWidth = Math.max(6, (value - 0.5) * 200);
  return <div className="evidence-row"><div className="evidence-label"><span>{label}</span><strong>{value.toFixed(3)}</strong></div><div className="bar-track" aria-label={`${label}: AUC ${value.toFixed(3)}`}><div className={`bar-fill ${tone}`} style={{ width: `${visualWidth}%` }} /></div></div>;
}

function ScoreMapStudio({ copy }: { copy: typeof COPY.en.studio | typeof COPY.pt.studio }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(72);
  const [error, setError] = useState<string | null>(null);

  const acceptFile = (file?: File) => {
    if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 12 * 1024 * 1024) {
      setError(copy.invalid);
      return;
    }
    setError(null);
    setFileName(file.name);
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return URL.createObjectURL(file);
    });
  };

  useEffect(() => {
    if (!previewUrl || !canvasRef.current) return;
    const image = new Image();
    image.onload = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const scale = Math.min(1, 1000 / image.naturalWidth);
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
      const cutoff = threshold * 2.55;
      for (let index = 0; index < pixels.data.length; index += 4) {
        const luminance = 0.2126 * pixels.data[index] + 0.7152 * pixels.data[index + 1] + 0.0722 * pixels.data[index + 2];
        if (luminance >= cutoff) {
          const strength = Math.min(1, (luminance - cutoff) / Math.max(1, 255 - cutoff));
          pixels.data[index] = 255;
          pixels.data[index + 1] = Math.round(118 - strength * 62);
          pixels.data[index + 2] = Math.round(42 + strength * 18);
        } else {
          const muted = Math.round(luminance * 0.42);
          pixels.data[index] = muted;
          pixels.data[index + 1] = muted;
          pixels.data[index + 2] = muted;
        }
      }
      context.putImageData(pixels, 0, 0);
    };
    image.src = previewUrl;
  }, [previewUrl, threshold]);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  return <div className="studio-shell">
    <div className="studio-upload" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); acceptFile(event.dataTransfer.files[0]); }}>
      <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => acceptFile(event.target.files?.[0])} />
      <div className="upload-orbit" aria-hidden="true"><span>+</span></div>
      <h3>{copy.uploadTitle}</h3>
      <p>{copy.uploadText}</p>
      <button type="button" onClick={() => inputRef.current?.click()}>{copy.choose} <span>↗</span></button>
      {error && <p className="upload-error" role="alert">{error}</p>}
    </div>
    <div className="studio-viewer">
      <div className="viewer-head"><span>{fileName ?? copy.empty}</span><strong><i /> {copy.local}</strong></div>
      <div className="viewer-grid">
        <figure><figcaption>{copy.source}</figcaption>{previewUrl ? <img src={previewUrl} alt={fileName ?? copy.source} /> : <div className="empty-map"><span>H</span></div>}</figure>
        <figure><figcaption>{copy.result}</figcaption>{previewUrl ? <canvas ref={canvasRef} aria-label={copy.result} /> : <div className="empty-map result"><span>72</span></div>}</figure>
      </div>
      <div className="threshold-control"><div><span>{copy.threshold}</span><strong>{threshold}%</strong></div><input aria-label={copy.threshold} type="range" min="1" max="99" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} /></div>
      <div className="viewer-note"><strong>{copy.localText}</strong><p>{copy.disclaimer}</p></div>
    </div>
  </div>;
}

export default function Home() {
  const [language, setLanguage] = useState<Language>("en");
  const [snrIndex, setSnrIndex] = useState(3);
  const [mismatchIndex, setMismatchIndex] = useState(0);
  const [trackId, setTrackId] = useState<keyof typeof TRACK_VALUES>("family");
  const copy = COPY[language];
  const snr = SNR_LEVELS[snrIndex];
  const mismatch = MISMATCH[mismatchIndex];
  const tracks = copy.variability.tracks;
  const track = useMemo(() => tracks[trackId], [trackId, tracks]);

  useEffect(() => {
    document.documentElement.lang = copy.documentLanguage;
  }, [copy.documentLanguage]);

  return <main>
    <header className="topbar"><a className="brand" href="#top" aria-label={copy.brandLabel}><span className="brand-mark">H</span><span><strong>HYPERMIX</strong><small>OBSERVATORY</small></span></a><nav aria-label={copy.navLabel}><a href="#studio">{copy.nav[0]}</a><a href="#benchmark">{copy.nav[1]}</a><a href="#physics">{copy.nav[2]}</a><a href="#variability">{copy.nav[3]}</a><a href="#limits">{copy.nav[4]}</a></nav><div className="top-actions"><div className="language-switcher" role="group" aria-label={copy.languageLabel}><button type="button" aria-label="English" aria-pressed={language === "en"} className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")}><span aria-hidden="true">🇺🇸</span><small>EN</small></button><button type="button" aria-label="Português" aria-pressed={language === "pt"} className={language === "pt" ? "active" : ""} onClick={() => setLanguage("pt")}><span aria-hidden="true">🇧🇷</span><small>PT</small></button></div><a className="github-link" href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">GitHub <span>↗</span></a></div></header>

    <section className="hero" id="top"><div className="hero-copy"><div className="eyebrow"><span className="pulse" /> {copy.hero.eyebrow}</div><h1>Detection without<br />the <em>victory lap.</em></h1><p className="hero-lead">{copy.hero.lead}</p><div className="hero-actions"><a className="primary-button" href="#studio">{copy.hero.explore} <span>↓</span></a><a className="text-button" href="#benchmark">{copy.hero.status} <span>→</span></a></div><div className="proof-strip"><div><strong>25</strong><span>{copy.hero.proof[0]}</span></div><div><strong>3</strong><span>{copy.hero.proof[1]}</span></div><div><strong>6</strong><span>{copy.hero.proof[2]}</span></div><div><strong>MIT</strong><span>{copy.hero.proof[3]}</span></div></div></div>
      <aside className="leader-card" aria-label={copy.leaderboard.aria}><div className="card-kicker"><span>01</span> {copy.leaderboard.kicker}</div><div className="leader-title"><span>{copy.leaderboard.mean}</span><strong>{copy.leaderboard.scope}</strong></div><EvidenceBar label={copy.leaderboard.methods[0]} value={0.990} tone="teal" /><EvidenceBar label={copy.leaderboard.methods[1]} value={0.987} tone="ice" /><EvidenceBar label={copy.leaderboard.methods[2]} value={0.943} tone="amber" /><EvidenceBar label={copy.leaderboard.methods[3]} value={0.860} tone="muted" /><EvidenceBar label={copy.leaderboard.methods[4]} value={0.656} tone="muted" /><div className="verdict"><span>{copy.leaderboard.conclusion}</span><p>{copy.leaderboard.verdict}</p></div></aside></section>

    <section className="studio-section" id="studio"><div className="studio-heading"><div><p className="overline">{copy.studio.overline}</p><h2>{copy.studio.title}</h2></div><p>{copy.studio.intro}</p></div><ScoreMapStudio copy={copy.studio} /></section>

    <section className="section" id="benchmark"><div className="section-heading"><div><span className="section-number">01</span><p className="overline">DETECTION LAB</p><h2>{copy.benchmark.title}</h2></div><p>{copy.benchmark.intro}</p></div>
      <div className="lab-grid"><div className="control-panel"><div className="control-head"><span>TARGET SNR</span><strong>{snr} dB</strong></div><input aria-label="Target SNR" type="range" min="0" max="3" step="1" value={snrIndex} onChange={(event) => setSnrIndex(Number(event.target.value))} /><div className="range-labels">{SNR_LEVELS.map((level) => <button key={level} onClick={() => setSnrIndex(SNR_LEVELS.indexOf(level))}>{level}</button>)}</div><div className="definition"><span>{copy.benchmark.definition}</span><code>{copy.benchmark.formula}</code></div></div><div className="results-panel"><div className="panel-meta"><span>{copy.benchmark.aggregate}</span><span>INDIAN PINES · SALINAS · PAVIA U.</span></div>{DETECTION[snr].map((value, index) => <EvidenceBar key={copy.benchmark.methods[index]} label={copy.benchmark.methods[index]} value={value} tone={METHOD_TONES[index]} />)}<div className="axis"><span>{copy.benchmark.axis[0]}</span><span>{copy.benchmark.axis[1]}</span></div></div></div>
      <div className="mismatch-card"><div className="mismatch-copy"><p className="overline">SPECTRAL MISMATCH</p><h3>{copy.benchmark.mismatchTitle}</h3><p>{copy.benchmark.mismatchText}</p><div className="chip-group" role="group" aria-label={copy.benchmark.mismatchLabel}>{MISMATCH.map((_, index) => <button className={index === mismatchIndex ? "active" : ""} key={copy.benchmark.mismatchShifts[index]} onClick={() => setMismatchIndex(index)}>{copy.benchmark.mismatchShifts[index]}</button>)}</div></div><div className="mismatch-values"><div><span>MF</span><strong>{mismatch.mf.toFixed(3)}</strong><small>AUC</small></div><div className="highlight"><span>{copy.benchmark.spatial}</span><strong>{mismatch.spatial.toFixed(3)}</strong><small>AUC</small></div><div><span>{copy.benchmark.learned}</span><strong>{mismatch.learned.toFixed(3)}</strong><small>AUC</small></div></div></div></section>

    <section className="section physics-section" id="physics"><div className="section-heading compact"><div><span className="section-number">02</span><p className="overline">PHYSICAL REALISM</p><h2>{copy.physics.title}</h2></div><p>{copy.physics.intro}</p></div><div className="realism-grid">{REALISM_VALUES.map((item, index) => <article className={`realism-card ${index >= 3 ? "risk" : ""}`} key={copy.physics.cards[index][0]}><div className="step-index">0{index + 1}</div><p>{copy.physics.cards[index][1]}</p><h3>{copy.physics.cards[index][0]}</h3><div className="dual-metric"><div><span>{copy.physics.oracle}</span><strong>{item.oracle.toFixed(3)}</strong></div><div><span>{copy.physics.lab}</span><strong>{item.lab.toFixed(3)}</strong></div></div><div className="delta">Δ {(item.lab - item.oracle).toFixed(3)}</div></article>)}</div><div className="insight-banner"><span className="signal-dot" /><strong>{copy.physics.evidence}</strong><p>{copy.physics.insight}</p></div></section>

    <section className="section" id="variability"><div className="section-heading"><div><span className="section-number">03</span><p className="overline">TARGET VARIABILITY · T1</p><h2>{copy.variability.title}</h2></div><p>{copy.variability.intro}</p></div><div className="track-tabs" role="tablist" aria-label={copy.variability.tabLabel}>{(Object.keys(TRACK_VALUES) as Array<keyof typeof TRACK_VALUES>).map((id) => <button role="tab" aria-selected={id === trackId} className={id === trackId ? "active" : ""} key={id} onClick={() => setTrackId(id)}><span>{tracks[id].name}</span><small>{tracks[id].verdict}</small></button>)}</div><div className="track-display"><div className="track-context"><p className="overline">{copy.variability.selected}</p><h3>{track.name}</h3><p>{track.detail}</p><div className="track-verdict">{track.verdict}</div></div><div className="track-bars">{TRACK_VALUES[trackId].map((value, index) => <EvidenceBar key={copy.variability.methods[index]} label={copy.variability.methods[index]} value={value} tone={index === 1 ? "amber" : index === 2 ? "ice" : "teal"} />)}</div></div><p className="honesty-note">{copy.variability.honesty}</p></section>

    <section className="section unmix-section"><div className="section-heading compact"><div><span className="section-number">04</span><p className="overline">ABUNDANCE UNMIXING</p><h2>{copy.unmixing.title}</h2></div><p>{copy.unmixing.intro}</p></div><div className="unmix-table"><div className="unmix-row head"><span>{copy.unmixing.columns[0]}</span><span>{copy.unmixing.columns[1]}</span><span>{copy.unmixing.columns[2]}</span><span>{copy.unmixing.columns[3]}</span></div>{UNMIXING.map((item) => <div className="unmix-row" key={item.scene}><strong>{item.scene}</strong><span>{item.mf.toFixed(4)}</span><span>{item.model.toFixed(4)}</span><b>{item.winner}</b></div>)}</div></section>

    <section className="limits" id="limits"><div><p className="overline">READ BEFORE CLAIMING</p><h2>{copy.limits.title}</h2></div><ol>{copy.limits.items.map((item, index) => <li key={item[0]}><span>0{index + 1}</span><p><strong>{item[0]}</strong> {item[1]}</p></li>)}</ol></section>
    <footer><div className="footer-brand"><span className="brand-mark">H</span><div><strong>HyperMix Observatory</strong><p>{copy.footer.tagline}</p></div></div><div className="footer-links"><a href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">{copy.footer.links[0]}</a><a href="https://github.com/JVLegend/HyperMix/blob/main/results/leaderboard.md" target="_blank" rel="noreferrer">{copy.footer.links[1]}</a><a href="https://github.com/JVLegend/HyperMix/blob/main/dataset/DATA_CARD.md" target="_blank" rel="noreferrer">{copy.footer.links[2]}</a></div><p className="footer-note">{copy.footer.note}</p></footer>
  </main>;
}
