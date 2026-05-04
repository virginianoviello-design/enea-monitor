"""
Classificatore A/B/C per eventi ENEA.

Logica (ispirata alla legenda dei PDF forniti):
- A (Partecipazione istituzionale raccomandata): eventi di alto rilievo politico
  o con presenza ministeriale/istituzionale, da presidiare a livello di vertice.
- B (Presidio ENEA opportuno): eventi importanti dove basta una presenza tecnica.
- C (Monitoraggio): eventi di interesse informativo/aggiornamento.

Strategia:
1. Regole deterministiche (keyword + organizzatore + luogo)
2. Punteggio pesato che combina più segnali
3. Opzionale: fallback su LLM (Claude API) per casi borderline
"""

from scraper import Event


# Keyword che alzano il peso verso A (presenza istituzionale/alto livello)
KEYWORDS_A = [
    "ministro", "ministero", "presidente della repubblica", "presidente del consiglio",
    "quirinale", "palazzo chigi", "senato", "camera dei deputati",
    "consiglio europeo", "commissione europea",
    "strategia nazionale", "piano nazionale", "pnrr",
    "mezzogiorno", "dopo il pnrr",
]

# Keyword che indicano un evento tecnico/settoriale rilevante (verso B)
KEYWORDS_B = [
    "transizione energetica", "sicurezza energetica", "storage", "accumuli",
    "comunità energetiche", "autoconsumo", "fotovoltaico", "eolico",
    "nucleare", "fusione", "smr",
    "efficienza energetica", "decarbonizzazione",
    "economia circolare", "riciclo", "rifiuti",
    "sostenibilità", "esg", "rendicontazione sostenibilità",
    "data center", "idrogeno",
]

# Organizzatori storicamente rilevanti (visti ricorrere nei PDF)
ORGANIZERS_HIGH_PRIORITY = {
    "asvis", "the european house ambrosetti", "teha",
    "wec italia", "motus-e", "elettricità futura",
    "fondazione per lo sviluppo sostenibile",
    "confindustria", "utilitalia",
    "il sole 24 ore", "sole 24 ore",
    "mase", "arera", "gse", "consob",
}

# Località/sedi che indicano alto rilievo
VENUES_HIGH_PRIORITY = {
    "quirinale", "palazzo chigi", "senato", "camera dei deputati",
    "palazzo montecitorio", "corte suprema di cassazione",
}


def classify(event: Event) -> str:
    """
    Ritorna "A", "B" o "C" basandosi su un punteggio composito.
    """
    title = event.title.lower()
    organizer = event.organizer.lower()
    location = event.location.lower()
    description = event.description.lower()
    full_text = f"{title} {description}"

    score_a = 0
    score_b = 0

    # --- Segnale 1: presenza di nome istituzionale nel testo ---
    for kw in KEYWORDS_A:
        if kw in full_text:
            score_a += 3

    # --- Segnale 2: keyword tematiche rilevanti per ENEA ---
    for kw in KEYWORDS_B:
        if kw in full_text:
            score_b += 2

    # --- Segnale 3: persona istituzionale presente (flag manuale dal scraper) ---
    if event.person:
        score_a += 5  # un impegno istituzionale è sempre da monitorare

    # --- Segnale 4: organizzatore di rilievo ---
    for org in ORGANIZERS_HIGH_PRIORITY:
        if org in organizer:
            score_b += 3
            break

    # --- Segnale 5: sede istituzionale ---
    for venue in VENUES_HIGH_PRIORITY:
        if venue in location:
            score_a += 4
            break

    # --- Segnale 6: evento online vs presenza fisica ---
    # gli eventi online sono tipicamente più informativi -> C
    if "online" in location:
        score_b -= 1

    # --- Segnale 7: priority_hint dalla fonte (se presente) ---
    # (Si può passare come parametro dal main, qui lasciato come esempio)

    # Decisione finale
    if score_a >= 5:
        return "A"
    if score_a >= 3 or score_b >= 4:
        return "B"
    return "C"


def classify_all(events: list[Event]) -> list[Event]:
    """Applica la classificazione a tutti gli eventi."""
    for evt in events:
        evt.priority = classify(evt)
    return events


# ============================================================
# OPZIONALE: classificazione con LLM (Claude API) per casi borderline
# ============================================================

def classify_with_llm(event: Event, api_key: str) -> str:
    """
    Fallback/ricontrollo con Claude API.
    Usare solo per eventi dove la regola dà punteggi simili A vs B.

    Richiede: pip install anthropic
    """
    # from anthropic import Anthropic
    # client = Anthropic(api_key=api_key)
    #
    # prompt = f"""Classifica questo evento per ENEA (Agenzia nazionale nuove
    # tecnologie, energia, sviluppo economico sostenibile) con una tra:
    # A = partecipazione a livello Presidenza/vertice raccomandata
    # B = presidio tecnico ENEA opportuno
    # C = solo monitoraggio informativo
    #
    # Evento: {event.title}
    # Organizzatore: {event.organizer}
    # Luogo: {event.location}
    # Descrizione: {event.description}
    #
    # Rispondi solo con una lettera: A, B o C."""
    #
    # resp = client.messages.create(
    #     model="claude-opus-4-7",
    #     max_tokens=10,
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # letter = resp.content[0].text.strip().upper()
    # return letter if letter in ("A", "B", "C") else "C"
    return "C"  # stub
