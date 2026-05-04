# ENEA Event Monitor

Flusso automatico di monitoraggio settimanale di eventi e convegni rilevanti per
il core business ENEA: energia rinnovabile e transizione, nucleare, efficienza
energetica, economia circolare, sostenibilità ed ESG.

Produce in output un PDF settimanale nello stile dei report istituzionali ENEA,
con classificazione A/B/C di ogni evento.

---

## Struttura del progetto

```
enea_monitor/
├── sources.py          # catalogo delle 25 fonti da monitorare
├── scraper.py          # raccolta eventi + cache deduplica
├── classifier.py       # classificatore A/B/C (regole + keyword)
├── pdf_generator.py    # generatore PDF in stile ENEA
├── main.py             # orchestratore del flusso
└── output/             # PDF e JSON generati
```

---

## Avvio rapido (modalità demo)

```bash
pip install reportlab requests beautifulsoup4 feedparser
python main.py --week 2026-04-27
```

Output:
- `output/ENEA_settimana_2026-04-27.pdf` — report settimanale
- `output/events_2026-04-27.json` — archivio dati strutturato
- `output/events_cache.db` — cache per tracciare eventi già visti

---

## Attivare lo scraping reale

Il codice attuale usa **dati mock** per dimostrare il flusso. Per attivare lo
scraping reale:

1. Implementare i parser specifici in `scraper.py`:
   - `parse_quirinale` — agenda del Presidente della Repubblica
   - `parse_governo` — agenda del Presidente del Consiglio
   - `parse_mase` — eventi del Ministero dell'Ambiente

2. Eseguire con `--live`:
   ```bash
   python main.py --live
   ```

3. Per le fonti con RSS, `scrape_source` userà automaticamente `feedparser`.

---

## Come si classifica un evento (A / B / C)

Il classificatore combina 7 segnali per ogni evento:

| Segnale | Peso |
|---------|------|
| Presenza di ministro/presidente nel titolo | +3 per keyword |
| Presenza nel testo di keyword tematiche ENEA | +2 per keyword |
| Partecipazione istituzionale esplicita (SM/GM/GP) | +5 |
| Organizzatore "high-priority" (ASviS, WEC, TEHA...) | +3 |
| Sede istituzionale (Quirinale, Senato...) | +4 |
| Evento online invece che in presenza | −1 |

Soglie finali:
- score_A ≥ 5 → **A** (partecipazione istituzionale raccomandata)
- score_A ≥ 3 o score_B ≥ 4 → **B** (presidio ENEA opportuno)
- altrimenti → **C** (monitoraggio)

### Fallback con Claude API (opzionale)

Per gli eventi borderline (punteggi simili tra A e B), è disponibile
`classify_with_llm` in `classifier.py`. Richiede:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Fonti monitorate (25)

### Istituzionali (4)
- Quirinale · Governo · MASE · ARERA · GSE

### Energia e rinnovabili (7)
- Italia Solare · Elettricità Futura · ANEV · Coordinamento FREE
- AIEE · WEC Italia · FIPER

### Efficienza energetica (3)
- FIRE · Kyoto Club · Motus-E

### Nucleare (2)
- SOGIN · AIN (Associazione Italiana Nucleare)

### Economia circolare (3)
- Comieco · Fondazione Sviluppo Sostenibile · Utilitalia

### Sostenibilità (2)
- ASviS · Legambiente

### Media e think tank (3)
- Il Sole 24 Ore · Staffetta Quotidiana · TEHA

---

## Automazione settimanale

Per far girare il flusso ogni lunedì alle 7:00 (cron):

```bash
0 7 * * 1 cd /path/to/enea_monitor && /usr/bin/python3 main.py --live >> logs/run.log 2>&1
```

In alternativa con GitHub Actions (`.github/workflows/weekly.yml`):

```yaml
on:
  schedule:
    - cron: '0 7 * * 1'   # lunedì 07:00 UTC
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python main.py --live
      - uses: actions/upload-artifact@v4
        with: { name: report, path: output/ }
```

---

## Roadmap suggerita

### Fase 1 — MVP (implementato qui)
- [x] Architettura modulare
- [x] Catalogo fonti
- [x] Mock data + PDF generation
- [x] Classificatore deterministico

### Fase 2 — Scraping reale
- [ ] Implementare i 25 parser specifici
- [ ] Gestione robusta degli errori di rete
- [ ] Rotazione user-agent e rispetto `robots.txt`

### Fase 3 — Qualità
- [ ] Integrazione Claude API per casi borderline
- [ ] Notifica email / Slack quando compare evento classe A
- [ ] Dashboard web (Streamlit) per consultare l'archivio

### Fase 4 — Espansione
- [ ] Aggiungere LinkedIn Events e Eventbrite
- [ ] Monitorare Twitter/X account istituzionali
- [ ] Estrazione location da GPS per mappe
