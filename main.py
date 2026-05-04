"""
Script principale del flusso di monitoraggio settimanale ENEA.

Uso:
    python main.py                  # settimana corrente, dati mock
    python main.py --week 2026-04-27   # settimana che inizia il 27 apr
    python main.py --live           # scraping reale (invece di mock)

Output:
    output/ENEA_settimana_YYYY-MM-DD.pdf
    output/events_YYYY-MM-DD.json  (archivio strutturato)
"""

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from sources import get_all_sources
from scraper import scrape_all, EventCache, Event
from classifier import classify_all
from pdf_generator import generate_weekly_report


def get_monday(date: datetime) -> datetime:
    """Ritorna il lunedì della settimana di 'date'."""
    return date - timedelta(days=date.weekday())


def separate_current_and_upcoming(events: list[Event],
                                   week_start: datetime) -> tuple[list[Event], list[Event]]:
    """
    Divide gli eventi in:
    - current: dentro la settimana (lun-dom)
    - upcoming: dalla settimana successiva in poi
    """
    week_end = week_start + timedelta(days=6)
    current, upcoming = [], []
    for evt in events:
        d = datetime.strptime(evt.date, "%Y-%m-%d")
        if week_start.date() <= d.date() <= week_end.date():
            current.append(evt)
        elif d.date() > week_end.date():
            upcoming.append(evt)
    return current, upcoming


def save_json_archive(events: list[Event], output_path: str):
    """Archivio JSON di tutti gli eventi per analisi successive."""
    data = [asdict(e) for e in events]
    Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="ENEA weekly event monitor")
    parser.add_argument("--week", type=str, default=None,
                        help="Data di inizio settimana in ISO (default: lunedì corrente)")
    parser.add_argument("--live", action="store_true",
                        help="Usa scraping reale invece dei dati mock")
    parser.add_argument("--output-dir", type=str, default="output")
    args = parser.parse_args()

    # Determina settimana di riferimento
    if args.week:
        week_start = datetime.strptime(args.week, "%Y-%m-%d")
    else:
        week_start = get_monday(datetime.now())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"[INFO] Monitoraggio settimana {week_start.strftime('%Y-%m-%d')}")
    print(f"[INFO] Modalità: {'LIVE scraping' if args.live else 'MOCK demo data'}")

    # --- Pipeline ---
    cache = EventCache(db_path=str(output_dir / "events_cache.db"))
    sources = get_all_sources()
    print(f"[INFO] Fonti caricate: {len(sources)}")

    print("[STEP 1/3] Raccolta eventi...")
    all_events = scrape_all(sources, week_start, cache, use_mock=not args.live)
    print(f"  -> {len(all_events)} eventi raccolti")

    print("[STEP 2/3] Classificazione A/B/C...")
    all_events = classify_all(all_events)
    by_tier = {"A": 0, "B": 0, "C": 0}
    for e in all_events:
        by_tier[e.priority] = by_tier.get(e.priority, 0) + 1
    print(f"  -> A: {by_tier['A']}  |  B: {by_tier['B']}  |  C: {by_tier['C']}")

    print("[STEP 3/3] Generazione report...")
    current, upcoming = separate_current_and_upcoming(all_events, week_start)
    pdf_path = output_dir / f"ENEA_settimana_{week_start.strftime('%Y-%m-%d')}.pdf"
    json_path = output_dir / f"events_{week_start.strftime('%Y-%m-%d')}.json"

    generate_weekly_report(current, upcoming, week_start, str(pdf_path))
    save_json_archive(all_events, str(json_path))

    print(f"[DONE] PDF: {pdf_path}")
    print(f"[DONE] JSON: {json_path}")


if __name__ == "__main__":
    main()
