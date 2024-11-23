import folium
from polyline import decode
import json

# Charger le fichier JSON
with open('strava_run/20240802_12042453750.json', 'r') as file:
    data = json.load(file)

# Décoder le polyline
coordinates = decode(data["map"]["summary_polyline"])

# Créer la carte centrée sur le point de départ
map = folium.Map(location=data["start_latlng"], zoom_start=15)

# Ajouter le tracé
folium.PolyLine(
    coordinates,
    weight=3,
    color='red',
    opacity=0.8,
    popup=f"Dénivelé total: {data['total_elevation_gain']}m"
).add_to(map)

# Ajouter des marqueurs pour le début, la fin et les points d'élévation
folium.Marker(
    data["start_latlng"],
    popup=f'Départ (Altitude: {data["elev_low"]}m)',
    icon=folium.Icon(color='green')
).add_to(map)

folium.Marker(
    data["end_latlng"],
    popup=f'Arrivée (Altitude: {data["elev_high"]}m)',
    icon=folium.Icon(color='red')
).add_to(map)

# Sauvegarder la carte
map.save(f"strava_run/20240802_12042453750.html")