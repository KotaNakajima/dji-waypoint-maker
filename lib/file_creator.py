#!/usr/bin/env python3
"""
Module for creating KML and WPML files for drone flight missions.
Supports VD (Vertical Down) and OBL (Oblique Photography) route types.
"""

import time
import math
from lib.object_calculator import calculate_object_details
from lib.drone_config import DEFAULT_OBL_ZOOM, DEFAULT_MISSION_CONFIG
from lib.xml_helpers import (
    build_mission_config_kml, build_mission_config_wpml,
    build_payload_param, build_start_action_group, calculate_total_distance,
)


# ---------------------------------------------------------------------------
# VD (Vertical Down) route generation
# ---------------------------------------------------------------------------

def create_vd_kml(objects, height, speed, drone_config, mission_config=None):
    """
    Generate a KML template for VD (Vertical Down) routes.

    Args:
        objects: List of corner-coordinate sets (with optional identifier tuples)
        height: Flight height in meters
        speed: Flight speed in m/s
        drone_config: Dict from drone_config.get_drone_config()
        mission_config: Optional mission config dict (defaults to DEFAULT_MISSION_CONFIG)

    Returns:
        KML XML string
    """
    if mission_config is None:
        mission_config = DEFAULT_MISSION_CONFIG

    current_time = int(time.time() * 1000)
    payload_pos = drone_config["payloadPositionIndex"]

    mission_config_xml = build_mission_config_kml(drone_config, mission_config)
    payload_param_xml = build_payload_param(drone_config, mission_config)

    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
    <Document>
        <wpml:author>DroneRouteGenerator</wpml:author>
        <wpml:createTime>{current_time}</wpml:createTime>
        <wpml:updateTime>{current_time}</wpml:updateTime>
        {mission_config_xml}'''

    kml += f'''
    <Folder>
      <wpml:templateType>waypoint</wpml:templateType>
      <wpml:templateId>0</wpml:templateId>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
        <wpml:positioningType>RTKBaseStation</wpml:positioningType>
        <wpml:globalShootHeight>{height}</wpml:globalShootHeight>
        <wpml:surfaceFollowModeEnable>0</wpml:surfaceFollowModeEnable>
        <wpml:surfaceRelativeHeight>0</wpml:surfaceRelativeHeight>
      </wpml:waylineCoordinateSysParam>
      {payload_param_xml}
      <wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:globalWaypointTurnMode>
      <wpml:globalUseStraightLine>1</wpml:globalUseStraightLine>
      <wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode>
      <wpml:globalHeight>{height}</wpml:globalHeight>
      <wpml:globalWaypointHeadingParam>
        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
        <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
      </wpml:globalWaypointHeadingParam>'''

    total_placemarks = len(objects)
    placemark_id_digits = len(str(total_placemarks))

    placemark_index = 0
    for i, corners in enumerate(objects):
        actual_corners, object_identifier = _extract_corners_and_id(corners)
        center_lat, center_lon, heading_angle = calculate_object_details(actual_corners)
        placemark_id = str(placemark_index).zfill(placemark_id_digits)

        if i == 0:
            # First waypoint includes gimbalRotate action
            kml += f'''
                <Placemark>
                    <Point>
                        <coordinates>
                            {center_lon},{center_lat}
                        </coordinates>
                    </Point>
                    <wpml:index>{placemark_index}</wpml:index>
                    <wpml:useGlobalHeight>1</wpml:useGlobalHeight>
                    <wpml:height>{height}</wpml:height>
                    <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
                    <wpml:useGlobalHeadingParam>0</wpml:useGlobalHeadingParam>
                    <wpml:waypointHeadingParam>
                        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
                        <wpml:waypointHeadingAngle>{heading_angle}</wpml:waypointHeadingAngle>
                        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
                    </wpml:waypointHeadingParam>
                    <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
                    <wpml:useStraightLine>1</wpml:useStraightLine>
                    <wpml:gimbalPitchAngle>-90</wpml:gimbalPitchAngle>
                    <wpml:actionGroup>
                        <wpml:actionGroupId>{placemark_index}</wpml:actionGroupId>
                        <wpml:actionGroupStartIndex>{placemark_index}</wpml:actionGroupStartIndex>
                        <wpml:actionGroupEndIndex>{placemark_index}</wpml:actionGroupEndIndex>
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
                        <wpml:action>
                            <wpml:actionId>1</wpml:actionId>
                            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
                            <wpml:actionActuatorFuncParam>
                                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                                <wpml:fileSuffix>at_{object_identifier if object_identifier else placemark_id}</wpml:fileSuffix>
                            </wpml:actionActuatorFuncParam>
                        </wpml:action>
                    </wpml:actionGroup>
                </Placemark>'''
        else:
            kml += f'''
                <Placemark>
                    <Point>
                        <coordinates>
                            {center_lon},{center_lat}
                        </coordinates>
                    </Point>
                    <wpml:index>{placemark_index}</wpml:index>
                    <wpml:useGlobalHeight>1</wpml:useGlobalHeight>
                    <wpml:height>{height}</wpml:height>
                    <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
                    <wpml:useGlobalHeadingParam>0</wpml:useGlobalHeadingParam>
                    <wpml:waypointHeadingParam>
                        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
                        <wpml:waypointHeadingAngle>{heading_angle}</wpml:waypointHeadingAngle>
                        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
                    </wpml:waypointHeadingParam>
                    <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
                    <wpml:useStraightLine>1</wpml:useStraightLine>
                    <wpml:gimbalPitchAngle>-90</wpml:gimbalPitchAngle>
                    <wpml:actionGroup>
                        <wpml:actionGroupId>{placemark_index}</wpml:actionGroupId>
                        <wpml:actionGroupStartIndex>{placemark_index}</wpml:actionGroupStartIndex>
                        <wpml:actionGroupEndIndex>{placemark_index}</wpml:actionGroupEndIndex>
                        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
                        <wpml:actionTrigger>
                            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
                        </wpml:actionTrigger>
                        <wpml:action>
                            <wpml:actionId>0</wpml:actionId>
                            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
                            <wpml:actionActuatorFuncParam>
                                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                                <wpml:fileSuffix>at_{object_identifier if object_identifier else placemark_id}</wpml:fileSuffix>
                            </wpml:actionActuatorFuncParam>
                        </wpml:action>
                    </wpml:actionGroup>
                </Placemark>'''
        placemark_index += 1

    kml += '''
        </Folder>'''
    kml += '''
      </Document>
    </kml>'''
    return kml


def create_vd_wpml(objects, height, speed, drone_config, mission_config=None):
    """
    Generate a WPML waylines file for VD routes.

    Args:
        objects: List of corner-coordinate sets (with optional identifier tuples)
        height: Flight height in meters
        speed: Flight speed in m/s
        drone_config: Dict from drone_config.get_drone_config()
        mission_config: Optional mission config dict (defaults to DEFAULT_MISSION_CONFIG)

    Returns:
        WPML XML string
    """
    if mission_config is None:
        mission_config = DEFAULT_MISSION_CONFIG

    payload_pos = drone_config["payloadPositionIndex"]

    mission_config_xml = build_mission_config_wpml(drone_config, mission_config)
    start_action_xml = build_start_action_group(payload_pos, gimbal_pitch=-90)

    # Pre-compute waypoint coordinates for distance calculation
    waypoint_coords = []
    for corners in objects:
        actual_corners, _ = _extract_corners_and_id(corners)
        center_lat, center_lon, _ = calculate_object_details(actual_corners)
        waypoint_coords.append((center_lat, center_lon))

    total_distance = calculate_total_distance(waypoint_coords)
    duration = total_distance / speed if speed > 0 else 0

    wpml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.6">
    <Document>
        {mission_config_xml}'''

    wpml += f'''
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:distance>{total_distance:.1f}</wpml:distance>
      <wpml:duration>{duration:.1f}</wpml:duration>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
      {start_action_xml}'''

    total_placemarks = len(objects)
    placemark_id_digits = len(str(total_placemarks))

    placemark_index = 0
    for i, corners in enumerate(objects):
        actual_corners, object_identifier = _extract_corners_and_id(corners)
        center_lat, center_lon, heading_angle = calculate_object_details(actual_corners)
        placemark_id = str(placemark_index).zfill(placemark_id_digits)

        # All waypoints now have the same structure (gimbalRotate moved to startActionGroup)
        wpml += f'''
                <Placemark>
                    <Point>
                        <coordinates>
                            {center_lon},{center_lat}
                        </coordinates>
                    </Point>
                    <wpml:index>{placemark_index}</wpml:index>
                    <wpml:executeHeight>{height}</wpml:executeHeight>
                    <wpml:waypointSpeed>{speed}</wpml:waypointSpeed>
                    <wpml:waypointHeadingParam>
                        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
                        <wpml:waypointHeadingAngle>{heading_angle}</wpml:waypointHeadingAngle>
                        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
                    </wpml:waypointHeadingParam>
                    <wpml:waypointTurnParam>
                        <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
                        <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
                    </wpml:waypointTurnParam>
                    <wpml:actionGroup>
                        <wpml:actionGroupId>{placemark_index}</wpml:actionGroupId>
                        <wpml:actionGroupStartIndex>{placemark_index}</wpml:actionGroupStartIndex>
                        <wpml:actionGroupEndIndex>{placemark_index}</wpml:actionGroupEndIndex>
                        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
                        <wpml:actionTrigger>
                            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
                        </wpml:actionTrigger>
                        <wpml:action>
                            <wpml:actionId>0</wpml:actionId>
                            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
                            <wpml:actionActuatorFuncParam>
                                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                                <wpml:fileSuffix>at_{object_identifier if object_identifier else placemark_id}</wpml:fileSuffix>
                            </wpml:actionActuatorFuncParam>
                        </wpml:action>
                    </wpml:actionGroup>
                    <wpml:waypointGimbalHeadingParam>
                      <wpml:waypointGimbalPitchAngle>0</wpml:waypointGimbalPitchAngle>
                      <wpml:waypointGimbalYawAngle>0</wpml:waypointGimbalYawAngle>
                    </wpml:waypointGimbalHeadingParam>
                    <wpml:isRisky>0</wpml:isRisky>
                    <wpml:waypointWorkType>0</wpml:waypointWorkType>
                </Placemark>'''
        placemark_index += 1

    wpml += '''
        </Folder>'''
    wpml += '''
      </Document>
    </kml>'''
    return wpml


