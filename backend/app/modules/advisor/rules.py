"""Reglas locales de vestimenta: el asesor gratis (sin IA).

No pretenden tener el criterio de un estilista, pero sí armar conjuntos correctos, variados
y explicados con honestidad. Cómo piensan:

1. La ocasión fija una formalidad base (1–10) y lo que quieres proyectar la ajusta y dice
   qué estilos y colores lo transmiten (ver `PROJECTIONS`).
2. Se arman TODAS las combinaciones posibles (arriba + abajo + calzado, o una pieza
   completa + calzado) y se califica cada una: formalidad, estilo, colores, clima.
3. Se propone la mejor que aún no hayas visto: "Proponme otro" va bajando por la lista.

Regla de oro: la formalidad manda. A una boda no vas en tenis aunque el color combine.
"""

from dataclasses import dataclass
from itertools import product
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

# Cómo se lee cada ocasión dentro de una frase ("Para una reunión…").
OCCASION_PHRASE: dict[str, str] = {
    "dia normal": "un día normal",
    "salida casual": "una salida casual",
    "escuela": "la escuela",
    "viaje": "un viaje",
    "trabajo": "el trabajo",
    "reunion": "una reunión",
    "cita": "una cita",
    "fiesta": "una fiesta",
    "evento formal": "un evento formal",
}

# Colores que combinan con todo: son el comodín seguro.
NEUTRALS = {
    "negro", "blanco", "gris", "beige", "azul marino", "marino", "cafe", "café", "crema",
    "hueso", "camel", "caqui", "kaki", "mezclilla", "plata",
    # La mezclilla oscura funciona como neutro aunque su color sea azul.
    "petroleo", "azul petroleo", "azul oscuro", "denim", "indigo", "azul mezclilla",
}
# Colores oscuros: dan autoridad y seriedad.
DARKS = {"negro", "azul marino", "marino", "gris oscuro", "vino", "cafe", "café", "verde olivo"}


@dataclass(frozen=True)
class Projection:
    """Lo que transmite una imagen: cuánto sube o baja la formalidad, un mínimo de
    formalidad, los estilos que la logran y qué colores le favorecen."""

    label: str
    # Cómo se dice con "imagen" (femenino): "una imagen segura". Sirve para todos.
    imagen: str
    delta: int
    floor: int
    styles: frozenset[str]
    likes_neutral: bool = False
    likes_dark: bool = False
    likes_color: bool = False
    why: str = ""


PROJECTIONS: dict[str, Projection] = {
    "elegante": Projection(
        "elegante", "elegante", 2, 7, frozenset({"elegante", "clasico", "minimalista"}),
        likes_neutral=True,
        why="la elegancia está en lo limpio: pocos colores y prendas bien hechas",
    ),
    "seguro": Projection(
        "seguro", "segura", 1, 5, frozenset({"clasico", "moderno", "ejecutivo"}),
        likes_dark=True,
        why="los tonos firmes y un corte clásico transmiten que sabes lo que haces",
    ),
    "atractivo": Projection(
        "atractivo", "atractiva", 1, 5, frozenset({"moderno", "elegante", "streetwear"}),
        likes_color=True,
        why="lo moderno y bien combinado llama la mirada sin exagerar",
    ),
    "moderno": Projection(
        "moderno", "moderna", 0, 1, frozenset({"moderno", "streetwear", "minimalista"}),
        why="las prendas actuales y las líneas simples se ven al día",
    ),
    "relajado": Projection(
        "relajado", "relajada", -2, 1, frozenset({"casual", "deportivo"}),
        why="lo cómodo y sin rigidez se ve natural",
    ),
    "profesional": Projection(
        "profesional", "profesional", 2, 7, frozenset({"ejecutivo", "clasico", "elegante"}),
        likes_neutral=True,
        why="los neutros y la formalidad media-alta dicen 'confíen en mí'",
    ),
    "poderoso": Projection(
        "poderoso", "poderosa", 3, 8, frozenset({"elegante", "ejecutivo"}),
        likes_dark=True,
        why="lo oscuro y formal impone presencia",
    ),
}


