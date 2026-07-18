"use client";

import { useMemo, useState } from "react";

const SNR_LEVELS = [20, 10, 5, 0] as const;
const DETECTION = {
  20: [["MF espacial", 0.995, "teal"], ["Detector aprendido", 0.995, "ice"], ["MF por pixel", 0.968, "amber"], ["ACE", 0.896, "muted"]],
  10: [["MF espacial", 0.993, "teal"], ["Detector aprendido", 0.993, "ice"], ["MF por pixel", 0.957, "amber"], ["ACE", 0.879, "muted"]],
  5: [["MF espacial", 0.990, "teal"], ["Detector aprendido", 0.987, "ice"], ["MF por pixel", 0.940, "amber"], ["ACE", 0.855, "muted"]],
  0: [["MF espacial", 0.982, "teal"], ["Detector aprendido", 0.972, "ice"], ["MF por pixel", 0.908, "amber"], ["ACE", 0.811, "muted"]],
} as const;

const MISMATCH = [
  { shift: "0%", mf: 0.940, spatial: 0.990, learned: 0.987 },
  { shift: "1%", mf: 0.899, spatial: 0.983, learned: 0.973 },
  { shift: "2,5%", mf: 0.781, spatial: 0.920, learned: 0.907 },
  { shift: "5%", mf: 0.647, spatial: 0.730, learned: 0.710 },
];

const REALISM = [
  { name: "Controle estilizado", oracle: 0.983, lab: 0.983, note: "Mistura linear" },
  { name: "Espectros medidos", oracle: 0.995, lab: 0.995, note: "USGS + bioHSI" },
  { name: "SRF 10 nm", oracle: 0.994, lab: 0.995, note: "Resposta gaussiana" },
  { name: "SRF + atmosfera", oracle: 0.994, lab: 0.913, note: "Mismatch aparece" },
  { name: "Cenário bilinear", oracle: 0.983, lab: 0.906, note: "Forward model completo" },
];

const TRACKS = [
  { id: "host", name: "Hospedeiro", detail: "SmURFP/biliverdina em E. coli e P. putida", values: [["MF espacial nominal", 0.996], ["Subespaço espacial", 0.967], ["Aprendido", 0.997], ["Oráculo", 0.997]], verdict: "Empate prático" },
  { id: "sensor", name: "Hospedeiro + sensor", detail: "FWHM 6-14 nm e atmosfera 0,7-1,3", values: [["MF espacial nominal", 0.993], ["Subespaço espacial", 0.910], ["Aprendido", 0.996], ["Oráculo", 0.995]], verdict: "Empate prático" },
  { id: "family", name: "Qualquer repórter", detail: "Bacterioclorofila a ou SmURFP/biliverdina", values: [["MF espacial nominal", 0.907], ["Subespaço espacial", 0.948], ["Aprendido", 0.928], ["Oráculo", 0.996]], verdict: "Subespaço clássico vence" },
] as const;

const UNMIXING = [
  { scene: "Indian Pines", mf: 0.0142, model: 0.0081, winner: "HyperMix" },
  { scene: "Salinas", mf: 0.0073, model: 0.0237, winner: "MF" },
  { scene: "Pavia University", mf: 0.0177, model: 0.0093, winner: "HyperMix" },
];

function EvidenceBar({ label, value, tone = "teal" }: { label: string; value: number; tone?: string }) {
  const visualWidth = Math.max(6, (value - 0.5) * 200);
  return <div className="evidence-row"><div className="evidence-label"><span>{label}</span><strong>{value.toFixed(3)}</strong></div><div className="bar-track" aria-label={`${label}: AUC ${value.toFixed(3)}`}><div className={`bar-fill ${tone}`} style={{ width: `${visualWidth}%` }} /></div></div>;
}

