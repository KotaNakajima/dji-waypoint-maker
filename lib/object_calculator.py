#!/usr/bin/env python3
"""
Module for calculating object details based on corner coordinates.
"""

import math

def calculate_object_details(corners, round_precision=3):
    """
    Calculate center coordinates and orientation of the object based on its four corners.
    Returns (center_lat, center_lon, heading_angle)
    - heading_angle: -180 to 180, aligned with the rectangle edges, preferring north orientation
    - round_precision: Number of decimal places to round the heading angle to
    """
    # Calculate center as average of four corners
    center_lat = sum(corner[0] for corner in corners) / 4
    center_lon = sum(corner[1] for corner in corners) / 4
    
    # Calculate bearings for each edge
    bearings = []
    for i in range(4):
        next_i = (i + 1) % 4
        lat1, lon1 = corners[i]
        lat2, lon2 = corners[next_i]
        
        # Calculate bearing (heading)
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        dlon = lon2_rad - lon1_rad
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        bearing = math.degrees(math.atan2(y, x))
        
        # Normalize bearing to -180 to 180 range
        if bearing < -180: 
            bearing += 360
        elif bearing > 180: 
            bearing -= 360
            
        bearings.append(bearing)
    
    # Calculate deviation from north-south axis for each edge
    ns_deviations = []
    for angle in bearings:
        # Find minimum deviation from either 0 degrees (north) or 180 degrees (south)
        ns_deviation = min(abs(angle), abs(abs(angle) - 180))
        ns_deviations.append(ns_deviation)
    
    # Find the edge most aligned with north-south
    ns_edge_index = ns_deviations.index(min(ns_deviations))
    heading_angle = bearings[ns_edge_index]
    
    # Ensure the heading is oriented towards north rather than south
    if abs(heading_angle) > 90:
        # If pointing south (>90 or <-90), rotate 180 degrees to point north
        if heading_angle > 0:
            heading_angle -= 180
        else:
            heading_angle += 180
    
    # Round the heading angle to the specified precision
    heading_angle = round(heading_angle, round_precision)
    
    return center_lat, center_lon, heading_angle
