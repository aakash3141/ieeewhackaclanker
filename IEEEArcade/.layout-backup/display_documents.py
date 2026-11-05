from pathlib import Path
import csv,json,re,html
p=Path('Review/BOM-mating-parts.json');parts=json.loads(p.read_text(encoding='utf-8-sig'))
for row in parts:
 if row['Reference']=='H33':
  row['Value']='2-way external display-supply branch housing'
  row['Verification']='Verified XH mate for J4, the low-current external 5V INPUT for AHCT buffers. Does not mate to the panel power header; direct panel power harness is separate.'
 if row['Reference']=='T1-T130':row['Verification']=row['Verification'].replace('2 display-power wires','2 buffer-supply branch wires')
 if row['Reference']=='DISP1':
  row['Verification']='User photos identify HUB75 ABC signal interface; pin12 GND, STB=LAT, active-low OE. Separate VCC/GND power header shown. Rated voltage/current, exact mate, dimensions and scan mapping still unverified. See DISPLAY_WIRING.md.'
parts.append({'Reference':'PS2','Quantity':'1','Value':'External regulated display supply / nominal 5V','Manufacturer':'To be selected after panel rating confirmation','MPN':'Not selected','DigiKey':'Not selected','DigiKey URL':'','Datasheet':'','Footprint':'N/A - external equipment','Assembly':'Direct high-current harness to panel VCC/GND; low-current branch to J4 pins 1/2; common ground','Verification':'Voltage/current not proven by photos. Confirm panel rating and worst-case current before selecting supply and harness. Do not power panel through J4, J3 or controller buck.'})
p.write_text(json.dumps(parts,indent=2)+'\n')
rows=list(csv.DictReader(Path('Review/BOM-schematic.csv').open(newline='',encoding='utf-8-sig')))
e=lambda x:html.escape(str(x or ''),quote=True)
def link(url,title):return f'<a href="{e(url)}" target="_blank" rel="noreferrer">{e(title)}</a>' if url else e(title or 'Not available')
def rowhtml(r):
 return '<tr class="part"><td>'+e(r['Reference'])+'<small>Qty: '+e(r['Quantity'])+'</small></td><td>'+e(r['Value'])+'<small>'+e(r['Manufacturer'])+'</small><b>'+e(r['MPN'])+'</b></td><td>'+link(r['DigiKey URL'],r['DigiKey'])+'</td><td>'+e(r['Footprint'])+'<small>'+e(r['Assembly'])+'</small></td><td>'+e(r['Verification'])+'<small>'+link(r['Datasheet'],'Manufacturer datasheet / product source')+'</small></td></tr>'
p=Path('Review/BOM.html');s=p.read_text();first=s.index('<tr class="part">');last=s.index('</tbody>',first)
s=s[:first]+'\n'.join(rowhtml(r) for r in rows+parts)+'\n'+s[last:]
s=re.sub(r'<p class="note">.*?</p>','<p class="note"><b>Display revision:</b> photo-matched HUB75 ABC; pin12 is GND. Q34/R514 added; R510 is now 10k. J4 is an external buffer-supply INPUT; the panel needs a separate direct power harness. Confirm panel voltage/current and power connector. See <a href="DISPLAY_WIRING.md">display wiring and remaining checks</a>. Procurement stock statements retain their original check dates; no parts ordered.</p>',s,count=1)
p.write_text(s)
p=Path('Review/DESIGN_REVIEW.md');s=p.read_text();s=s.replace('drives a provisional external scoreboard connector','drives a photo-matched HUB75 ABC scoreboard interface').replace('the provisional external connector','the photo-matched external connector')
s=re.sub(r'\* U7/U8 SN74AHCT245N,.*?(?=\n\n)', '* U7/U8 SN74AHCT245N translate 3.3 V Pico outputs to 5 V HUB75 signals. They now use the separate external +5V_DISPLAY supply. Twelve signal paths retain 33-ohm damping resistors; pin12 is grounded. GP9 controls the buffer enables through Q34; R510 is now a 10k disable pull-up and new R514 keeps panel OE inactive during reset. See [DISPLAY_WIRING.md](DISPLAY_WIRING.md).',s,count=1)
s=s.replace('| Display | up to 1.2 A at 5 V |','| Display | Separate external supply; rating/current to be confirmed. No panel load on controller buck. |')
s=re.sub(r'The stated BOM adapter is 12 V / 60 W.*?(?=\n\n)', 'The stated BOM adapter is 12 V / 60 W (nominal 5 A). Lamp current and actual adapter ratings still require confirmation. The display is now powered by a separate external regulated supply, with a direct panel harness and common GND; the prior 1.2 A controller-buck display allowance is retired. Its supply capacity must be selected from the actual panel rating and measured load.',s,count=1)
start=s.index('### Provisional scoreboard interface');end=s.index('## Footprints, source limitations',start)
s=s[:start]+'''### Photo-matched scoreboard interface

The user-supplied rear photos show a HUB75 RGB header with A/B/C addressing, **pin12 GND**, STB/LAT and active-low OE, plus a separate VCC/GND power header. The signal wiring is now matched to this evidence. Voltage/current, exact power mate, input pin-1 orientation and pixel/scan mapping still need confirmation. Full pin table, power harness and firmware sequence: [DISPLAY_WIRING.md](DISPLAY_WIRING.md).

No additional I2C expander or separate display-driver IC is needed. Retained AHCT buffers and the Pico PIO provide twelve signals; GP9 enables buffers after setup. J4 is now an external +5V_DISPLAY INPUT for the buffers only, isolated from the board +5V buck. Power the panel directly from the same external display supply and share GND.

'''+s[end:]
s=s.replace('Panel protocol/power/connectors and adapter model/plug/polarity require actual hardware check.','Photos identify the HUB75 ABC protocol and signal pinout. Panel voltage/current, physical mating orientation, power connector, scan mapping and adapter model/plug/polarity require hardware checks.')
s=s.replace('The display-end connector and IDC panel mate remain conditional on the actual panel.','The display power mate remains unidentified; J3 signal mapping follows the photos, with physical pin-1 orientation still to be checked.')
s=re.sub(r'Final native KiCad10\.0\.6 ERC:.*?(?=\n\n)', 'The display revision was checked against the current saved project before editing: both runs have 317 ERC findings (1 existing A1 VSYS power-pin error, 4 junction warnings and 312 library-symbol mismatch warnings). No additional findings were introduced. The earlier zero-message ERC-final files are historical. Current report: ERC-display.rpt. Netlist assertions and unchanged non-display connectivity: display-connectivity-verification.txt. The native BOM and PDF have been regenerated for the display revision; the earlier 324-reference claim no longer describes this revision.',s,count=1)
p.write_text(s)
p=Path('Review/connectivity-verification.txt');s=p.read_text();s='Historical verification from the earlier schematic revision. Current display revision: see display-connectivity-verification.txt, ERC-display.rpt and DISPLAY_WIRING.md.\n\n'+s;p.write_text(s)
print('Updated BOM, assembly notes and review; added external supply placeholder without inventing a rating or connector mate.')
