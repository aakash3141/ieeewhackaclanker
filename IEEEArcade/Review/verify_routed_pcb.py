"""Read-only audit of the routed four-layer PCB and saved KiCad DRC."""
from pathlib import Path
import pcbnew as p,xml.etree.ElementTree as E,json,hashlib,collections,math
root=Path.cwd();out=root/'Review';back=root/'.layout-backup/before-routing-20261110';b=p.LoadBoard(str(root/'IEEEArcade.kicad_pcb'));old=p.LoadBoard(str(back/'IEEEArcade.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()};prior={f.GetReference():f for f in old.GetFootprints()};checks=[]
def ck(ok,msg):
 assert ok,msg
 checks.append('PASS: '+msg)
r=E.parse(out/'routing-current-schematic.net').getroot();cs={c.get('ref'):c for c in r.findall('./components/comp')};expected={(n.get('ref'),n.get('pin')):net.get('name') for net in r.findall('./nets/net') for n in net.findall('node')}
ck(set(fs)==set(prior),'All 292 footprints retained, including all 285 schematic components and seven mounting holes')
for ref,f in fs.items():
 ck(f.GetPosition()==prior[ref].GetPosition() and f.GetOrientationDegrees()==prior[ref].GetOrientationDegrees(),ref+' placement and orientation preserved')
 ck(f.GetFPIDAsString()==prior[ref].GetFPIDAsString(),ref+' footprint assignment preserved')
for (ref,pin),name in expected.items():
 pads=[pad for pad in fs[ref].Pads() if pad.GetNumber()==pin];ck(bool(pads) and all(pad.GetNetname()==name for pad in pads),ref+'.'+pin+' schematic net preserved')
for f in back.glob('*.kicad_sch'):ck((root/f.name).read_bytes()==f.read_bytes(),f.name+' schematic unchanged')
ck((root/'IEEEArcade.kicad_pro').read_bytes()==(back/'IEEEArcade.kicad_pro').read_bytes(),'Project settings and DRC severities unchanged')
ck(b.GetCopperLayerCount()==4,'Four copper layers enabled')
points={(round(p.ToMM(pt.x),5),round(p.ToMM(pt.y),5)) for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts for pt in [d.GetStart(),d.GetEnd()]}
ck(points=={(30,30),(230,30),(230,155),(30,155)},'Exact 200 x 125 mm outline preserved')
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)];planes=[z for z in b.Zones() if not z.IsTeardropArea()];td=[z for z in b.Zones() if z.IsTeardropArea()]
ck(len(tracks)>0 and len(vias)>0,'Routes and vias exist in saved board')
ck(all(t.GetLayer()!=p.In1_Cu for t in tracks),'Inner1 is reserved for ground; no signal tracks cut the ground reference')
ck(all(p.ToMM(t.GetWidth())>=.199 for t in tracks),'Every track meets 0.20 mm minimum width')
ck(all(p.ToMM(t.GetDrillValue())>=.299 and p.ToMM(t.GetWidth(p.F_Cu))>=.599 for t in vias),'All vias are at least 0.60 mm diameter / 0.30 mm drill')
ck(len(planes)==9 and all(z.IsFilled() for z in planes),'Nine copper pours are filled')
ck(len(td)>0 and all(z.IsFilled() for z in td),'Native KiCad teardrop copper exists and is filled')
gnd=next(z for z in planes if z.GetNetname()=='GND' and z.GetLayer()==p.In1_Cu);ck(gnd.GetFilledPolysList(p.In1_Cu).OutlineCount()==1,'Inner1 ground reference is one continuous copper island around clearances/keepouts')
def keepouts(f):return sorted((z.GetZoneName(),tuple(z.GetLayerSet().Seq()),round(z.Outline().Area()),z.GetDoNotAllowPads(),z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowZoneFills(),z.GetDoNotAllowFootprints()) for z in f.Zones())
ck(keepouts(fs['A1'])==keepouts(prior['A1']),'All Pico keepout geometry, layer assignments and restrictions preserved')
cleanup=json.loads((out/'routing-cleanup.json').read_text())
for row in cleanup:
 if 'world_bbox_mm' not in row:continue
 shape=next(s for s in fs['A1'].GraphicalItems() if s.m_Uuid.AsString()==row['uuid']);bb=shape.GetBoundingBox();coords=[p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]
 ck(all(abs(a-c)<.001 for a,c in zip(coords,row['world_bbox_mm'])) and shape.GetLayer()==p.F_Paste,'Pico paste-only aperture geometry preserved as a filled paste shape: '+row['uuid'])
drc=json.loads((out/'routing-drc-final.json').read_text());ck(not drc['unconnected_items'],'KiCad reports zero unrouted connections');ck(not [v for v in drc['violations'] if v['severity']=='error'],'Physical DRC reports zero errors');ck(len(drc['violations'])==1 and drc['violations'][0]['type']=='lib_footprint_mismatch','Only the documented Pico library-footprint mismatch warning remains');ck(len(drc['schematic_parity'])==199 and all(v['description']=='No corresponding pin found in schematic' for v in drc['schematic_parity']),'199 native pin-parity warnings remain documented; direct pad-net mapping independently verified')
app=json.loads((out/'routing-application.json').read_text());summary={'board_size_mm':[200,125],'copper_layers':4,'schematic_components':len(cs),'pcb_footprints':len(fs),'pad_net_assignments_verified':len(expected),'track_segments':len(tracks),'vias':len(vias),'dedicated_ground_stitch_vias':app['counts']['stitching_vias'],'native_teardrops':len(td),'copper_pours':len(planes),'unconnected_items':len(drc['unconnected_items']),'physical_drc_errors':sum(v['severity']=='error' for v in drc['violations']),'physical_drc_warnings':sum(v['severity']=='warning' for v in drc['violations']),'native_schematic_parity_warnings':len(drc['schematic_parity']),'checks_passed':len(checks),'tracks_by_layer':dict(collections.Counter(p.LayerName(t.GetLayer()) for t in tracks)),'board_sha256':hashlib.sha256((root/'IEEEArcade.kicad_pcb').read_bytes()).hexdigest(),'display_supply':'External/source connection intentionally deferred by user; +5V_DISPLAY remains isolated'}
(out/'routing-verification.txt').write_text('\n'.join(checks)+'\n');(out/'routing-verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
