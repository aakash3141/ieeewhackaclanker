"""Placement only; run with KiCad 10's bundled Python from the project folder."""
from pathlib import Path
import pcbnew as p
import xml.etree.ElementTree as ET
import json, os, shutil, collections, hashlib

ROOT = Path.cwd()
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
boardfile = ROOT / 'IEEEArcade.kicad_pcb'
backup = ROOT / '.layout-backup/before-placement-20261105'
backup.mkdir(exist_ok=True)
for name in ['IEEEArcade.kicad_pcb', 'IEEEArcade.kicad_pro']:
    if not (backup/name).exists(): shutil.copy2(ROOT/name, backup/name)
sch_hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.glob('*.kicad_sch')}
b = p.LoadBoard(str(backup/'IEEEArcade.kicad_pcb'))
assert len(b.GetTracks()) == 0 and len(b.Zones()) == 0
fs = {f.GetReference(): f for f in b.GetFootprints()}
# Trim the custom inductor silk around its own lands, in both library and board copy.
lp=ROOT/'Arcade.pretty/L_Wurth_7447714150.kicad_mod'
if not (backup/lp.name).exists(): shutil.copy2(lp,backup/lp.name)
import re
ls=lp.read_text()
ls=re.sub(r'  \(fp_line\s+\(start (5\.12|-5\.12) (-?5\.12)\)\s+\(end \1 (-?5\.12)\)\s+\(stroke\s+\(width 0\.12\)\s+\(type solid\)\)\s+\(layer "F.SilkS"\)\)',lambda m: '\n'.join(f'  (fp_line (start {m[1]} {a}) (end {m[1]} {z}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))' for a,z in [(-5.12,-2.1),(2.1,5.12)]),ls)
lp.write_text(ls)
lf=fs['L1']; lx=lf.GetPosition().x; ly=lf.GetPosition().y
for shape in list(lf.GraphicalItems()):
    if isinstance(shape,p.PCB_SHAPE) and shape.GetLayer()==p.F_SilkS and shape.GetStart().x==shape.GetEnd().x:
        x=shape.GetStart().x
        lf.Remove(shape)
        for a,z in [(-5.12,-2.1),(2.1,5.12)]:
            seg=p.PCB_SHAPE(lf); seg.SetShape(p.SHAPE_T_SEGMENT); seg.SetStart(p.VECTOR2I(x,ly+p.FromMM(a))); seg.SetEnd(p.VECTOR2I(x,ly+p.FromMM(z))); seg.SetLayer(p.F_SilkS); seg.SetWidth(p.FromMM(.12)); lf.Add(seg)
netlist = ET.parse(Path(os.environ['TEMP'])/'arcade-placement.xml')
comps = {c.get('ref'): c for c in netlist.findall('./components/comp')}
assert set(comps) == set(fs), 'Component inventory differs'
audit = []
for ref,c in comps.items():
    fid = c.findtext('footprint')
    assert fid == fs[ref].GetFPID().GetUniStringLibId(), (ref, fid)
    lib,name = fid.split(':',1)
    path = (ROOT/'Arcade.pretty' if lib=='Arcade' else LIB/(lib+'.pretty'))/(name+'.kicad_mod')
    assert path.exists(), (ref, 'Missing footprint file', path)
    audit.append({'reference':ref,'footprint':fid,'library_file':str(path)})
# Synchronize every numbered pad directly from the saved schematic netlist.
expected = {}
for net in netlist.findall('./nets/net'):
    name = net.get('name')
    item = b.FindNet(name)
    if item is None or item.GetNetCode() < 0:
        item = p.NETINFO_ITEM(b,name); b.Add(item)
    for node in net.findall('node'):
        expected[(node.get('ref'),node.get('pin'))] = name
        pads = [pad for pad in fs[node.get('ref')].Pads() if pad.GetNumber()==node.get('pin')]
        assert pads, ('Missing pad',node.attrib)
        for pad in pads: pad.SetNet(item)
for ref,f in fs.items():
    for pad in f.Pads():
        if pad.GetNumber() and (ref,pad.GetNumber()) not in expected: pad.SetNetCode(0)

placed = set()
def v(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def put(ref,x,y,angle=0):
    f=fs[ref]; f.SetOrientationDegrees(angle); f.SetPosition(v(x,y)); placed.add(ref)
    return f
def txt(text,x,y,size=1,layer=p.F_SilkS,angle=0):
    t=p.PCB_TEXT(b); t.SetText(text); t.SetPosition(v(x,y)); t.SetTextSize(v(size,size))
    t.SetTextThickness(p.FromMM(.12)); t.SetLayer(layer); t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T)); b.Add(t)
    return t
def line(x1,y1,x2,y2,layer=p.Edge_Cuts,width=.05):
    s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_SEGMENT); s.SetStart(v(x1,y1)); s.SetEnd(v(x2,y2)); s.SetLayer(layer); s.SetWidth(p.FromMM(width)); b.Add(s)

