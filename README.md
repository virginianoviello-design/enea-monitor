# ENEA Event Monitor — V2

Monitoraggio automatico di eventi italiani sulle aree core ENEA (energia
rinnovabile, nucleare, efficienza, economia circolare, sostenibilità).

A differenza della V1, **questa versione fa ricerca web reale** tramite
l'API Anthropic con il tool `web_search` integrato. Non richiede scraper
specifici per ogni sito — Claude trova le informazioni ovunque siano
pubblicate.

## Output

Un file Markdown con la lista di tutti gli eventi futuri trovati,
raggruppati per area tematica. Ogni evento ha:

- Titolo (cliccabile, link diretto alla pagina)
- Data
- Luogo
- Organizzatore

Esempio:

```markdown
## Energia rinnovabile e transizione

- **[Solar Construction 2026](https://italiasolare.eu/...)**
  📅 28 maggio 2026 · 📍 Bari · 🏛 Italia Solare
```

## Uso locale

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-api03-...
python main.py
```

Output in `output/events_YYYY-MM-DD.md` e `.json`.

## Uso automatico (GitHub Actions)

Il workflow `monitor-settimanale.yml` gira ogni lunedì alle 7:00 ora
italiana e:

1. Esegue `main.py`
2. Salva il Markdown come artifact scaricabile (90 giorni di retention)
3. Pubblica il report come "Job Summary" — visibile direttamente sulla
   pagina dell'esecuzione GitHub, senza scaricare niente

Per attivarlo serve un **secret** `ANTHROPIC_API_KEY` configurato nelle
impostazioni del repository.

## Costi

L'API Anthropic costa per uso. Stima per esecuzione settimanale:

- 5 aree × ~3 ricerche web × ~1.500 token = ~25.000 token totali
- Modello Sonnet 4.5: ~0,30 € per esecuzione
- Mensile (4 esecuzioni): **~1,20 €**

Si possono ridurre i costi:

- Diminuendo `WEB_SEARCH_MAX_USES` da 3 a 2 in `main.py`
- Riducendo il numero di aree in `AREAS`
- Eseguendo ogni 2 settimane invece che ogni settimana

## Personalizzazione

Tutti i parametri principali sono in cima a `main.py`:

- `AREAS` — aree tematiche da cercare
- `MODEL` — modello Claude da usare
- `WEB_SEARCH_MAX_USES` — quante ricerche per area

## Differenze V2 vs V1

| Aspetto | V1 | V2 |
|---------|----|----|
| Eventi | Mock finti | Veri, dal web |
| Codice | 7 file, ~600 righe | 1 file, ~200 righe |
| Output | PDF impaginato | Markdown con link |
| Manutenzione | Scraper da fixare | Niente da manutenere |
| Costo | 0 | ~1,20 €/mese |
