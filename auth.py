import sqlite3
import hashlib
import uuid
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
import dotenv, os
import jwt as pyjwt

# Charger les variables d'environnement
dotenv.load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

class AuthManager:
    def __init__(self, db_file="users.db"):
        self.db_file = db_file
        self._init_db()
        self.secret_key = SECRET_KEY

    def _get_db(self):
        """Crée une nouvelle connexion à la base de données"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialise la base de données avec la table users si elle n'existe pas."""
        conn = self._get_db()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    user_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (length(username) >= 3 AND length(username) <= 50)
                )
            ''')
            conn.commit()
        finally:
            conn.close()

    def _hash_password(self, password: str) -> str:
        """Hash le mot de passe avec SHA-256"""
        salt = "votre_sel_unique_secret"  # À changer en production
        salted = password + salt
        return hashlib.sha256(salted.encode()).hexdigest()

    def _generate_token(self) -> str:
        """Génère un token unique pour l'utilisateur"""
        return str(uuid.uuid4())

    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """Enregistre un nouvel utilisateur"""
        # Validation basique
        if len(username) < 3 or len(username) > 50:
            return False, "Le nom d'utilisateur doit faire entre 3 et 50 caractères"
        if len(password) < 6:
            return False, "Le mot de passe doit faire au moins 6 caractères"

        conn = self._get_db()
        try:
            cursor = conn.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return False, "Nom d'utilisateur déjà pris"

            password_hash = self._hash_password(password)
            user_token = self._generate_token()

            conn.execute(
                'INSERT INTO users (username, password_hash, user_token) VALUES (?, ?, ?)',
                (username, password_hash, user_token)
            )
            conn.commit()
            return True, "Inscription réussie ! Vous pouvez maintenant vous connecter."

        except sqlite3.Error as e:
            return False, f"Erreur lors de l'inscription: {str(e)}"
        finally:
            conn.close()

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Authentifie un utilisateur"""
        conn = self._get_db()
        try:
            password_hash = self._hash_password(password)
            cursor = conn.execute(
                'SELECT user_token FROM users WHERE username = ? AND password_hash = ?',
                (username, password_hash)
            )
            
            result = cursor.fetchone()
            if result:
                # Création du token JWT
                payload = {
                    'user_token': result[0],
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow()
                }
                token = pyjwt.encode(
                    payload,
                    self.secret_key,
                    algorithm='HS256'
                )
                # Si le token est en bytes, le convertir en string
                if isinstance(token, bytes):
                    token = token.decode('utf-8')
                return True, token

            return False, "Identifiants invalides"

        except sqlite3.Error as e:
            return False, f"Erreur lors de la connexion: {str(e)}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"
        finally:
            conn.close()

    def verify_token(self, token: str) -> bool:
        """Vérifie si un token JWT est valide"""
        try:
            pyjwt.decode(token, self.secret_key, algorithms=["HS256"])
            return True
        except:
            return False

    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change le mot de passe d'un utilisateur"""
        if len(new_password) < 6:
            return False, "Le nouveau mot de passe doit faire au moins 6 caractères"

        conn = self._get_db()
        try:
            old_password_hash = self._hash_password(old_password)
            cursor = conn.execute(
                'SELECT 1 FROM users WHERE username = ? AND password_hash = ?',
                (username, old_password_hash)
            )
            
            if not cursor.fetchone():
                return False, "Ancien mot de passe incorrect"

            new_password_hash = self._hash_password(new_password)
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (new_password_hash, username)
            )
            
            conn.commit()
            return True, "Mot de passe modifié avec succès"

        except sqlite3.Error as e:
            return False, f"Erreur lors du changement de mot de passe: {str(e)}"
        finally:
            conn.close()

    def get_user_token(self, username: str, password: str) -> Tuple[bool, str]:
        """Récupère le token unique de l'utilisateur"""
        conn = self._get_db()
        try:
            password_hash = self._hash_password(password)
            cursor = conn.execute(
                'SELECT user_token FROM users WHERE username = ? AND password_hash = ?',
                (username, password_hash)
            )
            
            result = cursor.fetchone()
            if result:
                return True, result[0]

            return False, "Identifiants invalides"

        except sqlite3.Error as e:
            return False, f"Erreur lors de la récupération du token: {str(e)}"
        finally:
            conn.close()

    def get_user_token_from_jwt(self, jwt_token: str) -> Optional[str]:
        """Extrait le user_token depuis un JWT token"""
        try:
            payload = pyjwt.decode(jwt_token, self.secret_key, algorithms=["HS256"])
            return payload.get('user_token')
        except:
            return None

