"""国の情報の文に、ふりがなを「漢字[かな]」の形で付ける（build.py から使う）。
MeCab（fugashi + unidic-lite）で読みを出す。読みを間違えやすい言葉は furigana_fix.txt で直す。
（furigana_fix.txt の右側は、かなだけなら言葉ぜんたいのふりがな、「[」をふくむならそのまま使う）
"""
import os, re
import fugashi

here = os.path.dirname(os.path.abspath(__file__))
_tagger = fugashi.Tagger()
FIX = {}
for line in open(os.path.join(here, 'furigana_fix.txt'), encoding='utf-8'):
    if line.strip() and not line.startswith('#'):
        w, y = line.split()
        FIX[w] = y
_fix_re = re.compile('|'.join(sorted(map(re.escape, FIX), key=len, reverse=True))) if FIX else None
KANJI = re.compile(r'[一-鿿々]')

def kata2hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

def _word(surface, reading):
    if not KANJI.search(surface) or not reading:
        return surface
    r = kata2hira(reading)
    s = surface
    pre = suf = ''
    # 前後のかな（送りがななど）は読みから外す
    while s and r and not KANJI.match(s[-1]) and kata2hira(s[-1]) == r[-1]:
        suf = s[-1] + suf; s = s[:-1]; r = r[:-1]
    while s and r and not KANJI.match(s[0]) and kata2hira(s[0]) == r[0]:
        pre += s[0]; s = s[1:]; r = r[1:]
    if not s or not r or not all(KANJI.match(c) for c in s):
        return surface   # 漢字とかなが入りまじる言葉は付けない（まれ）
    return f'{pre}{s}[{r}]{suf}'

# 1文字の言葉で、MeCab の読みがこの文の中身（国の情報）に合わないもの
ONE = {'金': 'きん', '油': 'ゆ', '漁': 'ぎょ'}
NUM = re.compile(r'[0-9０-９万億千百]')

def _plain(text):
    out, prev = [], ''
    for w in _tagger(text):
        s, kana = w.surface, w.feature.kana or ''
        if s == '人':
            # 数のあと（3,506万人）は「にん」、民族の名前のあと（アラブ人・クルド人）は「じん」
            kana = 'にん' if prev and NUM.match(prev[-1]) else 'じん'
        elif s == '月' and prev and NUM.match(prev[-1]):
            kana = 'がつ'
        elif s in ONE:
            kana = ONE[s]
        out.append(_word(s, kana))
        prev = s
    return ''.join(out)

def furigana(text):
    if not text or not KANJI.search(text):
        return text
    if not _fix_re:
        return _plain(text)
    out, pos = [], 0
    for m in _fix_re.finditer(text):
        out.append(_plain(text[pos:m.start()]))
        y = FIX[m.group(0)]
        out.append(y if '[' in y else f'{m.group(0)}[{y}]')
        pos = m.end()
    out.append(_plain(text[pos:]))
    return ''.join(out)

if __name__ == '__main__':
    import sys
    for s in sys.argv[1:]:
        print(furigana(s))
