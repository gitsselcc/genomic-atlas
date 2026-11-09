"""Discover candidate pages from explicitly registered sources."""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from connectors import canonicalize_url, fetch_url, keyword_match, parse_feed, parse_html_document, parse_sitemap_document, robots_allowed, sha256_text

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def load_registry(path):
    try: raw=json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: raise ValueError("El registro debe ser JSON válido (también compatible con YAML)") from exc
    if not isinstance(raw,list): raise ValueError("El registro debe ser una lista")
    seen=set()
    for i,s in enumerate(raw):
        p=f"sources[{i}]"
        if not isinstance(s,dict): raise ValueError(f"{p}: debe ser objeto")
        for k in ("source_id","name","url","source_type"):
            if not isinstance(s.get(k),str) or not s[k].strip(): raise ValueError(f"{p}.{k}: obligatorio")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",s["source_id"]): raise ValueError(f"{p}.source_id inválido")
        if s["source_id"] in seen: raise ValueError(f"{p}.source_id duplicado")
        seen.add(s["source_id"])
        if s["source_type"] not in {"rss","sitemap","webpage"}: raise ValueError(f"{p}.source_type no admitido")
        canonicalize_url(s["url"])
        if not isinstance(s.get("active",True),bool): raise ValueError(f"{p}.active debe ser booleano")
        if not isinstance(s.get("areas",["all"]),list) or not isinstance(s.get("keywords",[]),list): raise ValueError(f"{p}: areas y keywords deben ser listas")
    return raw

def _fetch(url,source,robots):
    allowed,reason=robots_allowed(url,robots,timeout=source.get("timeout",20))
    if not allowed: raise PermissionError(reason)
    response=fetch_url(url,timeout=source.get("timeout",20),headers=source.get("headers",{}),max_bytes=source.get("max_response_bytes",3000000))
    if not 200 <= response.status < 300: raise RuntimeError(f"HTTP {response.status}: {url}")
    return response.content,response.headers

def collect_source(source,robots):
    content,headers=_fetch(source["url"],source,robots)
    kind=source["source_type"]
    if kind=="rss": items=parse_feed(content,source["url"])
    elif kind=="sitemap":
        parsed=parse_sitemap_document(content); pages=parsed["urls"]
        for child in parsed["sitemaps"][:source.get("max_child_sitemaps",10)]:
            child_bytes,_=_fetch(child["url"],source,robots)
            pages.extend(parse_sitemap_document(child_bytes)["urls"])
        items=[{"url":p["url"],"title":p["url"],"summary":"","lastmod":p.get("lastmod")} for p in pages[:source.get("max_pages",300)]]
    else:
        page=parse_html_document(content,headers); base=page["canonical"] or source["url"]; items=[]
        for link in page["links"]:
            href=link.get("href","")
            if not href or href.startswith(("#","mailto:","tel:","javascript:")): continue
            url=canonicalize_url(href,base)
            if urlsplit(url).hostname != urlsplit(source["url"]).hostname and not source.get("allow_external_links",False): continue
            items.append({"url":url,"title":link.get("text") or url,"summary":page["description"]})
        if not items: items=[{"url":base,"title":page["title"] or source["name"],"summary":page["description"]}]
    result=[]; now=utc_now()
    for item in items:
        text=" ".join((item.get("title",""),item.get("summary",""),item.get("url","")))
        if not keyword_match(text,source.get("keywords",[])): continue
        url=canonicalize_url(item["url"],source["url"]); title=(item.get("title") or url).strip(); summary=(item.get("summary") or "").strip()
        result.append({"candidate_id":sha256_text(url)[:20],"source_id":source["source_id"],"source_name":source["name"],"source_url":source["url"],"title":title[:300],"url":url,"summary":summary[:700],"published_at":item.get("published_at"),"source_lastmod":item.get("lastmod") or None,"detected_at":now,"content_hash":sha256_text(title+"\n"+summary),"areas":source.get("areas",["all"]),"status":"pending_review"})
    return result

def merge_candidates(path,incoming):
    path.parent.mkdir(parents=True,exist_ok=True); known={}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row=json.loads(line); known[row["url"]]=row.get("content_hash","")
            except (ValueError,KeyError): continue
    added=changed=0
    with path.open("a",encoding="utf-8") as handle:
        for row in incoming:
            previous=known.get(row["url"])
            if previous==row["content_hash"]: continue
            if previous is None: added+=1
            else: changed+=1; row["change_detected"]=True
            handle.write(json.dumps(row,ensure_ascii=False)+"\n"); known[row["url"]]=row["content_hash"]
    return added,changed

def main():
    parser=argparse.ArgumentParser(description="Genomic Atlas source discovery")
    parser.add_argument("--registry",default="research/sources/registry.json")
    parser.add_argument("--output",default="research/discovery/candidates.jsonl")
    args=parser.parse_args()
    try: sources=load_registry(ROOT/args.registry)
    except (OSError,ValueError) as exc: print(f"ERROR: {exc}",file=sys.stderr); return 1
    active=[s for s in sources if s.get("active",True)]; robots={}; found=[]; failures=0
    print(f"Fuentes registradas: {len(sources)} | activas: {len(active)}")
    for source in active:
        try:
            candidates=collect_source(source,robots); found.extend(candidates)
            print(f"OK  {source['source_id']}: {len(candidates)} candidatos")
        except Exception as exc:
            failures+=1; print(f"WARN {source['source_id']}: {exc}",file=sys.stderr)
    unique={}
    for row in found: unique.setdefault(row["url"],row)
    output=ROOT/args.output; added,changed=merge_candidates(output,list(unique.values()))
    print(f"Resultado: {len(unique)} únicos | {added} nuevos | {changed} cambios | {failures} fuentes con error")
    print(f"Salida: {args.output}")
    return 1 if failures else 0

if __name__=="__main__": raise SystemExit(main())
