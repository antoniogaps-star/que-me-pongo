"""Genera los archivos de marca de "¿Qué me pongo?" desde el símbolo vectorial.

El símbolo: un gancho de ropa cuyo cuello es un signo de interrogación — dice el nombre
de la app sin palabras. Se dibuja aquí con Pillow (no se recorta una imagen) para que
salga nítido en cualquier tamaño: del ícono de 48 px al splash de pantalla completa.

Uso:  python brand/generate_brand.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND_DIR = Path(__file__).resolve().parent

# Paleta (tomada del logo de Toño).
ORO = (212, 180, 131, 255)
ORO_CLARO = (232, 207, 160, 255)
NEGRO = (11, 11, 12, 255)
TRANSPARENTE = (0, 0, 0, 0)

# Se dibuja 4x más grande y luego se reduce: así los bordes salen suaves (antialias).
SS = 4


def _arc_points(
    cx: float, cy: float, r: float, start_deg: float, end_deg: float, steps: int = 96
) -> list[tuple[float, float]]:
    """Puntos de un arco, para trazarlo como línea gruesa con extremos redondeados."""
    return [
        (
            cx + r * math.cos(math.radians(start_deg + (end_deg - start_deg) * i / steps)),
            cy + r * math.sin(math.radians(start_deg + (end_deg - start_deg) * i / steps)),
        )
        for i in range(steps + 1)
    ]


def _thick_line(
    draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], width: float, color: tuple
) -> None:
    """Línea gruesa con las uniones y los extremos redondeados (Pillow no lo hace solo)."""
    draw.line(points, fill=color, width=int(width))
    r = width / 2
    for x, y in points:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def draw_mark(
    size: int,
    *,
    background: tuple = TRANSPARENTE,
    padding: float = 0.0,
    frame: bool = True,
) -> Image.Image:
    """Dibuja el símbolo. `padding` deja aire alrededor (para el ícono adaptativo).

    `frame=False` omite el marco redondeado: a tamaño de ícono (32–48 px) el marco y el
    gancho compiten y el dibujo se satura. Como el teléfono YA dibuja un cuadro redondeado
    alrededor del ícono, quitarlo deja el gancho grande y legible. El marco se conserva
    para el logo del splash y la landing, donde hay espacio de sobra.
    """
    s = size * SS
    img = Image.new("RGBA", (s, s), background)
    draw = ImageDraw.Draw(img)

    # Lienzo interior tras aplicar el aire pedido.
    pad = s * padding
    box = s - 2 * pad
    # Sin marco, el gancho se agranda para ocupar el hueco que dejó.
    zoom = 1.0 if frame else 1.34

    def u(v: float) -> float:
        """Convierte una coordenada del diseño (0–512) a píxeles del lienzo."""
        return pad + box / 2 + box * ((v - 256) / 512) * zoom

    stroke = box * (16 / 512)

    # ── Marco redondeado ────────────────────────────────────
    if frame:
        draw.rounded_rectangle(
            [u(46), u(46), u(466), u(466)],
            radius=u(150) - u(46),
            outline=ORO,
            width=int(stroke),
        )

    # El símbolo tiene DOS interrogantes: el gancho colgador es uno (arriba), y otro
    # grande atraviesa la barra del gancho, que se abre para dejarlo pasar.
    # Sin marco (ícono del teléfono) el trazo va un pelo más grueso: a 32–48 px los dos
    # interrogantes se cierran si la línea es muy fina.
    linea = box * (17 / 512) * (1.0 if frame else 1.12)

    def _pregunta(cx: float, cy: float, radio: float, tail_y: float) -> None:
        """Dibuja un '?' sin punto: arco de izquierda→arriba→derecha y cola hacia el centro."""
        arco = _arc_points(u(cx), u(cy), u(cx + radio) - u(cx), 180, 420)
        _thick_line(draw, arco, linea, ORO)
        fin = arco[-1]
        _thick_line(draw, [fin, (u(cx), u(tail_y))], linea, ORO)

    # ── Los hombros del gancho (diagonales desde el vértice) ──
    _thick_line(draw, [(u(83), u(333)), (u(256), u(231)), (u(429), u(333))], linea, ORO)

    # ── La barra, partida en dos: el hueco central es por donde pasa el "?" grande ──
    _thick_line(draw, [(u(83), u(333)), (u(214), u(333))], linea, ORO)
    _thick_line(draw, [(u(298), u(333)), (u(429), u(333))], linea, ORO)

    # ── Interrogante de arriba: es el colgador del gancho ──
    _pregunta(256, 145, 42, 224)

    # ── Interrogante grande: cruza la barra y su punto queda debajo ──
    _pregunta(256, 303, 34, 360)
    punto = box * (13 / 512)
    draw.ellipse(
        [u(256) - punto, u(392) - punto, u(256) + punto, u(392) + punto], fill=ORO
    )

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    out = BRAND_DIR
    out.mkdir(exist_ok=True)

    # Logo CON marco: para el splash y la landing, donde hay espacio de sobra.
    draw_mark(1024).save(out / "logo_mark.png")

    # Ícono de la app SIN marco: el teléfono ya recorta en cuadro redondeado, así que
    # el marco propio solo saturaría el dibujo a 48 px.
    icon = Image.new("RGBA", (1024, 1024), NEGRO)
    icon.alpha_composite(draw_mark(1024, padding=0.17, frame=False))
    icon.save(out / "icon.png")

    # Capa frontal del ícono adaptativo de Android (Android le pone su propio fondo
    # y recorta las esquinas: por eso lleva más aire todavía).
    draw_mark(1024, padding=0.30, frame=False).save(out / "icon_foreground.png")

    # Versiones chicas para la web y el panel.
    for px in (192, 512):
        icon.resize((px, px), Image.LANCZOS).save(out / f"icon-{px}.png")

    # Logo completo (símbolo + nombre + eslogan) y pantalla de bienvenida.
    draw_lockup(1400, 900, transparent=True).save(out / "logo.png")
    draw_lockup(1242, 2208).save(out / "splash.png")

    print("Marca generada en", out)


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Carga una fuente del sistema; si no está, usa la de respaldo de Pillow."""
    for path in (f"C:/Windows/Fonts/{name}", f"/usr/share/fonts/truetype/{name}"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    cx: float,
    y: float,
    color: tuple,
    tracking: float = 0.0,
) -> float:
    """Escribe centrado, con espaciado entre letras. Devuelve el alto ocupado."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths, strict=True):
        draw.text((x, y), ch, font=font, fill=color)
        x += w + tracking
    box = font.getbbox(text)
    return box[3] - box[1]


def draw_lockup(width: int, height: int, *, transparent: bool = False) -> Image.Image:
    """Símbolo + nombre + eslogan, centrados. Es el splash y también el logo completo."""
    img = Image.new("RGBA", (width, height), TRANSPARENTE if transparent else NEGRO)
    draw = ImageDraw.Draw(img)
    cx = width / 2

    unit = min(width, height)
    mark_size = int(unit * 0.30)
    mark = draw_mark(mark_size)

    title_font = _font("georgia.ttf", int(unit * 0.088))
    slogan_font = _font("georgia.ttf", int(unit * 0.026))

    # Alto total del bloque, para centrarlo verticalmente de verdad.
    gap1, gap2, gap3 = unit * 0.055, unit * 0.045, unit * 0.040
    title_h = title_font.getbbox("¿Qué me pongo?")[3]
    slogan_h = slogan_font.getbbox("TU CLÓSET")[3]
    total = mark_size + gap1 + title_h + gap2 + gap3 + slogan_h
    y = (height - total) / 2

    img.alpha_composite(mark, (int(cx - mark_size / 2), int(y)))
    y += mark_size + gap1

    _centered(draw, "¿Qué me pongo?", title_font, cx, y, ORO_CLARO, tracking=unit * 0.004)
    y += title_h + gap2

    # Filete ornamental: dos líneas y un rombo, como en el logo original.
    ancho = unit * 0.13
    draw.line([(cx - ancho, y), (cx - unit * 0.022, y)], fill=ORO, width=max(1, int(unit * 0.0016)))
    draw.line([(cx + unit * 0.022, y), (cx + ancho, y)], fill=ORO, width=max(1, int(unit * 0.0016)))
    d = unit * 0.011
    draw.polygon([(cx, y - d), (cx + d, y), (cx, y + d), (cx - d, y)], fill=ORO)
    y += gap3

    _centered(
        draw,
        "TU CLÓSET. TU ESTILO. TU MEJOR VERSIÓN.",
        slogan_font,
        cx,
        y,
        (185, 174, 156, 255),
        tracking=unit * 0.0055,
    )
    return img


if __name__ == "__main__":
    main()
