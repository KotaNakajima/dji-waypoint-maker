#!/usr/bin/env python3
"""
Drone Flight Route Generator

Generates DJI-compatible WPMZ flight route packages for automated drone missions.
Supports VD (Vertical Down), OBL (Oblique Photography), and mapping2d route types.

Supported drones: Mavic 3E, Mavic 3T, Mavic 3M
"""

import argparse
import math
import os
import sys
from datetime import datetime
from lib.csv_parser import parse_csv_input
from lib.object_calculator import calculate_object_details
from lib.drone_config import (
    DRONE_MODELS,
    M3M_IMAGE_FORMATS,
    get_drone_config,
    get_effective_camera,
    DEFAULT_VD_HEIGHT,
    DEFAULT_OBL_HEIGHT,
    DEFAULT_OBL_GIMBAL_ANGLE,
    DEFAULT_AUTO_FLIGHT_SPEED,
    DEFAULT_MAPPING2D_HEIGHT,
    SHUTTER_SPEEDS,
    MAX_BLUR_PX,
)


def print_header():
    print("Drone Flight Route Generator")
    print("=" * 50)
    print("Generates DJI WPMZ packages for automated drone missions.")
    print()


def print_help():
    help_text = """
Drone Flight Route Generator - Help

[Overview]
Generates DJI drone flight mission files (WPMZ) for Mavic 3 Enterprise series.

[CSV Format]
Basic:
  lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4

With identifier:
  lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,SerialNumb
  lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,plot_id

- Coordinate system: WGS84 (EPSG:4326)
- Each row = one target object with 4 corner coordinates
- SerialNumb takes priority over plot_id if both exist

[Route Types]
1. VD (Vertical Down)
   - Single overhead photo per target (default height: 7m)
   - Use case: orthomosaic, mapping

2. OBL (Oblique Photography)
   - Oblique photos from two directions (row + perpendicular)
   - Configurable gimbal angle, altitude, zoom 4x
   - Generates two separate flight files
   - Use case: crop observation, multi-angle analysis

3. mapping2d (Area Mapping)
   - Area-based survey with configurable overlap
   - DJI Pilot 2 auto-generates flight lines
   - Use case: large area mapping, orthophoto generation

[Supported Drones]
- M3E: Mavic 3 Enterprise (droneEnum=77, sub=0, payload=66)
- M3T: Mavic 3 Thermal  (droneEnum=77, sub=1, payload=67)
- M3M: Mavic 3 Multispectral (uses M3E proxy values)

[Output]
- WPMZ (.zip): Import into DJI Pilot 2
- KMZ (.kmz): Preview in Google Earth
"""
    print(help_text)


def get_csv_file_path():
    print("\nStep 2: CSV File Selection")
    print("-" * 30)

    while True:
        csv_path = input("Enter CSV file path (files in input_csv/ can be entered by name only): ").strip()

        if not csv_path:
            print("Please enter a file path.")
            continue

        if not os.path.isabs(csv_path):
            full_path = os.path.join("input_csv", csv_path)
            if os.path.exists(full_path):
                csv_path = full_path

        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            continue

        if not csv_path.lower().endswith('.csv'):
            print("Please specify a CSV file (.csv extension)")
            continue

        print(f"CSV file: {csv_path}")
        return csv_path


