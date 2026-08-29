"""Redesenha o overlay da grade de poços a partir da geometria congelada.

    python scripts/biohsi_pellets_plate_overlay.py

A geometria da placa de pellets foi obtida por anotação manual única, descrita em
`hypermix/data/biohsi_pellets_plate_geometry.json`. Este script existe para que a
evidência dessa anotação seja reproduzível por qualquer pessoa: ele lê o artefato
congelado, confere o SHA-256 da geometria e o MD5 do cubo, e redesenha
`assets/biohsi_pellets_plate_grid.png`.

O fundo é uma banda no infravermelho próximo, onde o repórter não domina, para
que o alinhamento seja julgado pela estrutura óptica dos poços e não pela
intensidade de qualquer sinal.

Requer o cubo baixado com `scripts/fetch_biohsi.py --dataset rg_bchla_pellets_ctrl.zip`.
"""

from __future__ import annotations

import hashlib
import json
import os
from importlib.resources import files

import numpy as np

from hypermix.envi import open_envi_cube

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBE_HDR = os.path.join(
    HERE, "data", "biohsi", "rg_bchla_pellets_ctrl", "data.hdr"
)
OUTPUT = os.path.join(HERE, "assets", "biohsi_pellets_plate_grid.png")
BACKGROUND_NM = 900.0
CIRCLE_RADIUS_PX = 28


def load_geometry() -> dict:
    resource = files("hypermix.data").joinpath("biohsi_pellets_plate_geometry.json")
    with resource.open("r", encoding="utf-8") as handle:
        doc = json.load(handle)
    blob = json.dumps(
        doc["geometry_image_frame"], sort_keys=True, separators=(",", ":")
    ).encode()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != doc["geometry_sha256"]:
        raise SystemExit("geometry hash mismatch; the frozen artifact was edited")
    return doc


def _cube_md5(path: str) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    from PIL import Image, ImageDraw

    doc = load_geometry()
    geometry = doc["geometry_image_frame"]

    if not os.path.exists(CUBE_HDR):
        raise SystemExit(
            "cubo ausente; rode "
            "python scripts/fetch_biohsi.py --dataset rg_bchla_pellets_ctrl.zip"
        )
    binary = CUBE_HDR[: -len(".hdr")]
    actual = _cube_md5(binary)
    if actual != doc["cube_md5"]:
        raise SystemExit(
            f"cube MD5 mismatch: expected {doc['cube_md5']}, got {actual}"
        )

    cube, header = open_envi_cube(CUBE_HDR)
    band = int(np.argmin(np.abs(header.wavelengths - BACKGROUND_NM)))
    plane = np.asarray(cube[:, :, band], dtype=np.float64)
    low, high = np.percentile(plane, [1, 99])
    grey = (np.clip((plane - low) / (high - low), 0.0, 1.0) * 255).astype(np.uint8)

    image = Image.fromarray(np.stack([grey] * 3, axis=-1))
    draw = ImageDraw.Draw(image)
    radius = CIRCLE_RADIUS_PX
    for row_index, y in enumerate(geometry["rows_y"]):
        for col_index, x in enumerate(geometry["cols_x"]):
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                outline=(50, 255, 120),
                width=2,
            )
            label = f"{geometry['row_labels'][row_index]}{col_index + 1}"
            draw.text((x - radius + 2, y - radius - 6), label, fill=(255, 220, 0))

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    image.save(OUTPUT)
    print(f"geometria conferida, SHA-256 {doc['geometry_sha256'][:16]}...")
    print(f"{len(geometry['rows_y'])} linhas x {len(geometry['cols_x'])} colunas")
    print(f"banda de fundo {header.wavelengths[band]:.1f} nm")
    print(f"overlay escrito em {OUTPUT}")
    print(
        "Rotulos impressos A a H aparecem na borda direita da imagem: "
        "a coluna fisica 1 fica a DIREITA."
    )


if __name__ == "__main__":
    main()
