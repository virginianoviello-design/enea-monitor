"""
Scraper modulare per raccolta eventi.

Strategia:
1. Per ogni fonte, prova prima RSS/iCal (pulito, strutturato)
2. Fallback su HTML scraping con BeautifulSoup
3. Parser specifici per le fonti più ostiche (Quirinale, Governo, MASE)
4. Cache SQLite per non rifare fetch inutili

Per la demo inclusa qui, uso dati MOCK che simulano il formato reale.
In produzione, sostituire `fetch_mock_events` con chiamate reali.
"""

import hashlib
import re
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# In produzione: import requests, feedparser
# from bs4 import BeautifulSoup


@dataclass
class Event:
    """Struttura normalizzata di un evento."""
    title: str
    date: str               # ISO format YYYY-MM-DD
    time: Optional[str]     # HH:MM o None
    location: str           # città o "online"
    organizer: str          # chi organizza
    source_id: str          # id della fonte di provenienza
    url: str                # link all'evento
    category: str           # categoria tematica (da sources.py)
    description: str = ""
    is_new: bool = False    # flag "NEW" come nei PDF ENEA
    priority: str = ""      # A / B / C (valorizzato dal classificatore)
    person: Optional[str] = None  # per impegni istituzionali: SM / GM / GP

    def hash_id(self) -> str:
        """Hash univoco basato su titolo+data+luogo per deduplica."""
        key = f"{self.title}|{self.date}|{self.location}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:12]


class EventCache:
    """Cache SQLite per tracciare eventi già visti (e flaggare i NEW)."""

    def __init__(self, db_path: str = "events_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_events (
                hash_id TEXT PRIMARY KEY,
                title TEXT,
                date TEXT,
                first_seen TEXT
            )
        """)
        conn.commit()
        conn.close()

    def is_new(self, event: Event) -> bool:
        """Ritorna True se l'evento non era mai stato visto."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT 1 FROM seen_events WHERE hash_id = ?", (event.hash_id(),)
        )
        seen = cursor.fetchone() is not None
        conn.close()
        return not seen

    def mark_seen(self, event: Event):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR IGNORE INTO seen_events VALUES (?, ?, ?, ?)",
            (event.hash_id(), event.title, event.date,
             datetime.now().isoformat())
        )
        conn.commit()
        conn.close()


# ============================================================
# PARSER SPECIFICI (stub — da implementare con requests + bs4)
# ============================================================

def parse_quirinale(html: str) -> list[Event]:
    """
    Parser per https://www.quirinale.it/agenda
    Il sito espone un'agenda settimanale strutturata con classi CSS note.
    In produzione: soup.find_all('div', class_='agenda-item')
    """
    # STUB — sostituire con parsing reale
    return []


def parse_governo(html: str) -> list[Event]:
    """Parser per https://www.governo.it/it/agenda-il-presidente"""
    return []


def parse_mase(html: str) -> list[Event]:
    """Parser per https://www.mase.gov.it/comunicazione/eventi"""
    return []


def parse_generic_html(html: str, source: dict) -> list[Event]:
    """
    Parser generico. Cerca pattern comuni:
    - tag <article>, <li class="event">, <div class="evento">
    - data in formato GG/MM/AAAA o GG mese AAAA
    - location dopo "|" o dopo "–"
    """
    events = []
    # In produzione, usare BeautifulSoup:
    # soup = BeautifulSoup(html, 'html.parser')
    # for article in soup.find_all(['article', 'li'], class_=re.compile(r'event|evento')):
    #     ...
    return events


# ============================================================
# DATI MOCK (per demo — rimuovere in produzione)
# ============================================================

