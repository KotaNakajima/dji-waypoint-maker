#!/usr/bin/env python3
"""
Module for creating mapping2d KML/WPML files for DJI drone missions.
Generates both template.kml and waylines.wpml with calculated flight paths.
"""

import math
import time

from lib.drone_config import get_effective_camera


# ---------------------------------------------------------------------------
# Flight line calculation
# ---------------------------------------------------------------------------

def calculate_mapping2d_spacing(height, forward_overlap, side_overlap, drone_config):
    """
    Calculate line spacing and photo interval from camera specs and overlap rates.

    When M3M is selected with multispectral, uses the multispectral camera
    specs (narrower FOV) as the limiting factor for spacing.

    Returns:
        (line_spacing_m, photo_interval_m)
    """
    cam = get_effective_camera(drone_config)
    hfov = math.radians(cam["horizontal_fov_deg"])
    vfov = math.radians(cam["vertical_fov_deg"])

    # Ground footprint at given height (nadir)
    footprint_across = 2.0 * height * math.tan(hfov / 2.0)  # perpendicular to flight
    footprint_along = 2.0 * height * math.tan(vfov / 2.0)   # along flight direction

    line_spacing = footprint_across * (1.0 - side_overlap / 100.0)
    photo_interval = footprint_along * (1.0 - forward_overlap / 100.0)

    return line_spacing, photo_interval


def generate_mapping2d_waypoints(polygon, direction_deg, line_spacing, margin):
    """
    Generate serpentine flight path waypoints across a polygon.

    Args:
        polygon: List of (lat, lon) tuples defining the boundary.
        direction_deg: Flight direction in degrees (0=north, 90=east).
        line_spacing: Distance between parallel flight lines in meters.
        margin: Extension of each line beyond polygon boundary in meters.

    Returns:
        List of (lat, lon) waypoints in flight order.
    """
    n = len(polygon)
    ref_lat = sum(p[0] for p in polygon) / n
    ref_lon = sum(p[1] for p in polygon) / n

    lat_m = 111111.0
    lon_m = 111111.0 * math.cos(math.radians(ref_lat))

    # Convert to local meters (x=east, y=north)
    local = [((p[1] - ref_lon) * lon_m, (p[0] - ref_lat) * lat_m) for p in polygon]

    # Rotate so flight direction aligns with X-axis
    alpha = math.radians(direction_deg - 90)
    cos_a = math.cos(alpha)
    sin_a = math.sin(alpha)
    rotated = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in local]

    # Bounding box in rotated space (Y = perpendicular to flight)
    min_y = min(p[1] for p in rotated)
    max_y = max(p[1] for p in rotated)

    # Generate scan lines
    waypoints_rotated = []
    y = min_y
    line_idx = 0

    while y <= max_y + 0.001:
        # Find intersections of horizontal line y with polygon edges
        intersections = []
        n_pts = len(rotated)
        for i in range(n_pts):
            j = (i + 1) % n_pts
            y1, y2 = rotated[i][1], rotated[j][1]
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                x = rotated[i][0] + t * (rotated[j][0] - rotated[i][0])
                intersections.append(x)

        if len(intersections) >= 2:
            intersections.sort()
            x_start = intersections[0] - margin
            x_end = intersections[-1] + margin

            if line_idx % 2 == 0:
                waypoints_rotated.append((x_start, y))
                waypoints_rotated.append((x_end, y))
            else:
                waypoints_rotated.append((x_end, y))
                waypoints_rotated.append((x_start, y))
            line_idx += 1

        y += line_spacing

    # Rotate back and convert to lat/lon
    waypoints = []
    for rx, ry in waypoints_rotated:
        x = rx * cos_a + ry * sin_a
        y_local = -rx * sin_a + ry * cos_a
        lat = ref_lat + y_local / lat_m
        lon = ref_lon + x / lon_m
        waypoints.append((lat, lon))

    return waypoints


# ---------------------------------------------------------------------------
# template.kml generation
# ---------------------------------------------------------------------------

