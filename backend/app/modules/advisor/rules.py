"""Reglas locales de vestimenta: el respaldo cuando no hay IA disponible.

No pretenden tener criterio de estilista — su trabajo es que la app **nunca se quede muda**
si no hay internet, se acabó el cupo de la IA o falta la llave. Arman un conjunto correcto
(nada ridículo) y explican en una frase honesta.

Regla de oro: la formalidad manda. A una boda no vas en tenis aunque el color combine.
"""

from dataclasses import dataclass
from typing import Any

# Qué tan formal es cada ocasión (1–10), para escoger prendas del nivel adecuado.
OCCASION_FORMALITY: dict[str, int] = {
    "dia normal": 4,
    "salida casual": 4,
    "escuela": 4,
    "viaje": 4,
    "trabajo": 7,
    "reunion": 7,
    "cita": 6,
    "fiesta": 6,
    "evento formal": 9,
}

# Colores que combinan con todo: son el comodín seguro.
NEUTRALS = {"negro", "blanco", "gris", "beige", "azul marino", "cafe", "café", "crema"}


@dataclass
class Outfit:
    """Un conjunto propuesto, con su explicación."""

    garment_ids: list[str]
    explanation: str
    projected_image: str


def _formality_of(occasion: str) -> int:
    return OCCASION_FORMALITY.get(occasion.strip().lower(), 5)


def _fits_season(garment: dict[str, Any], temperature_c: float | None) -> bool:
    """Descarta lo que no va con el clima. Sin dato de clima, todo pasa."""
    season = garment.get("season", "todo")
    if temperature_c is None or season == "todo":
        return True
    if season == "calor":
        return temperature_c >= 20
    return temperature_c <= 22  # "frio"


def _pick(
    garments: list[dict[str, Any]],
    category: str,
    target: int,
    temperature_c: float | None,
    used: set[str],
) -> dict[str, Any] | None:
    """Elige la prenda de esa categoría cuya formalidad esté más cerca de la ocasión."""
    candidates = [
        g
        for g in garments
        if g.get("category") == category
        and str(g.get("id")) not in used
        and _fits_season(g, temperature_c)
    ]
    if not candidates:
        return None
    # Desempate: primero la formalidad más cercana, luego los colores neutros (combinan más).
    return min(
        candidates,
        key=lambda g: (
            abs(int(g.get("formality", 5)) - target),
            0 if str(g.get("color", "")).lower() in NEUTRALS else 1,
        ),
    )


def build_outfit(
    garments: list[dict[str, Any]],
    *,
    occasion: str = "dia normal",
    projection: str = "",
    temperature_c: float | None = None,
) -> Outfit | None:
    """Arma un conjunto: arriba + abajo + calzado (+ abrigo si hace frío)."""
    target = _formality_of(occasion)
    used: set[str] = set()
    chosen: list[dict[str, Any]] = []

    for category in ("arriba", "abajo", "calzado"):
        piece = _pick(garments, category, target, temperature_c, used)
        if piece is None:
            return None  # Falta una pieza básica: no inventamos un outfit incompleto.
        used.add(str(piece["id"]))
        chosen.append(piece)

    if temperature_c is not None and temperature_c <= 18:
        coat = _pick(garments, "abrigo", target, temperature_c, used)
        if coat is not None:
            used.add(str(coat["id"]))
            chosen.append(coat)

    return Outfit(
        garment_ids=[str(g["id"]) for g in chosen],
        explanation=_explain(chosen, occasion, target, temperature_c),
        projected_image=projection or _projection_for(target),
    )


def _projection_for(target: int) -> str:
    if target >= 8:
        return "Formalidad y respeto"
    if target >= 6:
        return "Seguridad y buen gusto"
    return "Comodidad y naturalidad"


def _explain(
    chosen: list[dict[str, Any]], occasion: str, target: int, temperature_c: float | None
) -> str:
    """Una frase honesta: qué funciona y, si algo cojea, decirlo sin adornos."""
    names = ", ".join(str(g.get("name", "")) for g in chosen)
    partes = [f"Para {occasion} va bien: {names}."]

    gap = max(abs(int(g.get("formality", 5)) - target) for g in chosen)
    if gap >= 3:
        flojo = max(chosen, key=lambda g: abs(int(g.get("formality", 5)) - target))
        nombre = flojo.get("name", "una prenda")
        if int(flojo.get("formality", 5)) < target:
            partes.append(f"El único detalle: {nombre} es más informal de lo que pide la ocasión.")
        else:
            partes.append(f"El único detalle: {nombre} queda algo formal para el momento.")

    if temperature_c is not None:
        if temperature_c <= 18:
            partes.append(f"Con {temperature_c:.0f}°C, agrega abrigo.")
        elif temperature_c >= 28:
            partes.append(f"Con {temperature_c:.0f}°C, mantenlo ligero.")

    return " ".join(partes)
