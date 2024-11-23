import xml.etree.ElementTree as ET
from datetime import datetime
import csv
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth."""
    R = 6371000  # Earth's radius in meters
    
    # Convert latitude and longitude to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def calculate_pace(prev_point, current_point):
    """Calculate pace in minutes per kilometer."""
    # Extract coordinates and timestamps
    prev_lat, prev_lon, prev_time = prev_point
    curr_lat, curr_lon, curr_time = current_point
    
    # Calculate distance
    distance = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
    
    # Calculate time difference in seconds
    time_diff = (curr_time - prev_time).total_seconds()
    
    # Calculate pace (minutes per km)
    if distance > 0 and time_diff > 0:
        pace = (time_diff / 60) / (distance / 1000)
        return pace
    return 5.0  # Default pace if calculation is not possible

def gpx_to_csv(gpx_file, csv_file):
    # Parse the GPX file
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    
    # Define namespaces
    namespaces = {
        'gpx': 'http://www.topografix.com/GPX/1/1',
        'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
    }
    
    # Prepare data
    data = []
    track_points = root.findall('.//gpx:trkpt', namespaces)
    
    for i, point in enumerate(track_points):
        # Extract elevation
        elevation = float(point.find('gpx:ele', namespaces).text)
        
        # Extract heart rate
        hr_elem = point.find('.//gpxtpx:hr', namespaces)
        heart_rate = int(hr_elem.text) if hr_elem is not None else 0
        
        # Extract time and coordinates
        time = datetime.strptime(point.find('gpx:time', namespaces).text, "%Y-%m-%dT%H:%M:%SZ")
        lat = float(point.get('lat'))
        lon = float(point.get('lon'))
        
        # Calculate pace
        pace = 5.0  # Default pace
        if i > 0:
            prev_point = [data[i-1]['latitude'], data[i-1]['longitude'], data[i-1]['time']]
            current_point = [lat, lon, time]
            pace = calculate_pace(prev_point, current_point)
        
        # Store point data
        data.append({
            'timestamp': time,
            'pace_min_per_km': pace,
            'elevation_meters': elevation,
            'heart_rate_bpm': heart_rate,
            'latitude': lat,
            'longitude': lon,
            'time': time
        })
    
    # Write to CSV
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'pace_min_per_km', 'elevation_meters', 'heart_rate_bpm']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for point in data:
            writer.writerow({
                'timestamp': point['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'pace_min_per_km': point['pace_min_per_km'],
                'elevation_meters': point['elevation_meters'],
                'heart_rate_bpm': point['heart_rate_bpm']
            })
    
    print(f"CSV file '{csv_file}' has been created successfully!")

# Example usage
for i in range(1, 17):
    gpx_to_csv(f"activities/{i}.gpx", f'activity_data_{i}.csv')