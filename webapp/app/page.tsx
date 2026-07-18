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

const BACKGROUND = {
  mf: { auc: 0.987, pd: 0.650, aucCi: "0.968–0.997", pdCi: "0.227–0.872" },
  model: { auc: 0.976, pd: 0.324, aucCi: "0.945–0.994", pdCi: "0.087–0.544" },
  rx: { auc: 0.539, pd: 0.001 },
  rawModel: { auc: 0.869, pd: 0.108 },
} as const;

const CHAPTER_IDS = ["benchmark", "physics", "variability", "background", "unmixing"] as const;

const COPY = {
  en: {
    documentLanguage: "en",
    languageLabel: "Switch language",
    navLabel: "Primary navigation",
    progressLabel: "Story progress",
    nav: ["Story", "Benchmark", "Physics", "Background", "Limits"],
    brandLabel: "HyperMix, home",
    hero: {
      eyebrow: "OPEN BENCHMARK · AUDITED 18 JUL 2026",
      title: <>Detection without<br />the <em>victory lap.</em></>,
      lead: "An interactive observatory for testing what HyperMix actually demonstrates: in this benchmark, a well-calibrated spatial matched filter leads or ties the learned detector.",
      explore: "Follow the evidence",
      status: "Open Map Studio",
      proof: ["passing tests", "real backgrounds", "seeds in T7a", "open source"],
    },
    story: {
      overline: "THE CASE FILE",
      title: <>One claim.<br /><em>Five ways to test it.</em></>,
      intro: "Read the evidence in order. Each chapter removes one convenient assumption and asks whether learning finally earns a robust advantage.",
      chapters: [
        ["01", "Signal", "Does learning hold when the target fades?", "Spatial MF leads"],
        ["02", "Physics", "Does sensor realism reverse the result?", "Mismatch dominates"],
        ["03", "Variation", "Can measured target variation help?", "Mostly ties"],
        ["04", "Background", "Can raw scene statistics rescue learning?", "Not in this test"],
        ["05", "Quantity", "What remains useful beyond ranking?", "Mixed by scene"],
      ],
    },
    bridges: {
      benchmark: ["NEXT QUESTION", "The baseline survives low signal.", "Now remove the convenient assumption that the lab signature reaches the sensor unchanged."],
      physics: ["NEXT QUESTION", "Physical mismatch hurts more than model choice.", "Give learning measured target variation and a classical subspace a fair chance."],
      variability: ["FINAL CAUSAL TEST", "Still no robust learned advantage.", "Let a model consume the raw scene and learn its background statistics without labels."],
      background: ["WHAT REMAINS", "The last simple causal test also fails.", "A detector need not be superior to make the toolkit useful. Move from ranking pixels to estimating abundance."],
      unmixing: ["INSPECT THE ARTIFACT", "Useful does not mean universally better.", "Bring a score map, inspect its threshold, then finish with the boundaries of every claim."],
      studio: ["FINAL READING", "A convincing map is not biological validation.", "The last chapter states exactly what this benchmark can and cannot support."],
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
      overline: "CHAPTER 01 · SIGNAL",
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
      overline: "CHAPTER 02 · PHYSICS",
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
      overline: "CHAPTER 03 · VARIATION",
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
      overline: "CHAPTER 05 · QUANTITY",
      title: <>Detection is not enough.<br />How much is there?</>,
      intro: "Target MAE uses only pixels with abundance above 0.02. In Salinas, correlation concealed a relevant scale bias.",
      columns: ["SCENE", "MF MAE", "UNMIXER MAE", "LOWER ERROR"],
    },
    background: {
      overline: "CHAPTER 04 · BACKGROUND",
      title: <>The last<br /><em>honest test.</em></>,
      intro: "A shallow autoencoder learns only from unlabeled spectra in the test scene. It never receives labels, a target mask, or the target signature during training.",
      questionLabel: "RESEARCH QUESTION / T7A",
      question: "If real clutter is non-Gaussian, can scene-level background learning beat the spatial matched filter?",
      methods: ["Spatial matched filter", "Spatial background autoencoder"],
      auc: "AUC",
      pd: "Pd@FAR 1e-3",
      interval: "95% CI",
      difference: "PAIRED DIFFERENCE · AUTOENCODER MINUS MF",
      differenceValue: "AUC -0.011 · Pd -0.325",
      differenceCi: "Both 95% confidence intervals are below zero.",
      verdict: "No causal advantage",
      verdictText: "This pre-specified shallow autoencoder is significantly worse on both metrics. It closes this simple instantiation, not every possible background-density model.",
      secondary: "Target-agnostic checks",
      rx: "Global RX",
      raw: "Raw background AE",
    },
    limits: {
      overline: "READ BEFORE CLAIMING",
      title: <>What this project<br /><em>does not</em> demonstrate.</>,
      items: [
        ["There is no naturally occurring remote biological target.", "Backgrounds can be real or measured, but targets are implanted."],
        ["Pellets are not remote surfaces.", "Beer-Lambert converts absorbance into a reflectance-like target."],
        ["The MLP does not see the raw cube.", "It recombines MF, ACE, and smoothed versions built from the nominal target."],
        ["Three scenes are not a population.", "The hierarchical intervals describe this benchmark, not every sensor or ecosystem."],
        ["One background model is not the whole model class.", "T7a closes the pre-specified shallow autoencoder, not every density estimator."],
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
    progressLabel: "Progresso da história",
    nav: ["História", "Benchmark", "Física", "Fundo", "Limites"],
    brandLabel: "HyperMix, início",
    hero: {
      eyebrow: "BENCHMARK ABERTO · AUDITADO EM 18 JUL 2026",
      title: <>Detecção sem<br /><em>volta da vitória.</em></>,
      lead: "Um observatório interativo para testar o que o HyperMix realmente demonstra: neste benchmark, um matched filter espacial bem calibrado lidera ou empata com o detector aprendido.",
      explore: "Seguir as evidências",
      status: "Abrir Map Studio",
      proof: ["testes verdes", "fundos reais", "seeds em T7a", "código aberto"],
    },
    story: {
      overline: "O DOSSIÊ",
      title: <>Uma afirmação.<br /><em>Cinco formas de testá-la.</em></>,
      intro: "Leia as evidências em ordem. Cada capítulo remove uma premissa conveniente e pergunta se o aprendizado finalmente conquista uma vantagem robusta.",
      chapters: [
        ["01", "Sinal", "O aprendizado resiste quando o alvo enfraquece?", "MF espacial lidera"],
        ["02", "Física", "O realismo do sensor inverte o resultado?", "Mismatch domina"],
        ["03", "Variação", "Variação medida do alvo ajuda?", "Predominam empates"],
        ["04", "Fundo", "A estatística bruta da cena salva o aprendizado?", "Não neste teste"],
        ["05", "Quantidade", "O que segue útil além do ranking?", "Depende da cena"],
      ],
    },
    bridges: {
      benchmark: ["PRÓXIMA PERGUNTA", "O baseline resiste ao baixo sinal.", "Agora remova a premissa conveniente de que a assinatura do laboratório chega intacta ao sensor."],
      physics: ["PRÓXIMA PERGUNTA", "Mismatch físico pesa mais que escolher outro modelo.", "Dê ao aprendizado variação medida do alvo e compare com um subespaço clássico justo."],
      variability: ["TESTE CAUSAL FINAL", "Ainda não há vantagem robusta do aprendizado.", "Deixe um modelo consumir a cena bruta e aprender a estatística do fundo sem rótulos."],
      background: ["O QUE RESTA", "O último teste causal simples também falha.", "Um detector não precisa ser superior para tornar o toolkit útil. Passe do ranking de pixels à estimativa de abundância."],
      unmixing: ["INSPECIONE O ARTEFATO", "Útil não significa universalmente melhor.", "Traga um mapa de scores, examine seu limiar e termine nas fronteiras de toda afirmação."],
      studio: ["LEITURA FINAL", "Um mapa convincente não é validação biológica.", "O último capítulo declara exatamente o que este benchmark pode e não pode sustentar."],
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
      overline: "CAPÍTULO 01 · SINAL",
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
      overline: "CAPÍTULO 02 · FÍSICA",
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
      overline: "CAPÍTULO 03 · VARIAÇÃO",
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
      overline: "CAPÍTULO 05 · QUANTIDADE",
      title: <>Detectar é pouco.<br />Quanto existe?</>,
      intro: "Target MAE usa apenas pixels com abundância maior que 0,02. Em Salinas, a correlação escondia um viés de escala relevante.",
      columns: ["CENA", "MF MAE", "UNMIXER MAE", "MENOR ERRO"],
    },
    background: {
      overline: "CAPÍTULO 04 · FUNDO",
      title: <>O último teste<br /><em>honesto.</em></>,
      intro: "Um autoencoder raso aprende apenas com espectros não rotulados da cena de teste. O treino nunca recebe rótulos, máscara do alvo ou a assinatura do alvo.",
      questionLabel: "PERGUNTA DE PESQUISA / T7A",
      question: "Se o clutter real é não gaussiano, aprender o fundo da própria cena supera o matched filter espacial?",
      methods: ["Matched filter espacial", "Autoencoder espacial de fundo"],
      auc: "AUC",
      pd: "Pd@FAR 1e-3",
      interval: "IC 95%",
      difference: "DIFERENÇA PAREADA · AUTOENCODER MENOS MF",
      differenceValue: "AUC -0,011 · Pd -0,325",
      differenceCi: "Os dois intervalos de 95% ficaram abaixo de zero.",
      verdict: "Sem vantagem causal",
      verdictText: "Este autoencoder raso pré-especificado é significativamente inferior nas duas métricas. Isso fecha esta instanciação simples, não todo modelo possível de densidade do fundo.",
      secondary: "Controles alvo-agnósticos",
      rx: "RX global",
      raw: "AE de fundo sem blur",
    },
    limits: {
      overline: "LEIA ANTES DE AFIRMAR",
      title: <>O que este projeto<br /><em>não</em> demonstra.</>,
      items: [
        ["Não há alvo biológico remoto natural.", "Os fundos podem ser reais ou medidos, mas os alvos são implantados."],
        ["Pellet não é superfície remota.", "Beer-Lambert converte absorbância em um alvo semelhante a reflectância."],
        ["O MLP não vê o cubo bruto.", "Ele recombina MF, ACE e versões suavizadas com alvo nominal."],
        ["Três cenas não são uma população.", "Os intervalos hierárquicos descrevem este benchmark, não todo sensor ou ecossistema."],
        ["Um modelo de fundo não é toda a classe.", "T7a fecha o autoencoder raso pré-especificado, não todo estimador de densidade."],
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

function StoryBridge({ content, nextId }: { content: readonly [string, string, string]; nextId: string }) {
  return <a className="story-bridge" href={`#${nextId}`} data-reveal="up">
    <span>{content[0]}</span>
    <strong>{content[1]}</strong>
    <p>{content[2]}</p>
    <b aria-hidden="true">↓</b>
  </a>;
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

  return <div className="studio-shell" data-reveal="scale">
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
  const [activeChapter, setActiveChapter] = useState(0);
  const copy = COPY[language];
  const snr = SNR_LEVELS[snrIndex];
  const mismatch = MISMATCH[mismatchIndex];
  const tracks = copy.variability.tracks;
  const track = useMemo(() => tracks[trackId], [trackId, tracks]);

  useEffect(() => {
    document.documentElement.lang = copy.documentLanguage;
  }, [copy.documentLanguage]);

  useEffect(() => {
    const root = document.documentElement;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const compactViewport = window.matchMedia("(max-width: 700px)").matches;
    const supportsObservers = "IntersectionObserver" in window;
    let frame = 0;

    if (!reducedMotion && supportsObservers) root.classList.add("motion-ready");

    const updateScrollEffects = () => {
      frame = 0;
      const scrollable = Math.max(1, root.scrollHeight - window.innerHeight);
      const progress = Math.min(1, Math.max(0, window.scrollY / scrollable));
      root.style.setProperty("--page-progress", progress.toFixed(4));

      if (!reducedMotion && !compactViewport) {
        const heroTravel = Math.min(window.scrollY, window.innerHeight * 1.1);
        root.style.setProperty("--hero-copy-y", `${heroTravel * 0.075}px`);
        root.style.setProperty("--hero-card-y", `${heroTravel * -0.035}px`);
        root.style.setProperty("--hero-orbit-y", `${heroTravel * -0.09}px`);
      }
    };

    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(updateScrollEffects);
    };
    updateScrollEffects();
    window.addEventListener("scroll", onScroll, { passive: true });

    const revealObserver = reducedMotion || !supportsObservers ? null : new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver?.unobserve(entry.target);
        }
      }),
      { threshold: 0.12, rootMargin: "0px 0px -8%" },
    );
    revealObserver?.observe(document.querySelector("#story .story-intro") as Element);
    document.querySelectorAll("[data-reveal]").forEach((element) => revealObserver?.observe(element));

    const chapterObserver = supportsObservers ? new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const chapter = CHAPTER_IDS.indexOf(entry.target.id as typeof CHAPTER_IDS[number]);
          if (chapter >= 0) setActiveChapter(chapter);
        }
      }),
      { threshold: 0, rootMargin: "-28% 0px -58%" },
    ) : null;
    CHAPTER_IDS.forEach((id) => {
      const section = document.getElementById(id);
      if (section) chapterObserver?.observe(section);
    });

    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
      revealObserver?.disconnect();
      chapterObserver?.disconnect();
      root.classList.remove("motion-ready");
      root.style.removeProperty("--page-progress");
      root.style.removeProperty("--hero-copy-y");
      root.style.removeProperty("--hero-card-y");
      root.style.removeProperty("--hero-orbit-y");
    };
  }, []);

  return <main>
    <div className="scroll-progress" aria-hidden="true"><span /></div>
    <nav className="chapter-rail" aria-label={copy.progressLabel}>{copy.story.chapters.map((chapter, index) => <a key={chapter[0]} href={`#${CHAPTER_IDS[index]}`} aria-current={activeChapter === index ? "step" : undefined}><span>{chapter[1]}</span><i /><small>{chapter[0]}</small></a>)}</nav>
    <header className="topbar">
      <a className="brand" href="#top" aria-label={copy.brandLabel}><span className="brand-mark">H</span><span><strong>HYPERMIX</strong><small>OBSERVATORY</small></span></a>
      <nav aria-label={copy.navLabel}><a href="#story">{copy.nav[0]}</a><a href="#benchmark">{copy.nav[1]}</a><a href="#physics">{copy.nav[2]}</a><a href="#background">{copy.nav[3]}</a><a href="#limits">{copy.nav[4]}</a></nav>
      <div className="top-actions"><div className="language-switcher" role="group" aria-label={copy.languageLabel}><button type="button" aria-label="English" aria-pressed={language === "en"} className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")}><span aria-hidden="true">🇺🇸</span><small>EN</small></button><button type="button" aria-label="Português" aria-pressed={language === "pt"} className={language === "pt" ? "active" : ""} onClick={() => setLanguage("pt")}><span aria-hidden="true">🇧🇷</span><small>PT</small></button></div><a className="github-link" href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">GitHub <span>↗</span></a></div>
    </header>

    <section className="hero" id="top">
      <div className="hero-copy"><div className="eyebrow"><span className="pulse" /> {copy.hero.eyebrow}</div><h1>{copy.hero.title}</h1><p className="hero-lead">{copy.hero.lead}</p><div className="hero-actions"><a className="primary-button" href="#story">{copy.hero.explore} <span>↓</span></a><a className="text-button" href="#studio">{copy.hero.status} <span>→</span></a></div><div className="proof-strip"><div><strong>29</strong><span>{copy.hero.proof[0]}</span></div><div><strong>3</strong><span>{copy.hero.proof[1]}</span></div><div><strong>4</strong><span>{copy.hero.proof[2]}</span></div><div><strong>MIT</strong><span>{copy.hero.proof[3]}</span></div></div></div>
      <aside className="leader-card" aria-label={copy.leaderboard.aria}><div className="card-kicker"><span>01</span> {copy.leaderboard.kicker}</div><div className="leader-title"><span>{copy.leaderboard.mean}</span><strong>{copy.leaderboard.scope}</strong></div><EvidenceBar label={copy.leaderboard.methods[0]} value={0.990} tone="teal" /><EvidenceBar label={copy.leaderboard.methods[1]} value={0.987} tone="ice" /><EvidenceBar label={copy.leaderboard.methods[2]} value={0.943} tone="amber" /><EvidenceBar label={copy.leaderboard.methods[3]} value={0.860} tone="muted" /><EvidenceBar label={copy.leaderboard.methods[4]} value={0.656} tone="muted" /><div className="verdict"><span>{copy.leaderboard.conclusion}</span><p>{copy.leaderboard.verdict}</p></div></aside>
    </section>

    <section className="story-section" id="story">
      <div className="story-intro"><p className="overline">{copy.story.overline}</p><h2>{copy.story.title}</h2><p>{copy.story.intro}</p></div>
      <div className="story-chapters">{copy.story.chapters.map((chapter, index) => <a href={`#${CHAPTER_IDS[index]}`} className="story-chapter" data-reveal="left" key={chapter[0]}><span>{chapter[0]}</span><small>{chapter[1]}</small><strong>{chapter[2]}</strong><b>{chapter[3]}</b></a>)}</div>
    </section>

    <section className="section" id="benchmark">
      <div className="section-heading" data-reveal="up"><div><span className="section-number">01</span><p className="overline">{copy.benchmark.overline}</p><h2>{copy.benchmark.title}</h2></div><p>{copy.benchmark.intro}</p></div>
      <div className="lab-grid" data-reveal="scale"><div className="control-panel"><div className="control-head"><span>TARGET SNR</span><strong>{snr} dB</strong></div><input aria-label="Target SNR" type="range" min="0" max="3" step="1" value={snrIndex} onChange={(event) => setSnrIndex(Number(event.target.value))} /><div className="range-labels">{SNR_LEVELS.map((level) => <button key={level} onClick={() => setSnrIndex(SNR_LEVELS.indexOf(level))}>{level}</button>)}</div><div className="definition"><span>{copy.benchmark.definition}</span><code>{copy.benchmark.formula}</code></div></div><div className="results-panel"><div className="panel-meta"><span>{copy.benchmark.aggregate}</span><span>INDIAN PINES · SALINAS · PAVIA U.</span></div>{DETECTION[snr].map((value, index) => <EvidenceBar key={copy.benchmark.methods[index]} label={copy.benchmark.methods[index]} value={value} tone={METHOD_TONES[index]} />)}<div className="axis"><span>{copy.benchmark.axis[0]}</span><span>{copy.benchmark.axis[1]}</span></div></div></div>
      <div className="mismatch-card" data-reveal="up"><div className="mismatch-copy"><p className="overline">SPECTRAL MISMATCH</p><h3>{copy.benchmark.mismatchTitle}</h3><p>{copy.benchmark.mismatchText}</p><div className="chip-group" role="group" aria-label={copy.benchmark.mismatchLabel}>{MISMATCH.map((_, index) => <button className={index === mismatchIndex ? "active" : ""} key={copy.benchmark.mismatchShifts[index]} onClick={() => setMismatchIndex(index)}>{copy.benchmark.mismatchShifts[index]}</button>)}</div></div><div className="mismatch-values"><div><span>MF</span><strong>{mismatch.mf.toFixed(3)}</strong><small>AUC</small></div><div className="highlight"><span>{copy.benchmark.spatial}</span><strong>{mismatch.spatial.toFixed(3)}</strong><small>AUC</small></div><div><span>{copy.benchmark.learned}</span><strong>{mismatch.learned.toFixed(3)}</strong><small>AUC</small></div></div></div>
      <StoryBridge content={copy.bridges.benchmark} nextId="physics" />
    </section>

    <section className="section physics-section" id="physics">
      <div className="section-heading compact" data-reveal="up"><div><span className="section-number">02</span><p className="overline">{copy.physics.overline}</p><h2>{copy.physics.title}</h2></div><p>{copy.physics.intro}</p></div>
      <div className="realism-grid">{REALISM_VALUES.map((item, index) => <article className={`realism-card ${index >= 3 ? "risk" : ""}`} data-reveal="up" key={copy.physics.cards[index][0]}><div className="step-index">0{index + 1}</div><p>{copy.physics.cards[index][1]}</p><h3>{copy.physics.cards[index][0]}</h3><div className="dual-metric"><div><span>{copy.physics.oracle}</span><strong>{item.oracle.toFixed(3)}</strong></div><div><span>{copy.physics.lab}</span><strong>{item.lab.toFixed(3)}</strong></div></div><div className="delta">Δ {(item.lab - item.oracle).toFixed(3)}</div></article>)}</div>
      <div className="insight-banner" data-reveal="scale"><span className="signal-dot" /><strong>{copy.physics.evidence}</strong><p>{copy.physics.insight}</p></div>
      <StoryBridge content={copy.bridges.physics} nextId="variability" />
    </section>

    <section className="section" id="variability">
      <div className="section-heading" data-reveal="up"><div><span className="section-number">03</span><p className="overline">{copy.variability.overline}</p><h2>{copy.variability.title}</h2></div><p>{copy.variability.intro}</p></div>
      <div className="track-tabs" data-reveal="up" role="tablist" aria-label={copy.variability.tabLabel}>{(Object.keys(TRACK_VALUES) as Array<keyof typeof TRACK_VALUES>).map((id) => <button role="tab" aria-selected={id === trackId} className={id === trackId ? "active" : ""} key={id} onClick={() => setTrackId(id)}><span>{tracks[id].name}</span><small>{tracks[id].verdict}</small></button>)}</div><div className="track-display" data-reveal="scale"><div className="track-context"><p className="overline">{copy.variability.selected}</p><h3>{track.name}</h3><p>{track.detail}</p><div className="track-verdict">{track.verdict}</div></div><div className="track-bars">{TRACK_VALUES[trackId].map((value, index) => <EvidenceBar key={copy.variability.methods[index]} label={copy.variability.methods[index]} value={value} tone={index === 1 ? "amber" : index === 2 ? "ice" : "teal"} />)}</div></div><p className="honesty-note" data-reveal="up">{copy.variability.honesty}</p>
      <StoryBridge content={copy.bridges.variability} nextId="background" />
    </section>

    <section className="section background-section" id="background">
      <div className="section-heading" data-reveal="up"><div><span className="section-number">04</span><p className="overline">{copy.background.overline}</p><h2>{copy.background.title}</h2></div><p>{copy.background.intro}</p></div>
      <div className="background-question" data-reveal="scale"><span>{copy.background.questionLabel}</span><p>{copy.background.question}</p></div>
      <div className="background-comparison">{[BACKGROUND.mf, BACKGROUND.model].map((method, index) => <article className={index === 0 ? "method-card winner" : "method-card"} data-reveal={index === 0 ? "left" : "right"} key={copy.background.methods[index]}><div className="method-head"><span>0{index + 1}</span><h3>{copy.background.methods[index]}</h3></div><div className="method-metrics"><div><span>{copy.background.auc}</span><strong>{method.auc.toFixed(3)}</strong><small>{copy.background.interval} {method.aucCi}</small></div><div><span>{copy.background.pd}</span><strong>{method.pd.toFixed(3)}</strong><small>{copy.background.interval} {method.pdCi}</small></div></div></article>)}</div>
      <div className="background-difference" data-reveal="up"><div><span>{copy.background.difference}</span><strong>{copy.background.differenceValue}</strong></div><p>{copy.background.differenceCi}</p></div>
      <div className="background-foot" data-reveal="scale"><div className="background-verdict"><span>{copy.background.verdict}</span><p>{copy.background.verdictText}</p></div><div className="secondary-checks"><span>{copy.background.secondary}</span><div><p>{copy.background.rx}</p><strong>{BACKGROUND.rx.auc.toFixed(3)}</strong><small>AUC · Pd {BACKGROUND.rx.pd.toFixed(3)}</small></div><div><p>{copy.background.raw}</p><strong>{BACKGROUND.rawModel.auc.toFixed(3)}</strong><small>AUC · Pd {BACKGROUND.rawModel.pd.toFixed(3)}</small></div></div></div>
      <StoryBridge content={copy.bridges.background} nextId="unmixing" />
    </section>

    <section className="section unmix-section" id="unmixing">
      <div className="section-heading compact" data-reveal="up"><div><span className="section-number">05</span><p className="overline">{copy.unmixing.overline}</p><h2>{copy.unmixing.title}</h2></div><p>{copy.unmixing.intro}</p></div>
      <div className="unmix-table" data-reveal="scale"><div className="unmix-row head"><span>{copy.unmixing.columns[0]}</span><span>{copy.unmixing.columns[1]}</span><span>{copy.unmixing.columns[2]}</span><span>{copy.unmixing.columns[3]}</span></div>{UNMIXING.map((item) => <div className="unmix-row" key={item.scene}><strong>{item.scene}</strong><span>{item.mf.toFixed(4)}</span><span>{item.model.toFixed(4)}</span><b>{item.winner}</b></div>)}</div>
      <StoryBridge content={copy.bridges.unmixing} nextId="studio" />
    </section>

    <section className="studio-section" id="studio">
      <div className="studio-heading" data-reveal="up"><div><p className="overline">{copy.studio.overline}</p><h2>{copy.studio.title}</h2></div><p>{copy.studio.intro}</p></div><ScoreMapStudio copy={copy.studio} />
      <StoryBridge content={copy.bridges.studio} nextId="limits" />
    </section>

    <section className="limits" id="limits"><div data-reveal="left"><p className="overline">{copy.limits.overline}</p><h2>{copy.limits.title}</h2></div><ol>{copy.limits.items.map((item, index) => <li data-reveal="right" key={item[0]}><span>0{index + 1}</span><p><strong>{item[0]}</strong> {item[1]}</p></li>)}</ol></section>
    <footer><div className="footer-brand"><span className="brand-mark">H</span><div><strong>HyperMix Observatory</strong><p>{copy.footer.tagline}</p></div></div><div className="footer-links"><a href="https://github.com/JVLegend/HyperMix" target="_blank" rel="noreferrer">{copy.footer.links[0]}</a><a href="https://github.com/JVLegend/HyperMix/blob/main/results/leaderboard.md" target="_blank" rel="noreferrer">{copy.footer.links[1]}</a><a href="https://github.com/JVLegend/HyperMix/blob/main/dataset/DATA_CARD.md" target="_blank" rel="noreferrer">{copy.footer.links[2]}</a></div><p className="footer-note">{copy.footer.note}</p></footer>
  </main>;
}
