"""
ENEA Event Monitor — V2

Usa l'API Anthropic con il tool nativo `web_search` per trovare eventi
reali sul web, senza dover scrivere uno scraper per ogni singolo sito.

Output: lista Markdown con titolo, data, luogo, link, organizzatore.

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...
    python main.py
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic


# ============================================================
# CONFIGURAZIONE
# ============================================================

# Aree tematiche su cui Claude cercherà eventi.
# Ogni area diventerà una richiesta separata all'API per avere
# risultati più precisi e diversificati.
AREAS = [
    {
        "name": "Energia rinnovabile e transizione",
        "keywords": "energia rinnovabile, fotovoltaico, eolico, transizione energetica, comunità energetiche, storage",
    },
    {
        "name": "Nucleare",
        "keywords": "nucleare, fusione, SMR, energia nucleare",
    },
    {
        "name": "Efficienza energetica",
        "keywords": "efficienza energetica, energy manager, decarbonizzazione, riqualificazione energetica",
    },
    {
        "name": "Economia circolare",
        "keywords": "economia circolare, riciclo, rifiuti, recupero materiali, packaging sostenibile",
    },
    {
        "name": "Sostenibilità e ESG",
        "keywords": "sostenibilità, ESG, rendicontazione sostenibilità, sviluppo sostenibile",
    },
]

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
WEB_SEARCH_MAX_USES = 3  # max ricerche web per ciascuna area


# ============================================================
# PROMPT
# ============================================================

def build_search_prompt(area: dict, today_iso: str) -> str:
    """Crea il prompt per Claude per una singola area tematica."""
    return f"""Sei un assistente che monitora eventi e convegni in Italia per ENEA
(Agenzia nazionale per le nuove tecnologie, l'energia e lo sviluppo
economico sostenibile).

Oggi è il {today_iso}.

Cerca sul web TUTTI gli eventi, convegni, conferenze, webinar e presentazioni
italiani FUTURI (data uguale o successiva a oggi) sull'area tematica:
"{area['name']}"

Parole chiave correlate: {area['keywords']}

Concentrati su eventi organizzati da:
- Associazioni di settore (Italia Solare, Elettricità Futura, ANEV, FIRE,
  Kyoto Club, Motus-E, Coordinamento FREE, Comieco, Utilitalia, ASviS,
  Legambiente, WEC Italia, Fondazione per lo Sviluppo Sostenibile)
- Istituzioni (MASE, ARERA, GSE, Quirinale, Senato)
- Media specializzati (Il Sole 24 Ore, Staffetta Quotidiana)
- Università e think tank (TEHA / The European House Ambrosetti)

Fai PIÙ ricerche se servono per coprire bene l'area.

Per ogni evento trovato, restituisci ESCLUSIVAMENTE un oggetto JSON con
questa struttura ESATTA — niente testo prima o dopo, niente markdown,
niente backtick, solo JSON puro:

{{
  "events": [
    {{
      "title": "Titolo esatto dell'evento",
      "date": "YYYY-MM-DD",
      "location": "Città, oppure 'Online'",
      "organizer": "Chi organizza l'evento",
      "url": "Link diretto alla pagina dell'evento",
      "area": "{area['name']}"
    }}
  ]
}}