def fetch_mock_events(source: dict, week_start: datetime) -> list[Event]:
    """
    Ritorna eventi di esempio che simulano quelli reali.
    Usa la settimana `week_start` per generare date coerenti.
    """
    mock_data = {
        "italia_solare": [
            {
                "title": "Convenzione assicurativa Reddito Energetico Sardegna",
                "day_offset": 0, "time": "14:30",
                "location": "online",
                "description": "Webinar per operatori del settore fotovoltaico in Sardegna",
            },
            {
                "title": "SolarConstruction 2026",
                "day_offset": 35, "time": "09:00",
                "location": "Bari",
                "description": "Evento annuale sulla filiera costruzione impianti solari",
            },
        ],
        "elettricita_futura": [
            {
                "title": "Accumuli e flessibilità per un sistema elettrico più competitivo",
                "day_offset": 2, "time": "10:00",
                "location": "online",
                "description": "Webinar congiunto con CESI su storage e flessibilità di rete",
            },
        ],
        "anev": [
            {
                "title": "Eolico 2030: semplificazione reale o nuovi ostacoli?",
                "day_offset": 2, "time": "10:00",
                "location": "Roma",
                "description": "Tavolo di confronto su iter autorizzativi eolico",
            },
        ],
        "fire": [
            {
                "title": "Guida alla nomina dell'energy manager",
                "day_offset": 1, "time": "15:00",
                "location": "online",
                "description": "Webinar formativo su obblighi e best practice",
            },
            {
                "title": "Gli esperti in Gestione dell'Energia tra presente e futuro",
                "day_offset": 16, "time": "09:00",
                "location": "Rimini",
                "description": "Evento FIRE-SECEM",
            },
        ],
        "asvis": [
            {
                "title": "Ritorno al futuro. Investimenti e politiche sostenibili in un mondo instabile",
                "day_offset": 23, "time": "10:00",
                "location": "Milano",
                "description": "Evento ASviS sul futuro degli investimenti ESG",
            },
        ],
        "kyoto_club": [
            {
                "title": "Casa senza gas: la transizione elettrica per decarbonizzare il residenziale",
                "day_offset": 4, "time": "11:00",
                "location": "online",
                "description": "Webinar sulla decarbonizzazione del settore residenziale",
            },
        ],
        "comieco": [
            {
                "title": "Riciclo di Carta e Cartone: il ruolo e le potenzialità del Meridione",
                "day_offset": 4, "time": "10:00",
                "location": "Salerno",
                "description": "Conferenza annuale Comieco sul riciclo nel sud Italia",
            },
        ],
        "motus_e": [
            {
                "title": "Sicurezza energetica e competitività. Le aziende dello storage incontrano le Istituzioni",
                "day_offset": 20, "time": "10:00",
                "location": "Roma",
                "description": "Evento Motus-E / WEC Italia con partecipazione istituzionale",
            },
        ],
        "quirinale": [
            {
                "title": "Cerimonia in occasione dei settant'anni della Corte Costituzionale",
                "day_offset": 3, "time": "11:00",
                "location": "Quirinale",
                "description": "Cerimonia ufficiale",
                "person": "SM",
            },
        ],
        "mase": [
            {
                "title": "Il Santo Graal dell'Energia",
                "day_offset": 0, "time": "09:30",
                "location": "Milano",
                "description": "Convegno IlGiornale/Moneta con Ministro Picchetto Fratin",
                "person": "GP",
            },
            {
                "title": "Ogni scelta accelera il cambiamento",
                "day_offset": 2, "time": "12:00",
                "location": "Padova",
                "description": "Evento duezerocinquezero",
                "person": "GP",
            },
        ],
    }

    if source["id"] not in mock_data:
        return []

    events = []
    for item in mock_data[source["id"]]:
        date = week_start + timedelta(days=item["day_offset"])
        evt = Event(
            title=item["title"],
            date=date.strftime("%Y-%m-%d"),
            time=item.get("time"),
            location=item["location"],
            organizer=source["name"],
            source_id=source["id"],
            url=source["url"],
            category=source["category"],
            description=item.get("description", ""),
            person=item.get("person"),
        )
        events.append(evt)
    return events


# ============================================================
# FUNZIONE PRINCIPALE DI SCRAPING
# ============================================================

def scrape_source(source: dict, week_start: datetime, use_mock: bool = True) -> list[Event]:
    """
    Scrape di una singola fonte.
    use_mock=True per la demo; False in produzione.
    """
    if use_mock:
        return fetch_mock_events(source, week_start)

    # ---- Produzione ----
    # import requests
    # try:
    #     resp = requests.get(source["url"], timeout=15,
    #                         headers={"User-Agent": "ENEA-Monitor/1.0"})
    #     resp.raise_for_status()
    # except Exception as e:
    #     print(f"[ERR] {source['id']}: {e}")
    #     return []
    #
    # if source["type"] == "rss":
    #     import feedparser
    #     feed = feedparser.parse(resp.content)
    #     return [_event_from_rss(entry, source) for entry in feed.entries]
    #
    # if source["parser"]:
    #     parser_fn = globals()[source["parser"]]
    #     return parser_fn(resp.text)
    #
    # return parse_generic_html(resp.text, source)
    return []


def scrape_all(sources: list[dict], week_start: datetime,
               cache: EventCache, use_mock: bool = True) -> list[Event]:
    """
    Raccoglie eventi da tutte le fonti e applica deduplica + flag NEW.
    """
    all_events = []
    seen_hashes = set()

    for source in sources:
        events = scrape_source(source, week_start, use_mock=use_mock)
        for evt in events:
            h = evt.hash_id()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            evt.is_new = cache.is_new(evt)
            cache.mark_seen(evt)
            all_events.append(evt)

    # Ordina per data
    all_events.sort(key=lambda e: (e.date, e.time or "99:99"))
    return all_events
