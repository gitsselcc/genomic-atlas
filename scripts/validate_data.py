"""Validate public Genomic Atlas JSON and cross-file references."""
from __future__ import annotations
import json,re,sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]/'src/data'
NAMES=('areas','institutions','laboratories','opportunities','calls','funding')
TYPES={'summer','research_stay','research_year','congress','seminar','workshop','course','fellowship','mobility'}
LEVELS={'undergraduate','master','phd'}
def load_data(): return {n:json.loads((ROOT/f'{n}.json').read_text(encoding='utf-8')) for n in NAMES}
def valid_date(v):
    try: return isinstance(v,str) and date.fromisoformat(v).isoformat()==v
    except ValueError: return False
def valid_url(v):
    if not isinstance(v,str): return False
    p=urlparse(v)
    return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password

def validate(data):
    errors=[]; ids={}
    def err(path,msg): errors.append(f'{path}: {msg}')
    def text(row,key,path):
        if not isinstance(row.get(key),str) or not row[key].strip(): err(path+'.'+key,'texto obligatorio')
    def url(row,key,path):
        if not valid_url(row.get(key)): err(path+'.'+key,'URL HTTPS obligatoria')
    def refs(row,key,collection,path):
        val=row.get(key)
        if not isinstance(val,list) or not val or not all(isinstance(x,str) for x in val):
            err(path+'.'+key,'lista de identificadores obligatoria');return
        if len(val)!=len(set(val)):err(path+'.'+key,'duplicados')
        for ref in val:
            if ref not in ids[collection]:err(path+'.'+key,f'referencia desconocida: {ref}')
    for name in NAMES:
        rows=data.get(name)
        if not isinstance(rows,list):err(name,'debe ser lista');ids[name]=set();continue
        ids[name]=set()
        for j,row in enumerate(rows):
            p=f'{name}[{j}]'
            if not isinstance(row,dict):err(p,'debe ser objeto');continue
            ident=row.get('id')
            if not isinstance(ident,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',ident):err(p+'.id','id inválido')
            elif ident in ids[name]:err(p+'.id','duplicado')
            else:ids[name].add(ident)
    for row in data['areas']:
        p=f"areas[{row.get('id','?')}]"
        for k in ('name','description'):text(row,k,p)
        if not isinstance(row.get('subareas'),list) or not row['subareas'] or not all(isinstance(x,str) and x.strip() for x in row['subareas']):err(p+'.subareas','lista no vacía requerida')
    for row in data['institutions']:
        p=f"institutions[{row.get('id','?')}]"
        for k in ('name','country'):text(row,k,p)
        url(row,'website',p)
    for name in ('laboratories','opportunities'):
        for row in data[name]:
            p=f"{name}[{row.get('id','?')}]"
            if row.get('institution_id') not in ids['institutions']:err(p+'.institution_id','institución inexistente')
            refs(row,'research_area_ids','areas',p)
            if name=='laboratories':text(row,'name',p);url(row,'website',p)
            else:
                for k in ('title','description'):text(row,k,p)
                url(row,'official_url',p)
                if row.get('type') not in TYPES:err(p+'.type','tipo no admitido')
                if row.get('verification_status') not in ('verified','pending','outdated'):err(p+'.verification_status','estado no admitido')
                level=row.get('level')
                if not isinstance(level,list) or not level or any(x not in LEVELS for x in level):err(p+'.level','niveles no admitidos')
                checked=row.get('last_verified')
                if checked is not None and not valid_date(checked):err(p+'.last_verified','fecha ISO inválida')
                if row.get('verification_status')=='verified' and not valid_date(checked):err(p+'.last_verified','necesario para publicar')
    for row in data['calls']:
        p=f"calls[{row.get('id','?')}]";text(row,'cycle',p);url(row,'source_url',p)
        if row.get('opportunity_id') not in ids['opportunities']:err(p+'.opportunity_id','oportunidad inexistente')
        for key in ('opens_at','closes_at','starts_at','ends_at'):
            if row.get(key) is not None and not valid_date(row[key]):err(p+'.'+key,'fecha ISO inválida')
        for first,last in (('opens_at','closes_at'),('starts_at','ends_at')):
            if valid_date(row.get(first)) and valid_date(row.get(last)) and row[first]>row[last]:err(p,'fechas invertidas')
    for row in data['funding']:
        p=f"funding[{row.get('id','?')}]";text(row,'details',p);url(row,'source_url',p)
        if row.get('opportunity_id') not in ids['opportunities']:err(p+'.opportunity_id','oportunidad inexistente')
        if row.get('type') not in ('full','partial','none','unknown'):err(p+'.type','tipo de cobertura desconocido')
    return errors

if __name__=='__main__':
    try: problems=validate(load_data())
    except (OSError,ValueError) as exc:print(f'ERROR: {exc}',file=sys.stderr);raise SystemExit(1)
    if problems:
        print('\n'.join('ERROR: '+e for e in problems),file=sys.stderr);raise SystemExit(1)
    print('OK: catálogos JSON válidos y referencias consistentes')
