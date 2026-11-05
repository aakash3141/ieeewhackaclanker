from pathlib import Path
import re,uuid
exec(Path('display_inspect.py').read_text().split('for file in')[0])
def uid():return str(uuid.uuid4())
def fmt(v):return f'{v:.5f}'.rstrip('0').rstrip('.')
def at(b):return tuple(map(float,re.search(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',b).groups()))
def move(b,x,y,angle=None):
 ox,oy,oa=at(b); dx=x-ox;dy=y-oy
 b=re.sub(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)',lambda m:f'(at {fmt(float(m[1])+dx)} {fmt(float(m[2])+dy)} {m[3]})',b)
 if angle is not None:b=re.sub(r'\(at [^ ]+ [^ ]+ [^)]+\)',f'(at {fmt(x)} {fmt(y)} {angle})',b,count=1)
 return b

def prop(b,k,v):
 return re.sub(r'(\(property "'+re.escape(k)+r'" )"(?:\\.|[^"\\])*"',lambda m:m[1]+'"'+v.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"',b,count=1)
def fresh(b):return re.sub(r'\(uuid "[^"]+"\)',lambda m:f'(uuid "{uid()}")',b)
def label(name,x,y,angle=0):
 return f'(global_label "{name}" (shape bidirectional) (at {fmt(x)} {fmt(y)} {angle}) (effects (font (size 1.05 1.05)) (justify {"left" if angle==0 else "right"})) (uuid "{uid()}"))'
def wire(x1,y1,x2,y2):return f'(wire (pts (xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)})) (stroke (width 0) (type default)) (uuid "{uid()}"))'
def nc(x,y):return f'(no_connect (at {fmt(x)} {fmt(y)}) (uuid "{uid()}"))'
def text(t,x,y,size=1.05):
 t=t.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
 return f'(text "{t}" (exclude_from_sim no) (at {fmt(x)} {fmt(y)} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid()}"))'
root=Path('IEEEArcade.kicad_sch').read_text();s=Path('scoreboard.kicad_sch').read_text();bs=list(blocks(s));rb=list(blocks(root));bank=list(blocks(Path('button_bank_1.kicad_sch').read_text()))
syms={ref(b):b for b in bs if b.startswith('(symbol')}
path=re.search(r'\(path "([^"]+)"',syms['R4'])[1]
def clone(b,nr,x,y):
 oldref=ref(b);b=fresh(move(b,x,y));b=prop(b,'Reference',nr)
 b=b.replace(f'(reference "{oldref}")',f'(reference "{nr}")')
 b=re.sub(r'\(path "[^"]+"',f'(path "{path}"',b)
 return b
# Use existing verified 10k and 100k parts; no new resistor SKU.
r10=syms['R4'];q=next(b for b in bank if ref(b)=='Q1' and b.startswith('(symbol'))
q33=clone(q,'Q33',292.1,248.92)
q33=prop(q33,'Assembly','On PCB; display buffer enable, GPIO9 HIGH enables')
# Existing R510 is repurposed as 10k buffer-disable pull-up.
r510=clone(r10,'R510',294.64,232.41)
# Keep R510's symbol/pin identities for board association.
uold=re.findall(r'\(uuid "([^"]+)"\)',syms['R510']);unew=re.findall(r'\(uuid "([^"]+)"\)',r510)
for a,b in zip(unew,uold):r510=r510.replace(a,b)
r514=clone(r10,'R514',248.92,240.03)
r514=prop(r514,'Assembly','On PCB; keeps panel OE inactive when buffers disabled')
new=[]
for b in bs:
 if b.startswith('(lib_symbols'):
  # Add the existing MOSFET definition and PWR_FLAG for external supply.
  blib=next(x for x in bank if x.startswith('(lib_symbols'));rlib=next(x for x in rb if x.startswith('(lib_symbols'))
  extra=[next(x for x in blocks(blib) if x.startswith('(symbol "Transistor_FET:AO3400A"')),next(x for x in blocks(rlib) if x.startswith('(symbol "power:PWR_FLAG"'))]
  b=b[:-1]+'\n\t\t'+'\n\t\t'.join(extra)+'\n\t)'
 elif b.startswith('(title_block'): b=b.replace('Provisional 16-pin external scoreboard','Photo-matched HUB75 scoreboard / A-B-C scan')
 elif b.startswith('(symbol'):
  r=ref(b)
  if r=='R510':b=r510
  elif r in ['#PWR0055','#PWR0069']:b=label('DISP_BUF_OE_N',*at(b)[:2],180)
  elif '"power:+5V"' in b:b=label('+5V_DISPLAY',*at(b)[:2],180)
  elif r=='J3':
   b=prop(b,'Value','HUB75 / ABC / pin12 GND')
   b=prop(b,'Verification','Signal assignment read from DisplayConnections1.png: pin12 GND, not D; check mating-view pin1 on actual input header')
   b=prop(b,'Assembly','16-way straight-through IDC to panel INPUT; OUTPUT header unused for one panel')
  elif r=='J4':
   b=prop(b,'Value','EXT 5V INPUT / BUFFERS ONLY')
   b=prop(b,'Assembly','Input from external regulated 5V display supply; panel fed directly by separate high-current harness')
   b=prop(b,'Verification','Board-side XH mate verified; J4 is NOT the photographed 4-contact panel power connector')
 elif b.startswith('(global_label "DISP_D"'):
  b=label('DISP_ENABLE',48.26,177.8,180)
 elif b.startswith('(global_label "DISP_D_5V"'):
  if at(b)[0]>350:b=label('GND',*at(b)[:2])
  else:continue
 elif b.startswith('(wire'):
  pts=[tuple(map(float,m)) for m in re.findall(r'\(xy ([^ ]+) ([^)]+)\)',b)]
  if pts in [[(193.04,177.8),(283.21,177.8)],[(290.83,177.8),(307.34,177.8)],[(167.64,177.8),(48.26,177.8)]]:continue
 elif b.startswith('(text'):
  if 'A -> B: DIR high' in b:
   b=re.sub(r'\(text "(?:\\.|[^"\\])*"',lambda m:'(text "DIR high: A-to-B. /OE controlled by DISP_BUF_OE_N.\\nUnused inputs grounded; unused outputs left open."',b,count=1)
  elif 'EXTERNAL SCOREBOARD |' in b:
   b=prop(b,'dummy','dummy') # text retains UUID and placement below
   b=re.sub(r'\(text "(?:\\.|[^"\\])*"','(text "RGB SCOREBOARD | PHOTO-MATCHED HUB75 / A-B-C"',b,count=1)
  elif 'User requested an expected connector' in b:
   b=re.sub(r'\(text "(?:\\.|[^"\\])*"',lambda m:'(text "Photo: DR1/DG1/DB1, DR2/DG2/DB2, A/B/C, CLK, STB, OE. Pin12 = GND (NOT D).\\nPico PIO refresh: 6 RGB + 3 address + CLK/LAT/OE; no I2C expander. GP9 enables buffers."',b,count=1)
  elif 'J4: 1=+5 V' in b:
   b=text('J4 INPUT: 1=external +5V, 2=GND.\nPowers AHCT buffers ONLY.\nPanel power: direct external PSU\nto VCC/GND power contacts.\nDo not bridge to board +5V buck.\nConfirm panel voltage/current.\n5V is a design assumption.',337.82,198.12)
  elif 'R501..R513:' in b:
   b=text('R501..R509, R511..R513: 33 ohms. R510: 10k buffer-disable pull-up; R610: 100k GP9 pull-down.\nQ33 enables buffers only when GP9 HIGH; R514 holds panel OE HIGH when buffers are disabled.\nInitialize OE HIGH, CLK/LAT LOW and row/data outputs; then enable GP9. Use PIO/DMA scan refresh.\nExternal regulated display supply: direct power harness to panel, common GND to J4/J3. Voltage/current and scan mapping need confirmation.',20,269.24)
 new.append(b)
new += [nc(193.04,177.8),label('GND',167.64,177.8,180),q33,r514,
 label('+5V_DISPLAY',294.64,226.06,180),wire(294.64,226.06,294.64,228.6),
 wire(294.64,236.22,294.64,240.03),wire(294.64,240.03,294.64,243.84),label('DISP_BUF_OE_N',294.64,240.03),
 f'(junction (at 294.64 240.03) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))',
 wire(287.02,248.92,276.86,248.92),label('DISP_ENABLE',276.86,248.92,180),
 wire(294.64,254,294.64,259.08),label('GND',294.64,259.08),
 label('+5V_DISPLAY',248.92,231.14,180),wire(248.92,231.14,248.92,236.22),
 wire(248.92,243.84,248.92,248.92),label('DISP_OE_N_5V',248.92,248.92),
 text('RESET-SAFE DISPLAY ENABLE\nGP9 LOW / floating: blank\nGP9 HIGH: PIO owns panel',225,216.0),
 text('J3 -> panel INPUT (follow data-flow arrow).\nHeader pin rows, mating orientation checked:\n 1 R1   2 G1     3 B1   4 GND\n 5 R2   6 G2     7 B2   8 GND\n 9 A   10 B     11 C   12 GND\n13 CLK 14 STB   15 OE  16 GND\nSTB = LAT. OE is active LOW.\nPanel OUTPUT: leave open, or cascade.\nPower: all VCC contacts to supply +;\nall GND contacts to supply return.\nPhoto does not establish power pin numbers.',310,118.11,0.95)]
flag=next(b for b in rb if b.startswith('(symbol') and ref(b)=='#FLG01')
new.append(clone(flag,'#FLG03',358.14,152.4))
# Preserve existing sheet formatting, with new blocks appended.
Path('scoreboard.kicad_sch').write_text('(kicad_sch\n\t'+'\n\t'.join(new)+'\n)\n')
root=root.replace('(global_label "DISP_D"','(global_label "DISP_ENABLE"').replace('"Scoreboard (PROVISIONAL)"','"Scoreboard (HUB75 ABC)"')
# Describe freed address-D output repurposing at the Pico label.
Path('IEEEArcade.kicad_sch').write_text(root)
print('Updated scoreboard and root sheet; retained other sheets untouched.')