export default function Home() {
  const [snrIndex, setSnrIndex] = useState(3);
  const [mismatchIndex, setMismatchIndex] = useState(0);
  const [trackId, setTrackId] = useState("family");
  const snr = SNR_LEVELS[snrIndex];
  const mismatch = MISMATCH[mismatchIndex];
  const track = useMemo(() => TRACKS.find((item) => item.id === trackId) ?? TRACKS[2], [trackId]);

  return <main>
    <header className="topbar"><a className="brand" href="#top" aria-label="HyperMix, início"><span className="brand-mark">H</span><span><strong>HYPERMIX</strong><small>OBSERVATORY</small></span></a><nav aria-label="Navegação principal"><a href="#benchmark">Benchmark</a><a href="#physics">Física</a><a href="#variability">Variabilidade</a><a href="#limits">Limites</a></nav><a className="github-link" href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">GitHub <span>↗</span></a></header>

    <section className="hero" id="top"><div className="hero-copy"><div className="eyebrow"><span className="pulse" /> OPEN BENCHMARK · AUDITED 18 JUL 2026</div><h1>Detection without<br />the <em>victory lap.</em></h1><p className="hero-lead">Um observatório interativo para testar o que o HyperMix realmente demonstra: neste benchmark, um matched filter espacial bem calibrado lidera ou empata com o detector aprendido.</p><div className="hero-actions"><a className="primary-button" href="#benchmark">Explorar evidência <span>↓</span></a><a className="text-button" href="https://github.com/JVLegend/HyperMix/blob/main/STATUS.md" target="_blank" rel="noreferrer">Ler STATUS científico</a></div><div className="proof-strip"><div><strong>25</strong><span>testes verdes</span></div><div><strong>3</strong><span>fundos reais</span></div><div><strong>6</strong><span>seeds em T1</span></div><div><strong>MIT</strong><span>código aberto</span></div></div></div>
      <aside className="leader-card" aria-label="Leaderboard auditado"><div className="card-kicker"><span>01</span> LEADERBOARD AUDITADO</div><div className="leader-title"><span>AUC média</span><strong>3 cenas · 4 SNRs</strong></div><EvidenceBar label="Matched filter espacial" value={0.990} tone="teal" /><EvidenceBar label="Detector aprendido" value={0.987} tone="ice" /><EvidenceBar label="Matched filter" value={0.943} tone="amber" /><EvidenceBar label="ACE" value={0.860} tone="muted" /><EvidenceBar label="SAM" value={0.656} tone="muted" /><div className="verdict"><span>CONCLUSÃO</span><p>O ganho original confundia informação espectral com o prior espacial dos blobs.</p></div></aside></section>

    <section className="section" id="benchmark"><div className="section-heading"><div><span className="section-number">01</span><p className="overline">DETECTION LAB</p><h2>Baixe o sinal.<br />Veja quem resiste.</h2></div><p>Target SNR mede a contribuição do alvo contra o ruído, não a energia da cena inteira. Arraste o controle para observar o regime de baixo sinal.</p></div>
      <div className="lab-grid"><div className="control-panel"><div className="control-head"><span>TARGET SNR</span><strong>{snr} dB</strong></div><input aria-label="Target SNR" type="range" min="0" max="3" step="1" value={snrIndex} onChange={(event) => setSnrIndex(Number(event.target.value))} /><div className="range-labels">{SNR_LEVELS.map((level) => <button key={level} onClick={() => setSnrIndex(SNR_LEVELS.indexOf(level))}>{level}</button>)}</div><div className="definition"><span>DEFINIÇÃO</span><code>20 log₁₀(RMS alvo / RMS ruído)</code></div></div><div className="results-panel"><div className="panel-meta"><span>AUC AGREGADA</span><span>INDIAN PINES · SALINAS · PAVIA U.</span></div>{DETECTION[snr].map(([label, value, tone]) => <EvidenceBar key={label} label={label} value={value} tone={tone} />)}<div className="axis"><span>0.50 chance</span><span>1.00 perfeito</span></div></div></div>
      <div className="mismatch-card"><div className="mismatch-copy"><p className="overline">SPECTRAL MISMATCH</p><h3>Quando a assinatura está errada</h3><p>O alvo implantado não muda. Apenas a assinatura entregue ao detector é deslocada no índice espectral.</p><div className="chip-group" role="group" aria-label="Deslocamento espectral">{MISMATCH.map((item, index) => <button className={index === mismatchIndex ? "active" : ""} key={item.shift} onClick={() => setMismatchIndex(index)}>{item.shift}</button>)}</div></div><div className="mismatch-values"><div><span>MF</span><strong>{mismatch.mf.toFixed(3)}</strong><small>AUC</small></div><div className="highlight"><span>MF ESPACIAL</span><strong>{mismatch.spatial.toFixed(3)}</strong><small>AUC</small></div><div><span>APRENDIDO</span><strong>{mismatch.learned.toFixed(3)}</strong><small>AUC</small></div></div></div></section>

    <section className="section physics-section" id="physics"><div className="section-heading compact"><div><span className="section-number">02</span><p className="overline">PHYSICAL REALISM</p><h2>Do laboratório<br />ao sensor.</h2></div><p>Espectros medidos, resposta espectral, atmosfera e mistura bilinear entram como controles opt-in. O alvo oráculo já conhece a transformação; o alvo lab não.</p></div><div className="realism-grid">{REALISM.map((item, index) => <article className={`realism-card ${index >= 3 ? "risk" : ""}`} key={item.name}><div className="step-index">0{index + 1}</div><p>{item.note}</p><h3>{item.name}</h3><div className="dual-metric"><div><span>ORÁCULO</span><strong>{item.oracle.toFixed(3)}</strong></div><div><span>ALVO LAB</span><strong>{item.lab.toFixed(3)}</strong></div></div><div className="delta">Δ {(item.lab - item.oracle).toFixed(3)}</div></article>)}</div><div className="insight-banner"><span className="signal-dot" /><strong>Principal evidência da Fase B</strong><p>Com SRF + atmosfera, conhecer o alvo no sensor vale <b>0,081 AUC</b>. O mismatch físico pesa mais que trocar o detector.</p></div></section>

    <section className="section" id="variability"><div className="section-heading"><div><span className="section-number">03</span><p className="overline">TARGET VARIABILITY · T1</p><h2>O último teste<br />favorável ao MLP.</h2></div><p>O detector é treinado sobre variação medida, mas suas features continuam derivadas do alvo nominal. O subespaço clássico recebe a biblioteca de assinaturas plausíveis.</p></div><div className="track-tabs" role="tablist" aria-label="Tracks de variabilidade">{TRACKS.map((item) => <button role="tab" aria-selected={item.id === trackId} className={item.id === trackId ? "active" : ""} key={item.id} onClick={() => setTrackId(item.id)}><span>{item.name}</span><small>{item.verdict}</small></button>)}</div><div className="track-display"><div className="track-context"><p className="overline">TRACK SELECIONADO</p><h3>{track.name}</h3><p>{track.detail}</p><div className="track-verdict">{track.verdict}</div></div><div className="track-bars">{track.values.map(([label, value], index) => <EvidenceBar key={label} label={label} value={value} tone={index === 1 ? "amber" : index === 2 ? "ice" : "teal"} />)}</div></div><p className="honesty-note"><strong>Leitura correta:</strong> o track “qualquer repórter” combina classes químicas. Não é variabilidade intra-molécula. Nele, o subespaço espacial supera o MLP por 0,020 AUC.</p></section>

    <section className="section unmix-section"><div className="section-heading compact"><div><span className="section-number">04</span><p className="overline">ABUNDANCE UNMIXING</p><h2>Detectar é pouco.<br />Quanto existe?</h2></div><p>Target MAE usa apenas pixels com abundância maior que 0,02. Em Salinas, a correlação escondia um viés de escala relevante.</p></div><div className="unmix-table"><div className="unmix-row head"><span>CENA</span><span>MF MAE</span><span>UNMIXER MAE</span><span>MENOR ERRO</span></div>{UNMIXING.map((item) => <div className="unmix-row" key={item.scene}><strong>{item.scene}</strong><span>{item.mf.toFixed(4)}</span><span>{item.model.toFixed(4)}</span><b>{item.winner}</b></div>)}</div></section>

    <section className="limits" id="limits"><div><p className="overline">READ BEFORE CLAIMING</p><h2>O que este projeto<br /><em>não</em> demonstra.</h2></div><ol><li><span>01</span><p><strong>Não há alvo biológico remoto natural.</strong> Os fundos podem ser reais ou medidos, mas os alvos são implantados.</p></li><li><span>02</span><p><strong>Pellet não é superfície remota.</strong> Beer-Lambert converte absorbância em um alvo semelhante a reflectância.</p></li><li><span>03</span><p><strong>O MLP não vê o cubo bruto.</strong> Ele recombina MF, ACE e versões suavizadas com alvo nominal.</p></li><li><span>04</span><p><strong>AUC não basta.</strong> Intervalos de confiança, Pd@FAR e calibração de incerteza ainda estão no roadmap.</p></li></ol></section>
    <footer><div className="footer-brand"><span className="brand-mark">H</span><div><strong>HyperMix Observatory</strong><p>Open detection of engineered biosignatures.</p></div></div><div className="footer-links"><a href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">Source</a><a href="https://github.com/JVLegend/HyperMix/blob/main/results/leaderboard.md" target="_blank" rel="noreferrer">Results</a><a href="https://github.com/JVLegend/HyperMix/blob/main/dataset/DATA_CARD.md" target="_blank" rel="noreferrer">Data card</a></div><p className="footer-note">MIT · Desenvolvido por João Victor, estatístico · Financiado pela Experiment Foundation</p></footer>
  </main>;
}
