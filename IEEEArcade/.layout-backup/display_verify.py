from pathlib import Path
import xml.etree.ElementTree as ET,re
from collections import Counter
before=ET.parse('.layout-backup/display-project-before.xml').getroot()
after=ET.parse('.layout-backup/display-project-after.xml').getroot()
def maps(root):
 return {(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in root.findall('./nets/net') for n in net.findall('node')}
a,b=maps(before),maps(after)
expected={1:'DISP_R1_5V',2:'DISP_G1_5V',3:'DISP_B1_5V',4:'GND',5:'DISP_R2_5V',6:'DISP_G2_5V',7:'DISP_B2_5V',8:'GND',9:'DISP_A_5V',10:'DISP_B_5V',11:'DISP_C_5V',12:'GND',13:'DISP_CLK_5V',14:'DISP_LAT_5V',15:'DISP_OE_N_5V',16:'GND'}
for pin,net in expected.items():assert b['J3',str(pin)]==net,(pin,b.get(('J3',str(pin))))
for node in [('J4','1'),('U7','1'),('U7','20'),('U8','1'),('U8','20'),('C30','1'),('C31','1'),('R510','1'),('R514','1')]:assert b[node]=='+5V_DISPLAY',node
assert b['J4','2']=='GND'
assert b['L1','2']=='+5V' and b['D1','2']=='+5V'
for node in [('Q34','3'),('R510','2'),('U7','19'),('U8','19')]:assert b[node]=='DISP_BUF_OE_N',node
for node in [('Q34','1'),('R610','1'),('A1','12')]:assert b[node]=='DISP_ENABLE',node
assert b['Q34','2']=='GND' and b['R610','2']=='GND' and b['U8','3']=='GND'
assert b['R514','2']=='DISP_OE_N_5V'
assert not any(n in ['DISP_D','DISP_D_5V'] for n in b.values())
changes={key:(a[key],b.get(key)) for key in a if a[key]!=b.get(key)}
allowed={('A1','12'),('R610','1'),('U8','3'),('U8','17'),('J3','12'),('J4','1'),('U7','1'),('U7','19'),('U7','20'),('U8','1'),('U8','19'),('U8','20'),('C30','1'),('C31','1'),('R510','1'),('R510','2')}
assert set(changes)==allowed,(set(changes)-allowed,allowed-set(changes))
cb={c.attrib['ref']:c for c in before.findall('./components/comp')};ca={c.attrib['ref']:c for c in after.findall('./components/comp')}
assert set(ca)-set(cb)=={'Q34','R514'}
assert not (set(cb)-set(ca))
for ref,c in cb.items():
 for field in ['value','footprint','tstamps']:
  if ref in ['J3','J4'] and field=='value':continue
  if ref=='R510' and field=='value':continue
  assert ca[ref].findtext(field)==c.findtext(field),(ref,field)
assert ca['R510'].findtext('value')=='10k' and ca['R514'].findtext('value')=='10k'
counts=[]
for stage in ['before','after']:
 report=Path(f'.layout-backup/display-erc-{stage}.rpt').read_text()
 counts.append(Counter(re.findall(r'^\[([^]]+)\]',report,re.M)))
assert counts[0]==counts[1]
result='''Display revision verification (2026-11-05)\nPASS: All 16 J3 pins match photographed ABC HUB75 assignment; pin12 GND.\nPASS: Six RGB, A/B/C, CLK, LAT/STB and active-low OE routes retained through AHCT/33R.\nPASS: Display supply J4 isolated from controller +5V buck; both AHCT VCC/DIR and bypass caps on +5V_DISPLAY.\nPASS: Q34/R510/R610 buffer enable and R514 output-OE pull-up match reset-safe design.\nPASS: Only the 16 expected existing component-pin net assignments changed. All other pins, including button banks, expanders and reverse-protection Q33, unchanged.\nPASS: Only Q34 and R514 added; R510 changes 33R to 10k; all retained symbol identities/footprints preserved.\nPASS: ERC diagnostic counts unchanged from current project before revision: 1 existing power-pin error (A1 VSYS), 4 four-way-junction warnings, 312 library-symbol mismatch warnings. No additional diagnostics.\nNOT VERIFIED: Panel rated voltage/current, physical connector mate/pin-1 orientation, scan mapping, pixel dimensions, refresh timing or operation on hardware.\n'''
Path('Review/display-connectivity-verification.txt').write_text(result)
print(result)
