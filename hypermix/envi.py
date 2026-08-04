"""Leitura de cubos ENVI preservando metadados, unidades e escala radiométrica.

Este módulo existe porque ``datasets.load_envi_cube`` não serve à Fase C. Aquele
loader aplica min-max global sobre o cubo inteiro, descarta o cabeçalho e depende
do pacote opcional ``spectral``. Para dados medidos, a escala e os comprimentos de
onda são o objeto de estudo, não um detalhe de apresentação.

As decisões aqui são deliberadamente conservadoras:

- nenhum reescalonamento, deslocamento ou normalização é aplicado;
- o cabeçalho é preservado, inclusive as linhas de comentário iniciadas por ``;``,
  porque nelas os arquivos Headwall registram unidade, exposição e ortorretificação;
- o binário é mapeado em memória, então abrir um cubo de centenas de megabytes não
  o carrega inteiro;
- nada é inferido sobre unidade física. O cabeçalho pode declarar radiância num
  comentário e refletância na descrição. Cabe a quem analisa decidir, com o registro
  à vista.

Somente NumPy, sem dependência nova.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Mapping

import numpy as np

__all__ = [
    "EnviHeader",
    "ENVI_DTYPES",
    "parse_envi_header",
    "open_envi_cube",
    "envi_nodata_mask",
]

# Códigos de tipo do padrão ENVI que aparecem em cubos hiperespectrais.
ENVI_DTYPES: Mapping[int, str] = {
    1: "u1",
    2: "i2",
    3: "i4",
    4: "f4",
    5: "f8",
    12: "u2",
    13: "u4",
    14: "i8",
    15: "u8",
}

_INTERLEAVES = ("bsq", "bil", "bip")


@dataclass(frozen=True)
class EnviHeader:
    """Cabeçalho ENVI já validado, com os campos que a leitura exige."""

    samples: int
    lines: int
    bands: int
    data_type: int
    interleave: str
    byte_order: int
    header_offset: int = 0
    description: str | None = None
    wavelengths: np.ndarray | None = None
    wavelength_units: str | None = None
    fields: Mapping[str, str] = field(default_factory=dict)
    comments: Mapping[str, str] = field(default_factory=dict)

    @property
    def dtype(self) -> np.dtype:
        """Tipo NumPy com a ordem de bytes declarada no cabeçalho."""
        try:
            base = ENVI_DTYPES[self.data_type]
        except KeyError as exc:
            raise ValueError(f"unsupported ENVI data type: {self.data_type}") from exc
        prefix = ">" if self.byte_order else "<"
        return np.dtype(prefix + base)

    @property
    def shape(self) -> tuple[int, int, int]:
        """Forma lógica ``(lines, samples, bands)``, a convenção do HyperMix."""
        return (self.lines, self.samples, self.bands)

    @property
    def expected_size(self) -> int:
        """Bytes esperados no binário pareado, sem contar o deslocamento."""
        return self.lines * self.samples * self.bands * self.dtype.itemsize


def _split_entries(text: str) -> list[tuple[str, str]]:
    """Separa ``chave = valor``, respeitando blocos ``{...}`` de várias linhas."""
    entries: list[tuple[str, str]] = []
    index = 0
    length = len(text)
    while index < length:
        match = re.compile(r"^[ \t]*([^=\n;][^=\n]*?)[ \t]*=[ \t]*", re.M).search(
            text, index
        )
        if match is None:
            break
        key = match.group(1).strip().lower()
        start = match.end()
        if start < length and text[start] == "{":
            close = text.find("}", start)
            if close == -1:
                raise ValueError(f"unterminated ENVI block for key {key!r}")
            value = text[start + 1 : close]
            index = close + 1
        else:
            stop = text.find("\n", start)
            stop = length if stop == -1 else stop
            value = text[start:stop]
            index = stop + 1
        entries.append((key, value.strip()))
    return entries


def _parse_comments(text: str) -> dict[str, str]:
    """Coleta ``;chave = valor``, onde a Headwall guarda unidade e ortorretificação."""
    comments: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith(";") or "=" not in stripped:
            continue
        key, _, value = stripped[1:].partition("=")
        comments[key.strip().lower()] = value.strip()
    return comments


def _floats(block: str) -> np.ndarray:
    found = re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", block)
    return np.asarray([float(value) for value in found], dtype=np.float64)


def parse_envi_header(path: str | Path) -> EnviHeader:
    """Lê um ``.hdr`` ENVI sem tocar no binário pareado."""
    header_path = Path(path)
    text = header_path.read_text(encoding="utf-8", errors="replace")
    if not text.lstrip().upper().startswith("ENVI"):
        raise ValueError(f"not an ENVI header: {header_path}")

    fields = dict(_split_entries(text))
    comments = _parse_comments(text)

    try:
        samples = int(fields["samples"])
        lines = int(fields["lines"])
        bands = int(fields["bands"])
        data_type = int(fields["data type"])
    except KeyError as exc:
        raise ValueError(f"missing required ENVI key: {exc.args[0]!r}") from exc

    if min(samples, lines, bands) <= 0:
        raise ValueError("ENVI dimensions must be positive")

    interleave = fields.get("interleave", "bsq").strip().lower()
    if interleave not in _INTERLEAVES:
        raise ValueError(f"unsupported ENVI interleave: {interleave!r}")

    wavelengths = None
    if "wavelength" in fields:
        values = _floats(fields["wavelength"])
        if values.size != bands:
            raise ValueError(
                f"wavelength count {values.size} does not match bands {bands}"
            )
        wavelengths = values

    return EnviHeader(
        samples=samples,
        lines=lines,
        bands=bands,
        data_type=data_type,
        interleave=interleave,
        byte_order=int(fields.get("byte order", 0)),
        header_offset=int(fields.get("header offset", 0)),
        description=fields.get("description"),
        wavelengths=wavelengths,
        wavelength_units=fields.get("wavelength units"),
        fields=fields,
        comments=comments,
    )


def _binary_path(header_path: Path, explicit: str | Path | None) -> Path:
    """Resolve o binário pareado sem adivinhar silenciosamente."""
    if explicit is not None:
        candidate = Path(explicit)
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return candidate
    stem = header_path.with_suffix("")
    candidates = [stem, *(stem.with_suffix(ext) for ext in (".img", ".dat", ".bin"))]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"no ENVI binary paired with {header_path.name}; tried: "
        + ", ".join(candidate.name for candidate in candidates)
    )


def open_envi_cube(
    header_path: str | Path,
    *,
    binary_path: str | Path | None = None,
    strict_size: bool = True,
) -> tuple[np.memmap, EnviHeader]:
    """Mapeia um cubo ENVI como ``(lines, samples, bands)`` sem alterar os valores.

    Retorna o cubo e o cabeçalho lido. Os valores são exatamente os do arquivo:
    não há normalização, recorte nem conversão de unidade. O reordenamento entre
    interleaves é feito por transposição de vista, então nenhuma cópia é criada.
    """
    path = Path(header_path)
    header = parse_envi_header(path)
    binary = _binary_path(path, binary_path)

    available = binary.stat().st_size - header.header_offset
    if available < header.expected_size:
        raise ValueError(
            f"{binary.name} has {available} usable bytes, "
            f"expected at least {header.expected_size}"
        )
    if strict_size and available != header.expected_size:
        raise ValueError(
            f"{binary.name} has {available} usable bytes, "
            f"expected exactly {header.expected_size}; "
            "pass strict_size=False to allow trailing data"
        )

    lines, samples, bands = header.lines, header.samples, header.bands
    disk_shape = {
        "bsq": (bands, lines, samples),
        "bil": (lines, bands, samples),
        "bip": (lines, samples, bands),
    }[header.interleave]
    raw = np.memmap(
        binary,
        dtype=header.dtype,
        mode="r",
        offset=header.header_offset,
        shape=disk_shape,
    )
    axes = {"bsq": (1, 2, 0), "bil": (0, 2, 1), "bip": (0, 1, 2)}[header.interleave]
    return raw.transpose(axes), header


def envi_nodata_mask(cube: np.ndarray, sentinel: float = 0.0) -> np.ndarray:
    """Marca pixels iguais ao sentinela em todas as bandas.

    Cubos ortorretificados carregam preenchimento fora da faixa imageada. Esses
    pixels não são medidas e não devem entrar em estatística de fundo nem servir
    de mínimo para qualquer reescalonamento.
    """
    data = np.asarray(cube)
    if data.ndim != 3:
        raise ValueError("cube must be (lines, samples, bands)")
    if np.isnan(sentinel):
        return np.isnan(data).all(axis=2)
    return (data == sentinel).all(axis=2)
