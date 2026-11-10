"""Compact the current, unrouted board without changing schematic sources or project rules."""
from pathlib import Path
import pcbnew as p
import xml.etree.ElementTree as ET
import json,hashlib,shutil,csv,collections
ROOT=Path.cwd(); OUT=ROOT/'Review'; BACK=ROOT/'.layout-backup'/'before-compact-20261110'
BACK.mkdir(parents=True,exist_ok=True)
for n in ['IEEEArcade.kicad_pcb','IEEEArcade.kicad_pro']:
 if not (BACK/n).exists():shutil.copy2(ROOT/n,BACK/n)
source=BACK/'IEEEArcade.kicad_pcb';b=p.LoadBoard(str(source));assert len(b.GetTracks())==0 and len(b.Zones())==0
hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in list(ROOT.glob('*.kicad_sch'))+[ROOT/'IEEEArcade.kicad_pro']}
r=ET.parse(OUT/'compact-current-schematic.net').getroot();comps={c.get('ref'):c for c in r.findall('./components/comp')}
fs={f.GetReference():f for f in b.GetFootprints()}
removed=[]
for ref in sorted(set(fs)-set(comps)):
 if ref.startswith('H') and fs[ref].GetAttributes() & p.FP_BOARD_ONLY:continue
 removed.append(ref);b.Delete(fs[ref]);del fs[ref]
assert set(comps)<=set(fs)
expected={(n.get('ref'),n.get('pin')):net.get('name') for net in r.findall('./nets/net') for n in net.findall('node')}
for ref in comps:
 f=fs[ref];assert f.GetFPIDAsString()==comps[ref].findtext('footprint'),ref
 for pad in f.Pads():
  no=pad.GetNumber()
  if (ref,no) in expected:assert pad.GetNetname()==expected[ref,no],(ref,no,'pre-existing net mismatch')
# Preserve existing footprint-local graphics and antenna keepouts; replace board labels and outline.
for d in list(b.GetDrawings()):b.Delete(d)
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def box(bb):return [p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]
def court(f):
 boxes=[box(s.GetBoundingBox()) for s in f.GraphicalItems() if s.GetLayer()==p.F_CrtYd]
 if not boxes:return box(f.GetBoundingBox(False,False))
 return [min(a[0] for a in boxes),min(a[1] for a in boxes),max(a[2] for a in boxes),max(a[3] for a in boxes)]
placed=set()
def put(ref,x,y,angle=0,center=False):
 f=fs[ref];f.SetOrientationDegrees(angle)
 if center:
  bb=court(f);cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2;pos=f.GetPosition();f.SetPosition(v(p.ToMM(pos.x)+x-cx,p.ToMM(pos.y)+y-cy))
 else:f.SetPosition(v(x,y))
 placed.add(ref);return f
def text(s,x,y,size=1,angle=0,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));b.Add(t);return t
def line(a,c):
 d=p.PCB_SHAPE();d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(v(*a));d.SetEnd(v(*c));d.SetLayer(p.Edge_Cuts);d.SetWidth(p.FromMM(.05));b.Add(d)
for ch in range(1,33):
 bottom=ch>16;col=(ch-1)%16;x=84+8*col;mirror=lambda y:185-y if bottom else y
 put(f'J{ch+10}',x,mirror(43),-90 if bottom else 90)
 if ch<=30:
  put(f'Q{ch}',x-1,mirror(52),180 if bottom else 0,center=True)
  for prefix,dx,y in [(100,-1,58),(200,-1,63)]:put(f'R{prefix+ch}',x+dx,mirror(y),center=True)
 for prefix,y in [(300,68),(400,73)]:put(f'R{prefix+ch}',x+1,mirror(y),center=True)
 put(f'C{100+ch}',x+1,mirror(78),center=True)
 text(f'{ch:02}',x,mirror(47.5),.95)
 # Horizontal labels below/above the channel bank; full legend once per bank.
