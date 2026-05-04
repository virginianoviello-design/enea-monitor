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
MAX_TOKEN
