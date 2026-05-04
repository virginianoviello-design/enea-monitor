"""
ENEA Event Monitor V2.1
Con monitoraggio eventi istituzionali (Presidenza Repubblica,
Presidenza Consiglio, Ministero Ambiente).
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic


AREAS = [
    {
        "name": "Presidente della Repubblica",
        "keywords": "Sergio Mattarella, Quirinale, Presidente della Repubblica, agenda Quirinale, cerimonia Quirinale, udienza Quirinale",
    },
    {
        "name": "Presidente del Consiglio",
        "keywords": "Giorgia Meloni, Palazzo Chigi, Presidente del Consiglio, agenda Palazzo Chigi, vertice intergovernativo, Consiglio dei Ministri",
    },
    {
        "name": "Ministro Ambiente e Sicurezza Energetica",
        "keywords": "Gilberto Picchetto Fratin, MASE, Ministro Ambiente, Ministero Ambiente Sicurezza Energetica, intervento Picchetto",
    },
    {
        "name": "Energia rinnovabile e transizione",
        "keywords": "energia rinnovabile, fotovoltaico, eolico, transizione energetica, comunita energetiche, storage",
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
        "name": "Sostenibilita e ESG",
        "keywords": "sostenibilita, ESG, rendicontazione sostenibilita, sviluppo sostenibile",
    },
]

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
WEB_SEARCH_MAX_USES = 2
PAUSE_BETWEEN_AREAS = 35


def build_search_prompt(area, today_iso):
    institutional = area['name'] in (
        "Presidente della Repubblica",
        "Presidente del Consiglio",
        "Ministro Ambiente e Sicurezza Energetica",
    )

    if institutional:
        focus_block = """Concentrati su impegni ufficiali, cerimonie, udienze, vertici,
visite, conferenze stampa, dichiarazioni, eventi pubblici a cui partecipa
direttamente la figura istituzionale.

Fonti privilegiate da consultare:
- Sito ufficiale del Quirinale (quirinale.it)
- Sito del Governo (governo.it)
- Sito del MASE (mase.gov.it)
- Agenzie stampa (ANSA, AGI, Adnkronos)"""
    else:
        focus_block = """Concentrati su eventi organizzati da:
- Italia Solare, Elettricita Futura, ANEV, FIRE, Kyoto Club, Motus-E,
  Coordinamento FREE, Comieco, Utilitalia, ASviS, Legambiente, WEC Italia,
  Fondazione per lo Sviluppo Sostenibile, MASE, ARERA, GSE,
  Il Sole 24 Ore, Staffetta Quotidiana, TEHA"""

    return f"""Sei un assistente che monitora eventi e convegni in Italia per ENEA.

Oggi e il {today_iso}.

Cerca sul web eventi italiani FUTURI (data uguale o successiva a oggi)
sull'area tematica:
"{area['name']}"

Parole chiave: {area['keywords']}

{focus_block}

Restituisci ESCLUSIVAMENTE un oggetto JSON puro,
niente testo prima o dopo, niente markdown, niente backtick:

{{
  "events": [
    {{
      "title": "Titolo evento",
      "date": "YYYY-MM-DD",
      "location": "Citta o Online",
      "organizer": "Chi organizza",
      "url": "Link diretto",
      "area": "{area['name']}"
    }}
  ]
}}