for ref,x in [('U1',88),('U5',110),('U4',132),('U6',154)]:put(ref,x,92.5,center=True)
for cap,ic in [('C5','U1'),('C6','U5'),('C4','U4'),('C7','U6')]:
 pad=next(pad for pad in fs[ic].Pads() if pad.GetNumber()=='9');put(cap,p.ToMM(pad.GetPosition().x)-4.5,p.ToMM(pad.GetPosition().y),90,center=True)
# Retain the proven relative placement of the unrouted buck cluster.
for ref in ['U2','C14','C12','C13','L1','C19','R9','R10','R11','C18','C20','C21','C22','C23']:
 f=fs[ref];pos=f.GetPosition();put(ref,p.ToMM(pos.x)-21,p.ToMM(pos.y)-75,f.GetOrientationDegrees())
put('J1',42.5,72,-90);put('F1',55,72,90);put('C10',65,84);put('D1',74,42,90)
# USB at right edge, antenna toward the board interior. Keep all footprint keepouts.
put('A1',202.675,92.5,-90)
put('R412',218,73,center=True);put('C112',218,78,center=True)
put('R428',210,110,center=True);put('C128',210,115,center=True)
put('U3',219,119,center=True);put('C3',225,119,90,center=True)
put('C2',219,107,90,center=True);put('C1',217,140,90,center=True)
for ref,x,y in [('R1',215,128),('R2',221,128),('R3',221,134)]:put(ref,x,y,center=True)
# Display interface at bottom-left, with short local runs from buffers through damping resistors.
put('U7',45,112,center=True);put('U8',70,112,center=True)
for ic,cap in [('U7','C30'),('U8','C31')]:
 pad=next(a for a in fs[ic].Pads() if a.GetNumber()=='20');put(cap,p.ToMM(pad.GetPosition().x),96,center=True)
series=[('U7',18-i,f'R{501+i}') for i in range(8)]+[('U8',18,'R509'),('U8',16,'R511'),('U8',15,'R512'),('U8',14,'R513')]
for ic,no,ref in series:
 pad=next(a for a in fs[ic].Pads() if a.GetNumber()==str(no));put(ref,p.ToMM(pad.GetPosition().x)+4.8,p.ToMM(pad.GetPosition().y),center=True)
pulls=[('U7',2+i,f'R{601+i}') for i in range(8)]+[('U8',2,'R609'),('U8',4,'R611'),('U8',5,'R612')]
for ic,no,ref in pulls:
 pad=next(a for a in fs[ic].Pads() if a.GetNumber()==str(no));yy=101+3.5*(no-2) if ic=='U7' else (113.5 if ref=='R612' else p.ToMM(pad.GetPosition().y));put(ref,p.ToMM(pad.GetPosition().x)-4.8,yy,center=True)
for ref,x,y in [('Q34',40,132),('R613',40,137),('R4',49,132),('R510',61,132),('R514',72,132)]:
 if ref in fs:put(ref,x,y,center=True)