# One top-edge row. Vertical XH mating axes remain vertical; pin rows perpendicular to edge.
for ch in range(1,33):
    x=47+(ch-1)*10.5
    put(f'J{ch+10}',x,43,90)
    put(f'Q{ch}',x-1,54)
    for prefix,dx,y in [(100,-1,60),(200,-1,65),(300,1,70),(400,1,75)]:
        put(f'R{prefix+ch}',x+dx,y)
    put(f'C{100+ch}',x+1,80)
    txt(f'{ch:02d}',x,47.7,1)
    # One compact pin legend per connector, clear of the housing and adjacent header.
    txt('1:LED+ 2:LED- 3:NO 4:COM',x+4.6,39,.8,angle=90)
for n in range(4):
    txt(f'BANK {n+1} / {8*n+1:02d}-{8*n+8:02d}',83.75+84*n,88,1.3)

# Expander pairs sit behind the 16 channels they serve.
for ref,x,y in [('U1',121,100),('U5',121,123),('U4',289,100),('U6',289,123)]: put(ref,x,y)
# Supply decoupling alongside each IC's actual VDD pad (11 inputs / 9 outputs).
for cap,ic,pin in [('C2','U1','11'),('C3','U4','11'),('C4','U5','9'),('C5','U6','9')]:
    pad=next(a for a in fs[ic].Pads() if a.GetNumber()==pin)
    put(cap,p.ToMM(pad.GetPosition().x)-4.5,p.ToMM(pad.GetPosition().y),90)

# Power input, fuse and converter. Jack mouth faces the left edge.
put('J1',42.5,134,-90); put('F1',55,134,90); put('C10',65,146)
put('U2',83,132)
put('C14',78,132,90); put('C12',74,132,90); put('C13',70,127,90)
put('L1',77,122.8,90)
put('C19',85.5,127.5)
put('R9',89,132,90)
put('R10',89,137,90); put('R11',83,137); put('C18',93,137,90)
for r,x in [('C20',77),('C21',83),('C22',89),('C23',95)]: put(r,x,110,90)
put('D1',101,117,90)

# Pico USB opens at bottom edge; existing footprint antenna keepouts are preserved.
put('A1',375,144,180)
put('C1',357,159,90); put('C7',351,159,90)
put('U3',336,153); put('C6',328,153,90)
put('R1',326,140); put('R2',332,140); put('R3',338,140)

