import json
import glob
import os
from collections import Counter

drug_refs = Counter()
for f in glob.glob('data/knowledge_graph/formulas/*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        for c in data.get('composition', []):
            drug_refs[c.get('drug_id')] += 1
    except Exception as e:
        print(f'ERR {f}: {e}')

print('Top drug references in formulas:')
for k, v in drug_refs.most_common(20):
    print(f'  {k}: {v}')
print(f'Total unique drug refs: {len(drug_refs)}')

existing = set()
for f in glob.glob('data/knowledge_graph/drugs/*.json'):
    base = os.path.basename(f)
    parts = base.split('_')
    if parts:
        existing.add(parts[0])

missing = set(drug_refs.keys()) - existing
print(f'Existing drugs: {len(existing)}')
print(f'Missing drugs: {len(missing)}')
if missing:
    print('Missing list:')
    for d in sorted(missing):
        print(f'  {d}: {drug_refs[d]}')
