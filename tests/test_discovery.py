import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/discovery"))
from connectors import canonicalize_url,parse_feed,parse_html_document,parse_sitemap_document
from discover import load_registry,merge_candidates
class DiscoveryTests(unittest.TestCase):
 def fixture(self,name): return (ROOT/"tests"/"fixtures"/name).read_bytes()
 def test_url_normalization(self):
  self.assertEqual(canonicalize_url("HTTPS://Example.org/a?utm_source=x&b=2#top"),"https://example.org/a?b=2")
 def test_rss(self):
  rows=parse_feed(self.fixture("sample_feed.xml"),"https://example.org/feed")
  self.assertEqual(rows[0]["title"],"Summer research programme")
  self.assertEqual(rows[0]["url"],"https://example.org/call")
  self.assertTrue(rows[0]["published_at"].startswith("2026-11-09"))
 def test_sitemap(self):
  rows=parse_sitemap_document(self.fixture("sample_sitemap.xml"))["urls"]
  self.assertEqual(rows[0]["lastmod"],"2026-11-08")
 def test_html(self):
  page=parse_html_document(self.fixture("sample_page.html"),{"Content-Type":"text/html; charset=utf-8"})
  self.assertEqual(page["canonical"],"https://example.org/opportunities")
  self.assertEqual(len(page["links"]),2)
 def test_registry(self):
  self.assertGreaterEqual(len(load_registry(ROOT/"research/sources/registry.json")),4)
 def test_merge(self):
  row={"url":"https://example.org/p","content_hash":"a","candidate_id":"x","status":"pending_review"}
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"candidates.jsonl"
   self.assertEqual(merge_candidates(p,[row]),(1,0))
   self.assertEqual(merge_candidates(p,[row]),(0,0))
   self.assertEqual(merge_candidates(p,[dict(row,content_hash="b")]),(0,1))
   self.assertEqual(len(p.read_text().splitlines()),2)
if __name__=="__main__": unittest.main()
