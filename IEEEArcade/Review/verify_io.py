"""Independent checks against the KiCad-exported netlist, datasheet pin maps and installed footprints."""
from pathlib import Path
import xml.etree.ElementTree as ET,json,re,collections,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
from schematic_tools import parse,prop
r=ET.parse('Review/after-io.net').getroot();before=ET.parse('Review/before-io.net').getroot()
components={c.get('ref'):c for c in r.findall('./components/comp')}
nets={n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in r.findall('./nets/net')}
pinnet={p:name for name,nodes in nets.items() for p in nodes}
checks=[]
def check(ok,message):
 assert ok,message
 checks.append('PASS: '+message)
expanders={'U1':0x20,'U4':0x23,'U5':0x21,'U6':0x22}
for ref,addr in expanders.items():
 check(components[ref].findtext('value')=='MCP23017T-E/SO',ref+' is MCP23017T-E/SO')
 for pin,net in {'9':'+3V3','10':'GND','12':'/I2C_SCL','13':'/I2C_SDA','18':'/IO_RESET_N'}.items():check(pinnet[(ref,pin)]==net,f'{ref} pin{pin} = {net}')
 actual=0x20+sum((1<<i) if pinnet[(ref,str(15+i))]=='+3V3' else 0 for i in range(3))
 check(all(pinnet[(ref,str(15+i))] in ['GND','+3V3'] for i in range(3)) and actual==addr,f'{ref} A2:A0 produce unique address {addr:#04x}')
 for pin in ['11','14','19','20']:
  check(pinnet[(ref,pin)].startswith('unconnected-') and len(nets[pinnet[(ref,pin)]])==1,f'{ref} NC/unused interrupt pin{pin} intentionally open')
for i in range(1,33):
 name=f'SW_{i:02}';nodes=nets[name];chip=[(ref,p) for ref,p in nodes if ref in expanders]
 check(len(chip)==1 and chip[0][1] not in ['8','28'],f'{name} has one input-capable MCP23017 pin')
 check(len(nodes)==3 and {ref for ref,p in nodes}=={chip[0][0],f'R{400+i}',f'C{100+i}'},f'{name} connects only expander, 1k series resistor and 10nF filter')
 check(components[f'R{400+i}'].findtext('value')=='1k' and components[f'C{100+i}'].findtext('value').startswith('10n'),f'{name} RC values retained')
 raw=pinnet[(f'J{10+i}','3')];rawnodes=nets[raw]
 check({ref for ref,p in rawnodes}=={f'J{10+i}',f'R{300+i}',f'R{400+i}'},f'{name} connector NO has dedicated pull-up and series filter')
 check(pinnet[(f'J{10+i}','4')]=='GND' and pinnet[(f'R{300+i}','1')]=='+3V3',f'{name} COM grounded, pull-up to 3.3V')
for i in range(1,31):
 name=f'LAMP_{i:02}';nodes=nets[name];chip=[x for x in nodes if x[0] in expanders]
 check(len(nodes)==2 and len(chip)==1 and any(x[0]==f'R{100+i}' for x in nodes),name+' has one expander output and one gate resistor')
 check(pinnet[(f'J{10+i}','1')]=='+12V' and pinnet[(f'J{10+i}','2')]==pinnet[(f'Q{i}','3')],name+' harness has 12V anode / MOSFET drain cathode')
 check(pinnet[(f'Q{i}','2')]=='GND',name+' MOSFET source grounded')
for name,nodes in nets.items():check(not re.search(r'(SW_\d+_FILT|LAMP_\d+_EN|LAMP_3[12](?:$|_))',name),'No obsolete channel label on '+name)
for ref in ['J41','J42']:
 for pin in ['1','2']:check(pinnet[(ref,pin)].startswith('unconnected-') and len(nets[pinnet[(ref,pin)]])==1,ref+' menu lamp pin'+pin+' disconnected')
