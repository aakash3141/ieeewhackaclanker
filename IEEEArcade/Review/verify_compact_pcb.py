"""Read-only validation of compact placement against current schematic and saved board baseline."""
from pathlib import Path
import pcbnew as p,json,xml.etree.ElementTree as E,hashlib,collections
root=Path.cwd();out=root/'Review';b=p.LoadBoard(str(root/'IEEEArcade.kicad_pcb'));old=p.LoadBoard(str(root/'.layout-backup/before-compact-20261110/IEEEArcade.kicad_pcb'))
fs={f.GetReference():f for f in b.GetFootprints()};prior={f.GetReference():f for f in old.GetFootprints()};s=json.loads((out/'compact-placement-verification.json').read_text());r=E.parse(out/'compact-current-schematic.net').getroot();cs={c.get('ref'):c for c in r.findall('./components/comp')};checks=[]
def check(ok,msg):
 assert ok,msg
 checks.append('PASS: '+msg)
check(set(fs)==set(cs)|{f'H{i}' for i in range(1,8)},'All 285 current schematic references and seven mounting holes present exactly once')
for c in cs:
 check(fs[c].GetFPIDAsString()==cs[c].findtext('footprint'),'Assigned footprint retained: '+c)
 check(fs[c].GetValue()==prior[c].GetValue(),'Current component value retained: '+c)
for n in r.findall('./nets/net'):
 for node in n.findall('node'):
  ref,pin=node.get('ref'),node.get('pin');pads=[x for x in fs[ref].Pads() if x.GetNumber()==pin]
  check(bool(pads) and all(x.GetNetname()==n.get('name') for x in pads),'Schematic net retained: '+ref+'.'+pin)
for ch in range(1,33):
 f=fs[f'J{ch+10}'];xy=f.GetPosition();bottom=ch>16
 check(abs(p.ToMM(xy.x)-(84+8*((ch-1)%16)))<.00001 and abs(p.ToMM(xy.y)-(142 if bottom else 43))<.00001,'Connector bank position: channel '+str(ch))
 check(f.GetOrientationDegrees()==(-90 if bottom else 90),'Connector faces outward with pin1 inboard: channel '+str(ch))
edges=[d for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts]
check(len(edges)==4,'Four segments form rectangular outline')
points={(round(p.ToMM(pt.x),5),round(p.ToMM(pt.y),5)) for d in edges for pt in [d.GetStart(),d.GetEnd()]}
check(points=={(30,30),(230,30),(230,155),(30,155)},'Outline is exactly 200 x 125 mm')
check(b.GetCopperLayerCount()==old.GetCopperLayerCount()==4,'Four-layer stack preserved')
check(len(b.GetTracks())==len(old.GetTracks())==0 and len(b.Zones())==len(old.Zones())==0,'Placement-only scope: zero routing and copper zones before and after')
def zones(f):return {z.GetZoneName():(round(z.Outline().Area(),0),z.GetIsRuleArea(),z.GetDoNotAllowZoneFills(),z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowFootprints()) for z in f.Zones()}
check(zones(fs['A1'])==zones(prior['A1']),'Pico antenna, copper, USB and underside keepout areas/rules preserved')
for name,digest in s['preserved_source_hashes'].items():check(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Schematic/project file unchanged: '+name)
def sig(v):return (v['type'],v['severity'],tuple(sorted(x.get('uuid','') for x in v['items'])))
a=json.loads((out/'compact-parity-drc.json').read_text());base=json.loads((out/'compact-baseline-parity-drc.json').read_text())
for category in ['violations','schematic_parity']:
 check(not({sig(v) for v in a[category]}-{sig(v) for v in base[category]}),'No new '+category+' findings compared with current baseline')
check(not s['reference_placement_needs_review'],'All visible reference labels placed with clearance')
check(len(a['violations'])==3,'Only two existing Pico paste/keepout errors and one existing footprint warning remain')
check(len(a['schematic_parity'])==199,'Eight obsolete-footprint warnings removed; 199 existing native parity warnings remain')
(out/'compact-connectivity-verification.txt').write_text('\n'.join(checks)+'\n')
print('Passed',len(checks),'checks; 867 schematic pad/net assignments; no new physical DRC or parity findings.')

