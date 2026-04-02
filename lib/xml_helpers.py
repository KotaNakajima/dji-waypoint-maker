#!/usr/bin/env python3
"""
Shared XML builder functions for DJI WPML mission files.
Eliminates duplication of missionConfig, payloadParam, and action group blocks
across VD, OBL, and mapping2d generators.
"""

import math

from lib.drone_config import DEFAULT_MISSION_CONFIG


def build_mission_config_kml(drone_config, mission_config=None):
    """Build <wpml:missionConfig> block for KML (template.kml) files."""
    mc = mission_config or DEFAULT_MISSION_CONFIG
    drone_enum = drone_config["droneEnumValue"]
    drone_sub_enum = drone_config["droneSubEnumValue"]
    payload_enum = drone_config["payloadEnumValue"]
    payload_sub_enum = drone_config["payloadSubEnumValue"]
    payload_pos = drone_config["payloadPositionIndex"]

    return f'''<wpml:missionConfig>
            <wpml:flyToWaylineMode>{mc["flyToWaylineMode"]}</wpml:flyToWaylineMode>
            <wpml:finishAction>{mc["finishAction"]}</wpml:finishAction>
            <wpml:exitOnRCLost>{mc["exitOnRCLost"]}</wpml:exitOnRCLost>
            <wpml:executeRCLostAction>{mc["executeRCLostAction"]}</wpml:executeRCLostAction>
            <wpml:takeOffSecurityHeight>{mc["takeOffSecurityHeight"]}</wpml:takeOffSecurityHeight>
            <wpml:globalTransitionalSpeed>{mc["globalTransitionalSpeed"]}</wpml:globalTransitionalSpeed>
            <wpml:droneInfo>
                <wpml:droneEnumValue>{drone_enum}</wpml:droneEnumValue>
                <wpml:droneSubEnumValue>{drone_sub_enum}</wpml:droneSubEnumValue>
            </wpml:droneInfo>
            <wpml:waylineAvoidLimitAreaMode>{mc["waylineAvoidLimitAreaMode"]}</wpml:waylineAvoidLimitAreaMode>
            <wpml:payloadInfo>
                <wpml:payloadEnumValue>{payload_enum}</wpml:payloadEnumValue>
                <wpml:payloadSubEnumValue>{payload_sub_enum}</wpml:payloadSubEnumValue>
                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            </wpml:payloadInfo>
        </wpml:missionConfig>'''


def build_mission_config_wpml(drone_config, mission_config=None):
    """Build <wpml:missionConfig> block for WPML (waylines.wpml) files.
    Includes globalRTHHeight."""
    mc = mission_config or DEFAULT_MISSION_CONFIG
    drone_enum = drone_config["droneEnumValue"]
    drone_sub_enum = drone_config["droneSubEnumValue"]
    payload_enum = drone_config["payloadEnumValue"]
    payload_sub_enum = drone_config["payloadSubEnumValue"]
    payload_pos = drone_config["payloadPositionIndex"]

    return f'''<wpml:missionConfig>
            <wpml:flyToWaylineMode>{mc["flyToWaylineMode"]}</wpml:flyToWaylineMode>
            <wpml:finishAction>{mc["finishAction"]}</wpml:finishAction>
            <wpml:exitOnRCLost>{mc["exitOnRCLost"]}</wpml:exitOnRCLost>
            <wpml:executeRCLostAction>{mc["executeRCLostAction"]}</wpml:executeRCLostAction>
            <wpml:takeOffSecurityHeight>{mc["takeOffSecurityHeight"]}</wpml:takeOffSecurityHeight>
            <wpml:globalTransitionalSpeed>{mc["globalTransitionalSpeed"]}</wpml:globalTransitionalSpeed>
            <wpml:globalRTHHeight>{mc["globalRTHHeight"]}</wpml:globalRTHHeight>
            <wpml:droneInfo>
                <wpml:droneEnumValue>{drone_enum}</wpml:droneEnumValue>
                <wpml:droneSubEnumValue>{drone_sub_enum}</wpml:droneSubEnumValue>
            </wpml:droneInfo>
            <wpml:waylineAvoidLimitAreaMode>{mc["waylineAvoidLimitAreaMode"]}</wpml:waylineAvoidLimitAreaMode>
            <wpml:payloadInfo>
                <wpml:payloadEnumValue>{payload_enum}</wpml:payloadEnumValue>
                <wpml:payloadSubEnumValue>{payload_sub_enum}</wpml:payloadSubEnumValue>
                <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            </wpml:payloadInfo>
        </wpml:missionConfig>'''


