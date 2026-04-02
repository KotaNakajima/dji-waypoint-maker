#!/usr/bin/env python3
"""
Drone model configurations and default flight parameters.
Supports DJI Mavic 3 Enterprise series drones.
"""

DRONE_MODELS = {
    "M3E": {
        "name": "Mavic 3E",
        "droneEnumValue": 77,
        "droneSubEnumValue": 0,
        "payloadEnumValue": 66,
        "payloadSubEnumValue": 0,
        "payloadPositionIndex": 0,
        "imageFormat": "wide",
        "sensor_width_mm": 17.3,
        "sensor_height_mm": 13.0,
        "focal_length_mm": 12.0,
        "horizontal_fov_deg": 73.7,
        "vertical_fov_deg": 56.8,
        "image_width_px": 5280,
        "image_height_px": 3956,
    },
    "M3T": {
        "name": "Mavic 3T",
        "droneEnumValue": 77,
        "droneSubEnumValue": 1,
        "payloadEnumValue": 67,
        "payloadSubEnumValue": 0,
        "payloadPositionIndex": 0,
        "imageFormat": "wide",
        "sensor_width_mm": 17.3,
        "sensor_height_mm": 13.0,
        "focal_length_mm": 12.0,
        "horizontal_fov_deg": 73.7,
        "vertical_fov_deg": 56.8,
        "image_width_px": 5280,
        "image_height_px": 3956,
    },
    "M3M": {
        "name": "Mavic 3M",
        "droneEnumValue": 77,
        "droneSubEnumValue": 0,
        "payloadEnumValue": 68,
        "payloadSubEnumValue": 3,
        "payloadPositionIndex": 0,
        "imageFormat": "visable,narrow_band",
        # RGB camera (4/3 CMOS, 20MP) - same as M3E
        "sensor_width_mm": 17.3,
        "sensor_height_mm": 13.0,
        "focal_length_mm": 12.0,
        "horizontal_fov_deg": 73.7,
        "vertical_fov_deg": 56.8,
        "image_width_px": 5280,
        "image_height_px": 3956,
        "min_shoot_interval_s": 0.7,
        # Multispectral camera (1/2.8" CMOS, 5MP x4 bands)
        "ms_sensor_width_mm": 5.08,
        "ms_sensor_height_mm": 3.81,
        "ms_focal_length_mm": 4.29,
        "ms_horizontal_fov_deg": 61.2,
        "ms_vertical_fov_deg": 48.1,
        "ms_image_width_px": 2592,
        "ms_image_height_px": 1944,
        "ms_min_shoot_interval_s": 2.0,
    },
}

# Default flight parameters
DEFAULT_TRANSITIONAL_SPEED = 3   # m/s
DEFAULT_AUTO_FLIGHT_SPEED = 3    # m/s
DEFAULT_VD_HEIGHT = 7            # meters
DEFAULT_OBL_HEIGHT = 10          # meters
DEFAULT_OBL_GIMBAL_ANGLE = 45   # degrees (from nadir=90)
DEFAULT_OBL_ZOOM = 4            # optical zoom factor
DEFAULT_MAPPING2D_HEIGHT = 50   # meters

# M3M camera (imageFormat) options
M3M_IMAGE_FORMATS = {
    "1": {"label": "RGB only",                   "imageFormat": "visable"},
    "2": {"label": "Multispectral only",          "imageFormat": "narrow_band"},
    "3": {"label": "RGB + Multispectral",         "imageFormat": "visable,narrow_band"},
}

# Default mission settings (configurable via Advanced Settings)
DEFAULT_MISSION_CONFIG = {
    # User-configurable
    "finishAction": "goHome",
    "exitOnRCLost": "executeLostAction",
    "executeRCLostAction": "goBack",
    "takeOffSecurityHeight": 20,
    "globalTransitionalSpeed": 15,
    "globalRTHHeight": 20,
    "flyToWaylineMode": "safely",
    "waylineAvoidLimitAreaMode": 0,
    # Structural defaults (included in XML, not in interactive menu)
    "dewarpingEnable": 0,
    "returnMode": "singleReturnFirst",
    "samplingRate": 240000,
    "scanningMode": "nonRepetitive",
    "modelColoringEnable": 0,
    "quickOrthoMappingEnable": 0,
    "facadeWaylineEnable": 0,
    "isLookAtSceneSet": 0,
    "smartObliqueGimbalPitch": -45,
    "efficiencyFlightModeEnable": 0,
}

MISSION_CONFIG_OPTIONS = {
    "finishAction": ["goHome", "autoLand", "goContinue", "hover"],
    "exitOnRCLost": ["goContinue", "executeLostAction"],
    "executeRCLostAction": ["goBack", "hover", "landing"],
    "flyToWaylineMode": ["safely", "pointToPoint"],
}

# Common shutter speeds for blur-free speed calculation
SHUTTER_SPEEDS = [500, 800, 1000, 1600, 2000]
MAX_BLUR_PX = 0.5  # max acceptable motion blur in pixels


def get_effective_camera(drone_config):
    """
    Return the camera specs that determine flight planning (GSD, spacing, speed).

    When narrow_band is included in imageFormat, the multispectral camera is the
    limiting factor (lower resolution, narrower FOV). Otherwise use the RGB camera.

    Returns:
        dict with sensor_width_mm, sensor_height_mm, focal_length_mm,
        horizontal_fov_deg, vertical_fov_deg, image_width_px, image_height_px,
        min_shoot_interval_s
    """
    image_format = drone_config.get("imageFormat", "wide")
    use_ms = "narrow_band" in image_format and "ms_sensor_width_mm" in drone_config

    if use_ms:
        return {
            "sensor_width_mm": drone_config["ms_sensor_width_mm"],
            "sensor_height_mm": drone_config["ms_sensor_height_mm"],
            "focal_length_mm": drone_config["ms_focal_length_mm"],
            "horizontal_fov_deg": drone_config["ms_horizontal_fov_deg"],
            "vertical_fov_deg": drone_config["ms_vertical_fov_deg"],
            "image_width_px": drone_config["ms_image_width_px"],
            "image_height_px": drone_config["ms_image_height_px"],
            "min_shoot_interval_s": drone_config.get("ms_min_shoot_interval_s", 2.0),
        }
    else:
        return {
            "sensor_width_mm": drone_config["sensor_width_mm"],
            "sensor_height_mm": drone_config["sensor_height_mm"],
            "focal_length_mm": drone_config["focal_length_mm"],
            "horizontal_fov_deg": drone_config["horizontal_fov_deg"],
            "vertical_fov_deg": drone_config["vertical_fov_deg"],
            "image_width_px": drone_config["image_width_px"],
            "image_height_px": drone_config["image_height_px"],
            "min_shoot_interval_s": drone_config.get("min_shoot_interval_s", 0.7),
        }


def get_drone_config(model_key):
    """
    Get drone configuration by model key.

    Args:
        model_key: One of "M3E", "M3T", "M3M" (case-insensitive)

    Returns:
        dict with drone/payload enum values and camera specs

    Raises:
        ValueError: If model_key is not recognized
    """
    key = model_key.upper()
    if key not in DRONE_MODELS:
        valid = ", ".join(DRONE_MODELS.keys())
        raise ValueError(f"Unknown drone model '{model_key}'. Valid models: {valid}")
    return DRONE_MODELS[key]
