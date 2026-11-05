from pathlib import Path
import re

def blocks(s):
 depth=0; quoted=False; esc=False; start=0
 for i,c in enumerate(s):
  if quoted:
   if esc: esc=False
   elif c=='\\': esc=True
   elif c=='"': quoted=False
   continue
  if c=='"': quoted=True
  elif c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:yield s[start:i+1]
   depth-=1

def ref(b):
 m=re.search(r'\(property "Reference" "([^"]+)"',b)
 return m[1] if m else ''
for file in ['scoreboard.kicad_sch','IEEEArcade.kicad_sch']:
 print('\nFILE',file)
 bs=list(blocks(Path(file).read_text()))
 for b in bs:
  if b.startswith('(symbol') and ref(b) in ['U7','U8','J3','J4','R510','R610','R4','Q1','R101']:
   print(ref(b),re.search(r'\(at [^)]+\)',b)[0])
   if ref(b) in ['R510','R610','J4']:print(b)
  if b.startswith('(global_label') and any('"'+x+'"' in b for x in ['DISP_D','DISP_D_5V']):print(b)
