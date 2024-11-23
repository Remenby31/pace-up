from fitparse import FitFile
import json
import os
from datetime import datetime

class FitDataExtractor:
    def __init__(self, fit_files_dir, output_dir="garmin_run"):
        self.fit_files_dir = fit_files_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process_fit_file(self, fit_file_path):
        fitfile = FitFile(fit_file_path)
        
        activity_data = {
            "timestamp": [],
            "heart_rate": [],
            "position": [],
            "altitude": [],
            "speed": [],
            "distance": []
        }
        
        for record in fitfile.get_messages("record"):
            data = record.get_values()
            
            activity_data["timestamp"].append(str(data.get("timestamp")))
            activity_data["heart_rate"].append(data.get("heart_rate"))
            
            if "position_lat" in data and "position_long" in data:
                activity_data["position"].append({
                    "lat": data.get("position_lat") / ((2**32) / 360),
                    "lon": data.get("position_long") / ((2**32) / 360)
                })
            else:
                activity_data["position"].append(None)
            
            activity_data["altitude"].append(data.get("altitude"))
            activity_data["speed"].append(data.get("speed"))
            activity_data["distance"].append(data.get("distance"))
        
        return activity_data

    def process_directory(self):
        for filename in os.listdir(self.fit_files_dir):
            if filename.endswith(".fit"):
                try:
                    file_path = os.path.join(self.fit_files_dir, filename)
                    data = self.process_fit_file(file_path)
                    
                    output_file = os.path.join(self.output_dir, 
                                             f"{filename[:-4]}.json")
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Traité: {filename}")
                except Exception as e:
                    print(f"Erreur sur {filename}: {str(e)}")

# Utilisation
if __name__ == "__main__":
    fit_dir = input("Dossier contenant les fichiers .FIT: ")
    extractor = FitDataExtractor(fit_dir)
    extractor.process_directory()