def get_route_type():
    print("Step 1: Route Type Selection")
    print("-" * 30)
    print("Available route types:")
    print("1. VD (Vertical Down) - Overhead photography (CSV input)")
    print("2. OBL (Oblique Photography) - Angled photography (CSV input)")
    print("3. mapping2d (Area Mapping) - Area survey (manual coordinate input)")
    print()

    while True:
        choice = input("Select route type [1-3]: ").strip()

        if choice == "1":
            print("Selected: VD (Vertical Down)")
            return "vd"
        elif choice == "2":
            print("Selected: OBL (Oblique Photography)")
            return "obl"
        elif choice == "3":
            print("Selected: mapping2d (Area Mapping)")
            return "mapping2d"
        else:
            print("Please enter 1, 2, or 3.")


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two WGS84 points in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bearing(lat1, lon1, lat2, lon2):
    """Calculate initial bearing from point 1 to point 2 in degrees (0-360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    bearing = math.degrees(math.atan2(x, y))
    return bearing % 360


def _polygon_area_m2(corners):
    """Approximate area of a polygon defined by (lat, lon) corners in m^2."""
    n = len(corners)
    if n < 3:
        return 0.0
    # Shoelace formula on local meter-scale projection
    ref_lat = sum(c[0] for c in corners) / n
    ref_lon = sum(c[1] for c in corners) / n
    lat_m = 111111.0
    lon_m = 111111.0 * math.cos(math.radians(ref_lat))
    xs = [(c[1] - ref_lon) * lon_m for c in corners]
    ys = [(c[0] - ref_lat) * lat_m for c in corners]
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(area) / 2.0


def _calculate_mabr_direction(corners):
    """
    Calculate optimal flight direction using the minimum area bounding rectangle (MABR).
    The MABR long side gives the direction that produces the most efficient serpentine
    coverage, especially for irregular quadrilaterals.

    Returns:
        (long_bearing, short_bearing, long_length, short_length)
        Bearings in degrees (0=north, 90=east).
    """
    n = len(corners)
    ref_lat = sum(c[0] for c in corners) / n
    ref_lon = sum(c[1] for c in corners) / n

    lat_m = 111111.0
    lon_m = 111111.0 * math.cos(math.radians(ref_lat))

    # Convert to local meters (x=east, y=north)
    local = [((c[1] - ref_lon) * lon_m, (c[0] - ref_lat) * lat_m) for c in corners]

    best_area = float('inf')
    best_edge_angle = 0
    best_w = 0
    best_h = 0

    for i in range(len(local)):
        j = (i + 1) % len(local)
        dx = local[j][0] - local[i][0]
        dy = local[j][1] - local[i][1]
        if abs(dx) < 1e-10 and abs(dy) < 1e-10:
            continue
        edge_angle = math.atan2(dy, dx)

        cos_a = math.cos(-edge_angle)
        sin_a = math.sin(-edge_angle)
        rotated = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in local]

        min_x = min(p[0] for p in rotated)
        max_x = max(p[0] for p in rotated)
        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)

        w = max_x - min_x
        h = max_y - min_y
        area = w * h

        if area < best_area:
            best_area = area
            best_edge_angle = edge_angle
            best_w = w
            best_h = h

    # Determine long/short side directions
    if best_w >= best_h:
        long_math_angle = best_edge_angle
        short_math_angle = best_edge_angle + math.pi / 2
        long_len, short_len = best_w, best_h
    else:
        long_math_angle = best_edge_angle + math.pi / 2
        short_math_angle = best_edge_angle
        long_len, short_len = best_h, best_w

    # Convert math angle (from east, CCW) to bearing (from north, CW)
    long_bearing = (90 - math.degrees(long_math_angle)) % 360
    short_bearing = (90 - math.degrees(short_math_angle)) % 360

    return long_bearing, short_bearing, long_len, short_len


def get_mapping2d_corners():
    """Interactively input 4 corner coordinates for mapping2d polygon."""
    print("\nStep 2: Field Boundary Input (4 corners)")
    print("-" * 30)
    print("Enter the 4 corner coordinates of the survey area (WGS84).")
    print("Input format: lat,lon  (e.g. 35.6895,139.6917)")
    print()

    corners = []
    for i in range(4):
        while True:
            raw = input(f"  Corner {i + 1}: ").strip()
            try:
                parts = raw.replace(" ", "").split(",")
                if len(parts) != 2:
                    print("    Format: lat,lon (comma separated)")
                    continue
                lat, lon = float(parts[0]), float(parts[1])
                if not (-90 <= lat <= 90):
                    print("    Latitude must be between -90 and 90.")
                    continue
                if not (-180 <= lon <= 180):
                    print("    Longitude must be between -180 and 180.")
                    continue
                corners.append((lat, lon))
                break
            except ValueError:
                print("    Please enter valid numbers. Format: lat,lon")

    # Calculate and display area info
    print()
    print("--- Survey Area Summary ---")
    for i, (lat, lon) in enumerate(corners):
        print(f"  Corner {i + 1}: {lat:.6f}, {lon:.6f}")

    # Edge lengths
    edge_labels = ["1-2", "2-3", "3-4", "4-1"]
    edge_lengths = []
    for i in range(4):
        j = (i + 1) % 4
        d = _haversine_distance(corners[i][0], corners[i][1],
                                corners[j][0], corners[j][1])
        edge_lengths.append(d)
        print(f"  Edge {edge_labels[i]}: {d:.1f} m")

    area_m2 = _polygon_area_m2(corners)
    if area_m2 >= 10000:
        print(f"  Area: {area_m2:.0f} m2 ({area_m2 / 10000:.2f} ha)")
    else:
        print(f"  Area: {area_m2:.1f} m2")
    print()

    while True:
        response = input("Use these coordinates? [y/N]: ").lower().strip()
        if response in ('y', 'yes'):
            return corners
        elif response in ('n', 'no', ''):
            print("Re-entering coordinates.\n")
            return get_mapping2d_corners()
        print("Please enter 'y' or 'n'.")


def get_drone_model():
    print("\nStep 3: Drone Model Selection")
    print("-" * 30)
    print("Available drones:")
    for key, cfg in DRONE_MODELS.items():
        print(f"  {key}: {cfg['name']}")
    print()

    while True:
        model = input("Enter drone model [M3E/M3T/M3M] (default: M3E): ").strip().upper()
        if not model:
            model = "M3E"
        if model in DRONE_MODELS:
            print(f"Selected: {DRONE_MODELS[model]['name']}")
            break
        else:
            valid = ", ".join(DRONE_MODELS.keys())
            print(f"Invalid model. Choose from: {valid}")

    # M3M camera selection
    selected_image_format = None
    if model == "M3M":
        print("\nCamera selection for Mavic 3M:")
        for key, opt in M3M_IMAGE_FORMATS.items():
            default_mark = " (default)" if key == "3" else ""
            print(f"  {key}: {opt['label']}{default_mark}")
        print()

        while True:
            choice = input("Select camera [1/2/3] (default: 3): ").strip()
            if not choice:
                choice = "3"
            if choice in M3M_IMAGE_FORMATS:
                selected_image_format = M3M_IMAGE_FORMATS[choice]["imageFormat"]
                print(f"Camera: {M3M_IMAGE_FORMATS[choice]['label']}")
                break
            else:
                print("Invalid choice. Enter 1, 2, or 3.")

    return model, selected_image_format


def get_flight_params(route_type, drone_config=None):
    print("\nStep 4: Flight Parameters")
    print("-" * 30)

    # Height
    if route_type == "vd":
        default_height = DEFAULT_VD_HEIGHT
    elif route_type == "obl":
        default_height = DEFAULT_OBL_HEIGHT
    else:
        default_height = DEFAULT_MAPPING2D_HEIGHT

    while True:
        try:
            height = float(input(f"Flight height in meters (default: {default_height}): ").strip() or str(default_height))
            if height > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a number.")

    # Show GSD and blur-free max speed reference
    if drone_config and "image_width_px" in drone_config:
        cam = get_effective_camera(drone_config)
        gsd_m = (cam["sensor_width_mm"] * height) / \
                (cam["focal_length_mm"] * cam["image_width_px"])
        gsd_cm = gsd_m * 100

        # M3M: show both RGB and multispectral GSD
        if "ms_sensor_width_mm" in drone_config:
            rgb_gsd = (drone_config["sensor_width_mm"] * height) / \
                      (drone_config["focal_length_mm"] * drone_config["image_width_px"])
            ms_gsd = (drone_config["ms_sensor_width_mm"] * height) / \
                     (drone_config["ms_focal_length_mm"] * drone_config["ms_image_width_px"])
            print(f"\n  GSD at {height}m:")
            print(f"    RGB:           {rgb_gsd * 100:.2f} cm/px")
            print(f"    Multispectral: {ms_gsd * 100:.2f} cm/px")
        else:
            print(f"\n  GSD: {gsd_cm:.2f} cm/px at {height}m")

        print(f"  Blur-free max speed (max {MAX_BLUR_PX}px motion blur):")
        for ss in SHUTTER_SPEEDS:
            max_spd = MAX_BLUR_PX * gsd_m / (1.0 / ss)
            print(f"    1/{ss:<4d}: {max_spd:.1f} m/s")

        # Shooting interval speed constraint
        min_interval = cam.get("min_shoot_interval_s")
        if min_interval and min_interval >= 1.0:
            print(f"  * Min shooting interval: {min_interval:.1f}s (limits max effective speed)")
        print()

    # Speed
    while True:
        try:
            speed = float(input(f"Flight speed in m/s (default: {DEFAULT_AUTO_FLIGHT_SPEED}): ").strip() or str(DEFAULT_AUTO_FLIGHT_SPEED))
            if speed > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a number.")

    print(f"Height: {height}m, Speed: {speed}m/s")
    return height, speed


def determine_row_orientation(heading_angle):
    normalized_angle = (heading_angle + 360) % 360
    if (315 <= normalized_angle <= 360) or (0 <= normalized_angle <= 45) or (135 <= normalized_angle <= 225):
        return "north_south"
    else:
        return "east_west"


def get_oblique_settings(objects):
    print("\nOBL Settings")
    print("-" * 30)

    # Gimbal angle
    while True:
        try:
            gimbal_angle = float(input(f"Gimbal angle in degrees (0=horizontal, 90=nadir, default: {DEFAULT_OBL_GIMBAL_ANGLE}): ").strip() or str(DEFAULT_OBL_GIMBAL_ANGLE))
            if 0 <= gimbal_angle <= 90:
                break
            print("Please enter a value between 0 and 90.")
        except ValueError:
            print("Please enter a number.")

    # Analyze row direction from first object
    first_object = objects[0]
    if isinstance(first_object, tuple) and len(first_object) == 2:
        actual_corners, _ = first_object
    else:
        actual_corners = first_object

    _, _, heading_angle = calculate_object_details(actual_corners)
    row_orientation = determine_row_orientation(heading_angle)

    print(f"\nRow direction analysis:")
    print(f"Row heading: {heading_angle:.1f} degrees")

    if row_orientation == "north_south":
        print("Row direction: North-South")
        print("Perpendicular: East-West")

        print("\nSelect shooting side for row direction (N-S):")
        print("1. From North")
        print("2. From South")
        row_map = {"1": "north", "2": "south"}
        while True:
            choice = input("Row direction shooting side [1-2]: ").strip()
            if choice in row_map:
                row_side = row_map[choice]
                break
            print("Please enter 1 or 2.")

        print("\nSelect shooting side for perpendicular direction (E-W):")
        print("1. From East")
        print("2. From West")
        perp_map = {"1": "east", "2": "west"}
        while True:
            choice = input("Perpendicular direction shooting side [1-2]: ").strip()
            if choice in perp_map:
                perp_side = perp_map[choice]
                break
            print("Please enter 1 or 2.")
    else:
        print("Row direction: East-West")
        print("Perpendicular: North-South")

        print("\nSelect shooting side for row direction (E-W):")
        print("1. From East")
        print("2. From West")
        row_map = {"1": "east", "2": "west"}
        while True:
            choice = input("Row direction shooting side [1-2]: ").strip()
            if choice in row_map:
                row_side = row_map[choice]
                break
            print("Please enter 1 or 2.")

        print("\nSelect shooting side for perpendicular direction (N-S):")
        print("1. From North")
        print("2. From South")
        perp_map = {"1": "north", "2": "south"}
        while True:
            choice = input("Perpendicular direction shooting side [1-2]: ").strip()
            if choice in perp_map:
                perp_side = perp_map[choice]
                break
            print("Please enter 1 or 2.")

    print(f"Gimbal angle: {gimbal_angle} degrees")
    print(f"Row shooting side: {row_side}")
    print(f"Perpendicular shooting side: {perp_side}")
    return gimbal_angle, row_side, perp_side


def get_mapping2d_settings(corners):
    print("\nmapping2d Settings")
    print("-" * 30)

    while True:
        try:
            forward_overlap = float(input("Forward overlap % (default: 80): ").strip() or "80")
            if 0 <= forward_overlap <= 100:
                break
            print("Please enter a value between 0 and 100.")
        except ValueError:
            print("Please enter a number.")

    while True:
        try:
            side_overlap = float(input("Side overlap % (default: 70): ").strip() or "70")
            if 0 <= side_overlap <= 100:
                break
            print("Please enter a value between 0 and 100.")
        except ValueError:
            print("Please enter a number.")

    # Calculate optimal direction from minimum area bounding rectangle
    long_bearing, short_bearing, long_len, short_len = _calculate_mabr_direction(corners)

    print(f"\nFlight direction (inscribed rectangle: {long_len:.1f}m x {short_len:.1f}m):")
    print(f"  1. Along long side  ({long_len:.1f}m, bearing {long_bearing:.1f} deg)")
    print(f"  2. Along short side ({short_len:.1f}m, bearing {short_bearing:.1f} deg)")
    print("  3. Manual input (specify degrees)")

    while True:
        dir_choice = input("Select direction mode [1-3] (default: 1): ").strip()
        if dir_choice in ("", "1"):
            direction = round(long_bearing, 1)
            print(f"  -> Direction: {direction} deg (along long side)")
            break
        elif dir_choice == "2":
            direction = round(short_bearing, 1)
            print(f"  -> Direction: {direction} deg (along short side)")
            break
        elif dir_choice == "3":
            while True:
                try:
                    direction = float(input("Flight direction in degrees (0=north, 90=east, default: 0): ").strip() or "0")
                    if 0 <= direction < 360:
                        break
                    print("Please enter a value between 0 and 359.")
                except ValueError:
                    print("Please enter a number.")
            break
        print("Please enter 1, 2, or 3.")

    while True:
        try:
            margin = float(input("Margin beyond boundary in meters (default: 10): ").strip() or "10")
            if margin >= 0:
                break
            print("Please enter a non-negative number.")
        except ValueError:
            print("Please enter a number.")

    print("\nShoot type:")
    print("1. time - Trigger by time interval")
    print("2. distance - Trigger by distance interval")
    while True:
        choice = input("Select shoot type [1-2] (default: 1): ").strip()
        if choice in ("", "1"):
            shoot_type = "time"
            break
        elif choice == "2":
            shoot_type = "distance"
            break
        print("Please enter 1 or 2.")

    print(f"Forward overlap: {forward_overlap}%, Side overlap: {side_overlap}%")
    print(f"Direction: {direction} deg, Margin: {margin}m, Shoot type: {shoot_type}")
    return forward_overlap, side_overlap, direction, margin, shoot_type


def get_flight_name(route_type):
    print("\nStep 5: Flight Name")
    print("-" * 30)
    default_name = f"{route_type}_route"
    flight_name = input(f"Flight name (default: {default_name}): ").strip()
    if not flight_name:
        flight_name = default_name
    print(f"Flight name: {flight_name}")
    return flight_name


def get_output_directory(flight_name):
    print("\nStep 6: Output Directory")
    print("-" * 30)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_dir = f"{flight_name}_{timestamp}"
    output_dir = input(f"Output directory name (default: {default_dir}): ").strip()
    if not output_dir:
        output_dir = default_dir
    print(f"Output: output/{output_dir}")
    return output_dir


def confirm_settings(route_type, drone_model, flight_name, output_dir,
                     height, speed, csv_path=None, num_objects=None,
                     oblique_settings=None, mapping_settings=None,
                     mapping_corners=None, drone_config=None):
    print("\n" + "=" * 50)
    print("Confirmation")
    print("=" * 50)

    if csv_path:
        print(f"  CSV: {os.path.basename(csv_path)} ({num_objects} objects)")
    if mapping_corners:
        area_m2 = _polygon_area_m2(mapping_corners)
        print(f"  Survey area: 4 corners ({area_m2:.0f} m2)")

    route_labels = {
        "vd": "VD (Vertical Down)",
        "obl": "OBL (Oblique Photography)",
        "mapping2d": "mapping2d (Area Mapping)",
    }
    print(f"  Route type: {route_labels[route_type]}")
    print(f"  Drone: {DRONE_MODELS[drone_model]['name']}")
    if drone_model == "M3M":
        fmt = drone_config.get("imageFormat", "visable,narrow_band") if drone_config else "visable,narrow_band"
        fmt_labels = {"visable": "RGB only", "narrow_band": "Multispectral only",
                      "visable,narrow_band": "RGB + Multispectral"}
        print(f"  Camera: {fmt_labels.get(fmt, fmt)}")
    print(f"  Height: {height}m, Speed: {speed}m/s")

    if oblique_settings:
        gimbal_angle, row_side, perp_side = oblique_settings
        print(f"  Gimbal angle: {gimbal_angle} deg")
        print(f"  Row side: {row_side}, Perp side: {perp_side}")
        print("  Output: 2 files (row + perpendicular)")

    if mapping_settings:
        fwd, side, direction, margin, shoot = mapping_settings
        print(f"  Overlap: forward={fwd}%, side={side}%")
        print(f"  Direction: {direction} deg, Margin: {margin}m, Shoot: {shoot}")

    print(f"  Flight name: {flight_name}")
    print(f"  Output: output/{output_dir}")
    print()

    while True:
        response = input("Proceed? [y/N]: ").lower().strip()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no', ''):
            print("Cancelled.")
            return False
        print("Please enter 'y' or 'n'.")


def find_single_digit_divisors(n):
    return sorted([i for i in range(2, 10) if n % i == 0])


def ask_user_for_splitting(num_objects):
    print(f"\n{num_objects} waypoints found in CSV.")
    recommended = find_single_digit_divisors(num_objects)

    while True:
        response = input("Split into multiple files? (y/n): ").lower().strip()
        if response in ('y', 'yes'):
            break
        elif response in ('n', 'no'):
            return None
        print("Please enter 'y' or 'n'.")

    if recommended:
        print(f"Recommended split counts: {', '.join(map(str, recommended))}")

    while True:
        try:
            parts = int(input("How many parts? "))
            if 1 < parts <= num_objects:
                return parts
            print(f"Enter a number between 2 and {num_objects}.")
        except ValueError:
            print("Please enter an integer.")


def split_objects(objects, num_parts):
    part_size = len(objects) // num_parts
    remainder = len(objects) % num_parts
    parts = []
    start_idx = 0
    for i in range(num_parts):
        current_part_size = part_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_part_size
        parts.append(objects[start_idx:end_idx])
        start_idx = end_idx
    return parts


def main():
    parser = argparse.ArgumentParser(
        description="Drone Flight Route Generator - DJI WPMZ Package Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    parser.add_argument("--help", "-h", action="store_true", help="Show help")
    args = parser.parse_args()

    if args.help:
        print_help()
        return

    print_header()

    try:
        # Step 1: Route type (determines input method)
        route_type = get_route_type()

        # Step 2: Input - CSV for VD/OBL, manual corners for mapping2d
        csv_path = None
        objects = None
        mapping_corners = None

        if route_type == "mapping2d":
            mapping_corners = get_mapping2d_corners()
        else:
            csv_path = get_csv_file_path()
            objects = parse_csv_input(csv_path)
            if not objects:
                print("Error: No valid objects found in CSV.")
                return

        # Route-specific settings
        oblique_settings = None
        mapping_settings = None
        if route_type == "obl":
            oblique_settings = get_oblique_settings(objects)
        elif route_type == "mapping2d":
            mapping_settings = get_mapping2d_settings(mapping_corners)

        # Step 3: Drone model
        drone_model, selected_image_format = get_drone_model()
        drone_config = get_drone_config(drone_model)
        if selected_image_format is not None:
            drone_config = {**drone_config, "imageFormat": selected_image_format}

        # Step 4: Flight params
        height, speed = get_flight_params(route_type, drone_config)

        # Step 5: Flight name
        flight_name = get_flight_name(route_type)

        # Step 6: Output directory
        output_dir = get_output_directory(flight_name)

        # Confirmation
        if not confirm_settings(
            route_type, drone_model, flight_name, output_dir, height, speed,
            csv_path=csv_path,
            num_objects=len(objects) if objects else None,
            oblique_settings=oblique_settings,
            mapping_settings=mapping_settings,
            mapping_corners=mapping_corners,
            drone_config=drone_config,
        ):
            return

        print("\nGenerating flight files...")

        # --- mapping2d ---
        if route_type == "mapping2d":
            from lib.mapping_creator import (
                create_mapping2d_kml, create_mapping2d_wpml,
                calculate_mapping2d_spacing, generate_mapping2d_waypoints,
            )
            from lib.package_creator import create_zip_files_from_dir

            forward_overlap, side_overlap, direction, margin, shoot_type = mapping_settings

            # Calculate flight line spacing and photo interval
            line_spacing, photo_interval = calculate_mapping2d_spacing(
                height, forward_overlap, side_overlap, drone_config
            )
            print(f"  Line spacing: {line_spacing:.1f} m")
            print(f"  Photo interval: {photo_interval:.1f} m")

            # Check shooting interval constraint
            cam = get_effective_camera(drone_config)
            min_interval = cam.get("min_shoot_interval_s", 0)
            if min_interval > 0:
                max_speed_by_interval = photo_interval / min_interval
                if speed > max_speed_by_interval:
                    print(f"  WARNING: Speed {speed:.1f} m/s exceeds max {max_speed_by_interval:.1f} m/s")
                    print(f"           (photo interval {photo_interval:.1f}m / min shoot interval {min_interval:.1f}s)")
                    speed = max_speed_by_interval
                    print(f"           -> Speed adjusted to {speed:.1f} m/s")

            # Generate waypoints
            waypoints = generate_mapping2d_waypoints(
                mapping_corners, direction, line_spacing, margin
            )
            num_lines = len(waypoints) // 2
            print(f"  Flight lines: {num_lines}, Waypoints: {len(waypoints)}")

            if len(waypoints) < 2:
                print("Error: Could not generate flight lines. "
                      "Check polygon shape and spacing parameters.")
                return

            wpmz_dir = "wpmz"
            os.makedirs(wpmz_dir, exist_ok=True)

            # template.kml
            kml_content = create_mapping2d_kml(
                [mapping_corners], height, speed, forward_overlap, side_overlap,
                direction, margin, shoot_type, drone_config
            )
            kml_path = os.path.join(wpmz_dir, "template.kml")
            with open(kml_path, "w", encoding="utf-8") as f:
                f.write(kml_content)

            # waylines.wpml
            wpml_content = create_mapping2d_wpml(
                waypoints, height, speed, photo_interval, shoot_type, drone_config
            )
            wpml_path = os.path.join(wpmz_dir, "waylines.wpml")
            with open(wpml_path, "w", encoding="utf-8") as f:
                f.write(wpml_content)

            zip_path, kmz_path = create_zip_files_from_dir(
                wpmz_dir, "mapping2d", flight_name, output_dir
            )
            print(f"WPMZ: {zip_path}")
            print(f"KMZ:  {kmz_path}")

        # --- OBL ---
        elif route_type == "obl":
            from lib.file_creator import create_obl_kml, create_obl_wpml
            from lib.package_creator import create_zip_files_from_dir_with_part

            gimbal_angle, row_side, perp_side = oblique_settings

            # Splitting check
            waypoint_threshold = 50
            num_parts = None
            if len(objects) >= waypoint_threshold:
                num_parts = ask_user_for_splitting(len(objects))

            if num_parts is None:
                objects_to_process = [(objects, None)]
            else:
                object_parts = split_objects(objects, num_parts)
                objects_to_process = [(part, i + 1) for i, part in enumerate(object_parts)]
                print(f"\nSplit into {num_parts} parts:")
                for i, part in enumerate(object_parts):
                    print(f"  Part {i + 1}: {len(part)} objects")

            directions = [("row", row_side), ("perpendicular", perp_side)]
            for objects_part, part_num in objects_to_process:
                for flight_direction, direction_side in directions:
                    direction_suffix = "row" if flight_direction == "row" else "perp"
                    flight_name_with_dir = f"{flight_name}_{direction_suffix}"

                    wpmz_dir = "wpmz"
                    os.makedirs(wpmz_dir, exist_ok=True)

                    kml_content = create_obl_kml(
                        objects_part, flight_direction, height, gimbal_angle,
                        direction_side, speed, drone_config
                    )
                    with open(os.path.join(wpmz_dir, "template.kml"), "w", encoding="utf-8") as f:
                        f.write(kml_content)

                    wpml_content = create_obl_wpml(
                        objects_part, flight_direction, height, gimbal_angle,
                        direction_side, speed, drone_config
                    )
                    with open(os.path.join(wpmz_dir, "waylines.wpml"), "w", encoding="utf-8") as f:
                        f.write(wpml_content)

                    zip_path, kmz_path = create_zip_files_from_dir_with_part(
                        wpmz_dir, "obl", flight_name_with_dir, output_dir, part_num
                    )
                    print(f"WPMZ: {zip_path}")
                    print(f"KMZ:  {kmz_path}")

        # --- VD ---
        else:
            from lib.file_creator import create_vd_kml, create_vd_wpml
            from lib.package_creator import create_zip_files_from_dir_with_part

            # Splitting check
            num_parts = None
            if len(objects) >= 100:
                num_parts = ask_user_for_splitting(len(objects))

            if num_parts is None:
                objects_to_process = [(objects, None)]
            else:
                object_parts = split_objects(objects, num_parts)
                objects_to_process = [(part, i + 1) for i, part in enumerate(object_parts)]
                print(f"\nSplit into {num_parts} parts:")
                for i, part in enumerate(object_parts):
                    print(f"  Part {i + 1}: {len(part)} objects")

            for objects_part, part_num in objects_to_process:
                wpmz_dir = "wpmz"
                os.makedirs(wpmz_dir, exist_ok=True)

                kml_content = create_vd_kml(objects_part, height, speed, drone_config)
                with open(os.path.join(wpmz_dir, "template.kml"), "w", encoding="utf-8") as f:
                    f.write(kml_content)

                wpml_content = create_vd_wpml(objects_part, height, speed, drone_config)
                with open(os.path.join(wpmz_dir, "waylines.wpml"), "w", encoding="utf-8") as f:
                    f.write(wpml_content)

                zip_path, kmz_path = create_zip_files_from_dir_with_part(
                    wpmz_dir, "vd", flight_name, output_dir, part_num
                )
                print(f"WPMZ: {zip_path}")
                print(f"KMZ:  {kmz_path}")

        print(f"\nDone! Route type: {route_type.upper()}")
        if route_type == "obl":
            print("Generated row and perpendicular direction files.")
        if route_type == "mapping2d":
            area = _polygon_area_m2(mapping_corners)
            print(f"Survey area: {area:.0f} m2")
        elif num_parts:
            print(f"Total objects: {len(objects)} ({num_parts} parts)")
        else:
            print(f"Objects: {len(objects)}")

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
