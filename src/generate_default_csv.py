#!/usr/bin/env python3
"""
This script generates template CSV files for drone route planning.
The CSV files contain corner coordinates of target objects, which are used by generate_flight_files.py.

CSV format: Each row represents one object with four corner coordinates.
Each row has 8 columns in the format: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4
"""

import csv
import argparse
import math
import os

def calculate_corners(center_lat, center_lon, width, height, rotation=0):
    """
    Calculate the four corners of a rectangle given its center, dimensions, and rotation.
    
    Parameters:
    - center_lat, center_lon: Center coordinates in decimal degrees
    - width, height: Dimensions in meters
    - rotation: Rotation angle in degrees (0 = North-aligned)
    
    Returns:
    - List of four corner coordinates [(lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)]
    """
    # Convert degrees to radians
    rotation_rad = math.radians(rotation)
    
    # Approximate conversion from meters to degrees (rough estimation)
    # These will vary based on latitude, but for small areas, this approximation works
    lat_meter = 1 / 111111  # 1 meter in degrees latitude
    lon_meter = 1 / (111111 * math.cos(math.radians(center_lat)))  # 1 meter in degrees longitude
    
    # Half-width and half-height in degrees
    half_width_deg = (width / 2) * lon_meter
    half_height_deg = (height / 2) * lat_meter
    
    # Calculate corners (counter-clockwise from bottom-left)
    # Without rotation first
    corners = [
        (-half_height_deg, -half_width_deg),  # bottom-left
        (half_height_deg, -half_width_deg),   # top-left
        (half_height_deg, half_width_deg),    # top-right
        (-half_height_deg, half_width_deg)    # bottom-right
    ]
    
    # Apply rotation
    rotated_corners = []
    for dlat, dlon in corners:
        # Rotate the point around the origin
        rotated_dlat = dlat * math.cos(rotation_rad) - dlon * math.sin(rotation_rad)
        rotated_dlon = dlat * math.sin(rotation_rad) + dlon * math.cos(rotation_rad)
        
        # Calculate absolute coordinates
        lat = center_lat + rotated_dlat
        lon = center_lon + rotated_dlon
        
        rotated_corners.append((lat, lon))
    
    return rotated_corners

def generate_default_csv(output_file, num_objects=1, area_width=3, area_height=3):
    """
    Generate a template CSV file with default values.
    Creates one or more rectangular objects with specified dimensions.
    """
    # Default area: near Tokyo, Japan
    center_lat = 35.6895
    center_lon = 139.6917
    
    # List to store objects
    objects = []
    
    # Create objects in a line, separated by 10 meters
    for i in range(num_objects):
        # Offset each object by 10 meters eastward
        obj_lon = center_lon + (i * 10 / (111111 * math.cos(math.radians(center_lat))))
        
        # Calculate corners
        corners = calculate_corners(center_lat, obj_lon, area_width, area_height)
        
        # Flatten the list of corners
        flat_corners = []
        for lat, lon in corners:
            flat_corners.append(lat)
            flat_corners.append(lon)
        
        objects.append(flat_corners)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for obj in objects:
            writer.writerow(obj)
    
    print(f"Created template CSV file: {output_file}")
    print(f"Generated {num_objects} object(s) with dimensions {area_width}m x {area_height}m")
    print("CSV format: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4")
    print("Each row represents one target object with four corner coordinates.")

def main():
    parser = argparse.ArgumentParser(description="Generate template CSV files for drone route planning.")
    parser.add_argument("--output", type=str, default="template_targets.csv",
                        help="Output CSV filename (default: template_targets.csv)")
    parser.add_argument("--num", type=int, default=1,
                        help="Number of objects to generate (default: 1)")
    parser.add_argument("--width", type=float, default=3.0,
                        help="Width of each object in meters (default: 3.0)")
    parser.add_argument("--height", type=float, default=3.0,
                        help="Height of each object in meters (default: 3.0)")
    args = parser.parse_args()
    
    generate_default_csv(args.output, args.num, args.width, args.height)

if __name__ == "__main__":
    main()
