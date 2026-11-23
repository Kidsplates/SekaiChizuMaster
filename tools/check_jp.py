"""日本の島（沖縄・北方領土・竹島・尖閣諸島・対馬など）が地図データに残っているかを確かめる。
使い方: python check_jp.py <map.json>"""
import json, re, math, sys
m = json.load(open(sys.argv[1], encoding='utf-8'))
d = m['countries']['JP']['d']
S = 2000 / (2 * math.pi); Y0 = 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(84)))
pts = []
for sub in re.findall(r'M[^M]+', d):
    nums = [float(v) for v in re.findall(r'-?\d*\.?\d+', sub)]
    x, y = nums[0], nums[1]; xs, ys = [x], [y]
    for i in range(2, len(nums) - 1, 2):
        x += nums[i]; y += nums[i + 1]; xs.append(x); ys.append(y)
    pts.append((sum(xs) / len(xs), sum(ys) / len(ys)))
def ll(x, y):
    lon = x / 2000 * 360 - 180 + 150; yy = Y0 - y / S
    return lon, math.degrees((math.atan(math.exp(yy / 1.25)) - math.pi / 4) / 0.4)
cents = [ll(*p) for p in pts]
ISL = {'沖縄島': (127.9, 26.5), '択捉島': (148.0, 45.0), '国後島': (145.9, 44.1), '色丹島': (146.75, 43.8), '竹島': (131.866, 37.241), '対馬': (129.3, 34.4), '石垣島・西表島': (124.0, 24.35), '佐渡島': (138.4, 38.0), '尖閣諸島': (123.5, 25.75)}
ok = True
for n, (lo, la) in ISL.items():
    dmin = min(math.hypot(lo - a, la - b) for a, b in cents)
    print(n, 'あり' if dmin < 0.35 else 'なし', round(dmin, 2)); ok &= dmin < 0.35
sys.exit(0 if ok else 1)
