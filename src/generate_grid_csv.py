#!/usr/bin/env python3
"""
ドローン撮影用の規則的なグリッドCSVファイルを生成するスクリプト
- 東西方向: 1.5mの間隔で18ポイント
- 南北方向: 1.05mの間隔で50ポイント
- 合計: 900ポイント
- 北西角: 34.687177, 133.912699
"""

import csv
import argparse
import math

def generate_grid_csv(output_file, start_lat, start_lon, east_west_spacing, north_south_spacing, 
                      east_west_count, north_south_count, object_width=0.2, object_height=0.2):
    """
    規則的なグリッドパターンでドローン撮影ポイントのCSVファイルを生成します。
    各ポイントは小さな矩形（対象物体）として表現されます。
    """
    # 緯度経度の度あたりのメートル数（概算）
    lat_meter = 1 / 111111  # 緯度1度あたりのメートル
    lon_meter = 1 / (111111 * math.cos(math.radians(start_lat)))  # 経度1度あたりのメートル（緯度に依存）
    
    # オブジェクトの半分のサイズ（度単位）
    half_width_deg = (object_width / 2) * lon_meter
    half_height_deg = (object_height / 2) * lat_meter
    
    # 間隔を度単位に変換
    east_west_spacing_deg = east_west_spacing * lon_meter
    north_south_spacing_deg = north_south_spacing * lat_meter
    
    points = []
    
    # 900ポイントのグリッドを生成
    for i in range(north_south_count):
        for j in range(east_west_count):
            # 中心点の計算
            center_lat = start_lat - (i * north_south_spacing_deg)
            center_lon = start_lon + (j * east_west_spacing_deg)
            
            # 4つの角の座標を計算（矩形）
            # 注: 上が北、右が東と想定
            nw = (center_lat + half_height_deg, center_lon - half_width_deg)  # 北西
            ne = (center_lat + half_height_deg, center_lon + half_width_deg)  # 北東
            se = (center_lat - half_height_deg, center_lon + half_width_deg)  # 南東
            sw = (center_lat - half_height_deg, center_lon - half_width_deg)  # 南西
            
            # 角の座標を行に平坦化
            flat_corners = [nw[0], nw[1], ne[0], ne[1], se[0], se[1], sw[0], sw[1]]
            points.append(flat_corners)
    
    # CSVに出力
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for point in points:
            writer.writerow(point)
    
    print(f"グリッドCSVファイルを作成しました: {output_file}")
    print(f"合計ポイント数: {len(points)}")
    print(f"グリッドサイズ: 東西 {east_west_count} × 南北 {north_south_count}")
    print(f"北西角: {start_lat}, {start_lon}")
    print(f"東西間隔: {east_west_spacing}m, 南北間隔: {north_south_spacing}m")

def main():
    parser = argparse.ArgumentParser(description="ドローン撮影用のグリッドCSVファイルを生成")
    parser.add_argument("--output", type=str, default="grid_targets.csv",
                        help="出力CSVファイル名 (デフォルト: grid_targets.csv)")
    parser.add_argument("--start-lat", type=float, default=34.687177,
                        help="開始地点（北西角）の緯度 (デフォルト: 34.687177)")
    parser.add_argument("--start-lon", type=float, default=133.912699,
                        help="開始地点（北西角）の経度 (デフォルト: 133.912699)")
    parser.add_argument("--ew-spacing", type=float, default=1.5,
                        help="東西方向の間隔（メートル） (デフォルト: 1.5)")
    parser.add_argument("--ns-spacing", type=float, default=1.05,
                        help="南北方向の間隔（メートル） (デフォルト: 1.05)")
    parser.add_argument("--ew-count", type=int, default=18,
                        help="東西方向のポイント数 (デフォルト: 18)")
    parser.add_argument("--ns-count", type=int, default=50,
                        help="南北方向のポイント数 (デフォルト: 50)")
    parser.add_argument("--obj-width", type=float, default=0.2,
                        help="各オブジェクトの幅（メートル） (デフォルト: 0.2)")
    parser.add_argument("--obj-height", type=float, default=0.2,
                        help="各オブジェクトの高さ（メートル） (デフォルト: 0.2)")
    
    args = parser.parse_args()
    
    generate_grid_csv(args.output, args.start_lat, args.start_lon, 
                     args.ew_spacing, args.ns_spacing, 
                     args.ew_count, args.ns_count,
                     args.obj_width, args.obj_height)

if __name__ == "__main__":
    main()
