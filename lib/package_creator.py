#!/usr/bin/env python3
"""
Module for creating zip and KMZ packages for drone flight files.
"""

import os
import shutil
import zipfile
from datetime import datetime


def create_zip_files_from_dir(wpmz_dir, route_type, flight_name=None, output_dir_name=None):
    """
    Create a DJI WPMZ package from an existing wpmz directory that contains
    template.kml and waylines.wpml files.
    Returns the paths to the created zip and kmz files.
    """
    return create_zip_files_from_dir_with_part(wpmz_dir, route_type, flight_name, output_dir_name)


def create_zip_files_from_dir_with_part(wpmz_dir, route_type, flight_name=None,
                                         output_dir_name=None, part_number=None):
    """
    Create a DJI WPMZ package from an existing wpmz directory.
    Supports part numbers in filenames for split files.
    Returns the paths to the created zip and kmz files.
    """
    date_str = datetime.now().strftime("%Y%m%d")

    if flight_name is None:
        flight_name = f"{route_type}_route"

    if part_number is not None:
        zip_filename = f"{date_str}_{flight_name}_{route_type}_part{part_number}.zip"
        kmz_filename = f"{date_str}_{flight_name}_{route_type}_part{part_number}.kmz"
    else:
        zip_filename = f"{date_str}_{flight_name}_{route_type}.zip"
        kmz_filename = f"{date_str}_{flight_name}_{route_type}.kmz"

    kml_path = os.path.join(wpmz_dir, "template.kml")
    wpml_path = os.path.join(wpmz_dir, "waylines.wpml")

    # Create the zip file with wpmz/ directory structure
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(kml_path, arcname=os.path.join("wpmz", "template.kml"))
        if os.path.exists(wpml_path):
            zipf.write(wpml_path, arcname=os.path.join("wpmz", "waylines.wpml"))

    # Create a copy with .kmz extension
    shutil.copy(zip_filename, kmz_filename)

    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if output_dir_name:
        folder_name = output_dir_name
    else:
        if part_number is not None:
            folder_name = f"{date_str}_{flight_name}_split"
        else:
            folder_name = f"{date_str}_{flight_name}"

    output_folder_path = os.path.join(output_dir, folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    # Move files to output directory
    output_zip_path = os.path.join(output_folder_path, zip_filename)
    output_kmz_path = os.path.join(output_folder_path, kmz_filename)

    shutil.move(zip_filename, output_zip_path)
    shutil.move(kmz_filename, output_kmz_path)

    return output_zip_path, output_kmz_path


def create_template_only_package(wpmz_dir, route_type, flight_name=None,
                                  output_dir_name=None):
    """
    Create a DJI WPMZ package containing only template.kml (no waylines.wpml).
    Used for mapping2d routes where DJI Pilot 2 auto-generates waylines.
    Returns the paths to the created zip and kmz files.
    """
    date_str = datetime.now().strftime("%Y%m%d")

    if flight_name is None:
        flight_name = f"{route_type}_route"

    zip_filename = f"{date_str}_{flight_name}_{route_type}.zip"
    kmz_filename = f"{date_str}_{flight_name}_{route_type}.kmz"

    kml_path = os.path.join(wpmz_dir, "template.kml")

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(kml_path, arcname=os.path.join("wpmz", "template.kml"))

    shutil.copy(zip_filename, kmz_filename)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    folder_name = output_dir_name if output_dir_name else f"{date_str}_{flight_name}"
    output_folder_path = os.path.join(output_dir, folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    output_zip_path = os.path.join(output_folder_path, zip_filename)
    output_kmz_path = os.path.join(output_folder_path, kmz_filename)

    shutil.move(zip_filename, output_zip_path)
    shutil.move(kmz_filename, output_kmz_path)

    return output_zip_path, output_kmz_path
