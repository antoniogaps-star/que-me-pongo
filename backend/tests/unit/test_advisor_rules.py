"""Las reglas locales: el respaldo sin IA. Deben ser correctas, no geniales."""

from app.modules.advisor import rules

CLOSET = [
    {"id": "1", "category": "arriba", "name": "Playera gris", "color": "gris",
     "styles": ["casual"], "formality": 3, "season": "calor"},
    {"id": "2", "category": "arriba", "name": "Camisa blanca", "color": "blanco",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "3", "category": "abajo", "name": "Jeans azules", "color": "azul",
     "styles": ["casual"], "formality": 4, "season": "todo"},
    {"id": "4", "category": "abajo", "name": "Pantalón de vestir", "color": "negro",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "5", "category": "calzado", "name": "Tenis blancos", "color": "blanco",
     "styles": ["deportivo"], "formality": 3, "season": "todo"},
    {"id": "6", "category": "calzado", "name": "Zapatos negros", "color": "negro",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "7", "category": "abrigo", "name": "Chamarra negra", "color": "negro",
     "styles": ["casual"], "formality": 5, "season": "frio"},
]


def test_evento_formal_elige_lo_formal() -> None:
    """A un evento formal NO se va en tenis, aunque el color combine."""
    outfit = rules.build_outfit(CLOSET, occasion="evento formal")
    assert outfit is not None
    assert set(outfit.garment_ids) == {"2", "4", "6"}


def test_dia_normal_elige_lo_casual() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal")
    assert outfit is not None
    assert set(outfit.garment_ids) == {"1", "3", "5"}


def test_con_frio_agrega_abrigo() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal", temperature_c=10)
    assert outfit is not None
    assert "7" in outfit.garment_ids
    assert "abrigo" in outfit.explanation.lower()


def test_con_calor_no_usa_prendas_de_frio() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal", temperature_c=32)
    assert outfit is not None
    assert "7" not in outfit.garment_ids


def test_closet_incompleto_no_inventa_outfit() -> None:
    """Sin calzado no hay conjunto: es mejor pedir más prendas que mentir."""
    sin_calzado = [g for g in CLOSET if g["category"] != "calzado"]
    assert rules.build_outfit(sin_calzado, occasion="dia normal") is None


def test_explicacion_es_honesta_cuando_algo_no_cuadra() -> None:
    """Si solo hay tenis para un evento formal, el asesor lo dice en vez de callarlo."""
    limitado = [g for g in CLOSET if g["id"] in {"2", "4", "5"}]
    outfit = rules.build_outfit(limitado, occasion="evento formal")
    assert outfit is not None
    assert "detalle" in outfit.explanation.lower()


def test_proyeccion_del_usuario_se_respeta() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="cita", projection="Seguro")
    assert outfit is not None
    assert outfit.projected_image == "Seguro"
