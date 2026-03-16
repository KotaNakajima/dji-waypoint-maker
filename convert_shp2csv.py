#!/usr/bin/env python3
"""
Shapefile to CSV Converter v2 - Interactive Version
シェープファイルをCSV形式に変換するツール（インタラクティブ版）

このスクリプトはShapefileのポリゴンをCSV形式に変換し、generate_flight_files.pyで使用可能な
形式で出力します。各ポリゴンの4つの角座標を
(lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4) 形式で出力します。

SerialNumbまたはplot_id列が存在する場合、それらも含まれます。
"""

import os
import csv
import sys
from datetime import datetime
from pyproj import Transformer, CRS

# Try different import approaches for the shapefile library
try:
    import shapefile
except ImportError:
    try:
        from pyshp import shapefile
    except ImportError:
        raise ImportError("Could not import shapefile library. Please install using 'pip install pyshp'")

def print_header():
    """ヘッダーを表示"""
    print("🗺️  Shapefile to CSV 変換ツール v2 🗺️")
    print("=" * 50)
    print("このツールはShapefileをドローン飛行計画用CSVに変換します。")
    print()

def get_input_directory():
    """入力ディレクトリを取得"""
    print("ステップ 1: 入力ディレクトリの選択")
    print("-" * 30)
    
    base_dir = "input_qgis"
    if not os.path.exists(base_dir):
        print(f"❌ ベースディレクトリ '{base_dir}' が見つかりません。")
        sys.exit(1)
    
    # サブディレクトリを一覧表示
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    if not subdirs:
        print(f"❌ '{base_dir}' にサブディレクトリが見つかりません。")
        sys.exit(1)
    
    print("利用可能なサブディレクトリ:")
    for i, subdir in enumerate(subdirs, 1):
        print(f"{i}. {subdir}")
    print()
    
    while True:
        try:
            choice = input("サブディレクトリを選択してください（番号入力）: ").strip()
            index = int(choice) - 1
            if 0 <= index < len(subdirs):
                selected_dir = os.path.join(base_dir, subdirs[index])
                print(f"✅ 選択されたディレクトリ: {selected_dir}")
                return selected_dir
            else:
                print("❌ 無効な番号です。もう一度入力してください。")
        except ValueError:
            print("❌ 数字を入力してください。")

def get_coordinate_system():
    """座標参照系（CRS）を取得"""
    print("\nステップ 2: 座標参照系（CRS）の選択")
    print("-" * 30)
    print("座標系を選択してください:")
    print("1. 日本の測地系")
    print("2. UTM座標系")
    print("3. 自動検出（PRJファイルから）")
    print()
    
    while True:
        choice = input("選択してください [1-3]: ").strip()
        
        if choice == "1":
            return get_japanese_crs()
        elif choice == "2":
            return get_utm_crs()
        elif choice == "3":
            print("✅ 自動検出を選択しました。")
            return None
        else:
            print("❌ 1、2、または3を入力してください。")

def get_japanese_crs():
    """日本の測地系選択"""
    print("\n日本の測地系を選択してください:")
    print("1. JGD2011 （現行標準、推奨）")
    print("2. Tokyo測地系 （旧測地系）")
    print()
    
    while True:
        choice = input("選択してください [1-2]: ").strip()
        
        if choice == "1":
            return get_jgd2011_details()
        elif choice == "2":
            print("✅ Tokyo測地系を選択しました。")
            return create_tokyo_to_jgd2011_to_wgs84_transformer()
        else:
            print("❌ 1または2を入力してください。")

def get_jgd2011_details():
    """JGD2011の詳細選択"""
    print("\nJGD2011の座標系を選択してください:")
    print("1. EPSG:6677 - JGD2011 / Japan Plane Rectangular CS IX（関東地方）")
    print("2. その他のEPSGコードを指定")
    print()
    
    while True:
        choice = input("選択してください [1-2]: ").strip()
        
        if choice == "1":
            print("✅ EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX) を選択しました。")
            return create_jgd2011_to_wgs84_transformer(6677)
        elif choice == "2":
            return get_custom_epsg()
        else:
            print("❌ 1または2を入力してください。")