@dataclass
class Outfit:
    """Un conjunto propuesto, con su explicación."""

    garment_ids: list[str]
    explanation: str
    projected_image: str


def _norm(text: str | None) -> str:
    s = (text or "").strip().lower()
    for a, b in zip("áéíóúü", "aeiouu", strict=True):
        s = s.replace(a, b)
    return s


def _formality_of(occasion: str) -> int:
    return OCCASION_FORMALITY.get(_norm(occasion), 5)


def _target(occasion: str, projection: Projection | None) -> int:
    base = _formality_of(occasion)
    if projection is None:
        return base
    return max(1, min(10, max(base + projection.delta, projection.floor)))


def _fits_season(garment: dict[str, Any], temperature_c: float | None) -> bool:
    """Descarta lo que no va con el clima. Sin dato de clima, todo pasa."""
    season = garment.get("season", "todo")
    if temperature_c is None or season == "todo":
        return True
    if season == "calor":
        return temperature_c >= 20
    return temperature_c <= 22  # "frio"


def _formality(g: dict[str, Any]) -> int:
    return int(g.get("formality", 5))


def _color(g: dict[str, Any]) -> str:
    return _norm(str(g.get("color") or ""))


def _is_neutral(g: dict[str, Any]) -> bool:
    c = _color(g)
    if not c or c in NEUTRALS or any(n in c for n in ("gris", "negro", "blanco", "beige")):
        return True
    # Un pantalón de mezclilla (jeans) combina con todo, sea cual sea su tono de azul.
    nombre = _norm(str(g.get("name") or ""))
    return "mezclilla" in nombre or "jean" in nombre


def _is_dark(g: dict[str, Any]) -> bool:
    c = _color(g)
    return c in DARKS or "oscuro" in c or "negro" in c


def _styles(g: dict[str, Any]) -> set[str]:
    return {_norm(s) for s in g.get("styles") or []}


def _score(
    combo: list[dict[str, Any]],
    target: int,
    projection: Projection | None,
    preferred_styles: set[str],
    avoid_colors: set[str],
) -> float:
    """Qué tan bien funciona un conjunto. Más alto = mejor."""
    score = 0.0
    # 1) Formalidad: la que más pesa. Una prenda muy desfasada pesa el doble.
    for g in combo:
        gap = abs(_formality(g) - target)
        score -= gap * 2 + (gap * 2 if gap >= 3 else 0)
    # 2) Estilo: prendas que transmiten lo que pediste (y lo que te gusta).
    wanted = set(projection.styles) if projection else set()
    for g in combo:
        st = _styles(g)
        if st & wanted:
            score += 2
        if st & preferred_styles:
            score += 1
    # 3) Color: máximo un color fuerte; dos o más chocan.
    loud = [g for g in combo if not _is_neutral(g)]
    loud_colors = {_color(g) for g in loud}
    if len(loud_colors) >= 2:
        score -= 3 * (len(loud_colors) - 1)
    if projection is not None:
        if projection.likes_neutral and not loud:
            score += 2
        if projection.likes_dark:
            score += sum(1 for g in combo if _is_dark(g))
        if projection.likes_color and len(loud_colors) == 1:
            score += 2
    for g in combo:
        if any(c and c in _color(g) for c in avoid_colors):
            score -= 4
    return score


