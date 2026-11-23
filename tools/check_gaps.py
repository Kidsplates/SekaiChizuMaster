"""地図に穴（どの国・地域にも入っていない陸地）がないかを確かめる。
ふつうの版の Natural Earth の陸地と、prep_map.py が作った国・国でない地域・しま模様の地域を比べる。
使い方: python check_gaps.py <ne_10m_admin_0_countries.geojson（ふつうの版）> <prep.geojson> <disputed.geojson（prep_map.py が書き出したもの）>
"""
import json, sys
from shapely.geometry import shape
from shapely.ops import unary_union
def U(fn):
    return unary_union([shape(f['geometry']).buffer(0) for f in json.load(open(fn, encoding='utf-8'))['features']
                        if f['geometry'] and f['properties'].get('ADM0_A3') != 'ATA'])
land = U(sys.argv[1])
ours = unary_union([U(sys.argv[2]), U(sys.argv[3])])
gap = land.difference(ours.buffer(0.01))
parts = [p for p in getattr(gap, 'geoms', [gap]) if p.area > 0.002]
for p in sorted(parts, key=lambda p: -p.area):
    print('穴', round(p.area, 4), [round(v, 2) for v in p.bounds])
print('穴の数', len(parts))
sys.exit(1 if parts else 0)
