#!/usr/bin/env python3
"""Build cape achievement catalogues from RuneScape Wiki's MediaWiki API.
Run in GitHub Actions; browser never requests the Wiki directly.
"""
import json, re, html, urllib.parse, urllib.request, pathlib
from html.parser import HTMLParser

PAGES={
 "max":("Max Cape (achievement)",29),
 "mastermax":("Master Max Cape (achievement)",29),
 "quest":("Quest Cape (achievement)",100),
 "masterquest":("Master Quest Cape (achievement)",312),
 "comp":("Completionist Cape (achievement)",102),
 "trim":("Trimmed Completionist Cape (achievement)",89),
 "mastercomp":("Master Completionist Cape (achievement)",1),
 "mastertrim":("Master Trimmed Completionist Cape (achievement)",1),
}
class TableReader(HTMLParser):
 def __init__(self):
  super().__init__();self.tables=[];self.current=None;self.row=None;self.cell=None;self.depth=0;self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag=="table":
   if self.current is None:self.current=[];self.depth=1
   else:self.depth+=1
  if self.current is None:return
  if tag=="tr" and self.depth==1:self.row=[]
  if tag in ("td","th") and self.depth==1 and self.row is not None:self.cell=[]
  if tag in ("br",) and self.cell is not None:self.cell.append(" ")
 def handle_data(self,data):
  if self.cell is not None:self.cell.append(data)
 def handle_endtag(self,tag):
  if self.current is None:return
  if tag in ("td","th") and self.cell is not None:
   self.row.append(" ".join("".join(self.cell).split()));self.cell=None
  if tag=="tr" and self.row is not None:
   if self.row:self.current.append(self.row)
   self.row=None
  if tag=="table":
   self.depth-=1
   if self.depth==0:self.tables.append(self.current);self.current=None

def fetch(page):
 url="https://runescape.wiki/api.php?"+urllib.parse.urlencode({"action":"parse","page":page,"prop":"text","format":"json","formatversion":"2"})
 req=urllib.request.Request(url,headers={"User-Agent":"RSCompletionTracker/1.0 (GitHub Pages personal progress tracker; github.com/sandrovon/rs-completion-tracker)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=35) as response:
  obj=json.load(response)
 return obj["parse"]["text"]

def extract(page,expected):
 parser=TableReader();parser.feed(fetch(page))
 candidates=[]
 for table in parser.tables:
  if len(table)<2:continue
  header=table[0]
  joined=" ".join(header).lower()
  if "name" not in joined or "description" not in joined:continue
  ni=next((i for i,x in enumerate(header) if x.lower().strip()=="name"),None)
  di=next((i for i,x in enumerate(header) if x.lower().strip()=="description"),None)
  if ni is None or di is None:continue
  rows=[]
  for row in table[1:]:
   if len(row)<=max(ni,di):continue
   name=row[ni].strip();description=row[di].strip()
   if name and name.lower()!="name" and len(name)<180:
    rows.append({"title":name,"description":description})
  if rows:candidates.append(rows)
 if not candidates:raise ValueError("No achievement table found")
 rows=min(candidates,key=lambda rows:abs(len(rows)-expected))
 if expected>=20 and len(rows)<expected*.65:raise ValueError(f"Too few rows: {len(rows)} vs expected {expected}")
 seen=set();unique=[]
 for r in rows:
  if r["title"].casefold() in seen:continue
  seen.add(r["title"].casefold());unique.append(r)
 return unique

out={};errors={}
for id,(page,expected) in PAGES.items():
 try:
  rows=extract(page,expected)
  out[id]=rows
  print(f"{page}: {len(rows)} requirements")
 except Exception as e:
  errors[id]=str(e)
  print(f"WARNING {page}: {e}")
# Don't publish a misleading incomplete catalogue. Keep previous valid version if available.
destination=pathlib.Path("public/cape-requirements.json")
if len(out)<6:
 if destination.exists():print("Keeping previous cape catalogue")
 else:print("Wiki data insufficient; app will show starter tasks")
else:
 destination.parent.mkdir(exist_ok=True)
 destination.write_text(json.dumps({"source":"RuneScape Wiki","capes":out,"errors":errors},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
 print("Saved",destination)
