#!/usr/bin/env python3
"""
Module for parsing CSV input files containing corner coordinates of target objects.
"""

import csv

def detect_identifier_columns(header_row):
    """
    Detect SerialNumb or plot_id columns in the header row.
    Returns a tuple (serial_numb_index, plot_id_index) or (None, None) if not found.
    SerialNumb takes priority over plot_id if both exist.
    """
    serial_numb_index = None
    plot_id_index = None
    
    if header_row:
        # Convert to lowercase for case-insensitive comparison
        header_lower = [col.lower().strip() for col in header_row]
        
        # Look for SerialNumb variations
        serial_variations = ['serialnumb', 'serial_numb', 'serialnumber', 'serial_number', 'serial']
        for i, col in enumerate(header_lower):
            if col in serial_variations:
                serial_numb_index = i
                break
        
        # Look for plot_id variations
        plot_variations = ['plot_id', 'plotid', 'plot', 'id']
        for i, col in enumerate(header_lower):
            if col in plot_variations:
                plot_id_index = i
                break
    
    return serial_numb_index, plot_id_index

def parse_csv_input(csv_file):
    """
    Parse the input CSV file containing corner coordinates of target objects.
    Returns a list of objects, each with four corner coordinates and optional identifier.
    
    Format:
    - Standard: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4
    - With SerialNumb: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,SerialNumb
    - With plot_id: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,plot_id
    - With both: SerialNumb takes priority over plot_id
    - Header row is supported and automatically detected
    """
    objects = []
    
    with open(csv_file, 'r') as f:
        csv_reader = csv.reader(f)
        rows = list(csv_reader)
        
        if not rows:
            return objects
            
        # Check if first row might be a header
        first_row = rows[0]
        has_header = False
        serial_numb_index = None
        plot_id_index = None
        
        # Try to detect if first row is header by checking if coordinate columns contain non-numeric values
        if len(first_row) >= 8:
            try:
                # Try to parse first 8 values as coordinates
                for i in range(0, 8, 2):
                    float(first_row[i])    # lat
                    float(first_row[i+1])  # lon
                # If we get here, first row contains numeric data (not header)
                has_header = False
            except ValueError:
                # First row contains non-numeric data, likely a header
                has_header = True
                serial_numb_index, plot_id_index = detect_identifier_columns(first_row)
        
        # Start processing from appropriate row
        start_row = 1 if has_header else 0
        
        for row_idx, row in enumerate(rows[start_row:], start=start_row):
            # Check if the row has the minimum required values (8 coordinates)
            if len(row) < 8:
                print(f"Warning: Skipping row {row_idx + 1} with only {len(row)} values (minimum 8 required)")
                continue
                
            try:
                corners = [(float(row[i]), float(row[i+1])) for i in range(0, 8, 2)]
                
                # Check for identifier columns
                identifier = None
                
                # Priority: SerialNumb > plot_id
                if has_header:
                    if serial_numb_index is not None and serial_numb_index < len(row):
                        try:
                            identifier = int(row[serial_numb_index])
                        except ValueError:
                            print(f"Warning: Invalid SerialNumb value '{row[serial_numb_index]}' in row {row_idx + 1}")
                    elif plot_id_index is not None and plot_id_index < len(row):
                        try:
                            identifier = int(row[plot_id_index])
                        except ValueError:
                            print(f"Warning: Invalid plot_id value '{row[plot_id_index]}' in row {row_idx + 1}")
                else:
                    # No header detected, use old logic for backward compatibility
                    if len(row) >= 9:
                        try:
                            identifier = int(row[8])  # Assume 9th column is identifier
                        except ValueError:
                            print(f"Warning: Invalid identifier value '{row[8]}' in row {row_idx + 1}")
                
                # Store the object
                if identifier is not None:
                    objects.append((corners, identifier))
                else:
                    objects.append(corners)
                    
            except ValueError as e:
                print(f"Warning: Skipping row {row_idx + 1} due to invalid coordinate values: {e}")
                
    return objects
