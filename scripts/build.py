#!/usr/bin/env python3
"""Build a public-safe static site. Only explicitly approved articles are emitted."""
import argparse, datetime as dt, html, json, math, re, shutil, xml.etree.ElementTree as ET
from pathlib import Path
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
ROOT=Path(__file__).resolve().parents[1]
BASE='https://shivangsarat.github.io/builds-boxbox/'
E=html.escape
def code_highlight(code, lang, attrs):
    try: lexer=get_lexer_by_name(lang) if lang else TextLexer()
    except ClassNotFound: lexer=TextLexer()
    return highlight(code,lexer,HtmlFormatter(nowrap=True))
MD=MarkdownIt('commonmark',{'html':False,'linkify':False,'typographer':False,'highlight':code_highlight})

def read_articles():
    data=json.loads((ROOT/'articles/index.json').read_text()); assert isinstance(data,list)
    seen=set(); ids=set()
    for a in data:
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',a['slug']) and a['slug'] not in seen
        assert re.fullmatch(r'[A-Z][A-Z0-9-]+',a['id']) and a['id'] not in ids
        seen.add(a['slug']);ids.add(a['id'])
        assert Path(a['source']).name==a['source'] and a['source'].endswith('.md')
        assert Path(a['image']).name==a['image'] and a['image'].endswith('.png')
        assert (ROOT/'assets'/a['image']).is_file()
        dt.date.fromisoformat(a['social_date'])
        a['markdown']=(ROOT/'articles'/a['source']).read_text()
        assert not re.search(r'private editorial evidence|github_pat_|ghp_[A-Za-z0-9]{20}|BEGIN [A-Z ]*PRIVATE KEY',a['markdown'],re.I)
        a['words']=len(a['markdown'].split());a['minutes']=max(1,math.ceil(a['words']/220))
    return [a for a in data if a.get('approved') is True]

