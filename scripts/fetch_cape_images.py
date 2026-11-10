#!/usr/bin/env python3
"""Resolve the eight cape item images from RuneScape Wiki's MediaWiki API."""
import json,urllib.parse,urllib.request,pathlib
pages={"max":"Max cape","mastermax":"Master max cape","quest":"Quest point cape","masterquest":"Master quest cape","comp":"Completionist cape","trim":"Completionist cape (t)","mastercomp":"Master completionist cape","mastertrim":"Master trimmed completionist cape"}
out={}
for key,page in pages.items():
 try:
  url="https://runescape.wiki/api.php?"+urllib.parse.urlencode({"action":"query","titles":page,"prop":"pageimages","pithumbsize":320,"format":"json","redirects":1})
  req=urllib.request.Request(url,headers={"User-Agent":"RSCompletionTracker/1.0 (github.com/sandrovon/rs-completion-tracker)"})
  with urllib.request.urlopen(req,timeout=20) as resp:result=json.load(resp)
  for entry in result.get("query",{}).get("pages",{}).values():
   src=entry.get("thumbnail",{}).get("source")
   if src and src.startswith("https://"):out[key]=src
  print(key,page, "OK" if key in out else "image not found")
 except Exception as e:print(key,"image lookup failed:",e)
if out:
 target=pathlib.Path("public/cape-images.json");target.parent.mkdir(exist_ok=True)
 target.write_text(json.dumps(out,indent=2),encoding="utf-8")