# HUB75 cable and buffer power input at bottom edge; buffers and source damping nearby.
put('J3',175,162,90); put('J4',210,164)
put('U7',181,128); put('U8',204,128)
put('C30',185,123); put('C31',208,123)
for i,ref in enumerate([f'R{n}' for n in [501,502,503,504,505,506]]): put(ref,195,128+4.5*i)
for i,ref in enumerate([f'R{n}' for n in [507,508,509,511,512,513]]): put(ref,218,128+4.5*i)
for i in range(12): put(f'R{601+i}',235+(i//6)*8,126+(i%6)*5)
put('Q34',220,116); put('R4',226,116); put('R510',232,116); put('R514',238,116)
assert placed == set(fs), ('Unplaced',sorted(set(fs)-placed))

# Mechanical items are PCB-only and explicitly excluded from schematic BOM/position files.
for i,(x,y) in enumerate([(36,36),(210,99),(384,36),(36,164),(130,164),(275,164),(345,164)],1):
    f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_3.2mm_M3')
    f.SetReference(f'H{i}'); f.SetValue('M3 / 3.2mm NPTH'); f.SetPosition(v(x,y))
    f.SetAttributes(f.GetAttributes() | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
    b.Add(f)
    f.Reference().SetVisible(True); f.Reference().SetPosition(v(x,y-4.5)); f.Reference().SetTextSize(v(1,1)); f.Reference().SetTextThickness(p.FromMM(.12))
for x1,y1,x2,y2 in [(30,30,390,30),(390,30,390,170),(390,170,30,170),(30,170,30,30)]: line(x1,y1,x2,y2)
txt('IEEE ARCADE / PLACEMENT ONLY',160,96,1.5)
txt('12V DC / CENTER +',51,145,1)
txt('5V BUCK',83,103,1)
txt('HUB75 / ABC / PIN 12 GND',184,154,1)
txt('EXT 5V',211,159,1)
txt('1:+5V 2:GND',211,156,.8)
txt('USB',357,166,1)
txt('PICO ANTENNA / KEEP CLEAR',373,111,.9)
txt('360 x 140 mm / 7 x M3 / NO ROUTING',155,103,1,layer=p.Dwgs_User)
txt('TOP ENTRY XH / UNPLUG UPWARD / PIN 1 = LED+',210,24,1.2,layer=p.Dwgs_User)

# References: avoid component courtyards, exposed pad apertures, and other references.
def rectbox(bb): return [p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]
def intersects(a,c,gap=.2): return a[0]<c[2]+gap and a[2]>c[0]-gap and a[1]<c[3]+gap and a[3]>c[1]-gap
def courtyard(f):
    shapes=[s.GetBoundingBox() for s in f.GraphicalItems() if s.GetLayer()==p.F_CrtYd]
    if not shapes: return rectbox(f.GetBoundingBox(False,False))
    boxes=[rectbox(z) for z in shapes]
    return [min(z[0] for z in boxes),min(z[1] for z in boxes),max(z[2] for z in boxes),max(z[3] for z in boxes)]
courts={f.GetReference():courtyard(f) for f in b.GetFootprints()}
obstacles=list(courts.values())
textboxes=[rectbox(t.GetBoundingBox()) for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS]
ref_fail=[]
for ref,f in sorted(fs.items()):
    f.Value().SetVisible(False)
    t=f.Reference(); t.SetVisible(True); t.SetLayer(p.F_SilkS); t.SetTextSize(v(.85,.85)); t.SetTextThickness(p.FromMM(.12)); t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T)); t.SetKeepUpright(True)
    box=courts[ref]; x=(box[0]+box[2])/2; y=(box[1]+box[3])/2
    candidates=[(x,box[1]-.9),(x,box[3]+.9),(box[2]+2,y),(box[0]-2,y)]
    candidates += [(x+dx,y+dy) for dy in [-3,3,-5,5,-7,7] for dx in [0,-3,3,-6,6]]
    for tx,ty in candidates:
        t.SetPosition(v(tx,ty)); tb=rectbox(t.GetBoundingBox())
        if tb[0]<30.5 or tb[2]>389.5 or tb[1]<30.5 or tb[3]>169.5: continue
        if any(intersects(tb,z,.18) for z in obstacles+textboxes): continue
        textboxes.append(tb); break
    else: ref_fail.append(ref)

# Four copper layers; inner plane assignments are intent only, with NO copper zones.
b.GetDesignSettings().SetCopperLayerCount(4)
p.SaveBoard(str(boardfile),b)
# Explicit symmetric nominal 1.6mm stackup, including solder mask.
s=boardfile.read_text(encoding='utf-8')
stack='''\n\t\t(stackup
            (layer "F.SilkS" (type "Top Silk Screen"))
            (layer "F.Paste" (type "Top Solder Paste"))
            (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
            (layer "F.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "In1.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 2" (type "core") (thickness 1.04) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "In2.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "B.Cu" (type "copper") (thickness 0.035))
            (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
            (layer "B.Paste" (type "Bottom Solder Paste"))
            (layer "B.SilkS" (type "Bottom Silk Screen"))
            (copper_finish "ENIG") (dielectric_constraints no)
        )'''
s=s.replace('(setup','(setup'+stack,1)
boardfile.write_text(s,encoding='utf-8')
pro=json.loads((ROOT/'IEEEArcade.kicad_pro').read_text())
rules=pro['board']['design_settings']['rules']
rules.update(min_clearance=.2,min_track_width=.2,min_copper_edge_clearance=.5,min_hole_clearance=.25,min_hole_to_hole=.25,min_silk_clearance=.15,min_via_diameter=.6,min_through_hole_diameter=.3,min_via_annular_width=.15)
base=pro['net_settings']['classes'][0].copy()
classes=[]
for name,width,clear in [('Default',.25,.2),('Power_12V',3,.25),('Power_5V',1,.25),('Power_3V3',.6,.2),('Lamp',.5,.25),('Switch',.25,.2),('Display',.25,.2),('Buck_SW',1,.25)]:
    c=base.copy(); c.update(name=name,track_width=width,clearance=clear,via_diameter=.7,via_drill=.3,priority=len(classes)); classes.append(c)
pro['net_settings']['classes']=classes
patterns=[('+12V','Power_12V'),('Net-(F1-Pad1)','Power_12V'),('+5V','Power_5V'),('+5V_DISPLAY','Power_5V'),('Net-(A1-VSYS)','Power_5V'),('+3V3','Power_3V3'),('GND','Power_5V'),('SW_*','Switch'),('LAMP_*','Lamp'),('DISP_*','Display'),('Net-(U2-SW)','Buck_SW')]
patterns += [(f'Net-(J{n}-Pin_2)','Lamp') for n in range(11,43)]
patterns += [(f'Net-(J{n}-Pin_3)','Switch') for n in range(11,43)]
pro['net_settings']['netclass_patterns']=[{'netclass':c,'pattern':n} for n,c in patterns]
(ROOT/'IEEEArcade.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
check=p.LoadBoard(str(boardfile))
assert len(check.GetTracks())==0 and len(check.Zones())==0
assert check.GetDesignSettings().GetCopperLayerCount()==4
for f in check.GetFootprints():
    if f.GetReference() not in comps: continue
    for pad in f.Pads():
        if (f.GetReference(),pad.GetNumber()) in expected:
            assert pad.GetNetname()==expected[(f.GetReference(),pad.GetNumber())]
assert sch_hashes == {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.glob('*.kicad_sch')}
(ROOT/'Review/placement-footprint-audit.json').write_text(json.dumps(audit,indent=2))
summary={'schematic_components':len(comps),'pcb_footprints':len(check.GetFootprints()),'schematic_pad_net_assignments':len(expected),'tracks':len(check.GetTracks()),'board_copper_zones':len(check.Zones()),'copper_layers':4,'reference_placement_needs_review':ref_fail,'schematic_hashes':sch_hashes}
(ROOT/'Review/placement-verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
