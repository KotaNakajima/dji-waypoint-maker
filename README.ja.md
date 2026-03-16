# Drone Route Maker

DJI互換のドローン飛行ルート（WPMZ/KMZ）を生成するツールです。DJI Pilot 2にインポート可能なウェイポイントベースおよびエリアマッピングの飛行計画を作成します。

> **免責事項**: 本ツールは飛行ルートファイルの生成のみを行います。安全かつ合法的なドローン運用はユーザーの責任です。各ミッション前に必ず航空法規の遵守、空域制限の確認、飛行前安全点検を行ってください。

## 対応ドローン

| モデル | キー | droneEnum | subEnum | payloadEnum |
|--------|------|-----------|---------|-------------|
| Mavic 3 Enterprise | M3E | 77 | 0 | 66 |
| Mavic 3 Thermal | M3T | 77 | 1 | 67 |
| Mavic 3 Multispectral | M3M | 77 | 0 | 66 (プロキシ) |

## ルートタイプ

- **VD（Vertical Down）**: 各対象物の真上から1枚撮影。用途：オルソモザイク、地図作成。
- **OBL（Oblique Photography）**: 条方向と直交方向の2方位角から斜め撮影（4倍ズーム）。2つの別々のファイルを生成。用途：作物観察、多角度解析。
- **mapping2d（エリアマッピング）**: オーバーラップ設定可能な面的測量。蛇行飛行パスで自動撮影。用途：広域マッピング、オルソフォト生成。

## 必要環境

- Python 3.8以上
- シェープファイル変換用：`pyproj`, `pyshp`
- 飛行ルート生成はPython標準ライブラリのみ使用

```bash
pip install -r requirements.txt
```

## 使用方法

### 飛行ルートの生成

```bash
python generate_flight.py
```

対話形式で以下を設定します：
1. ルートタイプ（VD / OBL / mapping2d）
2. 入力データ — CSVファイル（VD/OBL）または手動4隅座標入力（mapping2d）
3. ルート固有の設定（OBLのジンバル角度、mapping2dのオーバーラップ・方向等）
4. ドローンモデル（M3E / M3T / M3M）
5. 飛行パラメータ（高度、速度）— GSDとブレ防止最高速度を参考情報として表示
6. 飛行名と出力ディレクトリ

#### mapping2dの方向計算

ポリゴンの最小面積外接矩形（MABR）に基づき、最適な飛行方向を自動算出します。不整形な四角形でも効率的な蛇行カバレッジを実現します。

#### ブレ防止速度参照

飛行高度入力後、地上解像度（GSD）と主要シャッタースピードでのブレ防止最高速度を表示します：

```
  GSD: 1.37 cm/px at 50m
  Blur-free max speed (max 0.5px motion blur):
    1/500 : 3.4 m/s
    1/800 : 5.5 m/s
    1/1000: 6.8 m/s
    1/1600: 10.9 m/s
    1/2000: 13.7 m/s
```

### シェープファイルからCSVへの変換

```bash
python convert_shp2csv.py
```

ESRIシェープファイル（ポリゴン）をCSV形式に変換します。JGD2011、UTM、Tokyo測地系の座標系に対応。

### テンプレートCSVの生成

```bash
python src/generate_default_csv.py --output test.csv --num 5 --width 3 --height 3
python src/generate_grid_csv.py --output grid.csv --ew-count 10 --ns-count 10
```

## CSV形式

各行は1つの対象物を表し、4つの角座標（WGS84）を含みます：

```
lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4
```

識別子列付きの場合：

```
lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,SerialNumb
```

ヘッダー行は自動検出されます。`SerialNumb`と`plot_id`の両方がある場合、`SerialNumb`が優先されます。

## 出力ファイル

- **`.zip`（WPMZ）**: DJI Pilot 2アプリにインポート
- **`.kmz`**: Google Earthでプレビュー

パッケージ構造：
```
wpmz/
  template.kml      # ミッションテンプレート（WPML仕様1.0.2）
  waylines.wpml     # 実行ウェイライン（WPML仕様1.0.6）
```

出力は `output/{飛行名}_{タイムスタンプ}/` に保存されます。

ウェイポイント数が多い場合、複数ファイルへの分割オプションが提示されます。

## プロジェクト構成

```
generate_flight.py          # メインエントリーポイント
convert_shp2csv.py          # シェープファイルからCSV変換
lib/
  drone_config.py           # ドローンモデル設定・カメラスペック
  csv_parser.py             # CSV入力パーサー
  object_calculator.py      # 中心/方位角計算
  file_creator.py           # VD + OBL KML/WPML生成
  mapping_creator.py        # mapping2d KML/WPML生成
  package_creator.py        # ZIP/KMZパッケージャー
src/
  generate_default_csv.py   # テンプレートCSV生成
  generate_grid_csv.py      # グリッドCSV生成
```

## ライセンス

MIT
