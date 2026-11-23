"""Natural Earth（日本の視点の版）から、地図の元になる GeoJSON を作る。
使い方: python prep_map.py <ne_10m_admin_0_countries_jpn.geojson> <ne_10m_admin_0_disputed_areas.geojson> <出力フォルダ>
"""
import json, sys, os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

src, disp, out = sys.argv[1], sys.argv[2], sys.argv[3]
here = os.path.dirname(os.path.abspath(__file__))
iso = set()
for line in open(os.path.join(here, 'countries.tsv'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    iso.add(line.split('\t')[0])

# 国として出題しない地域のうち、中国の一部として描くもの
MERGE_INTO = {'HKG': 'CN', 'MAC': 'CN'}
DROP = {'ATA'}  # 南極大陸は描かない
# ISO コードは国と同じだが、国の本体ではない小さな地域（国とは別の地域として描く）
NOT_MAIN = {'PRK', 'CLP', 'BRI', 'IOA', 'CSI', 'ATC'}
# 国でない地域の呼び名（ふだん使う名前にする）
REGION_NAME = {'TWN': '台湾[たいわん]', 'PRK': '北朝鮮[きたちょうせん]', 'PSX': 'パレスチナ', 'SAH': '西[にし]サハラ', 'GRL': 'グリーンランド'}

d = json.load(open(src, encoding='utf-8'))
geoms, regions, labels = {}, [], {}
for f in d['features']:
    p = f['properties']
    a3 = p['ADM0_A3']
    if a3 in DROP:
        continue
    g = shape(f['geometry'])
    if not g.is_valid:
        g = g.buffer(0)
    i2 = p['ISO_A2_EH']
    if a3 in MERGE_INTO:
        geoms.setdefault(MERGE_INTO[a3], []).append(g)
    elif i2 in iso and a3 not in NOT_MAIN:
        geoms.setdefault(i2, []).append(g)
        labels[i2] = (p['LABEL_X'], p['LABEL_Y'])
    else:
        regions.append({'id': 'r_' + a3, 'name': REGION_NAME.get(a3) or p.get('NAME_JA') or p['NAME'], 'en': p['NAME'], 'g': g, 'lx': p['LABEL_X'], 'ly': p['LABEL_Y']})

# 南樺太（北緯50度より南）と千島列島（ウルップ島より北）は、日本の地図と同じく
# 「どこの国の地域か決まっていないところ」としてロシアから切り出し、灰色で描く
from shapely.geometry import box as _box
ru = unary_union(geoms['RU'])
SAKHALIN_S = _box(141.0, 45.5, 146.0, 50.0)
def _parts(g):
    return list(g.geoms) if hasattr(g, 'geoms') else [g]
south_sakhalin = ru.intersection(SAKHALIN_S)
kuril = unary_union([p for p in _parts(ru) if p.area < 1.0 and 149.0 <= p.centroid.x <= 157.0 and 45.3 <= p.centroid.y <= 51.0])
assert not south_sakhalin.is_empty and not kuril.is_empty, '南樺太・千島列島が見つからない'
geoms['RU'] = [ru.difference(SAKHALIN_S).difference(kuril)]
regions.append({'id': 'r_KSA', 'name': '南樺太[みなみからふと]', 'en': 'Southern Sakhalin', 'g': south_sakhalin,
                'lx': south_sakhalin.centroid.x, 'ly': south_sakhalin.centroid.y})
regions.append({'id': 'r_KUR', 'name': '千島列島[ちしまれっとう]（ウルップ島[とう]より北[きた]）', 'en': 'Kuril Islands (Urup and north)', 'g': kuril,
                'lx': kuril.centroid.x, 'ly': kuril.centroid.y})

missing = iso - set(geoms)
if missing:
    sys.exit('地図に見つからない国: ' + ', '.join(sorted(missing)))

feats = []
for k, gs in geoms.items():
    feats.append({'type': 'Feature', 'properties': {'id': k, 'kind': 'c', 'lx': labels[k][0], 'ly': labels[k][1]}, 'geometry': mapping(unary_union(gs))})
for r in regions:
    feats.append({'type': 'Feature', 'properties': {'id': r['id'], 'kind': 'r', 'name': r['name'], 'en': r['en'], 'lx': r['lx'], 'ly': r['ly']}, 'geometry': mapping(r['g'])})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(out, 'prep.geojson'), 'w', encoding='utf-8'), ensure_ascii=False)

# 境界に争いのあるところ（答えの場所にしない・タップの判定に使わない）
# 日本の視点の版でどの国にも入っていない陸地（ゴラン高原・南パタゴニア氷原・アルティガスのコーナー・アビエイ・イレミ）も、
# ここでしま模様にして穴にならないようにする（check_gaps.py で確かめる）
DISPUTED = {
    'カシミール': 'カシミール地方[ちほう]', 'アクサイチン': 'カシミール地方[ちほう]', 'カラコルム回廊': 'カシミール地方[ちほう]',
    'ギルギット・バルティスタン州': 'カシミール地方[ちほう]', 'アザド・カシミール': 'カシミール地方[ちほう]', 'シアチェン氷河': 'カシミール地方[ちほう]',
    'アルナーチャル・プラデーシュ州': 'アルナーチャル・プラデーシュ',
    'ハラーイブ・トライアングル': 'ハラーイブ・トライアングル',
    'イレミ・トライアングル': 'イレミ・トライアングル', 'アビエイ': 'アビエイ地域[ちいき]',
    'ゴラン高原': 'ゴラン高原[こうげん]', '国際連合兵力引き離し監視軍': 'ゴラン高原[こうげん]', 'シェバー・ファームズ': 'ゴラン高原[こうげん]',
    '南パタゴニア氷原': '南[みなみ]パタゴニア氷原[ひょうげん]', 'アルティガスのコーナー': 'アルティガスのコーナー',
}
dd = json.load(open(disp, encoding='utf-8'))
groups = {}
for f in dd['features']:
    n = f['properties'].get('NAME_JA')
    if n in DISPUTED:
        g = shape(f['geometry'])
        groups.setdefault(DISPUTED[n], []).append(g if g.is_valid else g.buffer(0))
dfe = [{'type': 'Feature', 'properties': {'id': 'd%d' % i, 'kind': 'd', 'name': n}, 'geometry': mapping(unary_union(gs))}
       for i, (n, gs) in enumerate(groups.items())]
json.dump({'type': 'FeatureCollection', 'features': dfe}, open(os.path.join(out, 'disputed.geojson'), 'w', encoding='utf-8'), ensure_ascii=False)
print('国', len(geoms), '国でない地域', len(regions), '争いのあるところ', list(groups))