Regole importanti:
- Se non riesci a determinare la data esatta, usa il primo del mese stimato
- Se l'evento è su più giorni, usa la data di inizio
- Includi solo eventi con un link verificabile
- NON inventare eventi: se non trovi nulla, restituisci {{"events": []}}
- Massimo 15 eventi per area
"""


# ============================================================
# CHIAMATA API
# ============================================================

def search_events_for_area(client: Anthropic, area: dict, today_iso: str) -> list[dict]:
    """Chiama Claude con web_search per una singola area, parsa il JSON."""
    print(f"  -> Cerca: {area['name']}...", flush=True)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{
            "role": "user",
            "content": build_search_prompt(area, today_iso),
        }],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": WEB_SEARCH_MAX_USES,
        }],
    )

    # Estrai il testo finale dalla risposta (può contenere blocchi multipli)
    text_blocks = [b.text for b in response.content if b.type == "text"]
    full_text = "\n".join(text_blocks)

    # Estrai il JSON: cerchiamo il primo oggetto { ... } valido
    json_match = re.search(r"\{[\s\S]*\}", full_text)
    if not json_match:
        print(f"     [warn] nessun JSON valido nella risposta", flush=True)
        return []

    try:
        data = json.loads(json_match.group(0))
        events = data.get("events", [])
        print(f"     {len(events)} eventi trovati", flush=True)
        return events
    except json.JSONDecodeError as e:
        print(f"     [warn] errore parsing JSON: {e}", flush=True)
        return []


# ============================================================
# DEDUPLICA E ORDINAMENTO
# ============================================================

def normalize_title(title: str) -> str:
    """Per la deduplica: minuscolo, niente punteggiatura, spazi singoli."""
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(events: list[dict]) -> list[dict]:
    """Rimuove duplicati basandosi su titolo+data."""
    seen = set()
    unique = []
    for ev in events:
        key = (normalize_title(ev.get("title", "")), ev.get("date", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    return unique


def sort_by_date(events: list[dict]) -> list[dict]:
    """Ordina per data crescente, gli eventi senza data vanno in fondo."""
    return sorted(events, key=lambda e: e.get("date") or "9999-99-99")


# ============================================================
# OUTPUT MARKDOWN
# ============================================================

MONTHS_IT = {
    "01": "gennaio", "02": "febbraio", "03": "marzo", "04": "aprile",
    "05": "maggio", "06": "giugno", "07": "luglio", "08": "agosto",
    "09": "settembre", "10": "ottobre", "11": "novembre", "12": "dicembre",
}


def format_date_it(iso_date: str) -> str:
    """'2026-05-14' -> '14 maggio 2026'"""
    try:
        y, m, d = iso_date.split("-")
        return f"{int(d)} {MONTHS_IT.get(m, m)} {y}"
    except Exception:
        return iso_date


def generate_markdown(events: list[dict], today_iso: str) -> str:
    """Genera la lista Markdown raggruppata per area."""
    today_str = format_date_it(today_iso)
    lines = [
        f"# ENEA Event Monitor",
        f"",
        f"_Report generato il {today_str} — {len(events)} eventi futuri trovati_",
        f"",
    ]

    if not events:
        lines.append("Nessun evento trovato in questa esecuzione.")
        return "\n".join(lines)

    # Raggruppa per area
    by_area = {}
    for ev in events:
        area = ev.get("area", "Altro")
        by_area.setdefault(area, []).append(ev)

    for area_name in sorted(by_area.keys()):
        lines.append(f"## {area_name}")
        lines.append("")
        for ev in by_area[area_name]:
            title = ev.get("title", "(senza titolo)")
            url = ev.get("url", "#")
            date_it = format_date_it(ev.get("date", ""))
            location = ev.get("location", "n.d.")
            organizer = ev.get("organizer", "n.d.")
            lines.append(f"- **[{title}]({url})**  ")
            lines.append(f"  📅 {date_it} · 📍 {location} · 🏛 {organizer}")
            lines.append("")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERRORE] Manca la variabile ANTHROPIC_API_KEY", file=sys.stderr)
        print("         export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)

    today = datetime.now()
    today_iso = today.strftime("%Y-%m-%d")
    print(f"[INFO] ENEA Event Monitor — {today_iso}")
    print(f"[INFO] Modello: {MODEL}")
    print(f"[INFO] Aree tematiche: {len(AREAS)}")
    print()

    client = Anthropic(api_key=api_key)

    print("[STEP 1/3] Ricerca eventi per area...")
    all_events = []
    for area in AREAS:
        events = search_events_for_area(client, area, today_iso)
        all_events.extend(events)
    print(f"  Totale lordo: {len(all_events)} eventi")
    print()

    print("[STEP 2/3] Deduplica e ordinamento...")
    all_events = deduplicate(all_events)
    all_events = sort_by_date(all_events)
    print(f"  Totale netto: {len(all_events)} eventi")
    print()

    print("[STEP 3/3] Generazione output...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    md_path = output_dir / f"events_{today_iso}.md"
    json_path = output_dir / f"events_{today_iso}.json"

    md_content = generate_markdown(all_events, today_iso)
    md_path.write_text(md_content, encoding="utf-8")
    json_path.write_text(
        json.dumps(all_events, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")
    print()
    print("[DONE]")


if __name__ == "__main__":
    main()
