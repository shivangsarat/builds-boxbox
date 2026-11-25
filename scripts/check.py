from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]/'dist'
class Scan(HTMLParser):
    def __init__(self): super().__init__(); self.links=[];self.ids=set();self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: assert a['id'] not in self.ids;self.ids.add(a['id'])
        if tag in ('a','link') and 'href' in a:self.links.append(a['href'])
        if tag in ('img','script') and 'src' in a:self.links.append(a['src'])
        if tag=='img':assert a.get('alt')
scans={}
for f in ROOT.rglob('*.html'):
    s=Scan();s.feed(f.read_text());scans[f.resolve()]=s
for f,s in scans.items():
    for link in s.links:
        u=urlsplit(link)
        if u.scheme or u.netloc:continue
        target=(f.parent/unquote(u.path)).resolve() if u.path else f
        if target.is_dir():target=target/'index.html'
        assert ROOT.resolve() in target.parents and target.exists(),(f,link)
        if u.fragment:assert u.fragment in scans[target].ids,(f,link)
for name in ['feed.xml','sitemap.xml']:ET.parse(ROOT/name)
print(f'Checked {len(scans)} HTML pages: local links, anchors, image alt text and XML passed')