# ---------------------------------------------------------------------------
# OBL (Oblique Photography) route generation
# ---------------------------------------------------------------------------

def calculate_oblique_waypoint_position(center_lat, center_lon, heading_angle,
                                        altitude, gimbal_angle, direction,
                                        flight_direction):
    """
    Calculate waypoint position for oblique photography.

    Args:
        center_lat: Target latitude
        center_lon: Target longitude
        heading_angle: Row-direction heading from VD calculation
        altitude: Flight altitude in meters
        gimbal_angle: Gimbal tilt angle (90 = nadir)
        direction: Shooting direction ("north", "south", "east", "west")
        flight_direction: "row" or "perpendicular"

    Returns:
        (waypoint_lat, waypoint_lon, camera_heading)
    """
    horizontal_distance = altitude * math.tan(math.radians(abs(90 - gimbal_angle)))

    direction_angles = {
        "north": 0,
        "south": 180,
        "east": 90,
        "west": -90,
    }
    waypoint_angle = direction_angles[direction]

    lat_rad = math.radians(center_lat)
    dlat = (horizontal_distance * math.cos(math.radians(waypoint_angle))) / 111111
    dlon = (horizontal_distance * math.sin(math.radians(waypoint_angle))) / (111111 * math.cos(lat_rad))

    waypoint_lat = center_lat + dlat
    waypoint_lon = center_lon + dlon

    dx = center_lon - waypoint_lon
    dy = center_lat - waypoint_lat
    camera_heading = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    if camera_heading > 180:
        camera_heading -= 360

    return waypoint_lat, waypoint_lon, camera_heading


