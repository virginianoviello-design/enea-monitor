"""
Generatore PDF in stile ENEA.

Produce due pagine principali:
1. Impegni e convegni istituzionali (SM / GM / GP)
2. Eventi e convegni di interesse, raggruppati per fascia A/B/C

Il PDF è in formato orizzontale (landscape), con griglia a 7 colonne
(lunedì-domenica) che rispecchia il layout dei file ENEA forniti.
"""

from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from scraper import Event


# --- Palette ispirata ai PDF ENEA ---
COLOR_HEADER_BLUE = HexColor("#1E3A8A")      # blu scuro intestazione
COLOR_DAY_HEADER = HexColor("#1E3A8A")
COLOR_CARD_BG = HexColor("#F3F4F6")          # grigio chiaro sfondo card
COLOR_CARD_ACCENT = HexColor("#3B82F6")      # barra laterale blu
COLOR_NEW_RED = HexColor("#DC2626")          # rosso per flag NEW
COLOR_TEXT_PRIMARY = HexColor("#1F2937")
COLOR_TEXT_SECONDARY = HexColor("#6B7280")
COLOR_A = HexColor("#D1FAE5")   # verde chiaro (partecipazione raccomandata)
COLOR_B = HexColor("#FEF3C7")   # giallo chiaro (presidio opportuno)
COLOR_C = HexColor("#EDE9FE")   # viola chiaro (monitoraggio)


DAYS_IT = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Word-wrap semplice che spezza su spazi senza tagliare parole."""
    words = text.split()
    lines, current = [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = f"{current} {w}".strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _draw_event_card(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                     event: Event, show_new: bool = True):
    """Disegna una singola card evento dentro una cella del calendario."""
    # sfondo card
    c.setFillColor(COLOR_CARD_BG)
    c.setStrokeColor(COLOR_CARD_BG)
    c.rect(x, y - h, w, h, fill=1, stroke=0)

    # barra laterale blu
    c.setFillColor(COLOR_CARD_ACCENT)
    c.rect(x, y - h, 0.08 * cm, h, fill=1, stroke=0)

    # padding interno
    pad = 0.15 * cm
    text_x = x + pad + 0.1 * cm
    text_y = y - pad - 0.3 * cm

    # flag NEW
    if show_new and event.is_new:
        c.setFillColor(COLOR_NEW_RED)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(text_x, text_y, "NEW")
        title_offset_x = text_x + 0.7 * cm
        c.setFillColor(COLOR_TEXT_PRIMARY)
        c.setFont("Helvetica-Bold", 6)
        for line in _wrap_text(event.title, 32)[:2]:
            c.drawString(title_offset_x, text_y, line)
            text_y -= 0.25 * cm
            title_offset_x = text_x  # dalla seconda riga torna a sinistra
    else:
        c.setFillColor(COLOR_TEXT_PRIMARY)
        c.setFont("Helvetica-Bold", 6)
        for line in _wrap_text(event.title, 38)[:2]:
            c.drawString(text_x, text_y, line)
            text_y -= 0.25 * cm

    # organizzatore/luogo + ora
    c.setFillColor(COLOR_TEXT_SECONDARY)
    c.setFont("Helvetica", 5.5)
    detail = event.location
    if event.time:
        detail = f"{event.location}, ore {event.time}"
    for line in _wrap_text(detail, 42)[:2]:
        c.drawString(text_x, text_y, line)
        text_y -= 0.22 * cm


def _draw_calendar_header(c: canvas.Canvas, title: str, week_start: datetime,
                          page_w: float, page_h: float):
    """Disegna intestazione: titolo + logo zona + 7 colonne giorni."""
    # striscia blu superiore
    header_h = 1.4 * cm
    c.setFillColor(COLOR_HEADER_BLUE)
    c.rect(0, page_h - header_h, page_w, header_h, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * cm, page_h - 0.9 * cm, title)
    c.setFont("Helvetica", 10)
    week_end = week_start + timedelta(days=6)
    range_str = f"{week_start.day} – {week_end.day} {_month_it(week_start.month)}"
    c.drawString(1 * cm, page_h - 1.25 * cm, range_str)

    # sigla "ENEA-like" a destra
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(page_w - 1 * cm, page_h - 1.0 * cm, "ENEA Monitor")

    # riga giorni (secondo header)
    day_h = 1.1 * cm
    day_y = page_h - header_h - day_h
    c.setFillColor(COLOR_DAY_HEADER)
    c.rect(0, day_y, page_w, day_h, fill=1, stroke=0)

    col_x_start = 3.5 * cm   # spazio a sinistra per etichetta riga
    col_w = (page_w - col_x_start - 0.5 * cm) / 7

    c.setFillColor(white)
    for i, day_abbr in enumerate(DAYS_IT):
        date = week_start + timedelta(days=i)
        cx = col_x_start + i * col_w + col_w / 2
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(cx, day_y + 0.7 * cm, day_abbr)
        c.setFont("Helvetica", 11)
        c.drawCentredString(cx, day_y + 0.25 * cm, str(date.day))

    return col_x_start, col_w, day_y


def _month_it(m: int) -> str:
    return ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"][m - 1]


def _draw_row_label(c: canvas.Canvas, x: float, y: float, h: float,
                    initials: str, name: str, role: str):
    """Disegna l'etichetta a sinistra (SM, GM, GP...) con nome e ruolo."""
    # cerchio con iniziali
    cx = x + 1.2 * cm
    cy = y - h / 2
    c.setFillColor(COLOR_CARD_ACCENT)
    c.circle(cx, cy + 0.3 * cm, 0.7 * cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, cy + 0.15 * cm, initials)

    c.setFillColor(COLOR_TEXT_PRIMARY)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(cx, cy - 0.6 * cm, name)
    c.setFont("Helvetica", 6)
    for i, line in enumerate(_wrap_text(role, 22)):
        c.drawCentredString(cx, cy - 0.85 * cm - i * 0.22 * cm, line)


