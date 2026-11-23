"""countries.tsv・flag_groups.txt・地図データ（build_map.py が作る map.json）を、app_template.html に埋め込んで index.html を書き出す。
使い方: python build.py <map.json> <出力 index.html>
"""
import json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
mp = json.load(open(sys.argv[1], encoding='utf-8'))

REGION_NOTE = {
    'r_TWN': '日本[にほん]が 国[くに]として みとめていない 地域[ちいき]だよ',
    'r_PRK': '日本[にほん]が 国[くに]として みとめていない 地域[ちいき]だよ',
    'r_PSX': '日本[にほん]が 国[くに]として みとめていない 地域[ちいき]だよ',
    'r_SAH': 'どこの 国[くに]の 地域[ちいき]か きまっていない ところだよ',
    'r_BRT': 'どこの 国[くに]も じぶんの 土地[とち]だと いっていない ところだよ',
    'r_GRL': 'デンマークの 一部[いちぶ]の 地域[ちいき]だよ',
    'r_KSA': '日本[にほん]の 地図[ちず]では、どこの 国[くに]の 地域[ちいき]か きまっていない ところとして かくよ',
    'r_KUR': '日本[にほん]の 地図[ちず]では、どこの 国[くに]の 地域[ちいき]か きまっていない ところとして かくよ',
}
DISP_NOTE = {
    'カシミール地方[ちほう]': 'インド・パキスタン・中国[ちゅうごく]の あいだで、さかいめを あらそっている 地域[ちいき]だよ',
    'アルナーチャル・プラデーシュ': 'インドと 中国[ちゅうごく]の あいだで、さかいめを あらそっている 地域[ちいき]だよ',
    'ハラーイブ・トライアングル': 'エジプトと スーダンの あいだで、さかいめを あらそっている 地域[ちいき]だよ',
    'イレミ・トライアングル': 'ケニアと 南[みなみ]スーダンの あいだで、さかいめを あらそっている 地域[ちいき]だよ',
    'アビエイ地域[ちいき]': 'スーダンと 南[みなみ]スーダンの あいだで、さかいめを あらそっている 地域[ちいき]だよ',
    'ゴラン高原[こうげん]': 'シリアの 土地[とち]を イスラエルが 占領[せんりょう]している 地域[ちいき]。日本[にほん]は イスラエルの ものとは みとめていないよ',
    '南[みなみ]パタゴニア氷原[ひょうげん]': 'アルゼンチンと チリの あいだで、さかいめが きまっていない ところだよ',
    'アルティガスのコーナー': 'ウルグアイと ブラジルの あいだで、さかいめを あらそっている 地域[ちいき]だよ',
}
# ふりがなが付いていない漢字に、まとめてふりがなを付ける（正式名と、国でない地域の名前）
import re
YOMI = {
    '中央': 'ちゅうおう', '中華人民共和国': 'ちゅうかじんみんきょうわこく', '人民共和国': 'じんみんきょうわこく',
    '人民民主共和国': 'じんみんみんしゅきょうわこく', '公国': 'こうこく', '共和国': 'きょうわこく', '北': 'きた',
    '協同共和国': 'きょうどうきょうわこく', '南': 'みなみ', '及': 'およ', '合衆国': 'がっしゅうこく', '国': 'こく',
    '多民族国': 'たみんぞくこく', '大公国': 'たいこうこく', '大韓民国': 'だいかんみんこく', '日本': 'にほん', '東': 'ひがし',
    '東方共和国': 'とうほうきょうわこく', '民主人民共和国': 'みんしゅじんみんきょうわこく', '民主共和国': 'みんしゅきょうわこく',
    '民主社会主義共和国': 'みんしゅしゃかいしゅぎきょうわこく', '独立国': 'どくりつこく', '王国': 'おうこく',
    '社会主義共和国': 'しゃかいしゅぎきょうわこく', '英国': 'えいこく', '諸島': 'しょとう', '諸島共和国': 'しょとうきょうわこく',
    '赤道': 'せきどう', '連合': 'れんごう', '連合共和国': 'れんごうきょうわこく', '連合王国': 'れんごうおうこく', '連邦': 'れんぽう',
    '連邦共和国': 'れんぽうきょうわこく', '連邦民主共和国': 'れんぽうみんしゅきょうわこく', '首長国連邦': 'しゅちょうこくれんぽう',
    '南極地域': 'なんきょくちいき', '合衆国領有小離島': 'がっしゅうこくりょうゆうしょうりとう', '島': 'とう', '洋地域': 'ようちいき',
    '礁': 'しょう', '米軍基地': 'べいぐんきち', '領': 'りょう', '領南方': 'りょうなんぽう',
}
def ruby(s):
    out, pos = [], 0
    for m in re.finditer(r'([\u4E00-\u9FFF々]+)(\[[^\]]+\])?', s):
        out.append(s[pos:m.start()])
        if m.group(2):
            out.append(m.group(0))
        else:
            k = m.group(1)
            if k not in YOMI:
                sys.exit('ふりがなが分からない漢字: ' + k + '（' + s + '）')
            out.append(k + '[' + YOMI[k] + ']')
        pos = m.end()
    out.append(s[pos:])
    return ''.join(out)

