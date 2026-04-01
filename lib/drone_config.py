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
        "sensor_width_mm": 17.3,
        "sensor_height_mm": 13.0,
        "focal_length_mm": 12.0,
        "horizontal_fov_deg": 73.7,
        "vertical_fov_deg": 56.8,
        "image_width_px": 5280,
        "image_height_px": 3956,
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

# Common shutter speeds for blur-free speed calculation
SHUTTER_SPEEDS = [500, 800, 1000, 1600, 2000]
MAX_BLUR_PX = 0.5  # max acceptable motion blur in pixels


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