def generate_institutional_page(c: canvas.Canvas, events: list[Event],
                                week_start: datetime, page_w: float, page_h: float):
    """Pagina 1: impegni dei tre profili istituzionali (SM / GM / GP)."""
    col_x, col_w, cal_y_top = _draw_calendar_header(
        c, "Impegni e convegni istituzionali", week_start, page_w, page_h
    )

    rows = [
        ("SM", "Sergio Mattarella", "Presidente della Repubblica"),
        ("GM", "Giorgia Meloni", "Presidente del Consiglio dei Ministri"),
        ("GP", "Gilberto Picchetto Fratin", "Ministro Ambiente e Sicurezza Energetica"),
    ]

    row_h = (cal_y_top - 1 * cm) / len(rows)
    for i, (initials, name, role) in enumerate(rows):
        y_top = cal_y_top - i * row_h

        # sfondo alternato
        if i % 2 == 0:
            c.setFillColor(HexColor("#F9FAFB"))
            c.rect(0, y_top - row_h, page_w, row_h, fill=1, stroke=0)

        _draw_row_label(c, 0.2 * cm, y_top, row_h, initials, name, role)

        # eventi nella riga
        person_events = [e for e in events if e.person == initials]
        for evt in person_events:
            evt_date = datetime.strptime(evt.date, "%Y-%m-%d")
            day_idx = (evt_date - week_start).days
            if 0 <= day_idx <= 6:
                x = col_x + day_idx * col_w + 0.1 * cm
                y = y_top - 0.2 * cm
                _draw_event_card(c, x, y, col_w - 0.2 * cm,
                                 row_h * 0.45, evt, show_new=False)

    c.showPage()