def create_mapping2d_kml(polygons, height, speed, forward_overlap, side_overlap,
                         direction, margin, shoot_type, drone_config):
    """
    Generate a mapping2d KML template for area-based survey missions.

    Args:
        polygons: List of polygon corner lists. Each polygon is a list of
                  (lat, lon) tuples defining the survey boundary.
        height: Flight height in meters (relative to start point)
        speed: Auto flight speed in m/s
        forward_overlap: Forward overlap percentage (0-100)
        side_overlap: Side overlap percentage (0-100)
        direction: Flight direction in degrees (0=north, 90=east)
        margin: Margin distance in meters beyond polygon boundary
        shoot_type: "time" or "distance" for photo trigger mode
        drone_config: Dict from drone_config.get_drone_config()

    Returns:
        KML XML string
    """
    current_time = int(time.time() * 1000)
    drone_enum = drone_config["droneEnumValue"]
    drone_sub_enum = drone_config["droneSubEnumValue"]
    payload_enum = drone_config["payloadEnumValue"]
    payload_sub_enum = drone_config["payloadSubEnumValue"]
    payload_pos = drone_config["payloadPositionIndex"]
    image_format = drone_config["imageFormat"]

    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
    <Document>
        <wpml:author>DroneRouteGenerator</wpml:author>
        <wpml:createTime>{current_time}</wpml:createTime>
        <wpml:updateTime>{current_time}</wpml:updateTime>
        <wpml:missionConfig>
            <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
            <wpml:finishAction>goHome</wpml:finishAction>
            <wpml:exitOnRCLost>goContinue</wpml:exitOnRCLost>
            <wpml:executeRCLostAction>hover</wpml:executeRCLostAction>
            <wpml:takeOffSecurityHeight>{height}</wpml:takeOffSecurityHeight>
            <wpml:globalTransitionalSpeed>{speed}</wpml:globalTransitionalSpeed>
            <wpml:droneInfo>
                <wpml:droneEnumValue>{drone_enum}</wpml:droneEnumValue>
                <wpml:droneSubEnumValue>{drone_sub_enum}</wpml:droneSubEnumValue>
            </wpml:droneInfo>
            <wpml:payloadInfo>
                <wpml:payloadEnumValue>{payload_enum}</wpml:payloadEnumValue>
                <wpml:payloadSubEnumValue>{payload_sub_enum}</wpml:payloadSubEnumValue>
                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            </wpml:payloadInfo>
        </wpml:missionConfig>'''

    for idx, polygon in enumerate(polygons):
        coords_str = _polygon_to_coords_string(polygon, close=True)

        kml += f'''
    <Folder>
      <wpml:templateType>mapping2d</wpml:templateType>
      <wpml:templateId>{idx}</wpml:templateId>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
        <wpml:positioningType>RTKBaseStation</wpml:positioningType>
        <wpml:globalShootHeight>{height}</wpml:globalShootHeight>
        <wpml:surfaceFollowModeEnable>0</wpml:surfaceFollowModeEnable>
        <wpml:surfaceRelativeHeight>0</wpml:surfaceRelativeHeight>
      </wpml:waylineCoordinateSysParam>
      <wpml:payloadParam>
        <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
        <wpml:imageFormat>{image_format}</wpml:imageFormat>
      </wpml:payloadParam>
      <wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:globalWaypointTurnMode>
      <wpml:globalUseStraightLine>1</wpml:globalUseStraightLine>
      <wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode>
      <wpml:globalWaypointHeadingParam>
        <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
        <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
      </wpml:globalWaypointHeadingParam>
      <wpml:overlap>
        <wpml:orthoLidarOverlapH>{forward_overlap}</wpml:orthoLidarOverlapH>
        <wpml:orthoLidarOverlapW>{side_overlap}</wpml:orthoLidarOverlapW>
        <wpml:orthoCameraOverlapH>{forward_overlap}</wpml:orthoCameraOverlapH>
        <wpml:orthoCameraOverlapW>{side_overlap}</wpml:orthoCameraOverlapW>
      </wpml:overlap>
      <wpml:shootType>{shoot_type}</wpml:shootType>
      <wpml:direction>{direction}</wpml:direction>
      <wpml:margin>{margin}</wpml:margin>
      <wpml:globalHeight>{height}</wpml:globalHeight>
      <Placemark>
        <wpml:caliFlightEnable>0</wpml:caliFlightEnable>
        <wpml:elevationOptimizeEnable>1</wpml:elevationOptimizeEnable>
        <wpml:smartObliqueEnable>0</wpml:smartObliqueEnable>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>{coords_str}</coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
        <wpml:ellipsoidHeight>{height}</wpml:ellipsoidHeight>
        <wpml:height>{height}</wpml:height>
      </Placemark>
    </Folder>'''

    kml += '''
      </Document>
    </kml>'''

    return kml


# ---------------------------------------------------------------------------
# waylines.wpml generation
# ---------------------------------------------------------------------------

def create_mapping2d_wpml(waypoints, height, speed, photo_interval,
                          shoot_type, drone_config):
    """
    Generate waylines.wpml for mapping2d flight execution.

    Args:
        waypoints: List of (lat, lon) tuples from generate_mapping2d_waypoints().
        height: Flight height in meters.
        speed: Flight speed in m/s.
        photo_interval: Photo spacing in meters (from calculate_mapping2d_spacing).
        shoot_type: "time" or "distance".
        drone_config: Dict from drone_config.get_drone_config().

    Returns:
        WPML XML string
    """
    drone_enum = drone_config["droneEnumValue"]
    drone_sub_enum = drone_config["droneSubEnumValue"]
    payload_enum = drone_config["payloadEnumValue"]
    payload_sub_enum = drone_config["payloadSubEnumValue"]
    payload_pos = drone_config["payloadPositionIndex"]

    last_idx = len(waypoints) - 1

    # Photo trigger type and interval
    if shoot_type == "distance":
        trigger_type = "multipleDistance"
        trigger_param = round(photo_interval, 2)
    else:  # time
        trigger_type = "multipleTiming"
        trigger_param = round(photo_interval / speed, 2) if speed > 0 else 2.0

    wpml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.6">
    <Document>
        <wpml:missionConfig>
            <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
            <wpml:finishAction>goHome</wpml:finishAction>
            <wpml:exitOnRCLost>goContinue</wpml:exitOnRCLost>
            <wpml:executeRCLostAction>hover</wpml:executeRCLostAction>
            <wpml:takeOffSecurityHeight>{height}</wpml:takeOffSecurityHeight>
            <wpml:globalTransitionalSpeed>{speed}</wpml:globalTransitionalSpeed>
            <wpml:globalRTHHeight>20</wpml:globalRTHHeight>
            <wpml:droneInfo>
                <wpml:droneEnumValue>{drone_enum}</wpml:droneEnumValue>
                <wpml:droneSubEnumValue>{drone_sub_enum}</wpml:droneSubEnumValue>
            </wpml:droneInfo>
            <wpml:payloadInfo>
                <wpml:payloadEnumValue>{payload_enum}</wpml:payloadEnumValue>
                <wpml:payloadSubEnumValue>{payload_sub_enum}</wpml:payloadSubEnumValue>
                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            </wpml:payloadInfo>
        </wpml:missionConfig>
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>'''

    for i, (lat, lon) in enumerate(waypoints):
        wpml += f'''
      <Placemark>
        <Point>
          <coordinates>{lon},{lat}</coordinates>
        </Point>
        <wpml:index>{i}</wpml:index>
        <wpml:executeHeight>{height}</wpml:executeHeight>
        <wpml:waypointSpeed>{speed}</wpml:waypointSpeed>
        <wpml:waypointHeadingParam>
          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
          <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
          <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
        </wpml:waypointHeadingParam>
        <wpml:waypointTurnParam>
          <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
          <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
        </wpml:waypointTurnParam>
        <wpml:useStraightLine>1</wpml:useStraightLine>'''

        if i == 0:
            # First waypoint: gimbal rotation to nadir
            wpml += f'''
        <wpml:actionGroup>
          <wpml:actionGroupId>0</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>0</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>0</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
              <wpml:gimbalHeadingYawBase>north</wpml:gimbalHeadingYawBase>
              <wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode>
              <wpml:gimbalPitchRotateEnable>1</wpml:gimbalPitchRotateEnable>
              <wpml:gimbalPitchRotateAngle>-90</wpml:gimbalPitchRotateAngle>
              <wpml:gimbalRollRotateEnable>0</wpml:gimbalRollRotateEnable>
              <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
              <wpml:gimbalYawRotateEnable>0</wpml:gimbalYawRotateEnable>
              <wpml:gimbalYawRotateAngle>0</wpml:gimbalYawRotateAngle>
              <wpml:gimbalRotateTimeEnable>0</wpml:gimbalRotateTimeEnable>
              <wpml:gimbalRotateTime>0</wpml:gimbalRotateTime>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>
        <wpml:actionGroup>
          <wpml:actionGroupId>1</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>{last_idx}</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>{trigger_type}</wpml:actionTriggerType>
            <wpml:actionTriggerParam>{trigger_param}</wpml:actionTriggerParam>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>0</wpml:actionId>
            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>'''

        wpml += '''
      </Placemark>'''

    wpml += '''
    </Folder>
      </Document>
    </kml>'''

    return wpml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _polygon_to_coords_string(polygon, close=True):
    """
    Convert a list of (lat, lon) tuples to KML coordinates string (lon,lat,0).
    If close=True, repeats the first point at the end to close the polygon.
    """
    coords = []
    for lat, lon in polygon:
        coords.append(f"{lon},{lat},0")
    if close and polygon:
        first_lat, first_lon = polygon[0]
        coords.append(f"{first_lon},{first_lat},0")
    return " ".join(coords)