for ref in ['Q31','Q32','R131','R132','R231','R232']:check(ref not in components,ref+' surplus menu lamp component removed')
for pin in ['7','8']:check(pinnet[('U6',pin)].startswith('unconnected-'),'U6 spare pin'+pin+' intentionally unused')
for pin,name in {'1':'GND','2':'GND','3':'GND','4':'GND','5':'/I2C_SDA','6':'/I2C_SCL','7':'GND','8':'+3V3'}.items():check(pinnet[('U3',pin)]==name,f'24LC256 U3 pin{pin} = {name}')
for ref,pin,net in [('R1','1','+3V3'),('R1','2','/I2C_SDA'),('R2','1','+3V3'),('R2','2','/I2C_SCL'),('R3','1','+3V3'),('R3','2','/IO_RESET_N')]:check(pinnet[(ref,pin)]==net,f'{ref} pin{pin} {net}')
check(components['R1'].findtext('value')==components['R2'].findtext('value')=='4.7k','I2C has one 4.7k pull-up per line')
check(components['R3'].findtext('value')=='10k','Reset has 10k pull-up')
for ref in ['C3','C4','C5','C6','C7']:check(components[ref].findtext('value')=='100n' and pinnet[(ref,'1')]=='+3V3' and pinnet[(ref,'2')]=='GND',ref+' IC bypass 100nF across 3.3V and GND')
# Compare net equivalence classes without net names, excluding deliberately modified devices.
removed={'Q31','Q32','R131','R132','R231','R232'}
def groups(root):
 result=set()
 for n in root.findall('./nets/net'):
  pts=frozenset((x.get('ref'),x.get('pin')) for x in n.findall('node') if x.get('ref') not in expanders and x.get('ref') not in removed and not (x.get('ref') in ['J41','J42'] and x.get('pin') in ['1','2']))
  if pts:result.add(pts)
 return result
check(groups(r)==groups(before),'Every retained non-expander pin has exactly the same connectivity as before (excluding menu lamp pins)')
# Check pin numbers, functions and native footprint pad numbering/geometry.
s=parse(Path('IEEEArcade.kicad_sch').read_text());libs=s.child('lib_symbols').children('symbol')
expected={'Memory_EEPROM:24LC256':{'1':'A0','2':'A1','3':'A2','4':'GND','5':'SDA','6':'SCL','7':'WP','8':'VCC'},'Interface_Expansion:MCP23017x-x-SO':{**{str(i+1):f'GPB{i}' for i in range(8)},**{str(i+21):f'GPA{i}' for i in range(8)},'9':'V_{DD}','10':'V_{SS}','11':'NC','12':'SCK','13':'SDA','14':'NC','15':'A0','16':'A1','17':'A2','18':'~{RESET}','19':'INTB','20':'INTA'}}
for name,pins in expected.items():
 lib=next(l for l in libs if l.items[1]==name);p={p.val('number'):p for sub in lib.children('symbol') for p in sub.children('pin')}
 check({n:p.val('name') for n,p in p.items()}==pins,name+' complete symbol pin functions match datasheet SOIC pinout')
 if '23017' in name:check(all(p[n].items[1]=='output' for n in ['8','28']),'MCP23017 GPB7/GPA7 are output-type pins in symbol')
for ref,count,foot,pad1,padlast in [('U3',8,'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',(-2.475,-1.905),(2.475,-1.905)),('U1',28,'Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm',(-4.65,-8.255),(4.65,-8.255))]:
 check(components[ref].findtext('footprint')==foot,ref+' assigned correct SOIC package footprint')
 lib,n=foot.split(':');fp=parse((Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')/(n+'.kicad_mod')).read_text());pads={n.items[1]:n for n in fp.children('pad')}
 check(set(pads)=={str(n) for n in range(1,count+1)},foot+' pad numbering matches symbol')
 for no,xy in [('1',pad1),(str(count),padlast)]:check(tuple(float(v) for v in pads[no].child('at').items[1:3])==xy,foot+' pad'+no+' location matches SOIC orientation/pitch')
for ref in expanders:check(components[ref].findtext('footprint')==components['U1'].findtext('footprint'),ref+' uses verified wide SOIC-28 footprint')
# No new ERC findings; compare type, severity and item UUIDs.
def erc(file):
 d=json.loads(Path(file).read_text());return [(v['type'],v['severity'],(v['description'],) if v['type']=='four_way_junction' else tuple(sorted(x['uuid'] for x in v['items']))) for sh in d['sheets'] for v in sh['violations']]
b=erc('Review/ERC-before-io.json');a=erc('Review/ERC-io.json')
check(not(set(a)-set(b)),'ERC contains no new findings relative to pre-edit baseline')
checks.append('ERC baseline: '+str(collections.Counter((x[0],x[1]) for x in b)))
checks.append('ERC revised: '+str(collections.Counter((x[0],x[1]) for x in a)))
Path('Review/io-connectivity-verification.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks[-18:]));print('Total assertions:',len(checks)-2)