def generate_interest_page(c: canvas.Canvas, events: list[Event],
                           week_start: datetime, page_w: float, page_h: float):
    """Pagina 2: eventi di interesse, raggruppati per priorità A/B/C."""
    col_x, col_w, cal_y_top = _draw_calendar_header(
        c, "Eventi e convegni di interesse", week_start, page_w, page_h
    )

    tiers = [
        ("A", "Partecipazione istituzionale raccomandata", COLOR_A),
        ("B", "Presidio ENEA opportuno", COLOR_B),
        ("C", "Monitoraggio", COLOR_C),
    ]

    row_h = (cal_y_top - 1 * cm) / len(tiers)
    for i, (letter, label, color) in enumerate(tiers):
        y_top = cal_y_top - i * row_h

        # sfondo tier
        c.setFillColor(color)
        c.rect(0, y_top - row_h, 3.3 * cm, row_h, fill=1, stroke=0)

        # etichetta tier
        c.setFillColor(COLOR_TEXT_PRIMARY)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.4 * cm, y_top - 0.6 * cm, letter)
        c.setFont("Helvetica", 6)
        for k, line in enumerate(_wrap_text(label, 24)):
            c.drawString(0.4 * cm, y_top - 1 * cm - k * 0.22 * cm, line)

        # eventi del tier
        tier_events = [e for e in events if e.priority == letter and not e.person]

        # affianca max 2 card per giorno
        slots_per_day = 2
        slot_h = (row_h - 0.4 * cm) / slots_per_day
        slot_counts = [0] * 7

        for evt in tier_events:
            evt_date = datetime.strptime(evt.date, "%Y-%m-%d")
            day_idx = (evt_date - week_start).days
            if not (0 <= day_idx <= 6):
                continue
            slot = slot_counts[day_idx]
            if slot >= slots_per_day:
                continue
            slot_counts[day_idx] += 1

            x = col_x + day_idx * col_w + 0.1 * cm
            y = y_top - 0.2 * cm - slot * slot_h
            _draw_event_card(c, x, y, col_w - 0.2 * cm,
                             slot_h - 0.1 * cm, evt)

    c.showPage()


def generate_upcoming_page(c: canvas.Canvas, upcoming: list[Event],
                           page_w: float, page_h: float):
    """Pagina 3: appuntamenti settimane successive (lista semplice)."""
    # header
    header_h = 1.4 * cm
    c.setFillColor(COLOR_HEADER_BLUE)
    c.rect(0, page_h - header_h, page_w, header_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * cm, page_h - 0.9 * cm, "Appuntamenti settimane successive")

    # lista
    c.setFillColor(COLOR_TEXT_PRIMARY)
    y = page_h - header_h - 1 * cm
    for evt in upcoming:
        if y < 1.5 * cm:
            c.showPage()
            y = page_h - 1 * cm

        prefix = "NEW " if evt.is_new else ""
        c.setFont("Helvetica-Bold", 8)
        date_str = datetime.strptime(evt.date, "%Y-%m-%d").strftime("%d %B")
        c.drawString(1 * cm, y, f"{prefix}{date_str} — {evt.title}")
        c.setFont("Helvetica", 7)
        c.setFillColor(COLOR_TEXT_SECONDARY)
        c.drawString(1 * cm, y - 0.3 * cm, f"{evt.location} — {evt.organizer}")
        c.setFillColor(COLOR_TEXT_PRIMARY)
        y -= 0.7 * cm

    # legenda in fondo
    _draw_legend(c, page_w)
    c.showPage()


def _draw_legend(c: canvas.Canvas, page_w: float):
    """Legenda A/B/C in fondo alla pagina."""
    y = 1 * cm
    items = [
        ("A — Partecipazione istituzionale raccomandata", COLOR_A),
        ("B — Presidio ENEA opportuno", COLOR_B),
        ("C — Monitoraggio", COLOR_C),
    ]
    box_w = (page_w - 2 * cm) / 3
    for i, (label, color) in enumerate(items):
        x = 1 * cm + i * box_w
        c.setFillColor(color)
        c.rect(x, y, box_w - 0.3 * cm, 0.5 * cm, fill=1, stroke=0)
        c.setFillColor(COLOR_TEXT_PRIMARY)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.2 * cm, y + 0.17 * cm, label)


def generate_weekly_report(events: list[Event], upcoming: list[Event],
                           week_start: datetime, output_path: str):
    """Funzione principale: genera il PDF settimanale completo."""
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    generate_institutional_page(c, events, week_start, page_w, page_h)
    generate_interest_page(c, events, week_start, page_w, page_h)
    generate_upcoming_page(c, upcoming, page_w, page_h)

    c.save()
    return output_path