def get_custom_epsg():
    """カスタムEPSGコード入力"""
    while True:
        try:
            epsg = int(input("EPSGコードを入力してください: ").strip())
            if epsg > 0:
                print(f"✅ EPSG:{epsg} を選択しました。")
                return create_jgd2011_to_wgs84_transformer(epsg)
            else:
                print("❌ 正の整数を入力してください。")
        except ValueError:
            print("❌ 数字を入力してください。")

def get_utm_crs():
    """UTM座標系選択"""
    print("\nUTM座標系の詳細を入力してください:")
    
    while True:
        try:
            zone = int(input("UTMゾーン番号を入力してください (1-60): ").strip())
            if 1 <= zone <= 60:
                break
            else:
                print("❌ 1から60の間で入力してください。")
        except ValueError:
            print("❌ 数字を入力してください。")
    
    while True:
        hemisphere = input("半球を選択してください (n=北半球, s=南半球): ").strip().lower()
        if hemisphere in ['n', 'north', '北', '北半球']:
            northern = True
            break
        elif hemisphere in ['s', 'south', '南', '南半球']:
            northern = False
            break
        else:
            print("❌ 'n'（北半球）または's'（南半球）を入力してください。")
    
    print(f"✅ UTM Zone {zone}{'N' if northern else 'S'} を選択しました。")
    return create_utm_to_wgs84_transformer(zone, northern)

def get_output_settings():
    """出力設定を取得"""
    print("\nステップ 3: 出力設定")
    print("-" * 30)
    
    # 出力ディレクトリ
    default_output_dir = "input_csv"
    output_dir = input(f"出力ディレクトリを入力してください (デフォルト: {default_output_dir}): ").strip()
    if not output_dir:
        output_dir = default_output_dir
    
    # 出力ファイル名
    timestamp = datetime.now().strftime("%Y%m%d")
    default_filename = f"{timestamp}_polygons"
    output_filename = input(f"出力ファイル名を入力してください．拡張子は自動で付与されます． (デフォルト: {default_filename}): ").strip()
    if not output_filename:
        output_filename = default_filename
    
    print(f"✅ 出力先: {os.path.join(output_dir, output_filename)}")
    
    return output_dir, output_filename

def confirm_settings(input_dir, crs_name, output_dir, output_filename):
    """設定の最終確認"""
    print("\n" + "=" * 50)
    print("最終確認")
    print("=" * 50)
    print(f"✓ 入力ディレクトリ: {input_dir}")
    print(f"✓ 座標参照系: {crs_name}")
    print(f"✓ 出力先: {os.path.join(output_dir, output_filename)}")
    print()
    
    while True:
        response = input("変換を実行しますか？ [y/N]: ").lower().strip()
        if response in ['y', 'yes', 'はい']:
            return True
        elif response in ['n', 'no', 'いいえ', '']:
            print("処理をキャンセルしました。")
            return False
        else:
            print("'y'または'n'で答えてください。")

def create_utm_to_wgs84_transformer(utm_zone=53, northern=True):
    """UTMからWGS84への座標変換器を作成"""
    utm_crs = CRS.from_string(f"+proj=utm +zone={utm_zone} +{'north' if northern else 'south'} +datum=WGS84 +units=m +no_defs")
    wgs84_crs = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True)
    return transformer

def create_jgd2011_to_wgs84_transformer(epsg=6677):
    """JGD2011からWGS84への座標変換器を作成"""
    jgd2011_crs = CRS.from_epsg(epsg)
    wgs84_crs = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(jgd2011_crs, wgs84_crs, always_xy=True)
    return transformer

def create_tokyo_to_jgd2011_to_wgs84_transformer():
    """Tokyo測地系からJGD2011経由でWGS84への座標変換器を作成"""
    tokyo_crs = CRS.from_epsg(30169)
    jgd2011_crs = CRS.from_epsg(6677)
    wgs84_crs = CRS.from_epsg(4326)
    
    def transform_coords(x, y):
        transformer1 = Transformer.from_crs(tokyo_crs, jgd2011_crs, always_xy=True)
        x_jgd, y_jgd = transformer1.transform(x, y)
        
        transformer2 = Transformer.from_crs(jgd2011_crs, wgs84_crs, always_xy=True)
        lon, lat = transformer2.transform(x_jgd, y_jgd)
        
        return lon, lat
    
    return transform_coords