put('J3',54.5,146,90,center=True)
for ref,x,y in [('H1',36,36),('H2',224,36),('H3',36,149),('H4',224,149),('H5',121,86),('H6',36,90),('H7',224,60)]:put(ref,x,y)
assert placed==set(fs),('unplaced',sorted(set(fs)-placed))
for a,c in [((30,30),(230,30)),((230,30),(230,155)),((230,155),(30,155)),((30,155),(30,30))]:line(a,c)
text('IEEE ARCADE',55,91,1.2)
text('12V DC',45,62,1)
text('5V BUCK',57,31.7,.85)
text('HUB75 / PIN12 GND',54.5,138,.85)
text('USB',226,108,.85)
text('01-16: 1 LED+ / 2 LED- / 3 NO / 4 COM',144,31.4,.8)
text('17-30: 1 LED+ / 2 LED- / 3 NO / 4 COM',140,153.6,.8)
text('31/32 MENU: 3 NO / 4 COM',195,153.6,.8)
text('200 x 125 mm / PLACEMENT ONLY / UNROUTED',130,160,1,layer=p.Dwgs_User)
text('TOP-ENTRY BUTTON HEADERS / 16 TOP + 16 BOTTOM',130,25,1,layer=p.Dwgs_User)
# Place references into free silkscreen space; no silk/clearance rules are relaxed.
def hit(a,c,g=.15):return a[0]<c[2]+g and a[2]>c[0]-g and a[1]<c[3]+g and a[3]>c[1]-g
courts={ref:court(f) for ref,f in fs.items()};obstacles=list(courts.values());labels=[box(t.GetBoundingBox()) for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS];failed=[]
physical=[box(pad.GetBoundingBox()) for f in fs.values() for pad in f.Pads()]+[box(shape.GetBoundingBox()) for f in fs.values() for shape in f.GraphicalItems() if shape.GetLayer()==p.F_SilkS]
for ref,f in sorted(fs.items()):
 f.Value().SetVisible(False);t=f.Reference();t.SetVisible(True);t.SetLayer(p.F_SilkS);t.SetTextSize(v(.8,.8));t.SetTextThickness(p.FromMM(.1));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetKeepUpright(True)
 bb=courts[ref];x=(bb[0]+bb[2])/2;y=(bb[1]+bb[3])/2
 candidates=[(x,bb[1]-.7),(x,bb[3]+.7),(bb[2]+1.6,y),(bb[0]-1.6,y)]
 candidates += [(x+dx,y+dy) for dy in [-2,2,-3,3,-4,4,-6,6,-8,8] for dx in [0,-2,2,-4,4,-6,6,-8,8]]
 if ref in ['A1','U7','U8']: candidates=[(x,y)]+candidates
 localobs=[ob for key,ob in courts.items() if key!=ref] + [box(pad.GetBoundingBox()) for pad in f.Pads()] if ref in ['A1','U7','U8'] else obstacles
 for xx,yy in candidates:
  t.SetPosition(v(xx,yy));tb=box(t.GetBoundingBox())
  if tb[0]<30.5 or tb[2]>229.5 or tb[1]<30.5 or tb[3]>154.5:continue
  if any(hit(tb,ob) for ob in localobs+labels):continue
  labels.append(tb);break
 else:
  # References may sit inside a component courtyard if they clear the real pads and silk.
  for xx,yy in candidates+[(x+dx,y+dy) for dy in range(-10,11,2) for dx in range(-10,11,2)]:
   t.SetPosition(v(xx,yy));tb=box(t.GetBoundingBox())
   if tb[0]<30.5 or tb[2]>229.5 or tb[1]<30.5 or tb[3]>154.5:continue
   if any(hit(tb,ob,.2) for ob in physical+labels):continue
   labels.append(tb);break
  else:failed.append(ref)
p.SaveBoard(str(ROOT/'IEEEArcade.kicad_pcb'),b)
check=p.LoadBoard(str(ROOT/'IEEEArcade.kicad_pcb'));actual={f.GetReference():f for f in check.GetFootprints()}
assert set(actual)==set(fs)
for key,net in expected.items():
 ref,no=key;pads=[a for a in actual[ref].Pads() if a.GetNumber()==no];assert pads and all(a.GetNetname()==net for a in pads),key
assert hashes=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in hashes}
summary={'original_size_mm':[360,140],'new_size_mm':[200,125],'area_reduction_percent':100*(1-200*125/(360*140)),'schematic_components':len(comps),'footprints':len(actual),'removed_obsolete_references':removed,'schematic_pad_assignments':len(expected),'tracks':len(check.GetTracks()),'zones':len(check.Zones()),'layers':check.GetCopperLayerCount(),'reference_placement_needs_review':failed,'preserved_source_hashes':hashes}
(OUT/'compact-placement-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
with (OUT/'compact-placement-positions.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','X_mm','Y_mm','Rotation_deg'])
 for ref,fp in sorted(actual.items()):w.writerow([ref,fp.GetValue(),p.ToMM(fp.GetPosition().x),p.ToMM(fp.GetPosition().y),fp.GetOrientationDegrees()])
print(json.dumps(summary,indent=2))



