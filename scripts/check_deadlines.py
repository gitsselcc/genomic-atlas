"""Print deadlines in the next 60 days; this is NOT a source verification."""
import json
from datetime import date
from pathlib import Path
FILE=Path(__file__).resolve().parents[1]/'src/data/calls.json'
today=date.today()
upcoming=[]
for call in json.loads(FILE.read_text(encoding='utf-8')):
    if call.get('closes_at'):
        days=(date.fromisoformat(call['closes_at'])-today).days
        if 0<=days<=60:upcoming.append((days,call))
for days,call in sorted(upcoming):print(f"{days} días: {call['id']} ({call['closes_at']}) {call['source_url']}")
if not upcoming:print('Ninguna fecha de cierre registrada en los próximos 60 días.')
