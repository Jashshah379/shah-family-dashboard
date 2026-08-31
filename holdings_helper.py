"""
Reusable holdings-processing toolkit.
Loads STOCK_MASTER_DB / SYMBOL_MAP / DISPLAY_NAME_MAP from small JSON files
(extracted once from app_source.jsx) instead of ever re-parsing or printing
the giant source objects again.
"""
import csv, json, re, os

_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_DIR, 'stock_master_db.json')) as f:
    STOCK_DB = json.load(f)
with open(os.path.join(_DIR, 'symbol_map.json')) as f:
    SYMBOL_MAP = json.load(f)
with open(os.path.join(_DIR, 'display_name_map.json')) as f:
    DISPLAY_MAP = json.load(f)

STOCK_DB_CI = {k.upper().strip(): v for k, v in STOCK_DB.items()}
SYMBOL_MAP_CI = {k.upper().strip(): v for k, v in SYMBOL_MAP.items()}

# Manual overrides accumulated this session for names the auto-tables miss —
# add to this dict as new unresolved names are found, so future runs benefit.
MANUAL_OVERRIDES = {
    "SAMBHV STEEL TUBES LIMITE": ("Sambhv Steel Tubes", "SAMBHV"),
    "SAAKSHI MEDTEC N PANELS L": ("Saakshi Medtech And Panels", "SAAKSHI"),
    "JUPITER BIOSCIENCE LTD.-": ("Jupiter Bioscience", "JUPBIO"),
    "NEXTGEN ANIMATION MEDIAA": ("Nextgen Animation", "NEXTGEN"),
    "ACCENTIA TECHNOLOGIES LTD": ("Accentia Technologies", "ACCENTIA"),
    "AUSTRAL COKE & PROJECTS L": ("Austral Coke & Projects", "AUSTRAL"),
    "CMM BROADCASTING NETWORK": ("CMM Broadcasting Network", "CMMBROAD"),
    "KINGFISHER AIRLINES LTD.": ("Kingfisher Airlines", "KFAIRLINES"),
    "RISHABHDEV TECHNOCABLE LT": ("Rishabhdev Technocable", "RISHABH"),
    "EPIC ENZYMES PHARMACEUTIC": ("Epic Enzymes Pharmaceutic", "EPICENZ"),
    "GEI INDUSTRIAL SYSTEMS LT": ("GEI Industrial Systems", "GEIIND"),
    "GALAXY MEDICARE LIMITED": ("Galaxy Medicare", "GALAXY"),
    "PREMIUM PLAST LIMITED": ("Premium Plast", "PREMIUM"),
    "GTL INFRASTRUCTURE LTD.": ("GTL Infrastructure", "GTLINFRA"),
    "DIVINE MULTIMEDIA (INDIA)": ("Divine Multimedia", "DIVINEMULTI"),
    "CHD DEVELOPERS LTD.": ("CHD Developers", "CHDDEV"),
    "CLC Industries Limited": ("CLC Industries", "CLCIND"),
    "AQUA LOGISTICS LTD": ("Aqua Logistics", "AQUALOG"),
    "ALKA DIAMOND INDUSTRIES L": ("Alka Diamond Industries", "ALKA"),
    "Augmont Enterprises Limit": ("Augmont Enterprises", "AUGMONT"),
    "SILVERLINE TECHNOLOGIES L": ("Silverline Technologies", "SILVERLINE"),
    "SOLVE PLASTIC PRODUCTS L": ("Solve Plastic Products", "SOLVAY"),
    "NAKODA LIMITED": ("Nakoda", "NAKODA"),
    "KARUTURI GLOBAL LTD.": ("Karuturi Global", "KARUTURI"),
    "KWALITY LIMITED": ("Kwality", "KWALITY"),
    "SIGRUN HOLDINGS LIMITED": ("Sigrun Holdings", "SIGRUN"),
    "CALS REFINERIES LTD.": ("Cals Refineries", "CALSREF"),
    "Bharati Defence and Infra": ("Bharati Defence and Infrastructure", "BDA"),
    "Brand Concepts Limited": ("Brand Concepts", "BCONCEPTS"),
    "IVRCL LTD": ("IVRCL", "IVRCLINFRA"),
    "ISGEC HEAVY ENGINEERING L": ("ISGEC Heavy Engineering", "ISGEC"),
    "ITI LTD.": ("ITI", "ITI"),
    "INDIAN RAILWAY CATERING A": ("IRCTC", "IRCTC"),
    "LKP Securities Limited": ("LKP Securities", "LKPSEC"),
    "LTM LIMITED": ("LTM", "LTM"),
    "MAN INFRACONSTRUCTION LTD": ("MAN Infraconstruction", "MANINFRA"),
    "MOIL LTD.": ("MOIL", "MOIL"),
    "Northern Arc Capital Ltd.": ("Northern Arc Capital", "NORTHARC"),
    "Nuvoco Vistas Corporation": ("Nuvoco Vistas", "NUVOCO"),
    "Ola Electric Mobility Lim": ("Ola Electric Mobility", "OLAELEC"),
    "PEARL GLOBAL INDUSTRIES L": ("Pearl Global Industries", "PGIL"),
    "PRAJ INDUSTRIES LTD.": ("Praj Industries", "PRAJIND"),
    "SAAKSHI MEDTEC N PANELS L": ("Saakshi Medtech And Panels", "SAAKSHI"),
    "Siemens Energy India Limi": ("Siemens Energy India", "ENRIN"),
    "SIGMA ADVANCED SYSTEMS LI": ("Sigma Advanced Systems", "SIGMAADV"),
    "Swan Corp Limited": ("Swan Corp", "SWANCORP"),
    "Syrma SGS Technology Limi": ("Syrma SGS Technology", "SYRMA"),
    "UNICHEM LABORATORIES LTD.": ("Unichem Labs", "UNICHEMLAB"),
    "VA TECH WABAG LTD.": ("VA Tech Wabag", "WABAG"),
    "WHIRLPOOL OF INDIA LTD.": ("Whirlpool India", "WHIRLPOOL"),
    "ZEE LEARN LTD.": ("Zee Learn", "ZEELEARN"),
    "HT MEDIA LIMITED": ("HT Media", "HTMEDIA"),
    "Lalithaa Jewellery Mart L": ("Lalithaa Jewellery Mart", "LALITHAA"),
    "SHILCHAR TECHNOLOGIES LTD": ("Shilchar Technologies", "SHILCTECH"),
    "WeWork India Management L": ("WeWork India Management", "WEWORK"),
    "EXCEL GLASSES LTD.": ("Excel Glasses", "EXCEL"),
    "GUJARAT LEASE FINANCING L": ("Gujarat Lease Financing", "GLFL"),
    "JIK INDUSTRIES LTD.": ("JIK Industries", "JIKIND"),
    "KSS LIMITED": ("KSS", "KSS"),
    "ASTRA MICROWAVE PRODUCTS": ("Astra Microwave Products", "ASTRAMICRO"),
    "Dev Accelerator Limited": ("Dev Accelerator", "DEVAGL"),
    "WALCHANDNAGAR INDUSTRIES": ("Walchandnagar Industries", "WALCHANNAG"),
    "Spencer's Retail Limited": ("Spencer's Retail", "SPENCERS"),
}