def page(title,description,body,prefix='',slug='',image=None):
    canonical=BASE+slug
    image_meta=f'<meta property="og:image" content="{E(BASE+"assets/"+image)}">' if image else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(title)}</title><meta name="description" content="{E(description)}"><link rel="canonical" href="{E(canonical)}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(description)}"><meta property="og:url" content="{E(canonical)}"><meta property="og:type" content="{'article' if slug.startswith('articles/') else 'website'}">{image_meta}<meta name="theme-color" content="#0b0e14"><link rel="stylesheet" href="{prefix}assets/style.css"><link rel="alternate" type="application/rss+xml" title="BoxBox Builds" href="{prefix}feed.xml"><script defer src="{prefix}assets/search.js"></script></head><body><a class="skip" href="#main">Skip to content</a><header><div class="bar"><a class="brand" href="{prefix}index.html">BOXBOX BUILDS</a><nav aria-label="Main navigation"><a href="{prefix}index.html#journal">Journal</a><a href="{prefix}index.html#projects">Projects</a><a href="{prefix}feed.xml">RSS</a><a href="https://www.instagram.com/boxbox.builds/">Instagram</a></nav></div></header><main id="main">{body}</main><footer><div class="foot"><span>BOXBOX BUILDS · Independent engineering build journal</span><span>Idea. Code. Evolution.</span></div></footer></body></html>'''

def tags(a):return ''.join(f'<span class="tag">{E(t)}</span>' for t in a['tags'])

def card(a):
    key=' '.join([a['title'],a['summary'],a['project'],*a['tags']])
    return f'''<article class="card" data-search="{E(key)}"><img src="assets/{E(a['image'])}" alt="{E(a['alt'])}" loading="lazy" width="1200" height="1200"><div class="card-body"><span class="eyebrow">{E(a['project'])} / Chapter {E(a['edition'])} · {a['minutes']} min</span><h3><a href="articles/{a['slug']}/index.html">{E(a['title'])}</a></h3><p>{E(a['summary'])}</p><div class="tags">{tags(a)}</div><a class="read" href="articles/{a['slug']}/index.html">Read chapter →</a></div></article>'''

def article(a,previous,next_):
    tokens=MD.parse(a['markdown']); sections=[]; used=set()
    for i,t in enumerate(tokens):
        if t.type=='heading_open' and t.tag=='h2':
            label=tokens[i+1].content; slug=re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-') or 'section'; base=slug; k=2
            while slug in used:slug=f'{base}-{k}';k+=1
            used.add(slug);t.attrSet('id',slug);sections.append((slug,label))
    content=MD.renderer.render(tokens,MD.options,{})
    toc=''.join(f'<a href="#{id}">{E(label)}</a>' for id,label in sections)
    def related(item,direction):return f'<a href="../{item["slug"]}/index.html"><span>{direction} chapter</span>{E(item["title"])}</a>' if item else ''
    body=f'''<div class="article-header"><a href="../../index.html#journal">← All chapters</a><p class="eyebrow">{E(a['project'])} / Chapter {E(a['edition'])}</p><h1>{E(a['title'])}</h1><p class="dek">{E(a['summary'])}</p><div class="meta">{a['minutes']} min read · Evidence reviewed November 2026</div><div class="tags">{tags(a)}</div></div><figure class="article-hero"><img src="../../assets/{E(a['image'])}" alt="{E(a['alt'])}"><figcaption>{E(a['caption'])}</figcaption></figure><div class="article-grid"><article class="prose">{content}<p><a href="https://gridlock-f1dash.duckdns.org/">Explore the F1 Telemetry application →</a></p><nav class="article-nav" aria-label="Related chapters">{related(previous,'Previous')}{related(next_,'Next')}</nav></article><aside class="toc" aria-label="Contents"><strong>IN THIS CHAPTER</strong>{toc}</aside></div>'''
    return page(a['title']+' | BoxBox Builds',a['summary'],body,'../../','articles/'+a['slug']+'/',a['image'])

def build(out):
    assert out.resolve()==ROOT/'dist', 'Only the dedicated dist directory may be rebuilt'
    out.mkdir(parents=True,exist_ok=True); data=read_articles();assert data
    # Rebuild in a clean target to avoid retaining a removed article.
    for p in out.iterdir():
        if p.is_symlink() or p.is_file():p.unlink()
        elif p.is_dir():shutil.rmtree(p)
    (out/'assets').mkdir()
    for f in ('style.css','search.js',*(a['image'] for a in data)):
        shutil.copyfile(ROOT/'assets'/f,out/'assets'/f)
    body=f'''<section class="hero"><div class="eyebrow">The engineering build journal / 001</div><h1>Idea. Code.<br><em>Evolution.</em></h1><p>Two Formula 1 side projects, and the decisions, experiments and trade-offs behind building them. Follow the journey from the first recorded implementation to the current product.</p><a href="#journal">Explore the journal ↓</a></section><section id="journal"><div class="section-head"><h2>F1 Telemetry · The build journey</h2><span id="result-count" aria-live="polite">{len(data)} articles</span></div><label for="article-search" class="eyebrow">Find a topic</label><input class="search" id="article-search" type="search" placeholder="Search replay, API design, charts…"><div class="cards">{''.join(card(a) for a in data)}</div><p class="empty" id="no-results" hidden>No matching articles.</p></section><section id="projects"><div class="section-head"><h2>The projects</h2></div><div class="project"><h2>F1 Telemetry</h2><p>A dashboard for exploring Formula 1 race sessions, individual driver telemetry and tyre strategy.</p><a href="https://gridlock-f1dash.duckdns.org/">Explore the application →</a></div><div class="project"><h2>GRIDLOCK</h2><p>A Formula 1 prediction and tournament platform. Its build journal will follow the telemetry chapters as the editorial series develops.</p><a href="https://gridlock-f1pool.duckdns.org/">Explore GRIDLOCK →</a></div></section>'''
    with (out/'assets/style.css').open('a') as css: css.write('\n'+HtmlFormatter(style='monokai').get_style_defs('.prose pre')+'\n')
    (out/'index.html').write_text(page('BoxBox Builds | Engineering build journal','The development journey behind F1 Telemetry and GRIDLOCK.',body),encoding='utf8')
    for i,a in enumerate(data):
        folder=out/'articles'/a['slug'];folder.mkdir(parents=True)
        (folder/'index.html').write_text(article(a,data[i-1] if i else None,data[i+1] if i+1<len(data) else None),encoding='utf8')
    rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
    for key,value in [('title','BoxBox Builds'),('link',BASE),('description','Engineering build journal for F1 Telemetry and GRIDLOCK.'),('language','en')]:ET.SubElement(channel,key).text=value
    for a in reversed(data):
        item=ET.SubElement(channel,'item');url=BASE+'articles/'+a['slug']+'/'
        for key,value in [('title',a['title']),('link',url),('guid',url),('description',a['summary'])]:ET.SubElement(item,key).text=value
    ET.ElementTree(rss).write(out/'feed.xml',encoding='utf-8',xml_declaration=True)
    urls=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for u in [BASE]+[BASE+'articles/'+a['slug']+'/' for a in data]:ET.SubElement(ET.SubElement(urls,'url'),'loc').text=u
    ET.ElementTree(urls).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n');(out/'.nojekyll').touch()
    print(f'Built {len(data)} articles ({sum(a["words"] for a in data)} source words) at {out}')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'dist');args=p.parse_args();build(args.out)
