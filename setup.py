"""
One-step setup: regenerates stock_master_db.json, symbol_map.json, and
display_name_map.json from app_source.jsx. Run this ONCE at the start of
any bulk-holdings-update task, right after pulling app_source.jsx.

Usage:
    python3 dev-tools/setup.py /path/to/app_source.jsx
    (writes the 3 JSON files into the same directory as this script)
"""
import re, json, os, sys

def extract_obj(content, name):
    m = re.search(r'(?:const|var)\s+' + name + r'\s*=\s*\{', content)
    if not m:
        return {}
    start = m.end()
    depth = 1; i = start; in_str = False; q = None; esc = False
    while i < len(content) and depth > 0:
        c = content[i]
        if in_str:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == q: in_str = False
        else:
            if c in ('"', "'"): in_str = True; q = c
            elif c == '{': depth += 1
            elif c == '}': depth -= 1
        i += 1
    body = content[start:i-1]
    pairs = re.findall(r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"', body)
    return {k: v for k, v in pairs}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 setup.py /path/to/app_source.jsx")
        sys.exit(1)

    src_path = sys.argv[1]
    out_dir = os.path.dirname(os.path.abspath(__file__))

    with open(src_path) as f:
        content = f.read()

    tables = {
        'stock_master_db.json': extract_obj(content, 'STOCK_MASTER_DB'),
        'symbol_map.json': extract_obj(content, 'SYMBOL_MAP'),
        'display_name_map.json': extract_obj(content, 'DISPLAY_NAME_MAP'),
    }

    for fname, data in tables.items():
        with open(os.path.join(out_dir, fname), 'w') as f:
            json.dump(data, f)
        print(f"{fname}: {len(data)} entries")

    print("\nSetup complete. holdings_helper.py can now be imported.")
