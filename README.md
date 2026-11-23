# せかいちずマスター

世界の国の場所・国旗・首都・州をおぼえる、小学生と保護者むけの地図クイズです。スマートフォンの縦画面で、タップだけで遊べます。

- 遊ぶ：[https://kidsplates.github.io/SekaiChizuMaster/](https://kidsplates.github.io/SekaiChizuMaster/)
- 出題する国：日本が承認している 195 か国と日本の 196 か国。国名・首都は外務省の表記にそろえています。
- 国でない地域（台湾・パレスチナ・西サハラ・グリーンランドなど）は灰色で描き、国としては出題しません。
- 領土は日本政府の立場で描いています（北方領土・竹島は日本）。国境に争いのある地域（カシミール地方など）は斜線で描き、答えにも当たり判定にも使いません。

## ファイル

| ファイル | 中身 |
|---|---|
| `index.html` | アプリ本体（1 ファイル）。`tools/build.py` で作るので、直接は書き換えない |
| `flags/*.svg` | 国旗（196 枚） |
| `tools/countries.tsv` | 国の一覧（国名・首都・州・むずかしさ・解説） |
| `tools/country_info.tsv` | 国の情報（面積・人口・おもな民族・言語・おもな産業・独立） |
| `tools/flag_groups.txt` | 似ている国旗の組 |
| `tools/app_template.html` | 画面のもと |
| `tools/build.py` | データを画面のもとに埋め込んで `index.html` を作る |
| `tools/prep_map.py`・`tools/build_map.py` | Natural Earth から地図のデータ（`map.json`）を作る |
| `tools/furigana.py`・`tools/furigana_fix.txt` | 国の情報にふりがなを付ける。読みを手で直す表 |
| `tools/check_jp.py`・`tools/check_gaps.py` | 日本の島が欠けていないか、地図に穴がないかを調べる |
| `tools/capitals_check.txt`・`tools/mofa_slugs.txt` | 首都を外務省の各国の基礎データと照らし合わせた記録 |

地図の元データ（Natural Earth）と途中のファイルは大きいので Git に入れていません。下の手順で作り直せます。

## 作り直す手順

使うもの：Python 3（shapely・fugashi・unidic-lite）、Node.js の mapshaper

1. Natural Earth の GitHub（nvkelso/natural-earth-vector）の `geojson/` から、次の 2 つをどこかのフォルダ（下では `work/`）に置く
   - `ne_10m_admin_0_countries_jpn.geojson`（日本の視点の版。10m にしかない）
   - `ne_10m_admin_0_disputed_areas.geojson`
   - `ne_10m_admin_0_countries.geojson`（ふつうの版。地図に穴がないかを調べるときだけ使う）
2. 地図のデータを作る

```
python tools/prep_map.py work/ne_10m_admin_0_countries_jpn.geojson work/ne_10m_admin_0_disputed_areas.geojson work
mapshaper work/prep.geojson -simplify interval=5000 keep-shapes -o work/simp.geojson
mapshaper work/disputed.geojson -simplify interval=5000 keep-shapes -o work/simp_disp.geojson
python tools/build_map.py work/simp.geojson work/simp_disp.geojson work/prep.geojson work/map.json
python tools/check_jp.py work/map.json
python tools/check_gaps.py work/ne_10m_admin_0_countries.geojson work/prep.geojson work/disputed.geojson
```

3. アプリを作る

```
python tools/build.py work/map.json index.html
```

## 出典とライセンス

- 地図：[Natural Earth](https://www.naturalearthdata.com/)（パブリックドメイン）。日本の視点の版（worldview JPN）を使い、南極は描かず、形を簡略化しています。
- 国旗：[flag-icons](https://github.com/lipis/flag-icons)（MIT License, Copyright (c) 2013 Panayiotis Lipiridis）。svgo で小さくしています。
- 国名・首都・国の情報：[外務省「国・地域」](https://www.mofa.go.jp/mofaj/area/index.html)の各国の基礎データ。子ども向けに短くしたり、割合の数字や一部の注記を省いたりしています。
- 日本の面積：国土地理院「全国都道府県市区町村別面積調」
- 日本の人口：総務省統計局「人口推計」
- ふりがな：[fugashi](https://github.com/polm/fugashi)（MIT License）と [unidic-lite](https://github.com/polm/unidic-lite)（BSD License）で付けています（作るときだけ使い、アプリには含みません）。
- 文字：Google Fonts の M PLUS Rounded 1c（SIL Open Font License）