def resolve(raw_name):
    """Returns (canonical_name, ticker) or (raw_name, None) if unresolved."""
    key = raw_name.upper().strip()
    key_clean = re.sub(r'\s+(LTD\.?|LIMITED)\s*$', '', key).strip()
    if raw_name in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[raw_name]
    canon = STOCK_DB_CI.get(key) or STOCK_DB_CI.get(key_clean)
    ticker = SYMBOL_MAP_CI.get(key) or SYMBOL_MAP_CI.get(key_clean)
    if not ticker and canon:
        ticker = SYMBOL_MAP_CI.get(canon.upper().strip())
    if canon and ticker:
        return (canon, ticker)
    return (raw_name.strip(), None)

def parse_csv(filepath):
    """Parses the standard StockHolding.csv export format."""
    rows = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get('Scrip Name') or '').strip()
            if not name or name == 'Total':
                continue
            try:
                qty = float(r['Qty'])
                avg = float(r['Avg Cost'])
                cmp = float(r['CMP'])
                val = float(r['Mkt Val'])
                inv = float(r['Investment'])
            except (ValueError, KeyError):
                continue
            rows.append({'name': name, 'qty': qty, 'avg': avg, 'cmp': cmp, 'val': val, 'inv': inv})
    return rows

def build_entries(rows):
    """Resolves all rows, returns (entries, unresolved_names)."""
    entries = []
    unresolved = []
    for r in rows:
        canon, ticker = resolve(r['name'])
        if not ticker:
            unresolved.append(r['name'])
        unreal = r['val'] - r['inv']
        entries.append({
            's': canon, 'sym': ticker or canon.upper().replace(' ', ''),
            'qty': r['qty'], 'avg': r['avg'], 'cmp': r['cmp'],
            'val': round(r['val'], 2), 'inv': round(r['inv'], 2), 'unreal': round(unreal, 2),
        })
    return entries, unresolved

def to_js_array_body(entries):
    """Formats entries as JS object literals (one per line, no surrounding var/brackets)."""
    lines = []
    for e in entries:
        qty_str = str(int(e['qty'])) if e['qty'] == int(e['qty']) else str(e['qty'])
        lines.append(
            f'  {{s:"{e["s"]}",sym:"{e["sym"]}",qty:{qty_str},avg:{e["avg"]},cmp:{e["cmp"]},'
            f'val:{e["val"]},inv:{e["inv"]},unreal:{e["unreal"]}}},'
        )
    return '\n'.join(lines)

def totals(entries):
    return {
        'inv': round(sum(e['inv'] for e in entries), 2),
        'val': round(sum(e['val'] for e in entries), 2),
    }
