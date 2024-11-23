import pandas as pd
from datetime import datetime, timedelta
import json
import time
from typing import Optional, List, Dict
import os
from threading import Thread, Lock
import threading

class TimeManager:
    """Gestionnaire centralisé du temps de simulation"""
    def __init__(self):
        self._current_time = None
        self._start_time = None
        self._simulation_start = None
        self._lock = Lock()
        self._running = False
        self._thread = None
        self._ensure_config_file()

    def _ensure_config_file(self):
        config = {
            "simulation_speed": 1.0,
            "paused": False
        }
        if not os.path.exists("simulation_config.json"):
            with open("simulation_config.json", "w") as f:
                json.dump(config, f, indent=4)

    def _load_config(self) -> dict:
        try:
            with open("simulation_config.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur de lecture de la configuration: {e}")
            return {"simulation_speed": 1.0, "paused": False}

    def start(self, start_datetime: datetime):
        with self._lock:
            self._start_time = start_datetime
            self._simulation_start = datetime.now()
            self._current_time = start_datetime
            self._running = True
            self._thread = Thread(target=self._update_time, daemon=True)
            self._thread.start()

    def _update_time(self):
        while self._running:
            config = self._load_config()
            if not config["paused"]:
                with self._lock:
                    real_elapsed = datetime.now() - self._simulation_start
                    simulated_elapsed = real_elapsed * config["simulation_speed"]
                    self._current_time = self._start_time + simulated_elapsed
            time.sleep(0.1)

    def get_current_time(self) -> datetime:
        with self._lock:
            return self._current_time

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

class ActivitySimulator:
    def __init__(self, csv_file: str):
        self.df_full = self._load_data(csv_file)
        self.time_manager = TimeManager()
        self._current_index_lock = Lock()
        self._current_index = 0
        
    def _load_data(self, csv_file: str) -> pd.DataFrame:
        """Charge et prépare les données du CSV"""
        df = pd.read_csv(csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Assurer que les données sont triées chronologiquement
        df = df.sort_values('timestamp')
        
        # Conversion des colonnes si nécessaire
        if 'pace_min_per_km' not in df.columns and 'speed' in df.columns:
            # Convertir la vitesse (m/s) en allure (min/km)
            df['pace_min_per_km'] = 16.666667 / df['speed']  # 16.666667 = 1000/60
            
        return df

    def start_simulation(self):
        """Démarre la simulation"""
        if len(self.df_full) > 0:
            self.time_manager.start(self.df_full['timestamp'].iloc[0])
            
    def _find_current_index(self, current_time: datetime) -> int:
        """Helper method to find the correct index based on current time"""
        if current_time is None or len(self.df_full) == 0:
            return -1
            
        # Trouver le dernier index où timestamp <= current_time
        mask = self.df_full['timestamp'] <= current_time
        if not mask.any():
            return -1
        return mask.values.nonzero()[0][-1]

    def get_simulation_data(self) -> dict:
        """Récupère les données de simulation au format spécifié"""
        current_time = self.time_manager.get_current_time()
        if current_time is None:
            return None

        with self._current_index_lock:
            current_idx = self._find_current_index(current_time)
            if current_idx >= 0:
                history_df = self.df_full.iloc[:current_idx + 1]
                
                return {
                    'timestamp': history_df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
                    'pace_min_per_km': history_df['pace_min_per_km'].round(2).tolist(),
                    'elevation_meters': history_df['elevation_meters'].round(1).tolist(),
                    'heart_rate_bpm': history_df['heart_rate_bpm'].round().astype(int).tolist()
                }
            return None
    
    def get_current_time(self) -> Optional[str]:
        """
        Récupère le temps écoulé depuis le début de la session au format HH:MM:SS
        
        Returns:
            Optional[str]: Temps écoulé au format 'HH:MM:SS' ou None si la simulation n'a pas démarré
        """
        current_time = self.time_manager.get_current_time()
        if current_time is None or len(self.df_full) == 0:
            return None
            
        # Calculer la différence de temps depuis le début
        start_time = self.df_full['timestamp'].iloc[0]
        elapsed = current_time - start_time
        
        # Extraire les heures, minutes et secondes
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # Formater avec les zéros de tête
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_current_pace(self) -> Optional[float]:
        """Récupère l'allure actuelle en min/km"""
        current_time = self.time_manager.get_current_time()
        if current_time is None:
            return None
        
        with self._current_index_lock:
            current_idx = self._find_current_index(current_time)
            if current_idx >= 0:
                return self.df_full['pace_min_per_km'].iloc[current_idx]
            return None
        
    def get_current_distance(self) -> Optional[float]:
        """Récupère la distance totale parcourue en km"""
        current_time = self.time_manager.get_current_time()
        if current_time is None:
            return None
        
        with self._current_index_lock:
            current_idx = self._find_current_index(current_time)
            if current_idx >= 0:
                history_df = self.df_full.iloc[:current_idx + 1]
                # Calculer les intervalles de temps entre les points
                time_diff = history_df['timestamp'].diff().fillna(pd.Timedelta(seconds=0))
                # Convertir en heures
                time_diff_hours = time_diff.dt.total_seconds() / 3600
                # Calculer la distance pour chaque segment (vitesse * temps)
                distances = (60 / history_df['pace_min_per_km']) * time_diff_hours
                return distances.sum()
            return None

    def reset(self):
        """Réinitialise la simulation"""
        with self._current_index_lock:
            self._current_index = 0
        self.time_manager.stop()
        if len(self.df_full) > 0:
            self.time_manager.start(self.df_full['timestamp'].iloc[0])

    def force_progress(self, minutes: int):
        """Fait progresser la simulation de X minutes"""
        if len(self.df_full) == 0:
            return
        current_time = self.time_manager.get_current_time()
        new_time = current_time + timedelta(minutes=minutes)
        self.time_manager.stop()
        self.time_manager.start(new_time)