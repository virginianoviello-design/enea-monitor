"""
Catalogo delle fonti da monitorare per il sistema ENEA.

Ogni fonte ha:
- id: identificativo univoco
- name: nome leggibile
- url: URL della pagina eventi / RSS / calendario
- type: 'rss' | 'html' | 'ical' | 'api' | 'manual'
- category: area tematica principale
- priority_hint: suggerimento di rilievo (aiuta il classificatore)
- parser: nome della funzione di parsing in scraper.py (None = parser generico)

Organizzato per macro-area, facile da estendere.
"""

SOURCES = [
    # ===== ISTITUZIONALI (top priority, classificazione A tipica) =====
    {
        "id": "quirinale",
        "name": "Quirinale — Agenda Presidente",
        "url": "https://www.quirinale.it/agenda",
        "type": "html",
        "category": "istituzionale",
        "priority_hint": "A",
        "parser": "parse_quirinale",
    },
    {
        "id": "governo",
        "name": "Governo — Agenda Presidente del Consiglio",
        "url": "https://www.governo.it/it/agenda-il-presidente",
        "type": "html",
        "category": "istituzionale",
        "priority_hint": "A",
        "parser": "parse_governo",
    },
    {
        "id": "mase",
        "name": "MASE — Ministero Ambiente e Sicurezza Energetica",
        "url": "https://www.mase.gov.it/comunicazione/eventi",
        "type": "html",
        "category": "istituzionale",
        "priority_hint": "A",
        "parser": "parse_mase",
    },

    # ===== ENERGIA E TRANSIZIONE =====
    {
        "id": "italia_solare",
        "name": "Italia Solare",
        "url": "https://www.italiasolare.eu/eventi/",
        "type": "html",
        "category": "energia_rinnovabile",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "elettricita_futura",
        "name": "Elettricità Futura",
        "url": "https://www.elettricitafutura.it/eventi.html",
        "type": "html",
        "category": "energia_rinnovabile",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "anev",
        "name": "ANEV — Associazione Nazionale Energia del Vento",
        "url": "https://www.anev.org/eventi/",
        "type": "html",
        "category": "energia_rinnovabile",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "coordinamento_free",
        "name": "Coordinamento FREE",
        "url": "https://www.free-energia.it/eventi/",
        "type": "html",
        "category": "energia_rinnovabile",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "aiee",
        "name": "AIEE — Associazione Italiana Economisti dell'Energia",
        "url": "https://www.aiee.it/eventi/",
        "type": "html",
        "category": "energia",
        "priority_hint": "C",
        "parser": None,
    },
    {
        "id": "wec_italia",
        "name": "WEC Italia — World Energy Council",
        "url": "https://www.wec-italia.org/eventi/",
        "type": "html",
        "category": "energia",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "fiper",
        "name": "FIPER — Federazione Italiana Produttori Energia Rinnovabile",
        "url": "https://www.fiper.it/eventi/",
        "type": "html",
        "category": "energia_rinnovabile",
        "priority_hint": "C",
        "parser": None,
    },

    # ===== EFFICIENZA ENERGETICA =====
    {
        "id": "fire",
        "name": "FIRE — Federazione Italiana per l'Uso Razionale dell'Energia",
        "url": "https://www.fire-italia.org/eventi/",
        "type": "html",
        "category": "efficienza_energetica",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "kyoto_club",
        "name": "Kyoto Club",
        "url": "https://www.kyotoclub.org/category/eventi/",
        "type": "html",
        "category": "efficienza_energetica",
        "priority_hint": "C",
        "parser": None,
    },
    {
        "id": "motus_e",
        "name": "Motus-E (mobilità elettrica e storage)",
        "url": "https://www.motus-e.org/eventi/",
        "type": "html",
        "category": "efficienza_energetica",
        "priority_hint": "B",
        "parser": None,
    },

    # ===== NUCLEARE =====
    {
        "id": "sogin",
        "name": "SOGIN — Società Gestione Impianti Nucleari",
        "url": "https://www.sogin.it/it/comunicazione/eventi/",
        "type": "html",
        "category": "nucleare",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "associazione_italiana_nucleare",
        "name": "AIN — Associazione Italiana Nucleare",
        "url": "https://www.assonucleare.it/eventi/",
        "type": "html",
        "category": "nucleare",
        "priority_hint": "B",
        "parser": None,
    },

    # ===== ECONOMIA CIRCOLARE E RIFIUTI =====
    {
        "id": "comieco",
        "name": "Comieco — Consorzio Recupero Carta",
        "url": "https://www.comieco.org/eventi/",
        "type": "html",
        "category": "economia_circolare",
        "priority_hint": "C",
        "parser": None,
    },
    {
        "id": "fondazione_sviluppo_sostenibile",
        "name": "Fondazione per lo Sviluppo Sostenibile — Circular Economy Network",
        "url": "https://circulareconomynetwork.it/eventi/",
        "type": "html",
        "category": "economia_circolare",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "utilitalia",
        "name": "Utilitalia",
        "url": "https://www.utilitalia.it/eventi",
        "type": "html",
        "category": "economia_circolare",
        "priority_hint": "C",
        "parser": None,
    },

    # ===== SOSTENIBILITÀ E ESG =====
    {
        "id": "asvis",
        "name": "ASviS — Alleanza per lo Sviluppo Sostenibile",
        "url": "https://asvis.it/eventi/",
        "type": "html",
        "category": "sostenibilita",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "legambiente",
        "name": "Legambiente",
        "url": "https://www.legambiente.it/eventi/",
        "type": "html",
        "category": "sostenibilita",
        "priority_hint": "C",
        "parser": None,
    },

    # ===== MEDIA E THINK TANK =====
    {
        "id": "sole24ore_eventi",
        "name": "Il Sole 24 Ore — Eventi",
        "url": "https://eventi.ilsole24ore.com/",
        "type": "html",
        "category": "media",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "staffetta",
        "name": "Staffetta Quotidiana",
        "url": "https://www.staffettaonline.com/agenda.aspx",
        "type": "html",
        "category": "media",
        "priority_hint": "C",
        "parser": None,
    },
    {
        "id": "teha",
        "name": "TEHA — The European House Ambrosetti",
        "url": "https://eventi.ambrosetti.eu/",
        "type": "html",
        "category": "think_tank",
        "priority_hint": "B",
        "parser": None,
    },

    # ===== AUTORITÀ E REGOLATORI =====
    {
        "id": "arera",
        "name": "ARERA — Autorità Regolazione Energia",
        "url": "https://www.arera.it/comunicati-eventi",
        "type": "html",
        "category": "istituzionale",
        "priority_hint": "B",
        "parser": None,
    },
    {
        "id": "gse",
        "name": "GSE — Gestore Servizi Energetici",
        "url": "https://www.gse.it/eventi",
        "type": "html",
        "category": "istituzionale",
        "priority_hint": "B",
        "parser": None,
    },
]


# Mapping categoria -> area ENEA (usata nel classificatore)
CATEGORY_TO_ENEA_AREA = {
    "istituzionale": "Presidenza",
    "energia_rinnovabile": "Efficienza energetica e rinnovabili",
    "energia": "Efficienza energetica e rinnovabili",
    "efficienza_energetica": "Efficienza energetica e rinnovabili",
    "nucleare": "Fusione e sicurezza nucleare",
    "economia_circolare": "Economia circolare",
    "sostenibilita": "Sostenibilità dei sistemi produttivi",
    "media": "Divulgazione",
    "think_tank": "Divulgazione",
}


def get_sources_by_category(category: str):
    """Filtra le fonti per categoria."""
    return [s for s in SOURCES if s["category"] == category]


def get_all_sources():
    """Restituisce tutte le fonti."""
    return SOURCES