def extract_polygon_corners(polygon):
    """ポリゴンから4つの角を抽出"""
    points = polygon.points
    # 閉じたポリゴンの場合、最後の点を削除
    if points[0] == points[-1]:
        points = points[:-1]
    
    if len(points) < 4:
        raise ValueError(f"ポリゴンの点数が4未満です: {len(points)}")
    
    if len(points) == 4:
        return points
    else:
        # 4点以上の場合は等間隔でサンプリング
        num_points = len(points)
        interval = num_points // 4
        
        corners = [
            points[0],
            points[interval],
            points[2 * interval],
            points[3 * interval]
        ]
        
        return corners

def detect_identifier_fields(sf):
    """SerialNumbまたはplot_id列を検出"""
    serial_numb_index = None
    plot_id_index = None
    
    for i, field in enumerate(sf.fields):
        if field == ('DeletionFlag', 'C', 1, 0):
            continue
        
        field_name = field[0] if isinstance(field, list) else str(field)
        field_name_lower = field_name.lower()
        
        # SerialNumb variations
        if field_name_lower in ['serialnumb', 'serial_numb', 'serialnumber', 'serial_number', 'serial']:
            serial_numb_index = i - 1  # DeletionFlagを調整
            print(f"SerialNumb列を検出: {field_name} (インデックス: {serial_numb_index})")
            
        # plot_id variations  
        elif field_name_lower in ['plot_id', 'plotid', 'plot', 'id']:
            plot_id_index = i - 1  # DeletionFlagを調整
            print(f"plot_id列を検出: {field_name} (インデックス: {plot_id_index})")
    
    return serial_numb_index, plot_id_index

def auto_detect_transformer(input_dir):
    """PRJファイルから座標変換器を自動検出"""
    prj_files = [f for f in os.listdir(input_dir) if f.endswith('.prj')]
    
    if not prj_files:
        print("⚠️ PRJファイルが見つかりません。座標変換なしで処理します。")
        return None, "座標変換なし"
    
    prj_path = os.path.join(input_dir, prj_files[0])
    
    try:
        with open(prj_path, 'r') as f:
            prj_content = f.read().strip()
        
        print(f"PRJファイルを検出: {prj_files[0]}")
        
        if "UTM" in prj_content:
            transformer = create_utm_to_wgs84_transformer(53, True)
            crs_name = "UTM Zone 53N → WGS84 (自動検出)"
        elif "Tokyo" in prj_content and "Japan_Zone_9" in prj_content:
            transformer = create_tokyo_to_jgd2011_to_wgs84_transformer()
            crs_name = "Tokyo測地系 → JGD2011 → WGS84 (自動検出)"
        elif "Japan" in prj_content or "JGD2011" in prj_content:
            transformer = create_jgd2011_to_wgs84_transformer(6677)
            crs_name = "JGD2011 (EPSG:6677) → WGS84 (自動検出)"
        else:
            print("⚠️ 未知の座標系です。座標変換なしで処理します。")
            transformer = None
            crs_name = "座標変換なし (未知の座標系)"
        
        return transformer, crs_name
        
    except Exception as e:
        print(f"⚠️ PRJファイルの読み込みに失敗: {e}")
        return None, "座標変換なし (PRJファイル読み込み失敗)"