# 国の情報（面積・人口など）。外務省の基礎データから写したもの
from furigana import furigana
INFO = {}
for line in open(os.path.join(here, 'country_info.tsv'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    iso, area, pop, eth, lang, ind, indep, date = line.rstrip('\n').split('\t')
    area = area.replace('平方キロメートル', 'km²')
    # 日にちは読み方がむずかしいので省く（「1957年3月」まで）
    area, pop, eth, lang, ind, indep = [re.sub(r'(\d+月)\d+日', r'\1', v) for v in (area, pop, eth, lang, ind, indep)]
    INFO[iso] = {k: furigana(v) for k, v in dict(a=area, p=pop, e=eth, l=lang, d=ind, x=indep).items() if v}
    if date:
        INFO[iso]['s'] = date
review = os.environ.get('INFO_REVIEW')
if review:
    with open(review, 'w', encoding='utf-8') as f:
        for k, v in INFO.items():
            f.write(k + '\t' + '\t'.join(f'{kk}={vv}' for kk, vv in v.items()) + '\n')

countries = []
for line in open(os.path.join(here, 'countries.tsv'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    iso, n, cap, reg, tier, mark, formal, note = line.rstrip('\n').split('\t')
    g = mp['countries'][iso]
    countries.append({'id': iso, 'n': n, 'c': cap, 'r': reg, 't': int(tier),
                      'x': mark, 'f': ruby(formal), 'm': note,
                      'd': g['d'], 'l': g['l'], 'b': g['b'], 'a': g['a'], 'nb': mp['nb'].get(iso, []), 'i': INFO.get(iso, {})})
regions = [{'id': r['id'], 'n': ruby(r['n']), 'd': r['d'], 'l': r['l'], 'b': r['b'], 'm': REGION_NOTE.get(r['id'], '')} for r in mp['regions']]
disputed = [{'n': d['n'], 'd': d['d'], 'm': DISP_NOTE.get(d['n'], '')} for d in mp['disputed']]
lines = [l for l in open(os.path.join(here, 'flag_groups.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')]
groups = [l.split() for l in lines if not l.startswith('=')]
same = [l.split()[1:] for l in lines if l.startswith('=')]
known = {c['id'] for c in countries}
for gr in groups + same:
    for i in gr:
        if i not in known: print('flag_groups.txt: 収録していない国', i)
data = {'W': mp['W'], 'H': mp['H'], 'countries': countries, 'regions': regions, 'disputed': disputed, 'flagGroups': groups, 'flagSame': same}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
tpl = open(os.path.join(here, 'app_template.html'), encoding='utf-8').read()
assert '/*__WORLD_DATA__*/' in tpl
html = tpl.replace('/*__WORLD_DATA__*/', js)
open(sys.argv[2], 'w', encoding='utf-8').write(html)
print('書き出し', sys.argv[2], len(html.encode('utf-8')), 'bytes', len(countries), '国')
