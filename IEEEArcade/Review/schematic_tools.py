import re,json,xml.etree.ElementTree as E,zlib
from pathlib import Path
# Minimal lossless S-expression reader: retain text for all untouched nodes.
class Node:
 def __init__(self,start,end,items): self.start,self.end,self.items=start,end,items
 def key(self): return self.items[0] if self.items else ''
 def children(self,k): return [v for v in self.items if isinstance(v,Node) and v.key()==k]
 def child(self,k): return next(iter(self.children(k)),None)
 def val(self,k,i=1): return self.child(k).items[i]
def parse(s):
 tok=list(re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s)); pos=0
 def rec():
  nonlocal pos
  start=tok[pos].start(); pos+=1; items=[]
  while tok[pos].group()!=')':
   if tok[pos].group()=='(': items.append(rec())
   else:
    t=tok[pos].group(); items.append(json.loads(t) if t.startswith('"') else t); pos+=1
  end=tok[pos].end(); pos+=1; return Node(start,end,items)
 return rec()
def prop(n,k): return next((p.items[2] for p in n.children('property') if p.items[1]==k),None)