def process_shapefiles(input_dir, output_dir, output_filename, transformer):
    """Shapefileを処理してCSVに変換"""
    print("\n処理を開始します...")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename+".csv")
    
    # Shapefileを検索
    shapefiles = [f for f in os.listdir(input_dir) if f.endswith('.shp')]
    
    if not shapefiles:
        print(f"❌ {input_dir} にShapefileが見つかりません。")
        return False
    
    print(f"検出されたShapefile: {len(shapefiles)}個")
    for shp in shapefiles:
        print(f"  - {shp}")
    
    # 全オブジェクトを収集
    all_objects = []
    
    for shp_file in shapefiles:
        shp_path = os.path.join(input_dir, shp_file)
        print(f"\n処理中: {shp_file}")
        
        try:
            sf = shapefile.Reader(shp_path)
            
            # ポリゴンかチェック
            if sf.shapeType not in [5, 15, 25]:
                print(f"⚠️ スキップ: {shp_file} はポリゴンではありません (タイプ: {sf.shapeType})")
                continue
            
            # 識別子フィールドを検出
            serial_numb_index, plot_id_index = detect_identifier_fields(sf)
            
            # 各シェイプを処理
            for i, (shape, record) in enumerate(zip(sf.shapes(), sf.records())):
                try:
                    # 角座標を抽出
                    corners = extract_polygon_corners(shape)
                    
                    # 座標変換
                    transformed_corners = []
                    for j, corner in enumerate(corners):
                        x, y = corner

                        if transformer:
                            if callable(transformer) and not hasattr(transformer, 'transform'):
                                lon, lat = transformer(x, y)
                            else:
                                lon, lat = transformer.transform(x, y)
                        else:
                            lon, lat = x, y

                        transformed_corners.append((lat, lon))
                    
                    # 識別子を取得（優先順位: SerialNumb > plot_id）
                    identifier = None
                    if serial_numb_index is not None and serial_numb_index < len(record):
                        try:
                            identifier = int(record[serial_numb_index])
                        except (ValueError, TypeError):
                            print(f"⚠️ 無効なSerialNumb値: {record[serial_numb_index]} (行 {i+1})")
                    elif plot_id_index is not None and plot_id_index < len(record):
                        try:
                            identifier = int(record[plot_id_index])
                        except (ValueError, TypeError):
                            print(f"⚠️ 無効なplot_id値: {record[plot_id_index]} (行 {i+1})")
                    
                    # オブジェクトを追加
                    if identifier is not None:
                        all_objects.append((transformed_corners, identifier))
                    else:
                        all_objects.append(transformed_corners)
                        
                except Exception as e:
                    print(f"⚠️ シェイプ処理エラー (行 {i+1}): {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ {shp_file} の処理に失敗: {e}")
            continue
    
    if not all_objects:
        print("❌ 処理できるオブジェクトが見つかりませんでした。")
        return False
    
    # CSVに書き出し
    print(f"\nCSVファイルを作成中: {output_path}")
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            
            for obj in all_objects:
                row = []
                
                if isinstance(obj, tuple) and len(obj) == 2:
                    # 識別子付きオブジェクト
                    corners, identifier = obj
                    for lat, lon in corners:
                        row.extend([lat, lon])
                    row.append(identifier)
                else:
                    # 識別子なしオブジェクト
                    corners = obj
                    for lat, lon in corners:
                        row.extend([lat, lon])
                
                csvwriter.writerow(row)
        
        print(f"✅ 変換完了: {len(all_objects)}個のオブジェクトを処理しました")
        print(f"✅ 出力ファイル: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ CSVファイルの書き込みに失敗: {e}")
        return False

def main():
    """メイン関数"""
    try:
        print_header()
        
        # ステップ1: 入力ディレクトリ選択
        input_dir = get_input_directory()
        
        # ステップ2: 座標参照系選択
        transformer = get_coordinate_system()
        if transformer is None:
            transformer, crs_name = auto_detect_transformer(input_dir)
        else:
            crs_name = "ユーザー指定"
        
        # ステップ3: 出力設定
        output_dir, output_filename = get_output_settings()

        # 最終確認
        if not confirm_settings(input_dir, crs_name, output_dir, output_filename):
            return

        # 処理実行
        success = process_shapefiles(input_dir, output_dir, output_filename, transformer)
        
        if success:
            print(f"\n🎉 処理が正常に完了しました！")
        else:
            print(f"\n❌ 処理中にエラーが発生しました。")
            
    except KeyboardInterrupt:
        print("\n\n処理が中断されました。")
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