Regole:
- Solo eventi con link verificabile
- NON inventare eventi: se nulla, restituisci {{"events": []}}
- Massimo 10 eventi per area
"""


def search_events_for_area(client, area, today_iso):
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

    text_blocks = [b.text for b in response.content if b.type == "text"]
    full_text = "\n".join(text_blocks)

    json_match = re.search(r"\{[\s\S]*\}", full_text)
    if not json_match:
        print("     [warn] nessun JSON valido nella risposta", flush=True)
        return []

    try:
        data = json.loads(json_match.group(0))
        events = data.get("events", [])
        print(f"     {len(events)} eventi trovati", flush=True)
        return events
    except json.JSONDecodeError as e:
        print(f"     [warn] errore parsing JSON: {e}", flush=True)
        return []


def normalize_title(title):
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(events):
    seen = set()
    unique = []
    for ev in events:
        key = (normalize_title(ev.get("title", "")), ev.get("date", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    return unique


def sort_by_date(events):
    return sorted(events, key=lambda e: e.get("date") or "9999-99-99")


MONTHS_IT = {
    "01": "gennaio", "02": "febbraio", "03": "marzo", "04": "aprile",
    "05": "maggio", "06": "giugno", "07": "luglio", "08": "agosto",
    "09": "settembre", "10": "ottobre", "11": "novembre", "12": "dicembre",
}


def format_date_it(iso_date):
    try:
        y, m, d = iso_date.split("-")
        return f"{int(d)} {MONTHS_IT.get(m, m)} {y}"
    except Exception:
        return iso_date


# Ordine di apparizione delle aree nel report finale
AREA_ORDER = [
    "Presidente della Repubblica",
    "Presidente del Consiglio",
    "Ministro Ambiente e Sicurezza Energetica",
    "Energia rinnovabile e transizione",
    "Nucleare",
    "Efficienza energetica",
    "Economia circolare",
    "Sostenibilita e ESG",
]


def generate_markdown(events, today_iso):
    today_str = format_date_it(today_iso)
    lines = [
        "# ENEA Event Monitor",
        "",
        f"_Report generato il {today_str} - {len(events)} eventi futuri trovati_",
        "",
    ]

    if not events:
        lines.append("Nessun evento trovato in questa esecuzione.")
        return "\n".join(lines)

    by_area = {}
    for ev in events:
        area = ev.get("area", "Altro")
        by_area.setdefault(area, []).append(ev)

    # Stampa istituzionali per primi (sezione separata)
    institutional = [
        "Presidente della Repubblica",
        "Presidente del Consiglio",
        "Ministro Ambiente e Sicurezza Energetica",
    ]
    has_institutional = any(name in by_area for name in institutional)

    if has_institutional:
        lines.append("---")
        lines.append("")
        lines.append("# Impegni e convegni istituzionali")
        lines.append("")
        for name in institutional:
            if name not in by_area:
                continue
            lines.append(f"## {name}")
            lines.append("")
            for ev in by_area[name]:
                title = ev.get("title", "(senza titolo)")
                url = ev.get("url", "#")
                date_it = format_date_it(ev.get("date", ""))
                location = ev.get("location", "n.d.")
                organizer = ev.get("organizer", "n.d.")
                lines.append(f"- **[{title}]({url})**  ")
                lines.append(f"  Data: {date_it} | Luogo: {location} | Organizzatore: {organizer}")
                lines.append("")
            lines.append("")

    # Poi le aree tematiche
    other_areas = [a for a in AREA_ORDER if a not in institutional and a in by_area]
    if other_areas:
        lines.append("---")
        lines.append("")
        lines.append("# Eventi e convegni di interesse")
        lines.append("")
        for name in other_areas:
            lines.append(f"## {name}")
            lines.append("")
            for ev in by_area[name]:
                title = ev.get("title", "(senza titolo)")
                url = ev.get("url", "#")
                date_it = format_date_it(ev.get("date", ""))
                location = ev.get("location", "n.d.")
                organizer = ev.get("organizer", "n.d.")
                lines.append(f"- **[{title}]({url})**  ")
                lines.append(f"  Data: {date_it} | Luogo: {location} | Organizzatore: {organizer}")
                lines.append("")
            lines.append("")

    return "\n".join(lines)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERRORE] Manca la variabile ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    today = datetime.now()
    today_iso = today.strftime("%Y-%m-%d")
    print(f"[INFO] ENEA Event Monitor V2.1 - {today_iso}")
    print(f"[INFO] Modello: {MODEL}")
    print(f"[INFO] Aree tematiche: {len(AREAS)}")
    print(f"[INFO] Pausa tra aree: {PAUSE_BETWEEN_AREAS}s (per rispettare rate limit)")
    print()

    client = Anthropic(api_key=api_key)

    print("[STEP 1/3] Ricerca eventi per area...")
    all_events = []
    for i, area in enumerate(AREAS):
        if i > 0:
            print(f"  (pausa {PAUSE_BETWEEN_AREAS}s per rispettare rate limit...)", flush=True)
            time.sleep(PAUSE_BETWEEN_AREAS)
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