def _bases(garments: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Todas las bases posibles: arriba+abajo+calzado, o pieza completa+calzado."""
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for g in garments:
        by_cat.setdefault(str(g.get("category")), []).append(g)
    shoes = by_cat.get("calzado", [])
    combos = [list(c) for c in product(by_cat.get("arriba", []), by_cat.get("abajo", []), shoes)]
    combos += [list(c) for c in product(by_cat.get("completo", []), shoes)]
    return combos


def _best_extra(
    garments: list[dict[str, Any]],
    category: str,
    target: int,
    projection: Projection | None,
    used: set[str],
) -> dict[str, Any] | None:
    """El abrigo o accesorio que mejor acompaña (formalidad más cercana, estilo afín)."""
    wanted = set(projection.styles) if projection else set()
    candidates = [g for g in garments if g.get("category") == category and str(g["id"]) not in used]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda g: (
            abs(_formality(g) - target) - (2 if _styles(g) & wanted else 0),
            0 if _is_neutral(g) else 1,
        ),
    )


def _ids(combo: list[dict[str, Any]]) -> frozenset[str]:
    return frozenset(str(g["id"]) for g in combo)


def build_outfit(
    garments: list[dict[str, Any]],
    *,
    occasion: str = "dia normal",
    projection: str = "",
    temperature_c: float | None = None,
    anchor_garment_id: str | None = None,
    exclude: list[list[str]] | None = None,
    preferred_styles: list[str] | None = None,
    avoid_colors: list[str] | None = None,
) -> Outfit | None:
    """Arma el mejor conjunto que aún no se haya mostrado.

    `exclude`: conjuntos ya vistos (listas de ids). Si ya se vieron todos, se vuelve a
    empezar por el mejor y la explicación lo dice. `anchor_garment_id`: "¿con qué
    combino esto?", el conjunto debe incluir esa prenda.
    """
    proj = PROJECTIONS.get(_norm(projection))
    target = _target(occasion, proj)
    usable = [g for g in garments if _fits_season(g, temperature_c)]
    anchor = str(anchor_garment_id) if anchor_garment_id else None

    bases = _bases(usable)
    if anchor is not None:
        anchor_g = next((g for g in garments if str(g["id"]) == anchor), None)
        if anchor_g is None:
            return None
        if anchor_g.get("category") in {"arriba", "abajo", "calzado", "completo"}:
            bases = [b for b in bases if anchor in _ids(b)]
    if not bases:
        return None  # Falta una pieza básica: no inventamos un outfit incompleto.

    pref = {_norm(s) for s in preferred_styles or []}
    avoid = {_norm(c) for c in avoid_colors or []}
    ranked = sorted(bases, key=lambda b: _score(b, target, proj, pref, avoid), reverse=True)

    seen = {frozenset(str(i) for i in combo) for combo in exclude or []}
    fresh = [b for b in ranked if _ids(b) not in seen]
    repeated = not fresh
    chosen = list((fresh or ranked)[0])
    used = {str(g["id"]) for g in chosen}

    # Extras: la prenda ancla si es abrigo/accesorio, abrigo con frío, y un accesorio
    # solo si suma a lo que quieres proyectar.
    if anchor is not None and anchor not in used:
        chosen.append(next(g for g in garments if str(g["id"]) == anchor))
        used.add(anchor)
    if temperature_c is not None and temperature_c <= 18 and not any(
        g.get("category") == "abrigo" for g in chosen
    ):
        coat = _best_extra(usable, "abrigo", target, proj, used)
        if coat is not None:
            chosen.append(coat)
            used.add(str(coat["id"]))
    if proj is not None and not any(g.get("category") == "accesorio" for g in chosen):
        acc = _best_extra(usable, "accesorio", target, proj, used)
        if acc is not None and _styles(acc) & proj.styles:
            chosen.append(acc)
            used.add(str(acc["id"]))

    return Outfit(
        garment_ids=[str(g["id"]) for g in chosen],
        explanation=_explain(
            chosen, occasion, proj, target, temperature_c,
            options=len(ranked), repeated=repeated, garments=usable,
        ),
        projected_image=projection or _projection_for(target),
    )


def _projection_for(target: int) -> str:
    if target >= 8:
        return "Formalidad y respeto"
    if target >= 6:
        return "Seguridad y buen gusto"
    return "Comodidad y naturalidad"


def _names(items: list[dict[str, Any]]) -> str:
    names = [str(g.get("name", "")) for g in items]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " y " + names[-1]


def _explain(
    chosen: list[dict[str, Any]],
    occasion: str,
    proj: Projection | None,
    target: int,
    temperature_c: float | None,
    *,
    options: int,
    repeated: bool,
    garments: list[dict[str, Any]],
) -> str:
    """Explica POR QUÉ funciona, dice con tacto lo que no cuadra y da una salida."""
    ocasion = OCCASION_PHRASE.get(_norm(occasion), _norm(occasion) or "hoy")
    meta = f", con una imagen {proj.imagen}" if proj else ""
    partes = [f"Para {ocasion}{meta}: {_names(chosen)}."]

    # Por qué funciona: colores.
    loud = [g for g in chosen if not _is_neutral(g)]
    if not loud:
        partes.append("Todo en tonos neutros: combina sin riesgo y se ve ordenado.")
    elif len({_color(g) for g in loud}) == 1:
        color = str(loud[0].get("color") or "").strip()
        partes.append(
            f"{loud[0].get('name')} ({color}) es el punto de color y lo demás lo equilibra."
        )
    else:
        partes.append("Ojo: hay más de un color fuerte; si puedes, deja solo uno.")

    # Por qué funciona: estilo pedido.
    if proj is not None:
        aciertos = [g for g in chosen if _styles(g) & proj.styles]
        if len(aciertos) == len(chosen):
            partes.append(f"Todo el conjunto va con lo que buscas: {proj.why}.")
        elif aciertos:
            verbo = "va" if len(aciertos) == 1 else "van"
            partes.append(f"{_names(aciertos)} {verbo} con lo que buscas: {proj.why}.")
        if proj.likes_color and not loud:
            partes.append("Si quieres llamar más la atención, súmale un toque de color.")

    # Honestidad: la prenda que más se aleja de la formalidad que pide el momento.
    flojo = max(chosen, key=lambda g: abs(_formality(g) - target))
    gap = _formality(flojo) - target
    pide = f"una imagen {proj.imagen}" if proj else ocasion
    if abs(gap) >= 3:
        tipo = "informal" if gap < 0 else "formal"
        partes.append(
            f"El único detalle: {flojo.get('name')} es más {tipo} de lo que pide {pide}."
        )
        mejor = "más formal" if gap < 0 else "más relajado"
        cat = str(flojo.get("category"))
        hay_mejor = any(
            g.get("category") == cat and abs(_formality(g) - target) < abs(gap)
            for g in garments
        )
        if not hay_mejor:
            partes.append(
                f"En tu clóset no hay algo {mejor} de ese tipo; si consigues uno, este "
                "conjunto sube de nivel."
            )
    elif proj is not None and not any(_styles(g) & proj.styles for g in chosen):
        partes.append(
            f"Para una imagen más {proj.imagen} te faltan prendas de ese estilo; con lo que "
            "tienes, esta es la mejor opción."
        )

    if temperature_c is not None:
        coat = next((g for g in chosen if g.get("category") == "abrigo"), None)
        if temperature_c <= 18 and coat is not None:
            partes.append(f"Con {temperature_c:.0f}°C, súmale el abrigo: {coat.get('name')}.")
        elif temperature_c <= 18:
            partes.append(f"Con {temperature_c:.0f}°C, agrega abrigo.")
        elif temperature_c >= 28:
            partes.append(f"Con {temperature_c:.0f}°C, mantenlo ligero.")

    if repeated:
        partes.append(
            "Ya te mostré todas las combinaciones que permite tu clóset; agrega más "
            "prendas para tener nuevas opciones."
        )
    elif options == 1:
        partes.append(
            "Por ahora es la única combinación posible: agrega más prendas y te daré "
            "otras opciones."
        )
    return " ".join(partes)
