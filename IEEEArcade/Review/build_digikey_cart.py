"""Build one-board purchasing files directly from the saved PCB properties."""
import csv
import html
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from schematic_tools import parse, prop

ROOT = Path(__file__).resolve().parent
pcb = parse((ROOT.parent / 'IEEEArcade.kicad_pcb').read_text(encoding='utf-8'))
groups = defaultdict(list)
excluded = []
for fp in pcb.children('footprint'):
    ref = prop(fp, 'Reference')
    attr = fp.child('attr')
    if attr and any(x in attr.items for x in ('exclude_from_bom', 'dnp', 'board_only')):
        excluded.append(ref)
        continue
    part = prop(fp, 'DigiKey')
    if not part:
        raise ValueError(f'Missing DigiKey number: {ref}')
    groups[part].append(fp)

rows = []
for part, fps in sorted(groups.items()):
    assert len({prop(fp, 'MPN') for fp in fps}) == 1
    rows.append({'DigiKey Part Number': part, 'Quantity': len(fps),
                 'Customer Reference': ','.join(sorted(prop(fp, 'Reference') for fp in fps)),
                 'MPN': prop(fps[0], 'MPN'), 'Value': prop(fps[0], 'Value'),
                 'Product URL': prop(fps[0], 'DigiKey URL'),
                 'Verification': prop(fps[0], 'Verification') or ''})

def write_csv(name, data, fields):
    with (ROOT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)

fields = ['DigiKey Part Number', 'Quantity', 'Customer Reference']
netfile = ROOT / 'DigiKey-current-schematic.net'
if netfile.exists():
    schematic = ET.parse(netfile).findall('./components/comp')
    board_parts = {prop(fp, 'Reference'): part for part, fps in groups.items() for fp in fps}
    sch_parts = {c.attrib['ref']: next(p.attrib['value'] for p in c.findall('property') if p.attrib['name'] == 'DigiKey') for c in schematic}
    assert board_parts == sch_parts, 'Current schematic and PCB part assignments differ'
write_csv('DigiKey-board-cart.csv', rows, fields)
write_csv('DigiKey-board-details.csv', rows, list(rows[0]))
mates = json.loads((ROOT / 'BOM-mating-parts.json').read_text(encoding='utf-8-sig'))
optional = [{'DigiKey Part Number': m['DigiKey'], 'Quantity': int(m['Quantity'].split()[0]),
             'Customer Reference': m['Reference'], 'MPN': m['MPN'],
             'Value': m['Value'], 'Product URL': m['DigiKey URL'],
             'Verification': m['Verification']} for m in mates if m.get('DigiKey') and m['DigiKey'].endswith('-ND')]
write_csv('DigiKey-optional-harness.csv', optional, list(rows[0]))

base = 'https://www.digikey.com/classic/ordering/fastadd.aspx'
def link(data):
    args = []
    for i, row in enumerate(data, 1):
        args += [(f'part{i}', row['DigiKey Part Number']), (f'qty{i}', row['Quantity'])]
    return base + '?' + urlencode(args)

# GET links stay below DigiKey's documented ~1700-character limit.
batches, batch = [], []
for row in rows:
    if len(link(batch + [row])) > 1650:
        batches.append(batch)
        batch = []
    batch.append(row)
if batch:
    batches.append(batch)
links = [link(b) for b in batches]
(ROOT / 'DigiKey-cart-links.txt').write_text('\n'.join(links) + '\n', encoding='utf-8')

e = lambda value: html.escape(str(value), quote=True)
def table(data):
    return '<table><tr><th>Qty</th><th>Part</th><th>Value</th><th>References</th></tr>' + ''.join(
        f'<tr><td>{r["Quantity"]}</td><td><a href="{e(r["Product URL"])}">{e(r["DigiKey Part Number"])}</a></td><td>{e(r["Value"])}</td><td>{e(r["Customer Reference"])}</td></tr>' for r in data) + '</table>'
def form(data, label):
    inputs = ''.join(f'<input type="hidden" name="{key}{i}" value="{e(value)}">'
                     for i, r in enumerate(data, 1)
                     for key, value in [('part', r['DigiKey Part Number']), ('qty', r['Quantity']), ('cref', r['Customer Reference'])])
    return f'<form action="{base}" method="post" target="_blank">{inputs}<button>{e(label)}</button></form>'

page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>IEEEArcade DigiKey cart</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:9px;border-bottom:1px solid #ddd}}button{{padding:14px 22px;background:#b00;color:white;border:0;font-size:18px;cursor:pointer}}td:last-child{{font-size:12px;overflow-wrap:anywhere;max-width:450px}}</style>
<h1>IEEEArcade: one-board DigiKey cart</h1>
<p>{len(rows)} unique order lines, {sum(r['Quantity'] for r in rows)} board components. Exact quantities; no spares. Generated from saved PCB properties on 2026-11-10. Excludes {len(excluded)} non-BOM mounting footprints.</p>
<p>The button sends this parts list to DigiKey in your browser and adds it to your current cart. Click once to avoid duplicate quantities. No order is placed. Pricing, stock and minimum quantities have not been verified for every line; review DigiKey's results before checkout.</p>
{form(rows, 'Add all board components to DigiKey cart')}
<p>If the button fails, use these GET links once each: {" ".join(f'<a href="{e(url)}" target="_blank">Board batch {i}</a>' for i, url in enumerate(links, 1))}. Alternatively upload DigiKey-board-cart.csv and map part number, quantity and customer reference.</p>
{table(rows)}
<h2>Optional cable-side parts from historical harness BOM</h2><p>Separate from the board cart. These are original project harness quantities, not validated against the latest wiring. In particular, the XHP-2 branch housing refers to J4 from an older revision; J4 is absent from the current PCB. Inspect details and compatibility notes in DigiKey-optional-harness.csv before adding. Crimping spares are not included.</p>
{form(optional, 'Add optional cable-side parts')}{table(optional)}
<h2>Scope and existing open checks</h2>
<p>External arcade buttons, display, power adapters, cabinet wiring, tools and mounting hardware are outside the board cart. F1 includes its holder and preloaded fuse. A1 is the bare Pico 2 W module for soldering to the PCB. The historical design review flags J1 barrel-jack mechanical dimensions for confirmation and leaves the display supply and panel-side power connector unselected.</p>
<p><a href="https://forum.digikey.com/t/digikey-fastadd-bulk-add-parts-into-a-digikey-cart-via-third-party-tooling-and-urls/61356/1">DigiKey FastAdd documentation</a></p></html>'''
(ROOT / 'DigiKey-cart.html').write_text(page, encoding='utf-8')
print(json.dumps({'order_lines': len(rows), 'components': sum(r['Quantity'] for r in rows),
                  'excluded': excluded, 'batch_url_lengths': [len(x) for x in links],
                  'parts': [{k: r[k] for k in fields[:2]} for r in rows]}, indent=2))