def create_obl_kml(objects, flight_direction, altitude, gimbal_angle,
                   direction, speed, drone_config, mission_config=None):
    """
    Generate a KML template for OBL (Oblique Photography) routes.

    Args:
        objects: List of corner-coordinate sets
        flight_direction: "row" or "perpendicular"
        altitude: Flight altitude in meters
        gimbal_angle: Gimbal tilt angle (90 = nadir)
        direction: Shooting direction ("north"/"south"/"east"/"west")
        speed: Flight speed in m/s
        drone_config: Dict from drone_config.get_drone_config()
        mission_config: Optional mission config dict (defaults to DEFAULT_MISSION_CONFIG)

    Returns:
        KML XML string
    """
    if mission_config is None:
        mission_config = DEFAULT_MISSION_CONFIG

    current_time = int(time.time() * 1000)
    payload_pos = drone_config["payloadPositionIndex"]

    mission_config_xml = build_mission_config_kml(drone_config, mission_config)
    payload_param_xml = build_payload_param(drone_config, mission_config)

    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
    <Document>
        <wpml:author>DroneRouteGenerator</wpml:author>
        <wpml:createTime>{current_time}</wpml:createTime>
        <wpml:updateTime>{current_time}</wpml:updateTime>
        {mission_config_xml}'''

    kml += f'''
    <Folder>
      <wpml:templateType>waypoint</wpml:templateType>
      <wpml:templateId>0</wpml:templateId>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
        <wpml:positioningType>RTKBaseStation</wpml:positioningType>
        <wpml:globalShootHeight>{altitude}</wpml:globalShootHeight>
        <wpml:surfaceFollowModeEnable>0</wpml:surfaceFollowModeEnable>
        <wpml:surfaceRelativeHeight>0</wpml:surfaceRelativeHeight>
      </wpml:waylineCoordinateSysParam>
      {payload_param_xml}
      <wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:globalWaypointTurnMode>
      <wpml:globalUseStraightLine>1</wpml:globalUseStraightLine>
      <wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode>
      <wpml:globalHeight>{altitude}</wpml:globalHeight>
      <wpml:globalWaypointHeadingParam>
        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
        <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
      </wpml:globalWaypointHeadingParam>'''

    total_placemarks = len(objects)
    placemark_id_digits = len(str(total_placemarks))

    placemark_index = 0
    for i, corners in enumerate(objects):
        actual_corners, object_identifier = _extract_corners_and_id(corners)
        center_lat, center_lon, heading_angle = calculate_object_details(actual_corners)

        waypoint_lat, waypoint_lon, camera_heading = calculate_oblique_waypoint_position(
            center_lat, center_lon, heading_angle, altitude, gimbal_angle,
            direction, flight_direction
        )

        placemark_id = str(placemark_index).zfill(placemark_id_digits)
        direction_suffix = flight_direction[:3]  # "row" or "per"

        kml += f'''
                <Placemark>
                    <Point>
                        <coordinates>
                            {waypoint_lon},{waypoint_lat}
                        </coordinates>
                    </Point>
                    <wpml:index>{placemark_index}</wpml:index>
                    <wpml:useGlobalHeight>1</wpml:useGlobalHeight>
                    <wpml:height>{altitude}</wpml:height>
                    <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
                    <wpml:useGlobalHeadingParam>0</wpml:useGlobalHeadingParam>
                    <wpml:waypointHeadingParam>
                        <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
                        <wpml:waypointHeadingAngle>{camera_heading}</wpml:waypointHeadingAngle>
                        <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
                    </wpml:waypointHeadingParam>
                    <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
                    <wpml:useStraightLine>1</wpml:useStraightLine>
                    <wpml:gimbalPitchAngle>-{gimbal_angle}</wpml:gimbalPitchAngle>
                    <wpml:actionGroup>
                        <wpml:actionGroupId>{placemark_index}</wpml:actionGroupId>
                        <wpml:actionGroupStartIndex>{placemark_index}</wpml:actionGroupStartIndex>
                        <wpml:actionGroupEndIndex>{placemark_index}</wpml:actionGroupEndIndex>
                        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
                        <wpml:actionTrigger>
                            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
                        </wpml:actionTrigger>
                        <wpml:action>
                            <wpml:actionId>0</wpml:actionId>
                            <wpml:actionActuatorFunc>zoom</wpml:actionActuatorFunc>
                            <wpml:actionActuatorFuncParam>
                                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                                <wpml:focalLength>{DEFAULT_OBL_ZOOM}</wpml:focalLength>
                            </wpml:actionActuatorFuncParam>
                        </wpml:action>
                        <wpml:action>
                            <wpml:actionId>1</wpml:actionId>
                            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
                            <wpml:actionActuatorFuncParam>
                                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                                <wpml:fileSuffix>obl_{direction_suffix}_{object_identifier if object_identifier else placemark_id}</wpml:fileSuffix>
                            </wpml:actionActuatorFuncParam>
                        </wpml:action>
                    </wpml:actionGroup>
                </Placemark>'''
        placemark_index += 1

    kml += '''
        </Folder>'''
    kml += '''
      </Document>
    </kml>'''
    return kml


def create_obl_wpml(objects, flight_direction, altitude, gimbal_angle,
                    direction, speed, drone_config, mission_config=None):
    """
    Generate a WPML waylines file for OBL routes.

    Args:
        objects: List of corner-coordinate sets
        flight_direction: "row" or "perpendicular"
        altitude: Flight altitude in meters
        gimbal_angle: Gimbal tilt angle (90 = nadir)
        direction: Shooting direction ("north"/"south"/"east"/"west")
        speed: Flight speed in m/s
        drone_config: Dict from drone_config.get_drone_config()
        mission_config: Optional mission config dict (defaults to DEFAULT_MISSION_CONFIG)

    Returns:
        WPML XML string
    """
    if mission_config is None:
        mission_config = DEFAULT_MISSION_CONFIG

    payload_pos = drone_config["payloadPositionIndex"]

    mission_config_xml = build_mission_config_wpml(drone_config, mission_config)
    start_action_xml = build_start_action_group(payload_pos, gimbal_pitch=-gimbal_angle)

    # Pre-compute waypoint coordinates for distance calculation
    waypoint_coords = []
    for corners in objects:
        actual_corners, _ = _extract_corners_and_id(corners)
        center_lat, center_lon, heading_angle = calculate_object_details(actual_corners)
        wp_lat, wp_lon, _ = calculate_oblique_waypoint_position(
            center_lat, center_lon, heading_angle, altitude, gimbal_angle,
            direction, flight_direction
        )
        waypoint_coords.append((wp_lat, wp_lon))

    total_distance = calculate_total_distance(waypoint_coords)
    duration = total_distance / speed if speed > 0 else 0

    wpml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.6">
    <Document>
        {mission_config_xml}'''

    wpml += f'''
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:distance>{total_distance:.1f}</wpml:distance>
      <wpml:duration>{duration:.1f}</wpml:duration>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
      {start_action_xml}'''

    total_placemarks = len(objects)
    placemark_id_digits = len(str(total_placemarks))

    placemark_index = 0
    for i, corners in enumerate(objects):
        actual_corners, object_identifier = _extract_corners_and_id(corners)
        center_lat, center_lon, heading_angle = calculate_object_details(actual_corners)

        waypoint_lat, waypoint_lon, camera_heading = calculate_oblique_waypoint_position(
            center_lat, center_lon, heading_angle, altitude, gimbal_angle,
            direction, flight_direction
        )

        placemark_id = str(placemark_index).zfill(placemark_id_digits)
        direction_suffix = flight_direction[:3]

        # All waypoints now have the same structure (gimbalRotate moved to startActionGroup)
        wpml += f'''
            <Placemark>
                <Point>
                    <coordinates>
                        {waypoint_lon},{waypoint_lat}
                    </coordinates>
                </Point>
                <wpml:index>{placemark_index}</wpml:index>
                <wpml:executeHeight>{altitude}</wpml:executeHeight>
                <wpml:waypointSpeed>{speed}</wpml:waypointSpeed>
                <wpml:waypointHeadingParam>
                    <wpml:waypointHeadingMode>smoothTransition</wpml:waypointHeadingMode>
                    <wpml:waypointHeadingAngle>{camera_heading}</wpml:waypointHeadingAngle>
                    <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
                </wpml:waypointHeadingParam>
                <wpml:waypointTurnParam>
                    <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
                    <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
                </wpml:waypointTurnParam>
                <wpml:actionGroup>
                    <wpml:actionGroupId>{placemark_index}</wpml:actionGroupId>
                    <wpml:actionGroupStartIndex>{placemark_index}</wpml:actionGroupStartIndex>
                    <wpml:actionGroupEndIndex>{placemark_index}</wpml:actionGroupEndIndex>
                    <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
                    <wpml:actionTrigger>
                        <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
                    </wpml:actionTrigger>
                    <wpml:action>
                        <wpml:actionId>0</wpml:actionId>
                        <wpml:actionActuatorFunc>zoom</wpml:actionActuatorFunc>
                        <wpml:actionActuatorFuncParam>
                            <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                            <wpml:focalLength>{DEFAULT_OBL_ZOOM}</wpml:focalLength>
                        </wpml:actionActuatorFuncParam>
                    </wpml:action>
                    <wpml:action>
                        <wpml:actionId>1</wpml:actionId>
                        <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
                        <wpml:actionActuatorFuncParam>
                            <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
                            <wpml:fileSuffix>obl_{direction_suffix}_{object_identifier if object_identifier else placemark_id}</wpml:fileSuffix>
                        </wpml:actionActuatorFuncParam>
                    </wpml:action>
                </wpml:actionGroup>
                <wpml:waypointGimbalHeadingParam>
                  <wpml:waypointGimbalPitchAngle>0</wpml:waypointGimbalPitchAngle>
                  <wpml:waypointGimbalYawAngle>0</wpml:waypointGimbalYawAngle>
                </wpml:waypointGimbalHeadingParam>
                <wpml:isRisky>0</wpml:isRisky>
                <wpml:waypointWorkType>0</wpml:waypointWorkType>
            </Placemark>'''
        placemark_index += 1

    wpml += '''
        </Folder>'''
    wpml += '''
      </Document>
    </kml>'''
    return wpml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_corners_and_id(corners):
    """
    Extract actual corner coordinates and optional identifier from an object entry.

    Returns:
        (actual_corners, object_identifier_str_or_None)
    """
    if isinstance(corners, tuple) and len(corners) == 2:
        actual_corners, identifier = corners
        return actual_corners, str(identifier).zfill(4)
    return corners, None