def build_payload_param(drone_config, mission_config=None, include_sensor_fields=False):
    """Build <wpml:payloadParam> block.
    When include_sensor_fields=True (mapping2d), adds LiDAR/sensor-related fields."""
    mc = mission_config or DEFAULT_MISSION_CONFIG
    payload_pos = drone_config["payloadPositionIndex"]
    image_format = drone_config.get("imageFormat", "wide")

    xml = f'''<wpml:payloadParam>
        <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>'''

    if include_sensor_fields:
        xml += f'''
        <wpml:dewarpingEnable>{mc["dewarpingEnable"]}</wpml:dewarpingEnable>
        <wpml:returnMode>{mc["returnMode"]}</wpml:returnMode>
        <wpml:samplingRate>{mc["samplingRate"]}</wpml:samplingRate>
        <wpml:scanningMode>{mc["scanningMode"]}</wpml:scanningMode>
        <wpml:modelColoringEnable>{mc["modelColoringEnable"]}</wpml:modelColoringEnable>'''

    xml += f'''
        <wpml:imageFormat>{image_format}</wpml:imageFormat>
      </wpml:payloadParam>'''

    return xml


def build_start_action_group(payload_pos, gimbal_pitch=-90):
    """Build the <wpml:startActionGroup> initialization sequence for WPML files.
    Matches DJI Pilot 2 behavior: gimbalRotate -> hover -> setFocusType -> focus -> hover."""
    return f'''<wpml:startActionGroup>
        <wpml:action>
          <wpml:actionId>0</wpml:actionId>
          <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:gimbalHeadingYawBase>aircraft</wpml:gimbalHeadingYawBase>
            <wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode>
            <wpml:gimbalPitchRotateEnable>1</wpml:gimbalPitchRotateEnable>
            <wpml:gimbalPitchRotateAngle>{gimbal_pitch}</wpml:gimbalPitchRotateAngle>
            <wpml:gimbalRollRotateEnable>0</wpml:gimbalRollRotateEnable>
            <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
            <wpml:gimbalYawRotateEnable>1</wpml:gimbalYawRotateEnable>
            <wpml:gimbalYawRotateAngle>0</wpml:gimbalYawRotateAngle>
            <wpml:gimbalRotateTimeEnable>0</wpml:gimbalRotateTimeEnable>
            <wpml:gimbalRotateTime>10</wpml:gimbalRotateTime>
            <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
        <wpml:action>
          <wpml:actionId>1</wpml:actionId>
          <wpml:actionActuatorFunc>hover</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:hoverTime>0.5</wpml:hoverTime>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
        <wpml:action>
          <wpml:actionId>2</wpml:actionId>
          <wpml:actionActuatorFunc>setFocusType</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:cameraFocusType>manual</wpml:cameraFocusType>
            <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
        <wpml:action>
          <wpml:actionId>3</wpml:actionId>
          <wpml:actionActuatorFunc>focus</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:focusX>0</wpml:focusX>
            <wpml:focusY>0</wpml:focusY>
            <wpml:focusRegionWidth>0</wpml:focusRegionWidth>
            <wpml:focusRegionHeight>0</wpml:focusRegionHeight>
            <wpml:isPointFocus>0</wpml:isPointFocus>
            <wpml:isInfiniteFocus>1</wpml:isInfiniteFocus>
            <wpml:payloadPositionIndex>{payload_pos}</wpml:payloadPositionIndex>
            <wpml:isCalibrationFocus>0</wpml:isCalibrationFocus>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
        <wpml:action>
          <wpml:actionId>4</wpml:actionId>
          <wpml:actionActuatorFunc>hover</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:hoverTime>1</wpml:hoverTime>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
      </wpml:startActionGroup>'''


def calculate_total_distance(waypoints):
    """Calculate total flight distance in meters from a list of (lat, lon) waypoints."""
    total = 0.0
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        total += _haversine(lat1, lon1, lat2, lon2)
    return total


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
