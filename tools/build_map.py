"""簡略化した GeoJSON を、太平洋が真ん中の世界地図（ミラー図法）の SVG パスにして map.json に書き出す。
使い方: python build_map.py <simp.geojson> <simp_disp.geojson> <prep.geojson> <出力 map.json>
（prep.geojson は、となりの国を調べるのに使う。簡略化する前のもの）
"""
import json, sys, math
from shapely.geometry import shape, box, Polygon, MultiPolygon, Point
from shapely.strtree import STRtree
from shapely import affinity

simp, simpd, prep, out = sys.argv[1:5]
LON0 = 150.0             # 地図の真ん中の経度（日本の教科書と同じく太平洋を真ん中に）
SEAM = LON0 - 180.0      # 地図の左右のはし（西経30度）
LAT_N, LAT_S = 84.0, -57.0
W = 2000.0
S = W / (2 * math.pi)

def my(lat):
    return 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat)))
Y0 = my(LAT_N)
H = (Y0 - my(LAT_S)) * S

def proj(lon, lat):
    lp = lon - LON0
    if lp < -180: lp += 360
    if lp > 180: lp -= 360
    lat = max(min(lat, LAT_N), LAT_S)
    return ((lp + 180) / 360 * W, (Y0 - my(lat)) * S)

LEFT = box(SEAM, -90, 180, 90)       # 経度 -30..180 → 地図の左〜右寄り
RIGHT = box(-180, -90, SEAM, 90)     # 経度 -180..-30 → 地図の右はし側
def polys(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, MultiPolygon): return list(g.geoms)
    return [p for gg in getattr(g, 'geoms', []) for p in polys(gg)]

def project_geom(g):
    rings = []   # 1つの島ごとに [外側, 穴...]
    for half, shift in ((LEFT, 0), (RIGHT, 1)):
        part = g.intersection(half)
        for p in polys(part):
            def pr(coords):
                pts = []
                for x, y in coords:
                    if shift and x >= SEAM - 1e-9: x = SEAM - 1e-6
                    if not shift and x <= SEAM + 1e-9: x = SEAM + 1e-6
                    pts.append(proj(x, y))
                return pts
            rings.append([pr(p.exterior.coords)] + [pr(i.coords) for i in p.interiors])
    return rings

def area(r):
    a = 0
    for i in range(len(r) - 1):
        a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
    return abs(a) / 2

def path(rings, sc=10):
    out = []
    for poly in rings:
        for r in poly:
            pts = [(round(x * sc), round(y * sc)) for x, y in r]
            dedup = [pts[0]]
            for p in pts[1:]:
                if p != dedup[-1]: dedup.append(p)
            if len(dedup) < 4: continue
            if dedup[-1] == dedup[0]: dedup = dedup[:-1]
            f = lambda v: fmt(v, sc)
            s = 'M%s %s' % (f(dedup[0][0]), f(dedup[0][1]))
            px, py = dedup[0]
            seq = []
            for x, y in dedup[1:]:
                seq.append(('%s %s' % (f(x - px), f(y - py))).replace(' -', '-'))
                px, py = x, y
            out.append(s + 'l' + ' '.join(seq).replace(' -', '-') + 'z')
    return ''.join(out)
def fmt(v, sc):
    s = ('%%.%df' % len(str(sc - 1))) % (v / sc)
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    if s.startswith('0.'): s = s[1:]
    if s.startswith('-0.'): s = '-' + s[2:]
    return s or '0'

TAKESHIMA = Point(131.866, 37.241)
def keep_rings(rings, kid, geo):
    if not rings: return [], 0
    rings = sorted(rings, key=lambda p: -area(p[0]))
    total = sum(area(p[0]) for p in rings)
    big = area(rings[0][0])
    kept = []
    for i, p in enumerate(rings):
        a = area(p[0])
        if i == 0 or a >= 0.35 or (total < 30 and i < 8 and a >= 0.004) or (kid == 'JP' and a >= 0.0005):
            kept.append(p)
    return kept, total

# 竹島と尖閣諸島はとても小さく簡略化で消えるので、簡略化する前の形から足す（日本の領土として描く）
pd = json.load(open(prep, encoding='utf-8'))
extra = {}
SENKAKU = box(123.3, 25.6, 124.7, 26.0)
found = {'竹島': False, '尖閣諸島': False}
for ft in pd['features']:
    if ft['properties']['id'] == 'JP':
        for p in polys(shape(ft['geometry'])):
            if p.distance(TAKESHIMA) < 0.05:
                found['竹島'] = True
            elif p.intersects(SENKAKU):
                found['尖閣諸島'] = True
            else:
                continue
            extra.setdefault('JP', []).extend(project_geom(p.simplify(0.002)))
assert all(found.values()), '元データに見つからない島: ' + str(found)

d = json.load(open(simp, encoding='utf-8'))
countries, regions = {}, []
for ft in d['features']:
    pr = ft['properties']
    if not ft['geometry']: continue
    g = shape(ft['geometry'])
    rings, total = keep_rings(project_geom(g), pr['id'], g)
    if not rings: continue
    xs = [x for p in rings for x, y in p[0]]; ys = [y for p in rings for x, y in p[0]]
    big = area(rings[0][0])
    core = [p for p in rings if area(p[0]) >= big * 0.15]
    cx = [x for p in core for x, y in p[0]]; cy = [y for p in core for x, y in p[0]]
    lx, ly = proj(pr['lx'], pr['ly'])
    rec = {'d': path(rings) + path(extra.get(pr['id'], []), 1000), 'l': [round(lx, 1), round(ly, 1)], 'a': round(total, 2),
           'b': [round(min(cx), 1), round(min(cy), 1), round(max(cx), 1), round(max(cy), 1)]}
    if pr['kind'] == 'c':
        countries[pr['id']] = rec
    else:   # 国でない地域は、小さくても捨てない（捨てると陸に穴があく）
        rec.update(id=pr['id'], n=pr['name'])
        regions.append(rec)

dd = json.load(open(simpd, encoding='utf-8'))
disputed = []
for ft in dd['features']:
    g = shape(ft['geometry'])
    rings = project_geom(g)
    disputed.append({'n': ft['properties']['name'], 'd': path(rings)})

# となりの国（陸でさかいを接する国）
ids, gs = [], []
for ft in pd['features']:
    if ft['properties']['kind'] != 'c': continue
    ids.append(ft['properties']['id']); gs.append(shape(ft['geometry']).buffer(0.02))
tree = STRtree(gs)
nb = {}
for i, g in enumerate(gs):
    nb[ids[i]] = sorted(ids[j] for j in tree.query(g) if j != i and gs[j].intersects(g))

json.dump({'W': W, 'H': round(H, 1), 'lon0': LON0, 'countries': countries, 'regions': regions,
           'disputed': disputed, 'nb': nb}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('W', W, 'H', round(H, 1), 'countries', len(countries), 'regions', len(regions))
